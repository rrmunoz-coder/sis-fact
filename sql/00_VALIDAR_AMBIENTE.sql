-- SIS-FACT / Billing One
-- 00_VALIDAR_AMBIENTE.sql
-- Validacion previa del ambiente Oracle antes de crear objetos RM_CFACT_.
-- Compatible con DBeaver / SQL Developer / SQL*Plus.
-- No usa SET ni PROMPT para evitar ORA-00922 en clientes graficos.
-- Este script no crea tablas finales. Solo valida conexion, esquema, fecha,
-- objetos existentes y privilegio CREATE TABLE mediante una tabla temporal.

SELECT 'SIS-FACT / Billing One - Validacion de ambiente Oracle' AS validacion
  FROM dual;

SELECT USER AS connected_user
  FROM dual;

SELECT SYSDATE AS database_datetime
  FROM dual;

SELECT banner AS oracle_version
  FROM v$version
 WHERE ROWNUM = 1;

SELECT object_type,
       object_name
  FROM user_objects
 WHERE object_name LIKE 'RM_CFACT_%'
 ORDER BY object_type,
          object_name;

SELECT table_name AS tabla_antigua_sis
  FROM user_tables
 WHERE table_name IN (
    'SIS_USER',
    'SIS_DATA_SOURCE',
    'SIS_EXTRACTION_RUN',
    'SIS_INTEGRATION_CALL',
    'SIS_AUDIT_LOG',
    'SIS_AI_PROVIDER'
 )
 ORDER BY table_name;

DECLARE
    v_count NUMBER;
BEGIN
    SELECT COUNT(*)
      INTO v_count
      FROM user_tables
     WHERE table_name = 'RM_CFACT_ENV_TEST';

    IF v_count > 0 THEN
        EXECUTE IMMEDIATE 'DROP TABLE RM_CFACT_ENV_TEST PURGE';
    END IF;

    EXECUTE IMMEDIATE 'CREATE TABLE RM_CFACT_ENV_TEST (ID NUMBER)';
    EXECUTE IMMEDIATE 'DROP TABLE RM_CFACT_ENV_TEST PURGE';
END;
/

SELECT 'OK: validacion terminada. Si no hubo errores, ejecutar 01_CORE_INTEGRACION.sql y 02_SECURITY_USERS.sql.' AS resultado
  FROM dual;
