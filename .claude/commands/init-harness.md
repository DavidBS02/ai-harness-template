Vas a aplicar la configuración del harness al repo actual. Si aún no corriste /descubrir, hazlo primero: ese comando entiende el proyecto y decide el routing; este solo aplica. No implementes features.

0. **Entrantes.** Si existe `.harness/entrantes/`, el bootstrap encontró archivos que el repo ya tenía (por ejemplo, su propio `workflow-routing.md` o `harness-guide.md`) y dejó ahí la versión del harness. Fusiona cada uno con el del repo: **conserva todo lo propio** (lecciones, convenciones, decisiones) y añade lo del harness que falte (roles por herramienta, GitHub, guardias, riesgo). Cuando termines, borra `.harness/entrantes/`. [CONFIRMAR CONMIGO la fusión de cada archivo]

1. **openspec/config.yaml.** Fusiónalo con `.harness/openspec-config.base.yaml`:
   - Si el repo ya tiene `context`, consérvalo **intacto**. Si está vacío, siémbralo desde el SPEC, el spine y MAPA.md (producto, stack, capas, AD-*, convenciones, "nunca entra al repo").
   - En `rules` y `operations`, conserva las reglas existentes y añade las marcadas `[harness]` que falten (sección `## Harness` del proposal, tareas marcadas por el ejecutor, cierre en el runtime real, deudas como issues). No dupliques reglas equivalentes.
   - Verifica con `npx openspec validate --all` y que `npx openspec instructions proposal` muestre la regla `## Harness`.
2. **AGENTS.md.** Reemplaza los placeholders `<...>` con lo real, incluidas la tabla "Puntos de entrada" (qué hace falta para que un cambio llegue al runtime), la lista "No tocar" (= zona roja) y "Nunca entra al repo". Mantenlo corto: reglas, no prosa. Si el repo ya tenía instrucciones en otro sitio (CLAUDE.md largo, `.cursor/rules`), deja una sola fuente: AGENTS.md para reglas del repo y `.claude/rules/workflow-routing.md` para el método.
3. **Estado del proyecto.** Si alguna regla que se carga siempre contiene el estado, deudas o cifras (por ejemplo, una sección "Estado actual" dentro de `workflow-routing.md`), sácalo de ahí (`docs/LECCIONES.md` §8):
   - Cada **deuda** abierta → issue con etiqueta `deuda` (verifícala antes contra su archivo dueño; si ya está saldada, no la crees).
   - Cada **verificación diferida** → issue con etiqueta `verificacion-diferida`.
   - Cada **decisión vigente del usuario** → una entrada en `docs/DECISIONES.md` (append-only, con fecha).
   - Lo demás (historia de changes) ya está en `openspec/changes/archive/`: no se copia.
   - Luego `python3 scripts/harness.py estado` genera `docs/ESTADO.md`. Quita cifras reales y datos personales de todo lo versionado. [CONFIRMAR CONMIGO antes de mover]
4. **Lecciones.** Si el repo tiene lecciones propias (en su harness-guide o sus reglas), llévalas a `docs/LECCIONES.md` con su origen, sin duplicar las que ya están.
5. **Routing.** Confirma que `zonas` en `harness.json` refleja la zona roja, y que `skills` cubre las skills instaladas (`ls .claude/skills`): cualquier skill del método que no esté listada cae por prefijo; si su clase no es la correcta, añádela. Corre `python3 scripts/harness.py sync` y prueba `scripts/riesgo.sh`.
6. **CI y dependencias** (`docs/ESTANDAR-PROYECTO.md` §4). En `.github/workflows/ci.yml`, reemplaza el paso `STACK pendiente` por los gates reales del stack: instalación reproducible con lockfile, lint, tipos, tests, build y auditoría de dependencias (gitleaks ya está). El job debe llamarse `test`. En `.github/dependabot.yml`, agrega el ecosistema del stack. Si falta `.env.example`, créalo solo con nombres de variables.
7. **`_bmad-output/`.** Si está en `.gitignore`, propón versionar al menos los artefactos de contrato (SPEC y spine), porque OpenCode trabaja en worktrees y no ve lo ignorado (`docs/LECCIONES.md` §9). [CONFIRMAR CONMIGO]
8. **Placeholders de modelo.** NO los inventes. Están en `harness.json` → `agentes` (`grep -n REEMPLAZA-CON-ID harness.json`). Dime qué ID pegar en cada uno y de dónde sacarlo (OmniRoute → Combos / Providers; OpenCode → /models). Después, `python3 scripts/harness.py sync`.
9. **Memoria de código.** Si `harness.json → mcp.codebase_memory.habilitado` es `false`, omite este paso y dilo en el checklist final. Si es `true`, haz el indexado inicial en primer plano y muéstrale al usuario cada salida:
   - `bash scripts/cbm-instalar.sh`: instala el binario de la versión fijada, verificado por SHA-256.
   - `python3 scripts/harness.py cbm verificar-secretos`: si falla, NO indexes. Añade el patrón que falta a `mcp.codebase_memory.ignorar`, corre `sync` y repite.
   - `bash scripts/cbm-indexar.sh`: indexado completo.
   - `scripts/cbm cli --quiet list_projects`: el repo debe aparecer.
   Las herramientas MCP de escritura siguen vetadas para Claude; indexar se hace solo con estos scripts.
10. Commit `chore: init harness de copilotos` en la rama de trabajo. Cierra con un checklist de lo que queda manual (logins, IDs de modelo, protección de main, y si la memoria de código quedó indexada o apagada).
