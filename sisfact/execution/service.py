from __future__ import annotations

import calendar
from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
import re
import socket
from typing import Any
from urllib.parse import urljoin
import uuid

import oracledb
import pyodbc
import requests

from ..db import connection
from ..integrations.service import _credential_section, _lob_text, _parse_config, _request_headers

logger = logging.getLogger(__name__)

EXECUTION_MODES = {"MANUAL", "SCHEDULED", "EXTERNAL"}
FREQUENCY_TYPES = {"MINUTES", "HOURLY", "DAILY", "WEEKLY", "MONTHLY"}


def default_policy() -> dict[str, Any]:
    return {
        "policy_id": None,
        "execution_mode": "MANUAL",
        "frequency_type": None,
        "interval_value": 1,
        "run_time": "06:00",
        "day_of_week": 1,
        "day_of_month": 1,
        "timeout_minutes": 45,
        "max_retries": 2,
        "external_executor": None,
        "active": "Y",
        "last_due_at": None,
        "next_due_at": None,
    }


def _int_value(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        result = int(str(value if value not in (None, "") else default))
    except ValueError as exc:
        raise ValueError("Valor numérico no válido en política de ejecución.") from exc
    if result < minimum or result > maximum:
        raise ValueError(f"Valor fuera de rango ({minimum}-{maximum}).")
    return result


def _parse_time(value: str | None) -> tuple[int, int, str]:
    text = (value or "06:00").strip()
    match = re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", text)
    if not match:
        raise ValueError("Hora inválida. Usa formato HH:MM, por ejemplo 06:00.")
    hour, minute = int(match.group(1)), int(match.group(2))
    return hour, minute, f"{hour:02d}:{minute:02d}"


def policy_values(form) -> dict[str, Any]:
    mode = (form.get("execution_mode") or "MANUAL").strip().upper()
    if mode not in EXECUTION_MODES:
        raise ValueError("Modo de ejecución no válido.")

    active = "N" if str(form.get("policy_active") or "Y").strip().upper() == "N" else "Y"
    timeout_minutes = _int_value(form.get("timeout_minutes"), 45, 1, 1440)
    max_retries = _int_value(form.get("max_retries"), 2, 0, 10)
    external_executor = (form.get("external_executor") or "").strip() or None

    frequency_type = (form.get("frequency_type") or "").strip().upper() or None
    interval_value = _int_value(form.get("interval_value"), 1, 1, 10080)
    day_of_week = _int_value(form.get("day_of_week"), 1, 1, 7)
    day_of_month = _int_value(form.get("day_of_month"), 1, 1, 31)
    _hour, _minute, run_time = _parse_time(form.get("run_time"))

    if mode == "MANUAL":
        frequency_type = None
        external_executor = None
    elif mode == "SCHEDULED":
        if frequency_type not in FREQUENCY_TYPES:
            raise ValueError("Una ejecución programada requiere una periodicidad válida.")
    elif mode == "EXTERNAL":
        if not external_executor:
            raise ValueError("El modo EXTERNAL requiere indicar el ejecutor externo (KNIME, BOT, JOB, etc.).")
        if frequency_type and frequency_type not in FREQUENCY_TYPES:
            raise ValueError("Periodicidad externa no válida.")

    return {
        "execution_mode": mode,
        "frequency_type": frequency_type,
        "interval_value": interval_value,
        "run_time": run_time if frequency_type in {"DAILY", "WEEKLY", "MONTHLY"} else None,
        "day_of_week": day_of_week if frequency_type == "WEEKLY" else None,
        "day_of_month": day_of_month if frequency_type == "MONTHLY" else None,
        "timeout_minutes": timeout_minutes,
        "max_retries": max_retries,
        "external_executor": external_executor,
        "active": active,
    }


def _next_due(values: dict[str, Any], now: datetime | None = None) -> datetime | None:
    if values.get("active") != "Y":
        return None
    mode = values.get("execution_mode")
    freq = values.get("frequency_type")
    if mode == "MANUAL" or not freq:
        return None

    now = now or datetime.now()
    interval = int(values.get("interval_value") or 1)

    if freq == "MINUTES":
        return now + timedelta(minutes=interval)
    if freq == "HOURLY":
        return now + timedelta(hours=interval)

    hour, minute, _ = _parse_time(values.get("run_time"))
    if freq == "DAILY":
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=interval)
        return candidate

    if freq == "WEEKLY":
        target = int(values.get("day_of_week") or 1) - 1  # Monday=0
        delta = (target - now.weekday()) % 7
        candidate = (now + timedelta(days=delta)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(weeks=interval)
        return candidate

    if freq == "MONTHLY":
        target_day = int(values.get("day_of_month") or 1)
        year, month = now.year, now.month
        for _ in range(24):
            last_day = calendar.monthrange(year, month)[1]
            day = min(target_day, last_day)
            candidate = datetime(year, month, day, hour, minute)
            if candidate > now:
                return candidate
            month += interval
            while month > 12:
                month -= 12
                year += 1
        raise ValueError("No fue posible calcular la próxima ejecución mensual.")

    raise ValueError("Periodicidad no soportada.")


def _advance_due(values: dict[str, Any], due_at: datetime, now: datetime) -> datetime:
    current = due_at
    for _ in range(10000):
        probe = dict(values)
        if probe.get("frequency_type") in {"MINUTES", "HOURLY"}:
            current = _next_due(probe, current) or current
        else:
            current = _next_due(probe, current + timedelta(seconds=1)) or current
        if current > now:
            return current
    raise RuntimeError("No fue posible avanzar la agenda de ejecución.")


def get_policy(data_source_id: int) -> dict[str, Any] | None:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT POLICY_ID, DATA_SOURCE_ID, EXECUTION_MODE, FREQUENCY_TYPE,
                       INTERVAL_VALUE, RUN_TIME, DAY_OF_WEEK, DAY_OF_MONTH,
                       TIMEOUT_MINUTES, MAX_RETRIES, EXTERNAL_EXECUTOR, ACTIVE,
                       LAST_DUE_AT, NEXT_DUE_AT
                FROM RM_CFACT_EXECUTION_POLICY
                WHERE DATA_SOURCE_ID=:data_source_id
                """,
                {"data_source_id": data_source_id},
            )
            r = cur.fetchone()
    if not r:
        return None
    return {
        "policy_id": int(r[0]), "data_source_id": int(r[1]), "execution_mode": r[2],
        "frequency_type": r[3], "interval_value": int(r[4] or 1), "run_time": r[5],
        "day_of_week": None if r[6] is None else int(r[6]),
        "day_of_month": None if r[7] is None else int(r[7]),
        "timeout_minutes": int(r[8] or 45), "max_retries": int(r[9] or 0),
        "external_executor": r[10], "active": r[11],
        "last_due_at": r[12], "next_due_at": r[13],
    }


def save_policy(data_source_id: int, values: dict[str, Any], actor: str) -> dict[str, Any]:
    next_due_at = _next_due(values)
    binds = {
        "data_source_id": data_source_id,
        **values,
        "next_due_at": next_due_at,
        "actor": actor or "SYSTEM",
    }
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                MERGE INTO RM_CFACT_EXECUTION_POLICY P
                USING (SELECT :data_source_id DATA_SOURCE_ID FROM DUAL) X
                   ON (P.DATA_SOURCE_ID=X.DATA_SOURCE_ID)
                WHEN MATCHED THEN UPDATE SET
                    P.EXECUTION_MODE=:execution_mode,
                    P.FREQUENCY_TYPE=:frequency_type,
                    P.INTERVAL_VALUE=:interval_value,
                    P.RUN_TIME=:run_time,
                    P.DAY_OF_WEEK=:day_of_week,
                    P.DAY_OF_MONTH=:day_of_month,
                    P.TIMEOUT_MINUTES=:timeout_minutes,
                    P.MAX_RETRIES=:max_retries,
                    P.EXTERNAL_EXECUTOR=:external_executor,
                    P.ACTIVE=:active,
                    P.NEXT_DUE_AT=:next_due_at,
                    P.UPDATED_AT=SYSTIMESTAMP,
                    P.UPDATED_BY=:actor
                WHEN NOT MATCHED THEN INSERT (
                    DATA_SOURCE_ID, EXECUTION_MODE, FREQUENCY_TYPE, INTERVAL_VALUE,
                    RUN_TIME, DAY_OF_WEEK, DAY_OF_MONTH, TIMEOUT_MINUTES, MAX_RETRIES,
                    EXTERNAL_EXECUTOR, ACTIVE, NEXT_DUE_AT, CREATED_BY
                ) VALUES (
                    :data_source_id, :execution_mode, :frequency_type, :interval_value,
                    :run_time, :day_of_week, :day_of_month, :timeout_minutes, :max_retries,
                    :external_executor, :active, :next_due_at, :actor
                )
                """,
                binds,
            )
    return get_policy(data_source_id) or {"data_source_id": data_source_id}


