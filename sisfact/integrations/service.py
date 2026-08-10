from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

from flask import current_app, session
import oracledb
import pyodbc
import requests

from ..db import connection

SECRET_WORDS = {"password", "passwd", "pwd", "secret", "token", "api_key", "apikey", "authorization"}
CONNECTION_TYPES = {"ORACLE", "SQLSERVER", "REST", "SOAP", "FILE"}
EXTRACTION_TYPES = {"SQL", "REST", "SOAP", "FILE"}


def _lob_text(value: Any) -> str:
    if value is None:
        return ""
    return value.read() if hasattr(value, "read") else str(value)


def _parse_config(value: str | None) -> dict[str, Any]:
    text = (value or "").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"CONFIG_JSON no es JSON válido: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ValueError("CONFIG_JSON debe ser un objeto JSON.")
    _assert_no_secrets(data)
    return data


def _assert_no_secrets(value: Any, path: str = "CONFIG_JSON") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            if normalized in SECRET_WORDS or any(word in normalized for word in ("password", "secret", "token")):
                raise ValueError(f"{path} no puede contener secretos ({key}). Usa CREDENTIAL_REF.")
            _assert_no_secrets(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_secrets(item, f"{path}[{index}]")


def _credential_section(ref: str | None) -> dict[str, str]:
    reference = (ref or "").strip()
    if not reference:
        return {}
    parser = current_app.config["CONFIG_RAW"]
    if not parser.has_section(reference):
        raise ValueError(f"No existe la sección de credencial [{reference}] en config.ini.")
    return {key: value for key, value in parser[reference].items()}


def _redact(text: str, secrets: dict[str, str]) -> str:
    result = str(text)
    for key, value in secrets.items():
        if value and any(word in key.lower() for word in ("password", "secret", "token", "key")):
            result = result.replace(value, "***")
    return result[:2000]


def _normalize_scope_ids(scope_ids: list[int]) -> list[int]:
    return sorted(set(int(value) for value in scope_ids))


def _validate_active_scope_ids(cursor, scope_ids: list[int]) -> list[int]:
    ids = _normalize_scope_ids(scope_ids)
    if not ids:
        return ids
    bind_names = [f":s{i}" for i in range(len(ids))]
    binds = {f"s{i}": scope_id for i, scope_id in enumerate(ids)}
    cursor.execute(
        f"SELECT SCOPE_ID FROM RM_CFACT_SCOPE WHERE ACTIVE='Y' AND SCOPE_ID IN ({','.join(bind_names)})",
        binds,
    )
    found = {int(row[0]) for row in cursor.fetchall()}
    missing = sorted(set(ids) - found)
    if missing:
        raise ValueError(f"Scopes inexistentes o inactivos: {missing}")
    return ids


def _replace_connection_scopes(cursor, connection_id: int, scope_ids: list[int]) -> list[int]:
    ids = _validate_active_scope_ids(cursor, scope_ids)
    cursor.execute("DELETE FROM RM_CFACT_CONNECTION_SCOPE WHERE CONNECTION_ID=:id", {"id": connection_id})
    for scope_id in ids:
        cursor.execute(
            "INSERT INTO RM_CFACT_CONNECTION_SCOPE (CONNECTION_ID, SCOPE_ID, ACTIVE) VALUES (:connection_id, :scope_id, 'Y')",
            {"connection_id": connection_id, "scope_id": scope_id},
        )
    return ids


def _validate_source_scopes(cursor, connection_id: int, scope_ids: list[int]) -> list[int]:
    ids = _validate_active_scope_ids(cursor, scope_ids)
    if not ids:
        raise ValueError("Un insumo activo debe tener al menos un alcance.")
    cursor.execute(
        "SELECT SCOPE_ID FROM RM_CFACT_CONNECTION_SCOPE WHERE CONNECTION_ID=:id AND ACTIVE='Y'",
        {"id": connection_id},
    )
    connection_scope_ids = {int(row[0]) for row in cursor.fetchall()}
    if connection_scope_ids and not set(ids).issubset(connection_scope_ids):
        invalid = sorted(set(ids) - connection_scope_ids)
        raise ValueError(
            f"El insumo usa scopes no autorizados para su conexión: {invalid}. "
            "Si la conexión debe ser global, déjala sin scopes específicos."
        )
    return ids


def _replace_source_scopes(cursor, data_source_id: int, connection_id: int, scope_ids: list[int]) -> list[int]:
    ids = _validate_source_scopes(cursor, connection_id, scope_ids)
    cursor.execute("DELETE FROM RM_CFACT_SOURCE_SCOPE WHERE DATA_SOURCE_ID=:id", {"id": data_source_id})
    for scope_id in ids:
        cursor.execute(
            """
            INSERT INTO RM_CFACT_SOURCE_SCOPE (
                DATA_SOURCE_ID, SCOPE_ID, PRIORITY_ORDER, ACTIVE
            ) VALUES (:data_source_id, :scope_id, 100, 'Y')
            """,
            {"data_source_id": data_source_id, "scope_id": scope_id},
        )
    return ids


def list_connections() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT CONNECTION_ID, CONNECTION_CODE, CONNECTION_NAME, CONNECTION_TYPE,
                       CREDENTIAL_REF, CONFIG_JSON, ACTIVE, HEALTH_STATUS, LAST_TEST_AT,
                       CREATED_AT, UPDATED_AT
                FROM RM_CFACT_CONNECTION
                ORDER BY CONNECTION_NAME, CONNECTION_CODE
                """
            )
            for r in cur:
                result.append({
                    "connection_id": int(r[0]), "connection_code": r[1], "connection_name": r[2],
                    "connection_type": r[3], "credential_ref": r[4], "config_json": _lob_text(r[5]),
                    "active": r[6], "health_status": r[7], "last_test_at": r[8],
                    "created_at": r[9], "updated_at": r[10],
                })
    return result


def get_connection(connection_id: int) -> dict[str, Any] | None:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT CONNECTION_ID, CONNECTION_CODE, CONNECTION_NAME, CONNECTION_TYPE,
                       CREDENTIAL_REF, CONFIG_JSON, ACTIVE, HEALTH_STATUS, LAST_TEST_AT,
                       CREATED_AT, UPDATED_AT
                FROM RM_CFACT_CONNECTION WHERE CONNECTION_ID=:id
                """,
                {"id": connection_id},
            )
            r = cur.fetchone()
            if not r:
                return None
            return {
                "connection_id": int(r[0]), "connection_code": r[1], "connection_name": r[2],
                "connection_type": r[3], "credential_ref": r[4], "config_json": _lob_text(r[5]),
                "active": r[6], "health_status": r[7], "last_test_at": r[8],
                "created_at": r[9], "updated_at": r[10],
            }


def _connection_values(form, *, require_code: bool = True) -> dict[str, Any]:
    values = {
        "connection_code": (form.get("connection_code") or "").strip().upper(),
        "connection_name": (form.get("connection_name") or "").strip(),
        "connection_type": (form.get("connection_type") or "").strip().upper(),
        "credential_ref": (form.get("credential_ref") or "").strip() or None,
        "config": _parse_config(form.get("config_json")),
    }
    if require_code and not values["connection_code"]:
        raise ValueError("Código de conexión obligatorio.")
    if not values["connection_name"] or values["connection_type"] not in CONNECTION_TYPES:
        raise ValueError("Nombre y tipo de conexión válidos son obligatorios.")
    values["config_json"] = json.dumps(values.pop("config"), ensure_ascii=False, sort_keys=True)
    return values


def create_connection(form, scope_ids: list[int]) -> tuple[int, dict[str, Any]]:
    values = _connection_values(form)
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO RM_CFACT_CONNECTION (
                    CONNECTION_CODE, CONNECTION_NAME, CONNECTION_TYPE,
                    CREDENTIAL_REF, CONFIG_JSON, ACTIVE, CREATED_BY
                ) VALUES (
                    :connection_code, :connection_name, :connection_type,
                    :credential_ref, :config_json, 'Y', :created_by
                )
                """,
                {**values, "created_by": session.get("username") or "SYSTEM"},
            )
            cur.execute(
                "SELECT CONNECTION_ID FROM RM_CFACT_CONNECTION WHERE CONNECTION_CODE=:code",
                {"code": values["connection_code"]},
            )
            connection_id = int(cur.fetchone()[0])
            normalized_scopes = _replace_connection_scopes(cur, connection_id, scope_ids)
    after = get_connection(connection_id) or {"connection_id": connection_id}
    after["scope_ids"] = normalized_scopes
    return connection_id, after


def update_connection(connection_id: int, form, scope_ids: list[int]) -> tuple[dict[str, Any], dict[str, Any]]:
    before = get_connection(connection_id)
    if not before:
        raise ValueError("Conexión no existe.")
    before["scope_ids"] = connection_scope_ids(connection_id)
    values = _connection_values(form, require_code=False)
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE RM_CFACT_CONNECTION
                   SET CONNECTION_NAME=:connection_name, CONNECTION_TYPE=:connection_type,
                       CREDENTIAL_REF=:credential_ref, CONFIG_JSON=:config_json,
                       UPDATED_AT=SYSTIMESTAMP, UPDATED_BY=:updated_by
                 WHERE CONNECTION_ID=:connection_id
                """,
                {
                    **values, "updated_by": session.get("username") or "SYSTEM",
                    "connection_id": connection_id,
                },
            )
            normalized_scopes = _replace_connection_scopes(cur, connection_id, scope_ids)
    after = get_connection(connection_id) or before
    after["scope_ids"] = normalized_scopes
    return before, after


def set_connection_status(connection_id: int, active: str) -> tuple[dict[str, Any], dict[str, Any]]:
    before = get_connection(connection_id)
    if not before:
        raise ValueError("Conexión no existe.")
    value = "Y" if str(active).upper() == "Y" else "N"
    if value == "N":
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM RM_CFACT_DATA_SOURCE WHERE CONNECTION_ID=:id AND ACTIVE='Y'",
                    {"id": connection_id},
                )
                if int(cur.fetchone()[0]) > 0:
                    raise ValueError("No puedes desactivar una conexión que tiene insumos activos.")
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE RM_CFACT_CONNECTION SET ACTIVE=:active, UPDATED_AT=SYSTIMESTAMP, UPDATED_BY=:user_name WHERE CONNECTION_ID=:id",
                {"active": value, "user_name": session.get("username") or "SYSTEM", "id": connection_id},
            )
    return before, get_connection(connection_id) or before


def _test_oracle(config: dict[str, Any], cred: dict[str, str]) -> str:
    dsn = config.get("dsn")
    if not dsn:
        host = config.get("host")
        service_name = config.get("service_name")
        port = int(config.get("port", 1521))
        if not host or not service_name:
            raise ValueError("Oracle requiere dsn o host + service_name en CONFIG_JSON.")
        dsn = oracledb.makedsn(str(host), port, service_name=str(service_name))
    user = cred.get("user") or cred.get("username")
    password = cred.get("password")
    if not user or not password:
        raise ValueError("CREDENTIAL_REF debe contener user/username y password.")
    with oracledb.connect(user=user, password=password, dsn=str(dsn)) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM DUAL")
            value = cur.fetchone()[0]
    return f"Oracle respondió correctamente (SELECT={value})."


def _test_sqlserver(config: dict[str, Any], cred: dict[str, str]) -> str:
    driver = str(config.get("driver") or "ODBC Driver 18 for SQL Server")
    server = config.get("server") or config.get("host")
    database = config.get("database")
    port = int(config.get("port", 1433))
    user = cred.get("user") or cred.get("username")
    password = cred.get("password")
    if not server or not database or not user or not password:
        raise ValueError("SQL Server requiere server, database y credencial user/password.")
    encrypt = str(config.get("encrypt", "yes"))
    trust = str(config.get("trust_server_certificate", "no"))
    conn_str = (
        f"DRIVER={{{driver}}};SERVER={server},{port};DATABASE={database};"
        f"UID={user};PWD={password};Encrypt={encrypt};TrustServerCertificate={trust};"
    )
    with pyodbc.connect(conn_str, timeout=int(config.get("timeout", 10))) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        value = cur.fetchone()[0]
    return f"SQL Server respondió correctamente (SELECT={value})."


def _request_headers(config: dict[str, Any], cred: dict[str, str]) -> dict[str, str]:
    headers = {str(k): str(v) for k, v in (config.get("headers") or {}).items()}
    auth_type = str(config.get("auth_type") or "NONE").upper()
    if auth_type == "BEARER":
        token = cred.get("token") or cred.get("bearer_token")
        if not token:
            raise ValueError("Credencial BEARER sin token.")
        headers["Authorization"] = f"Bearer {token}"
    elif auth_type == "API_KEY":
        key = cred.get("api_key") or cred.get("key")
        header_name = str(config.get("api_key_header") or "X-API-Key")
        if not key:
            raise ValueError("Credencial API_KEY sin api_key.")
        headers[header_name] = key
    return headers


def _test_http(config: dict[str, Any], cred: dict[str, str], soap: bool = False) -> str:
    url = config.get("wsdl_url") if soap else (config.get("health_url") or config.get("base_url"))
    if not url:
        raise ValueError("SOAP requiere wsdl_url; REST requiere health_url o base_url.")
    auth = None
    if str(config.get("auth_type") or "NONE").upper() == "BASIC":
        user = cred.get("user") or cred.get("username")
        password = cred.get("password")
        if not user or not password:
            raise ValueError("Credencial BASIC sin user/password.")
        auth = (user, password)
    response = requests.get(
        str(url), headers=_request_headers(config, cred), auth=auth,
        timeout=int(config.get("timeout", 15)), verify=config.get("verify_tls", True),
    )
    if response.status_code >= 500:
        raise RuntimeError(f"HTTP {response.status_code}")
    label = "SOAP/WSDL" if soap else "REST"
    return f"{label} respondió HTTP {response.status_code}."


def _test_file(config: dict[str, Any]) -> str:
    path_text = str(config.get("path") or "").strip()
    if not path_text:
        raise ValueError("FILE requiere path en CONFIG_JSON.")
    path = Path(path_text)
    if not path.exists():
        raise FileNotFoundError(f"Ruta no existe: {path}")
    pattern = str(config.get("pattern") or "*")
    count = sum(1 for _ in path.glob(pattern)) if path.is_dir() else 1
    return f"Ruta accesible; elementos que cumplen patrón '{pattern}': {count}."


def test_connection(connection_id: int) -> dict[str, Any]:
    item = get_connection(connection_id)
    if not item:
        raise ValueError("Conexión no existe.")
    config = _parse_config(item["config_json"])
    cred = _credential_section(item["credential_ref"])
    started = time.perf_counter()
    status = "SUCCESS"
    detail = ""
    try:
        ctype = item["connection_type"]
        if ctype == "ORACLE": detail = _test_oracle(config, cred)
        elif ctype == "SQLSERVER": detail = _test_sqlserver(config, cred)
        elif ctype == "REST": detail = _test_http(config, cred, soap=False)
        elif ctype == "SOAP": detail = _test_http(config, cred, soap=True)
        elif ctype == "FILE": detail = _test_file(config)
        else: raise ValueError(f"Tipo no soportado: {ctype}")
    except Exception as exc:
        status = "ERROR"
        detail = _redact(f"{type(exc).__name__}: {exc}", cred)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO RM_CFACT_CONNECTION_TEST (
                    CONNECTION_ID, TESTED_BY, FINISHED_AT, STATUS, RESPONSE_TIME_MS, DETAIL
                ) VALUES (:connection_id, :tested_by, SYSTIMESTAMP, :status, :response_time_ms, :detail)
                """,
                {
                    "connection_id": connection_id, "tested_by": session.get("user_id"),
                    "status": status, "response_time_ms": elapsed_ms, "detail": detail,
                },
            )
            cur.execute(
                "UPDATE RM_CFACT_CONNECTION SET HEALTH_STATUS=:status, LAST_TEST_AT=SYSTIMESTAMP, UPDATED_AT=SYSTIMESTAMP WHERE CONNECTION_ID=:connection_id",
                {"status": status, "connection_id": connection_id},
            )
    return {"status": status, "response_time_ms": elapsed_ms, "detail": detail}


def list_scopes_active() -> list[dict[str, Any]]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT S.SCOPE_ID, S.SCOPE_CODE, S.SCOPE_NAME, C.COMPANY_NAME,
                       I.TAX_ID, B.BUSINESS_NAME, D.DOM_CODE, CY.CYCLE_CODE
                FROM RM_CFACT_SCOPE S
                JOIN RM_CFACT_COMPANY C ON C.COMPANY_ID=S.COMPANY_ID
                LEFT JOIN RM_CFACT_ISSUER I ON I.ISSUER_ID=S.ISSUER_ID
                LEFT JOIN RM_CFACT_BUSINESS B ON B.BUSINESS_ID=S.BUSINESS_ID
                LEFT JOIN RM_CFACT_DOM D ON D.DOM_ID=S.DOM_ID
                LEFT JOIN RM_CFACT_CYCLE CY ON CY.CYCLE_ID=S.CYCLE_ID
                WHERE S.ACTIVE='Y'
                ORDER BY S.PRIORITY_ORDER, S.SCOPE_NAME
                """
            )
            rows = cur.fetchall()
    return [
        {
            "scope_id": int(r[0]), "scope_code": r[1], "scope_name": r[2], "company_name": r[3],
            "tax_id": r[4], "business_name": r[5], "dom_code": r[6], "cycle_code": r[7],
        }
        for r in rows
    ]


def connection_scope_ids(connection_id: int) -> list[int]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT SCOPE_ID FROM RM_CFACT_CONNECTION_SCOPE WHERE CONNECTION_ID=:id AND ACTIVE='Y'", {"id": connection_id})
            return [int(r[0]) for r in cur.fetchall()]


def list_sources() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT D.DATA_SOURCE_ID, D.SOURCE_CODE, D.SOURCE_NAME, D.LOGICAL_TYPE,
                       D.CONNECTION_ID, C.CONNECTION_NAME, D.EXTRACTION_TYPE,
                       D.DEFINITION_TEXT, D.EXPECTED_FREQUENCY, D.CRITICAL_FLAG,
                       D.ACTIVE, D.LAST_SUCCESS_AT
                FROM RM_CFACT_DATA_SOURCE D
                JOIN RM_CFACT_CONNECTION C ON C.CONNECTION_ID=D.CONNECTION_ID
                ORDER BY D.SOURCE_NAME, D.SOURCE_CODE
                """
            )
            for r in cur:
                result.append({
                    "data_source_id": int(r[0]), "source_code": r[1], "source_name": r[2],
                    "logical_type": r[3], "connection_id": int(r[4]), "connection_name": r[5],
                    "extraction_type": r[6], "definition_text": _lob_text(r[7]),
                    "expected_frequency": r[8], "critical_flag": r[9], "active": r[10],
                    "last_success_at": r[11],
                })
    return result


def get_source(data_source_id: int) -> dict[str, Any] | None:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT D.DATA_SOURCE_ID, D.SOURCE_CODE, D.SOURCE_NAME, D.LOGICAL_TYPE,
                       D.CONNECTION_ID, C.CONNECTION_NAME, D.EXTRACTION_TYPE,
                       D.DEFINITION_TEXT, D.EXPECTED_FREQUENCY, D.CRITICAL_FLAG,
                       D.ACTIVE, D.LAST_SUCCESS_AT
                FROM RM_CFACT_DATA_SOURCE D
                JOIN RM_CFACT_CONNECTION C ON C.CONNECTION_ID=D.CONNECTION_ID
                WHERE D.DATA_SOURCE_ID=:id
                """,
                {"id": data_source_id},
            )
            r = cur.fetchone()
            if not r:
                return None
            return {
                "data_source_id": int(r[0]), "source_code": r[1], "source_name": r[2],
                "logical_type": r[3], "connection_id": int(r[4]), "connection_name": r[5],
                "extraction_type": r[6], "definition_text": _lob_text(r[7]),
                "expected_frequency": r[8], "critical_flag": r[9], "active": r[10],
                "last_success_at": r[11],
            }


def source_scope_ids(data_source_id: int) -> list[int]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT SCOPE_ID FROM RM_CFACT_SOURCE_SCOPE WHERE DATA_SOURCE_ID=:id AND ACTIVE='Y'", {"id": data_source_id})
            return [int(r[0]) for r in cur.fetchall()]


def _source_values(form) -> dict[str, Any]:
    values = {
        "source_code": (form.get("source_code") or "").strip().upper(),
        "source_name": (form.get("source_name") or "").strip(),
        "logical_type": (form.get("logical_type") or "").strip().upper(),
        "connection_id": int(form.get("connection_id") or 0),
        "extraction_type": (form.get("extraction_type") or "").strip().upper(),
        "definition_text": (form.get("definition_text") or "").strip(),
        "expected_frequency": (form.get("expected_frequency") or "").strip() or None,
        "critical_flag": "Y" if str(form.get("critical_flag") or "").upper() == "Y" else "N",
    }
    if not values["source_code"] or not values["source_name"] or not values["logical_type"]:
        raise ValueError("Código, nombre y tipo lógico del insumo son obligatorios.")
    if values["connection_id"] <= 0 or values["extraction_type"] not in EXTRACTION_TYPES:
        raise ValueError("Conexión y tipo de extracción válidos son obligatorios.")
    return values


