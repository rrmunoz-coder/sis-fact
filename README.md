# SIS-FACT / Billing One

SIS-FACT es la plataforma independiente para control integral de facturación, integración de fuentes de datos, conciliación tributaria y reportería ejecutiva/operacional.

La plataforma queda separada de ATLAS/Altas, pero adopta la misma dinámica operativa base: Flask, Oracle local para autorización, LDAP para password corporativa, configuración externa y entrega limpia por rama `main`.

## Versión vigente única

- Versión: `v0.1.0`
- Estado: base técnica inicial consolidada
- Nombre funcional: `Billing One`
- Repositorio: `sis-fact`
- Ruta operativa usada en servidor: `K:\@@@@@sis-fact`

No se mantienen carpetas de parches como versión paralela. Todo cambio debe entrar como commit sobre `main` y quedar reflejado en documentación/SQL/código.

## Objetivo

Construir una plataforma que permita integrar y controlar el ciclo completo de facturación:

```text
Empresa / RUT emisor
  -> Negocio
  -> Flujo
  -> Ciclo o código
  -> Período
  -> Ejecución
  -> Fases
  -> Casos, documentos, controles, SII y caja
```

## Regla obligatoria de naming Oracle

Todas las tablas propias del sistema deben comenzar con:

```text
RM_CFACT_
```

Ejemplos:

```text
RM_CFACT_USER
RM_CFACT_DATA_SOURCE
RM_CFACT_EXTRACTION_RUN
RM_CFACT_INTEGRATION_CALL
RM_CFACT_AUDIT_LOG
RM_CFACT_AI_PROVIDER
```

No se deben crear tablas nuevas con prefijos `SIS_`, `BILLING_`, `BO_` u otros nombres propios del sistema sin el prefijo `RM_CFACT_`.

## Flujo de login estilo ATLAS

```text
Usuario autorizado / rol -> Oracle local, tabla RM_CFACT_USER
Password corporativa     -> LDAP
Sesión web               -> Flask session
```

- Crear usuario no consulta LDAP.
- El login acepta `usuario`, `dominio\usuario` o `usuario@dominio`.
- Para autorización local se normaliza a usuario sin dominio.
- Para LDAP se arma el bind según `[ldap] login_format`, normalmente UPN.
- La password LDAP nunca se guarda en Oracle.

## Alcance de esta versión

- Core Flask independiente.
- Configuración externa sin secretos versionados.
- Script único de ejecución local: `run_dev.cmd`.
- Login web `/login` y panel base `/app`.
- Healthcheck simple `/health` y healthcheck JSON `/api/v1/health`.
- Capa de integración para Oracle, SQL Server, REST, SOAP y archivos.
- Registro de fuentes de datos.
- Registro de extracciones.
- Diseño inicial de capa de analítica e IA.
- Scripts SQL base con prefijo `RM_CFACT_`.

## Estructura

```text
sis-fact/
├── sisfact/
│   ├── auth/                    login LDAP/local y usuarios
│   ├── core/                    configuración y Oracle
│   ├── integrations/            conectores y registro de fuentes
│   ├── analytics/               capa de analítica e IA
│   └── web/                     rutas web/API
├── sql/                         scripts Oracle iniciales
├── docs/                        documentación funcional/técnica
├── prompts/                     prompts de construcción
├── tests/                       pruebas base
├── releases/v0.1.0/             notas de versión
├── requirements.txt
├── config.ini.example
├── run_dev.cmd                  ejecución local Windows
├── wsgi.py
├── VERSION.md
├── CHANGELOG.md
└── MANIFEST.md
```

## Instalación rápida de desarrollo

```cmd
cd /d K:\@@@@@sis-fact
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy config.ini.example config.ini
run_dev.cmd
```

## SQL inicial

Ejecutar en este orden:

```text
sql/00_VALIDAR_AMBIENTE.sql
sql/01_CORE_INTEGRACION.sql
sql/02_SECURITY_USERS.sql
```

## Manuales

```text
docs/MANUAL_INSTALACION.md
docs/AUTENTICACION_LDAP.md
docs/NAMING_ORACLE.md
docs/ENTREGAS_Y_PARCHES.md
```

## Seguridad

No se versiona:

- `config.ini` real.
- Credenciales.
- `.venv` ni `.venv.venv`.
- ZIP descargados.
- Carpeta `sis-fact-main`.
- Logs.
- Cachés Python.
- Dumps de bases de datos.
- Archivos productivos con datos sensibles.
