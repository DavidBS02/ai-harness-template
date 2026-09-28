# Workflow routing — cómo enrutar CADA pedido

**Siempre relevante.** Aplícala antes de hacer nada. El estado del proyecto NO vive aquí (vive en `docs/ESTADO.md`) para que esta regla siga siendo corta.

## Tres ejes que no se mezclan
1. **Método:** BMAD planea y refina · OpenSpec ejecuta por change (`propose → apply → archive`).
2. **Herramientas:** Claude Code = arquitecto · OpenCode = ejecutor · revisores (OmniRoute y Luna) = solo lectura.
3. **GitHub:** issue → rama `feat/<issue>-<change-id>` → PR → CI + etiqueta de riesgo → merge por `/juzgar-pr`.

## Árbol de decisión
1. **¿Research, ideación, producto, PRD, UX, arquitectura, cambiar un AD o dividir en épicas?** → **BMAD** en Claude Code (skill `bmad-*`, empieza por `bmad-help`). Termina con un dossier y el comando OpenSpec que lo aplica.
2. **¿Feature, fix, refactor o ajuste concreto?** → **OpenSpec** vía `/cambio "<idea>"` en Claude Code (envuelve `/opsx:propose` + issue + rama + worktree). Lo implementa OpenCode con `/ejecutar-cambio <change-id>`.
3. **¿Iniciativa grande?** → **BMAD primero** (spec + spine) → **un change de OpenSpec por pieza**.
4. **¿Trivial?** (riesgo bajo según `scripts/riesgo.sh` y ≤ 20 líneas) → sin change: OpenCode `@mecanico` en rama `fix/<slug>`, PR directo. La ceremonia tiene que pagar su costo.
5. **¿Ambiguo?** → **pregunta** una aclaración corta. No adivines el enrutamiento.

## BMAD no ejecuta NADA (regla dura)
BMAD produce entendimiento: hallazgos, decisiones, matrices, cortes de alcance. Su entregable es un **dossier**, no un diff.
- NO escribe código, config ni infra. NO crea ramas, commits ni PRs. NO marca tareas. NO aplica sus propias recomendaciones, ni siquiera sobre los artefactos de un change.
- Solo escribe en `_bmad-output/` (y en las reglas del harness cuando el usuario pide iterarlo).
- **Handoff:** toda sesión BMAD termina nombrando el comando que la aplica (`/cambio`, `/opsx:update <id>`).
- Señal de que cruzaste la línea: dentro de una skill `bmad-*` te descubres usando Edit/Write/git fuera de `_bmad-output/`. Para.

## Quién corre qué de OpenSpec
| Comando | Quién | Por qué |
|---|---|---|
| `/opsx:explore`, `/opsx:propose` (vía `/cambio`), `/opsx:update` | Claude Code | Definir el cambio es arquitectura |
| `/opsx-apply` (vía `/ejecutar-cambio`) | OpenCode | Implementar es volumen; marca `tasks.md` |
| `/opsx:sync`, `/opsx:archive` (dentro de `/juzgar-pr`) | Claude Code | Publicar a `openspec/specs/` es decidir qué es verdad |

## Fuentes de verdad (una por tipo)
- Intención de producto y arquitectura: `_bmad-output/` (SPEC con CAP-*, spine con AD-*). Cambiar un AD pasa por `bmad-architecture`, nunca por un change.
- Lo construido: `openspec/specs/`. El contexto que lee la IA: `openspec/config.yaml`.
- Estado, verificaciones diferidas y deudas: `docs/ESTADO.md`. **Una deuda se da por abierta solo tras abrir su archivo dueño.**
- Reglas del repo: `AGENTS.md`. Mapa y zonas: `docs/harness/MAPA.md`.

## El harness es vivo
Si encuentras una mejora en la forma de trabajo, itera el harness (esta regla, `docs/harness-guide.md`, `openspec/config.yaml`, `docs/LECCIONES.md`), no la apliques solo una vez.
