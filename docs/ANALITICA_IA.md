# Analítica, reportería e IA

## Enfoque

La capa de analítica y reportería se construirá desacoplada de las fuentes. Debe consumir información normalizada o agregada.

La IA no será requisito para operar el sistema. Será una capa opcional para apoyar explicación, detección de patrones y generación de resúmenes.

## Modos posibles de IA

| Modo | Descripción |
|---|---|
| Disabled | Sin IA; solo reglas y métricas determinísticas |
| Local | Modelo encapsulado localmente en servidor autorizado |
| Private API | API corporativa privada |
| External API | Servicio externo sujeto a aprobación |

## Casos de uso candidatos

- Explicar variaciones de facturación.
- Resumir hallazgos de Billing Compare.
- Priorizar errores por monto, criticidad y recurrencia.
- Traducir errores técnicos a impacto financiero.
- Generar narrativa ejecutiva mensual.
- Detectar patrones de no emisión.
- Recomendar controles preventivos.

## Restricciones

- No enviar datos sensibles a modelos externos sin aprobación.
- No depender de IA para cálculos oficiales.
- Toda conclusión relevante debe mantener trazabilidad al dato fuente.
- La IA no reemplaza reglas de conciliación ni controles tributarios.

## Arquitectura conceptual

```text
Datos normalizados
  -> métricas determinísticas
  -> contexto resumido
  -> AIGateway
  -> explicación / priorización / narrativa
```

## Primer paso

Mantener `AIGateway` deshabilitado por defecto y construir primero KPI determinísticos.
