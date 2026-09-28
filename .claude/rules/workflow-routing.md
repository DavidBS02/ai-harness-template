# Workflow routing — cómo enrutar CADA pedido

**Siempre relevante y corta a propósito.** Estado del proyecto: `docs/ESTADO.md` (generado). Rutas por skill, niveles y zonas: `docs/harness/RUTAS.md` (generado desde `harness.json`).

## Tres ejes que no se mezclan
1. **Método:** BMAD planea y refina · OpenSpec ejecuta por change (`propose → apply → archive`).
2. **Herramientas:** Claude Code = arquitecto · OpenCode = ejecutor · revisores (OmniRoute y Luna) = solo lectura.
3. **GitHub:** rama → PR → CI + etiqueta de riesgo + check de proceso → merge por `/juzgar-pr`. Deudas y verificaciones diferidas = issues.

## Árbol de decisión
1. **Producto, PRD, UX, arquitectura, cambiar un AD o dividir en épicas** → BMAD. Antes de invocar una skill, `/ruta <skill>`: las de *decidir* y *redactar* van en Claude; las de *recolectar* y *revisar* van en OpenCode (`/recolectar`, `/revisar-artefacto`) y dejan un digest que Claude lee.
2. **Feature, fix, refactor o ajuste** → `/cambio "<idea>"` (elige nivel 1–3) → OpenCode `/ejecutar-cambio <id>` (en `scripts/ejec-contenedor`) → `/juzgar-pr`.
3. **Iniciativa grande** → BMAD primero → un change por pieza.
4. **Trivial** (riesgo bajo y ≤ 20 líneas) → nivel 0: `scripts/nuevo.sh <slug> --nivel 0`, OpenCode `@mecanico`, PR con solo CI. Lotes de triviales en un PR `chore/lote-<fecha>`.
5. **Ambiguo** → pregunta.

## BMAD no ejecuta NADA (regla dura)
Entrega un **dossier**, no un diff. No escribe código ni config, no crea ramas ni commits, no marca tareas, no aplica sus recomendaciones. Solo escribe en `_bmad-output/`. Toda sesión BMAD termina nombrando el comando que la aplica (`/cambio`, `/opsx:update <id>`). `bmad-build`, `bmad-build-auto` y `bmad-agent-dev` están bloqueadas: implementar es `/ejecutar-cambio`.

## Skills nuevas: lista blanca
Toda skill que no esté en `harness.json` está **bloqueada en ambas herramientas**. Se clasifica una vez, en Claude Code, con `/clasificar-skill <nombre>` (hechos con `harness.py analizar-skill`, propuesta con evidencia, confirmación del usuario). OpenCode no puede clasificar.

## Tokens de BMAD
Una sesión por workflow (`/clear` antes). Modelo mediano para redactar, el más capaz solo para decidir. Lectura masiva y reviews → OpenCode. Carga solo los AD-* y CAP-* que tocan.

## Evidencia y seguridad
Revisiones: `harness.py revision registrar` sobre el commit revisado (las casillas no cuentan). Plano de control, riesgo alto, techo duro o presupuesto agotado: aprobación humana en GitHub. Qué es guardia y qué es barrera real: `docs/SEGURIDAD.md`.

## Fuentes de verdad
Intención: `_bmad-output/` · Construido: `openspec/specs/` · Contexto IA: `openspec/config.yaml` · Reglas: `AGENTS.md` · Datos del harness: `harness.json` · Decisiones: `docs/DECISIONES.md` · Deudas: issues `deuda` (se cierran solo tras verificar contra su archivo dueño).

## El harness es vivo
Mejora encontrada → itera `harness.json`, esta regla, `docs/LECCIONES.md` o `openspec/config.yaml`, corre `python3 scripts/harness.py sync`, y súbela al repo base.
