#!/usr/bin/env bash
# Crea labels de riesgo y protege main. Requiere: gh autenticado y remoto origin en GitHub.
set -euo pipefail
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Configurando $REPO"
for l in "riesgo:bajo:0E8A16" "riesgo:medio:FBCA04" "riesgo:alto:B60205"; do
  n="${l%:*}"; c="${l##*:}"; gh label create "$n" --color "$c" --force >/dev/null && echo "  label $n"; done
gh label create "feature" --color "1D76DB" --force >/dev/null || true
# Protección de main: PR obligatorio + checks ci y riesgo.
gh api -X PUT "repos/$REPO/branches/main/protection" \
  -H "Accept: application/vnd.github+json" \
  --input - > /dev/null << 'JSON' && echo "  main protegida (PR + checks ci, riesgo)"
{"required_status_checks":{"strict":true,"contexts":["test","clasificar"]},
 "enforce_admins":false,
 "required_pull_request_reviews":null,
 "restrictions":null,
 "allow_force_pushes":false,"allow_deletions":false}
JSON
echo "Listo."
