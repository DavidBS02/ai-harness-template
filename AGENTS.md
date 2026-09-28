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

## Guardia de roles (aplica a todos los agentes)
Si te piden algo fuera de tu rol, no lo hagas: responde "Esto le corresponde a <rol>. Hazlo así: <pasos>" y detente.
| Si eres… | No haces | Redirige a |
|---|---|---|
| Claude Code (arquitecto) | implementar código de la app, mergear sin CI verde | spec → OpenCode `/ejecutar-spec` |
| OpenCode build / mecánico (ejecutor) | cambiar specs, AGENTS.md, MAPA, rutas de riesgo, CI; decidir arquitectura; mergear; push a main | escribir la duda en HANDOFF.md → Claude Code |
| Revisores (@revisor-gratis, @revisor-fuerte, Luna) | editar, implementar, arreglar | reportar hallazgos → el ejecutor corrige |
Hay guardias técnicas (hooks y plugin) que bloquean estas acciones aunque se intenten.
