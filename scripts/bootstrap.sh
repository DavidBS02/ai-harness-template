#!/usr/bin/env bash
# Copia el harness a un proyecto (verde o existente) sin pisar lo que ya exista.
# Uso: bash scripts/bootstrap.sh /ruta/a/tu/proyecto
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:?Uso: bootstrap.sh /ruta/a/tu/proyecto}"
mkdir -p "$DEST"; cd "$DEST"
[ -d .git ] || { git init -q; git checkout -q -b main 2>/dev/null || true; echo "git init en $DEST"; }

copiar() { # copiar <rel> ; no sobrescribe: si ya existe y difiere, deja la versión del harness en .harness/entrantes/ para fusionarla con /init-harness
  local rel="$1"
  if [ -e "$DEST/$rel" ]; then
    if ! cmp -s "$HERE/$rel" "$DEST/$rel"; then mkdir -p "$(dirname "$DEST/.harness/entrantes/$rel")"; cp "$HERE/$rel" "$DEST/.harness/entrantes/$rel"; echo "  existe, no toco: $rel (versión del harness en .harness/entrantes/ para /init-harness)"; fi
  else mkdir -p "$(dirname "$DEST/$rel")"; cp "$HERE/$rel" "$DEST/$rel"; echo "  + $rel"; fi; }

echo "Copiando harness a $DEST"
for f in HANDOFF.md opencode.json harness.json \
  .claude/commands/init-harness.md .claude/commands/cambio.md .claude/commands/juzgar-pr.md .claude/commands/handoff.md .claude/rules/workflow-routing.md \
  .opencode/agents/explorador.md .opencode/agents/mecanico.md .opencode/agents/contexto-largo.md \
  .opencode/agents/revisor-gratis.md .opencode/agents/revisor-fuerte.md \
  .opencode/commands/ejecutar-cambio.md .opencode/commands/handoff.md \
  scripts/riesgo.sh scripts/cambio.sh scripts/instalar-frameworks.sh scripts/inventario.sh scripts/doctor.sh scripts/github-setup.sh \
  .harness/rutas-alto.txt .harness/rutas-bajo.txt .harness/openspec-config.base.yaml .harness/permisos-arquitecto.txt .harness/protegidas-ejecutor.txt \
  .claude/settings.json scripts/guardia_claude.py scripts/arq scripts/ejec .opencode/plugins/guardia.ts \
  .githooks/_lib.sh .githooks/pre-commit .githooks/commit-msg .githooks/pre-push .github/workflows/proceso.yml \
  .claude/commands/descubrir.md .opencode/commands/resumir-modulos.md \
  docs/harness/MAPA.md docs/harness/DELEGACION.md \
  .github/PULL_REQUEST_TEMPLATE.md .github/ISSUE_TEMPLATE/feature.md .github/workflows/ci.yml .github/workflows/riesgo.yml \
  docs/harness-guide.md docs/LECCIONES.md docs/ESTADO.md docs/ONBOARDING.md; do copiar "$f"; done
chmod +x scripts/*.sh scripts/arq scripts/ejec scripts/guardia_claude.py .githooks/* 2>/dev/null || true
git config core.hooksPath .githooks && echo "  git hooks activos (.githooks)"

# AGENTS.md y CLAUDE.md: si existen, no se pisan; se añade el import/sección al final.
if [ -e AGENTS.md ]; then
  grep -q "## Harness de copilotos" AGENTS.md || { printf '\n\n' >> AGENTS.md; sed -n '/## Reglas de trabajo/,$p' "$HERE/AGENTS.md" | sed '1s/.*/## Harness de copilotos (reglas de trabajo con agentes)/' >> AGENTS.md; echo "  ~ AGENTS.md: sección añadida"; }
else copiar AGENTS.md; fi
if [ -e CLAUDE.md ]; then
  grep -q "@AGENTS.md" CLAUDE.md || { printf '\n@AGENTS.md\n' >> CLAUDE.md; echo "  ~ CLAUDE.md: @AGENTS.md añadido"; }
  grep -q "@.claude/rules/workflow-routing.md" CLAUDE.md || { printf '@.claude/rules/workflow-routing.md\n' >> CLAUDE.md; echo "  ~ CLAUDE.md: regla de routing importada"; }
  grep -q "Guardia de rol" CLAUDE.md || { printf '\n' >> CLAUDE.md; sed -n '/^## Guardia de rol/,$p' "$HERE/CLAUDE.md" >> CLAUDE.md; echo "  ~ CLAUDE.md: guardia de rol añadida"; }
else copiar CLAUDE.md; fi

echo
echo "Listo. Siguientes pasos:"
echo "  1. bash scripts/doctor.sh          (herramientas y logins)"
echo "  2. bash scripts/github-setup.sh    (labels + protección de main; requiere remoto en GitHub)"
echo "  3. bash scripts/instalar-frameworks.sh   (BMAD + OpenSpec; no toca instalaciones existentes)"
echo "  4. claude  ->  /descubrir          (Claude entiende el proyecto, decide el routing y aplica /init-harness)"
