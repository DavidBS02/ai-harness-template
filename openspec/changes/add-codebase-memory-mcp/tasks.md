> **Cómo se ejecuta este change.** Casi todo es plano de control, que el contenedor monta en solo lectura, así que el ejecutor corre **fuera del contenedor y con override**: `HARNESS_OVERRIDE=1 scripts/ejec` → `/ejecutar-cambio add-codebase-memory-mcp`. Los commits quedan marcados con `Harness-Override: yes` y el PR exige aprobación humana.
> El grupo 0 lo hace el arquitecto en el PR de la propuesta. Si una tarea revela un hueco del spec, escríbelo en HANDOFF.md y detente.
>
> **Plan de sesiones** (recortado el 2026-10-01 tras S1, ver design.md → «Revisión del 2026-10-01»). Una sesión NUEVA de OpenCode por fila; al terminar cada una: commit, `/handoff`, `/exit`. Salidas cortas siempre.
>
> | Sesión | Qué | Estado |
> |---|---|---|
> | S1 | grupos 3 y 4 | ✅ `bde07f2` |
> | S2 | `grupo 3b,5,6`: 3.4 (caché compartida), 5.6 (acceso por rol), 6.1; luego 9.1–9.3 delegados a @mecanico; con ellos en verde, marcar 5.1–5.4 y hacer 5.5 | |
> | S3 | `grupo 7`, luego 9.7 delegado a @mecanico | |
> | S4 | `grupo 10,11`: 10.x (@mecanico), 11.1–11.2, revisiones 1 y 2 y 11.3 | |
> | Humano | 1.3, la parte manual de 6.1 y la Revisión 3 (Luna) | |
>
> **Recortado** (no se hace en este change): grupo 8 (contenedor), 7.3, 9.4, 9.5 y 9.6 como tests separados (su contenido va en 9.3 y 9.7).

## 0. Contrato y método (arquitecto, en esta rama)

- [x] 0.1 `harness.json → mcp.codebase_memory` con los campos de design D1 y D6, y `control_plane.rutas` ampliado (D9); verificar con `python3 -c "import json;json.load(open('harness.json'))"` y `python3 scripts/harness.py doctor`
- [x] 0.2 `.claude/commands/descubrir.md`: paso «¿Memoria de código?» (D10); verificar leyendo el paso contra el requisito «Recomendación de memoria de código en /descubrir»
- [x] 0.3 `.claude/commands/init-harness.md`: paso «Memoria de código» (D10); verificar contra el requisito «Indexado inicial en /init-harness»
- [x] 0.4 `docs/harness/MAPA.md`: sección `## Memoria de código` en la plantilla; verificar con `grep -n "Memoria de código" docs/harness/MAPA.md`
- [x] 0.5 `docs/harness-guide.md` y `README.md`: cómo activar, apagar, re-indexar y actualizar; verificar que los comandos citados coinciden con los nombres de D3, D4 y D7

## 1. Verificación temprana de dependencias externas (Open Questions)

- [x] 1.1 Descargar en un temporal fuera del repo el `.tar.gz` v0.11.0 de la plataforma del host, comprobar que su SHA-256 coincide con el de design.md → Context y anotar en HANDOFF.md la ruta del binario dentro del archivo (¿raíz o subcarpeta?); verificar con `shasum -a 256 <archivo>`
- [x] 1.2 Con ese binario: cómo informa su versión (`--version` u otro), si respeta `XDG_CONFIG_HOME` (`XDG_CONFIG_HOME=/tmp/x <bin> config set auto_index false` y luego `find /tmp/x`), la ruta exacta del archivo de config resultante, y si `cli --quiet index_repository --repo-path` y `cli --quiet list_projects` funcionan con `CBM_CACHE_DIR` apuntando a un temporal. Anota en HANDOFF.md qué variante de D5 aplica y la ruta efectiva; verificar con la salida de esos comandos pegada en HANDOFF.md
- [ ] 1.3 Con OpenCode 1.18.33: confirmar que `tools` global con `"codebase-memory_index_repository": false` más `agent.build.tools` en `true` vetan la herramienta a un subagente y la dejan a `build`. Si el esquema difiere, usar `permission` y anotarlo en HANDOFF.md; verificar listando las herramientas visibles para `revisor-gratis` y para `build` en una sesión de prueba (manual)

