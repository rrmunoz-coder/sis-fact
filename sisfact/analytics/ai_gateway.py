from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AIRequest:
    task: str
    context: dict[str, Any]
    prompt: str


@dataclass(frozen=True)
class AIResponse:
    provider: str
    status: str
    content: str
    metadata: dict[str, Any]


class AIGateway:
    """Contrato para encapsular IA local o externa.

    La versión v0.1.0 no llama modelos reales. El objetivo es dejar desacoplada
    la reportería/analítica de la solución IA elegida.
    """

    def __init__(self, provider: str = "disabled"):
        self.provider = provider

    def is_enabled(self) -> bool:
        return self.provider not in {"", "disabled", "none"}

    def analyze(self, request: AIRequest) -> AIResponse:
        if not self.is_enabled():
            return AIResponse(
                provider=self.provider,
                status="DISABLED",
                content="IA no configurada. Se utilizará analítica determinística.",
                metadata={"task": request.task},
            )
        raise NotImplementedError("Implementar proveedor local o externo en versión posterior.")
