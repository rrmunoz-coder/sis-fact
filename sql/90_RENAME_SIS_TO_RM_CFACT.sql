-- SIS-FACT / Billing One
-- Migracion auxiliar para ambientes donde se hayan creado tablas antiguas con prefijo SIS_.
-- Ejecutar solo si existen tablas antiguas. Validar previamente con el DBA.

DECLARE
    PROCEDURE rename_if_exists(p_old_name VARCHAR2, p_new_name VARCHAR2) IS
        v_count NUMBER;
    BEGIN
        SELECT COUNT(*)
          INTO v_count
          FROM user_tables
         WHERE table_name = UPPER(p_old_name);

        IF v_count > 0 THEN
            EXECUTE IMMEDIATE 'ALTER TABLE ' || p_old_name || ' RENAME TO ' || p_new_name;
        END IF;
    END;
BEGIN
    rename_if_exists('SIS_USER', 'RM_CFACT_USER');
    rename_if_exists('SIS_DATA_SOURCE', 'RM_CFACT_DATA_SOURCE');
    rename_if_exists('SIS_EXTRACTION_RUN', 'RM_CFACT_EXTRACTION_RUN');
    rename_if_exists('SIS_INTEGRATION_CALL', 'RM_CFACT_INTEGRATION_CALL');
    rename_if_exists('SIS_AUDIT_LOG', 'RM_CFACT_AUDIT_LOG');
    rename_if_exists('SIS_AI_PROVIDER', 'RM_CFACT_AI_PROVIDER');
END;
/

-- Nota: constraints e índices existentes conservarán el nombre antiguo si ya estaban creados.
-- Para instalación limpia, preferir ejecutar 01_CORE_INTEGRACION.sql y 02_SECURITY_USERS.sql actualizados.
