# Estado del proyecto SIS-FACT / Billing One

Fecha de referencia: 2026-08-09

## Resumen ejecutivo

El proyecto se encuentra en **Fase 1: estabilización técnica y cierre de base operativa**.

No está todavía en fase funcional de facturación ni en MVP de negocio. El foco actual es dejar una base limpia, única y ejecutable, con instalación reproducible, conexión Oracle, autenticación estilo ATLAS y reglas de despliegue ordenadas.

## Fase actual

```text
Fase 0 - Diseño conceptual y separación de ATLAS      COMPLETADA
Fase 1 - Base técnica / instalación / login           EN CURSO
Fase 2 - Modelo funcional de facturación              PENDIENTE
Fase 3 - Integraciones reales y controles             PENDIENTE
Fase 4 - Paneles operativos/directivos                PENDIENTE
Fase 5 - Servicio Windows / operación productiva      PENDIENTE
```

## Qué ya quedó definido

### Arquitectura general

- SIS-FACT / Billing One queda separado de ATLAS.
- Comparte dinámica técnica similar: Flask, Oracle, configuración externa y separación por capas.
- ATLAS queda para tiempo/capacidad/proyectos/esfuerzo.
- SIS-FACT queda para facturación, ciclos, emisión, foliación, SII, NC, pagos, controles y caja.

### Entrega única

La versión vigente queda en la rama principal del repositorio:

```text
main
```

No se deben manejar como versión principal:

```text
sis-fact-main/
sis-fact-main.zip
patch_*/
.venv.venv/
inicia.bat
```

La regla de entrega es:

```text
commit GitHub + instrucciones de actualización
```

No:

```text
zip suelto + carpeta duplicada + script alternativo no versionado
```

### Ruta operativa

Ruta usada en el servidor:

```text
K:\@@@@@sis-fact
```

La carpeta activa debe contener:

```text
sisfact/
sql/
docs/
requirements.txt
run_dev.cmd
wsgi.py
config.ini
```

## Reglas técnicas vigentes

### Naming Oracle

Todas las tablas propias del sistema deben comenzar con:

```text
RM_CFACT_
```

Tablas base actuales:

```text
RM_CFACT_DATA_SOURCE
RM_CFACT_EXTRACTION_RUN
RM_CFACT_INTEGRATION_CALL
RM_CFACT_AUDIT_LOG
RM_CFACT_AI_PROVIDER
RM_CFACT_USER
```

No crear tablas nuevas con prefijos `SIS_`, `BO_`, `BILLING_` u otro distinto.

### Autenticación estilo ATLAS

La regla funcional queda así:

```text
Usuario autorizado / rol -> Oracle local, RM_CFACT_USER
Password corporativa     -> LDAP
Sesión web               -> Flask session
```

Reglas:

- Crear usuario no consulta LDAP.
- LDAP solo valida password al momento del login.
- La password LDAP nunca se guarda en Oracle.
- El login debe aceptar `usuario`, `DOMINIO\usuario` o `usuario@dominio`.
- Para autorización local se normaliza a usuario sin dominio.

## Qué existe hoy en el código

### Backend Flask

- `wsgi.py` como entrada WSGI.
- `sisfact/__init__.py` crea la app Flask, carga configuración y registra rutas.
- `sisfact/web/routes.py` contiene rutas base y healthcheck.
- `sisfact/auth/` contiene login, sesión, LDAP, modelos y repositorio de usuarios.

### Rutas base

```text
/                         redirige a login o app
/health                   texto plano OK
/api/v1/health            healthcheck JSON
/login                    formulario login
/app                      panel base post-login
/logout                   cierre de sesión
/me                       sesión actual
/api/v1/security/ldap/status
/api/v1/auth/login
/api/v1/security/users    creación usuario; requiere ADMIN
```

### SQL base

```text
sql/00_VALIDAR_AMBIENTE.sql
sql/01_CORE_INTEGRACION.sql
sql/02_SECURITY_USERS.sql
sql/90_RENAME_SIS_TO_RM_CFACT.sql
```

## Validaciones realizadas en servidor

