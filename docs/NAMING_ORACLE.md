# Norma de naming Oracle SIS-FACT / Billing One

## Regla obligatoria

Todas las tablas propias del sistema SIS-FACT / Billing One deben comenzar con:

```text
RM_CFACT_
```

Esta regla aplica a:

- Tablas core.
- Tablas de seguridad.
- Tablas de integración.
- Tablas de auditoría.
- Tablas de analítica.
- Tablas funcionales futuras de facturación.

## Ejemplos aprobados

```text
RM_CFACT_USER
RM_CFACT_DATA_SOURCE
RM_CFACT_EXTRACTION_RUN
RM_CFACT_INTEGRATION_CALL
RM_CFACT_AUDIT_LOG
RM_CFACT_AI_PROVIDER
RM_CFACT_FLOW
RM_CFACT_EXECUTION
RM_CFACT_BILLING_CASE
RM_CFACT_INVOICE
RM_CFACT_PAYMENT
RM_CFACT_TAX_RECONCILIATION
```

## Nombres no permitidos para tablas propias

```text
SIS_USER
SIS_DATA_SOURCE
BILLING_CASE
BO_DATA_SOURCE
USER
DATA_SOURCE
```

## Criterio

El prefijo `RM_CFACT_` permite distinguir objetos propios del sistema de objetos productivos, fuentes externas, tablas temporales o tablas heredadas.

## Índices y constraints

Los índices y constraints también deben incluir el prefijo lógico cuando sea razonable:

```text
UK_RM_CFACT_USER_USERNAME
CK_RM_CFACT_USER_ACTIVE
IX_RM_CFACT_USER_ROLE
FK_RM_CFACT_EXT_DS
```

## Excepción

Solo quedan fuera de esta regla:

- Vistas externas que apunten a tablas legacy.
- Sinónimos hacia tablas productivas existentes.
- Tablas temporales explícitamente descartables, si el DBA exige otro estándar.

En esos casos se debe documentar la excepción en el script SQL correspondiente.
