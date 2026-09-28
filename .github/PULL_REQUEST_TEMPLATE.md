## Qué hace
<!-- una frase -->

## Change de OpenSpec
Closes #<issue> (nivel ≥ 2) — `openspec/changes/<id>/` (tras el archive: `openspec/changes/archive/<fecha>-<id>/`)
Capacidades: <creadas / modificadas>

## Nivel y riesgo
Nivel 0 | 1 | 2 | 3 · riesgo bajo | medio | alto (lo calcula `python3 scripts/harness.py nivel`; manda el más alto entre proposal, rutas y tamaño)

## Cómo se probó
- [ ] Tests locales en verde (`<comando>`)
- [ ] CI en verde
- [ ] Verificado contra la realidad: <qué se observó y dónde>

## Revisiones
- [ ] Revisión 1 (@revisor-gratis, combo OmniRoute): <resumen o "sin hallazgos críticos">
- [ ] Revisión 2 (@revisor-fuerte, DeepSeek V4) — solo riesgo medio/alto: <resumen o "no aplica">
- [ ] Revisión 3 (/codex:review, GPT-6 Luna) — solo riesgo alto: <resumen o "no aplica">
- [ ] OK final de Claude Code (/juzgar-pr)

## Archive
- [ ] `openspec validate --all` en verde y convenciones de deltas revisadas (docs/LECCIONES.md §1)
- [ ] Archivado en esta rama / o PR `chore/archive-<id>` después de verificar en producción
- [ ] Issues `verificacion-diferida` / `deuda` creados o cerrados con evidencia; `harness.py estado` corrido

## Notas para el arquitecto
<!-- decisiones tomadas, dudas, riesgos (o "ver HANDOFF.md") -->
