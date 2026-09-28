#!/usr/bin/env python3
"""Hook PreToolUse de Claude Code. FAIL-CLOSED: cualquier fallo (import, JSON, config) sale con 2 y bloquea.
Claude Code solo bloquea con exit 2; cualquier otro código deja pasar la acción (docs de hooks)."""
import json
import os
import sys

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import harness  # noqa: E402
    codigo, msg = harness.guard_claude(json.load(sys.stdin))
except SystemExit:
    raise
except Exception as e:  # noqa: BLE001
    if os.environ.get("HARNESS_OVERRIDE") == "1":
        sys.exit(0)
    codigo, msg = 2, f"⛔ Harness: el guardia falló ({e.__class__.__name__}: {e}); por seguridad se bloquea. Corre scripts/doctor.sh."
if msg:
    sys.stderr.write(msg + "\n")
sys.exit(codigo)
