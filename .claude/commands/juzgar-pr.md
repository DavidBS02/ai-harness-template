Vas a decidir si el PR $ARGUMENTS se mergea, y a archivar su change de OpenSpec.

1. `gh pr checkout $ARGUMENTS`, `gh pr view $ARGUMENTS --comments` y `gh pr checks $ARGUMENTS`. Si CI está en rojo, detente y explica.
2. Identifica el change: la rama `feat/<n>-<id>` → `openspec/changes/<id>/`. Lee proposal, design, specs, `tasks.md` y `HANDOFF.md`.
3. Riesgo = el más alto entre `bash scripts/riesgo.sh`, el `Riesgo:` del proposal y la etiqueta `riesgo:*`.
   - Alto: corre `/codex:review` con este encargo: "Actúa como adversario. Busca cómo romper este cambio: seguridad (inyección, validación, permisos, secretos), casos borde y concurrencia, errores de diseño y riesgos de datos. No repitas estilo ni conformidad; eso ya lo revisó otro agente." Además, lee tú el diff línea por línea.
   - Medio: confía en `@revisor-fuerte`, salvo un crítico dudoso o una segunda vuelta; en ese caso, llama a Luna.
   - Bajo: no llames a Luna.
4. Tareas: todas marcadas, o las pendientes son verificaciones que dependen del futuro. Esas van a `docs/ESTADO.md` → "Verificaciones diferidas", con su dependencia y cómo se verifican.
5. Decide:
   a) Devolver a OpenCode: notas en HANDOFF.md + comentario en el PR. Si el problema es del spec, corrígelo tú con `/opsx:update <id>` antes de devolver.
   b) Arreglo puntual de menos de 20 líneas: pide al usuario relanzar con `HARNESS_OVERRIDE=1 scripts/arq`.
   c) Aprobar → sigue al paso 6.
6. Checklist de archive (`docs/LECCIONES.md` §1 y §4), en orden:
   - `npx openspec validate --all` en verde.
   - Para cada `MODIFIED`: `grep '^### Requirement:' openspec/specs/<cap>/spec.md` y comparación literal; los RENAMED apuntan al nombre nuevo; están todos los escenarios publicados.
   - Si cambia un `## Purpose`, editarlo a mano en `openspec/specs/<cap>/spec.md`.
   - Si el change toca algo que se sirve congelado, el paso de publicación ocurrió después del último cambio de código.
7. Si la verificación se pudo hacer en la rama: `/opsx:archive <id>` en esta rama. Si exige producción: mergea primero, verifica, y archiva en un PR `chore/archive-<id>`.
8. Actualiza `docs/ESTADO.md`: fila del change, verificaciones diferidas y deudas. Verifica cada deuda **contra su archivo dueño** (`ls -la` + leer), no contra la lista (`docs/LECCIONES.md` §3). Si el change cambió stack, capas o convenciones, confirma que `openspec/config.yaml` quedó al día.
9. Commit (`chore(<id>): archive`), marca en el cuerpo del PR el "OK final", `gh pr merge --squash --delete-branch` y `git worktree remove ../wt-<id>`. Justifica la decisión en un comentario del PR.
