Vas a abrir un cambio con el harness para: $ARGUMENTS
No implementes código. Tu entregable es un change listo para que OpenCode lo ejecute. Gasta tokens solo en pensar: lo mecánico lo hace `scripts/nuevo.sh`.

0. Enrutamiento (`.claude/rules/workflow-routing.md`). Si es research, producto o arquitectura, detente y propone la skill BMAD que toca (`/ruta <skill>` dice dónde se corre). Si es trivial (riesgo bajo y ≤ 20 líneas), es nivel 0: `scripts/nuevo.sh <slug> --nivel 0` y dile al usuario que lo haga OpenCode `@mecanico`, sin change.
1. Nivel de ceremonia (tabla en `docs/harness/RUTAS.md`). Propónlo y CONFIRMA con el usuario en una línea:
   - 1 ligero: una capacidad, riesgo bajo o medio.
   - 2 estándar: varias capacidades o riesgo medio.
   - 3 completo: iniciativa nueva o riesgo alto (antes va BMAD).
   Estima el riesgo con las zonas de `docs/harness/RUTAS.md` (generadas desde `harness.json`); `scripts/riesgo.sh` lo recalcula sobre el diff real.
1b. **Tamaño (economía, `docs/LECCIONES.md` §20).** Estima las tareas del ejecutor. Si pasan de ~12, o el change toca más de 3 subsistemas, **pártelo** en changes que se mergean por separado y dile al usuario el orden. Un change grande no es más barato por tener un solo proposal: el ejecutor arrastra el contexto.
2. Contexto mínimo. Lee `openspec/config.yaml` y SOLO las capacidades de `openspec/specs/` que esto toca. Del spine y el SPEC, solo los AD-*/CAP-* relevantes. Si esto contradice un AD o una CAP, detente: primero va `bmad-architecture` o `bmad-spec`.
3. Parte mecánica: `scripts/nuevo.sh <id> --nivel <N>`; en nivel ≥ 2 añade `--issue "<título>"`; añade `--worktree` solo si vas a trabajar en paralelo.
4. Propuesta (skill `openspec-propose` / `/opsx:propose <id>`) según el nivel:
   - Nivel 1: proposal + tasks (design solo si hay una decisión técnica real) + specs si cambia comportamiento.
   - Nivel 2-3: proposal + design + specs + tasks.
   - Siempre: `proposal.md` cita AD-* y capacidades, tiene "Fuera de este change" y termina con `## Harness`: `Issue: #<n>` (nivel ≥ 2), `Nivel: <N>`, `Riesgo: bajo|medio|alto`, `Zonas: …`, `OpenCode-zona-roja: no|autorizado`.
   - Tareas con "verificar con …", "(manual)" donde toque, y la de despliegue termina en el paso que cambia lo que se sirve.
   - **Tareas pensadas para sesiones cortas:** grupos de ≤ 5 tareas (un grupo = una sesión de OpenCode), y cada encabezado de grupo dice quién lo hace: `(build)` si exige diseño o toca seguridad, `(@mecanico)` para tests, docs, empaquetado y repetición. La verificación preferida es un test o un comando con código de salida; los experimentos manuales y las builds pesadas, solo donde no hay otra forma.
   - **Artefactos concisos:** el design solo lleva decisiones, su porqué y la evidencia externa, sin repetir el spec. El ejecutor relee todo esto en cada paso.
   - Deltas MODIFIED según `docs/LECCIONES.md` §1. Si depende de algo externo, muestra real u Open Question temprana (§2).
5. `npx openspec validate <id>`. Solo si el riesgo es medio o alto: `/codex:adversarial-review` sobre proposal + design.
6. Commit (`spec(<id>): propuesta`), push y PR en draft con `.github/PULL_REQUEST_TEMPLATE.md`.
7. Cierra con la instrucción exacta para el ejecutor: `scripts/ejec-contenedor` (en el worktree si lo creaste) → `/ejecutar-cambio <id> grupo 1`, una sesión nueva por grupo.
