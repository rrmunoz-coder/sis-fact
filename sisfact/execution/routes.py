from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, session, url_for

from ..audit import record_event
from ..errors import flash_exception
from ..security import has_scope_access, permissions_required
from .service import (
    active_source_scope_ids,
    enqueue_manual,
    list_execution_dashboard,
    list_recent_runs,
)

bp = Blueprint("execution", __name__, url_prefix="/operacion/ejecuciones")


def _is_admin() -> bool:
    return str(session.get("role_code") or "").upper() == "ADMIN"


def _viewable_source(data_source_id: int) -> bool:
    if _is_admin():
        return True
    return any(has_scope_access(scope_id, "VIEW") for scope_id in active_source_scope_ids(data_source_id))


@bp.get("")
@permissions_required("CONTROL_VIEW")
def index():
    dashboard = [item for item in list_execution_dashboard() if _viewable_source(item["data_source_id"])]
    runs = [
        item for item in list_recent_runs(100)
        if item["scope_id"] is None or _is_admin() or has_scope_access(item["scope_id"], "VIEW")
    ]
    return render_template("execution/index.html", dashboard=dashboard, runs=runs)


@bp.post("/insumos/<int:data_source_id>/ejecutar")
@permissions_required("CONTROL_EXECUTE")
def run_source(data_source_id: int):
    try:
        scopes = active_source_scope_ids(data_source_id)
        executable = scopes if _is_admin() else [scope_id for scope_id in scopes if has_scope_access(scope_id, "EXECUTE")]
        queued = enqueue_manual(
            data_source_id,
            executable,
            session.get("username") or session.get("display_name") or "WEB",
        )
        record_event(
            "EXECUTION", "RM_CFACT_EXECUTION_QUEUE", "ENQUEUE_MANUAL", data_source_id,
            after={"data_source_id": data_source_id, "queued_scopes": queued},
        )
        flash(f"Ejecución solicitada para {queued} alcance(s). El worker la procesará en cola.", "success")
    except Exception as exc:
        flash_exception(exc, "Ejecución de insumo")
    return redirect(url_for("execution.index"))
