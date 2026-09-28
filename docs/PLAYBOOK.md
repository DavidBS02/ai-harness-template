# Harness de tres herramientas: Claude Code + OpenCode + OmniRoute (con GitHub como columna vertebral)

Fecha: 28 sep 2026. Presupuesto: Claude Pro (US$20) + OpenCode Go (US$10) + capas gratis (ChatGPT Free, Gemini AI Studio, Groq, Cerebras, Mistral, NVIDIA, OpenRouter :free).

## 0. La regla de oro

Cada herramienta hace UNA cosa y el traspaso entre ellas siempre pasa por GitHub (rama, spec, commit, PR). Nunca por copiar/pegar conversaciones.

| Rol | Herramienta | Modelo(s) | Escribe código | Ventana |
|---|---|---|---|---|
| Ideador / arquitecto / juez final | Claude Code (Claude Pro) | Modelo por defecto del plan; `/model` para ver opciones | Solo specs, issues y arreglos puntuales al final | 1 |
| Ejecutor | OpenCode (OpenCode Go) | GLM-5.3 (build), GLM-5.3-Flash (mecánico), DeepSeek V4.1 Flash (explorar, small_model), Kimi K3 (solo contexto largo) | Sí, todo el volumen | 2 |
| Revisor gratis nivel 1 | OpenCode + OmniRoute | Combo: DeepSeek V4 (NVIDIA) → Mistral Large → Gemini Flash | No (solo lectura) | 2 (subagente) |
| Revisor gratis nivel 2 (adversarial) | OpenCode + OmniRoute | DeepSeek V4 fijo | No | 2 (subagente) |
| Revisor frontera nivel 3 | Codex CLI (ChatGPT Free) vía codex-plugin-cc | GPT-6 Luna | No | 1 (dentro de Claude Code) |
| CI / verificación objetiva | GitHub Actions | ninguno | No | GitHub |

Aclaración: OmniRoute NO es un harness, es un gateway. "OmniRoute como revisor" significa: un subagente de OpenCode (`@revisor-gratis`) cuyo modelo viene de OmniRoute.

## 0b. Fase 0: descubrimiento (antes de la primera feature)

Claude Code corre `/descubrir`: inventario mecánico → resúmenes por módulo delegados a OpenCode → MAPA.md con zonas roja/amarilla/verde y rutas reales → `.harness/rutas-*.txt` (datos del routing) → DELEGACION.md (qué tarea de este repo va a qué modelo) → `/init-harness`. Después de esto, `scripts/riesgo.sh` clasifica con las rutas de TU repo, no con las genéricas. Repite `/descubrir` cuando el repo cambie de forma (nuevo módulo sensible, migración grande).

## 1. ¿OpenCode ejecuta y OmniRoute revisa, o al revés?

OpenCode ejecuta, OmniRoute revisa. Razones:

1. Ejecutar necesita cientos de llamadas con herramientas (leer, editar, correr tests). Las capas gratis dan 429 a mitad de tarea, tienen 1–5 requests por minuto en varios proveedores y `auto` cambia de modelo entre turnos, lo que rompe la caché y la coherencia. OpenCode Go es de pago, con cuota predecible y modelos entrenados para tool-calling.
2. Revisar es una tarea de un solo disparo, de solo lectura, con un diff acotado. Es el uso ideal de una cuota gratis con límite de peticiones.
3. El valor de un revisor viene de que sea de OTRA familia que quien escribió el código. GLM escribe, Gemini/GPT-OSS/Luna revisan. Si invirtieras, Gemini escribiría mal (tool-calling de capa gratis) y GLM revisaría a Gemini con menos criterio.

Excepción: si un día se te acaba la cuota de Go, OmniRoute puede ejecutar tareas MECÁNICAS pequeñas (tests, docs) con un modelo fijo. Nunca una feature completa.

## 2. Modelos: qué usa cada agente y por qué

### Claude Code (ventana 1)
- Planificación, specs, decisiones de arquitectura, desbloqueo de bugs difíciles, revisión final antes del merge.
- Usa el modelo por defecto del plan. Reserva el modelo más grande solo para decisiones de arquitectura (los límites de Pro se comparten con el chat de Claude).
- NO toques `ANTHROPIC_BASE_URL` ni `ANTHROPIC_API_KEY`. Si existe `ANTHROPIC_API_KEY` en tu entorno, Claude Code cobra por API en vez de usar tu Pro.

### OpenCode (ventana 2) — proveedor OpenCode Go
| Agente | Modelo | Uso | Costo relativo (peticiones por 5 h, aprox.) |
|---|---|---|---|
| `build` (por defecto) | opencode-go/glm-5.3 | Implementar el spec | ~220 |
| `@mecanico` | opencode-go/glm-5.3-flash | Tests, docs, renombres, migraciones repetitivas | ~6.300 |
| `@explorador` + `small_model` | opencode-go/deepseek-v4.1-flash | Leer código, buscar, títulos | miles |
| `contexto-largo` (primario, opcional) | opencode-go/kimi-k3 | Solo cuando hay que leer un repo entero | ~110 |

