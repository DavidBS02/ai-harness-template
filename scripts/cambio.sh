#!/usr/bin/env bash
# Utilidades del change de OpenSpec asociado a una rama.
#   scripts/cambio.sh id        -> change-id de la rama (feat|fix/<n>-<id> o feat|fix/<id>)
#   scripts/cambio.sh issue     -> número de issue de la rama, si lo tiene
#   scripts/cambio.sh propuesta -> ruta del proposal.md (activo o archivado), si existe
#   scripts/cambio.sh riesgo    -> bajo|medio|alto declarado en ## Harness, si existe
#   scripts/cambio.sh roja      -> exit 0 si el proposal autoriza a OpenCode en zona roja
# La rama sale de HARNESS_BRANCH (CI) o de git.
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RAMA="${HARNESS_BRANCH:-$(git branch --show-current 2>/dev/null)}"
id(){ echo "$RAMA" | sed -nE 's#^(feat|fix)/([0-9]+-)?([a-z0-9][a-z0-9-]*)$#\3#p'; }
issue(){ echo "$RAMA" | sed -nE 's#^(feat|fix)/([0-9]+)-.*#\2#p'; }
propuesta(){ local i; i="$(id)"; [ -z "$i" ] && return 1
  if [ -f "$ROOT/openspec/changes/$i/proposal.md" ]; then echo "$ROOT/openspec/changes/$i/proposal.md"; return 0; fi
  local a; a="$(ls -d "$ROOT"/openspec/changes/archive/*-"$i" 2>/dev/null | tail -1)"
  [ -n "$a" ] && [ -f "$a/proposal.md" ] && { echo "$a/proposal.md"; return 0; }; return 1; }
riesgo(){ local p; p="$(propuesta)" || return 1
  grep -Eio '^[-* ]*Riesgo:\s*(bajo|medio|alto)' "$p" | tail -1 | grep -Eio '(bajo|medio|alto)' | tr 'A-Z' 'a-z'; }
roja(){ local p; p="$(propuesta)" || return 1; grep -Eqi 'OpenCode-zona-roja:\s*autorizado' "$p"; }
case "${1:-id}" in id) id;; issue) issue;; propuesta) propuesta;; riesgo) riesgo;; roja) roja;; *) echo "uso: cambio.sh id|issue|propuesta|riesgo|roja" >&2; exit 2;; esac
