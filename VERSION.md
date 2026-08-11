# Billing One v0.2.3

Fecha: 2026-08-11

Estado: incorporación de mantenedor dedicado de Orígenes funcionales.

## Orígenes

El catálogo `RM_CFACT_ORIGIN` pasa a administrarse desde una pantalla propia:

```text
Contexto -> Administrar Orígenes
```

Permite:

- listar orígenes activos e inactivos;
- crear nuevos orígenes sin modificar código;
- activar/reactivar;
- desactivar lógicamente;
- ver cantidad de scopes activos;
- ver cantidad de flujos activos;
- impedir la desactivación mientras existan scopes o flujos activos dependientes.

Orígenes base actuales:

```text
ANDES
AMDOCS
SAP
ACEPTA
SGA
DHT
```

La lista es extensible y no está cerrada a estos valores.

## Modelo funcional

Sin cambio estructural respecto de v0.2.1:

```text
RUT emisor -> Negocio -> Origen -> Tipo de emisión -> Flujo operativo opcional
```

`DOM` y `Ciclo` continúan siendo segmentadores propios de determinados flujos.

## Base de datos

No cambia el esquema Oracle. Para una base v0.2.1/v0.2.2 ya existente se incorpora una carga idempotente de SGA y DHT:

```text
sql/migration_v0_2_2_to_v0_2_3/10_ORIGENES_BASE.sql
```

## Seguridad

Sin cambios de autenticación/autorización. Oracle autoriza y LDAP valida la contraseña web.

## Operación

Puerto web vigente: `5040`.
