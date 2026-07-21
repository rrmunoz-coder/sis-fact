from flask import Flask

from sisfact.auth.routes import auth_bp
from sisfact.core.config import load_config
from sisfact.web.routes import register_routes


def create_app(config_path: str = "config.ini") -> Flask:
    app = Flask(__name__)
    settings = load_config(config_path)

    app.config.update(settings.to_flask_config())
    app.secret_key = settings.secret_key

    app.register_blueprint(auth_bp)
    register_routes(app)
    return app
