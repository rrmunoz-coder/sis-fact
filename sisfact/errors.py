from __future__ import annotations

from flask import flash, g


def request_id() -> str:
    return str(getattr(g, "request_id", "sin-id"))


def flash_exception(exc: Exception, context: str = "Operación") -> None:
    flash(
        f"{context}: ocurrió un error. Código de incidente {request_id()}.",
        "error",
    )
