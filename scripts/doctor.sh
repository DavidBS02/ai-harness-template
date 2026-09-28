#!/usr/bin/env bash
# Verifica herramientas, logins y placeholders pendientes.
set -uo pipefail
ok(){ printf '  \033[32m✓\033[0m %s\n' "$1"; }; ko(){ printf '  \033[31m✗\033[0m %s\n' "$1"; }; warn(){ printf '  \033[33m!\033[0m %s\n' "$1"; }
echo "Herramientas:"
for b in git gh node claude opencode codex omniroute; do command -v "$b" >/dev/null && ok "$b $(($b --version 2>/dev/null || true) | head -1)" || ko "$b no instalado"; done
echo "Logins:"
gh auth status >/dev/null 2>&1 && ok "gh autenticado" || ko "gh: ejecuta gh auth login"
[ -n "${ANTHROPIC_API_KEY:-}" ] && warn "ANTHROPIC_API_KEY está definida: Claude Code cobrará por API en vez de usar tu Pro. Quítala." || ok "sin ANTHROPIC_API_KEY (Claude Code usará tu suscripción)"
[ -n "${ANTHROPIC_BASE_URL:-}" ] && warn "ANTHROPIC_BASE_URL está definida: Claude Code NO debe pasar por proxies." || ok "sin ANTHROPIC_BASE_URL"
curl -s -m 2 http://localhost:20128/v1/models >/dev/null 2>&1 && ok "OmniRoute respondiendo en :20128" || warn "OmniRoute no responde en :20128 (ejecuta: omniroute)"
[ -n "${OMNIROUTE_API_KEY:-}" ] && ok "OMNIROUTE_API_KEY definida" || warn "OMNIROUTE_API_KEY no definida (la usa opencode.json)"
echo "Método (BMAD + OpenSpec):"
[ -d openspec ] && ok "OpenSpec instalado" || warn "OpenSpec no instalado: bash scripts/instalar-frameworks.sh"
[ -d _bmad ] && ok "BMAD instalado" || warn "BMAD no instalado: bash scripts/instalar-frameworks.sh"
if [ -f package.json ] && [ -d openspec ]; then grep -q '"@fission-ai/openspec": "[0-9]' package.json && ok "OpenSpec fijado como devDependency" || warn "OpenSpec sin versión fija en package.json (validate/archive son contrato: fíjala)"; fi
[ -f openspec/config.yaml ] && { grep -q '## Harness' openspec/config.yaml && ok "config.yaml con reglas [harness]" || warn "openspec/config.yaml sin reglas del harness: /init-harness"; }
if [ -d openspec ]; then (npx --no-install openspec validate --all >/dev/null 2>&1 || npx --yes @fission-ai/openspec validate --all >/dev/null 2>&1) && ok "openspec validate --all" || ko "openspec validate --all falla"; fi
if [ -d _bmad-output ] && git check-ignore -q _bmad-output 2>/dev/null; then warn "_bmad-output/ está en .gitignore: OpenCode no verá el SPEC/spine en su worktree (docs/LECCIONES.md §9)"; fi
[ -f .claude/rules/workflow-routing.md ] && [ "$(wc -l < .claude/rules/workflow-routing.md)" -gt 120 ] && warn "workflow-routing.md tiene más de 120 líneas: saca el estado a issues/DECISIONES.md con /init-harness (docs/LECCIONES.md §8)"
echo "Harness:"
python3 -c "import json;json.load(open('harness.json'))" 2>/dev/null && ok "harness.json válido" || ko "harness.json inválido o ausente"
python3 scripts/harness.py sync --check >/dev/null 2>&1 && ok "adaptadores al día con harness.json" || warn "adaptadores desactualizados: python3 scripts/harness.py sync"
SM=$(python3 scripts/harness.py skills 2>/dev/null | grep -c "sin mapear:" || true); [ "$SM" = "0" ] && ok "todas las skills instaladas están clasificadas" || ko "$SM skill(s) sin mapear (bloqueadas): python3 scripts/harness.py skills → /clasificar-skill <nombre> en Claude Code"
for f in .githooks/pre-commit scripts/harness.py scripts/arq scripts/ejec; do [ -x "$f" ] || ko "$f no es ejecutable (chmod +x; y en git: git update-index --chmod=+x $f)"; done
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts -p 'test_*.py' >/dev/null 2>&1 && ok "selftest del harness en verde" || ko "selftest del harness falla: python3 -m unittest discover -s scripts -p 'test_*.py' -v"
echo "Guardias:"
[ "$(git config core.hooksPath)" = ".githooks" ] && ok "git hooks activos" || ko "git hooks inactivos: git config core.hooksPath .githooks"
[ -f .claude/settings.json ] && grep -q guardia_claude .claude/settings.json && ok "hook de Claude Code configurado" || ko "falta .claude/settings.json con el hook"
[ -f .opencode/plugins/guardia.ts ] && ok "plugin de OpenCode presente" || ko "falta .opencode/plugins/guardia.ts"
command -v python3 >/dev/null && ok "python3 (lo usa el hook de Claude)" || ko "python3 no instalado: el hook de Claude no funcionará"
echo "  Lanza siempre con scripts/arq (Claude) y scripts/ejec (OpenCode) para activar los roles."
echo "Placeholders pendientes:"
P=0; for f in AGENTS.md harness.json .github/workflows/ci.yml; do
  [ -f "$f" ] && grep -Eq 'REEMPLAZA-CON-ID|<una línea>|<comando>|Reemplaza este paso' "$f" && { warn "$f tiene placeholders"; P=1; }; done
[ $P -eq 0 ] && ok "sin placeholders"
echo "Ejecuta scripts/arq y luego /descubrir (o /init-harness) para llenar lo que falte."
