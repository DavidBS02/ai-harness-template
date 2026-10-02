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
`harness.json → mcp.codebase_memory` contiene `habilitado`, `servidor` (`codebase-memory`, el prefijo de las herramientas), `cache_dir` (caché del usuario compartida por todos los repos, D4), `estado_dir` (`.harness/cbm`, estado local del repo), `agentes_consulta`, `agentes_escritura` (`["build"]`), `herramientas_escritura` e `ignorar` (patrones gitignore). `sync` es el único que escribe:
- `.mcp.json`: solo la clave `mcpServers.codebase-memory` (`command: "${CLAUDE_PROJECT_DIR}/scripts/cbm"`). Conserva cualquier otro servidor y, si el archivo queda sin servidores, lo borra.
- `opencode.json`: `mcp.codebase-memory` (`type: local`, `command: ["sh", "-c", "exec \"$(git rev-parse --show-toplevel)/scripts/cbm\""]`, `enabled: true`). Los vetos van en dos capas:
  - `tools` global con `"codebase-memory_*": false`, así nadie recibe el servidor por defecto.
  - `agent.<a>.tools` con `"codebase-memory_*": true` para cada agente de `agentes_consulta`. A los que no están en `agentes_escritura` (por defecto, todos: ver «Revisión del 2026-10-02») se les añade además `"codebase-memory_<w>": false` por cada herramienta de escritura. `agentes_escritura` debe estar contenido en `agentes_consulta`, y `sync` falla si no lo está.

  Solo toca esas claves. Motivo: la definición de las 17 herramientas viaja en cada paso de cada agente que las recibe, así que se le quitan por completo a quien no explora (`@mecanico`).
- `.cbmignore`: cabecera `GENERADO` más `ignorar`.

Con `habilitado: false`, `sync` retira exactamente esas claves y el archivo `.cbmignore`. `sync --check` detecta la deriva igual que hoy.

*Alternativa descartada:* poner el veto en el frontmatter de cada `.opencode/agents/*.md`. Es una lista que hay que mantener, no cubre los subagentes integrados de OpenCode (`general`) y no cubre agentes nuevos.

### D2. Permisos de Claude Code: estáticos en `.claude/settings.json`
`permissions.deny` añade cuatro reglas literales, una por herramienta y sin abreviaturas ni llaves: `mcp__codebase-memory__index_repository`, `mcp__codebase-memory__delete_project`, `mcp__codebase-memory__manage_adr` y `mcp__codebase-memory__ingest_traces`. `enabledMcpjsonServers: ["codebase-memory"]` evita el aviso de aprobación; es seguro porque el binario está fijado por checksum y `scripts/cbm` verifica secretos antes de arrancar. Se deja estático (sync no reescribe `settings.json`). Un test exige que `deny` contenga literalmente `mcp__<servidor>__<w>` para cada `herramientas_escritura`. Con la memoria apagada esas entradas quedan inertes; el spec lo permite de forma explícita.

### D3. Binario: instalación propia con checksum, por plataforma
- `.harness/versiones.json → binarios.codebase-memory-mcp`: `version`, `url` (plantilla con `{version}`, `{os}` y `{arch}`) y `sha256` por `<os>-<arch>` (los 4 valores de Context).
- `scripts/cbm-instalar.sh`: detecta `os` (`darwin`/`linux`) y `arch` (`amd64`/`arm64`). Descarga a un temporal, compara el SHA-256 (`shasum -a 256` o `sha256sum`) y solo si coincide extrae a `.harness/bin/<os>-<arch>/codebase-memory-mcp`. Si falla, borra el temporal y sale con código ≠ 0. La descarga es con `curl -fsSL -o`, sin pipe a shell. Es idempotente: si ya está la versión fijada, no descarga.
- El directorio es por plataforma para que un repo compartido entre máquinas (por ejemplo, macOS y Linux) no use el binario de la otra.

