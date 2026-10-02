# Handoff (estado vivo de la rama)

- Fecha / herramienta / modelo: 2026-10-01 · OpenCode (build, `HARNESS_OVERRIDE=1`, fuera del contenedor) · `opencode-go/space-bunny-free` (gratis, cero retención)
- Issue / spec: #2 · openspec/changes/add-codebase-memory-mcp (nivel 3, riesgo alto, OpenCode-zona-roja: autorizado)
- Qué se hizo: grupos 0 (arquitecto), 1, 2, 3, 4 y **3b, 5, 6 (S2)** completos; las marcas de 3.4, 5.1–5.6 y 9.1–9.3 están puestas y el árbol está limpio.
- Qué falta: **6.1 (la parte manual)**, 1.3, 7.1, 7.2, 9.7, 10.1–10.3, 11.1–11.3, y las revisiones 1 y 2 (la 3 es de Luna) al final.
- Decisiones tomadas y por qué: ver abajo («Hallazgos técnicos»).
- Dudas para el arquitecto: ver abajo.
- Riesgos: cambio grande del plano de control; el PR exige aprobación humana en GitHub.
- Siguiente paso sugerido: S3 del plan de `tasks.md` = `/ejecutar-cambio add-codebase-memory-mcp grupo 7`: `scripts/cbm-indexar.sh` (7.1) y los hooks `post-merge`/`post-checkout` (7.2), y después 9.7 delegado a @mecanico.
- **Excepción de modelo (2026-10-01):** el change es de riesgo **alto**, así que por `modelo_por_riesgo` cada sesión debería ir con el modelo fuerte; el usuario lo autorizó explícitamente para S1 y para S2 (`space-bunny-free`, gratis y cero retención). S3–S6 vuelven al modelo fuerte salvo autorización nueva.
- Nota del arquitecto (2026-10-01), modelos: `build` queda por defecto en `opencode-go/deepseek-v4.1-flash`, pero **este change es de riesgo alto**: según `modelo_por_riesgo`, cada sesión de este change va con DeepSeek V4 Pro, elegido con `/models` al abrir la sesión (requiere la región «Global» activada en la cuenta de Go; respaldo `mimo-v2.6-pro`, luego `glm-5.3`), `@mecanico` a `opencode/mimo-v2.6-flash-free` (respaldo `opencode-go/mimo-v2.6-flash`), `recolector` y `contexto-largo` a `deepseek-v4-pro` (motivo: `docs/LECCIONES.md` §21). `sync` ya regeneró `.opencode/agents/*.md` y `opencode.json` en el árbol; commitéalos con la tarea 5.5. Si la calidad de DeepSeek en un grupo no alcanza (tests en rojo tras 3 intentos), anótalo aquí y cambia con `/models` al respaldo.

## Estado de los commits

| Grupo | Tareas | Commit |
|---|---|---|
| 0 (arquitecto) | 0.1–0.5 | ef8ea1a y anteriores |
| 1 | 1.1, 1.2 (1.3 queda manual) | a9da587 |
| 2 | 2.1–2.3 | a24c30a |
| 3+4 | 3.1–3.3, 4.1–4.3 | bde07f2 |
| 3b+5+6 (S2) | 3.4, 5.1–5.6, 6.1 (código), 9.1–9.3 | `bcca30a` (código) y `89799bb` (adaptadores + selftest) |

**Nada sin commitear.** Selftest completo verde: **70 tests OK** (`python3 -m unittest discover -s scripts -p 'test_*.py'`, ~230 s). `python3 scripts/harness.py sync --check` en verde.

## Sesión S2 (grupo 3b, 5, 6): qué quedó comprobado y cómo

