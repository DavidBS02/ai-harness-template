#!/usr/bin/env bash
# Instala el binario codebase-memory-mcp en la versión fijada de .harness/versiones.json → binarios,
# verificando el SHA-256 de la plataforma ANTES de extraer (spec: binario fijado y verificado).
# Sin install.sh oficial, sin `curl | bash`, sin gestores de paquetes. Idempotente.
#   bash scripts/cbm-instalar.sh
set -euo pipefail
RAIZ="$(git rev-parse --show-toplevel)"; cd "$RAIZ"

leer(){ python3 -c 'import json,sys
d = json.load(open(".harness/versiones.json"))["binarios"]["codebase-memory-mcp"]
print(eval("d" + sys.argv[1]))' "$1"; }

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
case "$OS" in darwin|linux) ;; *) echo "✗ plataforma no soportada: $OS (el harness asume darwin o linux)" >&2; exit 1;; esac
ARCH="$(uname -m)"
case "$ARCH" in x86_64|amd64) ARCH=amd64;; aarch64|arm64) ARCH=arm64;; *) echo "✗ arquitectura no soportada: $ARCH" >&2; exit 1;; esac
PLAT="$OS-$ARCH"
VERSION="$(leer "['version']")"
URL="$(leer "['url']")"
SHA="$(leer "['sha256']['$PLAT']" 2>/dev/null)" || SHA=""
[ -n "$SHA" ] || { echo "✗ sin SHA-256 fijado para $PLAT en .harness/versiones.json → binarios.codebase-memory-mcp (añádelo antes de instalar)" >&2; exit 1; }
URL="${URL//\{version\}/$VERSION}"; URL="${URL//\{os\}/$OS}"; URL="${URL//\{arch\}/$ARCH}"
DESTINO=".harness/bin/$PLAT/codebase-memory-mcp"

# idempotente: ya está la versión fijada → no descarga
if [ -x "$DESTINO" ]; then
  ACTUAL="$("$DESTINO" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
  if [ "$ACTUAL" = "$VERSION" ]; then echo "codebase-memory-mcp $VERSION ya instalado en $DESTINO"; exit 0; fi
  echo "⚠️  versión instalada ($ACTUAL) ≠ fijada ($VERSION): se reinstala"
fi

TMP="$(mktemp "${TMPDIR:-/tmp}/cbm-instalar.XXXXXX")"; trap 'rm -f "$TMP"' EXIT
echo "Descargando $URL"
curl -fsSL -o "$TMP" "$URL" || { echo "✗ descarga fallida" >&2; exit 1; }

sum(){ if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d" " -f1; else shasum -a 256 "$1" | cut -d" " -f1; fi; }
OBTENIDO="$(sum "$TMP")"
if [ "$OBTENIDO" != "$SHA" ]; then
  echo "✗ SHA-256 de $PLAT no coincide: esperaba $SHA, obtuve $OBTENIDO. No se instala nada (aborta sin binario utilizable)." >&2
  exit 1
fi
mkdir -p ".harness/bin/$PLAT"
# el binario está en la raíz del .tar.gz (verificado en HANDOFF.md §1.1)
tar -xzf "$TMP" -C ".harness/bin/$PLAT" codebase-memory-mcp
chmod 755 "$DESTINO"
echo "✓ codebase-memory-mcp $VERSION instalado en $DESTINO (SHA-256 verificado)"
