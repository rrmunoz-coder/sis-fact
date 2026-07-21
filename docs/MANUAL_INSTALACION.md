# Manual de instalación SIS-FACT / Billing One v0.1.0

## 1. Objetivo

Este manual permite instalar y ejecutar **SIS-FACT / Billing One** en Windows usando la ruta operativa acordada:

```text
K:\@@@@@\sis-fact
```

La versión `v0.1.0` instala la base técnica del sistema:

- Aplicación Flask independiente.
- Configuración externa sin secretos versionados.
- Conectores base Oracle, SQL Server, REST, SOAP y archivos.
- Login LDAP estilo Altas con autorización local en Oracle.
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

## 3. Requisitos del servidor

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

## 4. Obtener código fuente

Ruta final esperada:

```cmd
cd /d K:\@@@@@\sis-fact
```

### Opción manual recomendada

1. Abrir en navegador el repositorio `rrmunoz-coder/sis-fact`.
2. Presionar **Code**.
3. Elegir **Download ZIP**.
4. Descomprimir.
5. Renombrar la carpeta a `sis-fact`.
6. Dejarla en:

```text
K:\@@@@@\sis-fact
```

### Opción con Git instalado

```cmd
K:
cd \@@@@@
git clone https://github.com/rrmunoz-coder/sis-fact.git
cd sis-fact
```

Actualizar:

```cmd
cd /d K:\@@@@@\sis-fact
git pull
```

## 5. Crear entorno virtual

```cmd
cd /d K:\@@@@@\sis-fact
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 6. Configuración local

Copiar ejemplo:

```cmd
cd /d K:\@@@@@\sis-fact
copy config.ini.example config.ini
```

El archivo real queda en:

```text
K:\@@@@@\sis-fact\config.ini
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

## 7. Crear tablas base Oracle

Conectarse al esquema Oracle donde vivirá SIS-FACT y ejecutar en este orden:

```text
sql/01_CORE_INTEGRACION.sql
sql/02_SECURITY_USERS.sql
```

Desde SQL Developer o DBeaver, ejecutar los archivos ubicados en:

```text
K:\@@@@@\sis-fact\sql\01_CORE_INTEGRACION.sql
K:\@@@@@\sis-fact\sql\02_SECURITY_USERS.sql
```

Si antes se alcanzaron a crear tablas con prefijo `SIS_`, revisar y ejecutar la migración manual:

```text
sql/90_RENAME_SIS_TO_RM_CFACT.sql
```

## 8. Crear usuario inicial autorizado

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

## 9. Ejecutar en modo desarrollo

```cmd
cd /d K:\@@@@@\sis-fact
.venv\Scripts\activate
python -m flask --app wsgi:app run --host 0.0.0.0 --port 5060 --debug
```

Abrir:

```text
http://localhost:5060/health
http://localhost:5060/api/v1/security/ldap/status
http://localhost:5060/login
```

## 10. Ejecutar con Waitress

```cmd
cd /d K:\@@@@@\sis-fact
.venv\Scripts\activate
waitress-serve --host=0.0.0.0 --port=5060 wsgi:app
```

## 11. Instalar como servicio Windows

Servicio sugerido:

```text
SISFACT_BillingOne
```

Crear logs:

```cmd
mkdir K:\@@@@@\sis-fact\logs
```

Con NSSM:

```cmd
D:\tools\nssm\nssm.exe install SISFACT_BillingOne
```

Configurar:

```text
Application path:
K:\@@@@@\sis-fact\.venv\Scripts\waitress-serve.exe

Startup directory:
K:\@@@@@\sis-fact

Arguments:
--host=0.0.0.0 --port=5060 wsgi:app
```

Logs NSSM:

```text
I/O > Output:
K:\@@@@@\sis-fact\logs\service_out.log

I/O > Error:
K:\@@@@@\sis-fact\logs\service_err.log
```

Iniciar:

```cmd
net start SISFACT_BillingOne
```

Detener:

```cmd
net stop SISFACT_BillingOne
```

Reiniciar:

```cmd
net stop SISFACT_BillingOne
net start SISFACT_BillingOne
```

## 12. Validaciones

```cmd
sc query SISFACT_BillingOne
netstat -ano | findstr :5060
```

Endpoints:

```text
http://localhost:5060/health
http://localhost:5060/api/v1/sources
http://localhost:5060/api/v1/sources/health
http://localhost:5060/api/v1/security/ldap/status
http://localhost:5060/login
```

## 13. Troubleshooting rápido

### Puerto ocupado

```cmd
netstat -ano | findstr :5060
```

### Servicio inicia y se detiene

Revisar:

```text
K:\@@@@@\sis-fact\logs\service_err.log
K:\@@@@@\sis-fact\logs\service_out.log
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

## 14. Checklist

```text
[ ] Código en K:\@@@@@\sis-fact
[ ] Entorno virtual creado
[ ] Dependencias instaladas
[ ] config.ini real creado localmente
[ ] Tablas RM_CFACT_ creadas
[ ] Usuario inicial cargado en RM_CFACT_USER
[ ] LDAP responde o está configurado
[ ] Flask responde en modo manual
[ ] Waitress responde manualmente
[ ] Servicio Windows instalado
[ ] Healthcheck OK
```