- **3.4 (caché compartida), a mano con dos clones** (`git clone` de este repo a `/tmp/cbm-r3/{A,B}` con el binario enlazado): los dos responden a `list_projects` a la vez con el MISMO daemon y cada uno ve su proyecto (`private-tmp-cbm-r3-A`, `private-tmp-cbm-r3-B`); tocar `.cbmignore` en A borró solo el proyecto de A (B siguió ahí), el re-indexado en frío lo devolvió, y el `mtime` de `~/.cache/codebase-memory-mcp` del usuario no cambió (1790883897 antes y después).
- **Los cuatro desenlaces de `cbm invalidar-cache`**, que el log distingue con frases exactas: `índice al día (las exclusiones no cambiaron)` · `índice del proyecto <n> borrado: se re-indexa en frío` · `este repo no estaba en el índice: se indexa en frío`. Si el borrado falla, sale 1 con `⛔` (fail-closed: un índice viejo sobreviviendo dejaría consultable un archivo recién excluido).
- **La invalidación NO reimplementa la regla de nombres del servidor**: pregunta `scripts/cbm cli list_projects --format json` y empareja `root_path` (resuelto) con la raíz del repo; luego `scripts/cbm cli --quiet delete_project '{"project": "<nombre>"}'`. Regla observada en v0.11.0, por si hace falta: ruta real sin `/` inicial y con `/` y espacios como `-` (`/Users/x/repo` → `Users-x-repo`). Los tests usan un binario falso que devuelve `basename(raíz)`, así que **esa regla no está verificada por el selftest** (a propósito: la implementación no depende de ella).
- **5.6**: `opencode.json` lleva `tools["codebase-memory_*"]: false` global, `agent.<consulta>.tools["codebase-memory_*"]: true`, y para cada consulta que no escribe, las cuatro de escritura en `false`. `build` no lleva claves por herramienta; `@mecanico` no recibe ninguna. Con `habilitado: false` se retiran todas las claves `codebase-memory_*` (y los dicts que quedan vacíos) sin tocar otras.
- **6.1 (código)**: `.claude/settings.json` lleva las cuatro reglas literales `mcp__codebase-memory__<w>` en `permissions.deny`, `enabledMcpjsonServers: ["codebase-memory"]` y `./.mcp.json` + `./.cbmignore` en `sandbox.filesystem.denyWrite`.
- **Extras que hubo que hacer para que esto fuera testeable y correcto** (no estaban en tasks.md, pero no cambian el contrato): `scripts/cbm` lee la config por el override `HARNESS_CONFIG` igual que `harness.py` (antes leía `<raíz>/harness.json` a pelo y las dos fuentes podían discrepar); `harness.py cbm ruta-cache` es la única fuente de la ruta de caché y expande `${VAR:-def}` y `~` (`os.path.expandvars` no entiende `${VAR:-def}`: por eso el `mkdir` creaba el directorio literal `${XDG_CACHE_HOME:-~/.cache}` dentro del repo, que ya se borró); `doctor` reporta el error de incoherencia en vez de reventar.
- **Ojo con el estado de `opencode.json`**: a mitad de sesión apareció en el árbol con las claves VIEJAS por herramienta (las de la 5.6 sin aplicar) y `sync --check` lo delató. No se averigua quién lo escribió; si vuelve a pasar, `python3 scripts/harness.py sync` antes de commitear y `sync --check` justo antes.
- **`git config core.hooksPath` estaba DESACTIVADO en este clon** (por eso `doctor` se quejaba y por eso el hook de commit no añadía el marcador `Harness-Override`). Lo activé a mano (config local, no commiteado). Si en otra sesión `doctor` dice «git hooks inactivos», es eso.
- **Para @mecanico en S3 (9.7)**: en `scripts/test_harness.py` ya están `BINARIO_FALSO`, `TestMemoriaDeCodigo.instalar_binario_falso`, `env_indice` (pone `XDG_CACHE_HOME` y `CBM_FAKE_LOG` a un temporal) y `llamadas_a(herramienta)`. El binario falso responde `--version` con la versión fijada (obligatorio: `scripts/cbm` compara versión), `config set` como no-op, `list_projects --format json` y `delete_project`. Con `CBM_FAKE_VACIO=1` devuelve el índice vacío. **Nunca** tocar `~/.cache/ai-harness` ni `~/.cache/codebase-memory-mcp`.

## Verificación del grupo 3+4 (S1)

