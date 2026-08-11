/* ============================================================
   BILLING ONE / SIS-FACT
   MIGRACION v0.1 -> v0.2
   PASO 2 - RESTAURAR USUARIO v0.1 EN MODELO DE SEGURIDAD v0.2

   PRERREQUISITOS:
   1) 01_PREPARAR_MIGRACION_V0_1.sql ejecutado OK.
   2) sql/10_SECURITY_BASE.sql ejecutado OK.
   3) RM_CFACT_USER_V01 conserva exactamente 1 usuario.

   No elimina el staging. Se conserva hasta validar login.
   ============================================================ */

DECLARE
    v_stage_users NUMBER;
    v_target_users NUMBER;
    v_missing_roles NUMBER;
BEGIN
    SELECT COUNT(*) INTO v_stage_users FROM RM_CFACT_USER_V01;
    SELECT COUNT(*) INTO v_target_users FROM RM_CFACT_USER;

    SELECT COUNT(*)
      INTO v_missing_roles
      FROM RM_CFACT_USER_V01 U
     WHERE NOT EXISTS (
           SELECT 1
             FROM RM_CFACT_ROLE R
            WHERE UPPER(R.ROLE_CODE) = UPPER(U.ROLE_CODE)
              AND R.ACTIVE = 'Y'
     );

    IF v_stage_users <> 1 THEN
        RAISE_APPLICATION_ERROR(
            -20011,
            'RESTAURACION DETENIDA: RM_CFACT_USER_V01 debe contener exactamente 1 fila.'
        );
    END IF;

    IF v_target_users <> 0 THEN
        RAISE_APPLICATION_ERROR(
            -20012,
            'RESTAURACION DETENIDA: RM_CFACT_USER nuevo debe estar vacio antes de restaurar.'
        );
    END IF;

    IF v_missing_roles <> 0 THEN
        RAISE_APPLICATION_ERROR(
            -20013,
            'RESTAURACION DETENIDA: el ROLE_CODE v0.1 no existe en RM_CFACT_ROLE v0.2.'
        );
    END IF;
END;
/

INSERT INTO RM_CFACT_USER (
    USERNAME,
    DISPLAY_NAME,
    EMAIL,
    ROLE_ID,
    PASSWORD_HASH,
    ACTIVE,
    CREATED_AT,
    CREATED_BY,
    UPDATED_AT,
    UPDATED_BY
)
SELECT
    U.USERNAME,
    U.DISPLAY_NAME,
    U.EMAIL,
    R.ROLE_ID,
    U.PASSWORD_HASH,
    U.ACTIVE,
    CAST(U.CREATED_AT AS TIMESTAMP),
    U.CREATED_BY,
    CAST(U.UPDATED_AT AS TIMESTAMP),
    U.UPDATED_BY
FROM RM_CFACT_USER_V01 U
JOIN RM_CFACT_ROLE R
  ON UPPER(R.ROLE_CODE) = UPPER(U.ROLE_CODE)
 AND R.ACTIVE = 'Y';

INSERT INTO RM_CFACT_USER_AUTH (
    USER_ID,
    AUTH_TYPE,
    LDAP_USERNAME,
    SESSION_VERSION,
    FAILED_ATTEMPTS,
    UPDATED_AT
)
SELECT
    N.USER_ID,
    U.AUTH_TYPE,
    CASE WHEN U.AUTH_TYPE = 'LDAP' THEN U.USERNAME ELSE NULL END,
    1,
    0,
    SYSTIMESTAMP
FROM RM_CFACT_USER_V01 U
JOIN RM_CFACT_USER N
  ON UPPER(N.USERNAME) = UPPER(U.USERNAME);

COMMIT;

/* Validación del usuario migrado. */
SELECT
    U.USER_ID,
    U.USERNAME,
    U.DISPLAY_NAME,
    U.EMAIL,
    R.ROLE_CODE,
    U.ACTIVE,
    A.AUTH_TYPE,
    A.LDAP_USERNAME,
    A.SESSION_VERSION,
    A.FAILED_ATTEMPTS
FROM RM_CFACT_USER U
JOIN RM_CFACT_ROLE R ON R.ROLE_ID = U.ROLE_ID
JOIN RM_CFACT_USER_AUTH A ON A.USER_ID = U.USER_ID;

SELECT
    (SELECT COUNT(*) FROM RM_CFACT_USER_V01) AS USUARIO_STAGING,
    (SELECT COUNT(*) FROM RM_CFACT_USER) AS USUARIO_V02,
    (SELECT COUNT(*) FROM RM_CFACT_USER_AUTH) AS AUTH_V02
FROM DUAL;
