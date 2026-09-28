# Seguridad del harness: qué está garantizado y qué no

Este documento describe los controles **tal como están implementados** en `harness.json` 0.5.0 y cómo verificarlos. Cada control se clasifica en cuatro niveles:

- **A · Política:** está escrito en las instrucciones; el modelo decide si lo cumple.
- **B · Guardia:** un hook o plugin intenta impedirlo, pero hay vías conocidas para esquivarlo.
- **C · Enforcement:** una barrera que el agente no puede saltar desde su entorno (sistema operativo, servidor o GitHub).
- **D · Evidencia:** existe un registro objetivo de que el paso ocurrió.

Regla de lectura: donde dice B, **no** afirmes que el agente "no puede"; solo que se le bloquea en los caminos conocidos.

## 1. Controles por amenaza

| Amenaza | Control | Nivel | Dónde | Límite conocido |
|---|---|---|---|---|
| Leer `.env`, llaves SSH, credenciales | Hook de Claude (Read/Grep/Glob/Bash) y plugin de OpenCode | B | `harness.py guard_*`, `secretos` en `harness.json` | Comandos ofuscados (p. ej. `python -c` que arma la ruta) no se detectan |
| Leer secretos desde el contenedor | Los archivos secretos se montan como `/dev/null` de solo lectura | **C** | `scripts/ejec-contenedor` | Solo archivos dentro del repo; lo que no esté en disco no se enmascara |
| Leer secretos desde el host (Claude) | `sandbox.filesystem.denyRead` + `permissions.deny` | **C** solo con `/sandbox` activo | `.claude/settings.json` | Si el sandbox no arranca, Claude Code sigue sin él: verifícalo (PRUEBA-DE-HUMO 3.8) |
| Imprimir tokens del entorno (`printenv`, `$GH_TOKEN`, `gh auth token`) | Patrones de `secretos.comandos` | B | guardias | Un token presente en el entorno es alcanzable por código arbitrario; por eso los tokens son *fine-grained* y de alcance mínimo |
| Commitear un secreto | `pre-commit` (todos los roles, también humano) + `gitleaks` en CI | B local + **C** en CI | `.githooks/pre-commit`, `ci.yml` | El local se salta con `--no-verify` o `HARNESS_OVERRIDE=1`; gitleaks en CI no |
| Exfiltrar por red | — | **no cubierto** | — | El contenedor tiene red abierta. Pendiente P1: red con proxy de salida por lista blanca |
| Editar el propio guardia, hooks o workflows | Plano de control bloqueado para agentes | B (host) / **C** (contenedor: montado `:ro`; sandbox: `denyWrite`) | `control_plane` en `harness.json` | En el host sin sandbox, un comando ofuscado podría escribirlo |
| Debilitar el gate desde el PR | `proceso` y `riesgo` corren con `pull_request_target`: workflow, motor y `harness.json` de la **rama base** | **C** | `.github/workflows/proceso.yml`, `riesgo.yml` | Solo si `main` está protegida; ver §4 |
| Ampliar permisos editando `harness.json` localmente | Los guardias leen la config de `origin/main` (o `HEAD`), no del árbol de trabajo | B+ | `cargar_confiable` | Tras mergear, la regla nueva aplica: por eso el PR exige aprobación humana |
| Neutralizar el motor sin commitear | Los git hooks ejecutan el `harness.py` de `HEAD` | B+ | `.githooks/*` | Un agente que commitee un motor modificado lo tiene bloqueado por el propio hook de `HEAD` |
| Marcar una revisión como hecha sin hacerla | La casilla ya no cuenta; se exige un registro JSON atado al commit revisado | **D parcial** | `harness.py revision`, `.harness/revisiones/` | El registro lo escribe el propio agente: prueba cuándo y sobre qué commit, no que el revisor lo haya dicho. Ver §3 |
| Aprobar su propio cambio sensible | Riesgo alto, plano de control, techo duro o presupuesto agotado → review APPROVED del humano en GitHub sobre el HEAD | **C + D** | `aprobacion_humana` | Requiere que los agentes usen **otra identidad** de GitHub (§4) |
| Diff gigante | Techo duro (`max_archivos_duro`, `max_lineas_duro`) → aprobación humana | **C** en el gate | `umbrales` | Los umbrales de 5 archivos / 300 líneas son **señales de riesgo**, no límites |
| Mover un archivo fuera de una zona roja | `--no-renames`: el borrado del original cuenta | **C** en el gate | `diff()` | — |
| Guardia roto (Python ausente, JSON inválido, config faltante) | Fail-closed (§2) | **C** | `settings.json` (`|| exit 2`), `guardia_claude.py`, plugin, hooks | — |
| Subagentes de OpenCode | El plugin no los intercepta ([issue](https://github.com/anomalyco/opencode/issues/5894)); tienen permisos nativos `bash` con denegaciones | B | `.opencode/agents/*.md` | Verifica en tu versión que los patrones de `permission.bash` se respetan |
| Dependencia que cambia sola | Versiones fijadas en `.harness/versiones.json`; sin `latest` en instalación, contenedor ni gate | **C** (reproducible) | `versiones.json`, `Dockerfile`, `instalar-frameworks.sh` | Acciones de GitHub fijadas por etiqueta hasta que corras `fijar-acciones --aplicar`; imagen base sin digest hasta que lo fijes |

## 2. Fail-open vs fail-closed

| Fallo | Comportamiento | Por qué |
|---|---|---|
| El guardia de Claude lanza una excepción, recibe JSON inválido o no encuentra config | **Bloquea** (exit 2) | Claude Code solo bloquea con exit 2; cualquier otro código deja pasar la acción |
| No existe `python3` o `CLAUDE_PROJECT_DIR` viene vacío | **Bloquea**: el comando del hook termina en `|| exit 2` y resuelve la raíz con `git rev-parse` si falta la variable | Hay un [bug conocido](https://github.com/anthropics/claude-code/issues/33815) donde falta `CLAUDE_PROJECT_DIR` |
| El motor no responde al plugin de OpenCode | **Bloquea** la herramienta | Antes dejaba pasar |
| `harness.json` roto o ausente en un hook de git de agente | **Bloquea** el commit | Humano: se avisa pero no se bloquea (no hay agente que contener) |
| API de GitHub caída al verificar aprobación | **Falla el check** | No se puede afirmar que hubo aprobación |
| OmniRoute o un proveedor gratuito caído | **Degrada**: el revisor no responde, no hay evidencia y el gate lo exige; usa el `fallback` del agente (`harness.py ruta`) | Mejor esperar que mergear sin revisión |
| `doctor` no encuentra una herramienta opcional | **Continúa** con aviso | No afecta la seguridad |

Salto consciente para cualquier guardia: `HARNESS_OVERRIDE=1`. En los commits queda `Harness-Override: yes`.

## 3. Evidencia de revisión: qué prueba y qué no

Cada revisión se registra con:

```bash
python3 scripts/harness.py revision registrar --revisor revisor-gratis --modelo <id> --veredicto APROBAR --hallazgos salida.md
```

El registro (`.harness/revisiones/<rama>/…json`) guarda `commit_sha` (HEAD revisado), revisor, rol, modelo, veredicto, hash y texto de los hallazgos, tokens y costo declarados, y fecha. El gate lo acepta solo si:

- el `commit_sha` es ancestro del HEAD del PR, y
- después de ese commit solo cambiaron evidencia, estado u OpenSpec (no código).

**Prueba:** sobre qué commit exacto se declaró la revisión, con qué modelo, cuándo, y que el código no cambió después.
**No prueba:** que un modelo distinto haya producido el texto. El agente puede escribir el registro. Por eso, para riesgo alto y plano de control el gate exige además la **review APPROVED del humano en GitHub** sobre ese mismo commit, que sí es evidencia de nivel D.

Siguiente paso (P1, no implementado): una revisión que corra dentro de CI con una API key que el agente no tiene y publique su veredicto como comentario de `github-actions[bot]`. Eso sí sería evidencia infalsificable del revisor.

## 4. GitHub: identidad y protección

- **Protección de rama:** en repos privados del plan gratuito GitHub **no la ofrece** (ni branch protection ni rulesets). Sin ella, los checks `test`, `clasificar` y `verificar` fallan, pero **no impiden** el merge. Para enforcement real: repo público o GitHub Pro. `github-setup.sh` la configura cuando está disponible, con `enforce_admins: true`.
- **Identidad de los agentes:** GitHub no deja aprobar el PR propio. Si los agentes usan tu cuenta, no podrás dar la aprobación humana que exige el gate para riesgo alto y plano de control. Arquitectura recomendada:
  - una cuenta máquina (p. ej. `DavidBS02-bot`) con permiso de escritura y un token *fine-grained* limitado a los repos, que usan Claude y OpenCode;
  - tu cuenta, listada en `github.aprobadores_humanos`, solo para aprobar;
  - `bash scripts/github-setup.sh --revision-humana` para exigir la review de CODEOWNERS.
- **Permisos de workflows:** `proceso` (lectura), `riesgo` (escritura de PRs para etiquetar), `ci` (lectura). Los workflows con `pull_request_target` nunca ejecutan código del PR: lo leen con git.

## 5. Modelo de permisos por rol

| Nivel | Qué habilita | Humano | Claude (arquitecto) | OpenCode build | Subagentes | Revisores | CI |
|---|---|---|---|---|---|---|---|
| READ_ONLY | leer código (no secretos) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| SAFE_EDIT | editar docs, specs, `_bmad-output/` | ✓ | ✓ | tasks.md, digests, evidencia | ✓ (path según git hooks) | ✗ | ✗ |
| LOCAL_EXECUTION | correr comandos | ✓ | ✓ (sandbox) | ✓ (contenedor) | ✓ (contenedor) | pregunta | ✓ |
| REPO_WRITE | editar código de la app | ✓ | ✗ (override) | ✓ | ✓ | ✗ | ✗ |
| GIT_WRITE | commit y push de ramas | ✓ | ✓ (sin código) | ✓ (no main) | ✓ (no main) | ✗ | ✗ |
| PR_WRITE | abrir PR, comentar, etiquetar | ✓ | ✓ | ✓ | ✗ | ✗ | `riesgo` |
| CONTROL_WRITE | plano de control | ✓ con override + aprobación | solo `harness.json`, `ci.yml`, `dependabot.yml` | ✗ | ✗ | ✗ | ✗ |
| MERGE | mergear a main | ✓ | ✓ tras gate verde | ✗ | ✗ | ✗ | ✗ |
| PRODUCTION_WRITE | desplegar | ✓ | ✗ | ✗ (salvo tarea autorizada del change) | ✗ | ✗ | según el proyecto |

## 6. Upgrades y rollback

1. Rama `chore/upgrade-<herramienta>` y cambia la versión en `.harness/versiones.json`.
2. `scripts/ejec-contenedor --rebuild` para la imagen; reinstala la CLI en el host.
3. `bash scripts/doctor.sh --tests` y la sección 3 de `PRUEBA-DE-HUMO.md` (guardias).
4. PR: toca el plano de control, así que exige tu aprobación.
5. Rollback: revierte el commit del PR; `versiones.json` vuelve a la versión anterior y `--rebuild` la restaura.

Las acciones de GitHub: `python3 scripts/harness.py fijar-acciones --aplicar` (necesita `gh` autenticado) las fija a su SHA. Dependabot mantiene los SHA actualizados.

## 7. Riesgos residuales (no resueltos)

- Red abierta en el contenedor y en el host: un agente comprometido puede enviar lo que pueda leer.
- Los tokens necesarios (`GH_TOKEN`, `OMNIROUTE_API_KEY`) están en el entorno del contenedor.
- Los guardias B se basan en patrones; no son un sandbox.
- En el host sin `/sandbox`, Claude conserva acceso de lectura al disco fuera del repo mediante comandos de shell.
- Sin cuenta máquina, la aprobación humana exigida por el gate no se puede dar.
- En repos privados gratuitos, los checks no bloquean el merge.
