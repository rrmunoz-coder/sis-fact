from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..audit import record_event
from ..errors import flash_exception
from ..security import permissions_required
from .service import (
    catalogs_for_scope,
    create_issuer,
    create_scope,
    create_simple_catalog,
    list_issuers,
    list_scopes,
    list_simple_catalog,
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
        doms=list_simple_catalog("dom"),
        cycles=list_simple_catalog("cycle"),
        scopes=list_scopes(),
        scope_catalogs=catalogs_for_scope(),
    )


@bp.post("/catalogo/<kind>/nuevo")
@permissions_required("CONTEXT_MANAGE")
def create_catalog(kind: str):
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
        issuer_id, after = create_issuer(
            int(request.form.get("company_id") or 0),
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