### Validado OK

- `00_VALIDAR_AMBIENTE.sql` funcionó después de retirar `SET` y `PROMPT` para hacerlo compatible con DBeaver/SQL Developer.
- Flask levantó en puerto `5060`.
- `/health` respondió `HTTP 200` localmente.
- Se confirmó que Internet Explorer intenta descargar JSON, por eso `/health` se cambió a texto plano.

### Aún no cerrado

- Login LDAP end-to-end no queda confirmado.
- Falta confirmar que el usuario real exista en `RM_CFACT_USER` con `AUTH_TYPE='LDAP'` y `ACTIVE='Y'`.
- Falta confirmar si LDAP acepta bind UPN con el usuario corporativo real.
- Falta probar `/app` después de login.
- Falta probar instalación como servicio Windows con Waitress/NSSM.
- Falta limpiar físicamente en servidor carpetas residuales como `sis-fact-main`, ZIP y `.venv.venv`.

## Riesgos actuales

| Riesgo | Estado | Acción |
|---|---|---|
| Carpeta local mezclada por ZIP/parches | Alto | Mantener solo `K:\@@@@@sis-fact` como carpeta activa |
| Scripts locales no versionados | Medio | Usar solo `run_dev.cmd` del repo |
| Login LDAP no validado | Alto | Probar con usuario real en `RM_CFACT_USER` |
| Config real con duplicados | Medio | Validar `config.ini` antes de iniciar |
| Servicio Windows no instalado | Bajo por ahora | Resolver después de login OK |

## Próximos pasos inmediatos

### Paso 1: limpiar carpeta operativa

Mantener activos:

```text
K:\@@@@@sis-fact\sisfact
K:\@@@@@sis-fact\sql
K:\@@@@@sis-fact\docs
K:\@@@@@sis-fact\.venv
K:\@@@@@sis-fact\config.ini
K:\@@@@@sis-fact\run_dev.cmd
K:\@@@@@sis-fact\wsgi.py
```

No usar:

```text
sis-fact-main
sis-fact-main.zip
.venv.venv
inicia.bat
```

### Paso 2: actualizar código desde GitHub

Descargar ZIP nuevo o hacer `git pull` si Git queda disponible. Copiar encima sin borrar:

```text
config.ini
.venv
```

### Paso 3: validar usuario autorizado

```sql
SELECT username, display_name, email, role_code, auth_type, active
FROM rm_cfact_user
WHERE LOWER(username) = LOWER('tu_usuario');
```

Debe existir con:

```text
AUTH_TYPE = LDAP
ACTIVE    = Y
```

### Paso 4: levantar con script oficial

```cmd
cd /d K:\@@@@@sis-fact
run_dev.cmd
```

### Paso 5: probar endpoints

```text
http://127.0.0.1:5060/health
http://127.0.0.1:5060/login
http://127.0.0.1:5060/app
```

### Paso 6: cerrar login LDAP

Probar con:

```text
tu_usuario
CLAROCHILE\tu_usuario
tu_usuario@dominio
```

## Definición de terminado para Fase 1

La Fase 1 se considera terminada cuando:

```text
[ ] Carpeta operativa limpia
[ ] Solo una versión activa desde GitHub main
[ ] config.ini validado sin duplicados
[ ] 00/01/02 ejecutados OK
[ ] Usuario ADMIN creado en RM_CFACT_USER
[ ] run_dev.cmd levanta sin errores
[ ] /health OK
[ ] /login visible
[ ] Login LDAP exitoso
[ ] /app visible después del login
[ ] Manual actualizado con estos pasos
```

## Fase siguiente

Cuando Fase 1 cierre, el proyecto pasa a:

```text
Fase 2 - Modelo funcional de facturación
```

Objetivos de Fase 2:

- Definir tablas de flujo, ciclo, período, ejecución y fase.
- Definir `BILLING_CASE` o su equivalente `RM_CFACT_`.
- Definir modelo de documentos, emisión, foliación, NC, pagos y SII.
- Crear pantallas base para navegación funcional.
- Incorporar primeros controles reales de facturación.
