from __future__ import annotations

from typing import Any

from ..auth.ldap_auth import normalize_username
from ..db import connection


def list_roles() -> list[dict[str, Any]]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ROLE_ID, ROLE_CODE, ROLE_NAME FROM RM_CFACT_ROLE WHERE ACTIVE='Y' ORDER BY ROLE_NAME")
            return [
                {"role_id": int(r[0]), "role_code": r[1], "role_name": r[2]}
                for r in cur.fetchall()
            ]


def list_users(query: str = "") -> list[dict[str, Any]]:
    term = f"%{query.strip().lower()}%"
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT U.USER_ID, U.USERNAME, U.DISPLAY_NAME, U.EMAIL,
                       R.ROLE_CODE, R.ROLE_NAME, A.AUTH_TYPE, U.ACTIVE,
                       NVL(A.FAILED_ATTEMPTS,0), A.LOCKED_UNTIL
                FROM RM_CFACT_USER U
                JOIN RM_CFACT_ROLE R ON R.ROLE_ID=U.ROLE_ID
                JOIN RM_CFACT_USER_AUTH A ON A.USER_ID=U.USER_ID
                WHERE (:q='%%' OR LOWER(U.USERNAME) LIKE :q OR LOWER(U.DISPLAY_NAME) LIKE :q)
                ORDER BY U.DISPLAY_NAME, U.USERNAME
                """,
                {"q": term},
            )
            rows = cur.fetchall()
    return [
        {
            "user_id": int(r[0]), "username": r[1], "display_name": r[2],
            "email": r[3], "role_code": r[4], "role_name": r[5],
            "auth_type": r[6], "active": r[7], "failed_attempts": int(r[8] or 0),
            "locked_until": r[9],
        }
        for r in rows
    ]


def get_user(user_id: int) -> dict[str, Any] | None:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT U.USER_ID, U.USERNAME, U.DISPLAY_NAME, U.EMAIL, U.ROLE_ID,
                       R.ROLE_CODE, A.AUTH_TYPE, A.LDAP_USERNAME, U.ACTIVE
                FROM RM_CFACT_USER U
                JOIN RM_CFACT_ROLE R ON R.ROLE_ID=U.ROLE_ID
                JOIN RM_CFACT_USER_AUTH A ON A.USER_ID=U.USER_ID
                WHERE U.USER_ID=:user_id
                """,
                {"user_id": user_id},
            )
            row = cur.fetchone()
    if not row:
        return None
    return {
        "user_id": int(row[0]), "username": row[1], "display_name": row[2],
        "email": row[3], "role_id": int(row[4]), "role_code": row[5],
        "auth_type": row[6], "ldap_username": row[7], "active": row[8],
    }


def create_ldap_user(form) -> tuple[int, dict[str, Any]]:
    username = normalize_username(form.get("username"))
    display_name = (form.get("display_name") or "").strip()
    email = (form.get("email") or "").strip() or None
    role_code = (form.get("role_code") or "VIEWER").strip().upper()
    ldap_username = (form.get("ldap_username") or "").strip() or username

    if not username or not display_name:
        raise ValueError("Usuario y nombre son obligatorios.")

    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ROLE_ID FROM RM_CFACT_ROLE WHERE ROLE_CODE=:code AND ACTIVE='Y'", {"code": role_code})
            role = cur.fetchone()
            if not role:
                raise ValueError("Rol no válido o inactivo.")
            cur.execute(
                """
                INSERT INTO RM_CFACT_USER (
                    USERNAME, DISPLAY_NAME, EMAIL, ROLE_ID, ACTIVE, CREATED_BY
                ) VALUES (
                    :username, :display_name, :email, :role_id, 'Y', 'WEB_ADMIN'
                )
                """,
                {"username": username, "display_name": display_name, "email": email, "role_id": int(role[0])},
            )
            cur.execute("SELECT USER_ID FROM RM_CFACT_USER WHERE LOWER(USERNAME)=LOWER(:username)", {"username": username})
            user_id = int(cur.fetchone()[0])
            cur.execute(
                """
                INSERT INTO RM_CFACT_USER_AUTH (
                    USER_ID, AUTH_TYPE, LDAP_USERNAME, SESSION_VERSION, FAILED_ATTEMPTS
                ) VALUES (:user_id, 'LDAP', :ldap_username, 1, 0)
                """,
                {"user_id": user_id, "ldap_username": ldap_username},
            )
    return user_id, get_user(user_id) or {"user_id": user_id}


def update_user(user_id: int, form) -> tuple[dict[str, Any], dict[str, Any]]:
    before = get_user(user_id)
    if not before:
        raise ValueError("Usuario no existe.")
    display_name = (form.get("display_name") or "").strip()
    email = (form.get("email") or "").strip() or None
    role_code = (form.get("role_code") or "").strip().upper()
    ldap_username = (form.get("ldap_username") or "").strip() or before["username"]
    if not display_name or not role_code:
        raise ValueError("Nombre y rol son obligatorios.")

    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ROLE_ID FROM RM_CFACT_ROLE WHERE ROLE_CODE=:code AND ACTIVE='Y'", {"code": role_code})
            role = cur.fetchone()
            if not role:
                raise ValueError("Rol no válido o inactivo.")
            cur.execute(
                """
                UPDATE RM_CFACT_USER SET DISPLAY_NAME=:name, EMAIL=:email, ROLE_ID=:role_id,
                       UPDATED_AT=SYSTIMESTAMP, UPDATED_BY='WEB_ADMIN'
                WHERE USER_ID=:user_id
                """,
                {"name": display_name, "email": email, "role_id": int(role[0]), "user_id": user_id},
            )
            cur.execute(
                """
                UPDATE RM_CFACT_USER_AUTH SET LDAP_USERNAME=:ldap_username,
                       SESSION_VERSION=SESSION_VERSION+1, UPDATED_AT=SYSTIMESTAMP
                WHERE USER_ID=:user_id
                """,
                {"ldap_username": ldap_username, "user_id": user_id},
            )
    return before, get_user(user_id) or before


def set_user_status(user_id: int, active: str) -> tuple[dict[str, Any], dict[str, Any]]:
    before = get_user(user_id)
    if not before:
        raise ValueError("Usuario no existe.")
    value = "Y" if str(active).upper() == "Y" else "N"
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE RM_CFACT_USER SET ACTIVE=:active, UPDATED_AT=SYSTIMESTAMP WHERE USER_ID=:user_id", {"active": value, "user_id": user_id})
            cur.execute("UPDATE RM_CFACT_USER_AUTH SET SESSION_VERSION=SESSION_VERSION+1, UPDATED_AT=SYSTIMESTAMP WHERE USER_ID=:user_id", {"user_id": user_id})
    return before, get_user(user_id) or before


def reset_failed_attempts(user_id: int) -> None:
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE RM_CFACT_USER_AUTH
                   SET FAILED_ATTEMPTS=0, LOCKED_UNTIL=NULL, UPDATED_AT=SYSTIMESTAMP
                 WHERE USER_ID=:user_id
                """,
                {"user_id": user_id},
            )
