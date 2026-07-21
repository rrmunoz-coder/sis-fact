from __future__ import annotations

from typing import Any, Iterable

import oracledb

from sisfact.integrations.base import Connector
from sisfact.integrations.models import NormalizedRecord


class OracleConnector(Connector):
    def _connect(self):
        cfg = self.config[self.data_source.connection_key]
        dsn = oracledb.makedsn(cfg.get("host"), int(cfg.get("port", "1521")), service_name=cfg.get("service_name"))
        return oracledb.connect(user=cfg.get("user"), password=cfg.get("password"), dsn=dsn)

    def healthcheck(self) -> dict[str, Any]:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM DUAL")
                    value = cur.fetchone()[0]
            return {"source": self.data_source.source_code, "status": "OK", "value": value}
        except Exception as exc:
            return {"source": self.data_source.source_code, "status": "ERROR", "error": str(exc)}

    def extract(self, query_name: str, params: dict[str, Any] | None = None) -> Iterable[NormalizedRecord]:
        raise NotImplementedError("Las consultas Oracle reales se definirán por repositorio de dominio.")