def execution_summary_map() -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT D.DATA_SOURCE_ID,
                       P.EXECUTION_MODE, P.FREQUENCY_TYPE, P.INTERVAL_VALUE,
                       P.RUN_TIME, P.EXTERNAL_EXECUTOR, P.ACTIVE, P.NEXT_DUE_AT,
                       (SELECT MAX(E.STARTED_AT) FROM RM_CFACT_EXTRACTION_RUN E
                         WHERE E.DATA_SOURCE_ID=D.DATA_SOURCE_ID) LAST_RUN_AT,
                       (SELECT MAX(E.STATUS) KEEP (DENSE_RANK LAST ORDER BY E.STARTED_AT, E.EXTRACTION_ID)
                          FROM RM_CFACT_EXTRACTION_RUN E WHERE E.DATA_SOURCE_ID=D.DATA_SOURCE_ID) LAST_STATUS,
                       (SELECT MAX(E.ROWS_READ) KEEP (DENSE_RANK LAST ORDER BY E.STARTED_AT, E.EXTRACTION_ID)
                          FROM RM_CFACT_EXTRACTION_RUN E WHERE E.DATA_SOURCE_ID=D.DATA_SOURCE_ID) LAST_ROWS_READ,
                       (SELECT COUNT(*) FROM RM_CFACT_EXECUTION_QUEUE Q
                         WHERE Q.DATA_SOURCE_ID=D.DATA_SOURCE_ID AND Q.STATUS IN ('PENDING','RUNNING')) OPEN_QUEUE
                FROM RM_CFACT_DATA_SOURCE D
                LEFT JOIN RM_CFACT_EXECUTION_POLICY P ON P.DATA_SOURCE_ID=D.DATA_SOURCE_ID
                """
            )
            for r in cur:
                result[int(r[0])] = {
                    "execution_mode": r[1] or "SIN_POLITICA",
                    "frequency_type": r[2], "interval_value": r[3], "run_time": r[4],
                    "external_executor": r[5], "policy_active": r[6], "next_due_at": r[7],
                    "last_run_at": r[8], "last_status": r[9],
                    "last_rows_read": None if r[10] is None else int(r[10]),
                    "open_queue": int(r[11] or 0),
                }
    return result


def list_execution_dashboard() -> list[dict[str, Any]]:
    summaries = execution_summary_map()
    rows: list[dict[str, Any]] = []
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT D.DATA_SOURCE_ID, D.SOURCE_CODE, D.SOURCE_NAME, D.LOGICAL_TYPE,
                       D.EXTRACTION_TYPE, D.ACTIVE, C.CONNECTION_NAME, C.CONNECTION_TYPE
                FROM RM_CFACT_DATA_SOURCE D
                JOIN RM_CFACT_CONNECTION C ON C.CONNECTION_ID=D.CONNECTION_ID
                ORDER BY D.SOURCE_NAME, D.SOURCE_CODE
                """
            )
            for r in cur:
                item = {
                    "data_source_id": int(r[0]), "source_code": r[1], "source_name": r[2],
                    "logical_type": r[3], "extraction_type": r[4], "active": r[5],
                    "connection_name": r[6], "connection_type": r[7],
                }
                item.update(summaries.get(item["data_source_id"], {}))
                rows.append(item)
    return rows


