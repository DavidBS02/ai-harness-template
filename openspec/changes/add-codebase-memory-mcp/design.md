## Origen (dossier en lugar de BMAD)

El Nivel 3 lo fuerza el gate porque el change toca el plano de control. Se omite la sesión BMAD previa por decisión del usuario (2026-10-01): no hay producto ni AD de una app que decidir, es tooling del propio template. El dossier son los 8 puntos del pedido original (issue #2) más estas decisiones del usuario:

- Versión fijada **v0.11.0** en lugar de v0.7.0. v0.7.0 es de mayo de 2025 y no se pudo verificar que tenga `cli`, `auto_index` ni `CBM_CACHE_DIR`.
- Escritura del índice: **todos los agentes menos `build`** quedan en solo consulta. Se amplía la lista inicial de tres revisores por mínimo privilegio.

## Context

Muestras reales verificadas el 2026-10-01 (docs/LECCIONES.md §2):

- **Release v0.11.0** (15 sep 2026), `checksums.txt` leído literal con `curl`:
  ```
  dbf1c73bfcbde64e7dde4cd1320da7afc02e2c972ee1789ae039521411f5132e  codebase-memory-mcp-darwin-amd64.tar.gz
  4dee7f38b63740e6751d7a7ed7eb10291c1f2a3ea2415f599dc68370ca0a2d18  codebase-memory-mcp-darwin-arm64.tar.gz
  032b33c1833919a2d1de67ff6367fa6ea46aee8689c86ef223c88fae3b6e4536  codebase-memory-mcp-linux-amd64.tar.gz
  c0e46c87cf37e35f1ac0bd9cc7e1d8b0ca4ef40034e1008805d709fa52a4e38a  codebase-memory-mcp-linux-arm64.tar.gz
  ```
  URL: `https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.11.0/codebase-memory-mcp-<os>-<arch>.tar.gz`. La release también publica `checksums.txt.bundle` (firma); verificarla queda fuera de este change.
- **README del servidor**: sin argumentos sirve MCP por stdio. CLI: `codebase-memory-mcp cli [--quiet] <tool> [flags]` (p. ej. `cli index_repository --repo-path /abs`). Config: `codebase-memory-mcp config set auto_index false`, guardada en `~/.config/codebase-memory-mcp/config.json`; claves relevantes `auto_index` y `watcher_enabled`. Caché: `CBM_CACHE_DIR` (por defecto `~/.cache/codebase-memory-mcp`). Exclusiones por capas: patrones fijos (`.git`, `node_modules`…), luego jerarquía de `.gitignore`, luego `.cbmignore` (sintaxis gitignore); los symlinks se saltan siempre. `.codebase-memory/` solo se escribe con `persistence: true`.
- **17 herramientas MCP.** Escritura: `index_repository`, `delete_project`, `manage_adr` e `ingest_traces`. Consulta: `search_graph`, `trace_path`, `detect_changes`, `query_graph`, `get_graph_schema`, `compare_graphs`, `get_code_snippet`, `get_file_outline`, `get_architecture`, `search_code`, `list_projects`, `index_status` y `check_index_coverage`.
- **Claude Code** (`.mcp.json`): `{"mcpServers": {"<n>": {"command", "args", "env"}}}`, con expansión de `${CLAUDE_PROJECT_DIR}` en `command` y `env`. Los servidores de proyecto piden aprobación salvo que estén en `enabledMcpjsonServers` de `.claude/settings.json`. Las herramientas se nombran `mcp__<servidor>__<tool>` en `permissions.deny`.
- **OpenCode** (`opencode.json`): `"mcp": {"<n>": {"type": "local", "command": [...], "environment": {...}, "enabled": true}}`. Las herramientas se nombran `<servidor>_<tool>`. Patrón documentado de veto: `"tools": {"<glob>": false}` global y `"agent": {"<a>": {"tools": {"<glob>": true}}}` para habilitar por agente.

Estado actual del harness: `sync` ya regenera `opencode.json` (modelo y proveedor) y el frontmatter `model:` de los agentes; `doctor` ya verifica versiones fijadas; el contenedor monta el plano de control en solo lectura y enmascara secretos; `secretos.rutas` son regex, no globs.

## Goals / Non-Goals

**Goals:**
- Que un solo dato (`habilitado`) decida todo, y que apagarlo no deje restos activos.
- Que la confianza en el binario venga del checksum fijado, no de la red ni de un instalador de terceros.
- Que el veto de escritura no dependa de recordar añadir cada agente nuevo.

**Non-Goals:**
- Medir el ahorro de tokens.
- Cambiar los prompts de los comandos para que usen la memoria.
- Verificar la firma Sigstore (`checksums.txt.bundle`).

## Decisions

### D1. Datos en `harness.json`, adaptadores generados por `sync`
`harness.json → mcp.codebase_memory` contiene `habilitado`, `servidor` (`codebase-memory`, el prefijo de las herramientas), `cache_dir`, `config_dir`, `agentes_escritura` (`["build"]`), `herramientas_escritura` e `ignorar` (patrones gitignore). `sync` es el único que escribe:
- `.mcp.json`: solo la clave `mcpServers.codebase-memory` (`command: "${CLAUDE_PROJECT_DIR}/scripts/cbm"`). Conserva cualquier otro servidor y, si el archivo queda sin servidores, lo borra.
- `opencode.json`: `mcp.codebase-memory` (`type: local`, `command: ["sh", "-c", "exec \"$(git rev-parse --show-toplevel)/scripts/cbm\""]`, `enabled: true`). Además, `tools` con `"codebase-memory_<w>": false` por cada herramienta de escritura, y `agent.<a>.tools` con `true` para cada agente de `agentes_escritura`. Solo toca esas claves.
- `.cbmignore`: cabecera `GENERADO` más `ignorar`.

Con `habilitado: false`, `sync` retira exactamente esas claves y el archivo `.cbmignore`. `sync --check` detecta la deriva igual que hoy.

*Alternativa descartada:* poner el veto en el frontmatter de cada `.opencode/agents/*.md`. Es una lista que hay que mantener, no cubre los subagentes integrados de OpenCode (`general`) y no cubre agentes nuevos.

### D2. Permisos de Claude Code: estáticos en `.claude/settings.json`
`permissions.deny` añade `mcp__codebase-memory__{index_repository,delete_project,manage_adr,ingest_traces}`, y `enabledMcpjsonServers: ["codebase-memory"]` evita el aviso de aprobación. Es seguro porque el binario está fijado por checksum. Se deja estático (sync no reescribe `settings.json`). Un test verifica que `deny` cubre `herramientas_escritura`. Si la memoria está apagada, esas entradas no afectan a nada.

### D3. Binario: instalación propia con checksum, por plataforma
- `.harness/versiones.json → binarios.codebase-memory-mcp`: `version`, `url` (plantilla con `{version}`, `{os}` y `{arch}`) y `sha256` por `<os>-<arch>` (los 4 valores de Context).
- `scripts/cbm-instalar.sh`: detecta `os` (`darwin`/`linux`) y `arch` (`amd64`/`arm64`). Descarga a un temporal, compara el SHA-256 (`shasum -a 256` o `sha256sum`) y solo si coincide extrae a `.harness/bin/<os>-<arch>/codebase-memory-mcp`. Si falla, borra el temporal y sale con código ≠ 0. La descarga es con `curl -fsSL -o`, sin pipe a shell. Es idempotente: si ya está la versión fijada, no descarga.
- El directorio es por plataforma porque el contenedor (linux) monta el mismo repo que el host (darwin). Un binario único en `.harness/bin/` rompería uno de los dos.

### D4. Envoltorio `scripts/cbm`
Es el punto de entrada único: lo arrancan los dos MCP, los scripts y los humanos. Hace esto:
1. Sale con código 1 y un mensaje si `habilitado` es false.
2. Resuelve el binario: primero `.harness/bin/<os>-<arch>/`; si no existe, `/usr/local/bin/codebase-memory-mcp` (el del contenedor). En los dos casos exige que la versión coincida con la fijada; si no, sale con código 1 y el comando para reinstalar.
3. Exporta `CBM_CACHE_DIR=<raíz>/.harness/cbm` y aísla la configuración del servidor en `<raíz>/.harness/cbm/config` (D5).
4. Asegura `auto_index=false` y `watcher_enabled=false` de forma idempotente, con un marcador de versión en `config_dir` para no repetirlo en cada arranque.
5. Hace `exec` del binario con `"$@"`.

Lee `harness.json` con `python3` (ya es requisito del harness).

### D5. Configuración aislada por repo
El servidor guarda su config en `~/.config/codebase-memory-mcp/`. Para no tocar la del usuario ni la de otros repos, `scripts/cbm` exporta `XDG_CONFIG_HOME=<raíz>/.harness/cbm/config`. Si la tarea 1.2 muestra que el binario ignora `XDG_CONFIG_HOME`, el fallback es `HOME=<raíz>/.harness/cbm/home`, solo para el proceso del servidor. Las dos variantes dejan todo dentro de `.harness/cbm/`, que ya está ignorado.

### D6. Exclusión de secretos con verificación fail-closed
`secretos.rutas` son regex y `.cbmignore` usa sintaxis gitignore. No hay conversión automática fiable, así que:
- `mcp.codebase_memory.ignorar` lleva patrones gitignore escritos a mano que reflejan `secretos.rutas` (`.env`, `.env.*`, `!.env.example`, `!.env.sample`, `!.env.template`, `.ssh/`, `.aws/`, `.kube/`, `.gnupg/`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.keystore`, `*.jks`, `id_rsa`, `id_dsa`, `id_ecdsa`, `id_ed25519`, `credentials.json`, `service-account*.json`, `client_secret*.json`, `.npmrc`, `.netrc`, `.pypirc`, `.git-credentials`, `.docker/config.json`, `.config/gh/`), más `.harness/cbm/`, `.harness/bin/` y `.codebase-memory/`.
- `harness.py cbm verificar-secretos` recorre los archivos secretos reales del repo (`listar_secretos`) y comprueba cada uno con `git -c core.excludesFile=.cbmignore check-ignore --no-index -q <archivo>`. Eso imita las capas del servidor: `.gitignore` jerárquico más `.cbmignore`. Si alguno no queda excluido, falla y lo nombra.
- `cbm-indexar.sh` corre esa verificación antes de cada indexado; `doctor` también.
- Un test de unidad crea un archivo de ejemplo por cada regex de `secretos.rutas` y exige que la verificación pase con el `ignorar` por defecto. Así, si alguien añade un regex en `secretos` y olvida su patrón en `ignorar`, el selftest falla.

*Alternativa descartada:* traducir los regex a globs. Es frágil y daría una falsa sensación de cobertura.

### D7. Re-indexado: hooks finos, lógica en `scripts/cbm-indexar.sh`
- `.githooks/post-merge` llama a `scripts/cbm-indexar.sh --fondo`. `.githooks/post-checkout` hace lo mismo, pero solo si `$3 = 1` (cambio de rama). Los dos terminan con `|| true; exit 0` y no imprimen nada.
- `cbm-indexar.sh [--fondo]`:
  1. Si la memoria está apagada, sale con 0 (en primer plano, con un mensaje de cómo encenderla).
  2. Toma el lock con `mkdir .harness/cbm/indexando.lock` y guarda el PID. Un lock con PID muerto, o de más de 30 minutos, se considera huérfano y se retira.
  3. Corre `verificar-secretos`.
  4. Corre `scripts/cbm cli --quiet index_repository --repo-path <raíz>`.
  5. Con `--fondo`, todo lo anterior va desacoplado (`nohup … &`, stdout/stderr a `.harness/cbm/ultimo-indexado.log`) y el script vuelve de inmediato con 0. Sin `--fondo`, propaga el código de salida.
- Se elige git hooks en lugar de `auto_index` o watcher del servidor porque el harness controla cuándo se indexa (después de la verificación de secretos) y el servidor no arranca indexados por su cuenta.

### D8. Contenedor
El Dockerfile recibe `CBM_VERSION`, `CBM_SHA256_AMD64` y `CBM_SHA256_ARM64` como build-args (sin valores por defecto, como `OPENCODE_VERSION`). Elige la arquitectura con `dpkg --print-architecture`, descarga con `curl`, verifica con `sha256sum -c` e instala en `/usr/local/bin/codebase-memory-mcp`. Hay que añadir `curl` al `apt-get install`. `ejec-contenedor` lee esos valores de `versiones.json` y etiqueta la imagen `harness-ejecutor:<opencode>-cbm<cbm>`, así que un upgrade fuerza la build. Además añade `.mcp.json` y `.cbmignore` a los montajes de solo lectura; `.harness/cbm/` queda escribible para que `build` pueda indexar.

### D9. Plano de control y empaquetado
- `control_plane.rutas` añade `^scripts/cbm(-[a-z]+\.sh)?$`, `^\.mcp\.json$` y `^\.cbmignore$`. Los scripts de la memoria deciden qué se indexa, así que su modificación exige aprobación humana.
- `.claude/settings.json → sandbox.filesystem.denyWrite` añade esos mismos tres.
- `bootstrap.sh` copia `scripts/cbm`, `scripts/cbm-instalar.sh`, `scripts/cbm-indexar.sh`, `.githooks/post-merge` y `.githooks/post-checkout`, y añade al `.gitignore` destino las líneas de `.harness/cbm/`, `.harness/bin/` y `.codebase-memory/`. `.mcp.json` y `.cbmignore` los genera el `sync` que bootstrap ya corre.
- `instalar-frameworks.sh` llama a `scripts/cbm-instalar.sh` si la memoria está encendida.

### D10. Método
- `/init-harness` añade el paso «Memoria de código»: con la memoria encendida, `bash scripts/cbm-instalar.sh`, `python3 scripts/harness.py cbm verificar-secretos`, `bash scripts/cbm-indexar.sh` (en primer plano) y comprobación con `scripts/cbm cli --quiet list_projects`. Claude Code lo corre por Bash, porque los scripts del harness sí pueden escribir; las herramientas MCP de escritura siguen vetadas para Claude.
- `/descubrir` añade el paso «¿Memoria de código?» antes de aplicar `/init-harness`, con los criterios del spec. La decisión queda en la sección `## Memoria de código` de `docs/harness/MAPA.md`; en un proyecto verde, además, abre un issue `verificacion-diferida`.

## Risks / Trade-offs

- [Supply chain: el checksum viene de la misma release que el binario] → Se fija una vez y se versiona: un cambio posterior en la release no pasa la verificación. Los upgrades son PRs del plano de control con aprobación humana. La firma Sigstore queda para un change posterior.
- [Un secreto con un nombre no previsto se indexa] → El indexador respeta `.gitignore`, `verificar-secretos` cubre todo lo que `secretos` reconoce y un test ata `ignorar` a `secretos.rutas`. Lo que `secretos` no reconoce tampoco lo protegen hoy las demás guardias. Es la misma frontera de siempre, documentada en SEGURIDAD.md.
- [Un indexado en segundo plano consume CPU tras cada pull] → Hay lock (nunca dos a la vez) y el índice es incremental. Si molesta, `habilitado: false`.
- [El caché `.harness/cbm/` es compartido entre host y contenedor] → Es la misma versión y la misma ruta de repo (el contenedor monta la ruta idéntica), y el lock evita escrituras concurrentes desde los hooks. Un `index_repository` de `build` simultáneo a un hook del host es un riesgo residual; el servidor usa SQLite con su propio bloqueo.
- [OpenCode cambia el esquema de `tools` o `agent.tools`] → La versión de OpenCode está fijada (1.18.33). La tarea 1.3 lo verifica sobre esa versión real; si difiere, se usa la clave `permission` equivalente y se anota en HANDOFF.md.

## Migration Plan

Los repos que ya usan el harness reciben el cambio por `bootstrap.sh`, que deja los archivos en `.harness/entrantes/` cuando ya existen, y por `/init-harness`. El interruptor viene encendido, pero el MCP no hace nada útil hasta que se instala el binario: `doctor` lo avisa. Para revertir: `habilitado: false` + `sync`, y opcionalmente `rm -rf .harness/cbm .harness/bin`.

## Open Questions

Son diferibles: ninguna cambia los specs, el enfoque ni el desglose. Cada una tiene su fallback y se resuelve en el grupo 1 de tareas.
- ¿Respeta v0.11.0 `XDG_CONFIG_HOME`? Fallback: `HOME` aislado (D5).
- ¿Qué imprime `--version` (o el subcomando equivalente) para comparar la versión? El envoltorio extrae `\d+\.\d+\.\d+`.
- ¿OpenCode 1.18.33 aplica `tools` global más `agent.build.tools` como dice su documentación, con el prefijo `codebase-memory_`? Fallback: clave `permission`.
