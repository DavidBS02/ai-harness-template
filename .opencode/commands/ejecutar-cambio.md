---
description: Implementa un change de OpenSpec, lo revisa según su riesgo y deja el PR listo para juzgar.
---
Vas a implementar el change `$ARGUMENTS`.
1. `git branch --show-current` debe ser `feat/$ARGUMENTS` o `feat/<n>-$ARGUMENTS`, nunca main. Lee completo `openspec/changes/$ARGUMENTS/` y la sección "Puntos de entrada" de AGENTS.md.
2. Implementa con `/opsx-apply $ARGUMENTS`, tarea por tarea:
   - @explorador para ubicar código; @mecanico para tests y docs.
   - typecheck y tests antes de marcar cada tarea en `tasks.md`; un commit pequeño por tarea o bloque.
   - Las tareas "(manual)" no las marques: déjalas en HANDOFF.md.
   - NUNCA edites proposal, design ni specs (las guardias lo bloquean). Si falta algo del spec o aparece un ajuste de esquema, config o AD: HANDOFF.md y DETENTE (el arquitecto corre /opsx:update).
3. `python3 scripts/harness.py nivel` → nivel, riesgo y requisitos. Según eso:
   - Revisión 1 siempre (nivel ≥ 1): @revisor-gratis → corrige lo crítico.
   - Revisión 2 si el riesgo es medio o alto: @revisor-fuerte → corrige lo crítico.
4. `/handoff`, push y `gh pr ready`. En el cuerpo del PR, pega el resumen de cada revisión y marca sus casillas.
No archives ni mergees: eso es /juzgar-pr en Claude Code.
