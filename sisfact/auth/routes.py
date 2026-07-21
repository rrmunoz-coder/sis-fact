from __future__ import annotations

from flask import Blueprint, current_app, jsonify, redirect, render_template_string, request, session, url_for

from sisfact.auth.ldap_auth import LdapAuthenticator
from sisfact.auth.service import AuthService
from sisfact.auth.user_repository import UserRepository


auth_bp = Blueprint("auth", __name__)

LOGIN_TEMPLATE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>SIS-FACT Login</title>
  <style>
    body { font-family: Arial, sans-serif; background:#f4f6f8; margin:0; }
    .box { width:380px; margin:80px auto; background:white; padding:28px; border-radius:14px; box-shadow:0 8px 24px rgba(0,0,0,.12); }
    h1 { margin:0 0 8px 0; font-size:22px; }
    p { color:#555; }
    label { display:block; margin-top:14px; font-weight:bold; }
    input { width:100%; padding:10px; margin-top:6px; box-sizing:border-box; border:1px solid #bbb; border-radius:8px; }
    button { margin-top:20px; width:100%; padding:11px; border:0; border-radius:8px; background:#1f4e79; color:white; font-weight:bold; cursor:pointer; }
    .error { color:#9b1c1c; background:#fde8e8; border:1px solid #f5b5b5; padding:10px; border-radius:8px; }
  </style>
</head>
<body>
  <div class="box">
    <h1>SIS-FACT / Billing One</h1>
    <p>Ingreso corporativo LDAP.</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="post">
      <label>Usuario</label>
      <input name="username" autocomplete="username" placeholder="usuario" required>
      <label>Password</label>
      <input name="password" type="password" autocomplete="current-password" required>
      <button type="submit">Ingresar</button>
    </form>
  </div>
</body>
</html>
"""


@auth_bp.get("/login")
def login_form():
    return render_template_string(LOGIN_TEMPLATE, error=None)


@auth_bp.post("/login")
def login_submit():
    auth = AuthService(current_app.config["CONFIG_RAW"])
    result = auth.login(request.form.get("username", ""), request.form.get("password", ""))
    if not result.ok or result.user is None:
        return render_template_string(LOGIN_TEMPLATE, error=result.message), 401
    session["user"] = result.user.to_session()
    return redirect(url_for("home"))


@auth_bp.post("/api/v1/auth/login")
def api_login():
    payload = request.get_json(silent=True) or {}
    auth = AuthService(current_app.config["CONFIG_RAW"])
    result = auth.login(payload.get("username", ""), payload.get("password", ""))
    if not result.ok or result.user is None:
        return jsonify({"ok": False, "message": result.message}), 401
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
def create_user():
    """Crea usuario de autorización local.

    No valida ni consulta LDAP. El usuario LDAP se autentica recién en /login.
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
        created_by=(session.get("user") or {}).get("username", "SYSTEM"),
    )
    return jsonify({"ok": True, "user_id": user_id})
