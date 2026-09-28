#!/usr/bin/env bash
# Diagnóstico completo. Herramientas y sesiones aquí; todo lo del harness (config, secretos, control, versiones,
# guardias, skills, presupuesto) en `python3 scripts/harness.py doctor`, que es la misma lógica que prueba el selftest.
#   bash scripts/doctor.sh            diagnóstico
#   bash scripts/doctor.sh --tests    además corre el selftest del harness
set -uo pipefail
ok(){ printf '  \033[32m✓\033[0m %s\n' "$1"; }; ko(){ printf '  \033[31m✗\033[0m %s\n' "$1"; FALLO=1; }; warn(){ printf '  \033[33m!\033[0m %s\n' "$1"; }
FALLO=0
echo "Herramientas:"
for b in git gh python3 claude opencode codex omniroute docker; do
  if command -v "$b" >/dev/null; then ok "$b $( ("$b" --version 2>/dev/null || true) | head -1)"; else
    case "$b" in git|python3) ko "$b no instalado (obligatorio)";; *) warn "$b no instalado";; esac; fi; done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null && ok "python3 ≥ 3.8" || ko "python3 < 3.8"
echo "Sesiones y entorno:"
gh auth status >/dev/null 2>&1 && ok "gh autenticado" || warn "gh sin sesión: gh auth login"
[ -n "${ANTHROPIC_API_KEY:-}" ] && ko "ANTHROPIC_API_KEY definida: Claude Code cobraría por API. Quítala." || ok "sin ANTHROPIC_API_KEY"
[ -n "${ANTHROPIC_BASE_URL:-}" ] && ko "ANTHROPIC_BASE_URL definida: Claude Code no debe pasar por proxies." || ok "sin ANTHROPIC_BASE_URL"
[ -n "${GH_TOKEN_AGENTES:-}" ] && ok "GH_TOKEN_AGENTES definido" || warn "GH_TOKEN_AGENTES no definido (token fine-grained para el contenedor)"
curl -s -m 2 http://localhost:20128/v1/models >/dev/null 2>&1 && ok "OmniRoute responde en :20128" || warn "OmniRoute no responde en :20128"
if command -v docker >/dev/null; then docker info >/dev/null 2>&1 && ok "docker en marcha" || warn "docker instalado pero detenido"; fi
echo "Harness:"
python3 scripts/harness.py doctor "$@" || FALLO=1
echo "Versiones (fijadas vs instaladas):"
python3 scripts/harness.py versiones | sed 's/^/  /'
[ "$FALLO" = 0 ] && echo "Resultado: sin errores." || { echo "Resultado: hay errores (✗). Corrígelos antes de trabajar con agentes."; exit 1; }
