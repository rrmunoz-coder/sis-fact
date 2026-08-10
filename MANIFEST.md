# Manifiesto Billing One v0.2.0

## Contenido vigente

```text
sisfact/       aplicación Flask
sql/           DDL, validadores, migración y rollback greenfield
docs/          arquitectura, instalación y migración
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

## Exclusiones obligatorias

```text
config.ini
.venv/
.venv.venv/
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

`main` contiene una sola versión vigente. La historia anterior se conserva en Git, no como carpetas paralelas.
