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
echo "Placeholders pendientes:"
P=0; for f in AGENTS.md opencode.json .opencode/agents/revisor-gratis.md .opencode/agents/revisor-fuerte.md .github/workflows/ci.yml; do
  [ -f "$f" ] && grep -Eq 'REEMPLAZA-CON-ID|<una línea>|<comando>|Reemplaza este paso' "$f" && { warn "$f tiene placeholders"; P=1; }; done
[ $P -eq 0 ] && ok "sin placeholders"
echo "Ejecuta 'claude' y luego /init-harness para llenar lo que falte."
