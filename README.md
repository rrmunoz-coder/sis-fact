# SIS-FACT / Billing One

Billing One es la plataforma para control integral de facturación. Está separada funcionalmente de ATLAS, pero su base técnica deriva del patrón probado de ATLAS S.2.0: Flask, Oracle, LDAP, seguridad web, auditoría, pruebas, validadores y operación con Waitress.

## Versión vigente

- Versión: `v0.2.1`
- Rama vigente única: `main`
- Repositorio: `rrmunoz-coder/sis-fact`
- Ruta operativa: `K:\@@@@@sis-fact`
- Puerto web: `5040`

## Modelo funcional v0.2.1

```text
SEGURIDAD
Oracle autoriza + LDAP valida password + Flask mantiene sesión
        |
        v
CONTEXTO OPERATIVO
RUT emisor -> Negocio -> Origen -> Tipo de emisión -> Flujo opcional
        |
        |  Ejemplos de flujo/segmentación:
        |  ANDES  / MASIVO -> segmentador DOM
        |  AMDOCS / MASIVO -> segmentador CICLO
        |  AMDOCS / ONLINE -> Bill Now / Bill Online / Corrective Billing
        |
        v
ADQUISICIÓN
Conexión técnica -> Insumo funcional -> Scope
        |
        +--> Oracle
        +--> SQL Server
        +--> REST / SOAP
        +--> Archivos
        |
        v
RESULTADO OPERACIONAL
Estado + Completitud + Q esperada + Q emitida + Rechazos + Issues + Monto
```

### Regla clave

`DOM` y `Ciclo` **no son dimensiones universales** de Billing One. Son nombres de segmentación propios de ciertos orígenes/flujos. Se representan mediante `RM_CFACT_FLOW.SEGMENT_LABEL` y el valor runtime se registra en `RM_CFACT_EMISSION_STATUS.SEGMENT_VALUE`.

El **Origen funcional** (`ANDES`, `AMDOCS`, `SAP`, `ACEPTA`, etc.) tampoco equivale a la conexión técnica. Una conexión describe cómo acceder; un alcance describe dónde aplica funcionalmente.

## Administración web

Después del login:

```text
/app
  -> Administración de usuarios
  -> Contexto de facturación
  -> Fuentes e integraciones
```

### Contexto

- RUT emisores como raíz funcional;
- Negocios;
- Orígenes funcionales;
- Tipos de emisión (`MASIVO`, `ONLINE`, extensible);
- Flujos operativos y segmentador opcional (`DOM`, `CICLO`, `LOTE`, etc.);
- scopes operativos.

`RM_CFACT_COMPANY` se conserva únicamente como agrupación opcional del RUT emisor; no forma parte de la jerarquía operativa del scope.

### Fuentes e integraciones

- conexiones Oracle, SQL Server, REST, SOAP y FILE;
- conexión separada del insumo;
- prueba de conexión;
- scopes de aplicación;
- insumos con tipo lógico y definición de extracción;
- secretos externos mediante `CREDENTIAL_REF`;
- desactivación en vez de borrado físico.

### Resultados operacionales

`RM_CFACT_EMISSION_STATUS` registra por scope/periodo/segmento:

- estado;
- completitud;
- cantidad esperada;
- cantidad emitida;
- cantidad rechazada;
- cantidad de issues;
- monto total.

`RM_CFACT_ISSUE` permite detallar issues cuando corresponda.

## SQL

Instalación greenfield:

```text
sql/10_SECURITY_BASE.sql
sql/11_VALIDAR_SECURITY.sql
sql/20_CONTEXT_BASE.sql
sql/21_VALIDAR_CONTEXT.sql
sql/30_INTEGRATION_BASE.sql
sql/31_VALIDAR_INTEGRATION.sql
sql/40_OPERATIONAL_BASE.sql
sql/41_VALIDAR_OPERATIONAL.sql
sql/90_VALIDAR_BILLING_ONE.sql
```

Migración de la base v0.2.0 instalada el 11-08-2026:

```text
sql/migration_v0_2_0_to_v0_2_1/00_PRECHECK.sql
sql/migration_v0_2_0_to_v0_2_1/10_APPLY.sql
sql/migration_v0_2_0_to_v0_2_1/20_VALIDATE.sql
```

> `SISGAV2` está expresamente fuera de cualquier migración, rollback o limpieza de Billing One.

## Instalación Python

Se recomienda Python 3.12 x64.

```cmd
cd /d K:\@@@@@sis-fact
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Validación técnica

```cmd
.venv\Scripts\python.exe scripts\validar_release.py
.venv\Scripts\python.exe scripts\validar_higiene.py
.venv\Scripts\python.exe -m compileall -q sisfact tests tools scripts *.py
.venv\Scripts\python.exe -m pytest tests -q
.venv\Scripts\python.exe tools\test_oracle_connection.py
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
http://127.0.0.1:5040/health
http://127.0.0.1:5040/api/v1/health
http://127.0.0.1:5040/login
http://127.0.0.1:5040/app
```
