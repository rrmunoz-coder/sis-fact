# Billing One v0.2.4

Fecha: 2026-08-11

Estado: control operativo de ejecución de insumos.

## Cambio principal

La definición de un insumo deja de usar una frecuencia libre y pasa a tener una política real:

```text
Insumo -> Política -> Cola -> Worker -> Extraction Run
```

Modos:

- `MANUAL`: ejecución bajo demanda desde Billing One;
- `SCHEDULED`: scheduler crea ejecuciones por scope según agenda;
- `EXTERNAL`: KNIME/BOT/JOB/u otro ejecutor externo, con expectativa operativa registrada.

## Componentes

```text
BillingOne_Web
BillingOne_Scheduler
BillingOne_Worker
```

El worker está desacoplado de Flask/Waitress.

## Oracle

Nuevas tablas:

- `RM_CFACT_EXECUTION_POLICY`;
- `RM_CFACT_EXECUTION_QUEUE`.

El modelo completo queda en 28 tablas `RM_CFACT_*` de Billing One.

`RM_CFACT_EXTRACTION_RUN` conserva el histórico de cada intento.

## Adquisición v0.2.4

- Oracle SQL de solo lectura;
- SQL Server SQL de solo lectura;
- REST GET;
- archivos por patrón;
- SOAP: WSDL controlado, operación específica pendiente de parametrización.

`ROWS_READ` representa lo leído/observado. `ROWS_LOADED` permanece en 0 hasta implementar staging/normalización persistente.

## Orígenes

Se conserva el mantenedor dinámico de Orígenes de v0.2.3. `SGA` y `DHT` se incluyen de forma idempotente en el parche v0.2.4.

## Migración

```text
sql/migration_v0_2_3_to_v0_2_4/00_PRECHECK.sql
sql/migration_v0_2_3_to_v0_2_4/10_APPLY.sql
sql/migration_v0_2_3_to_v0_2_4/20_VALIDATE.sql
```

No modifica usuarios, LDAP, roles/permisos ni `SISGAV2`.

## Operación

Puerto web: `5040`.
