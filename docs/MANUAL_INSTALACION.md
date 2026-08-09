# Manual de instalación SIS-FACT / Billing One v0.1.0

## 1. Objetivo

Este manual permite instalar y ejecutar **SIS-FACT / Billing One** en Windows usando la ruta operativa acordada:

```text
K:\@@@@@sis-fact
```

La versión `v0.1.0` instala la base técnica consolidada del sistema:

- Aplicación Flask independiente.
- Configuración externa sin secretos versionados.
- Conectores base Oracle, SQL Server, REST, SOAP y archivos.
- Login LDAP estilo ATLAS con autorización local en Oracle.
- Registro de fuentes de datos.
- Registro de extracciones.
- Healthcheck técnico.
- Capa inicial de analítica e IA.

## 2. Regla obligatoria de tablas Oracle

Todas las tablas propias del sistema deben comenzar con:

```text
RM_CFACT_
```

Tablas base de esta versión:

```text
RM_CFACT_DATA_SOURCE
RM_CFACT_EXTRACTION_RUN
RM_CFACT_INTEGRATION_CALL
RM_CFACT_AUDIT_LOG
RM_CFACT_AI_PROVIDER
RM_CFACT_USER
```

No crear tablas nuevas del sistema con prefijo `SIS_`, `BO_`, `BILLING_` u otro distinto.

## 3. Regla de entrega única

El repositorio mantiene una sola versión vigente en `main`.

```text
NO usar como versión principal:
- sis-fact-main/
- sis-fact-main.zip
- .venv.venv/
- carpetas patch_*
- copias manuales del código
```

La carpeta local válida para ejecución es:

```text
K:\@@@@@sis-fact
```

El único entorno virtual esperado es:

```text
K:\@@@@@sis-fact\.venv
```

El script local de ejecución es:

```text
K:\@@@@@sis-fact\run_dev.cmd
```

## 4. Requisitos del servidor

```text
Windows Server o Windows 10/11 para desarrollo
Python 3.11 o superior
Git opcional
Oracle Instant Client, si se usará Oracle thick mode
ODBC Driver 17 o 18 for SQL Server, si se usará SQL Server
Acceso de red a Oracle / SQL Server / LDAP / APIs según corresponda
```

Puertos sugeridos:

```text
ATLAS, si existe:       5050
SIS-FACT / Billing One: 5060
```

## 5. Obtener código fuente

### Opción manual recomendada

1. Abrir en navegador el repositorio `rrmunoz-coder/sis-fact`.
2. Presionar **Code**.
3. Elegir **Download ZIP**.
4. Descomprimir.
5. Renombrar la carpeta descomprimida a `sis-fact`.
6. Dejarla en:

```text
K:\@@@@@sis-fact
```

### Opción con Git instalado

```cmd
K:
cd \
git clone https://github.com/rrmunoz-coder/sis-fact.git @@@@@sis-fact
cd /d K:\@@@@@sis-fact
```

Actualizar:

```cmd
cd /d K:\@@@@@sis-fact
git pull
```

## 6. Crear entorno virtual

```cmd
cd /d K:\@@@@@sis-fact
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

No usar `.venv.venv`.

## 7. Configuración local

Copiar ejemplo:

```cmd
cd /d K:\@@@@@sis-fact
copy config.ini.example config.ini
```

El archivo real queda en:

```text
K:\@@@@@sis-fact\config.ini
```

Debe tener secciones:

```ini
[flask]
[oracle]
[ldap]
[sqlserver_fact]
[ai]
```

No subir nunca `config.ini` real al repositorio.

## 8. Validar ambiente y crear tablas base Oracle

Conectarse al esquema Oracle donde vivirá SIS-FACT y ejecutar **siempre en este orden**:

```text
sql/00_VALIDAR_AMBIENTE.sql
sql/01_CORE_INTEGRACION.sql
sql/02_SECURITY_USERS.sql
```

El `00_VALIDAR_AMBIENTE.sql` se ejecuta primero porque valida conexión, esquema, privilegios y objetos existentes. No crea las tablas finales del sistema.

Desde DBeaver, ejecutar los archivos ubicados en:

```text
K:\@@@@@sis-fact\sql\00_VALIDAR_AMBIENTE.sql
K:\@@@@@sis-fact\sql\01_CORE_INTEGRACION.sql
K:\@@@@@sis-fact\sql\02_SECURITY_USERS.sql
```

Si antes se alcanzaron a crear tablas con prefijo `SIS_`, revisar y ejecutar la migración manual:

```text
sql/90_RENAME_SIS_TO_RM_CFACT.sql
```

## 9. Crear usuario inicial autorizado

Ejemplo para usuario LDAP:

```sql
INSERT INTO rm_cfact_user (
    username,
    display_name,
    email,
    role_code,
    auth_type,
    active,
    created_by
) VALUES (
    'tu_usuario',
    'Tu Nombre',
    'tu_usuario@clarochile.org',
    'ADMIN',
    'LDAP',
    'Y',
    'INSTALL'
);

