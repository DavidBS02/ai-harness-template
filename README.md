# ai-harness-template

Repo base para trabajar cualquier proyecto (verde o existente) con **un método** y **tres copilotos**, con roles delimitados y GitHub como columna vertebral.

| Eje | Qué | Quién |
|---|---|---|
| Método | **BMAD planea y refina · OpenSpec ejecuta por change** (`propose → apply → archive`) | — |
| Herramientas | Arquitecto: **Claude Code** (Claude Pro) · Ejecutor: **OpenCode** (OpenCode Go) · Revisores: **OmniRoute** (capas gratis) y **Codex** (GPT-6 Luna, ChatGPT Free) | solo lectura para revisores |
| GitHub | issue → rama `feat/<issue>-<change-id>` → PR → CI + etiqueta de riesgo + check de proceso → merge por `/juzgar-pr` | — |

Guía completa: [`docs/harness-guide.md`](docs/harness-guide.md) · Regla que se carga siempre: [`.claude/rules/workflow-routing.md`](.claude/rules/workflow-routing.md) · Lecciones con origen real: [`docs/LECCIONES.md`](docs/LECCIONES.md).

## Quickstart

```bash
git clone https://github.com/<tu-usuario>/ai-harness-template.git
bash ai-harness-template/scripts/bootstrap.sh /ruta/a/tu/proyecto   # no pisa nada existente
cd /ruta/a/tu/proyecto
bash scripts/instalar-frameworks.sh    # BMAD + OpenSpec (se salta lo ya instalado)
bash scripts/doctor.sh
bash scripts/github-setup.sh           # labels riesgo:* + protección de main
scripts/arq                             # Claude Code en rol arquitecto
> /descubrir
```

## Fase 0: `/descubrir` (lo hace Claude)

Primero entiende el proyecto; de ahí sale el routing.

1. **Diagnóstico del método:**
   - **A:** ya tiene BMAD y OpenSpec montados. No reinstala; usa el SPEC, el spine y `openspec/specs/`.
   - **B:** tiene código pero no método. Usa `bmad-project-context` o `bmad-deep-recon` y resúmenes delegados a OpenCode.
   - **C:** está verde. Ruta BMAD: `bmad-help` → forja/brief → `bmad-spec` → `bmad-architecture` → primer `/cambio`.
2. **Inventario mecánico** (`scripts/inventario.sh`, sin LLM).
3. **`docs/harness/MAPA.md`:** zonas roja, amarilla y verde con rutas reales, capacidades y AD-*.
4. **`harness.json` → `zonas`:** las regex que usa el motor para calcular el riesgo (calibradas por alcance del daño).
5. **`docs/harness/DELEGACION.md`:** qué tarea de este repo va a qué modelo, y los primeros changes.
6. **`/init-harness`:** fusiona las reglas `[harness]` con tu `openspec/config.yaml`, llena `AGENTS.md`, saca el estado de las reglas (deudas → issues, decisiones → `docs/DECISIONES.md`) y escribe el `ci.yml` real.

## Flujo por cambio

```
Claude   /cambio "<idea>"          nivel 1–3 · scripts/nuevo.sh (rama, issue si nivel ≥ 2) · /opsx:propose (con ## Harness) · PR draft
Claude   /codex:adversarial-review riesgo medio/alto: Luna ataca el plan
OpenCode /ejecutar-cambio <id>     /opsx-apply · marca tasks.md · @revisor-gratis · @revisor-fuerte · gh pr ready
GitHub   ci · riesgo · proceso     tests · etiqueta · change + issue + revisiones según riesgo + openspec validate
Claude   /juzgar-pr <n>            Luna si alto · checklist de archive · /opsx:archive · issues deuda/verificación · estado · merge
```

BMAD entra antes, cuando el pedido es de producto o arquitectura, y **no ejecuta nada**: entrega un dossier y nombra el `/cambio` o el `/opsx:update` que lo aplica.

**Niveles de ceremonia** (el costo sigue al tamaño): 0 directo (`fix/`, solo CI) · 1 ligero (change mínimo, una pasada de Claude) · 2 estándar · 3 completo (BMAD + tres revisiones). **Cada skill de BMAD y OpenSpec tiene su herramienta y su modelo** según su clase (decidir, redactar, recolectar, revisar, ejecutar, mecánico, prohibido): `/ruta <skill>` lo dice y las guardias lo imponen. Tabla en `docs/harness/RUTAS.md`. **Lista blanca:** una skill nueva sin clasificar se bloquea en ambas herramientas (y CI falla) hasta que la clasificas con `/clasificar-skill <nombre>` en Claude Code.

## Un motor, un archivo de datos

