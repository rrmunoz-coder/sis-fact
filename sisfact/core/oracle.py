from __future__ import annotations

from configparser import ConfigParser
from threading import Lock
from typing import Any

import oracledb

_CLIENT_LOCK = Lock()
_CLIENT_INITIALIZED = False
_POOL: oracledb.ConnectionPool | None = None
_POOL_LOCK = Lock()


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "s", "si", "y"}


def _init_client_if_needed(cfg: Any) -> None:
    global _CLIENT_INITIALIZED
    thick_mode = _bool(cfg.get("thick_mode", "false"))
    client_lib_dir = cfg.get("client_lib_dir", "").strip()

    if not thick_mode:
        return

    with _CLIENT_LOCK:
        if _CLIENT_INITIALIZED:
            return
        if client_lib_dir:
            oracledb.init_oracle_client(lib_dir=client_lib_dir)
        else:
            oracledb.init_oracle_client()
        _CLIENT_INITIALIZED = True


def get_oracle_config(config: ConfigParser, section: str = "oracle"):
    if config.has_section(section):
        return config[section]
    if config.has_section("oracle_billing_one"):
        # Compatibilidad con la primera versión del repositorio.
        return config["oracle_billing_one"]
    raise KeyError("No existe configuración Oracle. Se esperaba sección [oracle].")


def build_dsn(cfg: Any) -> str:
    dsn = cfg.get("dsn", "").strip()
    if dsn:
        return dsn
    host = cfg.get("host", "").strip()
    port = int(cfg.get("port", "1521"))
    service_name = cfg.get("service_name", "").strip()
    if not host or not service_name:
        raise ValueError("Config Oracle incompleta: definir dsn o host/port/service_name.")
    return oracledb.makedsn(host, port, service_name=service_name)


def connect(config: ConfigParser, section: str = "oracle"):
    cfg = get_oracle_config(config, section)
    _init_client_if_needed(cfg)
    return oracledb.connect(
        user=cfg.get("user"),
        password=cfg.get("password"),
        dsn=build_dsn(cfg),
    )


def get_pool(config: ConfigParser, section: str = "oracle") -> oracledb.ConnectionPool:
    global _POOL
    cfg = get_oracle_config(config, section)
    _init_client_if_needed(cfg)

    with _POOL_LOCK:
        if _POOL is None:
            _POOL = oracledb.create_pool(
                user=cfg.get("user"),
                password=cfg.get("password"),
                dsn=build_dsn(cfg),
                min=int(cfg.get("pool_min", "1")),
                max=int(cfg.get("pool_max", "8")),
                increment=int(cfg.get("pool_increment", "1")),
            )
        return _POOL
