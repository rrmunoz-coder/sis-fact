from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from flask import current_app
from werkzeug.security import check_password_hash

from ..db import connection
from .ldap_auth import LDAPStatus, authenticate_ldap, normalize_username


class AuthStatus(str, Enum):
    SUCCESS = "SUCCESS"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"
    CONFIG_ERROR = "CONFIG_ERROR"
    LOCKED = "LOCKED"


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: int
    username: str
    display_name: str
    role_code: str
    role_name: str
    auth_type: str
    session_version: int


@dataclass(frozen=True)
class AuthResult:
    status: AuthStatus
    user: AuthenticatedUser | None = None
    technical_detail: str | None = None


def _load_user(username: str):
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    U.USER_ID,
                    U.USERNAME,
                    U.PASSWORD_HASH,
                    U.DISPLAY_NAME,
                    R.ROLE_CODE,
                    R.ROLE_NAME,
                    A.AUTH_TYPE,
                    A.LDAP_USERNAME,
                    NVL(A.SESSION_VERSION, 1),
                    CASE WHEN A.LOCKED_UNTIL > SYSTIMESTAMP THEN 'Y' ELSE 'N' END,
                    NVL(A.FAILED_ATTEMPTS, 0)
                FROM RM_CFACT_USER U
                JOIN RM_CFACT_ROLE R ON R.ROLE_ID = U.ROLE_ID
                JOIN RM_CFACT_USER_AUTH A ON A.USER_ID = U.USER_ID
                WHERE LOWER(U.USERNAME) = LOWER(:username)
                  AND U.ACTIVE = 'Y'
                  AND R.ACTIVE = 'Y'
                """,
                {"username": normalize_username(username)},
            )
            return cur.fetchone()


def _record_success(user_id: int) -> None:
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE RM_CFACT_USER_AUTH
                   SET LAST_LOGIN_SUCCESS = SYSTIMESTAMP,
                       FAILED_ATTEMPTS = 0,
                       LOCKED_UNTIL = NULL,
                       UPDATED_AT = SYSTIMESTAMP
                 WHERE USER_ID = :user_id
                """,
                {"user_id": user_id},
            )


def _record_failure(user_id: int) -> None:
    max_attempts = int(current_app.config.get("MAX_FAILED_LOGINS", 5))
    lock_minutes = int(current_app.config.get("LOGIN_LOCK_MINUTES", 15))
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE RM_CFACT_USER_AUTH
                   SET LAST_LOGIN_FAILURE = SYSTIMESTAMP,
                       FAILED_ATTEMPTS = NVL(FAILED_ATTEMPTS, 0) + 1,
                       LOCKED_UNTIL = CASE
                           WHEN NVL(FAILED_ATTEMPTS, 0) + 1 >= :max_attempts
                           THEN SYSTIMESTAMP + NUMTODSINTERVAL(:lock_minutes, 'MINUTE')
                           ELSE LOCKED_UNTIL
                       END,
                       UPDATED_AT = SYSTIMESTAMP
                 WHERE USER_ID = :user_id
                """,
                {
                    "user_id": user_id,
                    "max_attempts": max_attempts,
                    "lock_minutes": lock_minutes,
                },
            )


def _normalize_origin_ip(origin_ip: str | None) -> str:
    value = (origin_ip or "UNKNOWN").strip()
    return value[:64] or "UNKNOWN"


def _ip_is_blocked(origin_ip: str | None) -> bool:
    value = _normalize_origin_ip(origin_ip)
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT CASE WHEN LOCKED_UNTIL > SYSTIMESTAMP THEN 'Y' ELSE 'N' END
                FROM RM_CFACT_LOGIN_RATE_LIMIT
                WHERE ORIGIN_IP = :origin_ip
                """,
                {"origin_ip": value},
            )
            row = cur.fetchone()
    return bool(row and str(row[0]).upper() == "Y")


