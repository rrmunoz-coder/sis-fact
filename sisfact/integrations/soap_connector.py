from __future__ import annotations

from typing import Any, Iterable

from zeep import Client
from zeep.transports import Transport
import requests

from sisfact.integrations.base import Connector
from sisfact.integrations.models import NormalizedRecord


class SoapConnector(Connector):
    def _client(self) -> Client:
        cfg = self.config[self.data_source.connection_key]
        session = requests.Session()
        timeout = int(cfg.get("timeout_seconds", "60"))
        transport = Transport(session=session, timeout=timeout)
        return Client(wsdl=cfg.get("wsdl_url"), transport=transport)

    def healthcheck(self) -> dict[str, Any]:
        cfg = self.config[self.data_source.connection_key]
        wsdl_url = cfg.get("wsdl_url")
        if not wsdl_url:
            return {"source": self.data_source.source_code, "status": "NOT_CONFIGURED"}
        return {"source": self.data_source.source_code, "status": "CONFIGURED", "wsdl_url": wsdl_url}

    def extract(self, query_name: str, params: dict[str, Any] | None = None) -> Iterable[NormalizedRecord]:
        raise NotImplementedError("Las operaciones SOAP reales se definirán por conector de dominio.")
