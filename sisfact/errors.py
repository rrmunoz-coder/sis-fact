from __future__ import annotations

import logging

from flask import flash, g

logger = logging.getLogger(__name__)


def request_id() -> str:
    return str(getattr(g, "request_id", "sin-id"))


def flash_exception(exc: Exception, context: str = "Operación") -> None:
    incident = request_id()

    # Errores de validación/control esperables: se pueden mostrar al usuario
    # porque no contienen stack técnico ni secretos.
    if isinstance(exc, ValueError):
        logger.warning(
            "%s: %s [incidente=%s]",
            context,
            exc,
            incident,
        )
        flash(f"{context}: {exc}", "error")
        return

    # Excepciones técnicas: el detalle queda solo en el log y la UI conserva
    # un identificador que permite correlacionar el incidente.
    logger.exception(
        "%s: error técnico [incidente=%s]",
        context,
        incident,
    )
    flash(
        f"{context}: ocurrió un error. Código de incidente {incident}.",
        "error",
    )
