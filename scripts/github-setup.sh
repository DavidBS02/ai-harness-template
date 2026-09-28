#!/usr/bin/env bash
# Crea labels de riesgo y protege main. Requiere: gh autenticado y remoto origin en GitHub.
set -euo pipefail
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
# --revision-humana: exige 1 review de CODEOWNERS. Úsalo solo cuando los agentes tengan su PROPIA cuenta (máquina):
# GitHub no deja aprobar el PR propio, así que con una sola identidad te bloquearías.
REVIEWS_JSON=null
[ "${1:-}" = "--revision-humana" ] && REVIEWS_JSON='{"require_code_owner_reviews":true,"required_approving_review_count":1,"dismiss_stale_reviews":true}'
echo "Configurando $REPO"
for l in "riesgo:bajo:0E8A16" "riesgo:medio:FBCA04" "riesgo:alto:B60205"; do
  n="${l%:*}"; c="${l##*:}"; gh label create "$n" --color "$c" --force >/dev/null && echo "  label $n"; done
gh label create "feature" --color "1D76DB" --force >/dev/null || true
gh label create "plano-de-control" --color "B60205" --description "El PR toca archivos que controlan a los agentes" --force >/dev/null && echo "  label plano-de-control"
gh label create "deuda" --color "5319E7" --description "Deuda abierta: se cierra solo tras verificar contra su archivo dueño" --force >/dev/null && echo "  label deuda"
gh label create "verificacion-diferida" --color "0052CC" --description "Verificación que depende del futuro; si falla, change nuevo" --force >/dev/null && echo "  label verificacion-diferida"
# Protección de main: PR obligatorio + checks ci y riesgo.
gh api -X PUT "repos/$REPO/branches/main/protection" \
  -H "Accept: application/vnd.github+json" \
  --input - > /dev/null 2>/tmp/gh-proteccion.err << JSON && echo "  main protegida (checks test, clasificar, verificar; admins incluidos)" || { echo "  ⚠️  no se pudo proteger main: $(head -c 200 /tmp/gh-proteccion.err)"; echo "     En repos privados del plan gratuito GitHub no ofrece protección: los gates avisan pero NO bloquean el merge (docs/SEGURIDAD.md)."; }
{"required_status_checks":{"strict":true,"contexts":["test","clasificar","verificar"]},
 "enforce_admins":true,
 "required_pull_request_reviews":${REVIEWS_JSON},
 "restrictions":null,
 "allow_force_pushes":false,"allow_deletions":false}
JSON
echo "Listo."
