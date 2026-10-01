# Harness guide — método (BMAD + OpenSpec) × herramientas × GitHub

Guía maestra para humanos. La regla corta que se carga siempre es `.claude/rules/workflow-routing.md`; los datos viven en `harness.json` y su tabla legible (generada) en `docs/harness/RUTAS.md`; las lecciones con su origen, en `docs/LECCIONES.md`.

## 1. El modelo

| Eje | Qué decide | Dueño |
|---|---|---|
| Método | Qué se hace y en qué artefacto queda | BMAD planea · OpenSpec ejecuta |
| Herramienta / modelo | Quién lo hace y con qué modelo | Claude Code arquitecto · OpenCode ejecutor · revisores de otra familia |
| GitHub | Cómo viaja y cuándo es verdad | rama → PR → CI → merge; deudas como issues |

**Arquitectura interna:** un motor (`scripts/harness.py`, Python, solo biblioteca estándar) y un archivo de datos (`harness.json`). Hooks de git, hook de Claude Code, plugin de OpenCode, Actions y scripts son envoltorios del motor. `harness.py sync` regenera los adaptadores; CI falla si se desincronizan; `scripts/test_harness.py` prueba todo en repos temporales.

## 2. Rutas por skill: cada skill tiene su herramienta y su modelo

Cada skill de BMAD y OpenSpec pertenece a una **clase**, y la clase decide herramienta y modelo. Así se controla el consumo sin configurar skill por skill.

| Clase | Herramienta · modelo | Ejemplos | Por qué |
|---|---|---|---|
| decidir | Claude, el más capaz | `bmad-architecture`, `bmad-spec`, `bmad-prd`, propose/archive/sync/update | Lo que se vuelve contrato |
| redactar | Claude, el mediano | brief, forja, elicitación, PM, UX, épicas, sprint, explore, `bmad-project-context` | Redactar no requiere el modelo más caro |
| recolectar | OpenCode `recolector` (Kimi K3) | `bmad-deep-recon` | Lectura masiva: deja un digest en `_bmad-output/digests/` |
| revisar | OpenCode `revisor-bmad` (DeepSeek V4) | `bmad-review`, `bmad-code-review`, `bmad-walkthrough` | Lo más caro de BMAD, y mejor con otra familia |
| ejecutar / mecánico | OpenCode `build` / `mecanico` | apply de OpenSpec, `bmad-qa-generate-e2e-tests` | Implementar es volumen |
| prohibido | ninguna | `bmad-build`, `bmad-build-auto`, `bmad-agent-dev` | Implementan fuera de OpenSpec: rompen "BMAD no ejecuta" |

- `/ruta <skill>` (o `python3 scripts/harness.py ruta <skill>`) dice dónde va.
- Las guardias lo imponen: Claude no puede correr skills de recolectar ni revisar; OpenCode no puede correr las de decidir ni redactar; nadie corre las prohibidas.
- **Lista blanca:** una skill que no está en `harness.json` se bloquea en ambas herramientas, y CI (`harness.py skills --check`) falla si hay skills instaladas sin mapear. Se clasifica una vez con `/clasificar-skill <nombre>` en Claude Code: `harness.py analizar-skill` extrae los hechos sin LLM (tamaño, referencias, señales de escribir código, revisar, leer mucho), Claude propone clase con citas del SKILL.md, tú confirmas, y `harness.py clasificar` la escribe con su motivo en `skills_motivos`. OpenCode no puede editar `harness.json`, así que no puede autorizarse.
- Clase `libre` para skills genéricas fuera del método (documentos, utilidades): corren en ambas herramientas.
- Flujo típico con recolección: OpenCode `/recolectar bmad-deep-recon <tema>` → digest → Claude `bmad-architecture` leyendo solo el digest. Con revisión: Claude escribe el spine → OpenCode `/revisar-artefacto bmad-review <ruta>` → Claude decide qué aplica.

## 3. Niveles de ceremonia: el costo sigue al tamaño

| Nivel | Cuándo | Rama | Qué lleva | Pasadas por Claude |
|---|---|---|---|---|
| 0 · Directo | riesgo bajo y ≤ 20 líneas | `fix/<slug>` | PR + CI. Sin change ni issue ni revisores LLM | 0 |
| 1 · Ligero | una capacidad, riesgo bajo o medio | `feat/<id>` | change mínimo (proposal + tasks), Revisión 1, sin issue | 1 (propone y juzga) |
| 2 · Estándar | varias capacidades o riesgo medio | `feat/<n>-<id>` | change completo, issue, revisiones según riesgo | 2 |
| 3 · Completo | iniciativa nueva o riesgo alto | `feat/<n>-<id>` | BMAD antes, change, issue, las tres revisiones | 2 + BMAD |

