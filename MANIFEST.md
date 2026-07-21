# Manifiesto SIS-FACT v0.1.0

## Contenido esperado

```text
sisfact/                     aplicación Flask
sisfact/core/                core común propio
sisfact/integrations/        conectores de fuentes de datos
sisfact/analytics/           analítica e IA
sisfact/web/                 rutas web
sql/                         scripts Oracle
configs/                     plantillas de configuración opcionales
docs/                        documentación funcional/técnica
prompts/                     prompt de construcción
releases/v0.1.0/             notas de versión
tests/                       pruebas básicas
requirements.txt             dependencias Python
config.ini.example           configuración ejemplo sin secretos
run_dev.cmd                  ejecución local
wsgi.py                      entrada WSGI
README.md                    resumen del proyecto
VERSION.md                   versión vigente
CHANGELOG.md                 historial de cambios
```

## Exclusiones obligatorias

```text
config.ini                  configuración real
.venv/                      entorno virtual
__pycache__/                caché Python
*.pyc                       bytecode
*.log                       logs
*_old/                      respaldos antiguos
_backup*/                   respaldos temporales
*.zip                       paquetes generados
*.xlsx con datos reales      archivos sensibles
*.csv con datos reales       archivos sensibles
```

## Regla de oro

El repositorio contiene código, SQL, documentación, prompts y scripts reproducibles. No contiene secretos, credenciales ni datos productivos.
