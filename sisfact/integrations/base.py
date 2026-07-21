from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable

from sisfact.integrations.models import DataSource, NormalizedRecord


class Connector(ABC):
    def __init__(self, data_source: DataSource, config: Any):
        self.data_source = data_source
        self.config = config

    @abstractmethod
    def healthcheck(self) -> dict[str, Any]:
        """Retorna estado técnico de la fuente."""

    @abstractmethod
    def extract(self, query_name: str, params: dict[str, Any] | None = None) -> Iterable[NormalizedRecord]:
        """Extrae datos normalizados desde la fuente."""
