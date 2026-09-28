#!/usr/bin/env bash
# Regenera docs/ESTADO.md desde openspec/ y los issues de GitHub (deuda, verificacion-diferida).
exec python3 "$(dirname "$0")/harness.py" estado "$@"
