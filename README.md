# SIS-FACT / Billing One

Billing One es la plataforma para control integral de facturación. Está separada funcionalmente de ATLAS, pero su base técnica deriva del patrón probado de ATLAS S.2.0: Flask, Oracle, LDAP, seguridad web, auditoría, pruebas, validadores y operación con Waitress.

## Versión vigente

- Versión: `v0.2.3`
- Rama vigente única: `main`
- Repositorio: `rrmunoz-coder/sis-fact`
- Ruta operativa: `K:\@@@@@sis-fact`
- Puerto web: `5040`

## Modelo funcional

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

`DOM` y `Ciclo` no son dimensiones universales: son segmentadores propios de determinados orígenes/flujos.

## Navegación web

Después del login se muestra una barra persistente:

```text
Inicio | Contexto | Fuentes e integraciones | Usuarios
```

Las opciones dependen de los permisos del usuario y la sección activa queda resaltada. Las pantallas hijas muestran una barra contextual `← Volver` hacia su menú padre.

## Administración web

### Contexto
- RUT emisores como raíz funcional;
- Negocios;
- Tipos de emisión (`MASIVO`, `ONLINE`, extensible);
- Flujos operativos y segmentador opcional (`DOM`, `CICLO`, `LOTE`, etc.);
- scopes operativos.

### Mantenedor de Orígenes v0.2.3

Ruta:

```text
Contexto -> Administrar Orígenes
```

Permite alta, activación/reactivación y baja lógica de orígenes funcionales. La baja se bloquea si el origen mantiene scopes o flujos activos.

Orígenes base actuales:

```text
ANDES
AMDOCS
SAP
ACEPTA
SGA
DHT
```

El catálogo es extensible: otros orígenes se agregan desde la web sin modificar código.

### Fuentes e integraciones
- conexiones Oracle, SQL Server, REST, SOAP y FILE;
- conexión separada del insumo;
- prueba de conexión;
- scopes de aplicación;
- insumos con tipo lógico y definición de extracción;
- secretos externos mediante `CREDENTIAL_REF`.

### Resultados operacionales
`RM_CFACT_EMISSION_STATUS` registra estado, completitud, cantidad esperada/emitida/rechazada, issues y monto por scope/periodo/segmento. `RM_CFACT_ISSUE` permite detallar incidencias.

## Base de datos

Para una base todavía en v0.2.0, primero aplicar:

```text
sql/migration_v0_2_0_to_v0_2_1/00_PRECHECK.sql
sql/migration_v0_2_0_to_v0_2_1/10_APPLY.sql
sql/migration_v0_2_0_to_v0_2_1/20_VALIDATE.sql
```

Para una base v0.2.1/v0.2.2 ya instalada, v0.2.3 no cambia estructura. Solo incorpora SGA y DHT de forma idempotente:

```text
sql/migration_v0_2_2_to_v0_2_3/10_ORIGENES_BASE.sql
```

> `SISGAV2` está expresamente fuera de cualquier migración, rollback o limpieza de Billing One.

## Validación técnica

```cmd
cd /d K:\@@@@@sis-fact
.venv\Scripts\python.exe scripts\validar_release.py
.venv\Scripts\python.exe scripts\validar_higiene.py
.venv\Scripts\python.exe -m compileall -q sisfact tests tools scripts *.py
.venv\Scripts\python.exe -m pytest tests -q
```

## Ejecución

```cmd
run_dev.cmd
```

Endpoints:

```text
http://127.0.0.1:5040/health
http://127.0.0.1:5040/api/v1/health
http://127.0.0.1:5040/login
http://127.0.0.1:5040/app
```
