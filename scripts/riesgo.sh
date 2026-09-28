#!/usr/bin/env bash
# Clasifica el riesgo de un diff de forma determinista, leyendo .harness/rutas-alto.txt y rutas-bajo.txt.
#   scripts/riesgo.sh [ref]   (por defecto compara con main)
# Salida: bajo | medio | alto ; detalle en stderr.
set -euo pipefail
BASE="${1:-main}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
UMBRAL_ARCHIVOS="${UMBRAL_ARCHIVOS:-5}"; UMBRAL_LINEAS="${UMBRAL_LINEAS:-300}"
cargar(){ grep -Ev '^\s*(#|$)' "$1" 2>/dev/null | paste -sd'|' -; }
ALTO_RE="$(cargar "$HERE/.harness/rutas-alto.txt")"; BAJO_RE="$(cargar "$HERE/.harness/rutas-bajo.txt")"
[ -z "$ALTO_RE" ] && ALTO_RE='(^|/)(auth|payments?|migrations?|secrets?)(/|$)'
[ -z "$BAJO_RE" ] && BAJO_RE='(^|/)(docs?|tests?)(/|$)|\.md$'

DECLARADO="$(bash "$HERE/scripts/cambio.sh" riesgo 2>/dev/null || true)"
nivel_max(){ local a="$1" b="${2:-bajo}"; for n in alto medio; do [ "$a" = "$n" ] || [ "$b" = "$n" ] && { echo "$n"; return; }; done; echo bajo; }
emitir(){ local n; n="$(nivel_max "$1" "$DECLARADO")"; [ -n "$DECLARADO" ] && [ "$n" != "$1" ] && echo "  (sube a $n por el Riesgo: declarado en el proposal)" >&2; echo "$n"; exit 0; }
FILES=$(git diff --name-only "$BASE"...HEAD); [ -z "$FILES" ] && emitir bajo
NUM_FILES=$(echo "$FILES" | wc -l | tr -d ' ')
NUM_LINES=$(git diff --shortstat "$BASE"...HEAD | grep -oE '[0-9]+ (insertion|deletion)' | awk '{s+=$1} END {print s+0}')

if echo "$FILES" | grep -Eq "$ALTO_RE"; then
  echo "alto: toca rutas sensibles:" >&2; echo "$FILES" | grep -E "$ALTO_RE" | sed 's/^/  /' >&2; emitir alto; fi
if [ "$NUM_FILES" -gt "$UMBRAL_ARCHIVOS" ] || [ "$NUM_LINES" -gt "$UMBRAL_LINEAS" ]; then
  echo "medio: $NUM_FILES archivos, $NUM_LINES líneas" >&2; emitir medio; fi
if echo "$FILES" | grep -Evq "$BAJO_RE"; then
  echo "medio: cambia código de producción ($NUM_FILES archivos, $NUM_LINES líneas)" >&2; emitir medio; fi
echo "bajo: solo docs/tests/config ($NUM_FILES archivos)" >&2; emitir bajo
