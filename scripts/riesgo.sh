#!/usr/bin/env bash
# Riesgo del diff actual: bajo|medio|alto (detalle en stderr). Lógica en scripts/harness.py.
exec python3 "$(dirname "$0")/harness.py" riesgo "$@"
