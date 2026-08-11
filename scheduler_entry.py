from __future__ import annotations

import logging
import time

from sisfact import create_app
from sisfact.execution.service import schedule_due

app = create_app()
logger = logging.getLogger("billing_one.scheduler")


if __name__ == "__main__":
    logger.info("BillingOne Scheduler iniciado")
    with app.app_context():
        try:
            while True:
                try:
                    queued = schedule_due()
                    if queued:
                        logger.info("Scheduler encoló %s ejecución(es)", queued)
                except Exception:
                    logger.exception("Error en ciclo de scheduler")
                time.sleep(30)
        except KeyboardInterrupt:
            logger.info("BillingOne Scheduler detenido por consola")
