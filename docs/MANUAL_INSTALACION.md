# Manual de instalación SIS-FACT / Billing One v0.1.0

## 1. Objetivo

Este manual permite instalar y ejecutar la versión base de **SIS-FACT / Billing One** en un ambiente Windows de desarrollo o servidor.

La versión `v0.1.0` instala la base técnica del sistema:

- Aplicación Flask independiente.
- Configuración externa sin secretos versionados.
- Conectores base Oracle, SQL Server, REST, SOAP y archivos.
- Registro de fuentes de datos.
- Registro de extracciones.
- Healthcheck técnico.
- Capa inicial de analítica e IA.

Esta versión aún no contiene login productivo, dashboards finales ni consultas productivas de facturación.

---

## 2. Requisitos del servidor

### Software base

```text
Windows Server o Windows 10/11 para desarrollo
Python 3.11 o superior
Git
Oracle Instant Client, si se usará Oracle
ODBC Driver 17 o 18 for SQL Server, si se usará SQL Server
Acceso de red a Oracle / SQL Server / APIs según corresponda
```

### Puerto recomendado

Por defecto se propone:

```text
SIS-FACT / Billing One: 5060
ATLAS, si existe:       5050
```

Pueden convivir varias aplicaciones Flask en el mismo Windows siempre que usen puertos distintos.

---

## 3. Clonar repositorio

En el servidor, ubicar una carpeta de aplicaciones. Ejemplo:

```cmd
D:
cd D:\
git clone https://github.com/rrmunoz-coder/sis-fact.git
cd sis-fact
```

Otra ruta válida:

```cmd
K:\@@@@@SIS_FACT
```

La ruta final debe ser estable si se instalará como servicio Windows.

---

## 4. Crear entorno virtual

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Validar:

```cmd
python --version
pip list
```

---

## 5. Configuración local

Copiar el ejemplo:

```cmd
copy config.ini.example config.ini
```

Completar `config.ini` con los datos reales del ambiente.

Nunca subir `config.ini` real al repositorio.

### Ejemplo de configuración esperada

```ini
[app]
secret_key=CAMBIAR_EN_SERVIDOR
host=0.0.0.0
port=5060
debug=false

[oracle_default]
host=servidor_oracle
port=1521
service_name=servicio
user=usuario
password=password

[sqlserver_default]
server=servidor_sql
port=1433
database=FACT_2024
user=usuario
password=password
driver=ODBC Driver 17 for SQL Server
trust_server_certificate=yes

[ai]
provider=disabled
```

---

## 6. Crear tablas base Oracle

Conectarse al esquema Oracle donde vivirá SIS-FACT y ejecutar:

```text
sql/00_VALIDAR_AMBIENTE.sql
sql/01_CORE_INTEGRACION.sql
```

Orden sugerido:

```cmd
sqlplus usuario/password@servicio @sql/00_VALIDAR_AMBIENTE.sql
sqlplus usuario/password@servicio @sql/01_CORE_INTEGRACION.sql
```

También se puede ejecutar desde DBeaver usando la conexión Oracle correspondiente.

Tablas principales creadas:

```text
SIS_DATA_SOURCE
SIS_EXTRACTION_RUN
SIS_INTEGRATION_CALL
SIS_AUDIT_LOG
SIS_AI_PROVIDER
```

---

## 7. Ejecución en modo desarrollo

Activar entorno:

```cmd
.venv\Scripts\activate
```

Ejecutar:

```cmd
python -m flask --app wsgi:app run --host 0.0.0.0 --port 5060 --debug
```

Abrir en navegador:

```text
http://localhost:5060
http://localhost:5060/health
```

Desde otro equipo:

```text
http://NOMBRE_SERVIDOR:5060
```

Si no responde desde otro equipo, validar firewall y apertura del puerto 5060.

---

## 8. Ejecución productiva con Waitress

Para ambiente servidor se recomienda Waitress:

```cmd
.venv\Scripts\activate
waitress-serve --host=0.0.0.0 --port=5060 wsgi:app
```

Validar:

```text
http://localhost:5060/health
```

---

## 9. Instalación como servicio Windows

SIS-FACT debe poder quedar levantado como servicio independiente. Se recomienda crear un servicio llamado:

