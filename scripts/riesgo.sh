#!/usr/bin/env bash
# Clasifica el riesgo de un diff de forma determinista. Uso:
#   scripts/riesgo.sh            -> compara con main
#   scripts/riesgo.sh <ref>      -> compara con <ref>
# Salida: bajo | medio | alto  (y detalle en stderr)
set -euo pipefail
BASE="${1:-main}"
FILES=$(git diff --name-only "$BASE"...HEAD)
[ -z "$FILES" ] && { echo bajo; exit 0; }

NUM_FILES=$(echo "$FILES" | wc -l | tr -d ' ')
NUM_LINES=$(git diff --shortstat "$BASE"...HEAD | grep -oE '[0-9]+ (insertion|deletion)' | awk '{s+=$1} END {print s+0}')

# Rutas de riesgo ALTO: ajusta a tu repo
ALTO_RE='(^|/)(auth|login|session|oauth|payment|payments|billing|checkout|migrations?|schema|crypto|secrets?|\.env|infra|terraform|k8s|helm|Dockerfile|\.github/workflows)(/|$|\.)'
# Rutas de riesgo BAJO puro: docs, tests, config trivial
BAJO_RE='(^|/)(docs?|tests?|__tests__|spec|specs|fixtures?)(/|$)|\.(md|txt|json|ya?ml|toml|lock)$'

if echo "$FILES" | grep -Eq "$ALTO_RE"; then
  echo "alto: toca rutas sensibles:" >&2; echo "$FILES" | grep -E "$ALTO_RE" >&2
  echo alto; exit 0
fi

if [ "$NUM_FILES" -gt 5 ] || [ "$NUM_LINES" -gt 300 ]; then
  echo "medio: $NUM_FILES archivos, $NUM_LINES líneas" >&2
  echo medio; exit 0
fi

if echo "$FILES" | grep -Evq "$BAJO_RE"; then
  echo "medio: cambia código de producción ($NUM_FILES archivos, $NUM_LINES líneas)" >&2
  echo medio; exit 0
fi

echo "bajo: solo docs/tests/config ($NUM_FILES archivos)" >&2
echo bajo
