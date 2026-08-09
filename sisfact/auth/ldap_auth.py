from __future__ import annotations

import ssl
from configparser import ConfigParser
from dataclasses import dataclass

from ldap3 import ALL, SIMPLE, Connection, Server, Tls


TRUE_VALUES = {"1", "true", "yes", "s", "si", "y"}


@dataclass(frozen=True)
class LdapResult:
    ok: bool
    server: str | None = None
    bind_user: str | None = None
    error: str | None = None


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in TRUE_VALUES


def normalize_username(value: str) -> str:
    """Normaliza usuario para autorizacion local.

    SIS-FACT guarda autorizacion local en RM_CFACT_USER.username sin dominio.
    El login puede llegar como usuario, usuario@dominio o DOMINIO\usuario.
    """
    username = (value or "").strip().lower()
    if "\\" in username:
        username = username.rsplit("\\", 1)[-1]
    if "@" in username:
        username = username.split("@", 1)[0]
    return username.strip()


class LdapAuthenticator:
    def __init__(self, config: ConfigParser):
        self.config = config
        self.cfg = config["ldap"] if config.has_section("ldap") else {}

    @property
    def enabled(self) -> bool:
        return _bool(self.cfg.get("enabled", "false"))

    def _servers(self) -> list[str]:
        return [s.strip() for s in self.cfg.get("servers", "").split(",") if s.strip()]

    def status(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "servers_configured": len(self._servers()),
            "port": int(self.cfg.get("port", "636")),
            "use_ssl": _bool(self.cfg.get("use_ssl", "true"), True),
            "login_format": self.cfg.get("login_format", "UPN"),
            "domain_suffix_configured": bool(self.cfg.get("domain_suffix", "").strip()),
            "netbios_domain_configured": bool(self.cfg.get("netbios_domain", "").strip()),
            "validate_certificate": _bool(self.cfg.get("validate_certificate", "true"), True),
        }

    def format_login(self, username: str) -> str:
        raw = (username or "").strip()
        if not raw:
            raise ValueError("Usuario LDAP vacio.")

        # Si viene como UPN completo, se respeta.
        if "@" in raw:
            return raw

        login_format = self.cfg.get("login_format", "UPN").strip().upper()

        # Si viene DOMINIO\usuario y el modo es NETBIOS, se respeta.
        if "\\" in raw and login_format == "NETBIOS":
            return raw

        local_user = normalize_username(raw)

        if login_format == "UPN":
            suffix = self.cfg.get("domain_suffix", "").strip()
            if not suffix:
                raise ValueError("LDAP login_format=UPN requiere domain_suffix.")
            return f"{local_user}@{suffix}"

        if login_format == "NETBIOS":
            netbios = self.cfg.get("netbios_domain", "").strip()
            if not netbios:
                raise ValueError("LDAP login_format=NETBIOS requiere netbios_domain.")
            return f"{netbios}\\{local_user}"

        return local_user

    def authenticate(self, username: str, password: str) -> LdapResult:
        if not self.enabled:
            return LdapResult(False, error="LDAP deshabilitado en config.ini")
        if not password:
            return LdapResult(False, error="Password vacio")

        servers = self._servers()
        if not servers:
            return LdapResult(False, error="No hay servidores LDAP configurados")

        port = int(self.cfg.get("port", "636"))
        use_ssl = _bool(self.cfg.get("use_ssl", "true"), True)
        validate_certificate = _bool(self.cfg.get("validate_certificate", "true"), True)
        ca_cert_file = self.cfg.get("ca_cert_file", "").strip() or None
        connect_timeout = int(self.cfg.get("connect_timeout", "5"))
        receive_timeout = int(self.cfg.get("receive_timeout", "8"))
        tls_ciphers = self.cfg.get("tls_ciphers", "").strip() or None

        tls = Tls(
            validate=ssl.CERT_REQUIRED if validate_certificate else ssl.CERT_NONE,
            ca_certs_file=ca_cert_file,
            ciphers=tls_ciphers,
        )
        bind_user = self.format_login(username)
        last_error = None

        for host in servers:
            try:
                server = Server(
                    host,
                    port=port,
                    use_ssl=use_ssl,
                    tls=tls,
                    get_info=ALL,
                    connect_timeout=connect_timeout,
                )
                conn = Connection(
                    server,
                    user=bind_user,
                    password=password,
                    authentication=SIMPLE,
                    receive_timeout=receive_timeout,
                    auto_bind=True,
                )
                conn.unbind()
                return LdapResult(True, server=host, bind_user=bind_user)
            except Exception as exc:
                last_error = str(exc)

        return LdapResult(False, bind_user=bind_user, error=last_error or "No se pudo autenticar contra LDAP")
