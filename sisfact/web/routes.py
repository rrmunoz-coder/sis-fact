from __future__ import annotations

from dataclasses import asdict

from flask import Flask, current_app, jsonify

from sisfact.analytics.reporting_service import ReportingService
from sisfact.integrations.factory import ConnectorFactory
from sisfact.integrations.registry import default_registry


def register_routes(app: Flask) -> None:
    @app.get("/")
    def home():
        return jsonify({
            "system": "SIS-FACT / Billing One",
            "version": "0.1.0",
            "status": "OK",
            "modules": ["core", "integrations", "analytics"],
        })

    @app.get("/health")
    def health():
        return jsonify({"status": "OK", "service": "sis-fact", "version": "0.1.0"})

    @app.get("/api/v1/sources")
    def list_sources():
        registry = default_registry()
        return jsonify([asdict(source) for source in registry.list_active()])

    @app.get("/api/v1/sources/health")
    def sources_health():
        registry = default_registry()
        factory = ConnectorFactory(current_app.config["CONFIG_RAW"])
        results = []
        for source in registry.list_active():
            try:
                connector = factory.create(source)
                results.append(connector.healthcheck())
            except Exception as exc:
                results.append({"source": source.source_code, "status": "ERROR", "error": str(exc)})
        return jsonify(results)

    @app.get("/api/v1/analytics/executive-snapshot")
    def executive_snapshot():
        snapshot = ReportingService().executive_snapshot()
        return jsonify(asdict(snapshot))
