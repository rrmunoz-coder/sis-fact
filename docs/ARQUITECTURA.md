# Arquitectura SIS-FACT / Billing One

## Decisión principal

SIS-FACT se construye como sistema separado de ATLAS/Altas. No depende de que ATLAS entre en producción.

La integración futura entre ambos será analítica, no funcional:

```text
Billing One controla qué ocurrió en la facturación.
ATLAS mide cuánto esfuerzo operacional requirió gestionarlo.
```

## Objetivo arquitectónico

Separar core, fuentes de datos, normalización, analítica y presentación.

```text
Navegador / API
  ↓
Flask / Waitress
  ↓
Core SIS-FACT
  ↓
Servicios de negocio
  ↓
Capa de integración
  ↓
Oracle / SQL Server / REST / SOAP / archivos / webhooks
```

## Capas

### Core

- Configuración externa.
- Seguridad base.
- Auditoría.
- Registro de errores.
- Convenciones de respuesta API.

### Integraciones

- Oracle.
- SQL Server.
- REST.
- SOAP.
- Archivos.
- Webhooks.
- Billing Compare.

### Normalización

Toda fuente debe transformarse a modelos comunes antes de alimentar dashboards o controles.

Campos comunes mínimos:

```text
source_system
source_table
source_record_id
issuer_tax_id
business_code
flow_code
scope_code
billing_period
execution_code
customer_id
account_id
document_type
document_number
issue_date
net_amount
tax_amount
total_amount
raw
```

### Analítica y reportería

La analítica debe consumir datos normalizados o agregados, no consultas masivas directas contra fuentes productivas.

### IA

La IA queda encapsulada detrás de un `AIGateway` para permitir:

- Solución local.
- Modelo privado.
- API externa.
- Modo deshabilitado.
- Analítica determinística sin IA.

## Principio de diseño

No hardcodear procesos. Los flujos, fases, fuentes, reglas y SLA deben ser configurables por base de datos o parámetros.
