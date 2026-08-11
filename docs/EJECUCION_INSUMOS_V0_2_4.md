# Control de ejecución de insumos — Billing One v0.2.4

## Objetivo

Separar la definición funcional del insumo de su política de ejecución y de cada corrida real.

```text
INSUMO
  -> POLITICA
  -> COLA
  -> WORKER
  -> RM_CFACT_EXTRACTION_RUN
  -> calidad/completitud/control de facturación
```

## Modos

### MANUAL

No existe agenda automática. Un usuario con `CONTROL_EXECUTE` y acceso `EXECUTE` al scope puede usar **Ejecutar ahora**.

### SCHEDULED

`BillingOne_Scheduler` revisa políticas vencidas cada 30 segundos y crea una fila de cola por scope activo del insumo. El scheduler no ejecuta SQL ni consume APIs.

Periodicidades soportadas inicialmente:

- cada N minutos;
- cada N horas;
- diario;
- semanal;
- mensual.

### EXTERNAL

Identifica insumos entregados por KNIME, BOT, JOB SQL u otro ejecutor. Billing One almacena el nombre del ejecutor y opcionalmente la próxima recepción esperada. **v0.2.4 no ejecuta ni confirma automáticamente el proceso externo**; el callback/registro automático del ejecutor externo es una fase posterior.

## Procesos separados

```text
BillingOne_Web       Flask/Waitress - configuración y visualización
BillingOne_Scheduler agenda y encola
BillingOne_Worker    toma la cola y ejecuta adquisición
```

El worker es independiente de Flask/Waitress para que una consulta larga o una API lenta no bloquee la web.

## Tablas

### RM_CFACT_EXECUTION_POLICY

Una política por `DATA_SOURCE_ID`.

Principales campos:

- `EXECUTION_MODE`;
- `FREQUENCY_TYPE`;
- `INTERVAL_VALUE`;
- `RUN_TIME`;
- `DAY_OF_WEEK`;
- `DAY_OF_MONTH`;
- `TIMEOUT_MINUTES`;
- `MAX_RETRIES`;
- `EXTERNAL_EXECUTOR`;
- `NEXT_DUE_AT`.

### RM_CFACT_EXECUTION_QUEUE

Una solicitud concreta por `DATA_SOURCE_ID + SCOPE_ID`.

Estados:

```text
PENDING -> RUNNING -> SUCCESS / WARNING / ERROR
```

Los reintentos reutilizan la misma fila de cola y crean una nueva `RM_CFACT_EXTRACTION_RUN` por intento.

### RM_CFACT_EXTRACTION_RUN

Continúa siendo el histórico técnico de ejecución. En v0.2.4 `ROWS_READ` expresa lo leído/observado por la adquisición. `ROWS_LOADED` queda en 0 hasta incorporar staging/normalización persistente.

## Motores de adquisición v0.2.4

- Oracle SQL: `SELECT` / `WITH` de solo lectura; cuenta filas sin cargarlas completas en memoria.
- SQL Server SQL: `SELECT` / `WITH` de solo lectura.
- REST: HTTP GET; estima cantidad por listas JSON conocidas.
- FILE: cuenta archivos que cumplen el patrón.
- SOAP: valida accesibilidad del WSDL y termina en `WARNING`; una operación SOAP real requiere parametrización por insumo.

## Seguridad

- No se permiten DML/DDL en definiciones SQL de adquisición.
- Las credenciales siguen fuera de Oracle mediante `CREDENTIAL_REF`.
- `CONTROL_EXECUTE` autoriza la acción general.
- Para usuarios no ADMIN también se exige acceso `EXECUTE` al scope.
- El worker nunca recibe password LDAP.

## Importante: adquisición no es completitud

```text
EXTRACCION SUCCESS
        !=
INSUMO COMPLETO
        !=
CONTROL DE FACTURACION OK
```

Ejemplo:

```text
Extracción: SUCCESS
Rows read: 2.950.000
Completitud esperada: 94,3 %
Control Billing: WARNING
```

La capa de completitud se conecta posteriormente con `RM_CFACT_EMISSION_STATUS`.

## Instalación en una base v0.2.3

DBeaver:

```text
sql/migration_v0_2_3_to_v0_2_4/00_PRECHECK.sql
sql/migration_v0_2_3_to_v0_2_4/10_APPLY.sql
sql/migration_v0_2_3_to_v0_2_4/20_VALIDATE.sql
```

Después actualizar código y validar:

```cmd
.venv\Scripts\python.exe scripts\validar_release.py
.venv\Scripts\python.exe -m compileall -q sisfact tests tools scripts *.py
.venv\Scripts\python.exe -m pytest tests -q
```

Prueba manual de procesos, antes de instalarlos como servicios:

```cmd
.venv\Scripts\python.exe scheduler_entry.py
.venv\Scripts\python.exe worker_entry.py
```

Cuando estén validados pueden instalarse con NSSM:

```text
service/install_scheduler.cmd
service/install_worker.cmd
```

`SISGAV2` permanece fuera de alcance.
