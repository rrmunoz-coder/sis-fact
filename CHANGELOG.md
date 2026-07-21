# Changelog

## v0.1.0 - 2026-07-21

### Incluye

- Inicialización del repositorio `sis-fact`.
- Base independiente para SIS-FACT / Billing One.
- Core Flask separado de ATLAS/Altas.
- Configuración externa mediante `config.ini`.
- Capa de integración para orígenes de datos.
- Conectores base para Oracle, SQL Server, REST, SOAP y archivos.
- Registro conceptual de fuentes, extracciones y llamadas de integración.
- Documentación de arquitectura, integración, analítica e IA.
- SQL inicial para tablas de integración y auditoría.

### Decisiones

- ATLAS y SIS-FACT se mantienen como sistemas separados.
- SIS-FACT podrá integrarse a ATLAS posteriormente para cruzar impacto financiero versus esfuerzo operativo.
- La analítica e IA se diseñan como capa desacoplada para permitir solución local, encapsulada o externa.

### Pendiente

- Incorporar login corporativo definitivo.
- Definir tablas productivas de Oracle y SQL Server.
- Crear módulos de flujos, ciclos, ejecuciones y fases.
- Implementar dashboard operacional y directivo.
- Implementar integración real con Billing Compare, facturador electrónico, SII/RCV y F29.
