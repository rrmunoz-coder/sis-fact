from __future__ import annotations

from typing import Any

from ..auth.ldap_auth import normalize_username
from ..db import connection


def list_roles() -> list[dict[str, Any]]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ROLE_ID, ROLE_CODE, ROLE_NAME FROM RM_CFACT_ROLE WHERE ACTIVE='Y' ORDER BY ROLE_NAME")
            return [{"role_id": int(r[0]), "role_code": r[1], "role_name": r[2]} for r in cur.fetchall()]


def list_scope_catalog() -> list[dict[str, Any]]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT S.SCOPE_ID, S.SCOPE_CODE, S.SCOPE_NAME, C.COMPANY_NAME,
                       I.TAX_ID, B.BUSINESS_NAME, D.DOM_CODE, CY.CYCLE_CODE
                FROM RM_CFACT_SCOPE S
                JOIN RM_CFACT_COMPANY C ON C.COMPANY_ID=S.COMPANY_ID
                LEFT JOIN RM_CFACT_ISSUER I ON I.ISSUER_ID=S.ISSUER_ID
                LEFT JOIN RM_CFACT_BUSINESS B ON B.BUSINESS_ID=S.BUSINESS_ID
                LEFT JOIN RM_CFACT_DOM D ON D.DOM_ID=S.DOM_ID
                LEFT JOIN RM_CFACT_CYCLE CY ON CY.CYCLE_ID=S.CYCLE_ID
                WHERE S.ACTIVE='Y'
                ORDER BY S.PRIORITY_ORDER, S.SCOPE_NAME, S.SCOPE_CODE
                """
            )
            rows = cur.fetchall()
    return [
        {
            "scope_id": int(r[0]), "scope_code": r[1], "scope_name": r[2],
            "company_name": r[3], "tax_id": r[4], "business_name": r[5],
            "dom_code": r[6], "cycle_code": r[7],
        }
        for r in rows
    ]


def get_user_scope_access(user_id: int) -> dict[int, dict[str, bool]]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT SCOPE_ID, CAN_VIEW, CAN_EXECUTE, CAN_CONFIGURE
                FROM RM_CFACT_USER_SCOPE
                WHERE USER_ID=:user_id
                """,
                {"user_id": user_id},
            )
            rows = cur.fetchall()
    return {
        int(r[0]): {
            "view": r[1] == "Y",
            "execute": r[2] == "Y",
            "configure": r[3] == "Y",
        }
        for r in rows
    }


def _normalized_scope_access(
    view_scope_ids: list[int],
    execute_scope_ids: list[int],
    configure_scope_ids: list[int],
) -> dict[int, tuple[str, str, str]]:
    access: dict[int, list[str]] = {}
    for scope_id in view_scope_ids:
        access.setdefault(int(scope_id), ["N", "N", "N"])[0] = "Y"
    for scope_id in execute_scope_ids:
        flags = access.setdefault(int(scope_id), ["N", "N", "N"])
        flags[0] = "Y"
        flags[1] = "Y"
    for scope_id in configure_scope_ids:
        flags = access.setdefault(int(scope_id), ["N", "N", "N"])
        flags[0] = "Y"
        flags[1] = "Y"
        flags[2] = "Y"
    return {scope_id: tuple(flags) for scope_id, flags in access.items()}


def _replace_user_scopes(
    cursor,
    user_id: int,
    view_scope_ids: list[int],
    execute_scope_ids: list[int],
    configure_scope_ids: list[int],
) -> None:
    cursor.execute("DELETE FROM RM_CFACT_USER_SCOPE WHERE USER_ID=:user_id", {"user_id": user_id})
    for scope_id, flags in _normalized_scope_access(view_scope_ids, execute_scope_ids, configure_scope_ids).items():
        cursor.execute(
            """
            INSERT INTO RM_CFACT_USER_SCOPE (
                USER_ID, SCOPE_ID, CAN_VIEW, CAN_EXECUTE, CAN_CONFIGURE
            ) VALUES (
                :user_id, :scope_id, :can_view, :can_execute, :can_configure
            )
            """,
            {
                "user_id": user_id, "scope_id": scope_id,
                "can_view": flags[0], "can_execute": flags[1], "can_configure": flags[2],
            },
        )


def list_users(query: str = "") -> list[dict[str, Any]]:
    term = f"%{query.strip().lower()}%"
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT U.USER_ID, U.USERNAME, U.DISPLAY_NAME, U.EMAIL,
                       R.ROLE_CODE, R.ROLE_NAME, A.AUTH_TYPE, U.ACTIVE,
                       NVL(A.FAILED_ATTEMPTS,0), A.LOCKED_UNTIL,
                       (SELECT COUNT(*) FROM RM_CFACT_USER_SCOPE US WHERE US.USER_ID=U.USER_ID) SCOPE_COUNT
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
            "locked_until": r[9], "scope_count": int(r[10] or 0),
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
        "scope_access": get_user_scope_access(user_id),
    }


def create_ldap_user(
    form,
    view_scope_ids: list[int],
    execute_scope_ids: list[int],
    configure_scope_ids: list[int],
) -> tuple[int, dict[str, Any]]:
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
            _replace_user_scopes(cur, user_id, view_scope_ids, execute_scope_ids, configure_scope_ids)
    return user_id, get_user(user_id) or {"user_id": user_id}


def update_user(
    user_id: int,
    form,
    view_scope_ids: list[int],
    execute_scope_ids: list[int],
    configure_scope_ids: list[int],
) -> tuple[dict[str, Any], dict[str, Any]]:
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
                UPDATE RM_CFACT_USER
                   SET DISPLAY_NAME=:name, EMAIL=:email, ROLE_ID=:role_id,
                       UPDATED_AT=SYSTIMESTAMP, UPDATED_BY='WEB_ADMIN'
                 WHERE USER_ID=:user_id
                """,
                {"name": display_name, "email": email, "role_id": int(role[0]), "user_id": user_id},
            )
            cur.execute(
                """
                UPDATE RM_CFACT_USER_AUTH
                   SET LDAP_USERNAME=:ldap_username, SESSION_VERSION=SESSION_VERSION+1,
                       UPDATED_AT=SYSTIMESTAMP
                 WHERE USER_ID=:user_id
                """,
                {"ldap_username": ldap_username, "user_id": user_id},
            )
            _replace_user_scopes(cur, user_id, view_scope_ids, execute_scope_ids, configure_scope_ids)
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
