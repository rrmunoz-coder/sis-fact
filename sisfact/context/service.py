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
    "dom": {
        "table": "RM_CFACT_DOM",
        "id": "DOM_ID",
        "code": "DOM_CODE",
        "name": "DOM_NAME",
    },
    "cycle": {
        "table": "RM_CFACT_CYCLE",
        "id": "CYCLE_ID",
        "code": "CYCLE_CODE",
        "name": "CYCLE_NAME",
    },
}


def _catalog(kind: str) -> dict[str, str]:
    try:
        return CATALOGS[kind]
    except KeyError as exc:
        raise ValueError("Catálogo no soportado.") from exc


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
                JOIN RM_CFACT_COMPANY C ON C.COMPANY_ID=I.COMPANY_ID
                """ + where + " ORDER BY C.COMPANY_NAME, I.LEGAL_NAME, I.TAX_ID"
            )
            rows = cur.fetchall()
    return [
        {
            "issuer_id": int(r[0]), "company_id": int(r[1]), "company_code": r[2],
            "company_name": r[3], "tax_id": r[4], "legal_name": r[5], "active": r[6],
        }
        for r in rows
    ]


def create_issuer(company_id: int, tax_id: str, legal_name: str) -> tuple[int, dict[str, Any]]:
    tax_id = tax_id.strip().upper()
    legal_name = legal_name.strip()
    if not tax_id or not legal_name:
        raise ValueError("RUT emisor y razón social son obligatorios.")
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM RM_CFACT_COMPANY WHERE COMPANY_ID=:id AND ACTIVE='Y'", {"id": company_id})
            if not cur.fetchone():
                raise ValueError("Empresa no válida o inactiva.")
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
        "issuer_id": issuer_id, "company_id": company_id, "tax_id": tax_id,
        "legal_name": legal_name, "active": "Y",
    }


def set_issuer_status(issuer_id: int, active: str) -> tuple[dict[str, Any], dict[str, Any]]:
    value = "Y" if str(active).upper() == "Y" else "N"
    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COMPANY_ID, TAX_ID, LEGAL_NAME, ACTIVE FROM RM_CFACT_ISSUER WHERE ISSUER_ID=:id", {"id": issuer_id})
            row = cur.fetchone()
            if not row:
                raise ValueError("RUT emisor no existe.")
            before = {
                "issuer_id": issuer_id, "company_id": int(row[0]), "tax_id": row[1],
                "legal_name": row[2], "active": row[3],
            }
            cur.execute("UPDATE RM_CFACT_ISSUER SET ACTIVE=:active WHERE ISSUER_ID=:id", {"active": value, "id": issuer_id})
    after = dict(before)
    after["active"] = value
    return before, after


def list_scopes(include_inactive: bool = True) -> list[dict[str, Any]]:
    where = "" if include_inactive else " WHERE S.ACTIVE='Y'"
    sql = """
        SELECT S.SCOPE_ID, S.SCOPE_CODE, S.SCOPE_NAME, S.COMPANY_ID,
               C.COMPANY_NAME, S.ISSUER_ID, I.TAX_ID, S.BUSINESS_ID, B.BUSINESS_NAME,
               S.DOM_ID, D.DOM_CODE, S.CYCLE_ID, CY.CYCLE_CODE,
               S.PRIORITY_ORDER, S.ACTIVE, S.VALID_FROM, S.VALID_TO
        FROM RM_CFACT_SCOPE S
        JOIN RM_CFACT_COMPANY C ON C.COMPANY_ID=S.COMPANY_ID
        LEFT JOIN RM_CFACT_ISSUER I ON I.ISSUER_ID=S.ISSUER_ID
        LEFT JOIN RM_CFACT_BUSINESS B ON B.BUSINESS_ID=S.BUSINESS_ID
        LEFT JOIN RM_CFACT_DOM D ON D.DOM_ID=S.DOM_ID
        LEFT JOIN RM_CFACT_CYCLE CY ON CY.CYCLE_ID=S.CYCLE_ID
    """ + where + " ORDER BY S.PRIORITY_ORDER, S.SCOPE_NAME, S.SCOPE_CODE"
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    return [
        {
            "scope_id": int(r[0]), "scope_code": r[1], "scope_name": r[2],
            "company_id": int(r[3]), "company_name": r[4],
            "issuer_id": None if r[5] is None else int(r[5]), "tax_id": r[6],
            "business_id": None if r[7] is None else int(r[7]), "business_name": r[8],
            "dom_id": None if r[9] is None else int(r[9]), "dom_code": r[10],
            "cycle_id": None if r[11] is None else int(r[11]), "cycle_code": r[12],
            "priority_order": int(r[13]), "active": r[14], "valid_from": r[15], "valid_to": r[16],
        }
        for r in rows
    ]


def _optional_int(value: Any) -> int | None:
    text = str(value or "").strip()
    return int(text) if text else None


def create_scope(form) -> tuple[int, dict[str, Any]]:
    scope_code = (form.get("scope_code") or "").strip().upper()
    scope_name = (form.get("scope_name") or "").strip()
    company_id = int(form.get("company_id") or 0)
    issuer_id = _optional_int(form.get("issuer_id"))
    business_id = _optional_int(form.get("business_id"))
    dom_id = _optional_int(form.get("dom_id"))
    cycle_id = _optional_int(form.get("cycle_id"))
    priority_order = int(form.get("priority_order") or 100)
    valid_from = (form.get("valid_from") or "").strip() or None
    valid_to = (form.get("valid_to") or "").strip() or None

    if not scope_code or not scope_name or company_id <= 0:
        raise ValueError("Código, nombre y empresa son obligatorios.")

    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM RM_CFACT_COMPANY WHERE COMPANY_ID=:id AND ACTIVE='Y'", {"id": company_id})
            if not cur.fetchone():
                raise ValueError("Empresa no válida o inactiva.")
            if issuer_id is not None:
                cur.execute(
                    "SELECT 1 FROM RM_CFACT_ISSUER WHERE ISSUER_ID=:issuer_id AND COMPANY_ID=:company_id AND ACTIVE='Y'",
                    {"issuer_id": issuer_id, "company_id": company_id},
                )
                if not cur.fetchone():
                    raise ValueError("El RUT emisor no pertenece a la empresa seleccionada o está inactivo.")
            cur.execute(
                """
                INSERT INTO RM_CFACT_SCOPE (
                    SCOPE_CODE, SCOPE_NAME, COMPANY_ID, ISSUER_ID, BUSINESS_ID,
                    DOM_ID, CYCLE_ID, PRIORITY_ORDER, ACTIVE, VALID_FROM, VALID_TO
                ) VALUES (
                    :scope_code, :scope_name, :company_id, :issuer_id, :business_id,
                    :dom_id, :cycle_id, :priority_order, 'Y',
                    CASE WHEN :valid_from IS NULL THEN NULL ELSE TO_DATE(:valid_from, 'YYYY-MM-DD') END,
                    CASE WHEN :valid_to IS NULL THEN NULL ELSE TO_DATE(:valid_to, 'YYYY-MM-DD') END
                )
                """,
                {
                    "scope_code": scope_code, "scope_name": scope_name, "company_id": company_id,
                    "issuer_id": issuer_id, "business_id": business_id, "dom_id": dom_id,
                    "cycle_id": cycle_id, "priority_order": priority_order,
                    "valid_from": valid_from, "valid_to": valid_to,
                },
            )
            cur.execute("SELECT SCOPE_ID FROM RM_CFACT_SCOPE WHERE SCOPE_CODE=:code", {"code": scope_code})
            scope_id = int(cur.fetchone()[0])
    return scope_id, {
        "scope_id": scope_id, "scope_code": scope_code, "scope_name": scope_name,
        "company_id": company_id, "issuer_id": issuer_id, "business_id": business_id,
        "dom_id": dom_id, "cycle_id": cycle_id, "priority_order": priority_order,
        "valid_from": valid_from, "valid_to": valid_to, "active": "Y",
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
        "issuers": [item for item in list_issuers(include_inactive=False)],
        "businesses": list_simple_catalog("business", include_inactive=False),
        "doms": list_simple_catalog("dom", include_inactive=False),
        "cycles": list_simple_catalog("cycle", include_inactive=False),
    }
