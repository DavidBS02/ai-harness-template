#!/usr/bin/env bash
# Instala BMAD-METHOD y OpenSpec en el repo actual con la configuración del harness, sin pisar instalaciones existentes.
#   bash scripts/instalar-frameworks.sh [--idioma Spanish] [--sin-bmad] [--sin-openspec]
set -euo pipefail
IDIOMA="Spanish"; BMAD=1; OSPEC=1
while [ $# -gt 0 ]; do case "$1" in --idioma) IDIOMA="$2"; shift;; --sin-bmad) BMAD=0;; --sin-openspec) OSPEC=0;; esac; shift; done
LANG_OS="$(echo "$IDIOMA" | tr 'A-Z' 'a-z')"

if [ "$OSPEC" = 1 ]; then
  if [ -d openspec ]; then echo "OpenSpec ya instalado (openspec/ existe): no lo toco. Para refrescar skills: npx openspec update"
  else
    if [ -f package.json ]; then
      V=$(npm view @fission-ai/openspec version); echo "Fijando @fission-ai/openspec@$V como devDependency"
      npm i -D --save-exact "@fission-ai/openspec@$V"; CMD="npx openspec"
    else CMD="npx --yes @fission-ai/openspec@latest"; echo "Sin package.json: OpenSpec vía npx (fija la versión cuando haya package.json)"; fi
    $CMD init --tools claude,opencode,codex --language "$LANG_OS" || $CMD init --tools claude,opencode,codex
  fi
  if [ -f openspec/config.yaml ] && ! grep -q '\[harness\]' openspec/config.yaml; then
    if ! grep -q '^rules:' openspec/config.yaml; then
      cp openspec/config.yaml openspec/config.yaml.orig; cp .harness/openspec-config.base.yaml openspec/config.yaml
      echo "openspec/config.yaml sembrado con la base del harness (original en config.yaml.orig). Completa el context con /init-harness."
    else echo "openspec/config.yaml ya tiene reglas propias: /init-harness fusionará las [harness] sin tocar las tuyas."; fi
  fi
fi

if [ "$BMAD" = 1 ]; then
  if [ -d _bmad ]; then echo "BMAD ya instalado (_bmad/ existe): no lo toco. Para actualizar: npx bmad-method install"
  else
    COMUN=(--modules core,bmm --yes --communication-language "$IDIOMA" --document-output-language "$IDIOMA" --output-folder _bmad-output)
    npx --yes bmad-method@latest install "${COMUN[@]}" --tools claude-code,codex,opencode \
      || { echo "El instalador de BMAD no aceptó 'opencode'; instalo para claude-code y codex (OpenCode usará .agents/skills)."; \
           npx --yes bmad-method@latest install "${COMUN[@]}" --tools claude-code,codex; }
    for f in _bmad/core/config.yaml _bmad/bmm/config.yaml; do
      [ -f "$f" ] && grep -q 'output_folder: _bmad-output' "$f" || echo "⚠️  Revisa output_folder en $f (debe ser _bmad-output)"; done
  fi
fi
echo "Listo. Siguiente: claude → /descubrir"