def _record_ip_failure(origin_ip: str | None) -> None:
    value = _normalize_origin_ip(origin_ip)
    max_attempts = int(current_app.config.get("MAX_FAILED_LOGINS_IP", 20))
    window_minutes = int(current_app.config.get("LOGIN_RATE_WINDOW_MINUTES", 15))
    lock_minutes = int(current_app.config.get("LOGIN_LOCK_MINUTES", 15))
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                MERGE INTO RM_CFACT_LOGIN_RATE_LIMIT L
                USING (SELECT :origin_ip AS ORIGIN_IP FROM DUAL) S
                   ON (L.ORIGIN_IP = S.ORIGIN_IP)
                WHEN MATCHED THEN UPDATE SET
                    L.FAILED_ATTEMPTS = CASE
                        WHEN L.WINDOW_STARTED_AT < SYSTIMESTAMP - NUMTODSINTERVAL(:window_minutes, 'MINUTE')
                        THEN 1 ELSE NVL(L.FAILED_ATTEMPTS, 0) + 1 END,
                    L.WINDOW_STARTED_AT = CASE
                        WHEN L.WINDOW_STARTED_AT < SYSTIMESTAMP - NUMTODSINTERVAL(:window_minutes, 'MINUTE')
                        THEN SYSTIMESTAMP ELSE L.WINDOW_STARTED_AT END,
                    L.LOCKED_UNTIL = CASE
                        WHEN (CASE
                            WHEN L.WINDOW_STARTED_AT < SYSTIMESTAMP - NUMTODSINTERVAL(:window_minutes, 'MINUTE')
                            THEN 1 ELSE NVL(L.FAILED_ATTEMPTS, 0) + 1 END) >= :max_attempts
                        THEN SYSTIMESTAMP + NUMTODSINTERVAL(:lock_minutes, 'MINUTE')
                        ELSE L.LOCKED_UNTIL END,
                    L.UPDATED_AT = SYSTIMESTAMP
                WHEN NOT MATCHED THEN INSERT (
                    ORIGIN_IP, FAILED_ATTEMPTS, WINDOW_STARTED_AT, UPDATED_AT
                ) VALUES (
                    :origin_ip, 1, SYSTIMESTAMP, SYSTIMESTAMP
                )
                """,
                {
                    "origin_ip": value,
                    "window_minutes": window_minutes,
                    "max_attempts": max_attempts,
                    "lock_minutes": lock_minutes,
                },
            )


def _record_ip_success(origin_ip: str | None) -> None:
    value = _normalize_origin_ip(origin_ip)
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM RM_CFACT_LOGIN_RATE_LIMIT WHERE ORIGIN_IP = :origin_ip",
                {"origin_ip": value},
            )


def authenticate(username: str, password: str, origin_ip: str | None = None) -> AuthResult:
    if _ip_is_blocked(origin_ip):
        return AuthResult(AuthStatus.LOCKED)

    lookup = normalize_username(username)
    if not lookup or not password:
        return AuthResult(AuthStatus.INVALID)

    row = _load_user(lookup)
    if not row:
        _record_ip_failure(origin_ip)
        return AuthResult(AuthStatus.INVALID)

    user_id = int(row[0])
    auth_type = str(row[6] or "").upper()
    if str(row[9] or "N").upper() == "Y":
        return AuthResult(AuthStatus.LOCKED)

    if auth_type == "LOCAL":
        password_hash = row[2]
        if not password_hash or not check_password_hash(password_hash, password):
            _record_failure(user_id)
            _record_ip_failure(origin_ip)
            return AuthResult(AuthStatus.INVALID)
    elif auth_type == "LDAP":
        ldap_username = row[7] or username
        ldap_result = authenticate_ldap(str(ldap_username), password)
        if ldap_result.status == LDAPStatus.INVALID_CREDENTIALS:
            _record_failure(user_id)
            _record_ip_failure(origin_ip)
            return AuthResult(AuthStatus.INVALID)
        if ldap_result.status == LDAPStatus.UNAVAILABLE:
            return AuthResult(AuthStatus.UNAVAILABLE, technical_detail=ldap_result.detail)
        if ldap_result.status == LDAPStatus.CONFIG_ERROR:
            return AuthResult(AuthStatus.CONFIG_ERROR, technical_detail=ldap_result.detail)
    else:
        return AuthResult(
            AuthStatus.CONFIG_ERROR,
            technical_detail=f"AUTH_TYPE no soportado: {auth_type}",
        )

    _record_success(user_id)
    _record_ip_success(origin_ip)
    return AuthResult(
        AuthStatus.SUCCESS,
        user=AuthenticatedUser(
            user_id=user_id,
            username=row[1],
            display_name=row[3],
            role_code=row[4],
            role_name=row[5],
            auth_type=auth_type,
            session_version=int(row[8] or 1),
        ),
    )
