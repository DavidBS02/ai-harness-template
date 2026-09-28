# Instrucciones para agentes (fuente única: Claude Code, OpenCode, Codex)

## Proyecto
- Qué hace: <una línea>
- Stack: <lenguaje, framework, base de datos>
- Contrato de producto: `_bmad-output/.../SPEC.md` (CAP-*) · Arquitectura: `_bmad-output/.../ARCHITECTURE-SPINE.md` (AD-*)
- Verdad de lo construido: `openspec/specs/` · Contexto para la IA: `openspec/config.yaml` · Estado: `docs/ESTADO.md`

## Comandos
- Instalar: `<comando>`
- Tests: `<comando>`
- Lint / typecheck: `<comando>`
- Build: `<comando>`
- Publicar (lo que cambia lo que se sirve): `<comando>`

## Puntos de entrada y qué hace falta para que un cambio llegue
| Punto de entrada | ¿Basta subir el código? | Si no, qué más |
|---|---|---|
| <ej. job programado> | sí | — |
| <ej. web app / API desplegada> | no | <comando de deploy> |

## Método (resumen; detalle en .claude/rules/workflow-routing.md)
- BMAD planea y refina (solo en Claude Code, solo escribe en `_bmad-output/`). OpenSpec ejecuta por change.
- Rama por change: `feat/<issue>-<change-id>`. Triviales sin change: `fix/<slug>`.
- Cada `proposal.md` termina con `## Harness` (Issue, Riesgo, Zonas, OpenCode-zona-roja).

## Reglas de trabajo
- Trabaja SOLO en la rama y worktree que te indiquen. Nunca en `main`.
- Antes de implementar, lee `openspec/changes/<id>/` completo. Si el spec no alcanza, escribe la duda en HANDOFF.md y detente.
- Commits pequeños, un tema por commit, mensaje en imperativo explicando POR QUÉ.
- Corre los tests después de cada cambio. No afirmes que pasan sin correrlos.
- No toques: <carpetas sensibles, secretos, migraciones en producción>.
- Al cerrar la sesión ejecuta `/handoff`.

## Nunca entra al repo
<secretos, ids reales, datos personales, archivos del usuario>

## Guardia de roles (aplica a todos los agentes)
Si te piden algo fuera de tu rol, no lo hagas: responde "Esto le corresponde a <rol>. Hazlo así: <pasos>" y detente.
| Si eres… | No haces | Redirige a |
|---|---|---|
| Claude Code (arquitecto) | implementar código de la app; mergear sin CI verde | `/cambio` → OpenCode `/ejecutar-cambio` |
| Claude Code en una skill `bmad-*` | editar fuera de `_bmad-output/` (tampoco artefactos de un change) | entregar dossier + nombrar `/cambio` o `/opsx:update <id>` |
| OpenCode (ejecutor) | editar proposal/design/specs, `openspec/specs/`, `config.yaml`, `_bmad*`, reglas, CI; archivar; mergear; push a main | HANDOFF.md → Claude Code |
| Revisores | editar, implementar, arreglar | reportar hallazgos → el ejecutor corrige |
Hay guardias técnicas (hooks y plugin) que bloquean estas acciones aunque se intenten.

## Método de trabajo propio del equipo (opcional)
<!-- Definición de hecho, tamaño máximo de PR, convención de commits, ritmo. -->
