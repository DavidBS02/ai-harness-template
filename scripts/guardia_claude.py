#!/usr/bin/env python3
"""Hook PreToolUse de Claude Code. Lógica en scripts/harness.py (guard_claude)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness  # noqa: E402
codigo, msg = harness.guard_claude(json.load(sys.stdin))
if msg:
    sys.stderr.write(msg + "\n")
sys.exit(codigo)
