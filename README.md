# ai-harness-template

Repo base para trabajar cualquier proyecto (verde o existente) con **un método** y **tres copilotos**, con roles delimitados y GitHub como columna vertebral.

| Eje | Qué | Quién |
|---|---|---|
| Método | **BMAD planea y refina · OpenSpec ejecuta por change** (`propose → apply → archive`) | — |
| Herramientas | Arquitecto: **Claude Code** (Claude Pro) · Ejecutor: **OpenCode** (OpenCode Go) · Revisores: **OmniRoute** (capas gratis) y **Codex** (GPT-6 Luna, ChatGPT Free) | solo lectura para revisores |
| GitHub | issue → rama `feat/<issue>-<change-id>` → PR → CI + etiqueta de riesgo + check de proceso → merge por `/juzgar-pr` | — |

**Configurar un proyecto:** [`docs/ESTANDAR-PROYECTO.md`](docs/ESTANDAR-PROYECTO.md) (seguridad, calidad y operación, paso a paso) · **Verificar:** [`docs/PRUEBA-DE-HUMO.md`](docs/PRUEBA-DE-HUMO.md).

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

Toda la lógica está en `scripts/harness.py` (Python, solo biblioteca estándar) y todos los datos en `harness.json`. Hooks de git, hook de Claude, plugin de OpenCode y Actions son envoltorios de ese motor. `python3 scripts/harness.py sync` regenera los adaptadores (`opencode.json`, modelos de los agentes, `docs/harness/RUTAS.md`, `.cursor/rules`) y CI falla si se desincronizan. La suite `scripts/test_harness.py` (pruebas de riesgo, niveles, proceso del PR, evidencia, aprobación humana, presupuesto, guardias, secretos, plano de control, fail-closed, rutas, versiones y los escenarios adversariales de `docs/SEGURIDAD.md`) corre en el workflow `harness-selftest`.

## Memoria de código

Claude Code y OpenCode consultan un índice local del repo ([codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp), versión fijada y verificada por SHA-256) en lugar de leer archivo por archivo. Viene **encendida**; `/descubrir` te recomienda si dejarla así.

- **Apagar:** `habilitado: false` en `harness.json → mcp.codebase_memory` → `python3 scripts/harness.py sync` → reinicia las herramientas.
- **Encender:** `habilitado: true` → `sync` → `bash scripts/cbm-instalar.sh` → `bash scripts/cbm-indexar.sh`.
- Se re-indexa sola, en segundo plano, tras `git pull`/`merge` y al cambiar de rama; a mano: `bash scripts/cbm-indexar.sh`.
- Solo el ejecutor (`build`) y los scripts del harness escriben en el índice; los revisores y Claude solo consultan. Los secretos nunca se indexan.

Detalle: [`docs/harness-guide.md` §16](docs/harness-guide.md).

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
.mcp.json / .cbmignore       memoria de código para Claude y exclusiones del índice (generados por sync)
.githooks/                   pre-commit / commit-msg / pre-push por rol · post-merge / post-checkout (re-indexado en segundo plano)
scripts/                     harness.py (motor) + test_harness.py · bootstrap, instalar-frameworks, doctor, github-setup, nuevo, estado, inventario, riesgo, cambio, arq, ejec, ejec-contenedor · cbm, cbm-instalar, cbm-indexar (memoria de código)
.github/                     plantillas de issue y PR; workflows ci, riesgo, proceso, harness-selftest
docs/                        harness-guide, LECCIONES, DECISIONES (a mano) · ESTADO, harness/RUTAS (generados) · ONBOARDING · harness/ (MAPA, DELEGACION, INVENTARIO, resumenes/)
_bmad/ _bmad-output/         BMAD (los instala instalar-frameworks.sh)
openspec/                    OpenSpec (lo instala instalar-frameworks.sh)
```

## Seguridad: qué está garantizado

Detalle, modelo de amenazas y riesgos residuales en [`docs/SEGURIDAD.md`](docs/SEGURIDAD.md). Resumen honesto:

| Control | Qué hace | Garantía |
|---|---|---|
| Guardias de Claude y OpenCode | Bloquean leer o imprimir secretos, editar código (Claude), artefactos del arquitecto (OpenCode), el plano de control y skills de otra herramienta. Fallan **cerrados** | Guardia: se basa en patrones |
| Contenedor del ejecutor | Secretos del repo montados como `/dev/null`; plano de control en solo lectura; sin `~/.ssh` ni llavero | Barrera del sistema operativo (la red **no** está restringida) |
| Sandbox de Claude (`/sandbox`) | `denyRead` de secretos y `denyWrite` del plano de control para bash | Barrera del sistema operativo, **solo si el sandbox arranca** |
| Git hooks | Por rol, con el motor y la config de `HEAD`; escaneo de secretos para todos | Local: se salta con `--no-verify` |
| Gate `proceso` (`pull_request_target`) | Evalúa con el motor y el `harness.json` de la rama base; exige evidencia de revisión atada al commit y review APPROVED humana en riesgo alto, plano de control, techo duro o presupuesto agotado | Real en el servidor; **bloquea el merge solo con `main` protegida** (repo público o GitHub Pro) |
| `ci` | Tests del stack y gitleaks | Real en el servidor |

Las casillas del PR no son evidencia. La evidencia son los registros de `harness.py revision registrar`, atados al commit revisado; lo que no prueban está explicado en `docs/SEGURIDAD.md` §3.

Lanza con `scripts/arq` (Claude, con `/sandbox`) y `scripts/ejec-contenedor` (OpenCode aislado). Override consciente: `HARNESS_OVERRIDE=1`, queda registrado en el commit.

## Reglas que no se negocian

1. La suscripción de Claude solo se usa en Claude Code. Nunca detrás de un proxy.
2. OmniRoute solo con proveedores por API key que permitan uso personal. Nunca OAuth de Antigravity o Kiro, ni sesiones web.
3. BMAD no ejecuta. OpenSpec es la única vía para cambiar el código.
4. Ningún agente modifica el plano de control (guardias, hooks, workflows, permisos, `harness.json`) sin tu aprobación verificable en GitHub.
5. `validate` en verde no garantiza el `archive`: checklist de `docs/LECCIONES.md` §1 antes de archivar.
6. Ningún agente afirma que los tests pasan: lo dice CI. La verificación es contra la realidad.
7. El traspaso entre herramientas pasa por GitHub y por archivos (change, HANDOFF, ESTADO), nunca por copiar conversaciones.
8. El harness es vivo: las mejoras vuelven a este repo base.

Licencia MIT.
