# Changelog

## v0.2.4 - 2026-08-11

Control operativo de ejecución de insumos.

### Ejecución
- Se elimina la frecuencia libre como mecanismo de control y se incorpora una política administrable por insumo.
- Modos `MANUAL`, `SCHEDULED` y `EXTERNAL`.
- Nueva cola por insumo/scope con reintentos y trazabilidad.
- Nuevo panel `Ejecuciones` con última corrida, filas leídas, próxima ejecución y cola abierta.
- Acción `Ejecutar ahora` con permiso `CONTROL_EXECUTE` y alcance por scope.

### Procesos
- `BillingOne_Scheduler` agenda y encola sin ejecutar la adquisición.
- `BillingOne_Worker` procesa la cola de manera independiente de Flask/Waitress.
- Scripts NSSM para Scheduler y Worker.

### Adquisición inicial
- Oracle SQL y SQL Server SQL restringidos a `SELECT/WITH`.
- REST GET.
- Archivos por patrón.
- SOAP valida WSDL y deja `WARNING` hasta parametrizar una operación específica.
- `ROWS_READ` se registra; `ROWS_LOADED` queda reservado para la futura capa persistente de staging/normalización.

### Oracle
- Nuevas tablas `RM_CFACT_EXECUTION_POLICY` y `RM_CFACT_EXECUTION_QUEUE`.
- Modelo global: 28 tablas Billing One.
- Parche `migration_v0_2_3_to_v0_2_4` con precheck/aplicación/validación.
- El parche incorpora SGA/DHT idempotentemente si faltan.
- Usuarios, LDAP, roles/permisos y `SISGAV2` quedan fuera del cambio.

## v0.2.3 - 2026-08-11

Mantenedor dedicado de Orígenes funcionales.

### Contexto
- Nueva pantalla `Contexto -> Administrar Orígenes`.
- Alta de orígenes sin modificar código.
- Edición del nombre manteniendo código estable.
- Activación/reactivación y baja lógica.
- Visualización de scopes y flujos activos por origen.
- Se bloquea la desactivación de un origen con dependencias activas.

### Datos base
- Se agregan `SGA` y `DHT` a la carga base de orígenes.
- SQL idempotente compatible con DBeaver.
- No hay cambios de estructura Oracle.

## v0.2.2 - 2026-08-11

Mejora de navegación y usabilidad sin cambios de base de datos.

### Navegación
- Barra principal persistente: `Inicio`, `Contexto`, `Fuentes e integraciones`, `Usuarios`.
- Opciones visibles según permisos del usuario.
- Sección activa resaltada.
- Barra secundaria contextual con retorno al menú padre.

## v0.2.1 - 2026-08-11

Corrección del modelo funcional.

### Contexto Billing
- Jerarquía `RUT emisor -> Negocio -> Origen -> Tipo de emisión -> Flujo opcional`.
- `DOM` y `Ciclo` dejan de ser dimensiones universales.
- Se agregan `RM_CFACT_ORIGIN`, `RM_CFACT_EMISSION_TYPE` y `RM_CFACT_FLOW`.
- Se agregan `RM_CFACT_EMISSION_STATUS` y `RM_CFACT_ISSUE`.
- Puerto web cambiado a `5040`.

## v0.2.0 - 2026-08-10

Reconstrucción de la base técnica de Billing One usando ATLAS S.2.0 como baseline de infraestructura.

- Flask, Oracle, LDAP, CSRF, seguridad web y auditoría.
- Roles/permisos y scopes.
- Conexiones e insumos administrables.
- `SISGAV2` fuera de alcance.

## v0.1.0

Base técnica inicial histórica. Consultar commits anteriores a v0.2.0.
