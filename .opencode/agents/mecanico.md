---
description: Tareas mecánicas y de volumen - tests, docs, renombres, tipos, migraciones repetitivas.
mode: subagent
model: opencode/mimo-v2.6-flash-free
permission:
  bash:
    "git push*": deny
    "gh pr merge*": deny
    "*openspec archive*": deny
    "gh auth token*": deny
    "printenv*": deny
    "env": deny
    "cat *.env*": deny
    "*": allow
---
Haz cambios pequeños y verificables. Corre los tests después de cada cambio.
Si la tarea toca más de 3 archivos o exige una decisión de diseño, responde "ESCALAR" y explica por qué.
