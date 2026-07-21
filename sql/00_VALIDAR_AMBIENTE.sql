-- SIS-FACT / Billing One
-- 00_VALIDAR_AMBIENTE.sql
-- Validacion previa del ambiente Oracle antes de crear objetos RM_CFACT_.
-- Este script no crea tablas. Solo valida conexion, esquema, fecha y objetos existentes.

SET SERVEROUTPUT ON;

PROMPT ============================================================
PROMPT SIS-FACT / Billing One - Validacion de ambiente Oracle
PROMPT ============================================================

PROMPT Usuario conectado:
SELECT USER AS connected_user FROM dual;

PROMPT Fecha/hora base de datos:
SELECT SYSDATE AS database_datetime FROM dual;

PROMPT Version Oracle:
SELECT banner FROM v$version WHERE ROWNUM = 1;

PROMPT Objetos RM_CFACT_ existentes en el esquema:
SELECT object_type, object_name
  FROM user_objects
 WHERE object_name LIKE 'RM_CFACT_%'
 ORDER BY object_type, object_name;

PROMPT Tablas antiguas SIS_ que podrian requerir migracion:
SELECT table_name
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

PROMPT Validacion de privilegio para crear tabla temporal de prueba:
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

    DBMS_OUTPUT.PUT_LINE('OK: privilegio CREATE TABLE validado.');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('ERROR: no fue posible crear tabla de prueba: ' || SQLERRM);
        RAISE;
END;
/

PROMPT ============================================================
PROMPT Validacion terminada. Si no hubo errores, ejecutar:
PROMPT 01_CORE_INTEGRACION.sql
PROMPT 02_SECURITY_USERS.sql
PROMPT ============================================================