Toda la lógica está en `scripts/harness.py` (Python, solo biblioteca estándar) y todos los datos en `harness.json`. Hooks de git, hook de Claude, plugin de OpenCode y Actions son envoltorios de ese motor. `python3 scripts/harness.py sync` regenera los adaptadores (`opencode.json`, modelos de los agentes, `docs/harness/RUTAS.md`, `.cursor/rules`) y CI falla si se desincronizan. La suite `scripts/test_harness.py` (20 pruebas: riesgo, niveles, proceso del PR, guardias de Claude y OpenCode, hooks por rol, rutas, sync, empaquetado) corre en el workflow `harness-selftest`.

## Estructura

```
harness.json                 datos del harness: zonas, permisos, modelos por agente, clases y rutas por skill, niveles
AGENTS.md                    reglas del repo (fuente única; incluye "Puntos de entrada" y "Nunca entra al repo")
CLAUDE.md                    @AGENTS.md + @.claude/rules/workflow-routing.md + guardia de rol
HANDOFF.md                   estado vivo de la rama
.claude/rules/               workflow-routing.md (corta, siempre cargada)
.claude/commands/            /descubrir /init-harness /cambio /juzgar-pr /ruta /clasificar-skill /handoff
.claude/settings.json        hook de guardia de Claude Code
.opencode/agents/            explorador, mecanico, contexto-largo, recolector, revisor-gratis, revisor-fuerte, revisor-bmad
.opencode/commands/          /ejecutar-cambio /recolectar /revisar-artefacto /resumir-modulos /ruta /handoff
.opencode/plugins/guardia.ts guardia de OpenCode
opencode.json                modelos por defecto + proveedor OmniRoute
.harness/                    base de openspec/config.yaml
.githooks/                   pre-commit / commit-msg / pre-push por rol
scripts/                     harness.py (motor) + test_harness.py · bootstrap, instalar-frameworks, doctor, github-setup, nuevo, estado, inventario, riesgo, cambio, arq, ejec
.github/                     plantillas de issue y PR; workflows ci, riesgo, proceso, harness-selftest
docs/                        harness-guide, LECCIONES, DECISIONES (a mano) · ESTADO, harness/RUTAS (generados) · ONBOARDING · harness/ (MAPA, DELEGACION, INVENTARIO, resumenes/)
_bmad/ _bmad-output/         BMAD (los instala instalar-frameworks.sh)
openspec/                    OpenSpec (lo instala instalar-frameworks.sh)
```

## Guardias de rol

| Capa | Dónde | Qué bloquea |
|---|---|---|
| 1. Instrucciones | CLAUDE.md, AGENTS.md, workflow-routing.md | Cada agente rechaza lo que no es suyo y redirige; BMAD no ejecuta |
| 2a. Hook de Claude | `.claude/settings.json` + `scripts/guardia_claude.py` | Claude no edita código de la app (sí `docs/`, `openspec/`, `_bmad-output/`, config del harness) ni corre skills de otra herramienta |
| 2b. Plugin de OpenCode | `.opencode/plugins/guardia.ts` | OpenCode no edita proposal, design, specs, `openspec/specs/`, `config.yaml`, BMAD, reglas ni CI; no toca zona roja sin autorización en el proposal; no corre skills de decidir/redactar ni las prohibidas; no archiva, no mergea, no hace push a main |
| 2c. Revisores | `.opencode/agents/revisor-*.md` | `edit: deny` |
| 3. Git hooks | `.githooks/` | No se commitea fuera del rol ni se hace push a main |
| 4. GitHub | `proceso.yml` + protección de main | No se mergea sin change, sin issue o sin las revisiones del riesgo |

Lanza con `scripts/arq` (Claude) y `scripts/ejec` (OpenCode). Override consciente: `HARNESS_OVERRIDE=1 scripts/arq`; queda registrado en el commit.

## Reglas que no se negocian

1. La suscripción de Claude solo se usa en Claude Code. Nunca detrás de un proxy.
2. OmniRoute solo con proveedores por API key que permitan uso personal. Nunca OAuth de Antigravity o Kiro, ni sesiones web.
3. BMAD no ejecuta. OpenSpec es la única vía para cambiar el código.
4. `validate` en verde no garantiza el `archive`: checklist de `docs/LECCIONES.md` §1 antes de archivar.
5. Ningún agente afirma que los tests pasan: lo dice CI. La verificación es contra la realidad.
6. El traspaso entre herramientas pasa por GitHub y por archivos (change, HANDOFF, ESTADO), nunca por copiar conversaciones.
7. El harness es vivo: las mejoras vuelven a este repo base.

Licencia MIT.
