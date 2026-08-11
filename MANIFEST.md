# Manifiesto Billing One v0.2.1

## Contenido vigente

```text
sisfact/       aplicación Flask
sql/           DDL, validadores, migraciones y rollback greenfield
docs/          arquitectura y modelo funcional
scripts/       validación de release/higiene
tools/         diagnóstico Oracle/LDAP
tests/         pruebas automáticas
requirements.txt
config.ini.example
run_dev.cmd
service_entry.py
wsgi.py
README.md
VERSION.md
CHANGELOG.md
```

## Modelo v0.2.1

```text
RUT emisor -> Negocio -> Origen -> Tipo de emisión -> Flujo opcional
```

Resultados operacionales: estado, completitud, cantidades, rechazos, issues y monto.

## Exclusiones obligatorias

```text
config.ini
.venv/
logs/
__pycache__/
*.pyc
*.log
*.zip
sis-fact-main/
nssm.exe
credenciales o datos productivos
```

## Regla

`main` contiene una sola versión vigente. La historia anterior se conserva en Git, no como carpetas paralelas. `SISGAV2` permanece fuera de Billing One.
