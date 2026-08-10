from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from ..audit import record_event
from ..security import login_required, roles_required
from .ldap_auth import ldap_status
from .service import AuthStatus, authenticate

bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


def _safe_next(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or not value.startswith("/"):
        return None
    return value


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("web.app_home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        result = authenticate(username, password, request.remote_addr)

        if result.status == AuthStatus.SUCCESS and result.user:
            user = result.user
            now = int(time.time())
            session.clear()
            session.permanent = True
            session.update(
                user_id=user.user_id,
                username=user.username,
                display_name=user.display_name,
                role_code=user.role_code,
                role_name=user.role_name,
                auth_type=user.auth_type,
                session_version=user.session_version,
                login_at=now,
                last_activity=now,
                last_validation=now,
            )
            record_event("AUTH", "RM_CFACT_USER", "LOGIN", user.user_id)
            destination = _safe_next(request.form.get("next") or request.args.get("next"))
            return redirect(destination or url_for("web.app_home"))

        if result.status == AuthStatus.UNAVAILABLE:
            logger.error("LDAP no disponible: %s", result.technical_detail)
            flash("No fue posible contactar el servicio de autenticación corporativa.", "error")
        elif result.status == AuthStatus.CONFIG_ERROR:
            logger.error("Error configuración autenticación: %s", result.technical_detail)
            flash("La autenticación no está correctamente configurada.", "error")
        elif result.status == AuthStatus.LOCKED:
            flash("El acceso está temporalmente bloqueado por intentos fallidos.", "error")
        else:
            flash("Usuario o clave incorrecta.", "error")

    return render_template(
        "auth/login.html",
        next_url=_safe_next(request.args.get("next")),
    )


@bp.post("/logout")
def logout():
    if session.get("user_id"):
        record_event("AUTH", "RM_CFACT_USER", "LOGOUT", session["user_id"])
    session.clear()
    return redirect(url_for("auth.login"))


@bp.get("/me")
@login_required
def me():
    return jsonify({
        "authenticated": True,
        "user_id": session.get("user_id"),
        "username": session.get("username"),
        "display_name": session.get("display_name"),
        "role_code": session.get("role_code"),
        "role_name": session.get("role_name"),
        "auth_type": session.get("auth_type"),
    })


@bp.get("/api/v1/security/ldap/status")
@roles_required("ADMIN")
def ldap_configuration_status():
    return jsonify(ldap_status())
