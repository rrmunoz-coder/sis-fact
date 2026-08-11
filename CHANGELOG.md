# Changelog

## v0.2.3 - 2026-08-11

Mantenedor dedicado de Orígenes funcionales.

### Contexto
- Nueva pantalla `Contexto -> Administrar Orígenes`.
- Alta de orígenes sin modificar código.
- Activación/reactivación y baja lógica.
- Visualización de scopes y flujos activos por origen.
- Se bloquea la desactivación de un origen con dependencias activas.
- El catálogo deja de quedar escondido dentro del mantenedor general de Contexto.

### Datos base
- Se agregan `SGA` y `DHT` a la carga base de orígenes.
- Se incorpora `sql/migration_v0_2_2_to_v0_2_3/10_ORIGENES_BASE.sql`, idempotente y compatible con DBeaver.
- No hay cambios de estructura Oracle.

### Operación
- API health actualizada a `0.2.3`.
- Puerto web permanece en `5040`.

## v0.2.2 - 2026-08-11

Mejora de navegación y usabilidad sin cambios de base de datos.

### Navegación
- Barra principal persistente: `Inicio`, `Contexto`, `Fuentes e integraciones`, `Usuarios`.
- Opciones visibles según permisos del usuario.
- Sección activa resaltada.
- Barra secundaria contextual con retorno al menú padre.
- Se retiran botones locales `Volver` de formularios de conexión, insumo y usuario.
- La navegación deja de depender del botón Atrás del navegador.

### Operación
- API health actualizada a `0.2.2`.
- Puerto web permanece en `5040`.
- No requiere SQL ni cambios Oracle.

## v0.2.1 - 2026-08-11

Corrección del modelo funcional antes de cargar configuración operativa real.

### Contexto Billing
- Se redefine la jerarquía como `RUT emisor -> Negocio -> Origen -> Tipo de emisión -> Flujo opcional`.
- `DOM` y `Ciclo` dejan de ser dimensiones universales.
- Se agregan `RM_CFACT_ORIGIN`, `RM_CFACT_EMISSION_TYPE` y `RM_CFACT_FLOW`.
- `RM_CFACT_FLOW.SEGMENT_LABEL` permite expresar `DOM`, `CICLO`, `LOTE` u otro segmentador según el origen.
- `RM_CFACT_COMPANY` queda como agrupación opcional del RUT emisor, fuera del scope operativo.
- Se retiran `RM_CFACT_DOM` y `RM_CFACT_CYCLE` del modelo vigente.

### Resultado operacional
- Se agrega `RM_CFACT_EMISSION_STATUS` para estado, completitud, Q esperada/emitida/rechazada, issues y monto.
- Se agrega `RM_CFACT_ISSUE` para detalle de incidencias.

### Integraciones
- Las conexiones continúan siendo técnicas.
- El origen funcional se obtiene desde el scope y no se duplica en la conexión.
- Formularios de conexión/insumo actualizados a la nueva jerarquía.

### Operación
- Puerto web oficial cambiado a `5040`; `5060` se abandona por ser puerto restringido por navegadores Chromium.
- Health API reporta `0.2.1`.

### Migración
- Se incorpora parche DBeaver/Oracle `v0.2.0 -> v0.2.1` con precheck, aplicación y validación.
- Usuarios, LDAP, roles, permisos y `SISGAV2` quedan fuera del parche.

## v0.2.0 - 2026-08-10

Reconstrucción de la base técnica de Billing One usando ATLAS S.2.0 como baseline de infraestructura.

### Base técnica
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
- Modelo inicial Empresa, RUT emisor, Negocio, DOM y Ciclo; reemplazado por v0.2.1 antes de carga operativa.

### Fuentes e integraciones
- Separación Conexión / Insumo / Scope.
- Tipos Oracle, SQL Server, REST, SOAP y FILE.
- `CREDENTIAL_REF` externo y rechazo de secretos en `CONFIG_JSON`.

### Oracle
- Modelo greenfield inicial de 23 tablas `RM_CFACT_*`.
- `SISGAV2` documentada como objeto protegido y fuera de alcance.

## v0.1.0

Base técnica inicial histórica. Consultar commits anteriores a v0.2.0.
