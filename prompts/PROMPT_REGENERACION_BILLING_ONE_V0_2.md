# Prompt de regeneración Billing One v0.2.0

Reconstruir SIS-FACT / Billing One respetando estas reglas:

1. Repositorio único `rrmunoz-coder/sis-fact`, rama vigente `main`.
2. Ruta operativa `K:\@@@@@sis-fact`; puerto 5060.
3. Base técnica derivada del patrón ATLAS S.2.0: Flask, Oracle pool, LDAP, sesiones revocables, rate limiting, CSRF, CSP, logging, auditoría, Waitress/NSSM, pruebas y validadores.
4. No copiar dominio ATLAS ni tablas `GT_*`.
5. Todos los objetos propios Oracle comienzan con `RM_CFACT_`.
6. LDAP solo autentica password. Oracle autoriza usuario, rol, permisos y alcance. Password LDAP nunca se almacena.
7. Contexto multidimensional: Empresa, RUT emisor, Negocio, DOM y Ciclo mediante scopes combinables, sin jerarquía rígida obligatoria.
8. Separar Conexión de Insumo. Los controles consumen conceptos funcionales, no tecnologías físicas.
9. Soportar Oracle, SQL Server, REST, SOAP y archivos. No todos los negocios usan todas las conexiones.
10. Conexiones/insumos se asignan por scope. Una conexión puede ser exclusiva o compartida.
11. `CONFIG_JSON` no contiene secretos; usar `CREDENTIAL_REF` a almacenamiento externo.
12. Cada bloque Oracle tiene DDL + validador. DDL actual: seguridad, contexto e integración. El validador final debe detectar objetos inválidos e inconsistencias funcionales.
13. `config.ini` real, `.venv`, logs, ZIP, datos y `nssm.exe` no se versionan.
14. `SISGAV2` es ajena a Billing One y nunca debe ser modificada ni incluida en rollback/migración.
15. No ejecutar limpieza de v0.1 hasta obtener conteos reales y generar migración explícita sin comodines destructivos.

Fuente de verdad de esta versión: README.md, docs/ARQUITECTURA_V0_2.md y sql/.
