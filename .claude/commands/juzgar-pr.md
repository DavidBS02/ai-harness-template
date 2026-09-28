Vas a decidir si el PR $ARGUMENTS se mergea y a archivar su change. Contexto mínimo: diff, change y comentarios; no releas el repo.

1. `gh pr checkout $ARGUMENTS`, `gh pr checks $ARGUMENTS`, `gh pr view $ARGUMENTS --comments`. CI rojo → detente y explica.
2. `python3 scripts/harness.py nivel origin/main` → nivel, riesgo y requisitos efectivos. Lee el change (`openspec/changes/<id>/`) y `HANDOFF.md`.
3. Revisión según riesgo:
   - Alto: `/codex:review` con este encargo: "Actúa como adversario: seguridad, casos borde, concurrencia, diseño, riesgos de datos. No repitas estilo ni conformidad." Además, lee tú el diff completo.
   - Medio: confía en `@revisor-fuerte` salvo un crítico dudoso o una segunda vuelta.
   - Bajo: basta el revisor gratis y CI.
4. Tareas sin marcar que dependen del futuro → **issue** por cada una: `gh issue create --label verificacion-diferida --title "<change>: <tarea>" --body "Depende de: … · Cómo se verifica: … · Si falla: change nuevo, no desarchivar"`.
5. Decide:
   a) Devolver: notas en HANDOFF.md + comentario en el PR. Si el problema es del spec, `/opsx:update <id>` primero.
   b) Arreglo < 20 líneas: pide al usuario relanzar con `HARNESS_OVERRIDE=1 scripts/arq`.
   c) Aprobar → paso 6.
6. Checklist de archive (`docs/LECCIONES.md` §1 y §4): `npx openspec validate --all`; encabezados MODIFIED literales (`grep '^### Requirement:' openspec/specs/<cap>/spec.md`); RENAMED al nombre nuevo; todos los escenarios; `## Purpose` editado a mano si cambió; publicación después del último cambio de código si algo se sirve congelado.
7. Archive: si se verificó en la rama, `/opsx:archive <id>` aquí; si exige producción, mergea, verifica y archiva en `chore/archive-<id>`.
8. Deudas: por cada deuda que este change abre, `gh issue create --label deuda --title … --body "Dueño: <archivo o skill> · Origen: <change>"`. Por cada issue `deuda` o `verificacion-diferida` que este change cierra, verifícalo **contra su archivo dueño** (`ls -la` + leer, nunca contra la lista) y ciérralo con evidencia (`gh issue close <n> --comment "<evidencia>"`). Si el usuario tomó una decisión nueva, añádela al final de `docs/DECISIONES.md`.
9. `python3 scripts/harness.py estado` (regenera ESTADO.md), vacía `HANDOFF.md` a su plantilla, marca "OK final" en el cuerpo del PR, commit (`chore(<id>): archive`), `gh pr merge --squash --delete-branch` y, si hubo worktree, `git worktree remove ../wt-<id>`. Justifica la decisión en un comentario.
