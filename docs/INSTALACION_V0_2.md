# Instalación Billing One v0.2.1

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

Generar `secret_key`:

```cmd
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 4. Validación del paquete

```cmd
.venv\Scripts\python.exe scripts\validar_release.py
.venv\Scripts\python.exe scripts\validar_higiene.py
.venv\Scripts\python.exe -m compileall -q sisfact tests tools scripts *.py
.venv\Scripts\python.exe -m pytest tests -q
```

## 5. Oracle greenfield v0.2.1

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
90_VALIDAR_BILLING_ONE.sql
```

## 6. Migración desde la v0.2.0 ya instalada

No reinstalar seguridad. Aplicar únicamente:

```text
sql/migration_v0_2_0_to_v0_2_1/00_PRECHECK.sql
sql/migration_v0_2_0_to_v0_2_1/10_APPLY.sql
sql/migration_v0_2_0_to_v0_2_1/20_VALIDATE.sql
```

El precheck debe mostrar 0 filas en scopes, integraciones operativas, DOM y Ciclo antes de ejecutar `10_APPLY.sql`.

El parche no modifica usuarios, LDAP, roles, permisos ni `SISGAV2`.

## 7. Infraestructura

Oracle:

```cmd
.venv\Scripts\python.exe tools\test_oracle_connection.py
```

LDAP web:

```cmd
.venv\Scripts\python.exe tools\test_ldap_bind.py
```

## 8. Desarrollo

```cmd
run_dev.cmd
```

Probar:

```text
http://127.0.0.1:5040/health
http://127.0.0.1:5040/api/v1/health
http://127.0.0.1:5040/login
http://127.0.0.1:5040/app
```

## 9. Waitress

```cmd
.venv\Scripts\python.exe service_entry.py
```

## 10. Criterio técnico de cierre

- release/higiene/compile/pytest OK;
- validadores 11/21/31/41/90 OK;
- Oracle OK;
- LDAP bind SUCCESS;
- login web correcto;
- contexto muestra RUT → Negocio → Origen → Tipo → Flujo;
- `RM_CFACT_DOM` y `RM_CFACT_CYCLE` no existen;
- `SISGAV2` permanece intacta.
