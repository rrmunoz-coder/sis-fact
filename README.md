# SIS-FACT / Billing One

Billing One es la plataforma para control integral de facturación. Su base técnica deriva del patrón probado de ATLAS S.2.0, pero su dominio funcional es independiente.

## Versión vigente

- Versión: `v0.2.4`
- Rama: `main`
- Repositorio: `rrmunoz-coder/sis-fact`
- Ruta: `K:\@@@@@sis-fact`
- Puerto web: `5040`

## Modelo funcional

```text
RUT emisor -> Negocio -> Origen -> Tipo de emisión -> Flujo opcional
                                      |
                                      v
Conexión técnica -> Insumo -> Política de ejecución -> Cola -> Worker
                                      |
                                      v
Extracción -> Calidad/Completitud -> Control Billing -> Issues/Estado
```

`DOM` y `Ciclo` son segmentadores de determinados flujos, no dimensiones universales.

## Navegación

```text
Inicio | Contexto | Fuentes e integraciones | Ejecuciones | Usuarios
```

Las opciones se muestran según permisos.

## Contexto

Incluye mantenedores para RUT emisor, negocio, origen, tipo de emisión, flujo y scope.

El mantenedor de Orígenes permite alta, edición de nombre, activación/reactivación y baja lógica. La baja se bloquea si existen scopes o flujos activos. El catálogo es extensible; base actual: ANDES, AMDOCS, SAP, ACEPTA, SGA y DHT.

## Fuentes e integraciones

- conexiones Oracle, SQL Server, REST, SOAP y FILE;
- conexión separada del insumo funcional;
- secretos externos mediante `CREDENTIAL_REF`;
- scopes de aplicación;
- prueba de conexión;
- política de ejecución por insumo.

## Control de ejecución v0.2.4

Modos:

- `MANUAL`: botón **Ejecutar ahora**;
- `SCHEDULED`: `BillingOne_Scheduler` encola según agenda;
- `EXTERNAL`: KNIME/BOT/JOB/otro; Billing One registra la expectativa, sin ejecutarlo internamente.

Procesos:

```text
BillingOne_Web       interfaz
BillingOne_Scheduler agenda y encola
BillingOne_Worker    procesa la cola
```

Oracle agrega:

- `RM_CFACT_EXECUTION_POLICY`;
- `RM_CFACT_EXECUTION_QUEUE`.

`RM_CFACT_EXTRACTION_RUN` conserva el histórico de intentos.

Motores iniciales del worker:

- Oracle SQL solo lectura;
- SQL Server SQL solo lectura;
- REST GET;
- FILE por patrón;
- SOAP: control WSDL en `WARNING` hasta parametrizar operación específica.

> `SUCCESS` de extracción significa que el origen pudo leerse. No significa por sí solo que el insumo esté completo ni que el control de facturación sea OK.

## Migraciones

Base v0.2.0 -> modelo funcional v0.2.1:

```text
sql/migration_v0_2_0_to_v0_2_1/00_PRECHECK.sql
sql/migration_v0_2_0_to_v0_2_1/10_APPLY.sql
sql/migration_v0_2_0_to_v0_2_1/20_VALIDATE.sql
```

Base v0.2.3 -> ejecución v0.2.4:

```text
sql/migration_v0_2_3_to_v0_2_4/00_PRECHECK.sql
sql/migration_v0_2_3_to_v0_2_4/10_APPLY.sql
sql/migration_v0_2_3_to_v0_2_4/20_VALIDATE.sql
```

El parche v0.2.4 incorpora SGA/DHT de forma idempotente si faltan. `SISGAV2` permanece fuera de alcance.

## Validación

```cmd
cd /d K:\@@@@@sis-fact
.venv\Scripts\python.exe scripts\validar_release.py
.venv\Scripts\python.exe scripts\validar_higiene.py
.venv\Scripts\python.exe -m compileall -q sisfact tests tools scripts *.py
.venv\Scripts\python.exe -m pytest tests -q
```

## Desarrollo

```cmd
run_dev.cmd
```

Prueba scheduler/worker en consola antes de instalarlos como servicio:

```cmd
.venv\Scripts\python.exe scheduler_entry.py
.venv\Scripts\python.exe worker_entry.py
```

Servicios NSSM, una vez validados:

```text
service/install_service.cmd
service/install_scheduler.cmd
service/install_worker.cmd
```

Endpoints principales:

```text
http://127.0.0.1:5040/health
http://127.0.0.1:5040/login
http://127.0.0.1:5040/app
http://127.0.0.1:5040/operacion/ejecuciones
```
