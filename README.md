# SIS-FACT / Billing One

Billing One es la plataforma multiempresa para control integral de facturación. Está separada funcionalmente de ATLAS, pero su **base técnica v0.2.0 deriva del patrón probado de ATLAS S.2.0**: Flask, Oracle, LDAP, seguridad web, auditoría, pruebas, validadores y operación con Waitress.

## Versión vigente

- Versión: `v0.2.0`
- Rama vigente única: `main`
- Repositorio: `rrmunoz-coder/sis-fact`
- Ruta operativa: `K:\@@@@@sis-fact`
- Puerto: `5060`

La historia de `v0.1.0` permanece en Git. No se mantienen carpetas paralelas, ZIP ni parches como versión activa.

## Principios de arquitectura

```text
SEGURIDAD TÉCNICA
Oracle autoriza + LDAP valida password + Flask mantiene sesión

CONTEXTO DE FACTURACIÓN
Empresa + RUT emisor + Negocio + DOM + Ciclo

ADQUISICIÓN
Conexión -> Insumo funcional -> Alcance

ORÍGENES
Oracle | SQL Server | REST | SOAP | Archivos

CONTROL
Validación de insumo -> Regla de facturación -> Resultado/Auditoría
```

El control depende del **insumo funcional y del contexto**, no del origen físico. Distintos negocios pueden usar fuentes completamente diferentes.

## Naming Oracle obligatorio

Todo objeto propio de Billing One comienza con `RM_CFACT_`.

## Estructura v0.2.0

```text
sisfact/
  auth/          autenticación LDAP/local
  users/         administración de usuarios
  templates/     interfaz web
  static/        CSS
  config.py      configuración estricta
  db.py          pool Oracle
  security.py    sesiones, roles y permisos
  audit.py       auditoría before/after
  web.py         health y panel base
sql/
  00_DIAGNOSTICO_PREVIO.sql
  10_SECURITY_BASE.sql
  11_VALIDAR_SECURITY.sql
  12_BOOTSTRAP_ADMIN.sql
  20_CONTEXT_BASE.sql
  21_VALIDAR_CONTEXT.sql
  30_INTEGRATION_BASE.sql
  31_VALIDAR_INTEGRATION.sql
  90_VALIDAR_BILLING_ONE.sql
  99_ROLLBACK_GREENFIELD.sql
  migration_v0_1/00_CONTEO_REAL_V0_1.sql
scripts/
tools/
tests/
```

## Instalación greenfield

> No usar este orden directamente sobre la instalación v0.1 existente hasta cerrar la migración.

```text
00_DIAGNOSTICO_PREVIO.sql
10_SECURITY_BASE.sql
11_VALIDAR_SECURITY.sql
12_BOOTSTRAP_ADMIN.sql
20_CONTEXT_BASE.sql
21_VALIDAR_CONTEXT.sql
30_INTEGRATION_BASE.sql
31_VALIDAR_INTEGRATION.sql
90_VALIDAR_BILLING_ONE.sql
```

En DBeaver ejecutar los archivos como **SQL Script** cuando contengan bloques PL/SQL terminados en `/`.

## Instalación Python

```cmd
cd /d K:\@@@@@sis-fact
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy config.ini.example config.ini
```

Generar un `secret_key` real:

```cmd
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

No versionar `config.ini`.

## Validación técnica

```cmd
.venv\Scripts\python.exe scripts\validar_release.py
.venv\Scripts\python.exe scripts\validar_higiene.py
.venv\Scripts\python.exe -m compileall -q sisfact tests tools scripts *.py
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe tools\test_oracle_connection.py
.venv\Scripts\python.exe tools\test_ldap_bind.py
```

## Ejecución

Desarrollo:

```cmd
run_dev.cmd
```

Waitress / servicio:

```cmd
.venv\Scripts\python.exe service_entry.py
```

Endpoints base:

```text
http://127.0.0.1:5060/health
http://127.0.0.1:5060/api/v1/health
http://127.0.0.1:5060/login
http://127.0.0.1:5060/app
http://127.0.0.1:5060/me
```

## Migración desde v0.1

**No borrar tablas todavía.** Ejecutar primero:

```text
sql/migration_v0_1/00_CONTEO_REAL_V0_1.sql
```

`SISGAV2` es un objeto ajeno a Billing One y está expresamente fuera de cualquier limpieza o rollback de este proyecto.

Ver `docs/MIGRACION_V0_1_V0_2.md`.
