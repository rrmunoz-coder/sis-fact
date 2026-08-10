# Billing One v0.2.0

Fecha: 2026-08-10

Estado: reconstrucción técnica sobre baseline ATLAS S.2.0.

Incluye:
- configuración estricta;
- pool Oracle;
- LDAP y login seguro;
- sesiones revocables;
- roles, permisos y scopes de usuario;
- mantenedor web de usuarios;
- contexto multiempresa/RUT/negocio/DOM/ciclo y mantenedor web;
- catálogo de conexiones e insumos con mantenedor web;
- prueba de conexión Oracle, SQL Server, REST, SOAP y FILE;
- auditoría;
- validadores Oracle greenfield;
- herramientas de prueba, CI y operación Waitress/NSSM.

Pendiente para aplicar en el Oracle existente:
- ejecutar conteos reales de v0.1;
- generar migración específica;
- aplicar y certificar DDL v0.2;
- validar login/LDAP y conexiones en servidor.

La migración de objetos v0.1 existentes permanece bloqueada hasta obtener los conteos reales antes de cualquier DROP.
