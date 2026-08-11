# Migración SIS-FACT v0.1 a Billing One v0.2.0

## Estado confirmado al 11-08-2026

La instalación Oracle v0.1 fue inventariada y posteriormente se ejecutaron conteos reales.

Resultado:

```text
RM_CFACT_AI_PROVIDER       0
RM_CFACT_AUDIT_LOG         0
RM_CFACT_DATA_SOURCE       0
RM_CFACT_EXTRACTION_RUN    0
RM_CFACT_INTEGRATION_CALL  0
RM_CFACT_USER              1
SIS_AI_PROVIDER            0
SIS_AUDIT_LOG              0
SIS_DATA_SOURCE            0
SIS_EXTRACTION_RUN         0
SIS_INTEGRATION_CALL       0
```

Conclusión: no existen datos de integración/auditoría a migrar. El único dato útil es 1 usuario de autorización en `RM_CFACT_USER`.

## Regla de seguridad

`SISGAV2` NO SE TOCA. No forma parte de ningún rollback, limpieza ni script de migración Billing One.

## Orden oficial de migración en DBeaver

Usar **Execute SQL Script** en los archivos que contengan bloques PL/SQL terminados en `/`.

### 1. Preparar v0.1

```text
sql/migration_v0_1/01_PREPARAR_MIGRACION_V0_1.sql
```

El script:
- vuelve a comprobar los conteos antes de ejecutar DDL destructivo;
- exige exactamente 1 usuario;
- renombra `RM_CFACT_USER` a `RM_CFACT_USER_V01` para conservarlo;
- elimina únicamente las tablas v0.1/legacy comprobadas vacías;
- no usa comodines destructivos;
- no toca `SISGAV2`.

Resultado esperado final:

```text
RM_CFACT_USER_V01     STAGING USUARIO v0.1 - CONSERVAR
USUARIOS_STAGING      1
SISGAV2_PROTEGIDA     EXISTE - NO TOCAR
```

### 2. Crear seguridad v0.2

```text
sql/10_SECURITY_BASE.sql
```

### 3. Restaurar usuario v0.1

```text
sql/migration_v0_1/02_RESTAURAR_USUARIO_V0_1.sql
```

El usuario se recrea en `RM_CFACT_USER` usando el rol equivalente de v0.2 y se crea su registro en `RM_CFACT_USER_AUTH`. Para usuarios LDAP no se almacena password.

Resultado esperado:

```text
USUARIO_STAGING  1
USUARIO_V02      1
AUTH_V02         1
```

### 4. Validar seguridad

```text
sql/11_VALIDAR_SECURITY.sql
```

### 5. Crear y validar contexto

```text
sql/20_CONTEXT_BASE.sql
sql/21_VALIDAR_CONTEXT.sql
```

### 6. Crear y validar integraciones

```text
sql/30_INTEGRATION_BASE.sql
sql/31_VALIDAR_INTEGRATION.sql
```

### 7. Certificación global

```text
sql/90_VALIDAR_BILLING_ONE.sql
```

Los controles principales deben quedar en `OK`. El staging `RM_CFACT_USER_V01` puede seguir existiendo durante esta certificación.

### 8. Validar aplicación y login real

Actualizar código desde `main`, instalar requirements y ejecutar pruebas técnicas. Luego validar Oracle, LDAP y login web con el usuario migrado.

### 9. Finalizar staging

Solo después de login real exitoso:

```text
sql/migration_v0_1/03_FINALIZAR_MIGRACION_V0_1.sql
```

Este script comprueba nuevamente que el usuario staging existe correctamente en `RM_CFACT_USER` + `RM_CFACT_USER_AUTH` y recién entonces elimina `RM_CFACT_USER_V01`.

## Prohibiciones

- no ejecutar `99_ROLLBACK_GREENFIELD.sql` sobre la instalación v0.1;
- no ejecutar `DROP TABLE SIS_%`;
- no eliminar manualmente `RM_CFACT_USER_V01` antes del login validado;
- no tocar `SISGAV2`;
- no almacenar password LDAP en Oracle ni en scripts.