```text
SISFACT_BillingOne
```

### 9.1 Opción recomendada: NSSM

Descargar NSSM en el servidor y dejarlo fuera del repositorio, por ejemplo:

```text
D:\tools\nssm\nssm.exe
```

No versionar `nssm.exe`.

Instalar servicio:

```cmd
D:\tools\nssm\nssm.exe install SISFACT_BillingOne
```

Configurar en la ventana de NSSM:

```text
Application path:
D:\sis-fact\.venv\Scripts\python.exe

Startup directory:
D:\sis-fact

Arguments:
-m waitress --host=0.0.0.0 --port=5060 wsgi:app
```

Si el comando anterior no reconoce waitress como módulo, usar:

```text
Application path:
D:\sis-fact\.venv\Scripts\waitress-serve.exe

Startup directory:
D:\sis-fact

Arguments:
--host=0.0.0.0 --port=5060 wsgi:app
```

Configurar logs en NSSM:

```text
I/O > Output:
D:\sis-fact\logs\service_out.log

I/O > Error:
D:\sis-fact\logs\service_err.log
```

Crear carpeta de logs antes de iniciar:

```cmd
mkdir D:\sis-fact\logs
```

Iniciar servicio:

```cmd
net start SISFACT_BillingOne
```

Detener servicio:

```cmd
net stop SISFACT_BillingOne
```

Reiniciar servicio:

```cmd
net stop SISFACT_BillingOne
net start SISFACT_BillingOne
```

Eliminar servicio, si se requiere reinstalar:

```cmd
D:\tools\nssm\nssm.exe remove SISFACT_BillingOne confirm
```

---

## 10. Validación post-instalación

### 10.1 Validar proceso

```cmd
net start SISFACT_BillingOne
sc query SISFACT_BillingOne
```

### 10.2 Validar puerto

```cmd
netstat -ano | findstr :5060
```

### 10.3 Validar healthcheck

```text
http://localhost:5060/health
```

Respuesta esperada:

```json
{
  "app": "SIS-FACT / Billing One",
  "status": "ok"
}
```

### 10.4 Validar fuentes

```text
http://localhost:5060/api/v1/sources
http://localhost:5060/api/v1/sources/health
```

---

## 11. Convivencia con otros Flask

Si ATLAS u otra aplicación Flask ya está en el servidor, usar puertos distintos:

```text
ATLAS               5050
SIS-FACT            5060
Otra aplicación     5070
```

Cada aplicación debe tener:

- Carpeta propia.
- `.venv` propio.
- `config.ini` propio.
- Servicio Windows propio.
- Puerto propio.

---

## 12. Troubleshooting

### Error: puerto ocupado

Validar:

```cmd
netstat -ano | findstr :5060
```

Cambiar el puerto en `config.ini` o detener el proceso que lo utiliza.

### Error: no conecta Oracle

Validar:

- Oracle Instant Client instalado.
- Variables de entorno, si aplican.
- Host, puerto y service name.
- Usuario y clave.
- Acceso de red desde el servidor.

### Error: no conecta SQL Server

Validar:

- ODBC Driver instalado.
- Puerto 1433 o puerto definido.
- Driver configurado en `config.ini`.
- Usuario y clave.
- `trust_server_certificate` según política interna.

### Error: el servicio inicia y se detiene

Revisar:

```text
D:\sis-fact\logs\service_err.log
D:\sis-fact\logs\service_out.log
```

Probar primero ejecución manual con Waitress.

---

## 13. Checklist de instalación

```text
[ ] Repositorio clonado
[ ] Entorno virtual creado
[ ] Dependencias instaladas
[ ] config.ini creado localmente
[ ] SQL base ejecutado
[ ] Flask responde en modo desarrollo
[ ] Waitress responde manualmente
[ ] Servicio Windows instalado
[ ] Servicio Windows inicia correctamente
[ ] Healthcheck OK
[ ] Puerto habilitado en firewall
[ ] Logs configurados
```

---

## 14. Próximo paso funcional

Después de validar esta instalación, el siguiente desarrollo es crear el modelo de negocio:

```text
Empresa / RUT emisor
Negocio
Flujo
Ciclo o código
Período
Ejecución
Fases
BILLING_CASE
```
