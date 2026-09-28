#!/usr/bin/env bash
# Copia el harness a un proyecto (verde o existente) sin pisar lo que ya exista.
# Uso: bash scripts/bootstrap.sh /ruta/a/tu/proyecto
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:?Uso: bootstrap.sh /ruta/a/tu/proyecto}"
mkdir -p "$DEST"; cd "$DEST"
[ -d .git ] || { git init -q; git checkout -q -b main 2>/dev/null || true; echo "git init en $DEST"; }

copiar() { # copiar <rel> ; no sobrescribe
  local rel="$1"; if [ -e "$DEST/$rel" ]; then echo "  existe, no toco: $rel"; else mkdir -p "$(dirname "$DEST/$rel")"; cp "$HERE/$rel" "$DEST/$rel"; echo "  + $rel"; fi; }

echo "Copiando harness a $DEST"
for f in HANDOFF.md opencode.json harness.json \
  .claude/commands/init-harness.md .claude/commands/spec.md .claude/commands/juzgar-pr.md .claude/commands/handoff.md \
  .opencode/agents/explorador.md .opencode/agents/mecanico.md .opencode/agents/contexto-largo.md \
  .opencode/agents/revisor-gratis.md .opencode/agents/revisor-fuerte.md \
  .opencode/commands/ejecutar-spec.md .opencode/commands/handoff.md \
  scripts/riesgo.sh scripts/doctor.sh scripts/github-setup.sh \
  .github/PULL_REQUEST_TEMPLATE.md .github/ISSUE_TEMPLATE/feature.md .github/workflows/ci.yml .github/workflows/riesgo.yml \
  docs/PLAYBOOK.md docs/ONBOARDING.md docs/INTEGRACION-FRAMEWORK.md docs/specs/_plantilla.md; do copiar "$f"; done
chmod +x scripts/*.sh

# AGENTS.md y CLAUDE.md: si existen, no se pisan; se añade el import/sección al final.
if [ -e AGENTS.md ]; then
  grep -q "## Harness de copilotos" AGENTS.md || { printf '\n\n' >> AGENTS.md; sed -n '/## Reglas de trabajo/,$p' "$HERE/AGENTS.md" | sed '1s/.*/## Harness de copilotos (reglas de trabajo con agentes)/' >> AGENTS.md; echo "  ~ AGENTS.md: sección añadida"; }
else copiar AGENTS.md; fi
if [ -e CLAUDE.md ]; then
  grep -q "@AGENTS.md" CLAUDE.md || { printf '\n@AGENTS.md\n' >> CLAUDE.md; echo "  ~ CLAUDE.md: @AGENTS.md añadido"; }
else copiar CLAUDE.md; fi

echo
echo "Listo. Siguientes pasos:"
echo "  1. bash scripts/doctor.sh          (herramientas y logins)"
echo "  2. bash scripts/github-setup.sh    (labels + protección de main; requiere remoto en GitHub)"
echo "  3. claude  ->  /init-harness       (adapta AGENTS.md, riesgo.sh y ci.yml a este repo)"
