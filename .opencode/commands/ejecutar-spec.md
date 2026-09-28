---
description: Implementa el spec indicado en la rama/worktree actual.
---
Implementa `docs/specs/$ARGUMENTS*.md` en esta rama.
1. Confirma con `git branch --show-current` que NO estás en main.
2. Usa @explorador para ubicar los archivos antes de editar.
3. Implementa paso a paso según el spec. Delega tests y docs a @mecanico.
4. Corre los tests tras cada paso. Commits pequeños.
5. Al terminar: corre `scripts/riesgo.sh` y anota el nivel.
   - Siempre: invoca @revisor-gratis y corrige lo crítico.
   - Si el nivel es medio o alto: después invoca @revisor-fuerte y corrige lo crítico.
   - Luego /handoff y crea el PR con `gh pr create --fill --body-file .github/PULL_REQUEST_TEMPLATE.md`.
Si el spec no alcanza para decidir algo, escribe la duda en HANDOFF.md y detente.
