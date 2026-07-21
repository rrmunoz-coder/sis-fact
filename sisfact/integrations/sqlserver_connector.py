from __future__ import annotations

from typing import Any, Iterable

import pyodbc

from sisfact.integrations.base import Connector
from sisfact.integrations.models import NormalizedRecord


class SqlServerConnector(Connector):
    def _connection_string(self) -> str:
        cfg = self.config[self.data_source.connection_key]
        return (
            f"DRIVER={{{cfg.get('driver')}}};"
            f"SERVER={cfg.get('server')};"
            f"DATABASE={cfg.get('database')};"
            f"UID={cfg.get('user')};"
            f"PWD={cfg.get('password')};"
            f"Encrypt={cfg.get('encrypt', 'no')};"
            f"TrustServerCertificate={cfg.get('trust_server_certificate', 'yes')};"
        )

    def _connect(self):
        return pyodbc.connect(self._connection_string(), timeout=30)

    def healthcheck(self) -> dict[str, Any]:
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                value = cur.fetchone()[0]
            return {"source": self.data_source.source_code, "status": "OK", "value": value}
        except Exception as exc:
            return {"source": self.data_source.source_code, "status": "ERROR", "error": str(exc)}

    def extract(self, query_name: str, params: dict[str, Any] | None = None) -> Iterable[NormalizedRecord]:
        raise NotImplementedError("Las consultas SQL Server reales se definirán por repositorio de dominio.")
