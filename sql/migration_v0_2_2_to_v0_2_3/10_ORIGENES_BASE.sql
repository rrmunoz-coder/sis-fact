/* ============================================================
   BILLING ONE v0.2.3
   Mantenedor de Origenes - carga base idempotente
   Oracle / DBeaver SQL plano

   No modifica estructura. Solo agrega SGA y DHT si no existen.
   ============================================================ */

INSERT INTO RM_CFACT_ORIGIN (ORIGIN_CODE, ORIGIN_NAME, ACTIVE)
SELECT 'SGA', 'SGA', 'Y'
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1 FROM RM_CFACT_ORIGIN WHERE UPPER(ORIGIN_CODE)='SGA'
);

INSERT INTO RM_CFACT_ORIGIN (ORIGIN_CODE, ORIGIN_NAME, ACTIVE)
SELECT 'DHT', 'DHT', 'Y'
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1 FROM RM_CFACT_ORIGIN WHERE UPPER(ORIGIN_CODE)='DHT'
);

COMMIT;

SELECT ORIGIN_ID, ORIGIN_CODE, ORIGIN_NAME, ACTIVE
FROM RM_CFACT_ORIGIN
ORDER BY ORIGIN_NAME, ORIGIN_CODE;
