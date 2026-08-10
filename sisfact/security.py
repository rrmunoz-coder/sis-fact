from __future__ import annotations

from functools import wraps
import logging
import time

from flask import current_app, flash, redirect, request, session, url_for

from .db import connection

logger = logging.getLogger(__name__)


def _clear_session(message: str):
    session.clear()
    flash(message, "error")
    return redirect(url_for("auth.login"))


def load_session_user(user_id: int) -> dict | None:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT U.USER_ID, U.USERNAME, U.DISPLAY_NAME, U.ACTIVE,
                       R.ROLE_CODE, R.ROLE_NAME, R.ACTIVE,
                       A.AUTH_TYPE, NVL(A.SESSION_VERSION, 1)
                FROM RM_CFACT_USER U
                JOIN RM_CFACT_ROLE R ON R.ROLE_ID = U.ROLE_ID
                JOIN RM_CFACT_USER_AUTH A ON A.USER_ID = U.USER_ID
                WHERE U.USER_ID = :user_id
                """,
                {"user_id": user_id},
            )
            row = cur.fetchone()
    if not row:
        return None
    return {
        "user_id": int(row[0]), "username": row[1], "display_name": row[2],
        "user_active": row[3], "role_code": row[4], "role_name": row[5],
        "role_active": row[6], "auth_type": row[7], "session_version": int(row[8] or 1),
    }


def enforce_session():
    if not session.get("user_id"):
        return None
    now = int(time.time())
    login_at = int(session.get("login_at", now))
    last_activity = int(session.get("last_activity", login_at))
    absolute_seconds = int(current_app.config["PERMANENT_SESSION_LIFETIME"].total_seconds())
    idle_seconds = int(current_app.config["SESSION_IDLE_MINUTES"]) * 60
    if now - login_at > absolute_seconds:
        return _clear_session("Tu sesión alcanzó su duración máxima. Ingresa nuevamente.")
    if now - last_activity > idle_seconds:
        return _clear_session("Tu sesión expiró por inactividad. Ingresa nuevamente.")

    validation_seconds = int(current_app.config["SESSION_VALIDATION_SECONDS"])
    last_validation = int(session.get("last_validation", 0))
    if now - last_validation >= validation_seconds:
        try:
            user = load_session_user(int(session["user_id"]))
        except Exception:
            logger.exception("No fue posible revalidar la sesión")
            return _clear_session("No fue posible validar tu sesión de forma segura. Ingresa nuevamente.")
        expected_version = int(session.get("session_version", 1))
        if (
            not user or user["user_active"] != "Y" or user["role_active"] != "Y"
            or user["session_version"] != expected_version
        ):
            return _clear_session("Tu acceso fue actualizado o revocado. Ingresa nuevamente.")
        session.update(
            username=user["username"], display_name=user["display_name"],
            role_code=user["role_code"], role_name=user["role_name"],
            auth_type=user["auth_type"], last_validation=now,
        )
    session["last_activity"] = now
    session.modified = True
    return None


def has_permission(permission_code: str) -> bool:
    user_id = session.get("user_id")
    if not user_id:
        return False
    code = permission_code.strip().upper()
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT UP.ALLOW_FLAG,
                       CASE WHEN RP.PERMISSION_ID IS NOT NULL THEN 'Y' ELSE 'N' END ROLE_ALLOW
                FROM RM_CFACT_USER U
                JOIN RM_CFACT_ROLE R ON R.ROLE_ID=U.ROLE_ID AND R.ACTIVE='Y'
                JOIN RM_CFACT_PERMISSION P ON P.PERMISSION_CODE=:code AND P.ACTIVE='Y'
                LEFT JOIN RM_CFACT_USER_PERMISSION UP
                  ON UP.USER_ID=U.USER_ID AND UP.PERMISSION_ID=P.PERMISSION_ID
                LEFT JOIN RM_CFACT_ROLE_PERMISSION RP
                  ON RP.ROLE_ID=R.ROLE_ID AND RP.PERMISSION_ID=P.PERMISSION_ID
                WHERE U.USER_ID=:user_id AND U.ACTIVE='Y'
                """,
                {"code": code, "user_id": int(user_id)},
            )
            row = cur.fetchone()
    if not row:
        return False
    if row[0] in ("Y", "N"):
        return row[0] == "Y"
    return row[1] == "Y"


def has_scope_access(scope_id: int, action: str = "VIEW") -> bool:
    user_id = session.get("user_id")
    if not user_id:
        return False
    if str(session.get("role_code", "")).upper() == "ADMIN":
        return True
    column = {
        "VIEW": "CAN_VIEW",
        "EXECUTE": "CAN_EXECUTE",
        "CONFIGURE": "CAN_CONFIGURE",
    }.get(action.strip().upper())
    if not column:
        raise ValueError("Acción de scope no soportada.")
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT US.{column}
                FROM RM_CFACT_USER_SCOPE US
                JOIN RM_CFACT_SCOPE S ON S.SCOPE_ID=US.SCOPE_ID AND S.ACTIVE='Y'
                WHERE US.USER_ID=:user_id AND US.SCOPE_ID=:scope_id
                """,
                {"user_id": int(user_id), "scope_id": int(scope_id)},
            )
            row = cur.fetchone()
    return bool(row and row[0] == "Y")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.full_path))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    allowed = {role.upper() for role in roles}
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("auth.login", next=request.full_path))
            if str(session.get("role_code", "")).upper() not in allowed:
                from flask import abort
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def permissions_required(*permissions):
    required = [item.strip().upper() for item in permissions]
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("auth.login", next=request.full_path))
            if not all(has_permission(code) for code in required):
                from flask import abort
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def scope_access_required(scope_arg: str, action: str = "VIEW"):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("user_id"):
                return redirect(url_for("auth.login", next=request.full_path))
            scope_id = kwargs.get(scope_arg)
            if scope_id is None or not has_scope_access(int(scope_id), action):
                from flask import abort
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator
