from __future__ import annotations

from typing import Any

from ..db import connection

CATALOGS = {
    "company": {
        "table": "RM_CFACT_COMPANY",
        "id": "COMPANY_ID",
        "code": "COMPANY_CODE",
        "name": "COMPANY_NAME",
    },
    "business": {
        "table": "RM_CFACT_BUSINESS",
        "id": "BUSINESS_ID",
        "code": "BUSINESS_CODE",
        "name": "BUSINESS_NAME",
    },
    "origin": {
        "table": "RM_CFACT_ORIGIN",
        "id": "ORIGIN_ID",
        "code": "ORIGIN_CODE",
        "name": "ORIGIN_NAME",
    },
    "emission_type": {
        "table": "RM_CFACT_EMISSION_TYPE",
        "id": "EMISSION_TYPE_ID",
        "code": "EMISSION_TYPE_CODE",
        "name": "EMISSION_TYPE_NAME",
    },
}


def _catalog(kind: str) -> dict[str, str]:
    try:
        return CATALOGS[kind]
    except KeyError as exc:
        raise ValueError("Catálogo no soportado.") from exc


def _optional_int(value: Any) -> int | None:
    text = str(value or "").strip()
    return int(text) if text else None


def list_simple_catalog(kind: str, include_inactive: bool = True) -> list[dict[str, Any]]:
    cfg = _catalog(kind)
    where = "" if include_inactive else " WHERE ACTIVE='Y'"
    sql = (
        f"SELECT {cfg['id']}, {cfg['code']}, {cfg['name']}, ACTIVE "
        f"FROM {cfg['table']}{where} ORDER BY {cfg['name']}, {cfg['code']}"
    )
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    return [
        {"id": int(r[0]), "code": r[1], "name": r[2], "active": r[3]}
        for r in rows
    ]


def create_simple_catalog(kind: str, code: str, name: str) -> tuple[int, dict[str, Any]]:
    cfg = _catalog(kind)
    code = code.strip().upper()
    name = name.strip()
    if not code or not name:
        raise ValueError("Código y nombre son obligatorios.")
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {cfg['table']} ({cfg['code']}, {cfg['name']}, ACTIVE) "
                "VALUES (:code, :name, 'Y')",
                {"code": code, "name": name},
            )
            cur.execute(
                f"SELECT {cfg['id']} FROM {cfg['table']} WHERE {cfg['code']}=:code",
                {"code": code},
            )
            item_id = int(cur.fetchone()[0])
    return item_id, {"id": item_id, "code": code, "name": name, "active": "Y"}


def set_simple_catalog_status(kind: str, item_id: int, active: str) -> tuple[dict[str, Any], dict[str, Any]]:
    cfg = _catalog(kind)
    value = "Y" if str(active).upper() == "Y" else "N"
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {cfg['code']}, {cfg['name']}, ACTIVE FROM {cfg['table']} WHERE {cfg['id']}=:id",
                {"id": item_id},
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Registro no existe.")
            before = {"id": item_id, "code": row[0], "name": row[1], "active": row[2]}
            cur.execute(
                f"UPDATE {cfg['table']} SET ACTIVE=:active WHERE {cfg['id']}=:id",
                {"active": value, "id": item_id},
            )
    after = dict(before)
    after["active"] = value
    return before, after


def list_issuers(include_inactive: bool = True) -> list[dict[str, Any]]:
    where = "" if include_inactive else " WHERE I.ACTIVE='Y'"
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT I.ISSUER_ID, I.COMPANY_ID, C.COMPANY_CODE, C.COMPANY_NAME,
                       I.TAX_ID, I.LEGAL_NAME, I.ACTIVE
                FROM RM_CFACT_ISSUER I
                LEFT JOIN RM_CFACT_COMPANY C ON C.COMPANY_ID=I.COMPANY_ID
                """ + where + " ORDER BY I.LEGAL_NAME, I.TAX_ID"
            )
            rows = cur.fetchall()
    return [
        {
            "issuer_id": int(r[0]),
            "company_id": None if r[1] is None else int(r[1]),
            "company_code": r[2],
            "company_name": r[3],
            "tax_id": r[4],
            "legal_name": r[5],
            "active": r[6],
        }
        for r in rows
    ]


def create_issuer(company_id: int | None, tax_id: str, legal_name: str) -> tuple[int, dict[str, Any]]:
    tax_id = tax_id.strip().upper()
    legal_name = legal_name.strip()
    if not tax_id or not legal_name:
        raise ValueError("RUT emisor y razón social son obligatorios.")
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            if company_id is not None:
                cur.execute(
                    "SELECT 1 FROM RM_CFACT_COMPANY WHERE COMPANY_ID=:id AND ACTIVE='Y'",
                    {"id": company_id},
                )
                if not cur.fetchone():
                    raise ValueError("Empresa/grupo no válido o inactivo.")
            cur.execute(
                """
                INSERT INTO RM_CFACT_ISSUER (COMPANY_ID, TAX_ID, LEGAL_NAME, ACTIVE)
                VALUES (:company_id, :tax_id, :legal_name, 'Y')
                """,
                {"company_id": company_id, "tax_id": tax_id, "legal_name": legal_name},
            )
            cur.execute("SELECT ISSUER_ID FROM RM_CFACT_ISSUER WHERE TAX_ID=:tax_id", {"tax_id": tax_id})
            issuer_id = int(cur.fetchone()[0])
    return issuer_id, {
        "issuer_id": issuer_id,
        "company_id": company_id,
        "tax_id": tax_id,
        "legal_name": legal_name,
        "active": "Y",
    }


def set_issuer_status(issuer_id: int, active: str) -> tuple[dict[str, Any], dict[str, Any]]:
    value = "Y" if str(active).upper() == "Y" else "N"
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COMPANY_ID, TAX_ID, LEGAL_NAME, ACTIVE FROM RM_CFACT_ISSUER WHERE ISSUER_ID=:id",
                {"id": issuer_id},
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("RUT emisor no existe.")
            before = {
                "issuer_id": issuer_id,
                "company_id": None if row[0] is None else int(row[0]),
                "tax_id": row[1],
                "legal_name": row[2],
                "active": row[3],
            }
            cur.execute(
                "UPDATE RM_CFACT_ISSUER SET ACTIVE=:active WHERE ISSUER_ID=:id",
                {"active": value, "id": issuer_id},
            )
    after = dict(before)
    after["active"] = value
    return before, after


def list_flows(include_inactive: bool = True) -> list[dict[str, Any]]:
    where = "" if include_inactive else " WHERE F.ACTIVE='Y'"
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT F.FLOW_ID, F.ORIGIN_ID, O.ORIGIN_CODE, O.ORIGIN_NAME,
                       F.EMISSION_TYPE_ID, E.EMISSION_TYPE_CODE, E.EMISSION_TYPE_NAME,
                       F.FLOW_CODE, F.FLOW_NAME, F.SEGMENT_LABEL, F.ACTIVE
                FROM RM_CFACT_FLOW F
                JOIN RM_CFACT_ORIGIN O ON O.ORIGIN_ID=F.ORIGIN_ID
                JOIN RM_CFACT_EMISSION_TYPE E ON E.EMISSION_TYPE_ID=F.EMISSION_TYPE_ID
                """ + where + " ORDER BY O.ORIGIN_NAME, E.EMISSION_TYPE_NAME, F.FLOW_NAME"
            )
            rows = cur.fetchall()
    return [
        {
            "flow_id": int(r[0]),
            "origin_id": int(r[1]),
            "origin_code": r[2],
            "origin_name": r[3],
            "emission_type_id": int(r[4]),
            "emission_type_code": r[5],
            "emission_type_name": r[6],
            "flow_code": r[7],
            "flow_name": r[8],
            "segment_label": r[9],
            "active": r[10],
        }
        for r in rows
    ]


def create_flow(
    origin_id: int,
    emission_type_id: int,
    flow_code: str,
    flow_name: str,
    segment_label: str | None,
) -> tuple[int, dict[str, Any]]:
    flow_code = flow_code.strip().upper()
    flow_name = flow_name.strip()
    segment_label = (segment_label or "").strip().upper() or None
    if origin_id <= 0 or emission_type_id <= 0 or not flow_code or not flow_name:
        raise ValueError("Origen, tipo de emisión, código y nombre de flujo son obligatorios.")
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM RM_CFACT_ORIGIN WHERE ORIGIN_ID=:id AND ACTIVE='Y'", {"id": origin_id})
            if not cur.fetchone():
                raise ValueError("Origen no válido o inactivo.")
            cur.execute(
                "SELECT 1 FROM RM_CFACT_EMISSION_TYPE WHERE EMISSION_TYPE_ID=:id AND ACTIVE='Y'",
                {"id": emission_type_id},
            )
            if not cur.fetchone():
                raise ValueError("Tipo de emisión no válido o inactivo.")
            cur.execute(
                """
                INSERT INTO RM_CFACT_FLOW (
                    ORIGIN_ID, EMISSION_TYPE_ID, FLOW_CODE, FLOW_NAME, SEGMENT_LABEL, ACTIVE
                ) VALUES (
                    :origin_id, :emission_type_id, :flow_code, :flow_name, :segment_label, 'Y'
                )
                """,
                {
                    "origin_id": origin_id,
                    "emission_type_id": emission_type_id,
                    "flow_code": flow_code,
                    "flow_name": flow_name,
                    "segment_label": segment_label,
                },
            )
            cur.execute(
                """
                SELECT FLOW_ID FROM RM_CFACT_FLOW
                WHERE ORIGIN_ID=:origin_id AND EMISSION_TYPE_ID=:emission_type_id AND FLOW_CODE=:flow_code
                """,
                {"origin_id": origin_id, "emission_type_id": emission_type_id, "flow_code": flow_code},
            )
            flow_id = int(cur.fetchone()[0])
    return flow_id, {
        "flow_id": flow_id,
        "origin_id": origin_id,
        "emission_type_id": emission_type_id,
        "flow_code": flow_code,
        "flow_name": flow_name,
        "segment_label": segment_label,
        "active": "Y",
    }


def set_flow_status(flow_id: int, active: str) -> tuple[dict[str, Any], dict[str, Any]]:
    value = "Y" if str(active).upper() == "Y" else "N"
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ORIGIN_ID, EMISSION_TYPE_ID, FLOW_CODE, FLOW_NAME, SEGMENT_LABEL, ACTIVE FROM RM_CFACT_FLOW WHERE FLOW_ID=:id",
                {"id": flow_id},
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Flujo no existe.")
            before = {
                "flow_id": flow_id,
                "origin_id": int(row[0]),
                "emission_type_id": int(row[1]),
                "flow_code": row[2],
                "flow_name": row[3],
                "segment_label": row[4],
                "active": row[5],
            }
            cur.execute("UPDATE RM_CFACT_FLOW SET ACTIVE=:active WHERE FLOW_ID=:id", {"active": value, "id": flow_id})
    after = dict(before)
    after["active"] = value
    return before, after


def list_scopes(include_inactive: bool = True) -> list[dict[str, Any]]:
    where = "" if include_inactive else " WHERE S.ACTIVE='Y'"
    sql = """
        SELECT S.SCOPE_ID, S.SCOPE_CODE, S.SCOPE_NAME,
               S.ISSUER_ID, I.TAX_ID, I.LEGAL_NAME,
               S.BUSINESS_ID, B.BUSINESS_CODE, B.BUSINESS_NAME,
               S.ORIGIN_ID, O.ORIGIN_CODE, O.ORIGIN_NAME,
               S.EMISSION_TYPE_ID, E.EMISSION_TYPE_CODE, E.EMISSION_TYPE_NAME,
               S.FLOW_ID, F.FLOW_CODE, F.FLOW_NAME, F.SEGMENT_LABEL,
               S.PRIORITY_ORDER, S.ACTIVE, S.VALID_FROM, S.VALID_TO
        FROM RM_CFACT_SCOPE S
        JOIN RM_CFACT_ISSUER I ON I.ISSUER_ID=S.ISSUER_ID
        JOIN RM_CFACT_BUSINESS B ON B.BUSINESS_ID=S.BUSINESS_ID
        JOIN RM_CFACT_ORIGIN O ON O.ORIGIN_ID=S.ORIGIN_ID
        JOIN RM_CFACT_EMISSION_TYPE E ON E.EMISSION_TYPE_ID=S.EMISSION_TYPE_ID
        LEFT JOIN RM_CFACT_FLOW F ON F.FLOW_ID=S.FLOW_ID
    """ + where + " ORDER BY S.PRIORITY_ORDER, I.TAX_ID, B.BUSINESS_NAME, O.ORIGIN_NAME, E.EMISSION_TYPE_NAME, S.SCOPE_NAME"
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    return [
        {
            "scope_id": int(r[0]),
            "scope_code": r[1],
            "scope_name": r[2],
            "issuer_id": int(r[3]),
            "tax_id": r[4],
            "legal_name": r[5],
            "business_id": int(r[6]),
            "business_code": r[7],
            "business_name": r[8],
            "origin_id": int(r[9]),
            "origin_code": r[10],
            "origin_name": r[11],
            "emission_type_id": int(r[12]),
            "emission_type_code": r[13],
            "emission_type_name": r[14],
            "flow_id": None if r[15] is None else int(r[15]),
            "flow_code": r[16],
            "flow_name": r[17],
            "segment_label": r[18],
            "priority_order": int(r[19]),
            "active": r[20],
            "valid_from": r[21],
            "valid_to": r[22],
        }
        for r in rows
    ]


def list_scopes_active() -> list[dict[str, Any]]:
    return list_scopes(include_inactive=False)


def create_scope(form) -> tuple[int, dict[str, Any]]:
    scope_code = (form.get("scope_code") or "").strip().upper()
    scope_name = (form.get("scope_name") or "").strip()
    issuer_id = int(form.get("issuer_id") or 0)
    business_id = int(form.get("business_id") or 0)
    origin_id = int(form.get("origin_id") or 0)
    emission_type_id = int(form.get("emission_type_id") or 0)
    flow_id = _optional_int(form.get("flow_id"))
    priority_order = int(form.get("priority_order") or 100)
    valid_from = (form.get("valid_from") or "").strip() or None
    valid_to = (form.get("valid_to") or "").strip() or None

    if (
        not scope_code
        or not scope_name
        or issuer_id <= 0
        or business_id <= 0
        or origin_id <= 0
        or emission_type_id <= 0
    ):
        raise ValueError("Código, nombre, RUT emisor, negocio, origen y tipo de emisión son obligatorios.")

    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            checks = (
                ("RM_CFACT_ISSUER", "ISSUER_ID", issuer_id, "RUT emisor"),
                ("RM_CFACT_BUSINESS", "BUSINESS_ID", business_id, "Negocio"),
                ("RM_CFACT_ORIGIN", "ORIGIN_ID", origin_id, "Origen"),
                ("RM_CFACT_EMISSION_TYPE", "EMISSION_TYPE_ID", emission_type_id, "Tipo de emisión"),
            )
            for table, key, value, label in checks:
                cur.execute(f"SELECT 1 FROM {table} WHERE {key}=:id AND ACTIVE='Y'", {"id": value})
                if not cur.fetchone():
                    raise ValueError(f"{label} no válido o inactivo.")
            if flow_id is not None:
                cur.execute(
                    """
                    SELECT 1 FROM RM_CFACT_FLOW
                    WHERE FLOW_ID=:flow_id AND ORIGIN_ID=:origin_id
                      AND EMISSION_TYPE_ID=:emission_type_id AND ACTIVE='Y'
                    """,
                    {
                        "flow_id": flow_id,
                        "origin_id": origin_id,
                        "emission_type_id": emission_type_id,
                    },
                )
                if not cur.fetchone():
                    raise ValueError("El flujo no pertenece al origen/tipo de emisión seleccionado o está inactivo.")
            cur.execute(
                """
                INSERT INTO RM_CFACT_SCOPE (
                    SCOPE_CODE, SCOPE_NAME, ISSUER_ID, BUSINESS_ID, ORIGIN_ID,
                    EMISSION_TYPE_ID, FLOW_ID, PRIORITY_ORDER, ACTIVE, VALID_FROM, VALID_TO
                ) VALUES (
                    :scope_code, :scope_name, :issuer_id, :business_id, :origin_id,
                    :emission_type_id, :flow_id, :priority_order, 'Y',
                    CASE WHEN :valid_from IS NULL THEN NULL ELSE TO_DATE(:valid_from, 'YYYY-MM-DD') END,
                    CASE WHEN :valid_to IS NULL THEN NULL ELSE TO_DATE(:valid_to, 'YYYY-MM-DD') END
                )
                """,
                {
                    "scope_code": scope_code,
                    "scope_name": scope_name,
                    "issuer_id": issuer_id,
                    "business_id": business_id,
                    "origin_id": origin_id,
                    "emission_type_id": emission_type_id,
                    "flow_id": flow_id,
                    "priority_order": priority_order,
                    "valid_from": valid_from,
                    "valid_to": valid_to,
                },
            )
            cur.execute("SELECT SCOPE_ID FROM RM_CFACT_SCOPE WHERE SCOPE_CODE=:code", {"code": scope_code})
            scope_id = int(cur.fetchone()[0])
    return scope_id, {
        "scope_id": scope_id,
        "scope_code": scope_code,
        "scope_name": scope_name,
        "issuer_id": issuer_id,
        "business_id": business_id,
        "origin_id": origin_id,
        "emission_type_id": emission_type_id,
        "flow_id": flow_id,
        "priority_order": priority_order,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "active": "Y",
    }


def set_scope_status(scope_id: int, active: str) -> tuple[dict[str, Any], dict[str, Any]]:
    value = "Y" if str(active).upper() == "Y" else "N"
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT SCOPE_CODE, SCOPE_NAME, ACTIVE FROM RM_CFACT_SCOPE WHERE SCOPE_ID=:id", {"id": scope_id})
            row = cur.fetchone()
            if not row:
                raise ValueError("Scope no existe.")
            before = {"scope_id": scope_id, "scope_code": row[0], "scope_name": row[1], "active": row[2]}
            cur.execute("UPDATE RM_CFACT_SCOPE SET ACTIVE=:active WHERE SCOPE_ID=:id", {"active": value, "id": scope_id})
    after = dict(before)
    after["active"] = value
    return before, after


def catalogs_for_scope() -> dict[str, list[dict[str, Any]]]:
    return {
        "companies": list_simple_catalog("company", include_inactive=False),
        "issuers": list_issuers(include_inactive=False),
        "businesses": list_simple_catalog("business", include_inactive=False),
        "origins": list_simple_catalog("origin", include_inactive=False),
        "emission_types": list_simple_catalog("emission_type", include_inactive=False),
        "flows": list_flows(include_inactive=False),
    }
