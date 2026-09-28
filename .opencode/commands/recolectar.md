---
description: Recolección BMAD barata. Uso: /recolectar <skill> <tema>  (ej. /recolectar bmad-deep-recon integración con el banco)
---
Primero corre `python3 scripts/harness.py ruta $1` y confirma que la clase es `recolectar`; si no, detente y di dónde se corre.
Luego delega en @recolector: ejecutar la skill `$1` sobre el tema "$ARGUMENTS" y dejar el digest en `_bmad-output/digests/`.
Haz commit solo del digest (`docs(bmad): digest <tema>`).