def create_source(form, scope_ids: list[int]) -> tuple[int, dict[str, Any]]:
    values = _source_values(form)
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM RM_CFACT_CONNECTION WHERE CONNECTION_ID=:id AND ACTIVE='Y'", {"id": values["connection_id"]})
            if not cur.fetchone():
                raise ValueError("Conexión no válida o inactiva.")
            normalized_scopes = _validate_source_scopes(cur, values["connection_id"], scope_ids)
            cur.execute(
                """
                INSERT INTO RM_CFACT_DATA_SOURCE (
                    SOURCE_CODE, SOURCE_NAME, LOGICAL_TYPE, CONNECTION_ID, EXTRACTION_TYPE,
                    DEFINITION_TEXT, EXPECTED_FREQUENCY, CRITICAL_FLAG, ACTIVE, CREATED_BY
                ) VALUES (
                    :source_code, :source_name, :logical_type, :connection_id, :extraction_type,
                    :definition_text, :expected_frequency, :critical_flag, 'Y', :created_by
                )
                """,
                {**values, "created_by": session.get("username") or "SYSTEM"},
            )
            cur.execute("SELECT DATA_SOURCE_ID FROM RM_CFACT_DATA_SOURCE WHERE SOURCE_CODE=:code", {"code": values["source_code"]})
            data_source_id = int(cur.fetchone()[0])
            _replace_source_scopes(cur, data_source_id, values["connection_id"], normalized_scopes)
    after = get_source(data_source_id) or {"data_source_id": data_source_id}
    after["scope_ids"] = normalized_scopes
    return data_source_id, after


def update_source(data_source_id: int, form, scope_ids: list[int]) -> tuple[dict[str, Any], dict[str, Any]]:
    before = get_source(data_source_id)
    if not before:
        raise ValueError("Insumo no existe.")
    before["scope_ids"] = source_scope_ids(data_source_id)
    values = _source_values(form)
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM RM_CFACT_CONNECTION WHERE CONNECTION_ID=:id AND ACTIVE='Y'", {"id": values["connection_id"]})
            if not cur.fetchone():
                raise ValueError("Conexión no válida o inactiva.")
            normalized_scopes = _validate_source_scopes(cur, values["connection_id"], scope_ids)
            cur.execute(
                """
                UPDATE RM_CFACT_DATA_SOURCE
                   SET SOURCE_NAME=:source_name, LOGICAL_TYPE=:logical_type,
                       CONNECTION_ID=:connection_id, EXTRACTION_TYPE=:extraction_type,
                       DEFINITION_TEXT=:definition_text, EXPECTED_FREQUENCY=:expected_frequency,
                       CRITICAL_FLAG=:critical_flag, UPDATED_AT=SYSTIMESTAMP, UPDATED_BY=:updated_by
                 WHERE DATA_SOURCE_ID=:data_source_id
                """,
                {**values, "updated_by": session.get("username") or "SYSTEM", "data_source_id": data_source_id},
            )
            _replace_source_scopes(cur, data_source_id, values["connection_id"], normalized_scopes)
    after = get_source(data_source_id) or before
    after["scope_ids"] = normalized_scopes
    return before, after


def set_source_status(data_source_id: int, active: str) -> tuple[dict[str, Any], dict[str, Any]]:
    before = get_source(data_source_id)
    if not before:
        raise ValueError("Insumo no existe.")
    value = "Y" if str(active).upper() == "Y" else "N"
    if value == "Y" and not source_scope_ids(data_source_id):
        raise ValueError("No se puede activar un insumo sin alcance.")
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE RM_CFACT_DATA_SOURCE SET ACTIVE=:active, UPDATED_AT=SYSTIMESTAMP, UPDATED_BY=:user_name WHERE DATA_SOURCE_ID=:id",
                {"active": value, "user_name": session.get("username") or "SYSTEM", "id": data_source_id},
            )
    return before, get_source(data_source_id) or before
