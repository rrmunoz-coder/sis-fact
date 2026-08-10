# Arquitectura Billing One v0.2.0

## 1. Decisión base

Billing One permanece separado funcionalmente de ATLAS. Se reutiliza el **patrón técnico probado de ATLAS S.2.0**, no su dominio de negocio.

Se hereda/adapta:
- application factory Flask;
- configuración estricta;
- pool Oracle y Thick Mode;
- LDAP;
- sesiones revocables;
- rate limiting;
- CSRF y headers HTTP;
- auditoría;
- logging y request-id;
- roles/permisos;
- mantenedor de usuarios;
- Waitress y disciplina de validación.

No se hereda:
- proyectos;
- tareas;
- horas;
- costos;
- aprobaciones;
- unidades organizacionales ATLAS;
- tablas `GT_*`.

## 2. Capas Billing One

```text
SEGURIDAD
  usuario / rol / permiso / sesión / LDAP / auditoría

CONTEXTO
  empresa / RUT emisor / negocio / DOM / ciclo / scope

ADQUISICIÓN
  conexión / insumo / parámetros / alcance / extracción / llamada

DOMINIO DE CONTROL
  pendiente de siguientes fases: documentos, emisión, SII, pagos,
  controles, resultados, casos y paneles
```

## 3. Contexto multidimensional

`RM_CFACT_SCOPE` combina dimensiones sin imponer una jerarquía rígida.

- `COMPANY_ID` es obligatorio.
- `ISSUER_ID`, `BUSINESS_ID`, `DOM_ID` y `CYCLE_ID` pueden ser `NULL` para representar un alcance más general.
- `PRIORITY_ORDER` permite resolver reglas más específicas antes de reglas genéricas.
- Los usuarios reciben scopes mediante `RM_CFACT_USER_SCOPE`.

## 4. Conexión versus insumo

Una conexión describe **cómo llegar** a un sistema.

Un insumo describe **qué dato funcional** necesita Billing One.

Ejemplo:

```text
CONEXIÓN ORACLE_BRM_PROD
  -> DOCUMENTOS_FACTURADOS
  -> CARGOS
  -> PAGOS

CONEXIÓN API_FACTURADOR
  -> DOCUMENTOS_DTE
  -> ESTADOS_SII
```

Un mismo `LOGICAL_TYPE` puede provenir de distintas tecnologías según el scope.

## 5. Seguridad de credenciales

`RM_CFACT_CONNECTION.CONFIG_JSON` solo contiene parámetros no secretos.

`CREDENTIAL_REF` apunta a una referencia externa. No se deben almacenar passwords, tokens o secretos en texto plano dentro de las tablas de catálogo ni en GitHub.

## 6. Validación

Cada bloque tiene DDL y validador:

```text
10_SECURITY_BASE.sql      -> 11_VALIDAR_SECURITY.sql
20_CONTEXT_BASE.sql       -> 21_VALIDAR_CONTEXT.sql
30_INTEGRATION_BASE.sql   -> 31_VALIDAR_INTEGRATION.sql
                              90_VALIDAR_BILLING_ONE.sql
```

El criterio de terminado no es "el script ejecutó", sino que el validador devuelva los estados esperados y no existan objetos inválidos.
