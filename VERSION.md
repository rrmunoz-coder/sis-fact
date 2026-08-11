# Billing One v0.2.1

Fecha: 2026-08-11

Estado: corrección del modelo funcional antes de cargar configuración operativa.

## Cambio principal

La jerarquía de contexto queda definida como:

```text
RUT emisor -> Negocio -> Origen -> Tipo de emisión -> Flujo operativo opcional
```

`DOM` y `Ciclo` dejan de ser dimensiones universales. Se modelan como nombres de segmentación del flujo cuando corresponda al origen:

- ANDES / MASIVO -> `SEGMENT_LABEL=DOM`;
- AMDOCS / MASIVO -> `SEGMENT_LABEL=CICLO`;
- ONLINE -> flujos como Bill Now, Bill Online o Corrective Billing.

## Nuevas tablas

- `RM_CFACT_ORIGIN`
- `RM_CFACT_EMISSION_TYPE`
- `RM_CFACT_FLOW`
- `RM_CFACT_EMISSION_STATUS`
- `RM_CFACT_ISSUE`

Se retiran del modelo vigente:

- `RM_CFACT_DOM`
- `RM_CFACT_CYCLE`

El modelo completo pasa de 23 a 26 tablas Billing One.

## Resultados operacionales

Se incorpora base para almacenar por scope, periodo y segmento:

- estado;
- completitud;
- Q esperada;
- Q emitida;
- Q rechazada;
- Q issues;
- monto total;
- detalle de issues.

## Seguridad

Sin cambios de modelo. Oracle sigue autorizando usuarios/roles/permisos y LDAP sigue validando exclusivamente la contraseña de acceso web.

## Operación

Puerto web vigente: `5040`.

## Migración

Aplicar únicamente sobre v0.2.0 sin configuración de contexto/integraciones:

```text
sql/migration_v0_2_0_to_v0_2_1/00_PRECHECK.sql
sql/migration_v0_2_0_to_v0_2_1/10_APPLY.sql
sql/migration_v0_2_0_to_v0_2_1/20_VALIDATE.sql
```

`SISGAV2` permanece expresamente fuera de alcance.
