# Modelo funcional Billing One v0.2.1

## Principio

Billing One separa tres conceptos que antes podían confundirse:

1. **Contexto funcional:** dónde ocurre la facturación.
2. **Acceso técnico:** cómo se obtiene el dato.
3. **Resultado operacional:** qué ocurrió con la emisión/control.

## Contexto funcional

```text
RUT emisor
  -> Negocio
    -> Origen
      -> Tipo de emisión
        -> Flujo operativo opcional
```

### RUT emisor
Entidad fiscal que emite el documento. Es la raíz funcional del scope.

### Negocio
Segmento funcional de facturación: fijo, móvil, empresas u otro catálogo administrable.

### Origen
Sistema/plataforma funcional donde se origina o materializa el proceso: ANDES, AMDOCS, SAP, ACEPTA u otros.

No equivale al tipo de conexión. ANDES puede consultarse por Oracle; ACEPTA puede consumirse por web service; el origen funcional no cambia por eso.

### Tipo de emisión
Clasificación transversal. Base inicial:

- `MASIVO`
- `ONLINE`

### Flujo operativo
Especialización opcional dentro de Origen + Tipo.

Ejemplos:

```text
ANDES  + MASIVO -> FACTURACION_MASIVA / SEGMENT_LABEL=DOM
AMDOCS + MASIVO -> FACTURACION_MASIVA / SEGMENT_LABEL=CICLO
AMDOCS + ONLINE -> BILL_NOW
AMDOCS + ONLINE -> BILL_ONLINE
AMDOCS + ONLINE -> CORRECTIVE_BILLING
```

`DOM` y `Ciclo` dejan de ser catálogos globales. El valor concreto, por ejemplo `22`, se registra como `SEGMENT_VALUE` del resultado operacional.

## Acceso técnico

```text
RM_CFACT_CONNECTION
  -> Oracle / SQL Server / REST / SOAP / FILE

RM_CFACT_DATA_SOURCE
  -> insumo funcional

RM_CFACT_SOURCE_SCOPE
  -> dónde aplica el insumo
```

La conexión no define el origen funcional. Esa semántica está en el Scope.

## Resultado operacional

`RM_CFACT_EMISSION_STATUS` registra por Scope:

- periodo;
- segmento runtime;
- estado;
- completitud;
- Q esperada;
- Q emitida;
- Q rechazada;
- Q issues;
- monto total.

`RM_CFACT_ISSUE` permite detallar incidencias con severidad, estado y fechas.

## Relaciones principales

```text
RM_CFACT_ISSUER
      |
RM_CFACT_BUSINESS
      |
RM_CFACT_ORIGIN ---- RM_CFACT_FLOW ---- RM_CFACT_EMISSION_TYPE
      \                 |                 /
       \                |                /
                RM_CFACT_SCOPE
                   /          \
        RM_CFACT_SOURCE_SCOPE  RM_CFACT_USER_SCOPE
                 |                    |
      RM_CFACT_DATA_SOURCE       RM_CFACT_USER
                 |
      RM_CFACT_EXTRACTION_RUN
                 |
      RM_CFACT_EMISSION_STATUS
                 |
          RM_CFACT_ISSUE
```

## Estado del modelo

- Seguridad y autenticación: operativas.
- Contexto v0.2.1: implementado.
- Integraciones: implementadas.
- Persistencia de estado operacional: implementada.
- Dashboard/controles que llenan `RM_CFACT_EMISSION_STATUS`: siguiente fase funcional.
