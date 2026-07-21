from __future__ import annotations

import ssl
from configparser import ConfigParser
from dataclasses import dataclass

from ldap3 import ALL, SIMPLE, Connection, Server, Tls


@dataclass(frozen=True)
class LdapResult:
    ok: bool
    server: str | None = None
    error: str | None = None


class LdapAuthenticator:
    def __init__(self, config: ConfigParser):
        self.config = config
        self.cfg = config["ldap"] if config.has_section("ldap") else {}

    @property
    def enabled(self) -> bool:
        return str(self.cfg.get("enabled", "false")).strip().lower() in {"1", "true", "yes", "s", "si", "y"}

    def status(self) -> dict[str, object]:
        servers = [s.strip() for s in self.cfg.get("servers", "").split(",") if s.strip()]
        return {
            "enabled": self.enabled,
            "servers_configured": len(servers),
            "port": int(self.cfg.get("port", "636")),
            "use_ssl": str(self.cfg.get("use_ssl", "true")).lower() == "true",
            "login_format": self.cfg.get("login_format", "UPN"),
            "domain_suffix_configured": bool(self.cfg.get("domain_suffix", "").strip()),
            "validate_certificate": str(self.cfg.get("validate_certificate", "true")).lower() == "true",
        }

    def format_login(self, username: str) -> str:
        login = username.strip()
        if "@" in login:
            return login

        login_format = self.cfg.get("login_format", "UPN").strip().upper()
        if login_format == "UPN":
            suffix = self.cfg.get("domain_suffix", "").strip()
            if not suffix:
                raise ValueError("LDAP login_format=UPN requiere domain_suffix.")
            return f"{login}@{suffix}"

        if login_format == "NETBIOS":
            netbios = self.cfg.get("netbios_domain", "").strip()
            if not netbios:
                raise ValueError("LDAP login_format=NETBIOS requiere netbios_domain.")
            return f"{netbios}\\{login}"

        return login

    def authenticate(self, username: str, password: str) -> LdapResult:
        if not self.enabled:
            return LdapResult(False, error="LDAP deshabilitado en config.ini")
        if not password:
            return LdapResult(False, error="Password vacío")

        servers = [s.strip() for s in self.cfg.get("servers", "").split(",") if s.strip()]
        if not servers:
            return LdapResult(False, error="No hay servidores LDAP configurados")

        port = int(self.cfg.get("port", "636"))
        use_ssl = str(self.cfg.get("use_ssl", "true")).strip().lower() == "true"
        validate_certificate = str(self.cfg.get("validate_certificate", "true")).strip().lower() == "true"
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
                return LdapResult(True, server=host)
            except Exception as exc:
                last_error = str(exc)

        return LdapResult(False, error=last_error or "No se pudo autenticar contra LDAP")
