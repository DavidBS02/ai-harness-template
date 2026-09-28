---
description: Resume cada módulo listado en docs/harness/resumenes/_modulos.txt para que Claude Code decida el routing. Solo lectura.
---
Para cada línea de `docs/harness/resumenes/_modulos.txt`, escribe `docs/harness/resumenes/<nombre>.md` (nombre = ruta con / reemplazado por _). Usa @explorador para módulos pequeños y cambia al agente `contexto-largo` (Kimi K3) solo si el módulo supera ~50 archivos.
Cada resumen, máximo 40 líneas, con estas secciones:
- Propósito (2 líneas)
- Entradas / salidas (APIs, eventos, tablas, archivos)
- Dependencias internas y externas
- Datos sensibles que maneja (personales, dinero, credenciales) — sé explícito: "ninguno" si no hay
- Tests: cuáles existen y qué cubren; qué NO cubren
- Deuda y olores (TODOs, duplicación, funciones enormes)
- Riesgo sugerido: rojo / amarillo / verde y por qué (Claude tomará la decisión final)
No modifiques código. Al terminar, `git add docs/harness/resumenes && git commit -m "docs: resúmenes de módulos para descubrimiento"` y corre /handoff.
