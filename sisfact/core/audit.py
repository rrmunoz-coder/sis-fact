from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class AuditEvent:
    action: str
    user_id: str | None
    module: str
    entity_type: str | None = None
    entity_id: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime = datetime.now(timezone.utc)


class AuditService:
    """Servicio base. En v0.1.0 solo define el contrato; persistencia queda para repositorio Oracle."""

    def record(self, event: AuditEvent) -> None:
        # Pendiente: persistir en SIS_AUDIT_LOG.
        return None
