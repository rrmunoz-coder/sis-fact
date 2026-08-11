from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import uuid

from flask import Flask, g, redirect, render_template, request
from flask_wtf.csrf import CSRFError, CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import load_config
from .errors import request_id
from .security import enforce_session, has_permission

csrf = CSRFProtect()


def _test_defaults() -> dict:
    from datetime import timedelta
    return {
        "TESTING": True,
        "SECRET_KEY": "test-only-secret-key-32-bytes-minimum-0001",
        "WTF_CSRF_ENABLED": False,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": False,
        "SESSION_IDLE_MINUTES": 30,
        "SESSION_VALIDATION_SECONDS": 120,
        "PERMANENT_SESSION_LIFETIME": timedelta(minutes=720),
        "FORCE_HTTPS": False,
        "TRUST_PROXY_HEADERS": False,
        "TRUSTED_PROXY_HOPS": 1,
        "HSTS_SECONDS": 31536000,
        "CONTENT_SECURITY_POLICY": "default-src 'self'; style-src 'self'; script-src 'self'",
    }


def _configure_logging(app: Flask) -> None:
    if app.testing:
        return
    log_dir = Path(app.root_path).parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_dir / "billing_one.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    handler.setLevel(logging.INFO)
    root_logger = logging.getLogger()
    if not any(isinstance(item, RotatingFileHandler) for item in root_logger.handlers):
        root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


def create_app(test_config: dict | None = None, config_path: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    if test_config is None:
        app.config.update(load_config(config_path))
    else:
        app.config.update(_test_defaults())
        app.config.update(test_config)

    app.config.setdefault("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)

    if app.config.get("TRUST_PROXY_HEADERS"):
        hops = int(app.config.get("TRUSTED_PROXY_HOPS", 1))
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=hops, x_host=hops, x_port=hops)

    _configure_logging(app)
    csrf.init_app(app)

    from .auth.routes import bp as auth_bp
    from .context.routes import bp as context_bp
    from .execution.routes import bp as execution_bp
    from .integrations.routes import bp as integrations_bp
    from .users.routes import bp as users_bp
    from .web import bp as web_bp
    for blueprint in (auth_bp, users_bp, context_bp, integrations_bp, execution_bp, web_bp):
        app.register_blueprint(blueprint)

    @app.before_request
    def protect_request():
        supplied = request.headers.get("X-Request-ID", "").strip() if app.config.get("TRUST_PROXY_HEADERS") else ""
        g.request_id = supplied[:64] if supplied and supplied.isascii() else uuid.uuid4().hex[:12]
        if app.config.get("FORCE_HTTPS") and not request.is_secure:
            return redirect(request.url.replace("http://", "https://", 1), code=307)
        if request.endpoint == "static":
            return None
        return enforce_session()

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = app.config["CONTENT_SECURITY_POLICY"]
        response.headers["X-Request-ID"] = request_id()
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = f"max-age={int(app.config['HSTS_SECONDS'])}; includeSubDomains"
        if request.endpoint and request.endpoint != "static":
            response.headers.setdefault("Cache-Control", "no-store")
        return response

    @app.context_processor
    def inject_security_helpers():
        return {"can": has_permission}

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        app.logger.warning("CSRF rechazado: %s [incidente=%s]", error.description, request_id())
        return render_template("errors/400.html", message="La sesión del formulario expiró o el formulario no es válido.", request_id=request_id()), 400

    @app.errorhandler(403)
    def forbidden(error):
        app.logger.warning("Acceso denegado: %s [incidente=%s]", error, request_id())
        return render_template("errors/403.html", request_id=request_id()), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html", request_id=request_id()), 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.error("Error no controlado [incidente=%s]", request_id(), exc_info=(type(error), error, error.__traceback__))
        return render_template("errors/500.html", request_id=request_id()), 500

    return app