- Selftest completo verde sobre el árbol actual: **55 tests OK** (`python3 -m unittest discover -s scripts -p 'test_*.py'`).
- 3.1: interruptor apagado → `scripts/cbm` sale **1** con mensaje; `~/.config` y `~/.cache/codebase-memory-mcp` del usuario con el mismo `mtime` antes y después (la config del usuario no se toca). El caso literal «`.env` sin excluir» se demostró con un `.gitignore` anidado que REINCLUYE el secreto (`sub/.gitignore` con `!.env`): sin el patrón en `.cbmignore`, `verificar-secretos` falla nombrando `sub/.env`. Ese es justo el caso que equityá el test 9.3.
- 3.2: con `auto_index=true` en una config global simulada (`HOME` temporal) y arranque vía wrapper, tras 10 s `list_projects` sigue en 0 y la config global sigue en `true`. Con control de no-vacuidad: el binario CRUDO con esa misma config global indexa (1 proyecto) y el wrapper no.
- 3.3: clon en `/tmp/cbm test/prueba cbm` (espacios en la ruta) responde `list_projects` por los dos comandos que `sync` genera: `["sh","-c",'exec "$(git rev-parse --show-toplevel)/scripts/cbm"']` (OpenCode) y `${CLAUDE_PROJECT_DIR}/scripts/cbm` (Claude).
- 4.2: invalidación probada con los tres casos — sin SHA previo borra la caché; SHA igual no borra; `.cbmignore` cambiado borra (indexado en frío).
- 4.3: con `.env` y `tmp/x.pem` de prueba, `search_code` de su contenido da **0 resultados**.

## Hallazgos técnicos (verificados, útiles para retomar)

- **v0.11.0 ignora `XDG_CONFIG_HOME`**: la config vive en `$CBM_CACHE_DIR/_config.db` (mismo dir que la caché). Aplica el fallback de D5: `scripts/cbm` exporta `CBM_CACHE_DIR`, `XDG_CONFIG_HOME` (inerte, documental) y `HOME` aislados bajo `.harness/cbm/<entorno>/`. Marcador de config en `.harness/cbm/<entorno>/config/.harness-config-<versión>`. `~/.config` y `~/.cache` del usuario no se tocan (verificado).
- **Valores por defecto del servidor**: `auto_index=false`, `watcher_enabled=true` → el envoltorio fija ambos en `false` (D4 paso 5). Verificado con `config get`.
- **macOS no tiene `timeout`**: para probar el arranque del servidor se usó `scripts/cbm < /dev/null` (el servidor sale solo con EOF de stdin). Para 3.2 (esperar 10 s) servirá `nohup ... & sleep 10; kill`.
- **Proyecto en `list_projects`**: el nombre se deriva de la ruta absoluta del repo (`/`→`-`, p. ej. `Users-...-ai-harness-template`). `search_code` exige `pattern` y `project`.
- **Exclusión del indexador**: `.cbmignore` (sintaxis gitignore, raíz del repo) funciona contra el indexador real: con `*.pem` quitado, `search_code` del contenido de `tmp/x.pem` lo encontraba; con el patrón, 0 resultados.
- **Un solo daemon activo por host**: v0.11.0 se niega a arrancar si hay un daemon vivo con OTRO `CBM_CACHE_DIR` (`CBM could not start because the active account daemon uses a different cache directory`). Importante para 3.2/3.3 y para los tests del grupo 9: hay que cerrar la sesión del servidor antes de arrancar otra, o usar la misma caché.
- **Arranque en frío lento**: ~9,2 s hasta que el servidor responde al `initialize`. Un cliente MCP de prueba con deadline de 8 s se cuelga y parece un fallo de handshake. Subir el deadline a 20 s.
- **El re-index por CLI es incremental**: no recoge archivos recién des-excluidos. Para que un secreto que estaba excluido aparezca en el índice hay que borrar la caché (justo lo que hace la invalidación de D6).
- **El contenido de `*.pem` nunca es buscable con `search_code`** aunque no esté excluido: `check_index_coverage` lo marca `not_tracked` y el patrón fijo `tmp/` cubre `tmp/x.pem`. El control negativo de 4.3 con `.pem` no puede demostrar nada; el equivalente válido es con `.env` (quitando su patrón de `.cbmignore` Y de `.gitignore` en frío: `results: 1`). El `0` del `.env` sí es atribuible a la exclusión. El `*.pem` sí funciona en la capa de exclusión (visible en `not_indexed` de `index_repository`).
- **Frontera conocida de `ignorar`**: un ARCHIVO llamado p. ej. `.ssh` (sin barra, regex `(^|/)\.ssh(/|$)` con `$`) no lo cubre el patrón `.ssh/` (solo dirs). `verificar-secretos` fallaría cerrado nombrándolo (seguro, no filtrador). Si importa, el arquitecto puede añadir `.ssh` (sin barra) a `ignorar` en un ajuste posterior. Los ejemplos naturales (`.ssh/id_rsa`, `.config/gh/hosts.yml`) sí quedan cubiertos.

