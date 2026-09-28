---
description: Revisión BMAD de un artefacto con otra familia de modelos. Uso: /revisar-artefacto <skill> <ruta>  (ej. /revisar-artefacto bmad-review _bmad-output/.../ARCHITECTURE-SPINE.md)
---
Primero corre `python3 scripts/harness.py ruta $1` y confirma que la clase es `revisar`; si no, detente y di dónde se corre.
Luego delega en @revisor-bmad: ejecutar la skill `$1` sobre `$2` y dejar la review en `_bmad-output/digests/`.
Haz commit solo de la review (`docs(bmad): review <tema>`).
