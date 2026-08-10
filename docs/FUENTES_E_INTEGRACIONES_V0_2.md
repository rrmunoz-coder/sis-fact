# Fuentes e Integraciones — Billing One v0.2.0

## Concepto

Billing One separa:

```text
CONEXIÓN = cómo acceder técnicamente
INSUMO   = qué dato funcional necesita el control
SCOPE    = dónde aplica ese dato
```

No todas las empresas o negocios utilizan todas las conexiones. Una conexión puede:

- quedar limitada a uno o más scopes;
- quedar sin filas en `RM_CFACT_CONNECTION_SCOPE`, lo que significa disponibilidad global;
- alimentar varios insumos diferentes.

Un insumo activo siempre debe tener al menos un scope.

## Administración web

```text
/app
  -> Fuentes e insumos
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
- cambiar origen técnico;
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

En `config.ini` real:

```ini
[credential.BRM_PROD]
user=usuario
password=...
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

Credencial externa con `user/password`.

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

Tipos iniciales de autenticación soportados en prueba:

- `NONE`;
- `BASIC`;
- `BEARER`;
- `API_KEY`.

### SOAP

```json
{"wsdl_url":"https://servicio/ws?wsdl","auth_type":"BASIC","timeout":15}
```

La prueba v0.2 comprueba accesibilidad HTTP del WSDL. Las operaciones SOAP reales se implementan por insumo en la fase de integración funcional.

### Archivos

```json
{"path":"K:\\facturacion\\entrada","pattern":"*.csv"}
```

La prueba valida acceso a la ruta y cantidad de elementos que cumplen el patrón.

## Seguridad de secretos

`CONFIG_JSON` rechaza claves que parezcan `password`, `secret`, `token`, etc.

Los secretos viven fuera del catálogo mediante `CREDENTIAL_REF`. No se muestran ni se escriben en auditoría.

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

Dos negocios pueden usar el mismo `LOGICAL_TYPE` con conexiones diferentes.

Ejemplo:

```text
ANDES / DOCUMENTOS_FACTURADOS -> Oracle BRM
MOVIL / DOCUMENTOS_FACTURADOS -> SQL Server
EMPRESAS / DOCUMENTOS_FACTURADOS -> API
```

Los controles futuros deben resolver el insumo por scope y tipo lógico, no referenciar directamente una base física.
