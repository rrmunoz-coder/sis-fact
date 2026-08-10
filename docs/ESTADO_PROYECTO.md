# Estado del proyecto Billing One

Fecha: 2026-08-10
Versión: v0.2.0

## Estado

- Fase 0 - Diseño conceptual: COMPLETADA.
- Fase 1 - Base técnica reconstruida sobre ATLAS S.2.0: CÓDIGO/DDL PREPARADO; pendiente validación en servidor y migración Oracle v0.1.
- Fase 2.1 - Contexto + fuentes + insumos: MODELO + MANTENEDORES WEB PREPARADOS; pendiente instalar y validar sobre Oracle v0.2.
- Fase 2.2 - Modelo funcional de facturación: PENDIENTE.
- Fase 3 - Integraciones y controles reales: base de conexiones/pruebas preparada; extractores reales pendientes.
- Fase 4 - Paneles: PENDIENTE.
- Fase 5 - Servicio Windows: scripts Waitress/NSSM preparados; validación productiva pendiente.

## Ya preparado en v0.2

- login LDAP/local y autorización Oracle;
- roles/permisos;
- sesiones revocables y rate limiting;
- scopes de usuario;
- mantenedor de usuarios;
- mantenedor Empresa/RUT/Negocio/DOM/Ciclo/Scope;
- mantenedor de Conexiones e Insumos;
- prueba de conexión Oracle/SQL Server/REST/SOAP/FILE;
- CREDENTIAL_REF externo;
- auditoría;
- DDL + validadores;
- CI y herramientas de diagnóstico.

## Bloqueo actual

Antes de aplicar DDL v0.2 al esquema existente debe ejecutarse:

```text
sql/migration_v0_1/00_CONTEO_REAL_V0_1.sql
```

No se autoriza borrar objetos v0.1 sin esos conteos.

`SISGAV2` está fuera del proyecto y no debe modificarse.

## Siguiente validación en servidor

1. actualizar carpeta operativa desde `main` sin perder `config.ini`;
2. revisar compatibilidad/recrear `.venv` preferentemente con Python 3.12;
3. instalar requirements;
4. ejecutar release/higiene/compile/pytest;
5. ejecutar conteos v0.1 en DBeaver;
6. con esa evidencia generar migración específica;
7. aplicar DDL 10/20/30 y validadores 11/21/31/90;
8. bootstrap ADMIN;
9. probar Oracle, transporte LDAP, bind LDAP y login web;
10. validar mantenedores de Usuarios, Contexto e Integraciones.
