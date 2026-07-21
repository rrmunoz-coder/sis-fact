# SIS-FACT / Billing One

SIS-FACT es la plataforma independiente para control integral de facturación, integración de fuentes de datos, conciliación tributaria y reportería ejecutiva/operacional.

La plataforma nace separada de ATLAS/Altas para no depender de su paso a producción, pero conserva una filosofía técnica similar: Flask, Oracle, configuración externa, versionado limpio y separación por capas.

## Versión vigente

- Versión: `v0.1.0`
- Estado: base técnica inicial
- Nombre funcional: `Billing One`
- Nombre de repositorio: `sis-fact`

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

## Alcance de esta versión

- Core Flask independiente.
- Configuración externa sin secretos versionados.
- Capa de integración para múltiples orígenes de datos.
- Conectores base para Oracle, SQL Server, REST, SOAP y archivos.
- Registro de fuentes de datos.
- Registro de extracciones.
- Healthcheck de plataforma.
- Login LDAP estilo Altas con autorización local en Oracle.
- Diseño inicial de capa de analítica e IA.
- Scripts SQL base.
- Documentación técnica inicial.
- Manual de instalación con ejecución como servicio Windows.

## Estructura

```text
sis-fact/
├── sisfact/                     código Flask
│   ├── auth/                    login LDAP/local y usuarios
│   ├── core/                    configuración, seguridad, base común
│   ├── integrations/            conectores y registro de fuentes
│   ├── analytics/               capa de analítica e IA
│   └── web/                     rutas y vistas
├── sql/                         scripts Oracle iniciales
├── docs/                        documentación funcional y técnica
├── prompts/                     prompts de construcción
├── tests/                       pruebas base
├── releases/v0.1.0/             notas de versión
├── requirements.txt             dependencias Python
├── config.ini.example           configuración ejemplo sin secretos
├── run_dev.cmd                  ejecución local Windows
├── wsgi.py                      entrada WSGI
├── VERSION.md
├── CHANGELOG.md
└── MANIFEST.md
```

## Decisión arquitectónica

ATLAS y SIS-FACT serán sistemas separados.

- ATLAS: tiempo, capacidad, proyectos, tareas, costos y esfuerzo operativo.
- SIS-FACT / Billing One: facturación, ciclos, emisión, foliación, SII, NC, pagos, controles y caja.

La integración futura entre ambos se realizará por una capa analítica común, no por fusión funcional.

## Seguridad

No se versiona:

- `config.ini` real.
- Credenciales.
- `.venv`.
- Logs.
- Cachés Python.
- Dumps de bases de datos.
- Archivos productivos con datos sensibles.

## Instalación rápida de desarrollo

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config.ini.example config.ini
python -m flask --app wsgi:app run --host 0.0.0.0 --port 5060 --debug
```

## Manuales

```text
docs/MANUAL_INSTALACION.md
docs/AUTENTICACION_LDAP.md
docs/NAMING_ORACLE.md
```

El manual de instalación incluye:

- Instalación en desarrollo.
- Instalación en servidor Windows.
- Configuración de Oracle y SQL Server.
- Configuración LDAP compatible con Altas.
- Ejecución con Flask.
- Ejecución productiva con Waitress.
- Instalación como servicio Windows con NSSM.
- Validación de healthcheck.
- Convivencia con ATLAS u otros Flask usando puertos distintos.

## Login LDAP

SIS-FACT usa autorización local y autenticación corporativa:

```text
Usuario autorizado / rol -> Oracle local, tabla RM_CFACT_USER
Password corporativa     -> LDAP
Sesión web               -> Flask session
```

Crear usuario no consulta LDAP. El usuario se crea en Oracle y, al ingresar a `/login`, SIS-FACT valida la password contra LDAP si `AUTH_TYPE = LDAP`.