- El proposal declara `Nivel:`; el motor aplica un mínimo según el riesgo (alto ⇒ 3) y `proceso.yml` exige solo lo que corresponde.
- **Lo mecánico con scripts** (`docs/LECCIONES.md` §12): `scripts/nuevo.sh <id> --nivel N [--issue "título"] [--worktree]` crea issue, rama y worktree sin gastar tokens.
- **Worktree solo si trabajas en paralelo.** Si no, una rama en el checkout normal basta.
- **Lotes:** varios triviales en un PR `chore/lote-<fecha>`.
- **Economía de la ejecución** (`docs/LECCIONES.md` §20). El costo de un agente es *contexto acumulado × pasos*, no tamaño del diff:
  - **Changes de ≤ ~12 tareas**; si no, se parten. Tareas en grupos de ≤ 5, cada grupo etiquetado `(build)` o `(@mecanico)`.
  - **Una sesión de OpenCode por grupo:** `/ejecutar-cambio <id> grupo N`, `/exit` y sesión nueva. Las revisiones van en su propia sesión al final.
  - **Modelo por costo:** `build` (GLM-5.3) para lo que exige diseño o toca seguridad; `@mecanico` (GLM-Flash) para tests, docs, empaquetado y repetición; `@explorador` para buscar. Claude solo decide y juzga.
  - **Leer poco:** `grep` y rangos, no archivos enteros; tests enfocados por tarea y la suite completa al cerrar el grupo; tres fallos seguidos → HANDOFF.md y parar.
  - **Para cortar una sesión en marcha:** Esc (dos veces si no para), pedir commit de lo marcado y HANDOFF.md, luego `/exit`.

## 4. Árbol de decisión por pedido

1. Producto, PRD, UX, arquitectura, cambiar un AD, dividir en épicas → BMAD (con `/ruta` para cada skill). Termina con dossier + comando que lo aplica.
2. Feature, fix, refactor → `/cambio` (nivel 1–3) → `/ejecutar-cambio` → `/juzgar-pr`.
3. Iniciativa grande → BMAD primero → un change por pieza.
4. Trivial → nivel 0.
5. Ambiguo → pregunta.

## 5. BMAD

- **Regla dura:** BMAD no ejecuta. Entrega un dossier, solo escribe en `_bmad-output/` y nombra el comando que lo aplica.
- **Tokens:** una sesión por workflow (`/clear` antes); modelo mediano para redactar y el más capaz solo para decidir; lectura masiva y reviews a OpenCode; spine fragmentado (índice + un archivo por AD o grupo) para cargar solo lo necesario; party mode solo para una decisión real en disputa; mide con `/status` antes y después durante dos semanas.
- **Instalación:** `scripts/instalar-frameworks.sh` (`core` + `bmm`, idioma, `output_folder: _bmad-output`).
- **Versiona los artefactos de contrato** (SPEC, spine, reviews) para que OpenCode los vea en su worktree (§9 de las lecciones). Los digests viven en `_bmad-output/digests/`, la única parte de `_bmad-output/` que OpenCode puede escribir.
- Cambiar un AD o una CAP pasa por `bmad-architecture` o `bmad-spec`, nunca por un change.

## 6. Handoff BMAD → OpenSpec

- Una vez por pieza: la épica se traduce a un change. Desde ahí, `openspec/specs/` es la verdad de lo construido.
- El primer change de producto siembra `openspec/config.yaml` y `AGENTS.md` (§5 de las lecciones).
- Si un change cambia stack, capas o convenciones, actualiza `openspec/config.yaml` en la misma tarea.

## 7. OpenSpec con el harness

- **Versión fijada** (devDependency): `validate` y `archive` son contrato de trabajo.
- **`## Harness` en cada proposal:** `Issue` (nivel ≥ 2), `Nivel`, `Riesgo`, `Zonas`, `OpenCode-zona-roja`. Lo leen el motor, los hooks, el plugin y las Actions.
- **Quién toca qué:** Claude escribe proposal, design y specs; OpenCode escribe código y marca `tasks.md`.
- **Archive** dentro del PR cuando se verifica en la rama; si exige producción, merge → verificar → PR `chore/archive-<id>`.
- **Verificaciones que dependen del futuro** → issue `verificacion-diferida`. Si fallan, no se desarchiva: change nuevo.

## 8. Flujo por cambio