def list_recent_runs(limit: int = 100) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 500))
    result: list[dict[str, Any]] = []
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT * FROM (
                    SELECT E.EXTRACTION_ID, E.DATA_SOURCE_ID, D.SOURCE_CODE, D.SOURCE_NAME,
                           E.SCOPE_ID, S.SCOPE_CODE, E.EXECUTION_CODE, E.STARTED_AT, E.FINISHED_AT,
                           E.ROWS_READ, E.ROWS_LOADED, E.ROWS_REJECTED, E.STATUS,
                           E.ERROR_STAGE, E.ERROR_MESSAGE
                    FROM RM_CFACT_EXTRACTION_RUN E
                    JOIN RM_CFACT_DATA_SOURCE D ON D.DATA_SOURCE_ID=E.DATA_SOURCE_ID
                    LEFT JOIN RM_CFACT_SCOPE S ON S.SCOPE_ID=E.SCOPE_ID
                    ORDER BY E.STARTED_AT DESC, E.EXTRACTION_ID DESC
                ) WHERE ROWNUM <= {limit}
                """
            )
            for r in cur:
                result.append({
                    "extraction_id": int(r[0]), "data_source_id": int(r[1]),
                    "source_code": r[2], "source_name": r[3],
                    "scope_id": None if r[4] is None else int(r[4]), "scope_code": r[5],
                    "execution_code": r[6], "started_at": r[7], "finished_at": r[8],
                    "rows_read": int(r[9] or 0), "rows_loaded": int(r[10] or 0),
                    "rows_rejected": int(r[11] or 0), "status": r[12],
                    "error_stage": r[13], "error_message": r[14],
                })
    return result


def active_source_scope_ids(data_source_id: int) -> list[int]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT SS.SCOPE_ID
                FROM RM_CFACT_SOURCE_SCOPE SS
                JOIN RM_CFACT_SCOPE S ON S.SCOPE_ID=SS.SCOPE_ID AND S.ACTIVE='Y'
                WHERE SS.DATA_SOURCE_ID=:id AND SS.ACTIVE='Y'
                ORDER BY SS.PRIORITY_ORDER, SS.SCOPE_ID
                """,
                {"id": data_source_id},
            )
            return [int(r[0]) for r in cur.fetchall()]


