---
description: Implementa un change de OpenSpec en su worktree, revisa, y deja el PR listo para juzgar.
---
Vas a implementar el change `$ARGUMENTS` de OpenSpec.
1. Comprueba que estás en la rama `feat/<n>-$ARGUMENTS` (`git branch --show-current`) y nunca en main. Lee completo `openspec/changes/$ARGUMENTS/` (proposal, design, specs, tasks) y la sección "Puntos de entrada" de AGENTS.md.
2. Implementa con la skill de apply de OpenSpec (`/opsx-apply $ARGUMENTS`), tarea por tarea y en orden:
   - Usa @explorador para ubicar código antes de editar y delega tests y docs a @mecanico.
   - Corre typecheck y tests antes de marcar cada tarea en `tasks.md`. Haz un commit pequeño por tarea o bloque.
   - Las tareas "(manual)" no las marques: déjalas listadas en HANDOFF.md para el usuario.
   - NUNCA edites proposal.md, design.md ni specs/ (las guardias lo bloquean). Si una tarea revela un hueco del spec, o un ajuste de esquema, config o AD, escríbelo en HANDOFF.md y DETENTE: lo resuelve el arquitecto con `/opsx:update`.
3. Al terminar, corre `bash scripts/riesgo.sh` y anota el nivel (manda el más alto entre ese y el `Riesgo:` del proposal).
   - Siempre: @revisor-gratis → corrige lo crítico.
   - Riesgo medio o alto: después @revisor-fuerte → corrige lo crítico.
4. `/handoff`, push y marca el PR como listo (`gh pr ready`). Pega en el cuerpo del PR el resumen de cada revisión y marca las casillas que correspondan.
No archives ni mergees: eso es `/juzgar-pr` en Claude Code.
