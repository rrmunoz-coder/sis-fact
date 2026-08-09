from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import Blueprint, current_app, jsonify, redirect, render_template_string, request, session, url_for

from sisfact.auth.ldap_auth import LdapAuthenticator, normalize_username
from sisfact.auth.service import AuthService
from sisfact.auth.user_repository import UserRepository


auth_bp = Blueprint("auth", __name__)

LOGIN_TEMPLATE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SIS-FACT Login</title>
  <style>
    body { font-family: Arial, sans-serif; background:#f4f6f8; margin:0; }
    .box { width:390px; margin:70px auto; background:white; padding:28px; border-radius:14px; box-shadow:0 8px 24px rgba(0,0,0,.12); }
    h1 { margin:0 0 8px 0; font-size:22px; }
    p { color:#555; line-height:1.35; }
    label { display:block; margin-top:14px; font-weight:bold; }
    input { width:100%; padding:10px; margin-top:6px; box-sizing:border-box; border:1px solid #bbb; border-radius:8px; }
    button { margin-top:20px; width:100%; padding:11px; border:0; border-radius:8px; background:#1f4e79; color:white; font-weight:bold; cursor:pointer; }
    .error { color:#9b1c1c; background:#fde8e8; border:1px solid #f5b5b5; padding:10px; border-radius:8px; margin:12px 0; }
    .hint { font-size:12px; color:#666; margin-top:14px; }
  </style>
</head>
<body>
  <div class="box">
    <h1>SIS-FACT / Billing One</h1>
    <p>Ingreso corporativo. El usuario debe existir en SIS-FACT y la password se valida contra LDAP.</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="post" action="{{ url_for('auth.login_submit') }}">
      <input type="hidden" name="next" value="{{ next_url }}">
      <label>Usuario</label>
      <input name="username" autocomplete="username" placeholder="usuario, dominio\\usuario o usuario@dominio" required autofocus>
      <label>Password</label>
      <input name="password" type="password" autocomplete="current-password" required>
      <button type="submit">Ingresar</button>
    </form>
    <div class="hint">No se guarda password LDAP en Oracle.</div>
  </div>
</body>
</html>
"""

APP_TEMPLATE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SIS-FACT / Billing One</title>
  <style>
    body { font-family: Arial, sans-serif; margin:0; background:#eef2f5; }
    header { background:#1f4e79; color:white; padding:18px 28px; }
    main { padding:24px 28px; }
    .card { background:white; border-radius:12px; padding:18px; margin-bottom:16px; box-shadow:0 4px 14px rgba(0,0,0,.08); }
    a { color:#1f4e79; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(230px, 1fr)); gap:14px; }
    .muted { color:#555; }
  </style>
</head>
<body>
  <header>
    <h1>SIS-FACT / Billing One</h1>
    <div>Usuario: {{ user.display_name }} | Rol: {{ user.role_code }}</div>
  </header>
  <main>
    <div class="card">
      <h2>Panel base</h2>
      <p class="muted">Login operativo. Desde esta base se agregan módulos de facturación, controles y tableros.</p>
    </div>
    <div class="grid">
      <div class="card"><h3>Estado</h3><a href="{{ url_for('health') }}">/health</a></div>
      <div class="card"><h3>LDAP</h3><a href="{{ url_for('auth.ldap_status') }}">/api/v1/security/ldap/status</a></div>
      <div class="card"><h3>Sesión</h3><a href="{{ url_for('auth.me') }}">/me</a></div>
      <div class="card"><h3>Salir</h3><a href="{{ url_for('auth.logout') }}">/logout</a></div>
    </div>
  </main>
</body>
</html>
"""


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if not session.get("user"):
            return redirect(url_for("auth.login_form", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        user = session.get("user") or {}
        if not user:
            return jsonify({"ok": False, "error": "No autenticado"}), 401
        if str(user.get("role_code", "")).upper() != "ADMIN":
            return jsonify({"ok": False, "error": "Requiere rol ADMIN"}), 403
        return view(*args, **kwargs)

    return wrapped


@auth_bp.get("/login")
def login_form():
    if session.get("user"):
        return redirect(url_for("auth.app_home"))
    return render_template_string(LOGIN_TEMPLATE, error=None, next_url=request.args.get("next", ""))


@auth_bp.post("/login")
def login_submit():
    auth = AuthService(current_app.config["CONFIG_RAW"])
    result = auth.login(request.form.get("username", ""), request.form.get("password", ""))
    if not result.ok or result.user is None:
        return render_template_string(
            LOGIN_TEMPLATE,
            error=result.message,
            next_url=request.form.get("next", ""),
        ), 401
    session["user"] = result.user.to_session()
    next_url = request.form.get("next") or url_for("auth.app_home")
    return redirect(next_url)


@auth_bp.get("/app")
@login_required
def app_home():
    return render_template_string(APP_TEMPLATE, user=session["user"])


@auth_bp.post("/api/v1/auth/login")
def api_login():
    payload = request.get_json(silent=True) or {}
    auth = AuthService(current_app.config["CONFIG_RAW"])
    result = auth.login(payload.get("username", ""), payload.get("password", ""))
    if not result.ok or result.user is None:
        return jsonify({"ok": False, "code": result.code, "message": result.message}), 401
    session["user"] = result.user.to_session()
    return jsonify({"ok": True, "user": result.user.to_session()})


@auth_bp.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login_form"))


@auth_bp.get("/me")
def me():
    return jsonify(session.get("user") or {"authenticated": False})


@auth_bp.get("/api/v1/security/ldap/status")
def ldap_status():
    return jsonify(LdapAuthenticator(current_app.config["CONFIG_RAW"]).status())


@auth_bp.post("/api/v1/security/users")
@admin_required
def create_user():
    """Crea usuario de autorizacion local.

    No valida ni consulta LDAP. El usuario LDAP se autentica recien en /login.
    """
    payload = request.get_json(silent=True) or {}
    required = ["username", "display_name", "role_code"]
    missing = [field for field in required if not payload.get(field)]
    if missing:
        return jsonify({"ok": False, "error": f"Campos obligatorios faltantes: {', '.join(missing)}"}), 400

    repo = UserRepository(current_app.config["CONFIG_RAW"])
    user_id = repo.create_user(
        username=payload["username"],
        display_name=payload["display_name"],
        email=payload.get("email"),
        role_code=payload["role_code"],
        auth_type=payload.get("auth_type", "LDAP"),
        created_by=normalize_username((session.get("user") or {}).get("username", "SYSTEM")),
    )
    return jsonify({"ok": True, "user_id": user_id})