## 2. Versión fijada e instalador

- [x] 2.1 `.harness/versiones.json → binarios.codebase-memory-mcp` con `version: "0.11.0"`, plantilla `url` y `sha256` para `darwin-amd64`, `darwin-arm64`, `linux-amd64` y `linux-arm64` (valores literales de design.md); verificar con `python3 -c "import json;print(json.load(open('.harness/versiones.json'))['binarios'])"`
- [x] 2.2 `scripts/cbm-instalar.sh` según D3: detección de os y arch, descarga con `curl -fsSL -o` a un temporal, verificación de SHA-256, extracción a `.harness/bin/<os>-<arch>/`, idempotente, sin `install.sh` ni pipe a shell; verificar instalando en el host (código 0 y versión correcta) y con un sha256 alterado a propósito en una copia temporal de versiones.json (código ≠ 0 y nada nuevo en `.harness/bin/`)
- [x] 2.3 `.gitignore`: `.harness/cbm/`, `.harness/bin/` y `.codebase-memory/`; verificar con `git check-ignore -v .harness/cbm/x .harness/bin/x .codebase-memory/x`

## 3. Envoltorio y configuración aislada (build)

- [x] 3.1 `scripts/cbm` según D4 y D5 (interruptor, resolución de binario por plataforma con comprobación de versión, caché y config por entorno `host`/`contenedor`, `verificar-secretos` al arrancar como servidor, `auto_index` y `watcher_enabled` apagados de forma idempotente, `exec "$@"`); verificar con `scripts/cbm cli --quiet list_projects` (código 0), con `habilitado:false` (código 1 y mensaje), comprobando que `~/.config/codebase-memory-mcp/config.json` no cambió (compara `stat` antes y después), y con un `.env` sin excluir (arrancar sin argumentos sale con 1 y nombra el archivo)
- [x] 3.2 Prueba de comportamiento de D5: con `auto_index=true` en una config «global» simulada (`HOME` temporal), arrancar `scripts/cbm` como servidor sobre un repo sin índice, esperar 10 s y cerrarlo; verificar que la caché del entorno sigue sin índice (`scripts/cbm cli --quiet list_projects` no lista el repo)
- [x] 3.3 Ruta con espacios: clonar el repo en un temporal con espacios en la ruta y arrancar el servidor con el `command` exacto que `sync` genera para OpenCode y para Claude (`${CLAUDE_PROJECT_DIR}` sustituido); verificar que los dos responden a `list_projects`

### 3b. Caché compartida (build, añadido el 2026-10-01)

- [x] 3.4 `scripts/cbm` y los subcomandos `cbm invalidar-cache` y `cbm marcar-indexado` según los nuevos D4, D5 y D6: `CBM_CACHE_DIR` = `mcp.codebase_memory.cache_dir` (por defecto `${XDG_CACHE_HOME:-$HOME/.cache}/ai-harness/cbm`) y `HOME` aislado bajo esa caché; sin entornos ni `HARNESS_CONTENEDOR`; estado local (hash, log y lock) en `.harness/cbm/`; la invalidación borra solo el proyecto de este repo con `cli delete_project`. Verificar: con dos clones temporales del repo, los dos responden a `list_projects` a la vez y cada uno ve su proyecto; cambiar `.cbmignore` en uno borra y re-indexa solo ese proyecto; `~/.cache/codebase-memory-mcp` del usuario sigue con el mismo `mtime`.

## 4. Secretos fuera del índice (build)

- [x] 4.1 `harness.py cbm verificar-secretos` según D6 (`listar_secretos` + `git -c core.excludesFile=.cbmignore check-ignore --no-index -q`); código 0 si todo está excluido, 1 nombrando los archivos si no; verificar con el test 9.3
- [x] 4.2 Invalidación de D6: guardar `cbmignore.sha256` tras cada indexado correcto; si difiere, borrar la caché del entorno antes de indexar; verificar con el test 9.6
- [x] 4.3 Prueba real: con `.env` y `tmp/x.pem` de prueba en el repo, indexar y buscar con `scripts/cbm cli --quiet search_code` el contenido de esos archivos; verificar que no aparecen y borrar los archivos de prueba

