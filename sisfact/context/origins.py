from __future__ import annotations

from typing import Any

from ..db import connection


def list_origins() -> list[dict[str, Any]]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT O.ORIGIN_ID, O.ORIGIN_CODE, O.ORIGIN_NAME, O.ACTIVE,
                       (SELECT COUNT(*) FROM RM_CFACT_SCOPE S
                         WHERE S.ORIGIN_ID=O.ORIGIN_ID AND S.ACTIVE='Y') ACTIVE_SCOPES,
                       (SELECT COUNT(*) FROM RM_CFACT_FLOW F
                         WHERE F.ORIGIN_ID=O.ORIGIN_ID AND F.ACTIVE='Y') ACTIVE_FLOWS
                FROM RM_CFACT_ORIGIN O
                ORDER BY O.ORIGIN_NAME, O.ORIGIN_CODE
                """
            )
            rows = cur.fetchall()
    return [
        {
            "origin_id": int(r[0]),
            "origin_code": r[1],
            "origin_name": r[2],
            "active": r[3],
            "active_scopes": int(r[4] or 0),
            "active_flows": int(r[5] or 0),
        }
        for r in rows
    ]


def create_origin(code: str, name: str) -> tuple[int, dict[str, Any]]:
    code = (code or "").strip().upper()
    name = (name or "").strip()
    if not code or not name:
        raise ValueError("Código y nombre del origen son obligatorios.")

    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ORIGIN_ID, ACTIVE FROM RM_CFACT_ORIGIN WHERE UPPER(ORIGIN_CODE)=:code",
                {"code": code},
            )
            existing = cur.fetchone()
            if existing:
                raise ValueError(
                    "El código de origen ya existe. Si está inactivo, reactívalo en vez de crear otro."
                )
            cur.execute(
                """
                INSERT INTO RM_CFACT_ORIGIN (ORIGIN_CODE, ORIGIN_NAME, ACTIVE)
                VALUES (:code, :name, 'Y')
                """,
                {"code": code, "name": name},
            )
            cur.execute(
                "SELECT ORIGIN_ID FROM RM_CFACT_ORIGIN WHERE ORIGIN_CODE=:code",
                {"code": code},
            )
            origin_id = int(cur.fetchone()[0])

    return origin_id, {
        "origin_id": origin_id,
        "origin_code": code,
        "origin_name": name,
        "active": "Y",
    }


def set_origin_status(origin_id: int, active: str) -> tuple[dict[str, Any], dict[str, Any]]:
    value = "Y" if str(active).upper() == "Y" else "N"

    with connection(commit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ORIGIN_CODE, ORIGIN_NAME, ACTIVE FROM RM_CFACT_ORIGIN WHERE ORIGIN_ID=:id",
                {"id": origin_id},
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Origen no existe.")

            before = {
                "origin_id": origin_id,
                "origin_code": row[0],
                "origin_name": row[1],
                "active": row[2],
            }

            if value == "N":
                cur.execute(
                    "SELECT COUNT(*) FROM RM_CFACT_SCOPE WHERE ORIGIN_ID=:id AND ACTIVE='Y'",
                    {"id": origin_id},
                )
                active_scopes = int(cur.fetchone()[0])
                cur.execute(
                    "SELECT COUNT(*) FROM RM_CFACT_FLOW WHERE ORIGIN_ID=:id AND ACTIVE='Y'",
                    {"id": origin_id},
                )
                active_flows = int(cur.fetchone()[0])
                if active_scopes or active_flows:
                    raise ValueError(
                        f"No se puede desactivar el origen: tiene {active_scopes} scope(s) activo(s) "
                        f"y {active_flows} flujo(s) activo(s). Desactiva primero sus dependencias."
                    )

            cur.execute(
                "UPDATE RM_CFACT_ORIGIN SET ACTIVE=:active WHERE ORIGIN_ID=:id",
                {"active": value, "id": origin_id},
            )

    after = dict(before)
    after["active"] = value
    return before, after
