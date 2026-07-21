from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutiveSnapshot:
    billed_amount: float
    foliated_amount: float
    distributed_amount: float
    credited_amount: float
    collected_amount: float
    blocked_amount: float
    open_cases: int


class ReportingService:
    def executive_snapshot(self) -> ExecutiveSnapshot:
        # Placeholder determinístico para validar API y vistas antes de conectar datos reales.
        return ExecutiveSnapshot(
            billed_amount=0,
            foliated_amount=0,
            distributed_amount=0,
            credited_amount=0,
            collected_amount=0,
            blocked_amount=0,
            open_cases=0,
        )