def enqueue_manual(data_source_id: int, scope_ids: list[int], requested_by: str) -> int:
    policy = get_policy(data_source_id)
    if not policy:
        raise ValueError("El insumo no tiene política de ejecución. Edítalo y guarda la política.")
    if policy["active"] != "Y":
        raise ValueError("La política de ejecución está pausada.")
    if policy["execution_mode"] == "EXTERNAL":
        raise ValueError("Este insumo es EXTERNAL y no puede ejecutarse internamente. Debe ser entregado por su ejecutor externo.")

    valid = set(active_source_scope_ids(data_source_id))
    selected = sorted(set(int(x) for x in scope_ids) & valid)
    if not selected:
        raise ValueError("No tienes un scope ejecutable para este insumo.")

    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ACTIVE FROM RM_CFACT_DATA_SOURCE WHERE DATA_SOURCE_ID=:id", {"id": data_source_id})
            row = cur.fetchone()
            if not row or row[0] != "Y":
                raise ValueError("El insumo no existe o está inactivo.")
            for scope_id in selected:
                cur.execute(
                    """
                    INSERT INTO RM_CFACT_EXECUTION_QUEUE (
                        DATA_SOURCE_ID, POLICY_ID, SCOPE_ID, REQUEST_TYPE, STATUS,
                        MAX_ATTEMPTS, REQUESTED_BY
                    ) VALUES (
                        :data_source_id, :policy_id, :scope_id, 'MANUAL', 'PENDING',
                        :max_attempts, :requested_by
                    )
                    """,
                    {
                        "data_source_id": data_source_id,
                        "policy_id": policy["policy_id"],
                        "scope_id": scope_id,
                        "max_attempts": int(policy["max_retries"]) + 1,
                        "requested_by": requested_by or "WEB",
                    },
                )
    return len(selected)


