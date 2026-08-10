# Estado del proyecto Billing One

Fecha: 2026-08-10
Versión: v0.2.0

## Estado

- Fase 0 - Diseño conceptual: COMPLETADA.
- Fase 1 - Base técnica reconstruida sobre ATLAS S.2.0: CÓDIGO/DDL PREPARADO; pendiente validación en servidor y migración Oracle v0.1.
- Fase 2.1 - Contexto + fuentes + insumos: MODELO ORACLE PREPARADO; interfaz de administración de conexiones pendiente.
- Fase 2.2 - Modelo funcional de facturación: PENDIENTE.
- Fase 3 - Integraciones y controles reales: PENDIENTE.
- Fase 4 - Paneles: PENDIENTE.
- Fase 5 - Servicio Windows: scripts base preparados; validación productiva pendiente.

## Bloqueo actual

Antes de aplicar DDL v0.2 al esquema existente debe ejecutarse:

```text
sql/migration_v0_1/00_CONTEO_REAL_V0_1.sql
```

No se autoriza borrar objetos v0.1 sin esos conteos.

`SISGAV2` está fuera del proyecto y no debe modificarse.

## Siguiente validación en servidor

1. actualizar carpeta operativa desde `main` conservando `config.ini` y `.venv` solo si son compatibles;
2. instalar requirements;
3. ejecutar validadores de release/higiene/compile/pytest;
4. ejecutar conteos v0.1 en DBeaver;
5. con esa evidencia generar migración específica;
6. aplicar DDL y validadores;
7. probar Oracle, LDAP, login y mantenedor de usuarios.
