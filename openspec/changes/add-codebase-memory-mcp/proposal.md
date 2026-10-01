## Why

Los agentes del harness (arquitecto, ejecutor y revisores) entienden el código leyendo archivos, y eso gasta tokens y contexto en cada sesión, sobre todo en repos grandes o con varios módulos. [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) indexa el repo en un grafo local y lo expone por MCP (búsqueda de símbolos, trazas de llamadas, arquitectura). Integrarlo en el template da esa memoria a todos los agentes sin abrir huecos en las reglas que ya existen: secretos, plano de control, versiones fijadas y mínimo privilegio.

## What Changes

- **Interruptor en `harness.json`**: sección `mcp.codebase_memory` con `habilitado: true` por defecto, el directorio de caché, la lista de herramientas de escritura y los agentes que solo consultan. Apagarlo es `habilitado: false` seguido de `harness.py sync`.
- **Versión fijada**: v0.11.0, con la URL de cada plataforma y su SHA-256 en `.harness/versiones.json → binarios`. Se instala descargando el `.tar.gz` de la release y verificando el checksum. Sin `install.sh` oficial y sin `curl | bash`.
- **Adaptadores generados por `sync`**: `.mcp.json` para Claude Code, bloque `mcp` de `opencode.json`, permisos por agente de OpenCode y `.cbmignore`. Todo existe solo si el interruptor está encendido; si se apaga, `sync` los retira.
- **Contenedor del ejecutor**: el binario fijado se instala en `.harness/contenedor/Dockerfile` con verificación de checksum. La etiqueta de la imagen incluye la versión, así que un upgrade fuerza la reconstrucción.
- **Índice local y fuera de git**: `CBM_CACHE_DIR=.harness/cbm`, configuración aislada por repo y `auto_index` y watcher del servidor apagados. `.gitignore` ignora `.harness/cbm/`, `.harness/bin/` y `.codebase-memory/`.
- **Mínimo privilegio, con veto por defecto**: solo el ejecutor (`build`) y los scripts del harness (hooks, `/init-harness`) escriben en el índice. Claude Code y todos los demás agentes de OpenCode tienen vetadas `index_repository`, `delete_project`, `manage_adr` e `ingest_traces`. Eso incluye a los revisores, los subagentes del template, los integrados y los que se creen después.
- **Secretos fuera del índice**: `.cbmignore` se genera desde `secretos`. Indexar falla cerrado si algún archivo secreto del repo quedaría indexado.
- **Re-indexado automático**: `.githooks/post-merge` y `.githooks/post-checkout` lanzan el indexado en segundo plano, sin bloquear git y sin fallar nunca. `scripts/cbm-indexar.sh` queda como comando manual de respaldo.
- **`/init-harness`**: instala el binario en el host, verifica secretos y hace el indexado inicial.
- **`/descubrir`**: nueva sección «¿Memoria de código?» que recomienda encender o apagar según la visión y el objetivo. El usuario confirma y la decisión queda en `docs/harness/MAPA.md` con su justificación.
- **`doctor`**: verifica binario, versión, `.cbmignore` frente a secretos, hooks y adaptadores.
- **Documentación**: `docs/harness-guide.md` y `README.md` (cómo activar, apagar, re-indexar y actualizar). `RUTAS.md` se regenera con `sync`.

## Capabilities

### New Capabilities
- `memoria-de-codigo`: integración de un servidor MCP de memoria de código en el harness. Cubre interruptor, versión fijada y verificada, adaptadores por herramienta, permisos de escritura por rol, exclusión de secretos, re-indexado automático no bloqueante, indexado inicial y recomendación en el descubrimiento.

### Modified Capabilities
(ninguna: `openspec/specs/` aún no existe en el template)

Reglas de arquitectura de `openspec/config.yaml` que gobiernan el change: «Un motor, un archivo de datos», «Fail-closed», «Plano de control», «Secretos» y «Dependencias externas fijadas por versión y checksum».

## Fuera de este change

- Usar la memoria de código dentro de los prompts de los comandos (`/ejecutar-cambio`, revisores) para ahorrar lecturas. Primero se mide; va en un change posterior.
- La persistencia del índice en el repo (`.codebase-memory/` con `persistence: true`) y compartir el índice entre máquinas.
- La UI web (`codebase-memory-mcp-ui`), `ingest_traces` con trazas reales y el uso de ADRs del servidor (`manage_adr`) como fuente de verdad. La fuente de verdad de decisiones sigue siendo `docs/DECISIONES.md` y los AD-* de BMAD.
- Soporte de Windows (el harness asume macOS/Linux).
- Telemetría de ahorro de tokens atribuible al MCP.

## Impact

- Plano de control: `harness.json`, `scripts/harness.py`, `scripts/test_harness.py`, `scripts/ejec-contenedor`, `scripts/bootstrap.sh`, `scripts/instalar-frameworks.sh`, `.githooks/post-merge` y `.githooks/post-checkout` (nuevos), `.harness/versiones.json`, `.harness/contenedor/Dockerfile`, `.claude/settings.json` y `opencode.json`.
- Nuevos: `scripts/cbm`, `scripts/cbm-instalar.sh`, `scripts/cbm-indexar.sh`, `.mcp.json` y `.cbmignore` (generados).
- Método y docs: `.claude/commands/descubrir.md`, `.claude/commands/init-harness.md`, `docs/harness-guide.md`, `README.md`, `docs/harness/MAPA.md` (plantilla), `.gitignore` y `docs/harness/RUTAS.md` (vía sync).
- Dependencia externa nueva: binario `codebase-memory-mcp` v0.11.0 (GitHub Releases de DeusData), verificado por SHA-256.
- Ejecución: los archivos del plano de control solo se editan con `HARNESS_OVERRIDE=1` y fuera del contenedor, porque este monta el plano de control en solo lectura. El PR exige aprobación humana en GitHub.

## Harness
- Issue: #2
- Nivel: 3
- Riesgo: alto
- Zonas: plano de control (harness.json, scripts/harness.py, scripts/test_harness.py, scripts/ejec-contenedor, scripts/bootstrap.sh, scripts/instalar-frameworks.sh, .githooks/, .harness/versiones.json, .harness/contenedor/, .claude/settings.json, opencode.json), scripts/cbm*, .claude/commands/, docs/, README.md, .gitignore
- OpenCode-zona-roja: autorizado