def schedule_due(now: datetime | None = None) -> int:
    now = now or datetime.now()
    queued = 0
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT P.POLICY_ID, P.DATA_SOURCE_ID, P.EXECUTION_MODE, P.FREQUENCY_TYPE,
                       P.INTERVAL_VALUE, P.RUN_TIME, P.DAY_OF_WEEK, P.DAY_OF_MONTH,
                       P.TIMEOUT_MINUTES, P.MAX_RETRIES, P.ACTIVE, P.NEXT_DUE_AT
                FROM RM_CFACT_EXECUTION_POLICY P
                JOIN RM_CFACT_DATA_SOURCE D ON D.DATA_SOURCE_ID=P.DATA_SOURCE_ID AND D.ACTIVE='Y'
                WHERE P.ACTIVE='Y'
                  AND P.EXECUTION_MODE='SCHEDULED'
                  AND P.NEXT_DUE_AT IS NOT NULL
                  AND P.NEXT_DUE_AT <= SYSTIMESTAMP
                ORDER BY P.NEXT_DUE_AT, P.POLICY_ID
                """
            )
            policies = cur.fetchall()

            for r in policies:
                policy = {
                    "policy_id": int(r[0]), "data_source_id": int(r[1]),
                    "execution_mode": r[2], "frequency_type": r[3],
                    "interval_value": int(r[4] or 1), "run_time": r[5],
                    "day_of_week": r[6], "day_of_month": r[7],
                    "timeout_minutes": int(r[8] or 45), "max_retries": int(r[9] or 0),
                    "active": r[10], "next_due_at": r[11],
                }
                due_at = policy["next_due_at"]
                if due_at is None:
                    continue
                cur.execute(
                    "SELECT SCOPE_ID FROM RM_CFACT_SOURCE_SCOPE WHERE DATA_SOURCE_ID=:id AND ACTIVE='Y' ORDER BY PRIORITY_ORDER, SCOPE_ID",
                    {"id": policy["data_source_id"]},
                )
                scopes = [int(x[0]) for x in cur.fetchall()]
                due_key = due_at.strftime("%Y%m%d%H%M%S")
                for scope_id in scopes:
                    request_key = f"SCHED:{policy['policy_id']}:{scope_id}:{due_key}"
                    try:
                        cur.execute(
                            """
                            INSERT INTO RM_CFACT_EXECUTION_QUEUE (
                                DATA_SOURCE_ID, POLICY_ID, SCOPE_ID, REQUEST_TYPE, REQUEST_KEY,
                                STATUS, MAX_ATTEMPTS, REQUESTED_BY
                            ) VALUES (
                                :data_source_id, :policy_id, :scope_id, 'SCHEDULED', :request_key,
                                'PENDING', :max_attempts, 'SCHEDULER'
                            )
                            """,
                            {
                                "data_source_id": policy["data_source_id"], "policy_id": policy["policy_id"],
                                "scope_id": scope_id, "request_key": request_key,
                                "max_attempts": policy["max_retries"] + 1,
                            },
                        )
                        queued += 1
                    except oracledb.IntegrityError as exc:
                        if "ORA-00001" not in str(exc):
                            raise
                next_due = _advance_due(policy, due_at, now)
                cur.execute(
                    """
                    UPDATE RM_CFACT_EXECUTION_POLICY
                       SET LAST_DUE_AT=:due_at, NEXT_DUE_AT=:next_due,
                           UPDATED_AT=SYSTIMESTAMP, UPDATED_BY='SCHEDULER'
                     WHERE POLICY_ID=:policy_id
                    """,
                    {"due_at": due_at, "next_due": next_due, "policy_id": policy["policy_id"]},
                )
    return queued


def _claim_next(worker_id: str) -> dict[str, Any] | None:
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT Q.QUEUE_ID, Q.DATA_SOURCE_ID, Q.SCOPE_ID, Q.ATTEMPT_NO, Q.MAX_ATTEMPTS
                FROM RM_CFACT_EXECUTION_QUEUE Q
                WHERE Q.QUEUE_ID = (
                    SELECT QUEUE_ID FROM (
                        SELECT Q2.QUEUE_ID
                        FROM RM_CFACT_EXECUTION_QUEUE Q2
                        JOIN RM_CFACT_DATA_SOURCE D2 ON D2.DATA_SOURCE_ID=Q2.DATA_SOURCE_ID AND D2.ACTIVE='Y'
                        WHERE Q2.STATUS='PENDING' AND Q2.AVAILABLE_AT <= SYSTIMESTAMP
                        ORDER BY Q2.REQUESTED_AT, Q2.QUEUE_ID
                    ) WHERE ROWNUM=1
                )
                FOR UPDATE SKIP LOCKED
                """
            )
            row = cur.fetchone()
            if not row:
                return None
            queue_id, data_source_id, scope_id = int(row[0]), int(row[1]), int(row[2])
            attempt_no = int(row[3] or 0) + 1
            max_attempts = int(row[4] or 1)
            correlation_id = uuid.uuid4().hex
            execution_code = f"QUEUE:{queue_id}:ATTEMPT:{attempt_no}"

            cur.execute(
                """
                UPDATE RM_CFACT_EXECUTION_QUEUE
                   SET STATUS='RUNNING', ATTEMPT_NO=:attempt_no, STARTED_AT=SYSTIMESTAMP,
                       FINISHED_AT=NULL, WORKER_ID=:worker_id, ERROR_MESSAGE=NULL
                 WHERE QUEUE_ID=:queue_id
                """,
                {"attempt_no": attempt_no, "worker_id": worker_id, "queue_id": queue_id},
            )
            cur.execute(
                """
                INSERT INTO RM_CFACT_EXTRACTION_RUN (
                    DATA_SOURCE_ID, SCOPE_ID, EXECUTION_CODE, CORRELATION_ID,
                    STARTED_AT, ROWS_READ, ROWS_LOADED, ROWS_REJECTED, STATUS
                ) VALUES (
                    :data_source_id, :scope_id, :execution_code, :correlation_id,
                    SYSTIMESTAMP, 0, 0, 0, 'RUNNING'
                )
                """,
                {
                    "data_source_id": data_source_id, "scope_id": scope_id,
                    "execution_code": execution_code, "correlation_id": correlation_id,
                },
            )
            cur.execute(
                """
                SELECT EXTRACTION_ID FROM RM_CFACT_EXTRACTION_RUN
                WHERE EXECUTION_CODE=:execution_code AND CORRELATION_ID=:correlation_id
                """,
                {"execution_code": execution_code, "correlation_id": correlation_id},
            )
            extraction_id = int(cur.fetchone()[0])
            cur.execute(
                "UPDATE RM_CFACT_EXECUTION_QUEUE SET EXTRACTION_ID=:extraction_id WHERE QUEUE_ID=:queue_id",
                {"extraction_id": extraction_id, "queue_id": queue_id},
            )
            return {
                "queue_id": queue_id, "data_source_id": data_source_id, "scope_id": scope_id,
                "attempt_no": attempt_no, "max_attempts": max_attempts,
                "extraction_id": extraction_id,
            }


