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

## 6. Adaptar al repo
```bash
bash scripts/doctor.sh
claude
> /init-harness
```

## 7. Prueba de humo (una feature pequeña, riesgo bajo)
1. Claude Code: `/spec "agregar un endpoint /health"`.
2. OpenCode (en el worktree): `/ejecutar-spec <issue>`.
3. Revisa que el PR tenga la etiqueta `riesgo:bajo` y el comentario de la Action.
4. Claude Code: `/juzgar-pr <número>`.
Si esto funciona, el harness está operativo.

## Checklist final
- [ ] `doctor.sh` sin ✗ y sin placeholders
- [ ] `main` protegida
- [ ] Prueba de humo mergeada
- [ ] Tu framework de trabajo conectado (docs/INTEGRACION-FRAMEWORK.md)
