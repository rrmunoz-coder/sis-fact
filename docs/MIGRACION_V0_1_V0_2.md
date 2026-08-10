# Migración SIS-FACT v0.1 a Billing One v0.2.0

## Estado

La instalación Oracle v0.1 fue inventariada y se confirmó:

- existen las 6 tablas `RM_CFACT_*` de la v0.1;
- no hay objetos `RM_CFACT_*` inválidos en el inventario recibido;
- existen 5 tablas legacy del primer modelo con prefijo `SIS_`;
- existe `SISGAV2`, creada antes del proyecto y **ajena a Billing One**.

## Regla de seguridad

`SISGAV2` NO SE TOCA. No forma parte de ningún rollback, limpieza ni script de migración Billing One.

## Paso pendiente obligatorio

Ejecutar en DBeaver:

```text
sql/migration_v0_1/00_CONTEO_REAL_V0_1.sql
```

El resultado debe indicar filas reales de:

```text
RM_CFACT_AI_PROVIDER
RM_CFACT_AUDIT_LOG
RM_CFACT_DATA_SOURCE
RM_CFACT_EXTRACTION_RUN
RM_CFACT_INTEGRATION_CALL
RM_CFACT_USER
SIS_AI_PROVIDER
SIS_AUDIT_LOG
SIS_DATA_SOURCE
SIS_EXTRACTION_RUN
SIS_INTEGRATION_CALL
```

## Qué no hacer todavía

- no ejecutar `99_ROLLBACK_GREENFIELD.sql` sobre v0.1;
- no ejecutar `DROP TABLE SIS_%`;
- no borrar `RM_CFACT_USER` antes de identificar el usuario ADMIN existente;
- no ejecutar DDL v0.2 sobre tablas con el mismo nombre;
- no tocar `SISGAV2`.

## Decisión después del conteo

Con los conteos se generará un script específico de migración que:

1. rescate únicamente datos útiles;
2. elimine explícitamente los objetos legacy identificados;
3. nunca use comodines destructivos;
4. cree el modelo v0.2;
5. vuelva a insertar los usuarios necesarios sin passwords LDAP;
6. ejecute los validadores 11/21/31/90.

La migración destructiva no se versionará como aprobada hasta contar con esa evidencia.
