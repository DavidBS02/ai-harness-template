# Onboarding: configuración por herramienta

Orden recomendado. Tiempo total: 30–45 min la primera vez.

## 0. Cuentas
| Cuenta | Plan | Para qué |
|---|---|---|
| Claude | Pro (US$20) | Claude Code |
| OpenCode Go | US$10 | modelos de ejecución en OpenCode |
| ChatGPT | Free | Codex CLI (GPT-6 Luna) como revisor de riesgo alto |
| NVIDIA NIM, Mistral, Google AI Studio, Groq, Cerebras, OpenRouter | gratis | revisores vía OmniRoute |
| GitHub | gratis | repo, PRs, Actions, labels |

## 1. Instalar
```bash
npm i -g opencode-ai omniroute @openai/codex
# Claude Code: sigue https://code.claude.com/docs/en/quickstart
# gh: https://cli.github.com
```
Verifica nombres de paquete en cada repo oficial; cambian.

## 2. Claude Code
- `claude` → login con tu cuenta Pro. Confirma con `/status` que NO usa API key.
- Plugin de Codex: `/plugin marketplace add openai/codex-plugin-cc` → `/plugin install codex@openai-codex` → `/reload-plugins` → `/codex:setup`.
- Antes: `codex login` con tu cuenta Free de ChatGPT y verifica que `/model` muestre GPT-6 Luna.
- En ChatGPT web: Configuración → Controles de datos → desactiva "mejorar el modelo".

## 3. OpenCode
- `opencode` → `/connect` → OpenCode Go → pega tu API key.
- `/models` → copia los IDs reales y corrige `opencode.json` y `.opencode/agents/*.md` si difieren de `opencode-go/glm-5.3`, `opencode-go/glm-5.3-flash`, `opencode-go/deepseek-v4.1-flash`, `opencode-go/kimi-k3`.
- NO conectes tu cuenta de Claude aquí.

## 4. OmniRoute
- `omniroute` → abre http://localhost:20128.
- Providers → añade SOLO por API key: NVIDIA NIM, Mistral, Google AI Studio, Groq, Cerebras, OpenRouter.
- Combos → crea `revisor`: DeepSeek V4 (NVIDIA) → Mistral Large → Gemini Flash. Copia su ID en `opencode.json` y `.opencode/agents/revisor-gratis.md`.
- Copia el ID de DeepSeek V4 en `.opencode/agents/revisor-fuerte.md`.
- Desactiva compresión (RTK/Caveman) para ambos.
- Exporta `OMNIROUTE_API_KEY` en tu shell.
- Nunca: cuenta de Claude, sesiones web de ChatGPT/Claude, OAuth de Antigravity, Gemini CLI o Kiro.

## 5. GitHub
```bash
gh auth login
git remote add origin git@github.com:<usuario>/<repo>.git && git push -u origin main
bash scripts/github-setup.sh     # labels riesgo:* + protección de main
```

## 6. Método: BMAD + OpenSpec
```bash
bash scripts/instalar-frameworks.sh     # no toca _bmad/ ni openspec/ si ya existen
```
Instala OpenSpec (fijado como devDependency si hay package.json) para `claude`, `opencode` y `codex`, y BMAD (`core` + `bmm`, español, salida en `_bmad-output/`) para `claude-code`, `codex` y `opencode` si el instalador la acepta. Si el repo ya los tenía (caso A de /descubrir), no reinstala nada: `/init-harness` fusiona las reglas del harness con tu `openspec/config.yaml`.

## 7. Fase 0: descubrimiento y routing
```bash
bash scripts/doctor.sh
scripts/arq
> /descubrir            # se detendrá pidiendo resúmenes si el repo tiene código
# en otra terminal, en el mismo repo:
scripts/ejec
> /resumir-modulos
# de vuelta en Claude Code:
> /descubrir            # continúa: MAPA.md, rutas de riesgo, DELEGACION.md, init-harness
```
Confirma con Claude la tabla de zonas (roja/amarilla/verde) cuando te la muestre; es la decisión más importante del setup.

## 8. Prueba de humo (un change pequeño, riesgo bajo)
1. Claude Code: `/cambio "agregar un endpoint /health"` → issue + rama `feat/<n>-add-health-endpoint` + change de OpenSpec + PR draft.
2. OpenCode: `cd ../wt-add-health-endpoint && scripts/ejec` → `/ejecutar-cambio add-health-endpoint`.
3. En el PR: etiqueta `riesgo:bajo`, comentario de la Action y checks `test`, `clasificar`, `verificar` en verde.
4. Claude Code: `/juzgar-pr <número>` → archive + `docs/ESTADO.md` + merge.
5. Comprueba la guardia: pídele a Claude que edite un archivo de código (debe negarse y redirigir) y a OpenCode que edite `proposal.md` (debe bloquearse).
Si todo esto funciona, el harness está operativo.

## Checklist final
- [ ] `doctor.sh` sin ✗ y sin placeholders
- [ ] `main` protegida
- [ ] Prueba de humo mergeada
- [ ] `openspec/config.yaml` con reglas `[harness]` y `context` sembrado
- [ ] Estado del proyecto en `docs/ESTADO.md`, reglas siempre cargadas cortas
