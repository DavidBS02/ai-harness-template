# Handoff (estado vivo de la rama)

- Fecha / herramienta / modelo: 2026-10-01 · OpenCode (build, `HARNESS_OVERRIDE=1`, fuera del contenedor) · opencode-go/glm-5.3
- Issue / spec: #2 · openspec/changes/add-codebase-memory-mcp (nivel 3, riesgo alto, OpenCode-zona-roja: autorizado)
- Qué se hizo: grupos 0 (arquitecto), 1 y 2 completos, verificados y commiteados. Parada ordenada a mitad del grupo 3.
- Qué falta: 3.1 (a medias), 3.2, 3.3, 4.1, 4.2, 4.3, 5.1–5.5, 6.1, 7.1–7.3, 8.1–8.2, 9.1–9.7, 10.1–10.3, 11.1–11.3 y las revisiones (1 y 2 mínimo; la 3 es de luna/codex).
- Decisiones tomadas y por qué: ver abajo («Hallazgos técnicos»).
- Dudas para el arquitecto: ver abajo.
- Riesgos: cambio grande del plano de control; el PR exige aprobación humana en GitHub.
- Siguiente paso sugerido: retomar por la verificación restante de 3.1, correr el selftest completo sobre el árbol actual y luego 3.2/3.3; después commitear por bloques (grupo 3+4.1, grupo 5) con sus marcas en tasks.md.

## Estado de los commits

| Grupo | Tareas | Commit |
|---|---|---|
| 0 (arquitecto) | 0.1–0.5 | ef8ea1a y anteriores |
| 1 | 1.1, 1.2 (1.3 queda manual) | a9da587 |
| 2 | 2.1–2.3 | a24c30a (incluye arreglos preexistentes del selftest: `TestAutoModificacion` no limpiaba `HARNESS_OVERRIDE` y fallaba al correr la suite con override; el helper `Repo` ahora excluye `.harness/bin` —binario de 289 MB— de los repos de prueba) |
| 3+4+5 (en curso) | SIN commitear, tareas sin marcar | — |

## Qué hay en el árbol de trabajo SIN commitear (todo corresponde a tareas NO marcadas)

- `scripts/cbm` (nuevo, ejecutable) — tarea 3.1 A MEDIAS. Implementado según D4/D5 e involuntariamente verificado en casi todo (ver abajo). Falta: (a) correr el selftest completo sobre el árbol actual (la última corrida verde fue antes de tocar `harness.py`), (b) el caso literal de 3.1 «`.env` sin excluir»: `.env` está doblemente cubierto (`.gitignore` raíz + `.cbmignore`), así que lo verifiqué de forma equivalente con `tmp/x.pem` (solo cubierto por `.cbmignore`); falta demostrar la reinclusión con `.gitignore` anidado (`!.env`), que cubrirá el test 9.3.
- `scripts/harness.py` (modificado) — tareas 4.1 y 5.1–5.4, código COMPLETO pero SIN MARCAR: `cbm verificar-secretos` (D6, verificado a mano: falla nombrando `tmp/x.pem` cuando se quita `*.pem` de `.cbmignore`; pasa con el `.cbmignore` por defecto) y los cambios de `sync` (D1: genera `.mcp.json`, claves `mcp`/`tools`/`agent` de `opencode.json`, `.cbmignore`, sección «Memoria de código» de RUTAS.md; retira todo con `habilitado: false`; `sync --check` pasa). Su verificación formal son los tests 9.1/9.2/9.3, TODAVÍA NO ESCRITOS (grupo 9). El docstring de uso todavía no menciona `cbm` (tarea 10.3).
- Adaptadores generados presentes en el árbol: `.mcp.json`, `.cbmignore`, `opencode.json`, `docs/harness/RUTAS.md`. Commitearlos es la tarea 5.5 (hacerlo junto con las marcas de 5.1–5.4 cuando pasen sus tests).
- `harness.json` volvió a quedar EXACTO como en HEAD (las pruebas del interruptor `habilitado:false` fueron temporales y se restauraron; verificado con `git diff` vacío y `sync --check` en verde).

## Hallazgos técnicos (verificados, útiles para retomar)

- **v0.11.0 ignora `XDG_CONFIG_HOME`**: la config vive en `$CBM_CACHE_DIR/_config.db` (mismo dir que la caché). Aplica el fallback de D5: `scripts/cbm` exporta `CBM_CACHE_DIR`, `XDG_CONFIG_HOME` (inerte, documental) y `HOME` aislados bajo `.harness/cbm/<entorno>/`. Marcador de config en `.harness/cbm/<entorno>/config/.harness-config-<versión>`. `~/.config` y `~/.cache` del usuario no se tocan (verificado).
- **Valores por defecto del servidor**: `auto_index=false`, `watcher_enabled=true` → el envoltorio fija ambos en `false` (D4 paso 5). Verificado con `config get`.
- **macOS no tiene `timeout`**: para probar el arranque del servidor se usó `scripts/cbm < /dev/null` (el servidor sale solo con EOF de stdin). Para 3.2 (esperar 10 s) servirá `nohup ... & sleep 10; kill`.
- **Proyecto en `list_projects`**: el nombre se deriva de la ruta absoluta del repo (`/`→`-`, p. ej. `Users-...-ai-harness-template`). `search_code` exige `pattern` y `project`.
- **Exclusión del indexador**: `.cbmignore` (sintaxis gitignore, raíz del repo) funciona contra el indexador real: con `*.pem` quitado, `search_code` del contenido de `tmp/x.pem` lo encontraba; con el patrón, 0 resultados.
- **Frontera conocida de `ignorar`**: un ARCHIVO llamado p. ej. `.ssh` (sin barra, regex `(^|/)\.ssh(/|$)` con `$`) no lo cubre el patrón `.ssh/` (solo dirs). `verificar-secretos` fallaría cerrado nombrándolo (seguro, no filtrador). Si importa, el arquitecto puede añadir `.ssh` (sin barra) a `ignorar` en un ajuste posterior. Los ejemplos naturales (`.ssh/id_rsa`, `.config/gh/hosts.yml`) sí quedan cubiertos.

## Dudas para el arquitecto

- Ninguna bloqueante. La 1.3 (sesión real de OpenCode 1.18.33 para `tools`/`agent.tools` con prefijo `codebase-memory_`) sigue siendo verificación manual pendiente del humano.

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