COMMIT;
```

La password no se guarda en Oracle. LDAP la valida al momento del login.

El login acepta:

```text
tu_usuario
CLAROCHILE\tu_usuario
tu_usuario@clarochile.org
```

Para autorización local se normaliza al usuario sin dominio.

## 10. Ejecutar en modo desarrollo

Ejecutar:

```cmd
cd /d K:\@@@@@sis-fact
run_dev.cmd
```

Abrir en Chrome o Edge:

```text
http://127.0.0.1:5060/health
http://127.0.0.1:5060/api/v1/security/ldap/status
http://127.0.0.1:5060/login
```

No usar Internet Explorer para validar JSON.

## 11. Ejecutar con Waitress

```cmd
cd /d K:\@@@@@sis-fact
.venv\Scripts\waitress-serve.exe --host=0.0.0.0 --port=5060 wsgi:app
```

## 12. Instalar como servicio Windows

Servicio sugerido:

```text
SISFACT_BillingOne
```

Crear logs:

```cmd
mkdir K:\@@@@@sis-fact\logs
```

Con NSSM:

```cmd
D:\tools\nssm\nssm.exe install SISFACT_BillingOne
```

Configurar:

```text
Application path:
K:\@@@@@sis-fact\.venv\Scripts\waitress-serve.exe

Startup directory:
K:\@@@@@sis-fact

Arguments:
--host=0.0.0.0 --port=5060 wsgi:app
```

Logs NSSM:

```text
I/O > Output:
K:\@@@@@sis-fact\logs\service_out.log

I/O > Error:
K:\@@@@@sis-fact\logs\service_err.log
```

Iniciar:

```cmd
net start SISFACT_BillingOne
```

Detener:

```cmd
net stop SISFACT_BillingOne
```

## 13. Validaciones

```cmd
netstat -ano | findstr :5060
curl http://127.0.0.1:5060/health
curl http://127.0.0.1:5060/api/v1/security/ldap/status
```

Endpoints:

```text
http://127.0.0.1:5060/health
http://127.0.0.1:5060/api/v1/health
http://127.0.0.1:5060/api/v1/security/ldap/status
http://127.0.0.1:5060/login
http://127.0.0.1:5060/app
```

## 14. Troubleshooting rápido

### Puerto ocupado

```cmd
netstat -ano | findstr :5060
```

### Servicio inicia y se detiene

Revisar:

```text
K:\@@@@@sis-fact\logs\service_err.log
K:\@@@@@sis-fact\logs\service_out.log
```

### LDAP falla por certificado

Para prueba controlada:

```ini
validate_certificate=false
```

Para ambiente formal, instalar CA y configurar:

```ini
ca_cert_file=C:\ruta\certificado_ca.pem
```

### Login dice usuario no registrado

Validar:

```sql
SELECT username, display_name, email, role_code, auth_type, active
FROM rm_cfact_user
WHERE LOWER(username) = LOWER('tu_usuario');
```

## 15. Checklist

```text
[ ] Código en K:\@@@@@sis-fact
[ ] No usar sis-fact-main ni zip como carpeta activa
[ ] Entorno virtual .venv creado
[ ] Dependencias instaladas
[ ] config.ini real local creado
[ ] 00_VALIDAR_AMBIENTE.sql ejecutado OK
[ ] 01_CORE_INTEGRACION.sql ejecutado OK
[ ] 02_SECURITY_USERS.sql ejecutado OK
[ ] Usuario inicial cargado en RM_CFACT_USER
[ ] run_dev.cmd levanta puerto 5060
[ ] /health OK
[ ] /api/v1/security/ldap/status OK
[ ] /login visible
[ ] /app visible después de login
```
