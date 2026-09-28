# Estándar para configurar un proyecto con el harness

Un proyecto que sigue este estándar queda con cuatro garantías: los agentes no pueden tocar lo que no deben (**seguridad**), nada llega a `main` sin pasar sus gates (**calidad**), cada cambio deja rastro en GitHub (**trazabilidad**) y el contexto vive en archivos, no en conversaciones (**continuidad**).

Se aplica siempre en este orden, porque cada paso depende del anterior:

1. **Máquina** (una vez): aislar credenciales y agentes.
2. **Proyecto**: crear o adoptar el repo con el harness y conectarlo a GitHub.
3. **Seguridad del proyecto**: sandbox, contenedor y secretos.
4. **Calidad**: los gates de CI y la definición de hecho.
5. **Descubrimiento**: zonas, routing y el primer change.
6. **Operación**: el flujo diario y el mantenimiento.

Tiempo estimado: la máquina, una tarde; cada proyecto nuevo, una a dos horas. La verificación de que todo funciona está en [`PRUEBA-DE-HUMO.md`](PRUEBA-DE-HUMO.md).

> Las guardias del harness evitan que los agentes se salgan de su rol, pero **no son una barrera de seguridad**. Esa la dan el sandbox, el contenedor y los permisos de las credenciales.

---

## 1. Una vez por máquina

El objetivo es que un agente engañado no tenga a su alcance nada que no sea el proyecto en el que trabaja.

1. **Usuario de macOS aparte para proyectos personales con agentes** (Configuración del Sistema → Usuarios y grupos). En ese usuario no inicies sesión con cuentas de trabajo: ni en `gh`, ni en git, ni en el navegador. Es la medida que más riesgo quita.
2. **Credenciales de GitHub mínimas:**
    - En ese usuario, `gh auth login` solo con tu cuenta personal.
    - Para los agentes, un token *fine-grained* (GitHub → Settings → Developer settings) limitado a los repos que trabajan, con permisos Contents, Pull requests, Issues y Workflows. Nunca un token clásico con `repo` completo. Guárdalo como `GH_TOKEN_AGENTES` fuera de cualquier repo.
    - Rótalo cada 90 días.
3. **Herramientas:** `claude`, `opencode`, `codex`, `gh`, `python3` (3.8 o más) y OrbStack o Docker Desktop. Fija versiones cuando puedas y actualiza a propósito, no automáticamente.
4. **Claude Code:** inicia sesión con tu suscripción y confirma con `/status` que no usa API key. Ni `ANTHROPIC_API_KEY` ni `ANTHROPIC_BASE_URL` en tu `.zshrc`.
5. **Codex:** `codex login` con ChatGPT Free, desactiva "mejorar el modelo" en Controles de datos e instala `codex-plugin-cc` en Claude Code (`/plugin marketplace add openai/codex-plugin-cc` → `/plugin install codex@openai-codex` → `/reload-plugins` → `/codex:setup`).
6. **OmniRoute:** solo proveedores por API key con uso personal permitido; nunca tu cuenta de Claude, sesiones web ni OAuth de Antigravity, Gemini CLI o Kiro. Que escuche únicamente en `localhost`. `OMNIROUTE_API_KEY` en el llavero o en un archivo con permisos `600`, nunca en un repo.
7. **Prueba rápida:** `bash scripts/doctor.sh` en cualquier proyecto con el harness debe salir sin ✗ en herramientas y logins.

## 2. Crear o adoptar el proyecto

Hay dos entradas, según si el proyecto existe o no. Desde aquí, todo pasa en una rama `chore/harness` hasta que el PR se mergee.

**Proyecto nuevo:**

1. `gh repo create DavidBS02/<nombre> --private --template DavidBS02/ai-harness-template --clone`
2. `cd <nombre> && git config core.hooksPath .githooks && python3 scripts/harness.py sync`

**Proyecto existente** (verde o con código):

1. `cd <proyecto> && git checkout main && git pull && git checkout -b chore/harness`
2. `bash ruta/a/ai-harness-template/scripts/bootstrap.sh .` — no pisa nada; lo que ya existía queda en `.harness/entrantes/` para fusionarlo después.

**En ambos casos:**

