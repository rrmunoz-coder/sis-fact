# Changelog

## v0.1.0 - consolidada

### Incluye

- Inicialización del repositorio `sis-fact`.
- Base independiente para SIS-FACT / Billing One.
- Core Flask separado de ATLAS/Altas.
- Configuración externa mediante `config.ini`.
- Ruta operativa única: `K:\@@@@@sis-fact`.
- Script único de ejecución local: `run_dev.cmd`.
- Login LDAP estilo ATLAS con autorización local en Oracle.
- Normalización de usuario para login: `usuario`, `DOMINIO\usuario` o `usuario@dominio`.
- Panel base `/app` después de login.
- Healthcheck simple `/health` y JSON `/api/v1/health`.
- Capa de integración para orígenes de datos.
- Conectores base para Oracle, SQL Server, REST, SOAP y archivos.
- SQL inicial con prefijo obligatorio `RM_CFACT_`.
- Tabla de usuarios `RM_CFACT_USER`.
- Documentación de instalación, LDAP, naming Oracle y modelo de entregas.

### Decisiones

- ATLAS y SIS-FACT se mantienen como sistemas separados.
- SIS-FACT adopta la dinámica operativa de ATLAS: Flask + Oracle local + LDAP + configuración externa.
- GitHub mantiene una sola versión vigente en `main`.
- Los parches se entregan como commits, no como carpetas o ZIP paralelos.
- No se versionan `config.ini`, `.venv`, `.venv.venv`, ZIP, `sis-fact-main` ni datos productivos.

### Pendiente

- Crear módulos productivos de flujos, ciclos, ejecuciones y fases.
- Implementar dashboard operacional y directivo.
- Implementar integración real con Billing Compare, facturador electrónico, SII/RCV y F29.
- Instalar como servicio Windows con Waitress/NSSM cuando el login quede validado en ambiente.
