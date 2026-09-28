# Harness guide — método (BMAD + OpenSpec) × herramientas × GitHub

Guía maestra. La regla corta que se carga siempre es `.claude/rules/workflow-routing.md`; esta es la versión completa. Las lecciones con su origen están en `docs/LECCIONES.md`.

---

## 1. El modelo en una tabla

Hay tres ejes independientes. Cada pedido pasa por los tres:

| Eje | Qué decide | Dueño |
|---|---|---|
| **Método** | *Qué* se hace y en qué artefacto queda | BMAD planea · OpenSpec ejecuta |
| **Herramienta / modelo** | *Quién* lo hace y con qué modelo | Claude Code arquitecto · OpenCode ejecutor · revisores de otra familia |
| **GitHub** | *Cómo* viaja y cuándo es verdad | issue → rama → PR → CI → merge |

## 2. Matriz maestra: fase × framework × herramienta × modelo × GitHub

| Fase | Framework / comando | Herramienta | Modelo | Escribe en | GitHub |
|---|---|---|---|---|---|
| 0. Descubrimiento | `/descubrir` (+ `bmad-deep-recon` / `bmad-project-context` en brownfield) | Claude Code (+ OpenCode para resúmenes) | Claude · DeepSeek Flash / Kimi K3 | `docs/harness/`, `.harness/` | rama `chore/harness-descubrimiento` + PR |
| 1. Idea y producto | `bmad-help` → `bmad-forge-idea` / `bmad-product-brief` → `bmad-prd` / `bmad-spec` | Claude Code | Claude | `_bmad-output/` | — (o PR `docs/…` si se versiona) |
| 2. Arquitectura | `bmad-architecture` (+ reviews adversariales BMAD) | Claude Code | Claude | `_bmad-output/planning-artifacts/` | — |
| 3. Handoff | primer change siembra `openspec/config.yaml` | Claude Code | Claude | `openspec/config.yaml`, `AGENTS.md` | parte del primer PR |
| 4. Proponer | `/cambio` → `/opsx:propose` (+ `/opsx:explore` si hace falta) | Claude Code | Claude | `openspec/changes/<id>/` | issue + rama `feat/<issue>-<id>` + PR draft |
| 4b. Atacar el plan | `/codex:adversarial-review` (riesgo medio/alto) | Claude Code + Codex | GPT-6 Luna (Free) | comentario | comentario en el PR |
| 5. Ejecutar | `/ejecutar-cambio <id>` → `/opsx-apply` | OpenCode (worktree) | GLM-5.3 · GLM-5.3-Flash · DeepSeek V4.1 Flash · Kimi K3 | código + `tasks.md` | commits en la rama |
| 6. Revisar | `@revisor-gratis` (siempre) · `@revisor-fuerte` (medio/alto, lentes de `bmad-code-review`) · `/codex:review` (alto) | OpenCode · Claude Code + Codex | combo OmniRoute · DeepSeek V4 · GPT-6 Luna | comentarios | PR + etiqueta `riesgo:*` + check `verificar` |
| 7. Corregir el spec | `/opsx:update <id>` | Claude Code | Claude | artefactos del change | commit en la rama |
| 8. Juzgar y archivar | `/juzgar-pr` → checklist → `/opsx:archive` | Claude Code | Claude | `openspec/specs/`, `docs/ESTADO.md` | squash merge |
| 9. Reconciliar | `/opsx:sync`; `bmad-correct-course` si el rumbo cambió | Claude Code | Claude | specs / dossier | PR `chore/…` |

## 3. Árbol de decisión por pedido

1. **Research, producto, PRD, UX, arquitectura, cambiar un AD, dividir en épicas** → BMAD (Claude Code). Termina con dossier + comando OpenSpec que lo aplica.
2. **Feature, fix, refactor o ajuste concreto** → `/cambio` (Claude Code) y `/ejecutar-cambio` (OpenCode).
3. **Iniciativa grande** → BMAD primero → un change por pieza.
4. **Trivial** (riesgo bajo y ≤ 20 líneas) → sin change: OpenCode `@mecanico` en `fix/<slug>`.
5. **Ambiguo** → pregunta.

**Ceremonia proporcional:** el ciclo completo es para cambios con valor real. Un fix de una línea no necesita propuesta, pero sí pasa por rama, PR y CI.

## 4. BMAD: qué hace, quién lo corre, dónde escribe

