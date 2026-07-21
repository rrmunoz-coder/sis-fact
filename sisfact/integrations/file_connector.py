from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from sisfact.integrations.base import Connector
from sisfact.integrations.models import NormalizedRecord


class FileConnector(Connector):
    def healthcheck(self) -> dict[str, Any]:
        return {"source": self.data_source.source_code, "status": "CONFIGURED"}

    def read_dataframe(self, file_path: str) -> pd.DataFrame:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(file_path)
        if path.suffix.lower() in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path, sep=None, engine="python")
        raise ValueError(f"Tipo de archivo no soportado: {path.suffix}")

    def extract(self, query_name: str, params: dict[str, Any] | None = None) -> Iterable[NormalizedRecord]:
        raise NotImplementedError("La normalización de archivos se definirá por tipo de carga.")
