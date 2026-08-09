# Autenticación LDAP en SIS-FACT / Billing One

## Decisión funcional

SIS-FACT usa el mismo enfoque operativo esperado para ATLAS:

```text
Usuario autorizado y rol en SIS-FACT -> Oracle local
Password corporativa                 -> LDAP
Sesión web                            -> Flask session
```

Esto significa que **crear usuario no consulta LDAP**. Crear usuario solo registra en Oracle que esa persona está autorizada para entrar a SIS-FACT y qué rol tendrá.

LDAP se usa únicamente cuando el usuario intenta iniciar sesión.

## Tabla de usuarios

La tabla principal de autorización es:

```text
RM_CFACT_USER
```

Campos principales:

```text
USERNAME       usuario corporativo sin dominio
DISPLAY_NAME   nombre visible
EMAIL          correo
ROLE_CODE      rol funcional
AUTH_TYPE      LDAP / LOCAL / SERVICE
ACTIVE         Y / N
```

## Normalización de usuario

El login acepta estas formas:

```text
rmunoz
EMPRESA\rmunoz
rmunoz@empresa.local
```

Para buscar autorización local en `RM_CFACT_USER`, SIS-FACT normaliza a:

```text
rmunoz
```

Para autenticar contra LDAP, SIS-FACT arma el usuario de bind según `login_format`.

Con `login_format = UPN`:

```text
rmunoz@empresa.local
```

Con `login_format = NETBIOS`:

```text
EMPRESA\rmunoz
```

## Configuración requerida

El archivo `config.ini` local debe contener:

```ini
[ldap]
enabled = true
servers = ldap01.empresa.local,ldap02.empresa.local
port = 636
use_ssl = true
start_tls = false
validate_certificate = true
ca_cert_file =
tls_ciphers = DEFAULT:@SECLEVEL=0
authentication = SIMPLE
login_format = UPN
domain_suffix = empresa.local
netbios_domain = EMPRESA
connect_timeout = 5
receive_timeout = 8
```

## Crear usuario LDAP autorizado

El primer usuario se debe crear por SQL, porque la API de creación requiere sesión ADMIN.

```sql
INSERT INTO rm_cfact_user (
    username, display_name, email, role_code, auth_type, active, created_by
) VALUES (
    'rmunoz', 'Ruben Muñoz', 'rmunoz@empresa.local', 'ADMIN', 'LDAP', 'Y', 'INSTALL'
);
COMMIT;
```

Después de iniciar sesión como ADMIN, también se puede crear por API:

```http
POST /api/v1/security/users
Content-Type: application/json
```

```json
{
  "username": "nuevo.usuario",
  "display_name": "Nuevo Usuario",
  "email": "nuevo.usuario@empresa.local",
  "role_code": "VIEWER",
  "auth_type": "LDAP"
}
```

## Login web

Abrir:

```text
http://127.0.0.1:5060/login
```

Flujo:

1. El usuario ingresa usuario y password.
2. SIS-FACT normaliza usuario para buscar autorización local.
3. SIS-FACT valida que el usuario exista en `RM_CFACT_USER` y esté activo.
4. Si `AUTH_TYPE = LDAP`, SIS-FACT hace bind contra LDAP.
5. Si LDAP responde OK, se crea sesión Flask.
6. Se redirige a `/app`.

## Endpoints de validación

```text
GET /health
GET /api/v1/health
GET /api/v1/security/ldap/status
GET /me
GET /logout
```

## Regla de seguridad

Nunca guardar password LDAP en Oracle. Para usuarios LDAP solo se guarda autorización local y rol.
