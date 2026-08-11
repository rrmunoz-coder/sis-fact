/* ============================================================
   BILLING ONE / SIS-FACT
   MIGRACION v0.1 -> v0.2
   PASO 3 - FINALIZAR MIGRACION

   EJECUTAR SOLO DESPUES DE:
   - DDL 10/20/30 y validadores 11/21/31/90 OK.
   - Usuario migrado visible en RM_CFACT_USER + RM_CFACT_USER_AUTH.
   - Login real validado correctamente.

   Este script elimina únicamente el staging RM_CFACT_USER_V01.
   SISGAV2 NO SE TOCA.
   ============================================================ */

DECLARE
    v_stage_users NUMBER;
    v_missing_target NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_stage_users FROM RM_CFACT_USER_V01;

    SELECT COUNT(*)
      INTO v_missing_target
      FROM RM_CFACT_USER_V01 S
     WHERE NOT EXISTS (
           SELECT 1
             FROM RM_CFACT_USER U
             JOIN RM_CFACT_USER_AUTH A ON A.USER_ID = U.USER_ID
            WHERE UPPER(U.USERNAME) = UPPER(S.USERNAME)
              AND U.ACTIVE = S.ACTIVE
              AND A.AUTH_TYPE = S.AUTH_TYPE
     );

    IF v_stage_users <> 1 THEN
        RAISE_APPLICATION_ERROR(
            -20021,
            'FINALIZACION DETENIDA: staging debe contener exactamente 1 usuario.'
        );
    END IF;

    IF v_missing_target <> 0 THEN
        RAISE_APPLICATION_ERROR(
            -20022,
            'FINALIZACION DETENIDA: el usuario staging no esta correctamente migrado.'
        );
    END IF;
END;
/

DROP TABLE RM_CFACT_USER_V01 CASCADE CONSTRAINTS PURGE;

SELECT 'STAGING_USUARIO_V01' AS CONTROL,
       CASE WHEN COUNT(*) = 0 THEN 'ELIMINADO - OK' ELSE 'REVISAR' END AS ESTADO
FROM USER_TABLES
WHERE TABLE_NAME = 'RM_CFACT_USER_V01';

SELECT 'SISGAV2_PROTEGIDA' AS CONTROL,
       CASE WHEN COUNT(*) = 1 THEN 'EXISTE - NO TOCAR'
            ELSE 'NO EXISTE - SIN ACCION' END AS ESTADO
FROM USER_TABLES
WHERE TABLE_NAME = 'SISGAV2';
