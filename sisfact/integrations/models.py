from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class SourceType(str, Enum):
    ORACLE = "ORACLE"
    SQLSERVER = "SQLSERVER"
    REST = "REST"
    SOAP = "SOAP"
    FILE = "FILE"
    WEBHOOK = "WEBHOOK"
    CONTROL_ENGINE = "CONTROL_ENGINE"


class SourceRole(str, Enum):
    BILLING = "BILLING"
    INVOICER = "INVOICER"
    TAX = "TAX"
    PAYMENT = "PAYMENT"
    CONTROL_ENGINE = "CONTROL_ENGINE"
    ANALYTICS = "ANALYTICS"


@dataclass(frozen=True)
class DataSource:
    source_code: str
    source_name: str
    source_type: SourceType
    system_role: SourceRole
    connection_key: str
    active: bool = True
    priority_order: int = 100
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionRun:
    data_source: DataSource
    extraction_type: str
    period: str | None = None
    flow_code: str | None = None
    scope_code: str | None = None
    execution_code: str | None = None
    status: str = "CREATED"
    rows_read: int = 0
    rows_loaded: int = 0
    rows_rejected: int = 0
    error_message: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None


@dataclass(frozen=True)
class NormalizedRecord:
    source_system: str
    source_table: str | None
    source_record_id: str
    issuer_tax_id: str | None
    business_code: str | None
    flow_code: str | None
    scope_code: str | None
    billing_period: str | None
    execution_code: str | None
    customer_id: str | None
    account_id: str | None
    document_type: str | None
    document_number: str | None
    issue_date: str | None
    net_amount: float | None
    tax_amount: float | None
    total_amount: float | None
    raw: dict[str, Any]
