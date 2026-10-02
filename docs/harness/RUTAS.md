# Rutas del harness

<!-- GENERADO por scripts/harness.py sync — no editar a mano; edita harness.json -->

Cada skill de BMAD y OpenSpec pertenece a una clase; la clase decide herramienta y modelo. Las guardias bloquean correr una skill en la herramienta equivocada. Consulta rápida: `python3 scripts/harness.py ruta <skill>`.

## Clases

| Clase | Herramienta | Agente / modelo | Qué |
|---|---|---|---|
| decidir | claude | el modelo más capaz de tu plan (/model) | Decisiones que se vuelven contrato: SPEC, AD-*, propuesta y publicación de specs |
| redactar | claude | el modelo mediano de tu plan (/model) | Elicitar, redactar y planear sin decidir contrato |
| recolectar | opencode | `recolector` · `opencode-go/deepseek-v4-pro` | Leer mucho y resumir: deja un digest en _bmad-output/digests/ para que Claude decida |
| revisar | opencode | `revisor-bmad` · `opencode-go/deepseek-v4-pro` | Revisión adversarial de artefactos o cambios con otra familia de modelos |
| ejecutar | opencode | `build` · `opencode-go/deepseek-v4.1-flash` | Implementar un change de OpenSpec |
| mecanico | opencode | `mecanico` · `opencode/mimo-v2.6-flash-free` | Tests, docs y trabajo repetitivo |
| prohibido | — (bloqueada) | — | Implementa fuera de OpenSpec y rompe 'BMAD no ejecuta'. Usa /cambio + /ejecutar-cambio. |
| libre | cualquiera | — | Skill genérica fuera del método (documentos, utilidades): se permite en ambas herramientas |

## Skills
| Skill | Clase |
|---|---|
| `bmad-agent-architect` | `decidir` |
| `bmad-architecture` | `decidir` |
| `bmad-correct-course` | `decidir` |
| `bmad-prd` | `decidir` |
| `bmad-spec` | `decidir` |
| `openspec-archive-change` | `decidir` |
| `openspec-propose` | `decidir` |
| `openspec-sync-specs` | `decidir` |
| `openspec-update-change` | `decidir` |
| `openspec-apply-change` | `ejecutar` |
| `bmad-qa-generate-e2e-tests` | `mecanico` |
| `bmad-agent-dev` | `prohibido` |
| `bmad-build` | `prohibido` |
| `bmad-build-auto` | `prohibido` |
| `bmad-deep-recon` | `recolectar` |
| `bmad-advanced-elicitation` | `redactar` |
| `bmad-agent-analyst` | `redactar` |
| `bmad-agent-pm` | `redactar` |
| `bmad-agent-ux-designer` | `redactar` |
| `bmad-brainstorming` | `redactar` |
| `bmad-create-epics-and-stories` | `redactar` |
| `bmad-customize` | `redactar` |
| `bmad-forge-idea` | `redactar` |
| `bmad-help` | `redactar` |
| `bmad-party-mode` | `redactar` |
| `bmad-prfaq` | `redactar` |
| `bmad-product-brief` | `redactar` |
| `bmad-project-context` | `redactar` |
| `bmad-retrospective` | `redactar` |
| `bmad-sprint-planning` | `redactar` |
| `bmad-ux` | `redactar` |
| `openspec-explore` | `redactar` |
| `bmad-code-review` | `revisar` |
| `bmad-review` | `revisar` |
| `bmad-walkthrough` | `revisar` |

**Skills no listadas: bloqueadas en ambas herramientas** hasta clasificarlas con `/clasificar-skill <nombre>` en Claude Code.

## Niveles de ceremonia
| Nivel | Qué lleva |
|---|---|
| 0 | Directo: ≤ trivial_lineas y riesgo bajo. Rama fix/<slug>, sin change, sin issue, solo CI. |
| 1 | Ligero: una capacidad, riesgo bajo o medio. Change (proposal + tasks), rama feat/<id>, sin issue, Revisión 1, Claude propone y juzga en una sesión. |
| 2 | Estándar: varias capacidades o riesgo medio. Change completo, issue, rama feat/<n>-<id>, revisiones según riesgo. |
| 3 | Completo: iniciativa nueva o riesgo alto. BMAD antes, change, issue y las tres revisiones. |

Revisiones por riesgo: bajo → Revisión 1 · medio → + Revisión 2 · alto → + Revisión 3 (Luna) y lectura humana; el riesgo alto sube el nivel a 3.

## Zonas
**Alto (rojo):**
- `(^|/)(auth|login|session|oauth|permissions?|rbac|iam)(/|$|\.)`
- `(^|/)(payments?|billing|checkout|invoic\w*)(/|$|\.)`
- `(^|/)(secrets?|credentials?|crypto|encryption)(/|$|\.)|(^|/)\.env`
- `(^|/)(migrations?|migrate)(/|$|\.)|\.sql$`
- `(^|/)(infra|terraform|k8s|helm|deploy)(/|$)|(^|/)Dockerfile|(^|/)docker-compose[^/]*$`
- `^\.github/`
- `(^|/)deploy[^/]*$`

**Bajo (sin código de producción):**
- `(^|/)(docs?|tests?|__tests__|spec|specs|fixtures?)(/|$)`
- `\.(md|txt)$`
- `^openspec/`
- `^_bmad-output/`
- `^HANDOFF\.md$`
- `^\.harness/(revisiones/|telemetria\.jsonl$)`

## Modelos por agente de OpenCode
| Agente | Modelo |
|---|---|
| `build` | `opencode-go/deepseek-v4.1-flash` |
| `mecanico` | `opencode/mimo-v2.6-flash-free` |
| `explorador` | `opencode-go/deepseek-v4.1-flash` |
| `contexto-largo` | `opencode-go/deepseek-v4-pro` |
| `recolector` | `opencode-go/deepseek-v4-pro` |
| `revisor-gratis` | `opencode-go/deepseek-v4.1-flash` |
| `revisor-fuerte` | `opencode-go/deepseek-v4-pro` |
| `revisor-bmad` | `opencode-go/deepseek-v4-pro` |

## Memoria de código
| Qué | Valor |
|---|---|
| Estado | encendida (`habilitado: true`) |
| Versión | `0.11.0` (fijada en `.harness/versiones.json → binarios`) |
| Quién consulta el índice | agente(s) `build`, `explorador`, `recolector`, `contexto-largo`, `revisor-gratis`, `revisor-fuerte`, `revisor-bmad` (el veto global `codebase-memory_*` se lo quita al resto) |
| Quién escribe el índice | agente(s) nadie + scripts del harness (hooks post-merge/post-checkout, `cbm-indexar.sh`, `/init-harness`) |
| Vetadas por defecto a Claude y al resto de agentes | `index_repository`, `delete_project`, `manage_adr`, `ingest_traces` |
Detalle: `docs/harness-guide.md` §16.
