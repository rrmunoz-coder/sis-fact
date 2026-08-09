from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass

from werkzeug.security import check_password_hash

from sisfact.auth.ldap_auth import LdapAuthenticator, normalize_username
from sisfact.auth.models import SisFactUser
from sisfact.auth.user_repository import UserRepository


@dataclass(frozen=True)
class AuthResult:
    ok: bool
    user: SisFactUser | None = None
    message: str = ""
    code: str = ""


class AuthService:
    def __init__(self, config: ConfigParser):
        self.config = config
        self.users = UserRepository(config)
        self.ldap = LdapAuthenticator(config)

    def login(self, username: str, password: str) -> AuthResult:
        lookup_username = normalize_username(username)
        if not lookup_username or not password:
            return AuthResult(False, message="Usuario y password son obligatorios", code="MISSING_CREDENTIALS")

        try:
            user = self.users.find_by_username(username)
        except Exception as exc:
            return AuthResult(False, message=f"No fue posible validar usuario en Oracle: {exc}", code="ORACLE_ERROR")

        if not user:
            return AuthResult(False, message="Usuario no registrado en SIS-FACT", code="USER_NOT_REGISTERED")
        if not user.active:
            return AuthResult(False, message="Usuario inactivo en SIS-FACT", code="USER_INACTIVE")

        auth_type = user.auth_type.upper()
        if auth_type == "LDAP":
            ldap_result = self.ldap.authenticate(username, password)
            if not ldap_result.ok:
                return AuthResult(False, message=f"LDAP rechazo el login: {ldap_result.error}", code="LDAP_REJECTED")
            return AuthResult(True, user=user, message="Login LDAP OK", code="OK")

        if auth_type == "LOCAL":
            try:
                password_hash = self.users.get_password_hash(lookup_username)
            except Exception as exc:
                return AuthResult(False, message=f"No fue posible leer password local: {exc}", code="ORACLE_ERROR")
            if not password_hash:
                return AuthResult(False, message="Usuario local sin password configurada", code="LOCAL_WITHOUT_PASSWORD")
            if not check_password_hash(password_hash, password):
                return AuthResult(False, message="Password local invalida", code="LOCAL_PASSWORD_INVALID")
            return AuthResult(True, user=user, message="Login local OK", code="OK")

        return AuthResult(False, message=f"Tipo de autenticacion no soportado: {auth_type}", code="AUTH_TYPE_UNSUPPORTED")
