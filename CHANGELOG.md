# Changelog

## v0.2.0 - 2026-08-10

Reconstrucción de la base técnica de Billing One usando ATLAS S.2.0 como baseline de infraestructura.

### Cambios principales
- Se retira del árbol vigente la base técnica v0.1; su historia queda en Git.
- Configuración real obligatoria y sin fallback inseguro.
- Pool Oracle y Thick Mode siguiendo patrón ATLAS.
- CSRF, CSP, headers de seguridad, request-id y logging rotativo.
- Login LDAP/local con rate limiting por usuario e IP.
- Sesiones con timeout, revalidación y revocación por `SESSION_VERSION`.
- Roles, permisos y overrides individuales.
- Mantenedor web de usuarios LDAP.
- Modelo multidimensional Empresa/RUT/Negocio/DOM/Ciclo.
- Modelo Conexión/Insumo/Alcance para Oracle, SQL Server, REST, SOAP y archivos.
- DDL separado de validadores y rollback greenfield.
- `SISGAV2` documentada como objeto protegido y fuera de alcance.
- IA removida del core inicial; se reintroducirá cuando el dominio esté consolidado.

## v0.1.0

Base técnica inicial histórica. Consultar commits anteriores a v0.2.0.