### D4. Envoltorio `scripts/cbm`
Es el punto de entrada único: lo arrancan los dos MCP, los scripts y los humanos. Hace esto:
1. Sale con código 1 y un mensaje si `habilitado` es false.
2. Resuelve el binario en `.harness/bin/<os>-<arch>/` y exige que su versión coincida con la fijada. Si falta o difiere, sale con código 1 y el comando para reinstalar. Dentro del contenedor no hay binario, así que sale con 1 explicándolo.
3. Exporta `CBM_CACHE_DIR=<cache_dir>` (por defecto `${XDG_CACHE_HOME:-$HOME/.cache}/ai-harness/cbm`) y `HOME=<cache_dir>/home` solo para el proceso del servidor (D5). **Una sola caché para todos los repos** porque v0.11.0 admite un solo daemon por usuario y se niega a arrancar si otro daemon vivo usa otro `CBM_CACHE_DIR` (hallazgo de la sesión S1). Con una caché por repo, dos proyectos o dos worktrees no podrían tener memoria a la vez. El servidor ya separa los proyectos por la ruta absoluta del repo.
4. Si no hay argumentos (arranque como servidor MCP): corre `harness.py cbm verificar-secretos` y sale con código 1 si falla, para que el servidor no sirva consultas mientras haya un secreto sin excluir.
5. Asegura `auto_index=false` y `watcher_enabled=false` de forma idempotente, con un marcador `<config>/.harness-config-<version>` para no repetirlo en cada arranque.
6. Hace `exec` del binario con `"$@"`.

Lee `harness.json` con `python3` (ya es requisito del harness).

### D5. Configuración aislada del usuario, compartida por el harness
La tarea 1.2 mostró que v0.11.0 ignora `XDG_CONFIG_HOME` y guarda la config en `$CBM_CACHE_DIR/_config.db`. Por eso aislar la caché ya aísla la config: la del harness vive en `<cache_dir>/_config.db` y es común a todos los repos con harness (`auto_index` y `watcher_enabled` en `false`), sin tocar `~/.cache/codebase-memory-mcp/` del usuario. El `HOME` aislado (`<cache_dir>/home`) es una red de seguridad por si el binario escribe algo más bajo `$HOME`. La prueba de aceptación es de comportamiento: con la config propia del usuario en `auto_index=true`, un arranque vía `scripts/cbm` no indexa (verificado en 3.2 con la caché por repo; se repite con la compartida).

