# Prompt de construcción SIS-FACT / Billing One v0.1.0

Actúa como arquitecto senior y desarrollador full-stack para construir SIS-FACT / Billing One, sistema independiente para control integral de facturación, integración de fuentes, conciliación tributaria y reportería ejecutiva/operacional.

## Decisiones base

- SIS-FACT es sistema separado de ATLAS/Altas.
- Se puede reutilizar filosofía técnica, pero no depender de su producción.
- Plataforma inicial: Flask + Oracle + SQL Server + conectores REST/SOAP/archivos.
- Configuración externa sin secretos versionados.
- Versionado semántico y estructura limpia.

## Objetivo funcional

Representar el ciclo de facturación completo:

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

## Reglas técnicas

- No hardcodear flujos, fases, fuentes ni reglas de negocio.
- No versionar credenciales.
- Mantener conectores desacoplados.
- Oracle será repositorio central inicial de SIS-FACT.
- SQL Server se consume mediante ODBC.
- SOAP y REST se tratan como fuentes configurables.
- La IA será opcional y encapsulada detrás de un gateway.

## Primer alcance

- Core Flask.
- Registro de fuentes.
- Healthcheck.
- DDL de integración.
- Conectores base.
- Documentación y roadmap.
