# Handoff (estado vivo de la rama)

- Fecha / herramienta / modelo: 2026-10-01 · OpenCode (build, override) · opencode-go/glm-5.3
- Issue / spec: #2 · openspec/changes/add-codebase-memory-mcp (nivel 3, riesgo alto, zona roja autorizada)
- Qué se hizo: (se actualiza por grupo de tareas)
- Qué falta: (se actualiza por grupo de tareas)
- Decisiones tomadas y por qué: (se actualiza por grupo de tareas)
- Dudas para el arquitecto: (se actualiza por grupo de tareas)
- Riesgos: cambio grande del plano de control; el PR exige aprobación humana en GitHub.
- Siguiente paso sugerido: (se actualiza por grupo de tareas)

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
