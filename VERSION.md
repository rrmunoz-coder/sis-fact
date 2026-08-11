# Billing One v0.2.2

Fecha: 2026-08-11

Estado: mejora de navegación y usabilidad sobre el modelo funcional v0.2.1.

## Navegación

Se incorpora una barra de navegación persistente para usuarios autenticados:

```text
Inicio | Contexto | Fuentes e integraciones | Usuarios
```

Las opciones se muestran según permisos. La sección activa queda resaltada.

En pantallas hijas se agrega una segunda barra contextual con navegación al menú padre, por ejemplo:

```text
← Volver a Fuentes e integraciones
← Volver a Usuarios
← Volver a Inicio
```

Los botones locales `Volver` se retiran de los formularios para evitar duplicidad de navegación.

## Modelo funcional

Sin cambios respecto de v0.2.1:

```text
RUT emisor -> Negocio -> Origen -> Tipo de emisión -> Flujo operativo opcional
```

`DOM` y `Ciclo` continúan modelados como segmentadores de flujo cuando corresponda.

## Base de datos

**v0.2.2 no requiere cambios Oracle.**

El parche Oracle v0.2.0 -> v0.2.1 sigue siendo el vigente para corregir el modelo de contexto y resultados.

## Seguridad

Sin cambios de autenticación/autorización. Oracle autoriza y LDAP valida la contraseña web.

## Operación

Puerto web vigente: `5040`.