```
Claude Code  /cambio "<idea>"  → nivel · scripts/nuevo.sh · /opsx:propose (## Harness) · validate · PR draft
             riesgo medio/alto → /codex:adversarial-review del plan
OpenCode     scripts/ejec → /ejecutar-cambio <id> → /opsx-apply · tests · tasks.md · revisores según nivel · gh pr ready
GitHub       ci (test) · riesgo (etiqueta + comentario) · proceso (nivel, change, issue, revisiones, sync --check, validate)
Claude Code  /juzgar-pr <n> → Luna si alto · checklist · /opsx:archive · issues deuda/verificación · harness.py estado · merge
```

Máximo dos vueltas entre OpenCode y Claude; a la tercera, el arquitecto decide (`/opsx:update`, o implementa con override).

## 9. Riesgo, zonas y revisión

- **Zonas por alcance del daño, no por dominio** (§11 de las lecciones). Rojo: filtrar credenciales, abrir acceso, corromper la única copia de los datos, romper el despliegue. Amarillo: lógica importante cubierta por tests (en un proyecto personal, el dinero va aquí si tiene tests). Verde: bajo impacto.
- **Riesgo final** = el más alto entre el cálculo por rutas y tamaño y el `Riesgo:` del proposal.
- **Revisores:** `@revisor-gratis` (combo OmniRoute) siempre con change · `@revisor-fuerte` (DeepSeek V4) si riesgo medio o alto · Luna (`/codex:review`) si alto. Cada revisión se registra con `harness.py revision registrar` sobre el commit revisado; el gate verifica que esa evidencia esté vigente. Riesgo alto, plano de control, techo duro o presupuesto agotado exigen además tu review APPROVED en GitHub sobre el HEAD.
- **Umbrales:** 5 archivos / 300 líneas son señales para el riesgo; `max_archivos_duro` / `max_lineas_duro` son el techo real, por encima del cual el gate pide aprobación humana.
- **Un solo entorno de producción:** despliegue solo desde main, uno a la vez, con respaldo previo si toca datos.

## 10. Guardias

| Capa | Bloquea |
|---|---|
| Instrucciones | Cada agente rechaza lo que no es suyo y redirige |
| Hook de Claude Code | Editar código de la app; correr skills de recolectar, revisar o prohibidas |
| Plugin de OpenCode | Editar artefactos del arquitecto (salvo `tasks.md` y digests); zona roja sin autorización; skills de decidir, redactar o prohibidas; archivar; mergear; push a main |
| Revisores | Editar (`edit: deny`; los de BMAD, `ask` y solo digests) |
| Git hooks | Commitear fuera del rol, push a main |
| GitHub (`pull_request_target`, motor y config de la base) | Mergear sin lo que exige el nivel y el riesgo; sin evidencia vigente; sin aprobación humana cuando corresponde. Bloquea el merge solo con `main` protegida |

Qué es guardia y qué es barrera real, y qué falla cerrado: `docs/SEGURIDAD.md`.

Override consciente: `HARNESS_OVERRIDE=1 scripts/arq` o `scripts/ejec`; queda como `Harness-Override: yes`.

## 11. Fuentes de verdad (pocas, a propósito)

| A mano | Generado |
|---|---|
| `AGENTS.md` (reglas del repo) | `docs/harness/RUTAS.md`, `opencode.json`, modelos de los agentes, `.cursor/rules/harness.mdc`, `.mcp.json`, `.cbmignore` (`harness.py sync`) |
| `harness.json` (datos del harness) | `docs/ESTADO.md` (`harness.py estado`, desde `openspec/` e issues) |
| `.harness/versiones.json` (versiones fijadas) | `.harness/telemetria.jsonl` (`harness.py telemetria registrar`, al mergear) |
| | `.harness/revisiones/` (evidencia, la escribe `harness.py revision registrar`) |
| `openspec/`, `_bmad-output/` (producto) | |
| `docs/DECISIONES.md` (append-only) y `docs/LECCIONES.md` | |
| Issues `deuda` y `verificacion-diferida` | |

Efímero: `HANDOFF.md`, que se vacía al mergear. Regla: si un dato puede derivarse de otra fuente, se genera (§13 de las lecciones).

## 12. Qué NO hace cada uno

- **Claude Code** no implementa (salvo override), no mergea sin CI verde y no corre skills de otra herramienta.
- **BMAD** no edita fuera de `_bmad-output/`.
- **OpenCode** no propone ni archiva, no edita el spec y no corre skills de decisión. Si falta algo, HANDOFF.md y se detiene.
- **Los revisores** solo reportan (los de BMAD, solo en digests).
- **CI** es la única voz que dice que los tests pasan.

## 13. Cuándo cambiar el setup

Configuración paso a paso: `docs/ESTANDAR-PROYECTO.md`; verificación: `docs/PRUEBA-DE-HUMO.md`.