Regla: un modelo por sesión. Si necesitas cambiar, primero `/compact`, luego cambia.

### OmniRoute (gateway local en :20128) — proveedor `omniroute` dentro de OpenCode
- Conecta SOLO proveedores por API key con uso personal permitido: Gemini (AI Studio), Groq, Cerebras, Mistral, NVIDIA NIM, OpenRouter :free.
- NO conectes: tu cuenta de Claude, sesiones web de ChatGPT/Claude, OAuth de Antigravity/Gemini CLI, Kiro. Todos prohíben proxies y banean cuentas.
- Crea un combo (cadena ordenada) para `@revisor-gratis`: DeepSeek V4 (NVIDIA NIM) → Mistral Large → Gemini Flash. Y un modelo fijo DeepSeek V4 para `@revisor-fuerte`. Nada de `auto` para revisar: necesitas resultados comparables.
- Compresión RTK/Caveman DESACTIVADA para el revisor (el diff no se comprime).

### Codex CLI (ChatGPT Free) dentro de Claude Code
- `codex-plugin-cc` instalado en Claude Code. Modelo: GPT-6 Luna (verifica con `codex` → `/model` que tu cuenta Free lo muestre en CLI).
- Solo para diffs importantes: seguridad, lógica de negocio, antes del merge. En Free no puedes comprar créditos; si se acaba, esperas.
- En ChatGPT: Configuración → Controles de datos → desactivar "mejorar el modelo".

## 3. GitHub: la columna vertebral

### Ramas
- `main`: protegida. Solo entra por PR con CI en verde.
- `feat/<issue>-<slug>`: una por spec. Un worktree por rama: `git worktree add ../wt-<slug> -b feat/<issue>-<slug>`.
- Claude Code y OpenCode NUNCA trabajan en el mismo worktree al mismo tiempo.

### Qué vive en GitHub
| Artefacto | Dónde | Quién lo crea |
|---|---|---|
| Idea / feature | Issue (plantilla `feature.md`) | Tú o Claude Code (`/spec` la crea con `gh issue create`) |
| Spec | `docs/specs/<issue>-<slug>.md` en la rama feat | Claude Code |
| Código | commits en la rama feat | OpenCode |
| Revisión 1 | comentario en el PR (`gh pr comment`) | OpenCode `@revisor-gratis` |
| Revisión 2 | comentario en el PR | Claude Code `/codex:review` |
| Verificación | GitHub Actions (`ci.yml`) | automática |
| Estado de la tarea | `HANDOFF.md` en la rama | quien cierre la sesión (`/handoff`) |

### Reglas de PR
- Título: `feat(<área>): <qué> (#<issue>)`.
- El PR enlaza el spec y pega las dos revisiones (o un resumen).
- Merge solo si: CI verde + revisor gratis sin hallazgos críticos + Luna sin hallazgos críticos + Claude Code da el OK final.
- Squash merge para mantener `main` limpio.

## 4. Flujo paso a paso (por feature)

```
[1] IDEA          Claude Code   /spec "<idea>"  → crea issue + rama + worktree + docs/specs/NNN.md
[2] SPEC REVIEW   Claude Code   /codex:adversarial-review docs/specs/NNN.md   (Luna ataca el plan)
                  Claude Code   corrige el spec, commit "spec: NNN"
[3] EJECUTAR      OpenCode      (en ../wt-slug)  /ejecutar-spec NNN   → build (GLM-5.3) + @mecanico + @explorador
                  OpenCode      commits pequeños; corre tests localmente
[4] REVISIÓN 1    OpenCode      @revisor-gratis "revisa git diff main..HEAD contra docs/specs/NNN.md"
                  OpenCode      corrige lo crítico; /handoff
[5] PR            OpenCode      gh pr create --fill --body-file .github/PULL_REQUEST_TEMPLATE.md
                  GitHub        CI corre tests/lint
[6] REVISIÓN 2    Claude Code   gh pr checkout NNN ; /codex:review   (Luna revisa el diff real)
                  Claude Code   lee CI + ambas revisiones; arregla lo puntual o devuelve a OpenCode con notas en HANDOFF.md
[7] MERGE         Claude Code   gh pr merge --squash ; git worktree remove ../wt-slug
```

Si el paso 6 devuelve trabajo a OpenCode, se repite 3→4→6 en la misma rama. Máximo dos vueltas; a la tercera, Claude Code lo arregla directamente.

## 4b. Dos revisores, dos trabajos (no todo pasa por los dos)

