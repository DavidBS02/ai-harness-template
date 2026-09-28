# Instrucciones para agentes (fuente única: Claude Code, OpenCode, Codex)

## Proyecto
- Qué hace: <una línea>
- Stack: <lenguaje, framework, base de datos>
- Contrato de producto: `_bmad-output/.../SPEC.md` (CAP-*) · Arquitectura: `_bmad-output/.../ARCHITECTURE-SPINE.md` (AD-*)
- Verdad de lo construido: `openspec/specs/` · Contexto para la IA: `openspec/config.yaml` · Estado (generado): `docs/ESTADO.md`
- Datos del harness (zonas, permisos, modelos, rutas por skill): `harness.json` → tabla legible en `docs/harness/RUTAS.md`

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
- BMAD planea y refina (solo escribe en `_bmad-output/`). OpenSpec ejecuta por change. Cada skill tiene su herramienta: `python3 scripts/harness.py ruta <skill>`.
- Niveles de ceremonia 0–3 (`docs/harness/RUTAS.md`). Ramas: `fix/<slug>` (0), `feat/<id>` (1), `feat/<n>-<id>` (2–3).
- Cada `proposal.md` termina con `## Harness` (Issue, Nivel, Riesgo, Zonas, OpenCode-zona-roja).
- Si el proyecto tiene un solo entorno de producción: se despliega solo desde main, uno a la vez, con respaldo previo si toca datos.

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
| Claude Code en una skill `bmad-*` | editar fuera de `_bmad-output/`; correr skills de recolectar/revisar (van a OpenCode) | entregar dossier + nombrar `/cambio` o `/opsx:update <id>` |
| OpenCode (ejecutor) | editar proposal/design/specs, `openspec/specs/`, `config.yaml`, `_bmad*` (salvo `_bmad-output/digests/`), reglas, CI, `harness.json`; correr skills de decidir/redactar; archivar; mergear; push a main | HANDOFF.md → Claude Code |
| Revisores | editar, implementar, arreglar | reportar hallazgos → el ejecutor corrige |
| Cualquiera | usar una skill que no está en `harness.json` | `/clasificar-skill <nombre>` en Claude Code |
Hay guardias técnicas (hooks y plugin) que bloquean estas acciones aunque se intenten.

## Método de trabajo propio del equipo (opcional)
<!-- Definición de hecho, tamaño máximo de PR, convención de commits, ritmo. -->