- Límite de Claude Pro 3 o más veces por semana → baja niveles, mueve más BMAD a recolectar/revisar, o Max 5x.
- Límite de Go a diario → GLM Coding Plan Lite o Go + Lite.
- Luna se queda corto seguido → ChatGPT Go o Plus.
- Un proveedor de OmniRoute cambia sus términos → quítalo.
- Más de unas pocas horas al mes arreglando el harness → simplifícalo.

## 14. Privacidad

Claude Code con `/sandbox` y lectura de secretos bloqueada; OpenCode en `scripts/ejec-contenedor` con un token *fine-grained*; nada de cuentas de trabajo en el mismo usuario de macOS (`docs/ESTANDAR-PROYECTO.md` §1 y §3). Código o fixtures con datos personales, `.env` y tokens: nunca a capas gratuitas. Nada de cifras reales en reglas, estado ni decisiones versionadas.

## 15. El harness es vivo

Mejora encontrada → `harness.json`, la regla de routing, las lecciones o `openspec/config.yaml` → `harness.py sync` → súbela al repo base.

## 16. Memoria de código (codebase-memory-mcp)

Un índice local del repo (grafo de símbolos, llamadas y arquitectura) que Claude Code y OpenCode consultan por MCP en lugar de leer archivos uno a uno. Viene **encendida por defecto**; `/descubrir` recomienda si dejarla así según la visión del proyecto y deja la decisión en `docs/harness/MAPA.md`.

| Qué | Dónde |
|---|---|
| Interruptor | `harness.json → mcp.codebase_memory.habilitado` |
| Versión y SHA-256 por plataforma | `.harness/versiones.json → binarios.codebase-memory-mcp` |
| Binario (host) | `.harness/bin/<os>-<arch>/` · en el contenedor: `/usr/local/bin/` |
| Índice y configuración del servidor | `.harness/cbm/host/` y `.harness/cbm/contenedor/`, uno por entorno (ignorados por git; nunca toca `~/.config` ni `~/.cache`) |
| Adaptadores (generados) | `.mcp.json` (Claude), bloque `mcp` y vetos en `opencode.json` (OpenCode), `.cbmignore` |

**Encender:** `habilitado: true` → `python3 scripts/harness.py sync` → `bash scripts/cbm-instalar.sh` → `bash scripts/cbm-indexar.sh` → reinicia Claude Code y OpenCode.
**Apagar:** `habilitado: false` → `python3 scripts/harness.py sync` → reinicia Claude Code y OpenCode. Opcional, para liberar disco: `rm -rf .harness/cbm .harness/bin`. Los hooks y scripts quedan inertes.
**Re-indexar a mano:** `bash scripts/cbm-indexar.sh`. Lo normal es no hacerlo: los hooks `post-merge` y `post-checkout` re-indexan en segundo plano, sin bloquear git, tras `pull`/`merge`, al cambiar de rama y en un `worktree add`. El log queda en `.harness/cbm/<entorno>/ultimo-indexado.log`. Tras un `rebase` (o `pull --rebase`) sí hay que re-indexar a mano, y también si corres `build` en el host (`scripts/ejec`) y lanza `index_repository` mientras un hook indexa. El servidor nunca indexa por su cuenta (`auto_index` y watcher apagados).
**Quién escribe:** solo el agente `build` de OpenCode (`agentes_escritura`) y los scripts del harness. `index_repository`, `delete_project`, `manage_adr` e `ingest_traces` están vetadas por defecto para Claude Code y para cualquier otro agente, incluidos los revisores y los agentes que añadas después. Todos conservan las herramientas de consulta.
**Secretos:** `.cbmignore` se genera desde `mcp.codebase_memory.ignorar`, que refleja `secretos`. Antes de cada indexado y al arrancar el servidor, `python3 scripts/harness.py cbm verificar-secretos` comprueba que ningún archivo secreto del repo quedaría indexado; si alguno no queda cubierto, no se indexa y el servidor no arranca. Si cambia `.cbmignore`, el índice anterior se borra y se rehace en frío. Si añades un patrón a `secretos.rutas`, añade su equivalente a `ignorar`: el selftest falla si no lo haces.
**Actualizar la versión:** es un cambio del plano de control. Edita `version` y los cuatro `sha256` en `.harness/versiones.json` desde el `checksums.txt` de la release nueva. Nunca uses su `install.sh` ni `curl | bash`. Abre el PR con aprobación humana, corre `bash scripts/cbm-instalar.sh` y `scripts/ejec-contenedor` reconstruirá la imagen sola. Si el formato del índice cambió, el primer indexado tarda como uno en frío.
**Diagnóstico:** `bash scripts/doctor.sh` revisa binario y versión, cobertura de secretos, hooks e índice.
