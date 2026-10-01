## Purpose

Dar a los agentes del harness una memoria de código local (grafo del repo expuesto por MCP) que se enciende o apaga con un interruptor, usa una versión fijada y verificada, nunca indexa secretos y solo puede escribirla el rol que implementa.

## ADDED Requirements

### Requirement: Interruptor único en harness.json
El harness SHALL leer el estado de la memoria de código solo de `harness.json → mcp.codebase_memory.habilitado`. El template MUST traerlo en `true`. Con `habilitado: false`, `harness.py sync` MUST retirar todo lo que genera para la memoria de código, y los hooks y scripts de indexado MUST terminar sin hacer nada y con código 0.

#### Scenario: Template recién copiado
- **WHEN** se corre `bootstrap.sh` sobre un repo y luego `harness.py sync`
- **THEN** existen la entrada `codebase-memory` en `.mcp.json`, la entrada `codebase-memory` en el bloque `mcp` de `opencode.json` y el archivo `.cbmignore`

#### Scenario: Apagar
- **WHEN** el humano pone `habilitado: false` y corre `harness.py sync`
- **THEN** desaparecen la entrada `codebase-memory` de `.mcp.json` y de `opencode.json`, los vetos de herramientas de la memoria en los agentes y `.cbmignore`; los demás servidores MCP y claves de esos archivos quedan intactos

#### Scenario: Hooks con la memoria apagada
- **WHEN** `habilitado` es `false` y el usuario hace `git checkout` de otra rama o `git merge`
- **THEN** no se lanza ningún indexado y el comando de git termina igual que sin el hook

#### Scenario: Deriva detectada
- **WHEN** `harness.json` cambia el interruptor y no se corrió `sync`
- **THEN** `harness.py sync --check` termina con código 1 y nombra los archivos desactualizados

### Requirement: Binario fijado y verificado por checksum
El harness SHALL instalar `codebase-memory-mcp` solo en la versión fijada en `.harness/versiones.json`, descargando el archivo de release de la plataforma y verificando su SHA-256 contra el valor fijado antes de extraerlo. MUST NOT usar el instalador oficial (`install.sh`), `curl | bash` ni gestores de paquetes. Si el checksum no coincide, la instalación MUST abortar sin dejar un binario utilizable.

#### Scenario: Instalación correcta en el host
- **WHEN** el usuario corre el instalador del harness en macOS o Linux (amd64 o arm64)
- **THEN** el binario queda en `.harness/bin/`, informa la versión fijada y el instalador termina con código 0

#### Scenario: Checksum alterado
- **WHEN** el archivo descargado no coincide con el SHA-256 fijado
- **THEN** el instalador termina con código distinto de 0, dice qué checksum esperaba y cuál obtuvo, y no deja ningún binario nuevo en `.harness/bin/`

#### Scenario: Plataforma sin checksum fijado
- **WHEN** la plataforma del host no tiene SHA-256 en `.harness/versiones.json`
- **THEN** el instalador se niega a descargar y explica qué plataforma falta

#### Scenario: Binario de otra versión
- **WHEN** el binario encontrado informa una versión distinta de la fijada
- **THEN** el envoltorio del servidor se niega a arrancar y `doctor` lo reporta como error con el comando para reinstalar

### Requirement: Contenedor del ejecutor con el binario fijado
La imagen del ejecutor SHALL incluir el binario en la versión fijada, verificado por SHA-256 durante la build. La imagen MUST reconstruirse cuando cambie la versión fijada.

#### Scenario: Build de la imagen
- **WHEN** `scripts/ejec-contenedor --rebuild` construye la imagen
- **THEN** dentro del contenedor el binario responde con la versión fijada

#### Scenario: Upgrade de versión
- **WHEN** cambia la versión fijada en `.harness/versiones.json`
- **THEN** la siguiente ejecución de `scripts/ejec-contenedor` construye una imagen nueva sin necesitar `--rebuild`

