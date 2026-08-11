from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..audit import record_event
from ..errors import flash_exception
from ..security import permissions_required
from .origins import create_origin, list_origins, set_origin_status, update_origin_name
from .service import (
    catalogs_for_scope,
    create_flow,
    create_issuer,
    create_scope,
    create_simple_catalog,
    list_flows,
    list_issuers,
    list_scopes,
    list_simple_catalog,
    set_flow_status,
    set_issuer_status,
    set_scope_status,
    set_simple_catalog_status,
)

bp = Blueprint("context", __name__, url_prefix="/administracion/contexto")


@bp.get("")
@permissions_required("CONTEXT_VIEW")
def index():
    return render_template(
        "context/index.html",
        companies=list_simple_catalog("company"),
        issuers=list_issuers(),
        businesses=list_simple_catalog("business"),
        emission_types=list_simple_catalog("emission_type"),
        flows=list_flows(),
        scopes=list_scopes(),
        scope_catalogs=catalogs_for_scope(),
    )


@bp.get("/origenes")
@permissions_required("CONTEXT_VIEW")
def origins():
    return render_template("context/origins.html", origins=list_origins())


@bp.post("/origenes/nuevo")
@permissions_required("CONTEXT_MANAGE")
def origin_create():
    try:
        origin_id, after = create_origin(
            request.form.get("code", ""),
            request.form.get("name", ""),
        )
        record_event("CONTEXT", "RM_CFACT_ORIGIN", "INSERT", origin_id, after=after)
        flash("Origen creado correctamente.", "success")
    except Exception as exc:
        flash_exception(exc, "Administración de orígenes")
    return redirect(url_for("context.origins"))


@bp.post("/origenes/<int:origin_id>/editar")
@permissions_required("CONTEXT_MANAGE")
def origin_edit(origin_id: int):
    try:
        before, after = update_origin_name(origin_id, request.form.get("name", ""))
        record_event("CONTEXT", "RM_CFACT_ORIGIN", "UPDATE", origin_id, before, after)
        flash("Nombre del origen actualizado.", "success")
    except Exception as exc:
        flash_exception(exc, "Administración de orígenes")
    return redirect(url_for("context.origins"))


@bp.post("/origenes/<int:origin_id>/estado")
@permissions_required("CONTEXT_MANAGE")
def origin_status(origin_id: int):
    try:
        before, after = set_origin_status(origin_id, request.form.get("active", "N"))
        record_event("CONTEXT", "RM_CFACT_ORIGIN", "STATUS", origin_id, before, after)
        flash("Estado del origen actualizado.", "success")
    except Exception as exc:
        flash_exception(exc, "Administración de orígenes")
    return redirect(url_for("context.origins"))


@bp.post("/catalogo/<kind>/nuevo")
@permissions_required("CONTEXT_MANAGE")
def create_catalog(kind: str):
    if kind == "origin":
        return origin_create()
    try:
        item_id, after = create_simple_catalog(
            kind,
            request.form.get("code", ""),
            request.form.get("name", ""),
        )
        record_event("CONTEXT", kind.upper(), "INSERT", item_id, after=after)
        flash("Registro creado correctamente.", "success")
    except Exception as exc:
        flash_exception(exc, "Administración de contexto")
    return redirect(url_for("context.index"))


@bp.post("/catalogo/<kind>/<int:item_id>/estado")
@permissions_required("CONTEXT_MANAGE")
def catalog_status(kind: str, item_id: int):
    if kind == "origin":
        return origin_status(item_id)
    try:
        before, after = set_simple_catalog_status(kind, item_id, request.form.get("active", "N"))
        record_event("CONTEXT", kind.upper(), "STATUS", item_id, before, after)
        flash("Estado actualizado.", "success")
    except Exception as exc:
        flash_exception(exc, "Administración de contexto")
    return redirect(url_for("context.index"))


@bp.post("/emisores/nuevo")
@permissions_required("CONTEXT_MANAGE")
def issuer_create():
    try:
        company_text = (request.form.get("company_id") or "").strip()
        company_id = int(company_text) if company_text else None
        issuer_id, after = create_issuer(
            company_id,
            request.form.get("tax_id", ""),
            request.form.get("legal_name", ""),
        )
        record_event("CONTEXT", "RM_CFACT_ISSUER", "INSERT", issuer_id, after=after)
        flash("RUT emisor creado correctamente.", "success")
    except Exception as exc:
        flash_exception(exc, "Administración de RUT emisor")
    return redirect(url_for("context.index"))


@bp.post("/emisores/<int:issuer_id>/estado")
@permissions_required("CONTEXT_MANAGE")
def issuer_status(issuer_id: int):
    try:
        before, after = set_issuer_status(issuer_id, request.form.get("active", "N"))
        record_event("CONTEXT", "RM_CFACT_ISSUER", "STATUS", issuer_id, before, after)
        flash("Estado del RUT emisor actualizado.", "success")
    except Exception as exc:
        flash_exception(exc, "Administración de RUT emisor")
    return redirect(url_for("context.index"))


@bp.post("/flujos/nuevo")
@permissions_required("CONTEXT_MANAGE")
def flow_create():
    try:
        flow_id, after = create_flow(
            int(request.form.get("origin_id") or 0),
            int(request.form.get("emission_type_id") or 0),
            request.form.get("flow_code", ""),
            request.form.get("flow_name", ""),
            request.form.get("segment_label"),
        )
        record_event("CONTEXT", "RM_CFACT_FLOW", "INSERT", flow_id, after=after)
        flash("Flujo operativo creado correctamente.", "success")
    except Exception as exc:
        flash_exception(exc, "Administración de flujo operativo")
    return redirect(url_for("context.index"))


@bp.post("/flujos/<int:flow_id>/estado")
@permissions_required("CONTEXT_MANAGE")
def flow_status(flow_id: int):
    try:
        before, after = set_flow_status(flow_id, request.form.get("active", "N"))
        record_event("CONTEXT", "RM_CFACT_FLOW", "STATUS", flow_id, before, after)
        flash("Estado del flujo actualizado.", "success")
    except Exception as exc:
        flash_exception(exc, "Administración de flujo operativo")
    return redirect(url_for("context.index"))


@bp.post("/scopes/nuevo")
@permissions_required("CONTEXT_MANAGE")
def scope_create():
    try:
        scope_id, after = create_scope(request.form)
        record_event("CONTEXT", "RM_CFACT_SCOPE", "INSERT", scope_id, after=after)
        flash("Alcance creado correctamente.", "success")
    except Exception as exc:
        flash_exception(exc, "Administración de alcance")
    return redirect(url_for("context.index"))


@bp.post("/scopes/<int:scope_id>/estado")
@permissions_required("CONTEXT_MANAGE")
def scope_status(scope_id: int):
    try:
        before, after = set_scope_status(scope_id, request.form.get("active", "N"))
        record_event("CONTEXT", "RM_CFACT_SCOPE", "STATUS", scope_id, before, after)
        flash("Estado del alcance actualizado.", "success")
    except Exception as exc:
        flash_exception(exc, "Administración de alcance")
    return redirect(url_for("context.index"))
