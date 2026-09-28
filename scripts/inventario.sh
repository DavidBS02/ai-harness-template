#!/usr/bin/env bash
# Inventario mecánico del repo (sin LLM). Escribe docs/harness/INVENTARIO.md.
# Es la entrada de /descubrir: Claude lee esto en vez de recorrer el repo a mano.
set -uo pipefail
OUT=docs/harness/INVENTARIO.md; mkdir -p docs/harness
EXCL='node_modules|\.git/|dist/|build/|vendor/|\.venv|__pycache__|\.next|target/'
{
echo "# Inventario del repo — $(date +%F)"; echo
echo "## Tamaño"; echo '```'
git ls-files | grep -Ev "$EXCL" | wc -l | xargs echo "archivos versionados:"
git ls-files | grep -Ev "$EXCL" | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -15
echo '```'; echo
echo "## Estructura (2 niveles, con archivos por carpeta)"; echo '```'
git ls-files | grep -Ev "$EXCL" | awk -F/ 'NF>1{print $1"/"$2} NF==1{print "."}' | sed 's#/[^/]*\.[^/]*$##' | sort | uniq -c | sort -rn | head -40
echo '```'; echo
echo "## Manifiestos de stack encontrados"; echo '```'
ls package.json pyproject.toml requirements.txt go.mod Cargo.toml pom.xml build.gradle Gemfile composer.json Makefile Dockerfile docker-compose.yml 2>/dev/null || echo "(ninguno)"
echo '```'; echo
echo "## Tests y CI"; echo '```'
echo "archivos de test: $(git ls-files | grep -Ei '(^|/)(tests?|__tests__|spec)/|\.(test|spec)\.[a-z]+$|_test\.go$|test_.*\.py$' | wc -l)"
ls .github/workflows 2>/dev/null | sed 's/^/workflow: /' || echo "sin workflows"
echo '```'; echo
echo "## Archivos con más cambios (churn, últimos 12 meses) — candidatos a zona caliente"; echo '```'
git log --since="12 months ago" --name-only --pretty=format: 2>/dev/null | grep -Ev "^$|$EXCL" | sort | uniq -c | sort -rn | head -25
echo '```'; echo
echo "## Rutas que huelen a sensibles (por nombre)"; echo '```'
git ls-files | grep -Ei 'auth|login|session|oauth|jwt|password|secret|token|payment|billing|stripe|checkout|migrat|schema|crypt|\.env|infra|terraform|k8s|helm|Dockerfile|workflow' | grep -Ev "$EXCL" | head -40 || echo "(ninguna)"
echo '```'; echo
echo "## Archivos más grandes (posible complejidad)"; echo '```'
git ls-files | grep -Ev "$EXCL" | xargs -I{} sh -c 'wc -l "{}" 2>/dev/null' | sort -rn | head -15
echo '```'; echo
echo "## TODO / FIXME / HACK"; echo '```'
git grep -nE 'TODO|FIXME|HACK|XXX' -- . ':!*.lock' 2>/dev/null | wc -l | xargs echo "total:"
git grep -lE 'TODO|FIXME|HACK|XXX' -- . ':!*.lock' 2>/dev/null | head -15
echo '```'; echo
echo "## Contexto para agentes existente"; echo '```'
ls AGENTS.md CLAUDE.md .cursorrules .clinerules .windsurfrules 2>/dev/null || echo "(ninguno)"
echo '```'
} > "$OUT"
echo "escrito $OUT"
