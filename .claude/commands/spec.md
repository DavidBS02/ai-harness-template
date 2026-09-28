Vas a convertir esta idea en un spec ejecutable por otro agente: $ARGUMENTS

1. Crea un issue en GitHub con `gh issue create --title "<título>" --body "<resumen>"` y guarda el número.
2. Crea la rama y el worktree: `git worktree add ../wt-<slug> -b feat/<issue>-<slug> main`.
3. Estima el riesgo con los criterios de docs/specs/_plantilla.md (bajo/medio/alto) y escríbelo en el spec; OpenCode lo confirmará con `scripts/riesgo.sh` sobre el diff real.
4. Escribe `docs/specs/<issue>-<slug>.md` usando la plantilla de docs/specs/_plantilla.md. Sé concreto: archivos a tocar, pasos ordenados, criterios de aceptación verificables, comandos de test.
5. Haz commit en esa rama: `spec: <issue> <slug>`.
6. Termina mostrando el spec y la ruta del worktree para OpenCode.
No implementes nada.
