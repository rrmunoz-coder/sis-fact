# Changelog

## v0.2.0 - 2026-08-10

Reconstrucción de la base técnica de Billing One usando ATLAS S.2.0 como baseline de infraestructura.

### Base técnica
- Se retira del árbol vigente la base técnica v0.1; su historia queda en Git.
- Configuración real obligatoria y sin fallback inseguro.
- Pool Oracle y Thick Mode siguiendo patrón ATLAS.
- CSRF, CSP, headers de seguridad, request-id y logging rotativo.
- Login LDAP/local con rate limiting por usuario e IP.
- Sesiones con timeout, revalidación y revocación por `SESSION_VERSION`.
- Waitress/NSSM, validadores de release, higiene y CI.

### Seguridad y administración
- Roles y permisos con override individual.
- Scopes de usuario con Ver / Ejecutar / Configurar.
- ADMIN con alcance global.
- Mantenedor web de usuarios LDAP.

### Contexto Billing
- Empresa, RUT emisor, Negocio, DOM y Ciclo.
- `RM_CFACT_SCOPE` multidimensional sin jerarquía rígida.
- Mantenedor web de catálogos y alcances.

### Fuentes e integraciones
- Separación Conexión / Insumo / Scope.
- Mantenedor web de conexiones e insumos.
- Tipos Oracle, SQL Server, REST, SOAP y FILE.
- Prueba de conexión con trazabilidad.
- `CREDENTIAL_REF` externo y rechazo de secretos en `CONFIG_JSON`.
- Desactivación en lugar de borrado físico.
- Creación/edición transaccional para evitar configuraciones parciales.

### Oracle
- Modelo greenfield de 23 tablas `RM_CFACT_*` entre Seguridad, Contexto e Integración.
- DDL acompañado de validadores por bloque y validador global.
- `SISGAV2` documentada como objeto protegido y fuera de alcance.
- IA removida del core inicial; se reintroducirá cuando el dominio esté consolidado.

## v0.1.0

Base técnica inicial histórica. Consultar commits anteriores a v0.2.0.
