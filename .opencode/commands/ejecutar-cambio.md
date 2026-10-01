---
description: Implementa un change de OpenSpec (un grupo de tareas por sesión), lo revisa según su riesgo y deja el PR listo para juzgar.
---
Vas a implementar el change `$ARGUMENTS`. Formato: `<id>` o `<id> grupo <N>[,<M>]`.

**Economía (obligatoria).** El costo de un agente crece con *contexto acumulado × pasos*, así que:
- **Una sesión = un grupo de `tasks.md`** (o los que diga `$ARGUMENTS`). Si no se indica grupo, haz el primero con tareas sin marcar. Al cerrar el grupo: commit, `/handoff` y DETENTE con «Grupo N listo. Siguiente: `/ejecutar-cambio <id> grupo N+1` en una sesión NUEVA».
- **Lee HANDOFF.md primero.** Del change, lee completos solo `tasks.md` y lo que el grupo cita del design y del spec, no todo.
- **Archivos grandes:** busca con `grep -n` o @explorador y lee solo los rangos que vas a tocar. Nunca leas un archivo de más de 300 líneas entero.
- **Delega por costo:** @mecanico (modelo Flash) para tests, docs, empaquetado y cambios repetitivos; @explorador para ubicar código. Tú (`build`) solo lo que exige diseño o toca seguridad. Si el encabezado del grupo dice `(@mecanico)`, delégalo entero y revisa su diff.
- **Tests enfocados por tarea** (la clase o el test que toca). La suite completa solo al cerrar el grupo y antes de las revisiones.
- **Depuración:** si una verificación falla 3 veces seguidas, para, anota en HANDOFF.md lo intentado y detente. No sigas probando a ciegas.

1. `git branch --show-current` debe ser `feat/<id>` o `feat/<n>-<id>`, nunca main. Lee la sección "Puntos de entrada" de AGENTS.md.
2. Implementa con `/opsx-apply <id>`, tarea por tarea, solo las del grupo:
   - typecheck y tests enfocados antes de marcar cada tarea en `tasks.md`; un commit pequeño por tarea o bloque.
   - Las tareas "(manual)" no las marques: déjalas en HANDOFF.md.
   - NUNCA edites proposal, design ni specs (las guardias lo bloquean). Si falta algo del spec o aparece un ajuste de esquema, config o AD: HANDOFF.md y DETENTE (el arquitecto corre /opsx:update).
3. **Solo cuando no quedan tareas sin marcar** (salvo las manuales), en una sesión propia: `python3 scripts/harness.py nivel` → nivel, riesgo y requisitos. Haz commit de todo el código ANTES de revisar: la evidencia queda atada a ese commit y se invalida si después cambias código.
   - Revisión 1 siempre (nivel ≥ 1): @revisor-gratis. Guarda su salida completa en `/tmp/rev1.md` y regístrala:
     `python3 scripts/harness.py revision registrar --revisor revisor-gratis --modelo <id del modelo que respondió> --veredicto APROBAR|CORREGIR --hallazgos /tmp/rev1.md`
   - Revisión 2 si el riesgo es medio o alto: @revisor-fuerte, igual, con `--revisor revisor-fuerte`.
   - Si el veredicto es CORREGIR: corrige, commit, y repite la revisión (cada vuelta cuenta contra el presupuesto: `python3 scripts/harness.py presupuesto`).
   - Nunca escribas un registro sin haber corrido el revisor: el registro guarda su salida y su modelo.
4. Commit de `.harness/revisiones/`, `/handoff`, push y `gh pr ready`. Las casillas del PR NO cuentan como evidencia.
No archives ni mergees: eso es /juzgar-pr en Claude Code.
