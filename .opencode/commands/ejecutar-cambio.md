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
3. `python3 scripts/harness.py nivel` → nivel, riesgo y requisitos. Haz commit de todo el código ANTES de revisar: la evidencia queda atada a ese commit y se invalida si después cambias código.
   - Revisión 1 siempre (nivel ≥ 1): @revisor-gratis. Guarda su salida completa en `/tmp/rev1.md` y regístrala:
     `python3 scripts/harness.py revision registrar --revisor revisor-gratis --modelo <id del modelo que respondió> --veredicto APROBAR|CORREGIR --hallazgos /tmp/rev1.md`
   - Revisión 2 si el riesgo es medio o alto: @revisor-fuerte, igual, con `--revisor revisor-fuerte`.
   - Si el veredicto es CORREGIR: corrige, commit, y repite la revisión (cada vuelta cuenta contra el presupuesto: `python3 scripts/harness.py presupuesto`).
   - Nunca escribas un registro sin haber corrido el revisor: el registro guarda su salida y su modelo.
4. Commit de `.harness/revisiones/`, `/handoff`, push y `gh pr ready`. Las casillas del PR NO cuentan como evidencia.
No archives ni mergees: eso es /juzgar-pr en Claude Code.
