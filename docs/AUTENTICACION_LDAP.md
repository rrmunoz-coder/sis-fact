# Autenticación LDAP en SIS-FACT / Billing One

## Decisión funcional

SIS-FACT usa el mismo enfoque esperado para Altas:

```text
Usuario existe y tiene rol en SIS-FACT  -> Oracle local
Password corporativa                    -> LDAP
Sesión web                               -> Flask session
```

Esto significa que **crear usuario no consulta LDAP**. Crear usuario solo registra en Oracle que esa persona está autorizada para entrar a SIS-FACT y qué rol tendrá.

El LDAP se usa únicamente cuando el usuario intenta iniciar sesión.

## Regla de naming de tablas

Todas las tablas propias de SIS-FACT / Billing One deben comenzar con:

```text
RM_CFACT_
```

Por eso la tabla de usuarios es:

```text
RM_CFACT_USER
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

Para un usuario `rmunoz`, con `login_format = UPN`, el bind LDAP se realiza como:

```text
rmunoz@empresa.local
```

Si el usuario escribe el correo completo en el login, se respeta el valor ingresado.

## Tabla de usuarios

Ejecutar:

```text
sql/02_SECURITY_USERS.sql
```

Tabla principal:

```text
RM_CFACT_USER
```

Campos principales:

```text
USERNAME       usuario corporativo sin password
DISPLAY_NAME   nombre visible
EMAIL          correo
ROLE_CODE      rol funcional
AUTH_TYPE      LDAP / LOCAL / SERVICE
ACTIVE         Y / N
```

## Crear usuario LDAP autorizado

Ejemplo SQL:

```sql
INSERT INTO rm_cfact_user (
    username, display_name, email, role_code, auth_type, active, created_by
) VALUES (
    'rmunoz', 'Ruben Muñoz', 'rmunoz@empresa.local', 'ADMIN', 'LDAP', 'Y', 'INSTALL'
);
COMMIT;
```

También se puede crear por API:

```http
POST /api/v1/security/users
Content-Type: application/json
```

```json
{
  "username": "rmunoz",
  "display_name": "Ruben Muñoz",
  "email": "rmunoz@empresa.local",
  "role_code": "ADMIN",
  "auth_type": "LDAP"
}
```

## Login web

Abrir:

```text
http://localhost:5060/login
```

Flujo:

1. El usuario ingresa usuario y password.
2. SIS-FACT valida que el usuario exista en `RM_CFACT_USER` y esté activo.
3. Si `AUTH_TYPE = LDAP`, SIS-FACT hace bind contra LDAP.
4. Si LDAP responde OK, se crea sesión Flask.

## Endpoints de validación

```text
GET /api/v1/security/ldap/status
GET /me
GET /logout
```

## Regla de seguridad

Nunca guardar password LDAP en Oracle. Para usuarios LDAP solo se guarda autorización local y rol.
