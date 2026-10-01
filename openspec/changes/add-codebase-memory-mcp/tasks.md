> **Cómo se ejecuta este change.** Casi todo es plano de control, que el contenedor monta en solo lectura, así que el ejecutor corre **fuera del contenedor y con override**: `HARNESS_OVERRIDE=1 scripts/ejec` → `/ejecutar-cambio add-codebase-memory-mcp`. Los commits quedan marcados con `Harness-Override: yes` y el PR exige aprobación humana.
> El grupo 0 lo hace el arquitecto en el PR de la propuesta. Si una tarea revela un hueco del spec, escríbelo en HANDOFF.md y detente.

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

## 3. Envoltorio y configuración aislada

- [ ] 3.1 `scripts/cbm` según D4 y D5 (interruptor, resolución de binario por plataforma con comprobación de versión, caché y config por entorno `host`/`contenedor`, `verificar-secretos` al arrancar como servidor, `auto_index` y `watcher_enabled` apagados de forma idempotente, `exec "$@"`); verificar con `scripts/cbm cli --quiet list_projects` (código 0), con `habilitado:false` (código 1 y mensaje), comprobando que `~/.config/codebase-memory-mcp/config.json` no cambió (compara `stat` antes y después), y con un `.env` sin excluir (arrancar sin argumentos sale con 1 y nombra el archivo)
- [ ] 3.2 Prueba de comportamiento de D5: con `auto_index=true` en una config «global» simulada (`HOME` temporal), arrancar `scripts/cbm` como servidor sobre un repo sin índice, esperar 10 s y cerrarlo; verificar que la caché del entorno sigue sin índice (`scripts/cbm cli --quiet list_projects` no lista el repo)
- [ ] 3.3 Ruta con espacios: clonar el repo en un temporal con espacios en la ruta y arrancar el servidor con el `command` exacto que `sync` genera para OpenCode y para Claude (`${CLAUDE_PROJECT_DIR}` sustituido); verificar que los dos responden a `list_projects`

## 4. Secretos fuera del índice

- [ ] 4.1 `harness.py cbm verificar-secretos` según D6 (`listar_secretos` + `git -c core.excludesFile=.cbmignore check-ignore --no-index -q`); código 0 si todo está excluido, 1 nombrando los archivos si no; verificar con el test 9.3
- [ ] 4.2 Invalidación de D6: guardar `cbmignore.sha256` tras cada indexado correcto; si difiere, borrar la caché del entorno antes de indexar; verificar con el test 9.6
- [ ] 4.3 Prueba real: con `.env` y `tmp/x.pem` de prueba en el repo, indexar y buscar con `scripts/cbm cli --quiet search_code` el contenido de esos archivos; verificar que no aparecen y borrar los archivos de prueba

## 5. Adaptadores generados por sync

- [ ] 5.1 `sync` genera o retira `.mcp.json` (solo `mcpServers.codebase-memory`, conservando otros servidores y borrando el archivo si queda vacío) según D1; verificar con el test 9.1
- [ ] 5.2 `sync` genera o retira en `opencode.json` las claves `mcp.codebase-memory`, `tools["codebase-memory_<w>"]=false` y `agent.<a>.tools[...]=true` para `agentes_escritura` según D1, sin tocar otras claves; verificar con el test 9.1
- [ ] 5.3 `sync` genera o retira `.cbmignore` con cabecera `GENERADO` desde `ignorar`; verificar con el test 9.1
- [ ] 5.4 `generar_rutas` añade a `docs/harness/RUTAS.md` una sección «Memoria de código» (estado, versión, quién escribe); verificar con `python3 scripts/harness.py sync && grep -n "Memoria de código" docs/harness/RUTAS.md`
- [ ] 5.5 Correr `python3 scripts/harness.py sync` y commitear los adaptadores generados; verificar con `python3 scripts/harness.py sync --check` (código 0)

## 6. Claude Code

- [ ] 6.1 `.claude/settings.json`: `permissions.deny` con 4 reglas literales (`mcp__codebase-memory__index_repository`, `mcp__codebase-memory__delete_project`, `mcp__codebase-memory__manage_adr` y `mcp__codebase-memory__ingest_traces`, sin llaves ni comodines), `enabledMcpjsonServers: ["codebase-memory"]` y `sandbox.filesystem.denyWrite` con `./.mcp.json`, `./.cbmignore` y `./scripts` (ya está); verificar con el test 9.2 y, en una sesión de Claude Code, que `delete_project` se deniega y `list_projects` responde (manual)

## 7. Re-indexado

- [ ] 7.1 `scripts/cbm-indexar.sh [--fondo]` según D7 (interruptor, lock por entorno con mkdir y PID y limpieza de huérfanos, `verificar-secretos`, invalidación, `index_repository`, log en `.harness/cbm/<entorno>/ultimo-indexado.log`); verificar en primer plano (código 0) y con `--fondo` (vuelve en < 1 s, `time bash scripts/cbm-indexar.sh --fondo`)
- [ ] 7.2 `.githooks/post-merge` y `.githooks/post-checkout` (este último solo con `$3 = 1` y sin rebase en curso), ejecutables, siempre `exit 0` y sin salida; verificar con el test 9.7 y a mano: `git switch -c tmp-cbm && git switch -` (log nuevo), `git checkout -- README.md` (sin log nuevo), `git worktree add ../wt-cbm -b tmp-wt` (log nuevo en `../wt-cbm/.harness/cbm/host/`), un `git rebase` (sin indexado a mitad) y con el binario renombrado (git no muestra errores)
- [ ] 7.3 Dos disparos seguidos no lanzan dos indexados; verificar con `bash scripts/cbm-indexar.sh --fondo; bash scripts/cbm-indexar.sh --fondo; pgrep -fc "index_repository"` (≤ 1)