#### Scenario: Checksum alterado en la build
- **WHEN** el checksum fijado para la arquitectura de la imagen no coincide con el archivo descargado
- **THEN** la build de la imagen falla

### Requirement: Índice y configuración locales, fuera de git
El servidor SHALL guardar su índice en `.harness/cbm/` del repo y leer su configuración de un directorio aislado por repo, con indexado automático al arrancar y watcher apagados. `.harness/cbm/`, `.harness/bin/` y `.codebase-memory/` MUST estar ignorados por git.

#### Scenario: Arranque del servidor
- **WHEN** Claude Code u OpenCode arrancan el servidor MCP
- **THEN** el servidor usa `.harness/cbm/` como caché, no indexa por su cuenta y no modifica la configuración global del usuario (`~/.config/codebase-memory-mcp/`)

#### Scenario: Nada del índice se versiona
- **WHEN** existe un índice y el usuario corre `git status`
- **THEN** no aparece ningún archivo bajo `.harness/cbm/`, `.harness/bin/` ni `.codebase-memory/`

### Requirement: Escritura del índice solo por el ejecutor
Las herramientas que modifican estado (`index_repository`, `delete_project`, `manage_adr`, `ingest_traces`) SHALL estar disponibles solo para los agentes de OpenCode listados en `mcp.codebase_memory.agentes_escritura` (por defecto, solo `build`) y para los scripts del harness. El veto MUST ser por defecto: Claude Code y cualquier otro agente de OpenCode (revisores, subagentes del template, subagentes integrados y agentes creados después) MUST tener esas herramientas vetadas y conservar las de consulta.

#### Scenario: Revisor intenta re-indexar
- **WHEN** un revisor de OpenCode invoca `index_repository`
- **THEN** la herramienta no está disponible para ese agente

#### Scenario: Revisor consulta
- **WHEN** un revisor invoca `search_graph` o `get_code_snippet`
- **THEN** la consulta funciona

#### Scenario: Claude intenta borrar el proyecto
- **WHEN** Claude Code invoca `delete_project` del servidor
- **THEN** la regla de permisos la deniega

#### Scenario: Agente nuevo sin declarar
- **WHEN** alguien añade `.opencode/agents/nuevo.md` sin tocar `agentes_escritura`
- **THEN** ese agente no tiene disponibles las herramientas de escritura

#### Scenario: Ejecutor indexa
- **WHEN** el agente `build` de OpenCode invoca `index_repository`
- **THEN** la herramienta está disponible

### Requirement: Secretos fuera del índice
Ningún archivo que coincida con `harness.json → secretos` (salvo `secretos.excepto`) SHALL entrar al índice. El harness MUST generar las exclusiones del indexador desde `secretos` y MUST verificar, antes de cada indexado, que todo archivo secreto presente en el repo queda excluido. Si alguno no queda excluido, el indexado MUST NOT ejecutarse.

#### Scenario: Secreto cubierto
- **WHEN** el repo tiene `.env` y `deploy/key.pem` y se lanza un indexado
- **THEN** el indexado corre y ninguno de esos archivos aparece en búsquedas del índice

#### Scenario: Secreto no cubierto
- **WHEN** existe un archivo secreto que las exclusiones generadas no cubren
- **THEN** el indexado no se ejecuta, el comando manual termina con código distinto de 0 nombrando el archivo, y el indexado en segundo plano deja el motivo en su log

#### Scenario: Excepciones permitidas
- **WHEN** el repo tiene `.env.example`
- **THEN** la verificación no lo trata como secreto

### Requirement: Re-indexado automático en segundo plano
Tras `git merge` (incluido `git pull`) y tras cambiar de rama con `git checkout` o `git switch`, el harness SHALL lanzar un re-indexado del repo en segundo plano. El hook MUST volver de inmediato, MUST terminar siempre con código 0 y MUST NOT imprimir errores que interrumpan el flujo de git. Si ya hay un indexado en curso en ese repo, MUST NOT lanzar otro.

