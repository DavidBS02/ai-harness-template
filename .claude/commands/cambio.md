Vas a abrir un cambio de OpenSpec con el harness para: $ARGUMENTS
No implementes código. Tu entregable es un change listo para que OpenCode lo ejecute.

0. Enrutamiento (`.claude/rules/workflow-routing.md`). Si esto es research, producto o arquitectura, detente y propone la skill BMAD que toca (empieza por `bmad-help`). Si es trivial (riesgo bajo y ≤ 20 líneas), detente y propone: OpenCode `@mecanico` en la rama `fix/<slug>`, sin change.
1. Contexto. Lee `openspec/config.yaml`, las capacidades de `openspec/specs/` que esto toca, `docs/harness/MAPA.md` (zonas) y, si existen, el SPEC y el spine de `_bmad-output/`. Si esto contradice un AD o una CAP, detente: primero va `bmad-architecture` o `bmad-spec`.
2. Issue: `gh issue create --title "<título>" --body "<resumen + capacidades afectadas>"`. Guarda el número `<n>`.
3. Nombre del change `<id>` en kebab-case (verbo-objeto, ej. `add-dark-mode`). Crea la rama y el worktree: `git worktree add ../wt-<id> -b feat/<n>-<id> main`.
4. En `../wt-<id>`, corre la propuesta de OpenSpec (skill `openspec-propose` / `/opsx:propose <id>`). Exige que:
   - `proposal.md` cite los AD-* y las capacidades que crea o modifica, tenga "Fuera de este change" y termine con `## Harness`: `Issue: #<n>`, `Riesgo: bajo|medio|alto`, `Zonas: …`, `OpenCode-zona-roja: no` (o `autorizado` solo si delegas zona roja con pasos cerrados).
   - Si depende de un artefacto externo, el design cite la muestra real o la declare Open Question con una tarea temprana (`docs/LECCIONES.md` §2).
   - Cada tarea de `tasks.md` termine en "verificar con …", las manuales digan "(manual)" y la de despliegue termine en el paso que cambia lo que se sirve.
   - Los deltas `MODIFIED` cumplan las convenciones de `docs/LECCIONES.md` §1 (encabezados literales, RENAMED, todos los escenarios).
5. `npx openspec validate <id>`. Si el riesgo es medio o alto: `/codex:adversarial-review` sobre `proposal.md` + `design.md`, y corrige lo que tenga razón.
6. Commit en la rama (`spec(<id>): propuesta`), push y PR en draft: `gh pr create --draft --title "feat(<área>): <qué> (#<n>)" --body-file .github/PULL_REQUEST_TEMPLATE.md`.
7. Cierra con el resumen del change y la instrucción exacta para el ejecutor: `cd ../wt-<id> && scripts/ejec` → `/ejecutar-cambio <id>`.