## 5. Adaptadores generados por sync (build)

- [x] 5.1 `sync` genera o retira `.mcp.json` (solo `mcpServers.codebase-memory`, conservando otros servidores y borrando el archivo si queda vacío) según D1; verificar con el test 9.1
- [x] 5.2 `sync` genera o retira en `opencode.json` las claves `mcp.codebase-memory`, `tools["codebase-memory_<w>"]=false` y `agent.<a>.tools[...]=true` para `agentes_escritura` según D1, sin tocar otras claves; verificar con el test 9.1
- [x] 5.3 `sync` genera o retira `.cbmignore` con cabecera `GENERADO` desde `ignorar`; verificar con el test 9.1
- [x] 5.4 `generar_rutas` añade a `docs/harness/RUTAS.md` una sección «Memoria de código» (estado, versión, quién escribe); verificar con `python3 scripts/harness.py sync && grep -n "Memoria de código" docs/harness/RUTAS.md`
- [x] 5.6 Acceso por rol (nuevo D1): `sync` escribe en `opencode.json` `tools["codebase-memory_*"]=false` global, `agent.<a>.tools["codebase-memory_*"]=true` para cada `agentes_consulta` y `false` por cada herramienta de escritura a los que no están en `agentes_escritura`; `sync` falla si `agentes_escritura` no está contenido en `agentes_consulta`; verificar con el test 9.2
- [x] 5.5 Correr `python3 scripts/harness.py sync` y commitear los adaptadores generados, incluidos `.opencode/agents/*.md` con los modelos nuevos; verificar con `python3 scripts/harness.py sync --check` (código 0)

## 6. Claude Code (build)

- [ ] 6.1 `.claude/settings.json`: `permissions.deny` con 4 reglas literales (`mcp__codebase-memory__index_repository`, `mcp__codebase-memory__delete_project`, `mcp__codebase-memory__manage_adr` y `mcp__codebase-memory__ingest_traces`, sin llaves ni comodines), `enabledMcpjsonServers: ["codebase-memory"]` y `sandbox.filesystem.denyWrite` con `./.mcp.json`, `./.cbmignore` y `./scripts` (ya está); verificar con el test 9.2 y, en una sesión de Claude Code, que `delete_project` se deniega y `list_projects` responde (manual)

## 7. Re-indexado (build)

- [x] 7.1 `scripts/cbm-indexar.sh [--fondo]` según D7 (interruptor, lock con mkdir y PID y limpieza de huérfanos, `verificar-secretos`, `cbm invalidar-cache`, `index_repository`, `cbm marcar-indexado`, log en `.harness/cbm/ultimo-indexado.log`); verificar en primer plano (código 0) y con `--fondo` (vuelve en < 1 s, `time bash scripts/cbm-indexar.sh --fondo`)
- [x] 7.2 `.githooks/post-merge` y `.githooks/post-checkout` (este último solo con `$3 = 1` y sin rebase en curso), ejecutables, siempre `exit 0` y sin salida; verificar con el test 9.7 y a mano: `git switch -c tmp-cbm && git switch -` (log nuevo), `git checkout -- README.md` (sin log nuevo), `git worktree add ../wt-cbm -b tmp-wt` (log nuevo en `../wt-cbm/.harness/cbm/`), un `git rebase` (sin indexado a mitad) y con el binario renombrado (git no muestra errores)

## 9. Selftest (`scripts/test_harness.py`) (@mecanico)

