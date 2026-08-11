from __future__ import annotations

from flask import Blueprint, Response, jsonify, redirect, render_template, session, url_for

from .security import login_required

bp = Blueprint("web", __name__)


@bp.get("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("web.app_home"))
    return redirect(url_for("auth.login"))


@bp.get("/health")
def health():
    return Response("OK - SIS-FACT / Billing One\n", mimetype="text/plain")


@bp.get("/api/v1/health")
def api_health():
    return jsonify({
        "status": "OK",
        "service": "sis-fact",
        "name": "Billing One",
        "version": "0.2.3",
    })


@bp.get("/app")
@login_required
def app_home():
    return render_template("app/home.html")