3. `bash scripts/instalar-frameworks.sh`: instala BMAD y OpenSpec (fijado como devDependency si hay `package.json`) y se salta lo ya instalado.
4. `bash scripts/github-setup.sh`: etiquetas `riesgo:*`, `deuda`, `verificacion-diferida` y, si el repo es público o tienes GitHub Pro, la protección de `main` con los checks `test`, `clasificar` y `verificar`.
5. `bash scripts/doctor.sh`: resuelve todo lo marcado con ✗. Los avisos (`!`) se resuelven en la sección 5.
6. Commit con tu rol humano (sin `scripts/arq`): `git add -A && git commit -m "chore: harness"`.

## 3. Seguridad del proyecto

El aislamiento sigue al riesgo: Claude Code corre en tu Mac con su sandbox; OpenCode, que usa modelos de terceros y gratuitos, corre en un contenedor.

**Claude Code: sandbox activado** ([documentación](https://code.claude.com/docs/en/sandboxing)).

1. En el proyecto, abre `scripts/arq` y corre `/sandbox`. Elige el modo que pide permiso para lo que no pueda correr aislado.
2. Si al arrancar Claude avisa que el sandbox no pudo iniciar, **no sigas**: sin sandbox, los comandos corren sin aislamiento.
3. El repo ya trae en `.claude/settings.json` el bloqueo de lectura de secretos: `permissions.deny` para la herramienta Read (`.env`, `.env.*`, `~/.ssh`, `~/.config/gh`, `~/.aws`) y `sandbox.filesystem.denyRead` para los comandos de bash. Si Claude Code avisa que alguna clave no es válida en tu versión, ajústala según la documentación. Limita la red del sandbox a los dominios que el proyecto necesita.

**OpenCode: dentro de un contenedor**, con `scripts/ejec-contenedor`.

- Monta solo el repo (y, si es un worktree, la carpeta `.git` del repo principal). Nada de tu `~/.ssh`, tu llavero ni tus sesiones.
- Usa `GH_TOKEN_AGENTES` como `GH_TOKEN`, nunca tu sesión de `gh`.
- Apunta OmniRoute a `host.docker.internal:20128` (vía `OMNIROUTE_BASE_URL`); fuera del contenedor, `scripts/ejec` usa `localhost`.
- Guarda el login de OpenCode Go en volúmenes de Docker propios (`harness-opencode-*`), aislados de tu máquina.
- Trae `git`, `gh` y `python3`, que necesitan los git hooks y los comandos del harness. `scripts/ejec-contenedor --rebuild` actualiza OpenCode.
- Máximo aislamiento (código de clientes, agentes en modo autónomo): una máquina virtual con OrbStack o UTM en vez del contenedor.

**Secretos:**

- `.env` siempre en `.gitignore`; en el repo solo `.env.example` sin valores reales.
- Nunca en archivos versionados: tokens, IDs reales, datos personales ni cifras reales, tampoco en `AGENTS.md`, `docs/` u `openspec/`.
- Nada con datos personales ni fixtures sin anonimizar va a los revisores gratuitos de OmniRoute.
- Si el ejecutor no necesita el `.env`, sácalo del repo antes de abrir el contenedor (el script avisa si lo ve).

## 4. Estándares de calidad

Nada llega a `main` sin pasar todos los gates de su nivel. Los gates viven en CI, no en la memoria de nadie: un agente nunca afirma que algo pasa, lo dice CI.

**Gates de CI** (el job de `ci.yml` se llama `test`; `/init-harness` escribe los pasos del stack):

| Gate | Qué corre | Obligatorio |
| --- | --- | --- |
| Instalación reproducible | `npm ci` o equivalente con lockfile | siempre |
| Lint y formato | el linter del stack, sin warnings nuevos | siempre |
| Tipos | typecheck del stack | si el lenguaje lo tiene |
| Tests | suite completa | siempre |
| Build | el build de producción | si hay build |
| Secretos | `gitleaks` (ya incluido en `ci.yml`) | siempre |
| Dependencias | `npm audit --audit-level=high`, `pip-audit`, etc. | siempre |
| Proceso del harness | `proceso` (nivel, change, issue, revisiones, `sync --check`, `skills --check`, `openspec validate`) | siempre |
| Riesgo | `riesgo` (etiqueta y comentario) | siempre |
| Selftest del harness | `harness-selftest` (cuando cambia el motor) | siempre |

**Pruebas:**

- Zona roja: todo cambio lleva pruebas que lo cubran; sin pruebas no hay merge.
- Zona amarilla: todo comportamiento nuevo o cambiado lleva su prueba.
- Cada tarea de OpenSpec termina en "verificar con …": un comando, una prueba o una observación concreta.
- Una prueba que falla se arregla o se discute en el PR; nunca se desactiva en silencio.

**Dependencias:**

- Versiones fijadas con lockfile versionado; OpenSpec fijado exacto.
- Dependabot semanal (`.github/dependabot.yml`, con `github-actions` ya incluido; `/init-harness` agrega el ecosistema del stack). El check `proceso` no les exige change ni revisiones: basta CI en verde y tu merge manual.
- Antes de agregar un paquete: mantenimiento activo, licencia compatible y que no duplique algo que ya hay.

**PRs:**

- Máximo 5 archivos o 300 líneas (umbrales de `harness.json`); si es más grande, se divide el change.
- Commits pequeños en imperativo que explican el porqué; squash merge a `main`.
- Plantilla de PR completa: nivel y riesgo, change, cómo se probó, revisiones marcadas, archive.

**Definición de hecho** (todo cambio con change):

- [ ] CI en verde en todos los gates.
- [ ] Verificado contra la realidad, no solo con tests: se observó el comportamiento donde corre.
- [ ] Revisiones que exige su riesgo, marcadas en el PR.
- [ ] Change archivado con el checklist de deltas (`docs/LECCIONES.md` §1).
- [ ] Deudas y verificaciones diferidas abiertas o cerradas como issues, con evidencia.
- [ ] `openspec/config.yaml` y `AGENTS.md` al día si cambió stack, capas o convenciones.

## 5. Descubrimiento y primer change

Aquí el harness pasa de genérico a ser el de este proyecto. Lo hace Claude Code (`scripts/arq`) y cada decisión importante la confirmas tú.

1. **`/descubrir`**: diagnostica el caso (A: método montado, B: código sin método, C: vacío), hace el inventario sin LLM y, si el repo es grande, delega la lectura a OpenCode con `/resumir-modulos` o `/recolectar`.
2. **Confirma la tabla de zonas** con el criterio de alcance del daño. Primero responde: ¿quién usa el sistema (solo tú, un equipo, clientes)? ¿Cuántos entornos hay?
    - Rojo: lo que puede filtrar credenciales, abrir acceso, corromper la única copia de los datos o romper el despliegue.
    - Amarillo: lógica importante cubierta por pruebas.
    - Verde: bajo impacto o bien cubierto.
3. **Routing:** las zonas quedan en `harness.json` → `zonas`; `python3 scripts/harness.py sync`. Prueba que tocar un archivo rojo dé riesgo alto.
4. **`/init-harness`**: fusiona `.harness/entrantes/`, siembra o completa `openspec/config.yaml`, llena `AGENTS.md` (con "Puntos de entrada" y "Nunca entra al repo"), saca el estado de las reglas (deudas a issues, decisiones a `docs/DECISIONES.md`), escribe los gates del stack en `ci.yml` y agrega su ecosistema a `dependabot.yml`.
5. **Skills:** `python3 scripts/harness.py skills --check` en verde. Cualquier skill sin mapear se clasifica con `/clasificar-skill <nombre>`.
6. **Un solo entorno de producción:** anota en `AGENTS.md` que se despliega solo desde `main`, uno a la vez, con respaldo previo si toca datos.
7. **Primer change de producto** (proyecto nuevo): antes va BMAD (`bmad-help` → brief → `bmad-spec` → `bmad-architecture`), y el primer `/cambio` incluye como tareas sembrar `openspec/config.yaml` y `AGENTS.md` con su verificación.

## 6. Trabajo diario

Cada pedido se enruta primero y después se ejecuta con la ceremonia de su nivel. Si dudas, `/ruta <skill>` o pregúntale a Claude.

| Si el pedido es… | Nivel | Quién y cómo |
| --- | --- | --- |
| Producto, PRD, UX, arquitectura o cambiar un AD | — | BMAD en Claude; lectura masiva con `/recolectar` y revisiones con `/revisar-artefacto` en OpenCode. Termina en un dossier y un `/cambio` |
| Trivial (riesgo bajo y ≤ 20 líneas) | 0 | `scripts/nuevo.sh <slug> --nivel 0` → OpenCode `@mecanico` → PR con solo CI |
| Una capacidad, riesgo bajo o medio | 1 | Claude `/cambio` → OpenCode `/ejecutar-cambio` → Claude `/juzgar-pr` |
| Varias capacidades o riesgo medio | 2 | Igual que 1, con issue y design |
| Iniciativa nueva o riesgo alto | 3 | BMAD antes, luego nivel 2 con las tres revisiones y tu lectura del diff |

Reglas que no cambian con el nivel:

- Siempre `scripts/arq` para Claude y `scripts/ejec-contenedor` para OpenCode.
- Un modelo por sesión; si cambias de modelo, primero `/compact`. Una sesión por workflow de BMAD, con `/clear` antes.
- Al cerrar cualquier sesión, `/handoff`.
- Si OpenCode encuentra un hueco en el spec, lo escribe en `HANDOFF.md` y se detiene; Claude lo resuelve con `/opsx:update`.
- Máximo dos vueltas entre OpenCode y Claude por PR; a la tercera, decide el arquitecto.

## 7. Mantenimiento

Con 15 minutos a la semana y una hora al mes, el proyecto no acumula deudas escondidas ni credenciales viejas.

**Cada semana (15 minutos):**

- [ ] `bash scripts/doctor.sh` sin ✗.
- [ ] Mergear o cerrar los PRs de Dependabot.
- [ ] `gh issue list --label deuda` y `--label verificacion-diferida`: cerrar con evidencia las resueltas, verificadas contra su archivo dueño y no contra la lista.
- [ ] `python3 scripts/harness.py estado` para regenerar `docs/ESTADO.md`.

**Cada mes (1 hora):**

- [ ] Actualizar a propósito Claude Code, OpenCode (`scripts/ejec-contenedor --rebuild`), Codex, OmniRoute, BMAD y OpenSpec; después, `skills --check` y clasificar lo nuevo con `/clasificar-skill`.
- [ ] Revisar los términos de uso de los proveedores gratuitos de OmniRoute y quitar los que cambiaron.
- [ ] Revisar los IDs de modelo en `harness.json` contra `/models` y correr `sync`.
- [ ] Registrar las métricas: tiempo idea → merge, bugs en producción, veces que chocaste con el límite de Claude, hallazgos útiles de los revisores y horas dedicadas al harness.
- [ ] Llevar al repo base cualquier mejora del harness o lección nueva (`docs/LECCIONES.md`).

**Cada 90 días:** rotar `GH_TOKEN_AGENTES` y las API keys de OmniRoute.

## 8. Checklist: proyecto listo para trabajar

Un proyecto está listo cuando cada casilla está marcada. Si falta una, se resuelve antes del primer cambio real.

**Máquina**

- [ ] Usuario de macOS aparte, sin cuentas de trabajo.
- [ ] `GH_TOKEN_AGENTES` *fine-grained*, limitado a los repos del proyecto.
- [ ] Sin `ANTHROPIC_API_KEY` ni `ANTHROPIC_BASE_URL` en el entorno.

**Seguridad**

- [ ] Sandbox de Claude Code activo y sin avisos de claves inválidas en `.claude/settings.json`.
- [ ] OpenCode corre con `scripts/ejec-contenedor`.
- [ ] `.env` en `.gitignore` y `.env.example` sin valores reales.
- [ ] OmniRoute solo en `localhost` y solo con proveedores por API key.

**Harness**

- [ ] `bash scripts/doctor.sh` sin ✗ ni avisos.
- [ ] `python3 scripts/harness.py skills --check` y `sync --check` en verde.
- [ ] Zonas confirmadas por alcance del daño en `harness.json`.
- [ ] `openspec/config.yaml` con `context` sembrado y reglas `[harness]`.
- [ ] `AGENTS.md` sin placeholders, con "Puntos de entrada" y "Nunca entra al repo".
- [ ] Estado fuera de las reglas: deudas como issues y decisiones en `docs/DECISIONES.md`.

**GitHub y calidad**

- [ ] Etiquetas creadas y, si se puede, `main` protegida con los checks `test`, `clasificar` y `verificar`.
- [ ] `ci.yml` con todos los gates de la sección 4, en verde (sin el aviso "STACK pendiente").
- [ ] `dependabot.yml` con el ecosistema del stack.
- [ ] `harness-selftest` en verde.

**Prueba final**

- [ ] Un cambio de nivel 1 recorrió todo el flujo y se mergeó con los checks en verde ([`PRUEBA-DE-HUMO.md`](PRUEBA-DE-HUMO.md)).
