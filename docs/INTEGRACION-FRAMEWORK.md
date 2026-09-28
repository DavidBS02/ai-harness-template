# Integrar tu framework de trabajo con este harness

Este harness solo define CÓMO usar los copilotos. Tu framework define CÓMO trabaja el equipo (sprints, definición de listo/hecho, ceremonias, estimación, etc.). Se conectan en cuatro puntos:

| Punto de contacto | Dónde | Qué haces |
|---|---|---|
| Reglas del método | `AGENTS.md` → sección `## Método de trabajo` | Escribe ahí (o importa con `@docs/metodo.md`) las reglas que un agente debe respetar: definición de hecho, convención de commits, tamaño máximo de PR, etc. |
| Entrada de trabajo | `.github/ISSUE_TEMPLATE/feature.md` | Añade los campos de tu framework (prioridad, épica, estimación). `/spec` los leerá del issue. |
| Definición de hecho | `.github/PULL_REQUEST_TEMPLATE.md` | Añade tu checklist de "hecho" debajo de las revisiones. `/juzgar-pr` no mergea si falta algo. |
| Ritmo | Tu calendario | El harness es por feature; tu framework decide cuántas features entran por ciclo y en qué orden. |

Regla de precedencia: si tu framework y este harness chocan, gana tu framework en TODO lo que sea forma de trabajo, y gana el harness en TODO lo que sea seguridad de cuentas y routing de modelos (sección "Reglas que no se negocian" del README).

Plantilla para la sección en AGENTS.md:
```
## Método de trabajo
@docs/metodo.md
- Definición de hecho: <tu lista>
- Tamaño máximo de PR: <n> archivos / <m> líneas (si es mayor, dividir el spec)
- Convención de commits: <conventional commits / la tuya>
```
