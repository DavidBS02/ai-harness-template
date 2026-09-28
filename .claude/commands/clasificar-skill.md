Vas a clasificar la skill `$ARGUMENTS` para decidir en qué herramienta y con qué modelo corre. Hasta que esté en `harness.json`, está bloqueada en Claude Code y en OpenCode.
No la ejecutes: solo léela.

1. Hechos, sin gastar tokens en releer: `python3 scripts/harness.py analizar-skill $ARGUMENTS`. Si `encontrada` es false, pregunta al usuario de dónde viene (¿instalación nueva, plugin, skill de usuario?) y dónde está su SKILL.md.
2. Lee el `SKILL.md` y, si usa `render_skill.py` (BMAD) o referencia un workflow, lee **solo** el workflow principal que referencia. No leas más archivos que esos.
3. Decide la clase con estas preguntas, en orden, y para en la primera que sea sí:
   - ¿Escribe o modifica código, config, ramas, commits o PRs por su cuenta (fuera de OpenSpec)? → `prohibido` (si es del método) o `ejecutar`/`mecanico` (si es precisamente implementar un change de OpenSpec o tests).
   - ¿Su salida se vuelve contrato (AD-*, CAP-*, specs publicadas, alcance)? → `decidir`.
   - ¿Revisa, critica o audita un artefacto o un diff? → `revisar` (otra familia de modelos, en OpenCode).
   - ¿Su trabajo principal es leer mucho y resumir, sin decidir? → `recolectar`.
   - ¿Elicita, redacta o planea sin decidir contrato? → `redactar`.
   - ¿No es del método (documentos, utilidades) y es inocua en cualquier herramienta? → `libre`.
   Usa `tokens_aprox` como desempate: si es pesada y la clase lo permite, prefiere la opción que corre en OpenCode.
4. Propón al usuario, en una tabla corta: clase, herramienta, agente/modelo resultante, y **2 o 3 citas textuales** del SKILL.md o del workflow que lo justifican. Si ninguna clase encaja bien, dilo y propón crear una clase nueva en `harness.json` → `clases` (con herramienta y agente). [CONFIRMAR CONMIGO]
5. Con la confirmación: `python3 scripts/harness.py clasificar $ARGUMENTS <clase> --motivo "<evidencia en una línea>"` (escribe `harness.json` y regenera los adaptadores). Luego `python3 scripts/harness.py skills --check` para ver si quedan otras sin mapear.
6. Rama `chore/skill-$ARGUMENTS`, commit (`chore(harness): clasifica $ARGUMENTS como <clase>`), push y PR. Si otras skills quedaron sin mapear, ofrece clasificarlas en el mismo PR.