## Dudas para el arquitecto

- Ninguna bloqueante. Quedan dos verificaciones manuales para el humano: la 1.3 (sesión real de OpenCode 1.18.33 para `tools`/`agent.tools` con prefijo `codebase-memory_*`) y la parte manual de la 6.1 (que `delete_project` se deniega y `list_projects` responde en una sesión de Claude Code). El código de la 6.1 ya está y su parte automática la cubre el test 9.2.
- **Resuelto en S2, cerrado:** la 4.2 («invalidación de D6») se quedó como subcomandos reutilizables de `harness.py` (`cbm invalidar-cache`, `cbm marcar-indexado`) y la 7.1 solo tiene que invocarlos. Con el cambio de diseño de S2, `invalidar-cache` ya no borra la caché entera sino el proyecto del repo con `cli delete_project`.
- **Resuelto en S2, cerrado:** la tensión 4.3 ↔ 9.3. El control negativo de 9.3 usa `.env` y está escrito y en verde.

## Grupo 1 — Verificación temprana de dependencias externas

### 1.1 Descarga y checksum (darwin-arm64)
- URL: `https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.11.0/codebase-memory-mcp-darwin-arm64.tar.gz`
- `shasum -a 256` obtuvo `4dee7f38b63740e6751d7a7ed7eb10291c1f2a3ea2415f599dc68370ca0a2d18` = esperado en design.md → Context. ✔
- Ruta del binario dentro del `.tar.gz`: **raíz del archivo** (`codebase-memory-mcp`, junto a `LICENSE`, `install.sh` —que no se usa— y `THIRD_PARTY_NOTICES.md`). Sin subcarpeta.
- Extracción: `tar -xzf <archivo> codebase-memory-mcp`.

### 1.2 Versión, config y CLI (hallazgos con el binario real)
- **Versión:** `codebase-memory-mcp --version` → `codebase-memory-mcp 0.11.0` (rc 0). El envoltorio extrae `\d+\.\d+\.\d+`.
- **`XDG_CONFIG_HOME` NO se respeta** (v0.11.0): `XDG_CONFIG_HOME=/tmp/x ./codebase-memory-mcp config set auto_index false` escribe fuera de `/tmp/x`.
- **Config efectiva:** el binario guarda config y caché en el MISMO directorio: `$CBM_CACHE_DIR/_config.db` (con `HOME` aislado: `$HOME/.cache/codebase-memory-mcp/_config.db`). No existe `~/.config/codebase-memory-mcp/config.json` en v0.11.0.
- **Variante de D5 que aplica:** el fallback (`HOME` aislado) documentado en design.md; además `CBM_CACHE_DIR` ya aísla la config por sí solo. `scripts/cbm` exporta `CBM_CACHE_DIR=<raíz>/.harness/cbm/<entorno>`, `XDG_CONFIG_HOME=<raíz>/.harness/cbm/<entorno>/config` (inerte en v0.11.0, documental) y `HOME=<raíz>/.harness/cbm/<entorno>/home` (fallback activo). Todo queda bajo `.harness/cbm/`, ignorado por git.
- **Valores por defecto:** `auto_index=false`, `watcher_enabled=true` → el envoltorio fija ambos en `false` (marcador `.harness-config-<version>`).
- **CLI:** `cli [--quiet] <tool> [json_args]` funciona: `cli --quiet index_repository --repo-path <abs>` (rc 0, imprime resumen JSON), `cli --quiet list_projects` (rc 0; nombre del proyecto derivado de la ruta abs con `/`→`-`, p. ej. `private-tmp-cbm-mini`). `search_code` exige `pattern` y `project`.
- **Exclusión:** `.cbmignore` (sintaxis gitignore) excluye del índice: con `.env` y `*.pem` en `.cbmignore`, re-indexado y `search_code` del contenido de esos archivos → 0 resultados (antes de excluirlas, sí aparecían).

