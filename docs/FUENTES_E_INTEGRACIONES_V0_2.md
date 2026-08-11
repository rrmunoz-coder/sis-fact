# Fuentes e Integraciones — Billing One v0.2.1

## Concepto

Billing One separa cuatro conceptos:

```text
ORIGEN FUNCIONAL = sistema/plataforma de negocio: ANDES, AMDOCS, SAP, ACEPTA...
CONEXIÓN TÉCNICA  = cómo acceder: Oracle, SQL Server, REST, SOAP, FILE
INSUMO            = qué dato funcional necesita el control
SCOPE             = RUT emisor + Negocio + Origen + Tipo de emisión + Flujo opcional
```

La conexión no define el origen funcional. Un mismo tipo técnico puede servir a varios orígenes y un origen puede ser consumido por tecnologías distintas.

Una conexión puede:

- quedar limitada a uno o más scopes;
- quedar sin filas en `RM_CFACT_CONNECTION_SCOPE`, lo que significa disponibilidad global;
- alimentar varios insumos diferentes.

Un insumo activo siempre debe tener al menos un scope.

## Administración web

```text
/app
  -> Fuentes e integraciones
  -> /administracion/integraciones
```

Con permiso `CONNECTION_MANAGE`:

- crear conexión;
- editar configuración;
- cambiar alcance;
- probar conexión;
- activar/desactivar.

Con permiso `SOURCE_MANAGE`:

- crear insumo;
- cambiar conexión técnica;
- actualizar definición de extracción;
- asignar scopes;
- activar/desactivar.

No existe borrado físico desde la interfaz: desactivar conserva trazabilidad.

## Tipos de conexión

### Oracle

`CONFIG_JSON`:

```json
{"host":"servidor","port":1521,"service_name":"SERVICIO"}
```

o:

```json
{"dsn":"servidor:1521/SERVICIO"}
```

`CREDENTIAL_REF`:

```text
credential.BRM_PROD
```

### SQL Server

```json
{
  "server":"servidor",
  "port":1433,
  "database":"FACTURACION",
  "driver":"ODBC Driver 18 for SQL Server",
  "encrypt":"yes",
  "trust_server_certificate":"no"
}
```

### REST

```json
{
  "base_url":"https://servicio/api",
  "health_url":"https://servicio/api/health",
  "auth_type":"BEARER",
  "timeout":15,
  "verify_tls":true
}
```

### SOAP

```json
{"wsdl_url":"https://servicio/ws?wsdl","auth_type":"BASIC","timeout":15}
```

### Archivos

```json
{"path":"K:\\facturacion\\entrada","pattern":"*.csv"}
```

## Seguridad de secretos

`CONFIG_JSON` rechaza claves que parezcan `password`, `secret`, `token`, etc. Los secretos viven fuera del catálogo mediante `CREDENTIAL_REF`.

## Insumos

Ejemplos de `LOGICAL_TYPE`:

```text
DOCUMENTOS_FACTURADOS
DOCUMENTOS_DTE
ESTADOS_SII
PAGOS
ACTIVOS
CARGOS
REAJUSTES
```

El mismo `LOGICAL_TYPE` puede resolverse de forma distinta según scope.

Ejemplos:

```text
RUT A / FIJO / ANDES  / MASIVO -> DOCUMENTOS_FACTURADOS -> Oracle
RUT A / FIJO / AMDOCS / ONLINE -> DOCUMENTOS_FACTURADOS -> Oracle
RUT B / EMPRESAS / SAP / MASIVO -> DOCUMENTOS_FACTURADOS -> REST
RUT C / FIJO / ACEPTA / ONLINE -> ESTADOS_SII -> SOAP/REST
```

Los controles deben resolver el insumo por scope y tipo lógico, no referenciar directamente una base física.