### D6. Exclusión de secretos con verificación fail-closed
`secretos.rutas` son regex y `.cbmignore` usa sintaxis gitignore. No hay conversión automática fiable, así que:
- `mcp.codebase_memory.ignorar` lleva patrones gitignore escritos a mano que reflejan `secretos.rutas` (`.env`, `.env.*`, `!.env.example`, `!.env.sample`, `!.env.template`, `.ssh/`, `.aws/`, `.kube/`, `.gnupg/`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.keystore`, `*.jks`, `id_rsa`, `id_dsa`, `id_ecdsa`, `id_ed25519`, `credentials.json`, `service-account*.json`, `client_secret*.json`, `.npmrc`, `.netrc`, `.pypirc`, `.git-credentials`, `.docker/config.json`, `.config/gh/`), más `.harness/cbm/`, `.harness/bin/` y `.codebase-memory/`.
- `harness.py cbm verificar-secretos` recorre los archivos secretos reales del repo (`listar_secretos`) y comprueba cada uno con `git -c core.excludesFile=.cbmignore check-ignore --no-index -q <archivo>`. Eso imita las capas del servidor: `.gitignore` jerárquico más `.cbmignore`. Si alguno no queda excluido, falla y lo nombra.
- Por qué `-c core.excludesFile=.cbmignore`: reemplaza a propósito el excludes global del usuario, porque el indexador no lo lee. Si se contara, un secreto excluido solo por el global saldría como «excluido» mientras el indexador sí lo indexa (falso negativo). Lo que sí se respeta es la jerarquía de `.gitignore` del repo, igual que el indexador; `--no-index` hace que la comprobación valga también para archivos versionados.
- `cbm-indexar.sh` corre esa verificación antes de cada indexado; `scripts/cbm` la corre al arrancar el servidor (D4); `doctor` también.
- Invalidación: tras cada indexado correcto se guarda el SHA-256 de `.cbmignore` en `.harness/cbm/cbmignore.sha256` del repo (`harness.py cbm marcar-indexado`). Si antes de indexar no coincide (`harness.py cbm invalidar-cache`), se borra **solo el proyecto de este repo** de la caché compartida (`scripts/cbm cli --quiet delete_project` con el nombre del proyecto) y se indexa en frío. Así ningún archivo recién excluido sobrevive en un índice viejo, y los demás repos no se tocan. Es necesario porque el re-indexado del CLI es incremental y no reevalúa lo ya indexado (hallazgo de S1).
- Un test de unidad crea un archivo de ejemplo por cada regex de `secretos.rutas` y exige que la verificación pase con el `ignorar` por defecto. Así, si alguien añade un regex en `secretos` y olvida su patrón en `ignorar`, el selftest falla.

*Alternativa descartada:* traducir los regex a globs. Es frágil y daría una falsa sensación de cobertura.

### D7. Re-indexado: hooks finos, lógica en `scripts/cbm-indexar.sh`
- `.githooks/post-merge` llama a `scripts/cbm-indexar.sh --fondo`. `.githooks/post-checkout` hace lo mismo, pero solo si `$3 = 1` (cambio de rama: `checkout`, `switch` y `worktree add`, que dispara `post-checkout` en el worktree nuevo, con su propia raíz y su propio estado en `.harness/cbm/`; en el índice compartido es otro proyecto). Los dos terminan con `|| true; exit 0` y no imprimen nada. `rebase` y `pull --rebase` quedan fuera a propósito: `post-checkout` salta a mitad del rebase con `$3=1`, y para no indexar un estado intermedio el hook no hace nada si existe `.git/rebase-merge` o `.git/rebase-apply` (en un worktree, bajo `git rev-parse --git-dir`). Esos casos se re-indexan con `cbm-indexar.sh`.
- `cbm-indexar.sh [--fondo]`:
  1. Si la memoria está apagada, sale con 0 (en primer plano, con un mensaje de cómo encenderla).
  2. Toma el lock con `mkdir .harness/cbm/indexando.lock` y guarda el PID. Un lock con PID muerto, o de más de 30 minutos, se considera huérfano y se retira.
  3. Corre `verificar-secretos` y la invalidación de D6.
  4. Corre `scripts/cbm cli --quiet index_repository --repo-path <raíz>`.
  5. Con `--fondo`, todo lo anterior va desacoplado (`nohup … &`, stdout/stderr a `.harness/cbm/ultimo-indexado.log`) y el script vuelve de inmediato con 0. Sin `--fondo`, propaga el código de salida.
- Se elige git hooks en lugar de `auto_index` o watcher del servidor porque el harness controla cuándo se indexa (después de la verificación de secretos) y el servidor no arranca indexados por su cuenta.

### D8. Contenedor: fuera de este change (recorte del 2026-10-01)
Por prioridad de costo y velocidad, el usuario recortó el soporte en el contenedor. En `scripts/ejec-contenedor` el servidor no arranca (no hay binario) y OpenCode sigue sin memoria; `scripts/cbm` lo explica. Hacerlo después exigirá montar la caché compartida del usuario en el contenedor y resolver el daemon único (D4), además de instalar el binario con checksum en la imagen.

### D9. Plano de control y empaquetado
- `control_plane.rutas` añade `^scripts/cbm(-[a-z]+\.sh)?$`, `^\.mcp\.json$` y `^\.cbmignore$`. Los scripts de la memoria deciden qué se indexa, así que su modificación exige aprobación humana.
- `.claude/settings.json → sandbox.filesystem.denyWrite` añade esos mismos tres.
- `bootstrap.sh` copia `scripts/cbm`, `scripts/cbm-instalar.sh`, `scripts/cbm-indexar.sh`, `.githooks/post-merge` y `.githooks/post-checkout`, y añade al `.gitignore` destino las líneas de `.harness/cbm/`, `.harness/bin/` y `.codebase-memory/`. `.mcp.json` y `.cbmignore` los genera el `sync` que bootstrap ya corre.
- `instalar-frameworks.sh` llama a `scripts/cbm-instalar.sh` si la memoria está encendida.

### D10. Método
- `/init-harness` añade el paso «Memoria de código»: con la memoria encendida, `bash scripts/cbm-instalar.sh`, `python3 scripts/harness.py cbm verificar-secretos`, `bash scripts/cbm-indexar.sh` (en primer plano) y comprobación con `scripts/cbm cli --quiet list_projects`. Claude Code lo corre por Bash, porque los scripts del harness sí pueden escribir; las herramientas MCP de escritura siguen vetadas para Claude.
- `/descubrir` añade el paso «¿Memoria de código?» antes de aplicar `/init-harness`, con los criterios del spec. La decisión queda en la sección `## Memoria de código` de `docs/harness/MAPA.md`; en un proyecto verde, además, abre un issue `verificacion-diferida`.

## Revisión del 2026-10-02 (tras las revisiones 1 y 2 de S4): nadie indexa por MCP
La Revisión 2 demostró que la verificación de secretos vive en el envoltorio (`scripts/cbm`, al arrancar el servidor y en la CLI), pero una llamada MCP a `index_repository` llega por stdio al daemon sin pasar por ella: `build` podía indexar un `.env` y dejarlo consultable. Se evaluaron tres salidas: (a) retirar la escritura por MCP a todos los agentes; (b) un proxy MCP que verifique cada `tools/call`; (c) un plugin de OpenCode que lo bloquee. **Se elige (a)**, en la que coinciden el ejecutor y el arquitecto y que el usuario aprobó: no añade código de seguridad nuevo, deja un único camino de escritura (los scripts, que verifican) y no cuesta nada útil, porque los hooks re-indexan solos y `build` puede correr `bash scripts/cbm-indexar.sh`. `agentes_escritura` queda vacío por defecto. Si un proyecto lo llena, acepta ese riesgo: queda documentado en harness-guide §16.

## Revisión del 2026-10-01 (tras la sesión S1)
- **Caché compartida (D4 y D5).** La caché por repo y entorno impedía usar la memoria en dos repos a la vez (un daemon por usuario), lo que contradice el objetivo de usar el método en varios proyectos.
- **Acceso por rol (D1).** El servidor solo se ofrece a los agentes que exploran.
- **Recorte (D8 y tareas).** Fuera el contenedor y las pruebas redundantes.
- **Invalidación (D6).** Se aceptan los subcomandos `cbm invalidar-cache` y `cbm marcar-indexado` que propuso el ejecutor; ahora borran solo el proyecto del repo.
- **Prueba de exclusión.** El control negativo usa `.env`, no `*.pem`, porque el indexador nunca rastrea `.pem` y no demostraría nada.

## Risks / Trade-offs
- [Un solo daemon por usuario: dos repos con versiones fijadas distintas no pueden tener memoria a la vez] → Con una sola caché y una sola versión del template no ocurre; `scripts/cbm` reporta el conflicto en claro. Al actualizar la versión, se actualiza en todos los repos.

- [Supply chain: el checksum viene de la misma release que el binario y no es una raíz de confianza independiente] → Se fija una vez y se versiona: un cambio posterior en la release no pasa la verificación. Los upgrades son PRs del plano de control con aprobación humana. No protege contra una release comprometida antes de fijar los valores; verificar la firma Sigstore (`checksums.txt.bundle`) es deuda con issue propio (riesgo aceptado por el usuario al elegir v0.11.0, publicada hace dos semanas).
- [Un secreto con un nombre no previsto se indexa] → El indexador respeta `.gitignore`, `verificar-secretos` cubre todo lo que `secretos` reconoce y un test ata `ignorar` a `secretos.rutas`. Lo que `secretos` no reconoce tampoco lo protegen hoy las demás guardias. Es la misma frontera de siempre, documentada en SEGURIDAD.md.
- [Un indexado en segundo plano consume CPU tras cada pull] → Hay lock (nunca dos a la vez) y el índice es incremental. Si molesta, `habilitado: false`.
- [Carreras de escritura en la caché compartida] → Todo pasa por un único daemon del servidor, que serializa los accesos a su base de datos, y los hooks de cada repo se serializan con su lock. Queda un residuo: `build` llama a `index_repository` mientras un hook indexa el mismo repo. La mitigación es re-indexar a mano con `cbm-indexar.sh`; está documentado en harness-guide §16.
- [El excludes global del usuario no cuenta en la verificación] → Es intencional (D6): el indexador tampoco lo lee.
- [`rebase` no re-indexa] → Es una exclusión explícita del spec; se re-indexa a mano.
- [OpenCode cambia el esquema de `tools` o `agent.tools`] → La versión de OpenCode está fijada (1.18.33). La tarea 1.3 lo verifica sobre esa versión real; si difiere, se usa la clave `permission` equivalente y se anota en HANDOFF.md.

## Migration Plan

Los repos que ya usan el harness reciben el cambio por `bootstrap.sh`, que deja los archivos en `.harness/entrantes/` cuando ya existen, y por `/init-harness`. El interruptor viene encendido, pero el MCP no hace nada útil hasta que se instala el binario: `doctor` lo avisa. Para revertir: `habilitado: false` + `sync`, y opcionalmente `rm -rf .harness/cbm .harness/bin`.

## Open Questions

Son diferibles: ninguna cambia los specs, el enfoque ni el desglose. Cada una tiene su fallback y se resuelve en el grupo 1 de tareas.
- ¿Respeta v0.11.0 `XDG_CONFIG_HOME`? Fallback: `HOME` aislado (D5).
- ¿Qué imprime `--version` (o el subcomando equivalente) para comparar la versión? El envoltorio extrae `\d+\.\d+\.\d+`.
- ¿OpenCode 1.18.33 aplica `tools` global más `agent.build.tools` como dice su documentación, con el prefijo `codebase-memory_`? Fallback: clave `permission`.
