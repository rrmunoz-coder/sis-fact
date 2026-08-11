from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..audit import record_event
from ..context.service import list_scopes_active
from ..errors import flash_exception
from ..security import permissions_required
from .service import (
    connection_scope_ids,
    create_connection,
    create_source,
    get_connection,
    get_source,
    list_connections,
    list_sources,
    set_connection_status,
    set_source_status,
    source_scope_ids,
    test_connection,
    update_connection,
    update_source,
)

bp = Blueprint("integrations", __name__, url_prefix="/administracion/integraciones")


def _scope_ids() -> list[int]:
    return [int(value) for value in request.form.getlist("scope_ids")]


@bp.get("")
@permissions_required("CONNECTION_VIEW", "SOURCE_VIEW")
def index():
    return render_template(
        "integrations/index.html",
        connections=list_connections(),
        sources=list_sources(),
    )


@bp.route("/conexiones/nueva", methods=["GET", "POST"])
@permissions_required("CONNECTION_MANAGE")
def connection_create():
    scopes = list_scopes_active()
    if request.method == "POST":
        try:
            connection_id, after = create_connection(request.form, _scope_ids())
            record_event("INTEGRATIONS", "RM_CFACT_CONNECTION", "INSERT", connection_id, after=after)
            flash("Conexión creada correctamente.", "success")
            return redirect(url_for("integrations.index"))
        except Exception as exc:
            flash_exception(exc, "Administración de conexiones")
    return render_template(
        "integrations/connection_form.html",
        item=None,
        scopes=scopes,
        selected_scope_ids=[],
    )


@bp.route("/conexiones/<int:connection_id>/editar", methods=["GET", "POST"])
@permissions_required("CONNECTION_MANAGE")
def connection_edit(connection_id: int):
    item = get_connection(connection_id)
    if not item:
        abort(404)
    scopes = list_scopes_active()
    selected = connection_scope_ids(connection_id)
    if request.method == "POST":
        try:
            before, after = update_connection(connection_id, request.form, _scope_ids())
            record_event("INTEGRATIONS", "RM_CFACT_CONNECTION", "UPDATE", connection_id, before, after)
            flash("Conexión actualizada correctamente.", "success")
            return redirect(url_for("integrations.index"))
        except Exception as exc:
            flash_exception(exc, "Administración de conexiones")
            item = get_connection(connection_id) or item
            selected = connection_scope_ids(connection_id)
    return render_template(
        "integrations/connection_form.html",
        item=item,
        scopes=scopes,
        selected_scope_ids=selected,
    )


@bp.post("/conexiones/<int:connection_id>/estado")
@permissions_required("CONNECTION_MANAGE")
def connection_status(connection_id: int):
    try:
        before, after = set_connection_status(connection_id, request.form.get("active", "N"))
        record_event("INTEGRATIONS", "RM_CFACT_CONNECTION", "STATUS", connection_id, before, after)
        flash("Estado de conexión actualizado.", "success")
    except Exception as exc:
        flash_exception(exc, "Administración de conexiones")
    return redirect(url_for("integrations.index"))


@bp.post("/conexiones/<int:connection_id>/probar")
@permissions_required("CONNECTION_MANAGE")
def connection_test(connection_id: int):
    try:
        result = test_connection(connection_id)
        record_event("INTEGRATIONS", "RM_CFACT_CONNECTION", "TEST", connection_id, after=result)
        category = "success" if result["status"] == "SUCCESS" else "error"
        flash(
            f"Prueba {result['status']} en {result['response_time_ms']} ms: {result['detail']}",
            category,
        )
    except Exception as exc:
        flash_exception(exc, "Prueba de conexión")
    return redirect(url_for("integrations.index"))


@bp.route("/insumos/nuevo", methods=["GET", "POST"])
@permissions_required("SOURCE_MANAGE")
def source_create():
    connections = [x for x in list_connections() if x["active"] == "Y"]
    scopes = list_scopes_active()
    if request.method == "POST":
        try:
            data_source_id, after = create_source(request.form, _scope_ids())
            record_event("INTEGRATIONS", "RM_CFACT_DATA_SOURCE", "INSERT", data_source_id, after=after)
            flash("Insumo creado correctamente.", "success")
            return redirect(url_for("integrations.index"))
        except Exception as exc:
            flash_exception(exc, "Administración de insumos")
    return render_template(
        "integrations/source_form.html",
        item=None,
        connections=connections,
        scopes=scopes,
        selected_scope_ids=[],
    )


@bp.route("/insumos/<int:data_source_id>/editar", methods=["GET", "POST"])
@permissions_required("SOURCE_MANAGE")
def source_edit(data_source_id: int):
    item = get_source(data_source_id)
    if not item:
        abort(404)
    connections = [
        x for x in list_connections()
        if x["active"] == "Y" or x["connection_id"] == item["connection_id"]
    ]
    scopes = list_scopes_active()
    selected = source_scope_ids(data_source_id)
    if request.method == "POST":
        try:
            before, after = update_source(data_source_id, request.form, _scope_ids())
            record_event("INTEGRATIONS", "RM_CFACT_DATA_SOURCE", "UPDATE", data_source_id, before, after)
            flash("Insumo actualizado correctamente.", "success")
            return redirect(url_for("integrations.index"))
        except Exception as exc:
            flash_exception(exc, "Administración de insumos")
            item = get_source(data_source_id) or item
            selected = source_scope_ids(data_source_id)
    return render_template(
        "integrations/source_form.html",
        item=item,
        connections=connections,
        scopes=scopes,
        selected_scope_ids=selected,
    )


@bp.post("/insumos/<int:data_source_id>/estado")
@permissions_required("SOURCE_MANAGE")
def source_status(data_source_id: int):
    try:
        before, after = set_source_status(data_source_id, request.form.get("active", "N"))
        record_event("INTEGRATIONS", "RM_CFACT_DATA_SOURCE", "STATUS", data_source_id, before, after)
        flash("Estado del insumo actualizado.", "success")
    except Exception as exc:
        flash_exception(exc, "Administración de insumos")
    return redirect(url_for("integrations.index"))
