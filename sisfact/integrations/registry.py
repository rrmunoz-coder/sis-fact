from __future__ import annotations

from dataclasses import dataclass, field

from sisfact.integrations.models import DataSource, SourceRole, SourceType


@dataclass
class SourceRegistry:
    sources: dict[str, DataSource] = field(default_factory=dict)

    def register(self, source: DataSource) -> None:
        self.sources[source.source_code] = source

    def get(self, source_code: str) -> DataSource:
        if source_code not in self.sources:
            raise KeyError(f"Fuente no registrada: {source_code}")
        return self.sources[source_code]

    def list_active(self) -> list[DataSource]:
        return [source for source in self.sources.values() if source.active]


def default_registry() -> SourceRegistry:
    registry = SourceRegistry()
    registry.register(DataSource("ORACLE_BILLING", "Oracle Billing", SourceType.ORACLE, SourceRole.BILLING, "oracle_billing_one", priority_order=10))
    registry.register(DataSource("MSSQL_FACT", "SQL Server FACT", SourceType.SQLSERVER, SourceRole.BILLING, "sqlserver_fact", priority_order=20))
    registry.register(DataSource("FACTURADOR_REST", "Facturador REST", SourceType.REST, SourceRole.INVOICER, "rest_default", priority_order=30))
    registry.register(DataSource("FACTURADOR_SOAP", "Facturador SOAP", SourceType.SOAP, SourceRole.INVOICER, "soap_default", priority_order=40))
    registry.register(DataSource("SII_RCV", "SII Registro de Ventas", SourceType.FILE, SourceRole.TAX, "sii_file", priority_order=50))
    registry.register(DataSource("BILLING_COMPARE", "Billing Compare", SourceType.CONTROL_ENGINE, SourceRole.CONTROL_ENGINE, "billing_compare", priority_order=60))
    return registry
