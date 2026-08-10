# Instalación Billing One v0.2.0

## Importante

Este manual distingue entre **greenfield** y la instalación v0.1 existente.

No ejecutar los DDL greenfield sobre el Oracle actual hasta cerrar `docs/MIGRACION_V0_1_V0_2.md`.

## 1. Ruta

```text
K:\@@@@@sis-fact
```

No usar `sis-fact-main`, ZIP, `.venv.venv` ni scripts locales alternativos.

## 2. Python

Se recomienda Python 3.12 x64, alineado con el runtime ATLAS validado.

```cmd
cd /d K:\@@@@@sis-fact
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Configuración

```cmd
copy config.ini.example config.ini
.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Completar `config.ini` real. No subirlo a GitHub.

Validar secciones sin mostrar passwords:

```cmd
.venv\Scripts\python.exe -c "import configparser; p=configparser.ConfigParser(); p.read('config.ini',encoding='utf-8'); print(p.sections())"
```

Esperado como mínimo:

```text
flask
security
oracle
ldap
```

## 4. Validación del paquete

```cmd
.venv\Scripts\python.exe scripts\validar_release.py
.venv\Scripts\python.exe scripts\validar_higiene.py
.venv\Scripts\python.exe -m compileall -q sisfact tests tools scripts *.py
.venv\Scripts\python.exe -m pytest -q
```

## 5. Oracle greenfield

Solo en esquema nuevo o después de una migración v0.1 autorizada:

```text
00_DIAGNOSTICO_PREVIO.sql
10_SECURITY_BASE.sql
11_VALIDAR_SECURITY.sql
12_BOOTSTRAP_ADMIN.sql
20_CONTEXT_BASE.sql
21_VALIDAR_CONTEXT.sql
30_INTEGRATION_BASE.sql
31_VALIDAR_INTEGRATION.sql
90_VALIDAR_BILLING_ONE.sql
```

En DBeaver usar **Execute SQL Script** cuando el archivo contiene `/` de cierre PL/SQL.

## 6. Primer ADMIN

Editar una copia local de `12_BOOTSTRAP_ADMIN.sql` y reemplazar usuario, nombre y correo. El script no contiene password LDAP.

## 7. Pruebas de infraestructura

```cmd
.venv\Scripts\python.exe tools\test_oracle_connection.py
.venv\Scripts\python.exe tools\test_ldap_bind.py
```

La prueba LDAP usa `getpass`.

## 8. Desarrollo

```cmd
run_dev.cmd
```

Probar:

```text
http://127.0.0.1:5060/health
http://127.0.0.1:5060/api/v1/health
http://127.0.0.1:5060/login
```

Después del login:

```text
http://127.0.0.1:5060/app
http://127.0.0.1:5060/me
```

## 9. Waitress

```cmd
.venv\Scripts\python.exe service_entry.py
```

La instalación NSSM como servicio se cerrará al final de la estabilización del runtime v0.2.0.

## 10. Criterio técnico de cierre

- release/higiene/compile/pytest OK;
- `90_VALIDAR_BILLING_ONE.sql` sin revisiones estructurales;
- Oracle OK;
- LDAP bind real SUCCESS;
- `/health` y `/login` OK;
- login web correcto;
- `/app` visible;
- mantenedor de usuarios accesible con `USER_MANAGE`;
- sin errores críticos en `logs/billing_one.log`.
