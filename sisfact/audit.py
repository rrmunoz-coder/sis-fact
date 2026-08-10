from __future__ import annotations

import json
import logging
from typing import Any

from flask import request, session

from .db import connection

logger = logging.getLogger(__name__)


def origin_ip() -> str | None:
    return request.remote_addr


def _payload(
    module: Any,
    entity: Any,
    action: Any,
    entity_id: Any = None,
    before: Any = None,
    after: Any = None,
    *,
    user_id: int | None = None,
    ip_address: str | None = None,
) -> dict[str, Any]:
    return {
        "user_id": user_id if user_id is not None else session.get("user_id"),
        "module_name": str(module)[:80],
        "entity_name": str(entity)[:80],
        "entity_id": None if entity_id is None else str(entity_id)[:120],
        "action_name": str(action).upper()[:40],
        "before_data": None if before is None else json.dumps(before, default=str, ensure_ascii=False),
        "after_data": None if after is None else json.dumps(after, default=str, ensure_ascii=False),
        "client_ip": ip_address if ip_address is not None else origin_ip(),
    }


def write_event(
    cursor,
    module: Any,
    entity: Any,
    action: Any,
    entity_id: Any = None,
    before: Any = None,
    after: Any = None,
    *,
    user_id: int | None = None,
    ip_address: str | None = None,
) -> None:
    cursor.execute(
        """
        INSERT INTO RM_CFACT_AUDIT_LOG (
            USER_ID, MODULE_NAME, ENTITY_NAME, ENTITY_ID, ACTION_NAME,
            BEFORE_DATA, AFTER_DATA, CLIENT_IP
        ) VALUES (
            :user_id, :module_name, :entity_name, :entity_id, :action_name,
            :before_data, :after_data, :client_ip
        )
        """,
        _payload(
            module, entity, action, entity_id, before, after,
            user_id=user_id, ip_address=ip_address,
        ),
    )


def record_event(
    module: Any,
    entity: Any,
    action: Any,
    entity_id: Any = None,
    before: Any = None,
    after: Any = None,
    *,
    critical: bool = False,
) -> bool:
    try:
        with connection(commit=True) as conn:
            with conn.cursor() as cur:
                write_event(cur, module, entity, action, entity_id, before, after)
        return True
    except Exception:
        logger.exception(
            "Fallo auditoría module=%s entity=%s action=%s id=%s",
            module, entity, action, entity_id,
        )
        if critical:
            raise
        return False
