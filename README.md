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

## Alcance de esta versión

- Core Flask independiente.
- Configuración externa sin secretos versionados.
- Capa de integración para múltiples orígenes de datos.
- Conectores base para Oracle, SQL Server, REST, SOAP y archivos.
- Registro de fuentes de datos.
- Registro de extracciones.
- Healthcheck de plataforma.
- Diseño inicial de capa de analítica e IA.
- Scripts SQL base.
- Documentación técnica inicial.

## Estructura

```text
sis-fact/
├── sisfact/                     código Flask
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
