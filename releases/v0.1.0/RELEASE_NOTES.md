# SIS-FACT v0.1.0 - Base core e integración

## Resumen

Primera versión base del sistema independiente SIS-FACT / Billing One.

## Incluye

- App Flask mínima ejecutable.
- Configuración externa.
- Healthcheck.
- API para listar fuentes.
- API para healthcheck de fuentes.
- API de snapshot ejecutivo placeholder.
- Conectores base Oracle, SQL Server, REST, SOAP y archivos.
- Gateway conceptual de IA.
- SQL inicial de fuentes, extracciones, llamadas de integración, auditoría e IA.
- Documentación de arquitectura, integración, analítica e IA.

## No incluye aún

- Login real.
- Mantenedores visuales.
- Dashboard UI.
- Consultas reales de facturación.
- Integración real con SII, Billing Compare o facturadores.

## Validación mínima

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config.ini.example config.ini
run_dev.cmd
```

Probar:

```text
GET /
GET /health
GET /api/v1/sources
GET /api/v1/sources/health
GET /api/v1/analytics/executive-snapshot
```
