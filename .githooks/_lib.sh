# Utilidades comunes de los git hooks del harness.
ROOT="$(git rev-parse --show-toplevel)"
ROL="${HARNESS_ROL:-humano}"
OVERRIDE="${HARNESS_OVERRIDE:-0}"
cargar(){ grep -Ev '^\s*(#|$)' "$ROOT/$1" 2>/dev/null; }
coincide_prefijo(){ # coincide_prefijo <ruta> <archivo-de-prefijos>
  local f="$1" p; while IFS= read -r p; do [ -z "$p" ] && continue
    [ "$f" = "${p%/}" ] && return 0; case "$f" in "$p"*) return 0;; esac; done < <(cargar "$2"); return 1; }
es_zona_roja(){ local re; re="$(cargar .harness/rutas-alto.txt | paste -sd'|' -)"; [ -n "$re" ] && echo "$1" | grep -Eq "$re"; }
spec_autoriza_roja(){ local rama n f; rama="$(git branch --show-current)"
  n="$(echo "$rama" | sed -nE 's#^(feat|fix)/([0-9]+)-.*#\2#p')"; [ -z "$n" ] && return 1
  f="$(ls "$ROOT"/docs/specs/"$n"-*.md 2>/dev/null | head -1)"; [ -n "$f" ] && grep -Eqi 'OpenCode-zona-roja:\s*autorizado' "$f"; }
rechazo(){ printf '\n⛔ Harness (%s): %s\n   Cómo hacerlo bien: %s\n   Override consciente: HARNESS_OVERRIDE=1 (queda registrado en el commit)\n\n' "$ROL" "$1" "$2" >&2; exit 1; }
