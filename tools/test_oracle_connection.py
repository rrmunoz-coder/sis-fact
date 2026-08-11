from __future__ import annotations

import configparser
import os
from pathlib import Path

import oracledb


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path(
    os.getenv("BILLING_ONE_CONFIG", "") or PROJECT_ROOT / "config.ini"
)


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "si", "sí", "s"}


def main() -> None:
    if not CONFIG_PATH.is_file():
        raise SystemExit(f"ORACLE_ERROR no existe config: {CONFIG_PATH}")

    parser = configparser.ConfigParser()
    parser.read(CONFIG_PATH, encoding="utf-8")

    if not parser.has_section("oracle"):
        raise SystemExit(f"ORACLE_ERROR falta la sección [oracle] en {CONFIG_PATH}")

    cfg = parser["oracle"]
    user = cfg.get("user", "").strip()
    password = cfg.get("password", "")
    dsn = cfg.get("dsn", "").strip()
    thick_mode = _as_bool(cfg.get("thick_mode"), True)
    client_dir = cfg.get("client_lib_dir", "").strip()

    if not user or not password or not dsn:
        raise SystemExit("ORACLE_ERROR [oracle] requiere user, password y dsn")

    if thick_mode:
        if not client_dir:
            raise SystemExit(
                "ORACLE_ERROR thick_mode=true pero oracle.client_lib_dir está vacío"
            )
        client_path = Path(client_dir)
        if not client_path.is_dir():
            raise SystemExit(f"ORACLE_ERROR no existe Oracle Client: {client_path}")
        if not (client_path / "oci.dll").is_file():
            raise SystemExit(f"ORACLE_ERROR no se encontró OCI.DLL en {client_path}")
        try:
            oracledb.init_oracle_client(lib_dir=str(client_path))
        except oracledb.Error as exc:
            raise SystemExit(f"ORACLE_ERROR no fue posible inicializar Thick mode: {exc}")

    try:
        with oracledb.connect(user=user, password=password, dsn=dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT USER, SYSDATE FROM DUAL")
                db_user, dt = cur.fetchone()
                print(f"ORACLE_OK user={db_user} database_datetime={dt}")
    except oracledb.Error as exc:
        raise SystemExit(f"ORACLE_ERROR {exc}")


if __name__ == "__main__":
    main()
