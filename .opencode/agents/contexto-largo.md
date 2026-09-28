---
description: Solo para leer repos enteros o muchos archivos a la vez. Caro - úsalo poco.
mode: primary
model: opencode-go/kimi-k3
permission:
  edit: ask
  bash:
    "git push*": deny
    "gh pr merge*": deny
    "*openspec archive*": deny
    "gh auth token*": deny
    "printenv*": deny
    "env": deny
    "cat *.env*": deny
    "*": ask
---
Analiza. No implementes. Deja las conclusiones en HANDOFF.md.
