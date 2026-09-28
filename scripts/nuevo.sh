#!/usr/bin/env bash
# Parte mecánica de un cambio, sin gastar tokens: issue (opcional), rama y worktree (opcional).
#   scripts/nuevo.sh <change-id> [--nivel 0|1|2|3] [--issue "título"] [--worktree]
# Nivel 0 → rama fix/<id> · Nivel 1 → feat/<id> · Nivel 2-3 → feat/<n>-<id> (crea issue si pasas --issue)
set -euo pipefail
ID="${1:?uso: nuevo.sh <change-id> [--nivel N] [--issue \"título\"] [--worktree]}"; shift
[[ "$ID" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "change-id en kebab-case: verbo-objeto (ej. add-dark-mode)" >&2; exit 2; }
NIVEL=2; TITULO=""; WT=0
while [ $# -gt 0 ]; do case "$1" in --nivel) NIVEL="$2"; shift;; --issue) TITULO="$2"; shift;; --worktree) WT=1;; esac; shift; done
N=""
if [ "$NIVEL" -ge 2 ]; then
  [ -n "$TITULO" ] || { echo "nivel $NIVEL necesita issue: pasa --issue \"título\"" >&2; exit 2; }
  URL=$(gh issue create --title "$TITULO" --body "Change de OpenSpec: \`$ID\` (nivel $NIVEL)" --label feature); N="${URL##*/}"
  echo "issue #$N"
fi
case "$NIVEL" in 0) RAMA="fix/$ID";; 1) RAMA="feat/$ID";; *) RAMA="feat/$N-$ID";; esac
git fetch -q origin main 2>/dev/null || true
BASE=$(git rev-parse --verify -q origin/main >/dev/null && echo origin/main || echo main)
if [ "$WT" = 1 ]; then git worktree add "../wt-$ID" -b "$RAMA" "$BASE" >/dev/null; echo "worktree ../wt-$ID en rama $RAMA"
else git checkout -q -b "$RAMA" "$BASE"; echo "rama $RAMA"; fi
echo "RAMA=$RAMA"; [ -n "$N" ] && echo "ISSUE=$N"
