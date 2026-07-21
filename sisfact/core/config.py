from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AppSettings:
    secret_key: str
    environment: str
    debug: bool
    host: str
    port: int
    raw: configparser.ConfigParser

    def to_flask_config(self) -> dict[str, Any]:
        return {
            "ENVIRONMENT": self.environment,
            "DEBUG": self.debug,
            "APP_HOST": self.host,
            "APP_PORT": self.port,
            "CONFIG_RAW": self.raw,
        }


def _bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "s", "si", "y"}


def load_config(config_path: str = "config.ini") -> AppSettings:
    parser = configparser.ConfigParser()
    path = Path(config_path)

    if path.exists():
        parser.read(path, encoding="utf-8")
    else:
        # Permite iniciar el proyecto sin config real en ambiente de desarrollo.
        parser.read_dict({
            "app": {
                "secret_key": "dev-only-change-me",
                "environment": "dev",
                "debug": "true",
                "host": "0.0.0.0",
                "port": "5060",
            }
        })

    app_cfg = parser["app"] if parser.has_section("app") else {}
    return AppSettings(
        secret_key=app_cfg.get("secret_key", "dev-only-change-me"),
        environment=app_cfg.get("environment", "dev"),
        debug=_bool(app_cfg.get("debug", "false")),
        host=app_cfg.get("host", "0.0.0.0"),
        port=int(app_cfg.get("port", "5060")),
        raw=parser,
    )