| Revisor | Modelo | Pregunta que responde | Cuándo corre |
|---|---|---|---|
| @revisor-gratis (OpenCode) | Combo OmniRoute: DeepSeek V4 (NVIDIA NIM) → Mistral Large → Gemini Flash | ¿Hace lo que dice el spec y está completo? | Siempre |
| @revisor-fuerte (OpenCode) | DeepSeek V4 fijo (NVIDIA NIM vía OmniRoute), prompt adversarial | ¿Cómo rompo esto? | Riesgo medio o alto |
| /codex:review (Claude Code) | GPT-6 Luna (ChatGPT Free) | Segunda opinión adversarial de otra familia | Solo riesgo alto, o crítico dudoso, o segunda vuelta |

Por qué no Gemini Pro: desde marzo de 2026 la capa gratis de Google es solo Flash. DeepSeek V4 y Mistral Large son más fuertes y sus capas gratis permiten uso personal.

Routing determinista: `scripts/riesgo.sh` clasifica el diff por rutas y tamaño (sin LLM), leyendo `.harness/rutas-alto.txt` y `rutas-bajo.txt` que escribió `/descubrir`. Lo usan `/spec`, `/ejecutar-spec`, `/juzgar-pr` y la Action `riesgo.yml`, que etiqueta el PR (`riesgo:bajo|medio|alto`) y comenta qué revisiones exige. Si el spec, el script y la etiqueta difieren, gana el nivel más alto.
- bajo: solo docs/tests/config → revisor-gratis + CI
- medio: código de producción, o >5 archivos, o >300 líneas → + revisor-fuerte
- alto: toca auth, pagos, migraciones, esquema, secretos, infra, workflows → + Luna + lectura tuya línea por línea

Cada revisor corre DESPUÉS de corregir lo que encontró el anterior, para no gastar cuotas en lo obvio.

## 5. Delimitación estricta: qué NO hace cada uno

- **Claude Code NO** implementa features completas (gasta tu Pro en lo que solo Claude hace bien). NO se conecta a proxies. NO trabaja en el worktree de OpenCode.
- **OpenCode NO** decide arquitectura ni cambia el spec. Si el spec no alcanza, escribe la duda en HANDOFF.md y para. NO usa `auto` de OmniRoute para implementar.
- **OmniRoute NO** ejecuta features. NO recibe credenciales OAuth ni de suscripción. NO comprime diffs de revisión.
- **Codex/Luna NO** se usa para tareas rutinarias (la cuota Free es chica y no se recarga).
- **GitHub Actions** es la única verdad sobre "los tests pasan". Ningún agente puede afirmar que pasan sin que CI lo confirme.

## 6. Contexto compartido

- `AGENTS.md`: reglas del repo. Lo leen OpenCode y Codex de forma nativa; Claude Code lo importa desde `CLAUDE.md` (`@AGENTS.md`).
- `docs/specs/*.md`: contrato de cada feature.
- `HANDOFF.md`: estado vivo. Se actualiza con `/handoff` en las dos herramientas.
- Git: la historia de commits es el contexto real. Commits pequeños con mensajes que digan POR QUÉ.
- Nada del historial de chat se copia entre herramientas.

## 7. Instalación (una vez) — detalle en docs/ONBOARDING.md

1. `npm i -g opencode-ai omniroute @openai/codex` (verifica nombres en cada repo).
2. OpenCode: `/connect` → OpenCode Go (API key). Luego `/models` y corrige IDs en `opencode.json` y `.opencode/agents/*.md`.
3. OmniRoute: `omniroute` → `http://localhost:20128` → Providers → agrega NVIDIA NIM, Mistral, Gemini, Groq, Cerebras, OpenRouter. Crea el combo `revisor` (DeepSeek V4 → Mistral Large → Gemini Flash) y copia su ID en `revisor-gratis.md` y `opencode.json`; copia el ID de DeepSeek V4 en `revisor-fuerte.md`. Desactiva compresión para ambos.
4. Codex: `codex login` con tu cuenta Free de ChatGPT.
5. Claude Code: `/plugin marketplace add openai/codex-plugin-cc` → `/plugin install codex@openai-codex` → `/reload-plugins` → `/codex:setup`.
6. GitHub: `gh auth login`; protege `main` (Settings → Branches → require PR + status checks).
7. Copia esta carpeta a la raíz del repo y ajusta `AGENTS.md`, `.github/workflows/ci.yml` y las rutas sensibles de `scripts/riesgo.sh` a tu stack.

## 8. Cuándo cambiar el setup

- Llegas al límite de Claude Pro 3+ veces por semana → Max 5x, o mueve más implementación a OpenCode.
- Llegas al límite de Go a diario → GLM Coding Plan Lite (US$18) para GLM directo, o Go + Lite.
- Luna se queda corto seguido → ChatGPT Go (US$8) o Plus (US$20).
- Un proveedor de OmniRoute cambia sus términos → quítalo; la wiki de OmniRoute mantiene la tabla de ToS.

## 9. Privacidad

- Código propio/open source: cualquier capa.
- Código de clientes o con datos personales: solo Claude Code (Pro), OpenCode Go (proveedores sin retención) y CI. Nada a capas gratis ni a Gemini AI Studio gratis (puede usar datos para mejorar productos).
