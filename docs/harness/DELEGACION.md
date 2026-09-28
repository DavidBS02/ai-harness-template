# Matriz de delegación de este repo (lo escribe Claude Code en /descubrir)

Regla general del harness: Claude piensa, OpenCode ejecuta, revisores gratis revisan, Luna revisa lo rojo. Esta matriz la aterriza a ESTE repo.

| Tipo de tarea en este repo | Ejemplo concreto | Modelo/agente | Revisión mínima |
|---|---|---|---|
| Tests y docs de zona verde | | OpenCode @mecanico (GLM-Flash) | revisor-gratis |
| Feature en zona verde | | OpenCode build (GLM-5.3) | revisor-gratis |
| Feature en zona amarilla | | OpenCode build + spec detallado | revisor-gratis + revisor-fuerte |
| Cambio en zona roja | | OpenCode solo con `OpenCode-zona-roja: autorizado` y tareas cerradas; si no, Claude con override | + Luna + humano |
| Refactor grande / lectura de todo un módulo | | OpenCode contexto-largo (Kimi K3) resume → Claude decide | según zona |
| Bug atascado | | Claude Code + /codex:rescue | según zona |
| Producto, PRD, arquitectura, cambiar un AD | | BMAD en Claude Code (dossier → /cambio) | — |

## Umbrales de riesgo ajustados a este repo
- UMBRAL_ARCHIVOS: 5   (cámbialo en .harness/ o exportando la variable)
- UMBRAL_LINEAS: 300

## Primeros 3 changes propuestos
| # | Change (id) | Zona | Riesgo | ¿Pasa antes por BMAD? | Por qué primero |
|---|---|---|---|---|---|