### 1.3 OpenCode 1.18.33 `tools`/`agent.tools` (MANUAL — queda para el humano)
Confirmar en una sesión real de OpenCode que el veto global `tools: {"codebase-memory_index_repository": false}` + `agent.build.tools: {"...": true}` veta la herramienta a un subagente (p. ej. `revisor-gratis`) y la deja a `build`, con el prefijo `codebase-memory_`. Si el esquema difiriera, usar la clave `permission` equivalente y anotarlo aquí. El selftest (9.2) cubre la estructura del `opencode.json` generado; esta verificación de runtime queda pendiente.

## Grupo 7 — Script de re-indexado y hooks de git (S3)

- **7.1 `scripts/cbm-indexar.sh [--fondo]`**: interruptor, lock `mkdir`+PID (huérfano si el PID
  muere o pasa de 30 min), `verificar-secretos` → `invalidar-cache` → `index_repository` →
  `marcar-indexado`. Con `--fondo` el lock se toma en el proceso rápido y lo suelta el worker
  desacoplado (`nohup`, log en `.harness/cbm/ultimo-indexado.log`), que es lo que evita que dos
  disparos seguidos indexen dos veces. Flag interno `--lock-comprado` para ese worker.
  Medido: primer plano OK, `--fondo` 0,08 s.
- **7.2 `.githooks/post-merge` y `.githooks/post-checkout`**: `post-checkout` solo con `$3=1` y sin
  `rebase-merge`/`rebase-apply` bajo `git rev-parse --git-dir` (sirve también en worktree, que
  dispara el hook en su propia raíz). Los dos: `|| true; exit 0`, sin salida.
  Verificado a mano: switch → log nuevo; `git checkout -- README.md` → sin log; `rebase-merge`
  presente → sin log; `worktree add` → log en `../wt-cbm/.harness/cbm/`; rebase real → sin indexado
  a mitad; con `scripts/cbm-indexar.sh` o el binario ausentes git no muestra errores.
- **9.7** (delegado a @mecanico, revisado): clase `TestHooksReindexado` con 5 tests sobre el
  binario falso (solo `$3=1`, rebase, lock tomado, fallo del indexador → los hooks salen con 0,
  `habilitado:false` sin log) + aserciones de `TestEmpaquetado` de que los scripts y hooks están
  en git como `100755`. Suite completa: 75 tests OK (~4 min).

### Lo que broke y se arregló aquí (para el que siga)

- El fixture `Repo` de `scripts/test_harness.py` copia `.githooks` y hace `git checkout`, así que
  desde 7.2 los hooks creaban `.harness/cbm/` en el repo temporal y `git add -A` lo recogía:
  7 tests de riesgo, nivel, evidencia y presupuesto fallaban. Arreglado ignorando
  `.harness/cbm/` en `.git/info/exclude` del temporal (exclude local: ningún test lo ve y no toca
  el `.gitignore` del repo). Ojo con esto al añadir hooks nuevos al fixture.
- Los tests de hooks lanzan el indexado en segundo plano: `TestHooksReindexado` espera con límite
  de tiempo a que el worker termine antes de cerrar el temporal.
