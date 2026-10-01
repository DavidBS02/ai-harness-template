#!/usr/bin/env bash
# Re-indexa la memoria de código de este repo (D7). Uso: scripts/cbm-indexar.sh [--fondo]
# Lo llaman a mano (/init-harness, tras un rebase) y en segundo plano los hooks post-merge y
# post-checkout. En --fondo no imprime nada (los hooks no pueden ensuciar la salida de git).
#   1. Si la memoria está apagada, sale con 0 sin indexar (en primer plano lo dice).
#   2. Lock con mkdir + PID: dos disparos a la vez indexa uno solo. Un lock con PID muerto o
#      de más de 30 minutos se considera huérfano y se retira.
#   3. verificar-secretos (fail-closed) y luego la invalidación de D6.
#   4. cbm cli index_repository y marcar-indexado.
# En --fondo el trabajo pesado va desacoplado (nohup, log en .harness/cbm/ultimo-indexado.log)
# y el script vuelve de inmediato con 0.
#
# --lock-comprado es interno: lo usa el worker en segundo plano, que hereda el lock ya tomado
# por el proceso padre en lugar de competir por él.
set -uo pipefail
RAIZ="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$RAIZ" ] || RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
FONDO=0
LOCK_COMPRADO=0
case "${1:-}" in
  --fondo) FONDO=1;;
  --lock-comprado) FONDO=1; LOCK_COMPRADO=1;;
esac

# habilitado y estado_dir de harness.json → mcp.codebase_memory (mismo override que harness.py)
DATOS="$(python3 -c '
import json, os, sys
cfg = os.environ.get("HARNESS_CONFIG") or sys.argv[1]
mcp = json.load(open(cfg)).get("mcp", {}).get("codebase_memory", {})
print("true" if mcp.get("habilitado") else "false")
print(mcp.get("estado_dir") or ".harness/cbm")
' "$RAIZ/harness.json" 2>/dev/null)" || DATOS=""
if [ -z "$DATOS" ]; then
  [ "$FONDO" -eq 1 ] || echo "! memoria de código: no se pudo leer harness.json desde $RAIZ; no se indexa" >&2
  exit 0
fi
{ read -r HABILITADO; read -r ESTADO_REL; } <<<"$DATOS"
case "$ESTADO_REL" in /*) ESTADO="$ESTADO_REL";; *) ESTADO="$RAIZ/$ESTADO_REL";; esac
if [ "$HABILITADO" != "true" ]; then
  [ "$FONDO" -eq 1 ] || echo "Memoria de código apagada (harness.json → mcp.codebase_memory.habilitado: false). Enciéndela, corre: python3 scripts/harness.py sync y reintenta."
  exit 0
fi

LOCK="$ESTADO/indexando.lock"
edad_lock() {
  local m
  m="$(stat -f %m "$LOCK" 2>/dev/null || stat -c %Y "$LOCK" 2>/dev/null || echo 0)"
  echo $(( $(date +%s) - m ))
}
tomar_lock() {
  mkdir -p "$ESTADO" 2>/dev/null || true
  mkdir "$LOCK" 2>/dev/null && return 0
  # Ya hay lock: está vivo si su PID existe y el lock tiene menos de 30 minutos
  local PID
  PID="$(cat "$LOCK/pid" 2>/dev/null || true)"
  case "$PID" in ''|*[!0-9]*) :;; *)
    if kill -0 "$PID" 2>/dev/null && [ "$(edad_lock)" -lt 1800 ]; then return 1; fi;;
  esac
  rm -rf "$LOCK" 2>/dev/null || true
  mkdir "$LOCK" 2>/dev/null && return 0
  return 1
}

if [ "$LOCK_COMPRADO" -eq 0 ] && ! tomar_lock; then
  [ "$FONDO" -eq 1 ] || echo "Ya hay un indexado en curso; nada que hacer."
  exit 0
fi
mkdir -p "$ESTADO"

if [ "$FONDO" -eq 1 ] && [ "$LOCK_COMPRADO" -eq 0 ]; then
  # El padre NO pone trap: el lock lo suelta el worker al terminar. Sus mensajes van al log.
  nohup "$0" --lock-comprado >> "$ESTADO/ultimo-indexado.log" 2>&1 &
  echo $! > "$LOCK/pid" 2>/dev/null || true
  disown 2>/dev/null || true
  exit 0
fi
trap 'rm -rf "$LOCK" 2>/dev/null || true' EXIT

printf '\n=== %s ===\n' "$(date '+%Y-%m-%d %H:%M:%S')"
python3 "$RAIZ/scripts/harness.py" cbm verificar-secretos || exit 1
python3 "$RAIZ/scripts/harness.py" cbm invalidar-cache || exit 1
"$RAIZ/scripts/cbm" cli --quiet index_repository --repo-path "$RAIZ" || exit 1
python3 "$RAIZ/scripts/harness.py" cbm marcar-indexado || exit 1
echo "índice al día"