## 8. Contenedor del ejecutor

- [ ] 8.1 `.harness/contenedor/Dockerfile` según D8 (`curl` en apt, build-args sin defecto, `sha256sum -c`, instalación en `/usr/local/bin` y `ENV HARNESS_CONTENEDOR=1`); verificar además que dentro del contenedor la caché es `.harness/cbm/contenedor/`; verificar con `scripts/ejec-contenedor --rebuild --shell` → `scripts/cbm cli --quiet list_projects` (manual)
- [ ] 8.2 `scripts/ejec-contenedor`: build-args desde `versiones.json`, etiqueta `harness-ejecutor:<opencode>-cbm<cbm>` y `.mcp.json` y `.cbmignore` en los montajes de solo lectura; verificar con `docker image ls harness-ejecutor` tras la build y cambiando la versión en una copia local (pide build nueva sin `--rebuild`)

## 9. Selftest (`scripts/test_harness.py`)

- [ ] 9.1 Tests de `sync`: encendido genera `.mcp.json`, las claves de `opencode.json` y `.cbmignore`; apagado los retira; conserva otros servidores y claves; `sync --check` detecta la deriva; verificar con `python3 -m unittest discover -s scripts -p 'test_*.py'`
- [ ] 9.2 Test: `.claude/settings.json → permissions.deny` contiene literalmente `mcp__<servidor>__<w>` para cada herramienta de `herramientas_escritura` (sin llaves ni comodines), y `opencode.json` las veta globalmente y las abre solo a `agentes_escritura`; verificar con el selftest
- [ ] 9.3 Test: por cada regex de `secretos.rutas` se crea un archivo de ejemplo y `verificar-secretos` pasa con el `ignorar` por defecto; con un patrón quitado de `.cbmignore`, falla nombrando el archivo; un `.gitignore` anidado que reincluye un secreto con `!` hace fallar la verificación; un excludes global del usuario (`core.excludesFile`) que sí lo cubriría no cambia el resultado; `.env.example` no cuenta como secreto; verificar con el selftest
- [ ] 9.4 Test: con `habilitado: false`, `cbm-indexar.sh --fondo` y los hooks salen con 0 sin crear ningún `ultimo-indexado.log` bajo `.harness/cbm/`; verificar con el selftest
- [ ] 9.6 Test de invalidación con un binario falso (script que registra sus argumentos): cambiar `.cbmignore` entre dos indexados borra la caché del entorno antes del segundo; sin cambios, no la borra; verificar con el selftest
- [ ] 9.7 Test de hooks con el mismo binario falso: `post-checkout` con `$3=0` no lanza nada; con `$3=1` lanza; con `.git/rebase-merge` presente no lanza; dos disparos seguidos con el lock tomado lanzan uno; los dos hooks salen con 0 aunque `cbm-indexar.sh` falle; verificar con el selftest
- [ ] 9.5 Ampliar `TestEmpaquetado` y `test_contenedor_monta_control_plane_solo_lectura` con los nuevos scripts, hooks y montajes; verificar con el selftest

## 10. Diagnóstico y empaquetado

- [ ] 10.1 `doctor` según el requisito «Diagnóstico de la memoria de código» (binario y versión, `verificar-secretos`, hooks ejecutables, existencia del índice; apagado → una línea ok); `harness.py versiones` lista también `binarios`; verificar con `python3 scripts/harness.py doctor` en los dos estados del interruptor
- [ ] 10.2 `scripts/bootstrap.sh` (archivos nuevos y líneas de `.gitignore`) e `instalar-frameworks.sh` (llama a `cbm-instalar.sh` si está encendido), según D9; verificar con el test 11.1
- [ ] 10.3 Actualizar el docstring de uso de `harness.py` con el subcomando `cbm`; verificar con `python3 scripts/harness.py | grep cbm`

## 11. Prueba de humo e integración

- [ ] 11.1 `bash scripts/bootstrap.sh "$(mktemp -d)/demo"` → en el destino: `python3 scripts/harness.py sync --check`, `bash scripts/cbm-instalar.sh`, `bash scripts/cbm-indexar.sh` y `scripts/cbm cli --quiet list_projects` muestra el repo; verificar con la salida pegada en HANDOFF.md
- [ ] 11.2 Selftest completo y doctor en verde en este repo; verificar con `python3 scripts/harness.py doctor --tests`
- [ ] 11.3 Push de la rama, PR listo (`gh pr ready`) con la salida de `revision listar` (revisiones 1, 2 y 3 por riesgo alto); verificar con `gh pr checks` (el merge y la aprobación humana los hace el usuario vía `/juzgar-pr`; el cambio llega a los proyectos cuando está en `main`, que es de donde copia `bootstrap.sh`)
