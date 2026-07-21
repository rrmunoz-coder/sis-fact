# Modelo de integración de fuentes

## Fuentes iniciales

SIS-FACT debe consumir información desde múltiples orígenes:

| Fuente | Tipo | Rol |
|---|---|---|
| Oracle Billing | ORACLE | Billing operacional |
| SQL Server FACT | SQLSERVER | Documentos históricos y tablas MS SQL |
| Facturador REST | REST | Estado documental |
| Facturador SOAP | SOAP | Estado documental / emisión |
| SII Registro de Ventas | FILE/API | Validación tributaria |
| Billing Compare | CONTROL_ENGINE | Motor de control |
| Pagos | ORACLE/SQLSERVER/REST | Caja y recaudación |

## Regla de consulta

Los dashboards no deben ejecutar consultas masivas en vivo contra todos los orígenes. El patrón recomendado es:

```text
Fuente externa
  -> extracción auditada
  -> staging o normalización
  -> repositorio SIS-FACT
  -> reportería
```

## Tabla SIS_DATA_SOURCE

Registra las fuentes activas, su tipo, rol y clave de conexión.

No guarda contraseñas. La columna `CONNECTION_KEY` apunta a `config.ini` o a un almacén seguro.

## Tabla SIS_EXTRACTION_RUN

Registra cada extracción:

- Fuente.
- Tipo de extracción.
- Período.
- Flujo.
- Ciclo/código.
- Ejecución.
- Filas leídas.
- Filas cargadas.
- Filas rechazadas.
- Estado.
- Error.
- Versión de consulta.

## Tabla SIS_INTEGRATION_CALL

Registra llamadas puntuales a APIs, WS o servicios externos:

- Endpoint.
- Correlation ID.
- Estado técnico.
- Estado funcional.
- HTTP status.
- Tiempo de respuesta.
- Reintento.
- Código de respuesta.
- Error.

## Precedencia funcional

| Pregunta | Fuente prioritaria |
|---|---|
| Qué debía facturarse | Billing |
| Qué se calculó | Billing |
| Qué se folió | Facturador |
| Qué reconoce tributariamente el SII | SII/RCV |
| Qué se declaró | F29 |
| Qué se pagó | Recaudación |
| Qué hallazgo se detectó | Billing Compare |

## No usar COALESCE indiscriminado

No se debe mezclar el mismo dato entre fuentes sin regla de precedencia. Cada atributo debe tener una fuente responsable.
