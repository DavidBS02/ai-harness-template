# Instrucciones para agentes (fuente única: Claude Code, OpenCode, Codex)

## Proyecto
- Qué hace: <una línea>
- Stack: <lenguaje, framework, base de datos>

## Comandos
- Instalar: `<comando>`
- Tests: `<comando>`
- Lint: `<comando>`
- Build: `<comando>`

## Reglas de trabajo
- Trabaja SOLO en la rama y worktree que te indiquen. Nunca en `main`.
- Antes de implementar, lee `docs/specs/<issue>-<slug>.md`. Si el spec no alcanza, escribe la duda en HANDOFF.md y detente.
- Commits pequeños, un tema por commit, mensaje en imperativo explicando POR QUÉ.
- Corre los tests después de cada cambio. No afirmes que pasan sin correrlos.
- No toques: <carpetas sensibles, secretos, migraciones en producción>.
- Al cerrar la sesión ejecuta `/handoff`.

## Roles (no te salgas del tuyo)
- Claude Code: specs, arquitectura, revisión final, merge.
- OpenCode: implementación según spec, tests, PR.
- Revisores (@revisor-gratis, /codex:review): solo reportan hallazgos, no editan.

## Método de trabajo
<!-- Conecta aquí tu framework: ver docs/INTEGRACION-FRAMEWORK.md -->
- Definición de hecho: <tu lista>
- Tamaño máximo de PR: <n> archivos / <m> líneas
- Convención de commits: <la tuya>