- **Herramienta:** siempre Claude Code. BMAD es juicio, y sus skills son largas: correrlas con un modelo débil produce artefactos pobres.
- **Instalación:** `scripts/instalar-frameworks.sh` (`core` + `bmm`, español, `output_folder: _bmad-output`, herramientas `claude-code`, `codex` y `opencode` si el instalador la ofrece). Las skills quedan en `.claude/skills/` y en `.agents/skills/`, que es el espejo neutral para otras herramientas.
- **Punto de entrada:** `bmad-help` recomienda el siguiente paso.
- **Salida:** solo `_bmad-output/` (`planning-artifacts/`, `specs/`, `forge/`, `reviews/`). Versiona los artefactos de **contrato** (SPEC, spine); los borradores pueden ignorarse (`docs/LECCIONES.md` §9).
- **Regla dura:** BMAD no ejecuta nada (ver `workflow-routing.md`). El guardia de Claude permite editar `_bmad-output/` y bloquea código; la separación entre BMAD y OpenSpec *dentro* de Claude es una regla de instrucción, no un bloqueo técnico.
- **Cambiar un AD o una CAP** pasa por `bmad-architecture` o `bmad-spec`, nunca por un change.

## 5. Handoff BMAD → OpenSpec

- Se hace **una vez por pieza**: la épica o historia de BMAD se traduce a un change de OpenSpec. Desde ahí, `openspec/specs/` es la verdad de lo construido y los artefactos BMAD quedan como intención (no se implementa directo desde historias BMAD).
- El **primer change de producto siembra** `openspec/config.yaml` (`context`: producto, stack, capas, AD-*, convenciones, "nunca entra al repo") y `AGENTS.md`. Verificación: `npx openspec validate --all` y que `npx openspec instructions proposal` devuelva el contexto nuevo.
- Cuando un change cambia stack, capas o convenciones, actualiza `openspec/config.yaml` **en la misma tarea**.

## 6. OpenSpec con el harness

- **Versión fijada** (devDependency en proyectos Node): el comportamiento de `validate` y `archive` es contrato de trabajo y no cambia sin decidirlo.
- **Ciclo:** `/cambio` (propose) → ajustar (`/opsx:update`) → `/ejecutar-cambio` (apply) → revisar → **verificar contra la realidad** → `/juzgar-pr` (archive + merge).
- **Sección `## Harness` en cada `proposal.md`** (la pide `openspec/config.yaml`): `Issue`, `Riesgo`, `Zonas`, `OpenCode-zona-roja`. Es lo que leen `riesgo.sh`, los git hooks, el plugin de OpenCode y la Action `proceso`.
- **Quién toca qué del change:** Claude escribe `proposal.md`, `design.md` y `specs/`; OpenCode escribe código y marca `tasks.md`. Las guardias lo imponen.
- **Archive dentro del PR, antes del merge,** cuando la verificación se puede hacer en la rama. Si la verificación exige producción: merge → verificar → PR `chore/archive-<id>` con el archive. Las verificaciones que dependen del futuro se registran en `docs/ESTADO.md`; si fallan, **no se desarchiva**: se abre un change nuevo.

## 7. Flujo por cambio (paso a paso)

```
Claude Code   /cambio "<idea>"
              → gh issue create · rama feat/<n>-<id> · worktree ../wt-<id>
              → /opsx:propose <id> (con ## Harness) · validate · commit · push · PR draft
              → riesgo medio/alto: /codex:adversarial-review sobre proposal + design
OpenCode      cd ../wt-<id> && scripts/ejec → /ejecutar-cambio <id>
              → /opsx-apply · tests por tarea · marca tasks.md · commits pequeños
              → scripts/riesgo.sh · @revisor-gratis · (@revisor-fuerte) · /handoff · gh pr ready
GitHub        ci (test) · riesgo (etiqueta) · proceso (change + issue + revisiones según riesgo)
Claude Code   /juzgar-pr <n>
              → CI · revisiones · (Luna si alto) · checklist de archive · /opsx:archive · docs/ESTADO.md
              → merge squash · git worktree remove
```

Si `/juzgar-pr` devuelve trabajo, OpenCode repite el paso 5 en la misma rama. Máximo dos vueltas; a la tercera, el arquitecto decide (`/opsx:update`, o implementa con override).

## 8. Riesgo y revisión

