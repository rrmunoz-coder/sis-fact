from __future__ import annotations

import logging
import time

from sisfact import create_app
from sisfact.execution.service import process_one, worker_identity

app = create_app()
logger = logging.getLogger("billing_one.worker")


if __name__ == "__main__":
    worker_id = worker_identity()
    logger.info("BillingOne Worker iniciado id=%s", worker_id)
    with app.app_context():
        try:
            while True:
                processed = process_one(worker_id)
                if not processed:
                    time.sleep(5)
        except KeyboardInterrupt:
            logger.info("BillingOne Worker detenido por consola")