def _load_execution_context(queue: dict[str, Any]) -> dict[str, Any]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT D.SOURCE_CODE, D.SOURCE_NAME, D.EXTRACTION_TYPE, D.DEFINITION_TEXT,
                       C.CONNECTION_TYPE, C.CREDENTIAL_REF, C.CONFIG_JSON,
                       P.TIMEOUT_MINUTES,
                       S.SCOPE_CODE, I.TAX_ID, B.BUSINESS_CODE, O.ORIGIN_CODE,
                       E.EMISSION_TYPE_CODE, F.FLOW_CODE, F.SEGMENT_LABEL
                FROM RM_CFACT_DATA_SOURCE D
                JOIN RM_CFACT_CONNECTION C ON C.CONNECTION_ID=D.CONNECTION_ID
                LEFT JOIN RM_CFACT_EXECUTION_POLICY P ON P.DATA_SOURCE_ID=D.DATA_SOURCE_ID
                JOIN RM_CFACT_SCOPE S ON S.SCOPE_ID=:scope_id
                JOIN RM_CFACT_ISSUER I ON I.ISSUER_ID=S.ISSUER_ID
                JOIN RM_CFACT_BUSINESS B ON B.BUSINESS_ID=S.BUSINESS_ID
                JOIN RM_CFACT_ORIGIN O ON O.ORIGIN_ID=S.ORIGIN_ID
                JOIN RM_CFACT_EMISSION_TYPE E ON E.EMISSION_TYPE_ID=S.EMISSION_TYPE_ID
                LEFT JOIN RM_CFACT_FLOW F ON F.FLOW_ID=S.FLOW_ID
                WHERE D.DATA_SOURCE_ID=:data_source_id
                """,
                {"scope_id": queue["scope_id"], "data_source_id": queue["data_source_id"]},
            )
            r = cur.fetchone()
    if not r:
        raise ValueError("No fue posible resolver el contexto de ejecución del insumo.")
    return {
        **queue,
        "source_code": r[0], "source_name": r[1], "extraction_type": r[2],
        "definition_text": _lob_text(r[3]), "connection_type": r[4],
        "credential_ref": r[5], "config_json": _lob_text(r[6]),
        "timeout_minutes": int(r[7] or 45), "scope_code": r[8], "tax_id": r[9],
        "business_code": r[10], "origin_code": r[11], "emission_type_code": r[12],
        "flow_code": r[13], "segment_label": r[14],
    }


def _assert_readonly_sql(sql: str) -> str:
    text = (sql or "").strip()
    while text.endswith(";"):
        text = text[:-1].rstrip()
    if not text:
        raise ValueError("La definición SQL está vacía.")
    if ";" in text:
        raise ValueError("La extracción SQL debe contener una sola sentencia.")
    if not re.match(r"^(SELECT|WITH)\b", text, re.IGNORECASE):
        raise ValueError("Por seguridad, una extracción SQL debe comenzar con SELECT o WITH.")
    forbidden = re.compile(r"\b(INSERT|UPDATE|DELETE|MERGE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|BEGIN|DECLARE|EXECUTE|CALL)\b", re.IGNORECASE)
    if forbidden.search(text):
        raise ValueError("La definición SQL contiene una operación no permitida para extracción.")
    return text


def _count_cursor_rows(cursor, batch_size: int = 2000) -> int:
    count = 0
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        count += len(rows)
    return count


def _execute_oracle_sql(ctx: dict[str, Any], config: dict[str, Any], cred: dict[str, str]) -> dict[str, Any]:
    sql = _assert_readonly_sql(ctx["definition_text"])
    dsn = config.get("dsn")
    if not dsn:
        host, service_name = config.get("host"), config.get("service_name")
        if not host or not service_name:
            raise ValueError("Conexión Oracle requiere dsn o host + service_name.")
        dsn = oracledb.makedsn(str(host), int(config.get("port", 1521)), service_name=str(service_name))
    user = cred.get("user") or cred.get("username")
    password = cred.get("password")
    if not user or not password:
        raise ValueError("Credencial Oracle incompleta.")
    with oracledb.connect(user=user, password=password, dsn=str(dsn)) as conn:
        try:
            conn.call_timeout = int(ctx["timeout_minutes"]) * 60 * 1000
        except Exception:
            pass
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = _count_cursor_rows(cur)
    return {"status": "SUCCESS", "rows_read": rows, "detail": f"Oracle SQL leído: {rows} fila(s)."}


def _execute_sqlserver_sql(ctx: dict[str, Any], config: dict[str, Any], cred: dict[str, str]) -> dict[str, Any]:
    sql = _assert_readonly_sql(ctx["definition_text"])
    driver = str(config.get("driver") or "ODBC Driver 18 for SQL Server")
    server = config.get("server") or config.get("host")
    database = config.get("database")
    user = cred.get("user") or cred.get("username")
    password = cred.get("password")
    if not server or not database or not user or not password:
        raise ValueError("Conexión SQL Server incompleta.")
    conn_str = (
        f"DRIVER={{{driver}}};SERVER={server},{int(config.get('port',1433))};DATABASE={database};"
        f"UID={user};PWD={password};Encrypt={config.get('encrypt','yes')};"
        f"TrustServerCertificate={config.get('trust_server_certificate','no')};"
    )
    with pyodbc.connect(conn_str, timeout=max(1, int(ctx["timeout_minutes"]) * 60)) as conn:
        cur = conn.cursor()
        try:
            cur.timeout = max(1, int(ctx["timeout_minutes"]) * 60)
        except Exception:
            pass
        cur.execute(sql)
        rows = _count_cursor_rows(cur)
    return {"status": "SUCCESS", "rows_read": rows, "detail": f"SQL Server leído: {rows} fila(s)."}


def _execute_rest(ctx: dict[str, Any], config: dict[str, Any], cred: dict[str, str]) -> dict[str, Any]:
    base_url = str(config.get("base_url") or "").strip()
    definition = (ctx["definition_text"] or "").strip()
    if not base_url and not definition.startswith(("http://", "https://")):
        raise ValueError("REST requiere base_url o una URL absoluta en la definición.")
    url = definition if definition.startswith(("http://", "https://")) else urljoin(base_url.rstrip("/") + "/", definition.lstrip("/"))
    auth = None
    if str(config.get("auth_type") or "NONE").upper() == "BASIC":
        user = cred.get("user") or cred.get("username")
        password = cred.get("password")
        if not user or not password:
            raise ValueError("Credencial BASIC incompleta.")
        auth = (user, password)
    response = requests.get(
        url, headers=_request_headers(config, cred), auth=auth,
        timeout=max(1, int(ctx["timeout_minutes"]) * 60), verify=config.get("verify_tls", True),
    )
    response.raise_for_status()
    rows = 1
    try:
        payload = response.json()
        if isinstance(payload, list):
            rows = len(payload)
        elif isinstance(payload, dict):
            for key in ("items", "data", "results", "rows"):
                if isinstance(payload.get(key), list):
                    rows = len(payload[key])
                    break
    except ValueError:
        rows = 1 if response.content else 0
    return {"status": "SUCCESS", "rows_read": rows, "detail": f"REST HTTP {response.status_code}; elementos estimados={rows}."}


def _execute_file(ctx: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    base = Path(str(config.get("path") or ""))
    if not base.exists():
        raise ValueError(f"Ruta de archivos no existe: {base}")
    pattern = (ctx["definition_text"] or "").strip() or str(config.get("pattern") or "*")
    items = [p for p in base.glob(pattern) if p.is_file()]
    return {"status": "SUCCESS", "rows_read": len(items), "detail": f"Archivos encontrados: {len(items)} con patrón {pattern}."}


def _execute_soap(ctx: dict[str, Any], config: dict[str, Any], cred: dict[str, str]) -> dict[str, Any]:
    wsdl = str(config.get("wsdl_url") or "").strip()
    if not wsdl:
        raise ValueError("SOAP requiere wsdl_url en la conexión.")
    auth = None
    if str(config.get("auth_type") or "NONE").upper() == "BASIC":
        user = cred.get("user") or cred.get("username")
        password = cred.get("password")
        if user and password:
            auth = (user, password)
    response = requests.get(wsdl, auth=auth, timeout=max(1, int(ctx["timeout_minutes"]) * 60), verify=config.get("verify_tls", True))
    response.raise_for_status()
    return {
        "status": "WARNING", "rows_read": 0,
        "detail": "WSDL accesible. La operación SOAP genérica aún no se ejecuta porque requiere parámetros específicos del insumo.",
    }


def _execute_context(ctx: dict[str, Any]) -> dict[str, Any]:
    config = _parse_config(ctx["config_json"])
    cred = _credential_section(ctx["credential_ref"])
    extraction_type = str(ctx["extraction_type"] or "").upper()
    connection_type = str(ctx["connection_type"] or "").upper()

    if extraction_type == "SQL" and connection_type == "ORACLE":
        return _execute_oracle_sql(ctx, config, cred)
    if extraction_type == "SQL" and connection_type == "SQLSERVER":
        return _execute_sqlserver_sql(ctx, config, cred)
    if extraction_type == "REST" and connection_type == "REST":
        return _execute_rest(ctx, config, cred)
    if extraction_type == "FILE" and connection_type == "FILE":
        return _execute_file(ctx, config)
    if extraction_type == "SOAP" and connection_type == "SOAP":
        return _execute_soap(ctx, config, cred)
    raise ValueError(f"Combinación no soportada: extracción={extraction_type}, conexión={connection_type}.")


def _finish_success(queue: dict[str, Any], result: dict[str, Any]) -> None:
    status = result.get("status") or "SUCCESS"
    rows_read = int(result.get("rows_read") or 0)
    detail = str(result.get("detail") or "")[:4000]
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE RM_CFACT_EXTRACTION_RUN
                   SET FINISHED_AT=SYSTIMESTAMP, ROWS_READ=:rows_read,
                       STATUS=:status, ERROR_STAGE=NULL, ERROR_MESSAGE=:detail
                 WHERE EXTRACTION_ID=:extraction_id
                """,
                {"rows_read": rows_read, "status": status, "detail": detail, "extraction_id": queue["extraction_id"]},
            )
            cur.execute(
                """
                UPDATE RM_CFACT_EXECUTION_QUEUE
                   SET STATUS=:status, FINISHED_AT=SYSTIMESTAMP, ERROR_MESSAGE=NULL
                 WHERE QUEUE_ID=:queue_id
                """,
                {"status": status, "queue_id": queue["queue_id"]},
            )
            if status == "SUCCESS":
                cur.execute(
                    "UPDATE RM_CFACT_DATA_SOURCE SET LAST_SUCCESS_AT=SYSTIMESTAMP WHERE DATA_SOURCE_ID=:id",
                    {"id": queue["data_source_id"]},
                )


