# Instalación Billing One v0.2.4

## 1. Ruta

```text
K:\@@@@@sis-fact
```

Mantener una sola versión activa. El `config.ini` real no se versiona.

## 2. Python

Se recomienda Python 3.12 x64.

```cmd
cd /d K:\@@@@@sis-fact
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Configuración

Puerto web vigente: `5040`.

```ini
[flask]
host = 0.0.0.0
port = 5040
```

## 4. Validación del paquete

```cmd
.venv\Scripts\python.exe scripts\validar_release.py
.venv\Scripts\python.exe scripts\validar_higiene.py
.venv\Scripts\python.exe -m compileall -q sisfact tests tools scripts *.py
.venv\Scripts\python.exe -m pytest tests -q
```

## 5. Oracle greenfield v0.2.4

```text
10_SECURITY_BASE.sql
11_VALIDAR_SECURITY.sql
12_BOOTSTRAP_ADMIN.sql
20_CONTEXT_BASE.sql
21_VALIDAR_CONTEXT.sql
30_INTEGRATION_BASE.sql
31_VALIDAR_INTEGRATION.sql
40_OPERATIONAL_BASE.sql
41_VALIDAR_OPERATIONAL.sql
50_EXECUTION_BASE.sql
51_VALIDAR_EXECUTION.sql
90_VALIDAR_BILLING_ONE.sql
```

## 6. Migraciones

Si la base sigue en v0.2.0, primero aplicar la corrección funcional:

```text
sql/migration_v0_2_0_to_v0_2_1/00_PRECHECK.sql
sql/migration_v0_2_0_to_v0_2_1/10_APPLY.sql
sql/migration_v0_2_0_to_v0_2_1/20_VALIDATE.sql
```

Luego aplicar control de ejecución:

```text
sql/migration_v0_2_3_to_v0_2_4/00_PRECHECK.sql
sql/migration_v0_2_3_to_v0_2_4/10_APPLY.sql
sql/migration_v0_2_3_to_v0_2_4/20_VALIDATE.sql
```

El parche v0.2.4 crea `RM_CFACT_EXECUTION_POLICY` y `RM_CFACT_EXECUTION_QUEUE`, y agrega SGA/DHT si faltan. No modifica usuarios, LDAP, roles/permisos ni `SISGAV2`.

## 7. Infraestructura

```cmd
.venv\Scripts\python.exe tools\test_oracle_connection.py
.venv\Scripts\python.exe tools\test_ldap_bind.py
```

## 8. Web

```cmd
run_dev.cmd
```

Probar:

```text
http://127.0.0.1:5040/health
http://127.0.0.1:5040/login
http://127.0.0.1:5040/app
http://127.0.0.1:5040/operacion/ejecuciones
```

## 9. Scheduler y Worker

Primero probar en consolas separadas:

```cmd
.venv\Scripts\python.exe scheduler_entry.py
```

```cmd
.venv\Scripts\python.exe worker_entry.py
```

El scheduler solo crea cola. El worker ejecuta la adquisición.

Después de validar pueden instalarse con NSSM:

```text
service/install_service.cmd
service/install_scheduler.cmd
service/install_worker.cmd
```

Servicios esperados:

```text
BillingOne_Web
BillingOne_Scheduler
BillingOne_Worker
```

## 10. Criterio técnico de cierre

- release/higiene/compile/pytest OK;
- validadores 11/21/31/41/51/90 OK;
- Oracle OK;
- LDAP bind SUCCESS;
- login web correcto;
- `Ejecuciones` visible según permisos;
- una ejecución MANUAL pasa PENDING → RUNNING → SUCCESS/WARNING/ERROR;
- scheduler encola una política SCHEDULED de prueba;
- `SISGAV2` permanece intacta.
