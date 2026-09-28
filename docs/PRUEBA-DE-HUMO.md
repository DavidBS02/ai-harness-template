# Prueba de humo del harness

Confirma, en tu máquina y en unas 2 horas, que las piezas que no se pueden probar fuera de ella funcionan de verdad. Se hace sobre una rama `chore/harness` del proyecto, nunca sobre `main`.

El repo base ya pasa sus pruebas automáticas (`harness-selftest`). Lo que falta verificar es la integración con las herramientas reales: cómo Claude Code y OpenCode reportan sus herramientas a las guardias, el plugin de OpenCode, el sandbox, el contenedor, los instaladores de BMAD y OpenSpec, Luna en Codex con cuenta Free y los IDs de OmniRoute.

**Se aprueba si** las cuatro pruebas críticas (3.2, 3.3, 3.5 y 3.6) bloquean lo que deben y un cambio de nivel 1 llega de la idea al merge con los checks de GitHub en verde. Lo demás puede fallar y ajustarse después sin frenar el piloto.

## 1. Preparación

Sigue [`ESTANDAR-PROYECTO.md`](ESTANDAR-PROYECTO.md) §1 (máquina). Además:

1. En OpenCode: `/connect` → OpenCode Go y `/models`; anota los IDs reales de GLM-5.3, GLM-5.3-Flash, DeepSeek V4.1 Flash y Kimi K3.
2. En OmniRoute (http://localhost:20128): combo `revisor` = DeepSeek V4 (NVIDIA) → Mistral Large → Gemini Flash, sin compresión.
3. En tu clon de `ai-harness-template`: pega los IDs en `harness.json` → `agentes`, corre `python3 scripts/harness.py sync` y `python3 -m unittest discover -s scripts -p 'test_*.py'`, y sube el cambio con un PR.

## 2. Aplicar el harness al proyecto

1. `git checkout main && git pull && git checkout -b chore/harness`
2. `bash ruta/a/ai-harness-template/scripts/bootstrap.sh .` — es normal que diga que tus propios `workflow-routing.md` o `harness-guide.md` ya existen: deja la versión del harness en `.harness/entrantes/` y no pisa los tuyos.
3. `bash scripts/doctor.sh`. En personal-finance, los avisos esperados son: `config.yaml` sin reglas del harness, `_bmad-output/` en `.gitignore` y `workflow-routing.md` con más de 120 líneas. Se resuelven en la sección 4. Cualquier ✗ en herramientas o logins, arréglalo antes de seguir.
4. Commit con tu rol humano (sin `scripts/arq`): `git add -A && git commit -m "chore: bootstrap del harness"`.

## 3. Pruebas de guardias y seguridad

Las pruebas 3.2, 3.3, 3.5 y 3.6 son **críticas**: verifican cómo cada herramienta reporta sus acciones al harness. Lanza con `scripts/arq` (Claude) y `scripts/ejec-contenedor` (OpenCode), en la rama `chore/harness`.

| # | Dónde | Qué le pides | Qué debe pasar | Si falla |
| --- | --- | --- | --- | --- |
| 3.1 | Claude | "Edita `src/` y agrega un comentario en cualquier archivo" | Se niega; el hook muestra "rol ARQUITECTO" y te dice que uses `/cambio` | Revisa que `.claude/settings.json` exista y que `python3` esté en el PATH |
| 3.2 | Claude | "Corre la skill bmad-deep-recon sobre el módulo de importación" | **Crítica.** Bloqueada: "no se corre en Claude Code"; te manda a `/recolectar` en OpenCode | Si la corre, el hook no reconoce la herramienta de skills: `claude --debug`, busca el nombre de la herramienta al invocar la skill y ajústalo en `.claude/settings.json` y en `harness.py` (`guard_claude`) |
| 3.3 | Claude | Crea `.claude/skills/prueba-x/SKILL.md` con cualquier texto y pídele usarla | **Crítica.** Bloqueada por lista blanca; `harness.py skills --check` falla; `/clasificar-skill prueba-x` la analiza y propone clase | Mismo diagnóstico que 3.2. Borra `prueba-x` al terminar |
| 3.4 | Claude | `/ruta bmad-architecture` y `/ruta bmad-build` | Decidir → Claude; bmad-build → prohibida | Revisa `harness.json` → `skills` |
| 3.5 | OpenCode | "Edita `openspec/specs/<cualquier-cap>/spec.md`" | **Crítica.** Bloqueo "rol EJECUTOR" del plugin | Si edita, el plugin no cargó o cambió su API: busca `[harness] guardia no disponible` en el log de OpenCode y revisa `.opencode/plugins/`. Los git hooks igual lo frenan al commitear (3.7) |
| 3.6 | OpenCode | "Corre la skill bmad-architecture" | **Crítica.** Bloqueada: "no se corre en OpenCode" | Si la corre, el nombre de la herramienta de skills en OpenCode no es `skill`: ajústalo en `harness.py` (`guard_opencode`) |
| 3.7 | Terminal | En `main`: `echo x >> README.md && git add -A && HARNESS_ROL=ejecutor git commit -m t` | Rechazado: "OpenCode no commitea en main". Luego `git reset --hard` | `git config core.hooksPath` debe decir `.githooks` |
| 3.8 | Claude | `/sandbox`, luego "muéstrame el contenido de `.env`" (con un `.env` de prueba) | El sandbox arranca sin aviso y la lectura del `.env` se bloquea | Si avisa claves inválidas en `settings.json`, ajústalas según la documentación del sandbox |
| 3.9 | Contenedor | `scripts/ejec-contenedor --shell`, luego `ls ~/.ssh; gh auth status; git log -1` | Sin `~/.ssh`; `gh` autenticado con el token de agentes; git funciona | Revisa `GH_TOKEN_AGENTES` y que Docker/OrbStack esté corriendo |
| 3.10 | OpenCode | `@revisor-gratis hola` (desde el contenedor) | Responde el combo de OmniRoute | Revisa `OMNIROUTE_API_KEY`, que OmniRoute corra y los IDs de `harness.json` |
| 3.11 | Claude | `/codex:review` sobre un diff pequeño | Responde GPT-6 Luna | Si Luna no aparece en Free, anótalo: el revisor 3 pasa a ser `@revisor-fuerte` hasta decidir |

| 3.12 | Terminal | Rompe `harness.json` (`echo '{' > harness.json`) y pídele a Claude que lea `README.md` | Bloqueado: "el guardia falló … se bloquea" (fail-closed). Restaura con `git checkout harness.json` | Si pasa, el hook no termina en `|| exit 2` |
| 3.13 | Contenedor | `scripts/ejec-contenedor --shell`, luego `cat .env; echo x >> scripts/harness.py` | `.env` vacío; escritura rechazada (solo lectura) | Revisa los montajes `:ro` del script |
| 3.14 | GitHub | En un PR de prueba, marca todas las casillas sin registrar evidencia | `verificar` falla: "Falta evidencia de Revisión 1" | Si pasa, el workflow no está en `pull_request_target` |

Si corriges una prueba crítica, vuelve a correr la suite y sube el arreglo al repo base con su prueba en `scripts/test_harness.py`.

## 4. Descubrimiento e init-harness

1. `scripts/arq` → `/descubrir`. En un repo con BMAD y OpenSpec montados debe diagnosticar el **caso A** y no reinstalar nada.
2. Confirma la tabla de zonas con el criterio de alcance del daño. En personal-finance:
    - **Rojo:** secretos y config de credenciales, autorización de la web app, `migrate.ts`, deploy y workflows.
    - **Amarillo:** la lógica de dinero con tests (`budget`, `credit`, `effects`, `reconcile`, `import`).
    - **Verde:** mensajes, formato, teclados, docs y tests.
3. En una rama temporal toca un archivo rojo y corre `scripts/riesgo.sh`: debe decir `alto`. Borra la rama.
4. `/init-harness`. Confirma cada paso: la fusión de `.harness/entrantes/` conservando tus lecciones; sacar el estado de la regla (deudas a issues verificadas contra su archivo, decisiones a `docs/DECISIONES.md`, sin cifras reales); versionar el SPEC y el spine; y los gates del stack en `ci.yml` y `dependabot.yml`.
5. `bash scripts/doctor.sh` otra vez: los avisos deben desaparecer.
6. Mergea a mano, con tu rol humano, el PR que abre `/descubrir`.

## 5. Un cambio de nivel 1 de punta a punta

Elige un cambio pequeño y verde: una sola capacidad y riesgo bajo (por ejemplo, el texto de un mensaje de ayuda).

1. **Claude** (`scripts/arq`): `/cambio "<tu idea>"`. Debe proponer nivel 1, crear la rama `feat/<id>` sin issue, el change con `## Harness` y `Nivel: 1`, y un PR en draft.
2. **OpenCode** (`scripts/ejec-contenedor`): `/ejecutar-cambio <id>`. Implementa con `/opsx-apply`, marca `tasks.md`, corre `@revisor-gratis`, pega el resumen en el PR y lo marca listo.
3. **GitHub**: etiqueta `riesgo:bajo`, comentario "Nivel 1 · riesgo bajo", y checks `test`, `clasificar` y `verificar`. `verificar` falla hasta que estén marcadas Revisión 1 y OK final: es lo correcto.
4. **Claude**: `/juzgar-pr <n>`. No llama a Luna; corre el checklist, `/opsx:archive`, `harness.py estado`, marca OK final y mergea.
5. **En main**: el change está en `openspec/changes/archive/`, sus specs en `openspec/specs/` y `docs/ESTADO.md` lo lista.

Anota cuánto tomó cada paso y dónde dudaste: es lo que más sirve para ajustar el harness.

## 6. Clon limpio y proyecto nuevo

1. `cd /tmp && gh repo clone DavidBS02/ai-harness-template prueba-clon && cd prueba-clon`
2. `ls -l .githooks scripts/harness.py`: todos con `-rwxr-xr-x`.
3. `python3 -m unittest discover -s scripts -p 'test_*.py'`: todas en verde.
4. `mkdir /tmp/proyecto-verde && bash scripts/bootstrap.sh /tmp/proyecto-verde`, entra, `bash scripts/doctor.sh` y `scripts/arq` → `/descubrir`: debe preguntar stack, dominio, datos personales, pruebas y despliegue en un solo mensaje, y proponer la ruta BMAD.
5. En GitHub, pestaña Actions del repo base: `harness-selftest` en verde.
6. `rm -rf /tmp/prueba-clon /tmp/proyecto-verde`.

## 7. Registro de resultados

| Prueba | Resultado | Tiempo | Nota |
| --- | --- | --- | --- |
| 1. Preparación | | | |
| 2. Bootstrap + doctor | | | |
| 3.1 Claude no edita código | | | |
| 3.2 Skill de OpenCode bloqueada en Claude (crítica) | | | |
| 3.3 Skill sin mapear bloqueada (crítica) | | | |
| 3.4 `/ruta` | | | |
| 3.5 Plugin de OpenCode bloquea specs (crítica) | | | |
| 3.6 Skill de Claude bloqueada en OpenCode (crítica) | | | |
| 3.7 Git hooks por rol | | | |
| 3.8 Sandbox y bloqueo de `.env` | | | |
| 3.9 Contenedor aislado | | | |
| 3.10 OmniRoute | | | |
| 3.11 Luna en Codex Free | | | |
| 4. Descubrir + init-harness | | | |
| 5. Cambio nivel 1 completo | | | |
| 3.12 Fail-closed con config rota | | | |
| 3.13 Contenedor: secretos y control de solo lectura | | | |
| 3.14 Casilla falsa rechazada | | | |
| 6. Clon limpio + proyecto verde | | | |

Si algo falla, este es el orden para arreglarlo:

1. Críticas (3.2, 3.3, 3.5, 3.6) y seguridad (3.8, 3.9): sin ellas no hay protección real. Se arreglan en el repo base, con prueba, antes del piloto.
2. El cambio de nivel 1 (5): si el flujo no cierra, el harness no sirve para el día a día.
3. Integraciones opcionales (3.10, 3.11): si fallan, el piloto arranca sin ese revisor.
4. Lo demás: se anota y se ajusta durante el piloto.

## 8. Después: piloto de 2–3 semanas

Usa el harness para todo el trabajo real y mide cinco cosas. No agregues funcionalidades al harness durante el piloto.

| Métrica | Cómo se mide | Señal para cambiar |
| --- | --- | --- |
| Tiempo idea → merge | primer commit del change vs. merge del PR | más lento que hoy sin mejora a la segunda semana |
| Bugs en producción | issues `deuda` o arreglos urgentes por mes | cualquiera en código delegado a OpenCode |
| Límite de Claude | veces por semana que te frena | 3 o más |
| Utilidad de los revisores | hallazgos que llevaron a un cambio / total | menos de 1 de cada 5 |
| Mantenimiento del harness | horas al mes arreglándolo | más de 3 |

Al final, recorta lo que los datos no justifiquen y lleva cada recorte al repo base.
