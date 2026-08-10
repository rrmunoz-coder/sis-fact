from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import ssl

from flask import current_app
from ldap3 import Connection, NONE, NTLM, SIMPLE, Server, Tls
from ldap3.core.exceptions import LDAPException


class LDAPStatus(str, Enum):
    SUCCESS = "SUCCESS"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    UNAVAILABLE = "UNAVAILABLE"
    CONFIG_ERROR = "CONFIG_ERROR"


@dataclass(frozen=True)
class LDAPResult:
    status: LDAPStatus
    detail: str | None = None


def normalize_username(value: str | None) -> str:
    username = (value or "").strip()
    if "\\" in username:
        username = username.rsplit("\\", 1)[-1]
    if "@" in username:
        username = username.split("@", 1)[0]
    return username.strip().lower()


def _build_login(ldap_username: str) -> str:
    value = ldap_username.strip()
    if not value:
        raise ValueError("LDAP_USERNAME vacío")

    if "@" in value or "\\" in value or "=" in value:
        return value

    login_format = current_app.config["LDAP_LOGIN_FORMAT"]
    if login_format == "UPN":
        suffix = current_app.config["LDAP_DOMAIN_SUFFIX"]
        if not suffix:
            raise ValueError("ldap.domain_suffix es obligatorio para login_format=UPN")
        return f"{value}@{suffix}"
    if login_format == "NTLM":
        domain = current_app.config["LDAP_NETBIOS_DOMAIN"]
        if not domain:
            raise ValueError("ldap.netbios_domain es obligatorio para login_format=NTLM")
        return f"{domain}\\{value}"
    if login_format in ("RAW", "AS_ENTERED"):
        return value
    raise ValueError(f"ldap.login_format no soportado: {login_format}")


def _detail(conn: Connection | None) -> str:
    if conn is None:
        return "sin conexión"
    parts: list[str] = []
    if conn.last_error:
        parts.append(f"last_error={conn.last_error}")
    if conn.result:
        parts.append(
            "result="
            f"{conn.result.get('result')}, "
            f"description={conn.result.get('description')}, "
            f"message={conn.result.get('message')}"
        )
    return " | ".join(parts) or "sin detalle entregado por ldap3"


def authenticate_ldap(ldap_username: str, password: str) -> LDAPResult:
    if not current_app.config["LDAP_ENABLED"]:
        return LDAPResult(LDAPStatus.CONFIG_ERROR, "LDAP deshabilitado")
    servers = current_app.config["LDAP_SERVERS"]
    if not servers:
        return LDAPResult(LDAPStatus.CONFIG_ERROR, "Sin servidores LDAP configurados")

    use_ssl = current_app.config["LDAP_USE_SSL"]
    start_tls = current_app.config["LDAP_START_TLS"]
    auth_name = current_app.config["LDAP_AUTHENTICATION"]

    if use_ssl and start_tls:
        return LDAPResult(LDAPStatus.CONFIG_ERROR, "use_ssl y start_tls no pueden estar activos simultáneamente")
    if auth_name == "SIMPLE" and not use_ssl and not start_tls:
        return LDAPResult(LDAPStatus.CONFIG_ERROR, "SIMPLE bind requiere LDAPS o StartTLS")

    try:
        bind_user = _build_login(ldap_username)
    except ValueError as exc:
        return LDAPResult(LDAPStatus.CONFIG_ERROR, str(exc))

    if auth_name == "SIMPLE":
        authentication = SIMPLE
    elif auth_name == "NTLM":
        authentication = NTLM
    else:
        return LDAPResult(LDAPStatus.CONFIG_ERROR, f"authentication no soportado: {auth_name}")

    validate = ssl.CERT_REQUIRED if current_app.config["LDAP_VALIDATE_CERTIFICATE"] else ssl.CERT_NONE
    ca_cert_file = current_app.config["LDAP_CA_CERT_FILE"] or None
    tls_ciphers = current_app.config.get("LDAP_TLS_CIPHERS", "").strip() or None
    tls = Tls(validate=validate, ca_certs_file=ca_cert_file, ciphers=tls_ciphers)

    details: list[str] = []
    for host in servers:
        conn: Connection | None = None
        try:
            server = Server(
                host,
                port=current_app.config["LDAP_PORT"],
                use_ssl=use_ssl,
                tls=tls,
                get_info=NONE,
                connect_timeout=current_app.config["LDAP_CONNECT_TIMEOUT"],
            )
            conn = Connection(
                server,
                user=bind_user,
                password=password,
                authentication=authentication,
                receive_timeout=current_app.config["LDAP_RECEIVE_TIMEOUT"],
                raise_exceptions=False,
            )
            if start_tls:
                conn.open()
                if conn.closed:
                    details.append(f"{host}: OPEN falló: {_detail(conn)}")
                    continue
                if not conn.start_tls():
                    details.append(f"{host}: STARTTLS falló: {_detail(conn)}")
                    continue
            if conn.bind():
                return LDAPResult(LDAPStatus.SUCCESS)

            result_code = int((conn.result or {}).get("result", -1))
            if result_code == 49:
                return LDAPResult(
                    LDAPStatus.INVALID_CREDENTIALS,
                    f"{host}: credenciales rechazadas: {_detail(conn)}",
                )
            details.append(f"{host}: BIND falló: {_detail(conn)}")
        except LDAPException as exc:
            details.append(f"{host}: {type(exc).__name__}: {exc}")
        except (OSError, ssl.SSLError) as exc:
            details.append(f"{host}: {type(exc).__name__}: {exc}")
        except Exception as exc:
            details.append(f"{host}: {type(exc).__name__}: {exc}")
        finally:
            if conn is not None:
                try:
                    conn.unbind()
                except Exception:
                    pass

    return LDAPResult(LDAPStatus.UNAVAILABLE, "; ".join(details) or "LDAP no disponible")


def ldap_status() -> dict:
    return {
        "enabled": bool(current_app.config.get("LDAP_ENABLED")),
        "servers_configured": len(current_app.config.get("LDAP_SERVERS", [])),
        "port": current_app.config.get("LDAP_PORT"),
        "use_ssl": bool(current_app.config.get("LDAP_USE_SSL")),
        "start_tls": bool(current_app.config.get("LDAP_START_TLS")),
        "validate_certificate": bool(current_app.config.get("LDAP_VALIDATE_CERTIFICATE")),
        "authentication": current_app.config.get("LDAP_AUTHENTICATION"),
        "login_format": current_app.config.get("LDAP_LOGIN_FORMAT"),
    }