def _finish_error(queue: dict[str, Any], exc: Exception) -> None:
    message = f"{type(exc).__name__}: {exc}"[:4000]
    retry = int(queue["attempt_no"]) < int(queue["max_attempts"])
    delay_seconds = min(300, 30 * int(queue["attempt_no"]))
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE RM_CFACT_EXTRACTION_RUN
                   SET FINISHED_AT=SYSTIMESTAMP, STATUS='ERROR',
                       ERROR_STAGE='ACQUISITION', ERROR_MESSAGE=:message
                 WHERE EXTRACTION_ID=:extraction_id
                """,
                {"message": message, "extraction_id": queue["extraction_id"]},
            )
            if retry:
                cur.execute(
                    """
                    UPDATE RM_CFACT_EXECUTION_QUEUE
                       SET STATUS='PENDING', AVAILABLE_AT=SYSTIMESTAMP + NUMTODSINTERVAL(:delay_seconds,'SECOND'),
                           FINISHED_AT=NULL, ERROR_MESSAGE=:message
                     WHERE QUEUE_ID=:queue_id
                    """,
                    {"delay_seconds": delay_seconds, "message": message, "queue_id": queue["queue_id"]},
                )
            else:
                cur.execute(
                    """
                    UPDATE RM_CFACT_EXECUTION_QUEUE
                       SET STATUS='ERROR', FINISHED_AT=SYSTIMESTAMP, ERROR_MESSAGE=:message
                     WHERE QUEUE_ID=:queue_id
                    """,
                    {"message": message, "queue_id": queue["queue_id"]},
                )


def worker_identity() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def process_one(worker_id: str | None = None) -> bool:
    worker_id = worker_id or worker_identity()
    queue = _claim_next(worker_id)
    if not queue:
        return False
    try:
        ctx = _load_execution_context(queue)
        result = _execute_context(ctx)
        _finish_success(queue, result)
        logger.info(
            "Ejecución completada queue=%s source=%s scope=%s status=%s rows=%s",
            queue["queue_id"], ctx["source_code"], ctx["scope_code"], result.get("status"), result.get("rows_read"),
        )
    except Exception as exc:
        logger.exception("Fallo ejecución queue=%s", queue["queue_id"])
        _finish_error(queue, exc)
    return True
