# Handoff (estado vivo de la rama)

- Fecha / herramienta / modelo: 2026-10-01 · OpenCode (build, `HARNESS_OVERRIDE=1`, fuera del contenedor) · `opencode-go/space-bunny-free` (gratis, cero retención)
- Issue / spec: #2 · openspec/changes/add-codebase-memory-mcp (nivel 3, riesgo alto, OpenCode-zona-roja: autorizado)
- Qué se hizo: grupos 0 (arquitecto), 1, 2, 3 y 4 completos, verificados y commiteados (`bde07f2` cierra 3.1–3.3 y 4.1–4.3).
- Qué falta (tras el recorte del arquitecto): 3.4 (caché compartida, nueva), 5.1–5.6 (5.1–5.4 ya en el árbol sin commitear; 5.6 nueva), 6.1, 7.1–7.2, 9.1–9.3 y 9.7, 10.1–10.3, 11.1–11.3 y las revisiones 1 y 2 (la 3 es de Luna).
- **Recorte y cambio de diseño del arquitecto (2026-10-01, después de S1):** ver `design.md` → «Revisión del 2026-10-01» y el plan de sesiones de `tasks.md`.
  - **Caché única compartida por todos los repos** (`mcp.codebase_memory.cache_dir`, por defecto `~/.cache/ai-harness/cbm`), por tu hallazgo del daemon único. Estado local en `.harness/cbm/` y sin entornos ni `HARNESS_CONTENEDOR`; la invalidación borra solo el proyecto del repo con `cli delete_project`. Tus subcomandos `cbm invalidar-cache` y `cbm marcar-indexado` se aceptan, adaptados a eso. **`scripts/cbm` y esos subcomandos hay que rehacerlos (tarea 3.4).**
  - **Acceso por rol:** nuevo `agentes_consulta` en `harness.json` (tarea 5.6).
  - **Fuera:** grupo 8 (contenedor), 7.3, 9.4, 9.5 y 9.6 (su contenido va en 9.3 y 9.7).
  - **Tu duda sobre 4.3 y 9.3:** el test 9.3 usa `.env` para el control negativo.
- Decisiones tomadas y por qué: ver abajo («Hallazgos técnicos»).
- Dudas para el arquitecto: ver abajo.
- Riesgos: cambio grande del plano de control; el PR exige aprobación humana en GitHub.
- Siguiente paso sugerido: S2 del plan de `tasks.md` = `/ejecutar-cambio add-codebase-memory-mcp grupo 3b,5,6`: primero `python3 scripts/harness.py sync` (harness.json cambió), luego 3.4, 5.6 y 6.1, después 9.1–9.3 delegados a @mecanico; con esos tests en verde, marcar 5.1–5.4 y hacer 5.5.
- **Excepción de modelo autorizada por el usuario (2026-10-01, sesión S1):** el change es de riesgo **alto**, así que por `modelo_por_riesgo` esta sesión debería usar el modelo fuerte, pero el usuario autorizó explícitamente `space-bunny-free` (gratis, cero retención) porque la ventana de 5 h de Go estaba agotada. No se detuvo la ejecución por el chequeo de modelo. Cuando la ventana se reponga, las sesiones S2–S6 deben volver al modelo fuerte salvo autorización nueva.
- Nota del arquitecto (2026-10-01), modelos: `build` queda por defecto en `opencode-go/deepseek-v4.1-flash`, pero **este change es de riesgo alto**: según `modelo_por_riesgo`, cada sesión de este change va con DeepSeek V4 Pro, elegido con `/models` al abrir la sesión (requiere la región «Global» activada en la cuenta de Go; respaldo `mimo-v2.6-pro`, luego `glm-5.3`), `@mecanico` a `opencode/mimo-v2.6-flash-free` (respaldo `opencode-go/mimo-v2.6-flash`), `recolector` y `contexto-largo` a `deepseek-v4-pro` (motivo: `docs/LECCIONES.md` §21). `sync` ya regeneró `.opencode/agents/*.md` y `opencode.json` en el árbol; commitéalos junto con la tarea 5.5. Si la calidad de DeepSeek en un grupo no alcanza (tests en rojo tras 3 intentos), anótalo aquí y cambia con `/models` al respaldo. La sesión S1 del 2026-10-01 no avanzó (agotó la ventana de 5 h, que es compartida entre modelos): retomar S1 desde cero.
- Nota del arquitecto (2026-10-01): `ignorar` en `harness.json` pasó de `.ssh/`, `.aws/`, `.kube/`, `.gnupg/`, `.config/gh/` a la forma sin barra (cubre archivo y directorio; cierra la «frontera conocida» de abajo). El `.cbmignore` sin commitear está desactualizado: corre `python3 scripts/harness.py sync` antes de verificar 4.x y antes de 5.5.