#### Scenario: Pull con cambios
- **WHEN** el usuario corre `git pull` y entra un merge
- **THEN** el comando termina sin esperar al indexado y el índice se actualiza poco después

#### Scenario: Checkout de un archivo
- **WHEN** el usuario corre `git checkout -- archivo.py` (no cambia de rama)
- **THEN** no se lanza ningún indexado

#### Scenario: Binario ausente
- **WHEN** el binario no está instalado
- **THEN** el hook no lanza nada, termina con código 0 y la causa queda en el log de indexado

#### Scenario: Indexados concurrentes
- **WHEN** se dispara un segundo hook mientras el primer indexado sigue corriendo
- **THEN** el segundo no lanza otro proceso

### Requirement: Re-indexado manual de respaldo
El harness SHALL ofrecer un comando para re-indexar en primer plano, con la misma verificación de secretos, que informe éxito o fallo con su código de salida.

#### Scenario: Re-indexado manual
- **WHEN** el usuario corre el comando de re-indexado con la memoria encendida y el binario instalado
- **THEN** el índice queda actualizado y el comando termina con código 0

#### Scenario: Re-indexado manual con la memoria apagada
- **WHEN** `habilitado` es `false`
- **THEN** el comando informa que la memoria está apagada, explica cómo encenderla y termina con código 0 sin indexar

### Requirement: Indexado inicial en /init-harness
Con la memoria encendida, `/init-harness` SHALL instalar el binario fijado en el host, verificar que ningún secreto quedaría indexado y hacer el primer indexado completo en primer plano, mostrando el resultado al usuario.

#### Scenario: Init con memoria encendida
- **WHEN** el usuario corre `/init-harness` con `habilitado: true`
- **THEN** al terminar, la herramienta de consulta `list_projects` muestra el repo indexado

#### Scenario: Init con memoria apagada
- **WHEN** `habilitado` es `false`
- **THEN** `/init-harness` omite el paso y lo dice en su checklist final

### Requirement: Recomendación de memoria de código en /descubrir
`/descubrir` SHALL incluir una sección «¿Memoria de código?» que recomiende encender o apagar según la visión y el objetivo del proyecto, con estos criterios: encender si el repo ya existe o es grande, tiene varios módulos o lenguajes, tendrá vida larga o habrá trabajo en paralelo; apagar si es muy pequeño, solo documentación o su lenguaje no está soportado; en un proyecto verde, encender y revisar en el primer hito. El usuario MUST confirmar, y la decisión y su justificación MUST quedar escritas en `docs/harness/MAPA.md`.

#### Scenario: Repo existente con varios módulos
- **WHEN** `/descubrir` analiza un repo con código en varios módulos
- **THEN** recomienda encender, pide confirmación y escribe la decisión con su justificación en MAPA.md

#### Scenario: Repo solo de documentación
- **WHEN** el repo no tiene código de aplicación ni lo tendrá
- **THEN** recomienda apagar y, si el usuario confirma, deja `habilitado: false` y corre `sync`

#### Scenario: Proyecto verde
- **WHEN** el repo es verde (caso C)
- **THEN** recomienda encender, registra en MAPA.md que se revisará en el primer hito y abre un issue `verificacion-diferida` para esa revisión

### Requirement: Diagnóstico de la memoria de código
`doctor` SHALL reportar, con la memoria encendida, si el binario está instalado y en la versión fijada, si las exclusiones cubren todos los secretos del repo, si los hooks de re-indexado existen y son ejecutables y si existe un índice. Con la memoria apagada MUST decir que está apagada y no reportar errores de la memoria.

#### Scenario: Binario ausente
- **WHEN** la memoria está encendida y no hay binario en `.harness/bin/`
- **THEN** `doctor` muestra un aviso con el comando de instalación

#### Scenario: Secreto sin excluir
- **WHEN** un archivo secreto del repo no queda excluido del indexado
- **THEN** `doctor` lo reporta como error nombrando el archivo
