from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from ..audit import record_event
from ..errors import flash_exception
from ..security import permissions_required
from .service import (
    create_ldap_user,
    get_user,
    list_roles,
    list_scope_catalog,
    list_users,
    reset_failed_attempts,
    set_user_status,
    update_user,
)

bp = Blueprint("users", __name__, url_prefix="/administracion/usuarios")


def _scope_ids(name: str) -> list[int]:
    return [int(value) for value in request.form.getlist(name)]


@bp.get("")
@permissions_required("USER_MANAGE")
def index():
    query = request.args.get("q", "").strip()
    return render_template("users/list.html", users=list_users(query), q=query)


@bp.route("/nuevo", methods=["GET", "POST"])
@permissions_required("USER_MANAGE")
def create():
    if request.method == "POST":
        try:
            user_id, after = create_ldap_user(
                request.form,
                _scope_ids("view_scope_ids"),
                _scope_ids("execute_scope_ids"),
                _scope_ids("configure_scope_ids"),
            )
            record_event("USERS", "RM_CFACT_USER", "INSERT", user_id, after=after)
            flash("Usuario LDAP creado correctamente.", "success")
            return redirect(url_for("users.index"))
        except Exception as exc:
            flash_exception(exc, "Gestión de usuarios")
    return render_template(
        "users/form.html",
        user=None,
        roles=list_roles(),
        scopes=list_scope_catalog(),
        scope_access={},
    )


@bp.route("/<int:user_id>/editar", methods=["GET", "POST"])
@permissions_required("USER_MANAGE")
def edit(user_id: int):
    user = get_user(user_id)
    if not user:
        abort(404)
    if request.method == "POST":
        try:
            before, after = update_user(
                user_id,
                request.form,
                _scope_ids("view_scope_ids"),
                _scope_ids("execute_scope_ids"),
                _scope_ids("configure_scope_ids"),
            )
            record_event("USERS", "RM_CFACT_USER", "UPDATE", user_id, before, after)
            flash("Usuario actualizado. Sus sesiones anteriores fueron revocadas.", "success")
            return redirect(url_for("users.index"))
        except Exception as exc:
            flash_exception(exc, "Gestión de usuarios")
            user = get_user(user_id) or user
    return render_template(
        "users/form.html",
        user=user,
        roles=list_roles(),
        scopes=list_scope_catalog(),
        scope_access=user.get("scope_access", {}),
    )


@bp.post("/<int:user_id>/estado")
@permissions_required("USER_MANAGE")
def status(user_id: int):
    try:
        before, after = set_user_status(user_id, request.form.get("active", "N"))
        record_event("USERS", "RM_CFACT_USER", "STATUS", user_id, before, after)
        flash("Estado actualizado y sesiones revocadas.", "success")
    except Exception as exc:
        flash_exception(exc, "Gestión de usuarios")
    return redirect(url_for("users.index"))


@bp.post("/<int:user_id>/reiniciar-intentos")
@permissions_required("USER_MANAGE")
def reset_attempts(user_id: int):
    try:
        reset_failed_attempts(user_id)
        record_event("USERS", "RM_CFACT_USER_AUTH", "RESET_FAILED_ATTEMPTS", user_id)
        flash("Intentos fallidos reiniciados.", "success")
    except Exception as exc:
        flash_exception(exc, "Gestión de usuarios")
    return redirect(url_for("users.index"))
