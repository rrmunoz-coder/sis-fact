from pathlib import Path
import ssl
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ldap3 import Connection, NONE, Server, Tls
from sisfact import create_app


def main():
    app = create_app()
    with app.app_context():
        cfg = app.config
        validate = ssl.CERT_REQUIRED if cfg["LDAP_VALIDATE_CERTIFICATE"] else ssl.CERT_NONE
        tls = Tls(
            validate=validate,
            ca_certs_file=cfg["LDAP_CA_CERT_FILE"] or None,
            ciphers=cfg.get("LDAP_TLS_CIPHERS") or None,
        )
        errors = []
        for host in cfg["LDAP_SERVERS"]:
            conn = None
            try:
                server = Server(
                    host,
                    port=cfg["LDAP_PORT"],
                    use_ssl=cfg["LDAP_USE_SSL"],
                    tls=tls,
                    get_info=NONE,
                    connect_timeout=cfg["LDAP_CONNECT_TIMEOUT"],
                )
                conn = Connection(server, receive_timeout=cfg["LDAP_RECEIVE_TIMEOUT"], raise_exceptions=False)
                conn.open()
                if conn.closed:
                    raise RuntimeError(conn.last_error or "socket cerrado")
                if cfg["LDAP_START_TLS"] and not conn.start_tls():
                    raise RuntimeError(conn.last_error or "STARTTLS fallo")
                print(f"LDAP_TRANSPORT_OK host={host} port={cfg['LDAP_PORT']}")
            except Exception as exc:
                errors.append(f"{host}: {type(exc).__name__}: {exc}")
            finally:
                if conn is not None:
                    try:
                        conn.unbind()
                    except Exception:
                        pass
        if errors:
            raise SystemExit("LDAP_TRANSPORT_ERROR " + "; ".join(errors))


if __name__ == "__main__":
    main()
