# Utilidades comunes de los git hooks del harness.
ROOT="$(git rev-parse --show-toplevel)"
ROL="${HARNESS_ROL:-humano}"
OVERRIDE="${HARNESS_OVERRIDE:-0}"
cargar(){ grep -Ev '^\s*(#|$)' "$ROOT/$1" 2>/dev/null; }
coincide_prefijo(){ # coincide_prefijo <ruta> <archivo-de-prefijos>
  local f="$1" p; while IFS= read -r p; do [ -z "$p" ] && continue
    [ "$f" = "${p%/}" ] && return 0; case "$f" in "$p"*) return 0;; esac; done < <(cargar "$2"); return 1; }
coincide_regex(){ local re; re="$(cargar "$2" | paste -sd'|' -)"; [ -n "$re" ] && echo "$1" | grep -Eq "$re"; }
es_zona_roja(){ coincide_regex "$1" .harness/rutas-alto.txt; }
spec_autoriza_roja(){ bash "$ROOT/scripts/cambio.sh" roja; }
rechazo(){ printf '\n⛔ Harness (%s): %s\n   Cómo hacerlo bien: %s\n   Override consciente: HARNESS_OVERRIDE=1 (queda registrado en el commit)\n\n' "$ROL" "$1" "$2" >&2; exit 1; }
