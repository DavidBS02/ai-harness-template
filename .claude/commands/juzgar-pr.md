Vas a decidir si el PR $ARGUMENTS se mergea.

1. `gh pr checkout $ARGUMENTS` y lee `gh pr view $ARGUMENTS --comments`.
2. Verifica CI: `gh pr checks $ARGUMENTS`. Si hay rojo, detente y explica.
3. Lee el spec enlazado y HANDOFF.md.
4. Corre `scripts/riesgo.sh` y compara con la etiqueta `riesgo:*` del PR y el campo Riesgo del spec (si difieren, gana el más alto). Si es ALTO, corre `/codex:review` con este encargo: "Actúa como adversario. Busca cómo romper este cambio: seguridad (inyección, validación, permisos, secretos), casos borde y concurrencia (vacíos, límites, carreras, timeouts, reintentos), errores de diseño (acoplamiento, efectos secundarios, contratos de API) y riesgos de datos (migraciones, pérdida, compatibilidad). No repitas hallazgos de estilo ni de conformidad con el spec; eso ya lo revisó otro agente." Si es medio, confía en @revisor-fuerte salvo que reporte un crítico dudoso o el PR ya haya dado dos vueltas: entonces sí llama a Luna. Si es bajo, no llames a Luna.
5. Decide: (a) merge con `gh pr merge --squash`, (b) arreglo puntual tuyo si es < 20 líneas, o (c) devolver a OpenCode escribiendo las notas en HANDOFF.md y comentando el PR.
Justifica la decisión en un comentario del PR.