## Estado de los commits

| Grupo | Tareas | Commit |
|---|---|---|
| 0 (arquitecto) | 0.1–0.5 | ef8ea1a y anteriores |
| 1 | 1.1, 1.2 (1.3 queda manual) | a9da587 |
| 2 | 2.1–2.3 | a24c30a (incluye arreglos preexistentes del selftest: `TestAutoModificacion` no limpiaba `HARNESS_OVERRIDE` y fallaba al correr la suite con override; el helper `Repo` ahora excluye `.harness/bin` —binario de 289 MB— de los repos de prueba) |
| 3+4 | 3.1–3.3, 4.1–4.3 | bde07f2 |
| 5 (en curso) | código COMPLETO en el árbol, SIN commitear y sin marcar | — |

## Qué hay en el árbol de trabajo SIN commitear (todo corresponde a tareas NO marcadas)

- `scripts/harness.py` (modificado) — tareas 5.1–5.4, código COMPLETO pero SIN MARCAR: los cambios de `sync` (D1: genera `.mcp.json`, claves `mcp`/`tools`/`agent` de `opencode.json`, `.cbmignore`, sección «Memoria de código» de RUTAS.md; retira todo con `habilitado: false`; `sync --check` pasa) y el arreglo de `generar_rutas(cfg, root)` para leer la versión fijada. Su verificación formal son los tests 9.1/9.2, TODAVÍA NO ESCRITOS (grupo 9). El docstring de uso todavía no menciona `cbm` (tarea 10.3).
- Adaptadores generados presentes en el árbol: `.mcp.json`, `.cbmignore`, `opencode.json`, `docs/harness/RUTAS.md`. Commitearlos es la tarea 5.5 (hacerlo junto con las marcas de 5.1–5.4 cuando pasen sus tests).
- `.opencode/agents/{mecanmico,recolector,contexto-largo}.md`: los regeneró `sync` con los modelos que elegiste; se commitean con 5.5.
- `harness.json` volvió a quedar EXACTO como en HEAD (la prueba del interruptor `habilitado:false` fue temporal y se restauró; verificado con `git diff` vacío y `sync --check` en verde).

## Verificación del grupo 3+4 (lo que sí quedó comprobado)

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

- Ninguna bloqueante. La 1.3 (sesión real de OpenCode 1.18.33 para `tools`/`agent.tools` con prefijo `codebase-memory_`) sigue siendo verificación manual pendiente del humano.
- **Para el arquitecto, menor:** la 4.2 dice «invalidación de D6» y el design la sitúa dentro de `cbm-indexar.sh` (D7 paso 3, tarea 7.1). Como la 4.2 es del grupo 4 y `cbm-indexar.sh` no existe hasta el grupo 7, la implementé como subcomandos reutilizables de `harness.py`: `cbm invalidar-cache` (compara el SHA-256 de `.cbmignore` con el guardado y borra la caché del entorno si difiere) y `cbm marcar-indexado` (lo guarda tras un indexado correcto). Así 7.1 solo tiene que invocarlos. Si prefieres la lógica dentro de `cbm-indexar.sh`, es un ajuste local sin cambio de comportamiento.
- **Tensión menor entre 4.3 y el grupo 9:** el control negativo que la 4.3 describe («con un patrón quitado de `.cbmignore`, aparecen») no es observable con `*.pem` (ver arriba: `tmp/` y `not_tracked` lo tapan igual). El test 9.3 debe usar `.env` para el control negativo, no `*.pem`.

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
