from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass

from werkzeug.security import check_password_hash

from sisfact.auth.ldap_auth import LdapAuthenticator
from sisfact.auth.models import SisFactUser
from sisfact.auth.user_repository import UserRepository


@dataclass(frozen=True)
class AuthResult:
    ok: bool
    user: SisFactUser | None = None
    message: str = ""


class AuthService:
    def __init__(self, config: ConfigParser):
        self.config = config
        self.users = UserRepository(config)
        self.ldap = LdapAuthenticator(config)

    def login(self, username: str, password: str) -> AuthResult:
        normalized = username.strip().lower()
        if not normalized or not password:
            return AuthResult(False, message="Usuario y password son obligatorios")

        user = self.users.find_by_username(normalized)
        if not user:
            return AuthResult(False, message="Usuario no registrado en SIS-FACT")
        if not user.active:
            return AuthResult(False, message="Usuario inactivo en SIS-FACT")

        auth_type = user.auth_type.upper()
        if auth_type == "LDAP":
            ldap_result = self.ldap.authenticate(normalized, password)
            if not ldap_result.ok:
                return AuthResult(False, message=f"LDAP rechazó el login: {ldap_result.error}")
            return AuthResult(True, user=user, message="Login LDAP OK")

        if auth_type == "LOCAL":
            password_hash = self.users.get_password_hash(normalized)
            if not password_hash:
                return AuthResult(False, message="Usuario local sin password configurada")
            if not check_password_hash(password_hash, password):
                return AuthResult(False, message="Password local inválida")
            return AuthResult(True, user=user, message="Login local OK")

        return AuthResult(False, message=f"Tipo de autenticación no soportado: {auth_type}")
