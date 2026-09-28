#!/usr/bin/env bash
# Datos del change de la rama: id|issue|propuesta|riesgo|nivel|roja. Lógica en scripts/harness.py.
exec python3 "$(dirname "$0")/harness.py" cambio "$@"
