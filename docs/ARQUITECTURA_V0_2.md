# Arquitectura Billing One v0.2.1

## Capas

```text
IDENTIDAD
LDAP valida contraseña corporativa
        |
AUTORIZACIÓN
Oracle: usuario + rol + permisos + scopes
        |
CONTEXTO FUNCIONAL
RUT emisor -> Negocio -> Origen -> Tipo de emisión -> Flujo opcional
        |
ADQUISICIÓN
Conexión técnica -> Insumo funcional -> Scope
        |
TRAZABILIDAD
Extracción / llamada de integración
        |
RESULTADO
Estado + Completitud + Q emitida + Rechazos + Issues + Monto
```

## Contexto

La raíz funcional es `RM_CFACT_ISSUER` (RUT emisor). `RM_CFACT_COMPANY` se conserva como agrupación opcional y no pertenece al scope operativo.

`RM_CFACT_SCOPE` relaciona obligatoriamente:

- RUT emisor;
- Negocio;
- Origen;
- Tipo de emisión;
- Flujo opcional.

`RM_CFACT_FLOW` pertenece a una combinación Origen + Tipo. La FK compuesta de Scope impide asociar un flujo a un origen/tipo distinto.

### DOM y Ciclo

No son dimensiones universales. `RM_CFACT_FLOW.SEGMENT_LABEL` define el nombre del segmentador cuando existe; `RM_CFACT_EMISSION_STATUS.SEGMENT_VALUE` guarda el valor observado en runtime.

Ejemplos:

```text
ANDES  / MASIVO / flujo FACT_MASIVA / SEGMENT_LABEL=DOM   / SEGMENT_VALUE=22
AMDOCS / MASIVO / flujo FACT_MASIVA / SEGMENT_LABEL=CICLO / SEGMENT_VALUE=22
AMDOCS / ONLINE / flujo BILL_NOW   / sin segmentador
```

## Origen funcional vs conexión técnica

`RM_CFACT_ORIGIN` describe el sistema/plataforma de negocio: ANDES, AMDOCS, SAP, ACEPTA, etc.

`RM_CFACT_CONNECTION` describe el transporte/acceso: Oracle, SQL Server, REST, SOAP o archivo.

No se duplican. La relación funcional de un insumo con su origen se obtiene a través de `RM_CFACT_SOURCE_SCOPE -> RM_CFACT_SCOPE`.

## Resultado operacional

`RM_CFACT_EMISSION_STATUS` persiste el resumen de una emisión/control por scope, periodo y segmento. `RM_CFACT_ISSUE` detalla incidencias opcionales.

Este modelo habilita el panel futuro:

```text
RUT | Negocio | Origen | Tipo | Flujo | Estado | Completitud | Q emisión | Rechazos | Issues | Monto
```

## Seguridad

No cambia en v0.2.1:

- Oracle autoriza;
- LDAP solo autentica contraseña web;
- roles/permisos/scopes se resuelven en tablas `RM_CFACT_*`;
- la contraseña LDAP nunca se almacena.