- [x] 9.1 Tests de `sync`: encendido genera `.mcp.json`, las claves de `opencode.json` y `.cbmignore`; apagado los retira; conserva otros servidores y claves; `sync --check` detecta la deriva; verificar con `python3 -m unittest discover -s scripts -p 'test_*.py'`
- [x] 9.2 Test: `.claude/settings.json → permissions.deny` contiene literalmente `mcp__<servidor>__<w>` para cada herramienta de `herramientas_escritura` (sin llaves ni comodines), y `opencode.json` las veta globalmente y las abre solo a `agentes_escritura`; verificar con el selftest
- [x] 9.3 Test: por cada regex de `secretos.rutas` se crea un archivo de ejemplo y `verificar-secretos` pasa con el `ignorar` por defecto; con un patrón quitado de `.cbmignore`, falla nombrando el archivo; un `.gitignore` anidado que reincluye un secreto con `!` hace fallar la verificación; un excludes global del usuario (`core.excludesFile`) que sí lo cubriría no cambia el resultado; `.env.example` no cuenta como secreto. El control negativo usa `.env`, no `*.pem` (HANDOFF: el indexador nunca rastrea `.pem`). Invalidación con un binario falso que registra sus argumentos: cambiar `.cbmignore` entre dos indexados llama a `delete_project` con el proyecto de ese repo y sin cambios no lo llama; verificar con el selftest
- [x] 9.7 Test de hooks con el mismo binario falso: `post-checkout` con `$3=0` no lanza nada; con `$3=1` lanza; con `.git/rebase-merge` presente no lanza; dos disparos seguidos con el lock tomado lanzan uno; los dos hooks salen con 0 aunque `cbm-indexar.sh` falle; con `habilitado: false` no lanzan nada ni crean `ultimo-indexado.log`; `TestEmpaquetado` incluye los scripts y hooks nuevos como ejecutables; verificar con el selftest

## 10. Diagnóstico y empaquetado (@mecanico; 10.1 build)

- [x] 10.1 `doctor` según el requisito «Diagnóstico de la memoria de código» (binario y versión, `verificar-secretos`, hooks ejecutables, existencia del índice; apagado → una línea ok); `harness.py versiones` lista también `binarios`; verificar con `python3 scripts/harness.py doctor` en los dos estados del interruptor
- [x] 10.2 `scripts/bootstrap.sh` (archivos nuevos y líneas de `.gitignore`) e `instalar-frameworks.sh` (llama a `cbm-instalar.sh` si está encendido), según D9; verificar con el test 11.1
- [x] 10.3 Actualizar el docstring de uso de `harness.py` con el subcomando `cbm`; verificar con `python3 scripts/harness.py | grep cbm`

## 12. Nadie indexa por MCP (build, opción a del 2026-10-02)

- [ ] 12.1 Con `agentes_escritura: []` (ya en `harness.json`), correr `python3 scripts/harness.py sync`: en `opencode.json`, `build` debe tener `codebase-memory_*: true` y las 4 de escritura en `false`, como los demás agentes de consulta. Si `sync` o su validación asumen que `agentes_escritura` no está vacío, corregirlos. Verificar con `python3 -c "import json;print(json.load(open('opencode.json'))['agent']['build'])"`
- [ ] 12.2 Actualizar los tests 9.1 y 9.2 al nuevo contrato: ningún agente recibe herramientas de escritura y la lista vacía es válida. Añadir un caso con `agentes_escritura` no vacío para que la rama siga cubierta. Verificar con el selftest enfocado en esas clases
- [ ] 12.3 Repetir la Revisión 1 (@revisor-gratis) y la 2 (@revisor-fuerte) sobre el commit final, porque la evidencia queda atada al commit, y registrarlas; si aprueban, hacer 11.3. Verificar con `python3 scripts/harness.py revision listar` (las dos vigentes y en APROBAR)

## 11. Prueba de humo e integración (build)

- [x] 11.1 `bash scripts/bootstrap.sh "$(mktemp -d)/demo"` → en el destino: `python3 scripts/harness.py sync --check`, `bash scripts/cbm-instalar.sh`, `bash scripts/cbm-indexar.sh` y `scripts/cbm cli --quiet list_projects` muestra el repo; verificar con la salida pegada en HANDOFF.md
- [x] 11.2 Selftest completo y doctor en verde en este repo; verificar con `python3 scripts/harness.py doctor --tests`
- [ ] 11.3 Push de la rama, PR listo (`gh pr ready`) con la salida de `revision listar` (revisiones 1, 2 y 3 por riesgo alto); verificar con `gh pr checks` (el merge y la aprobación humana los hace el usuario vía `/juzgar-pr`; el cambio llega a los proyectos cuando está en `main`, que es de donde copia `bootstrap.sh`)
