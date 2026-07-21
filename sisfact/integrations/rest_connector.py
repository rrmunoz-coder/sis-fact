from __future__ import annotations

from typing import Any, Iterable

import requests

from sisfact.integrations.base import Connector
from sisfact.integrations.models import NormalizedRecord


class RestConnector(Connector):
    def _base_url(self) -> str:
        return self.config[self.data_source.connection_key].get("base_url")

    def healthcheck(self) -> dict[str, Any]:
        base_url = self._base_url()
        if not base_url:
            return {"source": self.data_source.source_code, "status": "NOT_CONFIGURED"}
        return {"source": self.data_source.source_code, "status": "CONFIGURED", "base_url": base_url}

    def get_json(self, resource: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        cfg = self.config[self.data_source.connection_key]
        timeout = int(cfg.get("timeout_seconds", "30"))
        response = requests.get(f"{self._base_url().rstrip('/')}/{resource.lstrip('/')}", params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()

    def extract(self, query_name: str, params: dict[str, Any] | None = None) -> Iterable[NormalizedRecord]:
        raise NotImplementedError("Los recursos REST reales se definirán por conector de dominio.")