| Revisor | Modelo | Pregunta | Cuándo |
|---|---|---|---|
| `@revisor-gratis` | combo OmniRoute (DeepSeek V4 → Mistral Large → Gemini Flash) | ¿Cumple los specs y las tareas del change? | Siempre |
| `@revisor-fuerte` | DeepSeek V4 fijo, lentes adversarial y edge-case de `bmad-code-review` | ¿Cómo rompo esto? | Riesgo medio o alto |
| `/codex:review` | GPT-6 Luna (ChatGPT Free) | Segunda opinión adversarial de otra familia | Riesgo alto, crítico dudoso o segunda vuelta |

Riesgo final = el **más alto** entre `scripts/riesgo.sh` (rutas de `.harness/rutas-alto.txt` y tamaño), el `Riesgo:` del proposal y la etiqueta de la Action.

## 9. Modelos por agente de OpenCode

| Agente | Modelo | Uso |
|---|---|---|
| `build` | `opencode-go/glm-5.3` | Implementar el change |
| `@mecanico` | `opencode-go/glm-5.3-flash` | Tests, docs, renombres, triviales |
| `@explorador` / `small_model` | `opencode-go/deepseek-v4.1-flash` | Leer, buscar, resúmenes |
| `contexto-largo` | `opencode-go/kimi-k3` | Repos o módulos enteros (caro) |

Un modelo por sesión; para cambiar, primero `/compact`.

## 10. Guardias (qué se bloquea de verdad)

| Capa | Bloquea |
|---|---|
| Instrucciones (CLAUDE.md, AGENTS.md, esta regla) | Cada agente rechaza lo que no es suyo y redirige. BMAD no ejecuta. |
| Hook de Claude Code | Editar código de la app (Claude solo toca `docs/`, `_bmad-output/`, `openspec/`, config del harness). |
| Plugin de OpenCode | Editar `proposal.md`, `design.md`, `specs/`, `openspec/specs/`, `config.yaml`, `_bmad*`, reglas y CI; zona roja sin `OpenCode-zona-roja: autorizado`; `openspec archive`; `gh pr merge`; push a main. |
| Revisores | Editar cualquier cosa (`edit: deny`). |
| Git hooks | Commitear fuera del rol, push a main. |
| GitHub (`proceso.yml` + protección) | Mergear sin change, sin issue o sin las revisiones del riesgo. |

Override consciente: `HARNESS_OVERRIDE=1 scripts/arq` o `scripts/ejec`; queda como `Harness-Override: yes` en el commit.

## 11. Contexto compartido

- `AGENTS.md`: reglas del repo, que leen todas las herramientas. `CLAUDE.md` lo importa junto con la regla de routing.
- `openspec/config.yaml`: contexto que lee la IA al generar artefactos.
- `openspec/changes/<id>/`: el contrato del cambio en curso. `HANDOFF.md`: el estado vivo de la rama.
- `docs/ESTADO.md`: estado del proyecto, verificaciones diferidas, deudas y decisiones vigentes del usuario.
- `docs/harness/MAPA.md` y `DELEGACION.md`: zonas y a quién va cada tipo de tarea.
- Nada del historial de chat se copia entre herramientas.

## 12. Qué NO hace cada uno

- **Claude Code** no implementa features (salvo override), no mergea sin CI verde y no afirma que los tests pasan.
- **BMAD** (dentro de Claude) no edita nada fuera de `_bmad-output/`, ni siquiera los artefactos de un change.
- **OpenCode** no propone ni archiva, no edita proposal/design/specs y no cambia la arquitectura. Si falta algo en el spec, lo escribe en HANDOFF.md y se detiene.
- **Los revisores** solo reportan.
- **CI** es la única voz que dice que los tests pasan.

## 13. Instalación y cuándo cambiar el setup

Pasos en `docs/ONBOARDING.md`. Umbrales para cambiar:
- Llegas al límite de Claude Pro 3 o más veces por semana → Max 5x, o baja la ceremonia BMAD a lo necesario.
- Llegas al límite de Go a diario → GLM Coding Plan Lite o Go + Lite.
- Luna se queda corto seguido → ChatGPT Go o Plus.
- Un proveedor de OmniRoute cambia sus términos → quítalo.

## 14. Privacidad

Código de clientes o con datos personales: solo Claude Code (Pro), OpenCode Go (proveedores sin retención) y CI. No uses capas gratuitas con ese código. Tampoco pongas cifras reales ni datos personales en reglas o estado versionados.

## 15. El harness es vivo

Si encuentras una mejora a la forma de trabajo, itera: `workflow-routing.md`, esta guía, `openspec/config.yaml`, `docs/LECCIONES.md` y `AGENTS.md`, y súbela al repo base para que la hereden todos los proyectos.
