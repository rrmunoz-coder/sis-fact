# SIS-FACT / Billing One

Billing One es la plataforma multiempresa para control integral de facturación. Está separada funcionalmente de ATLAS, pero su **base técnica v0.2.0 deriva del patrón probado de ATLAS S.2.0**: Flask, Oracle, LDAP, seguridad web, auditoría, pruebas, validadores y operación con Waitress.

## Versión vigente

- Versión: `v0.2.0`
- Rama vigente única: `main`
- Repositorio: `rrmunoz-coder/sis-fact`
- Ruta operativa: `K:\@@@@@sis-fact`
- Puerto: `5060`

La historia de `v0.1.0` permanece en Git. No se mantienen carpetas paralelas, ZIP ni parches como versión activa.

## Arquitectura

```text
SEGURIDAD
Oracle autoriza + LDAP valida password + Flask mantiene sesión
        |
        v
CONTEXTO
Empresa + RUT emisor + Negocio + DOM + Ciclo -> Scope
        |
        v
ADQUISICIÓN
Conexión -> Insumo funcional -> Scope
        |
        +--> Oracle
        +--> SQL Server
        +--> REST / SOAP
        +--> Archivos
        |
        v
CONTROL
Validación de insumo -> Regla de facturación -> Resultado/Auditoría
```

El control depende del **insumo funcional y del contexto**, no del origen físico. Distintos negocios pueden usar fuentes completamente diferentes.

## Administración web disponible

Después del login:

```text
/app
  -> Administración de usuarios
  -> Contexto de facturación
  -> Fuentes e integraciones
```

### Usuarios

- Oracle autoriza usuario/rol/permisos.
- LDAP valida password.
- sesiones revocables y bloqueo por intentos;
- asignación de scopes por Ver / Ejecutar / Configurar;
- ADMIN tiene alcance global.

### Contexto

- Empresas;
- RUT emisores;
- Negocios;
- DOM;
- Ciclos;
- scopes multidimensionales.

### Fuentes e integraciones

- conexiones Oracle, SQL Server, REST, SOAP y FILE;
- conexión separada del insumo;
- prueba de conexión;
- scopes de aplicación;
- insumos con tipo lógico y definición de extracción;
- desactivación en vez de borrado físico.

## Seguridad de credenciales

`RM_CFACT_CONNECTION.CONFIG_JSON` no admite secretos. `CREDENTIAL_REF` apunta a una sección externa de `config.ini` o a un gestor de secretos futuro.

El archivo `config.ini` real nunca se versiona.

## Naming Oracle

Todo objeto propio de Billing One comienza con:

```text
RM_CFACT_
```

## SQL v0.2.0

```text
sql/00_DIAGNOSTICO_PREVIO.sql
sql/10_SECURITY_BASE.sql
sql/11_VALIDAR_SECURITY.sql
sql/12_BOOTSTRAP_ADMIN.sql
sql/20_CONTEXT_BASE.sql
sql/21_VALIDAR_CONTEXT.sql
sql/30_INTEGRATION_BASE.sql
sql/31_VALIDAR_INTEGRATION.sql
sql/90_VALIDAR_BILLING_ONE.sql
sql/99_ROLLBACK_GREENFIELD.sql
sql/migration_v0_1/00_CONTEO_REAL_V0_1.sql
```

> No ejecutar los DDL greenfield directamente sobre la instalación v0.1 actual hasta cerrar la migración.

## Instalación Python

Se recomienda Python 3.12 x64.

```cmd
cd /d K:\@@@@@sis-fact
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy config.ini.example config.ini
```

Generar `secret_key` real:

```cmd
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

## Validación técnica

```cmd
.venv\Scripts\python.exe scripts\validar_release.py
.venv\Scripts\python.exe scripts\validar_higiene.py
.venv\Scripts\python.exe -m compileall -q sisfact tests tools scripts *.py
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe tools\test_oracle_connection.py
.venv\Scripts\python.exe tools\test_ldap_transport.py
.venv\Scripts\python.exe tools\test_ldap_bind.py
```

## Ejecución

Desarrollo:

```cmd
run_dev.cmd
```

Waitress:

```cmd
.venv\Scripts\python.exe service_entry.py
```

Endpoints:

```text
http://127.0.0.1:5060/health
http://127.0.0.1:5060/api/v1/health
http://127.0.0.1:5060/login
http://127.0.0.1:5060/app
http://127.0.0.1:5060/me
```

## Migración v0.1

**No borrar tablas todavía.** Primero ejecutar:

```text
sql/migration_v0_1/00_CONTEO_REAL_V0_1.sql
```

`SISGAV2` es un objeto ajeno a Billing One y está expresamente fuera de cualquier limpieza o rollback.

## Documentación

```text
docs/ARQUITECTURA_V0_2.md
docs/INSTALACION_V0_2.md
docs/MIGRACION_V0_1_V0_2.md
docs/FUENTES_E_INTEGRACIONES_V0_2.md
docs/ESTADO_PROYECTO.md
```
