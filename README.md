# ai-harness-template

Plantilla genérica para trabajar con tres copilotos a la vez, con roles delimitados y GitHub como columna vertebral:

- **Claude Code** (Claude Pro): ideación, specs, arquitectura, juicio final del PR.
- **OpenCode** (OpenCode Go): ejecución del spec, tests, PR.
- **OmniRoute** (capas gratis, vía OpenCode): revisores de conformidad y adversarial.
- **Codex CLI** (ChatGPT Free, dentro de Claude Code): tercer revisor solo en riesgo alto.

Funciona para proyectos nuevos (verde) o existentes. Solo cubre el uso de copilotos; el método de trabajo (sprints, definición de done, etc.) se conecta aparte, ver `docs/INTEGRACION-FRAMEWORK.md`.

## Quickstart (15 min)

```bash
# 1. Clona la plantilla y aplícala a tu proyecto (verde o existente)
git clone https://github.com/<tu-usuario>/ai-harness-template.git
bash ai-harness-template/scripts/bootstrap.sh /ruta/a/tu/proyecto

# 2. Verifica herramientas y logins
cd /ruta/a/tu/proyecto && bash scripts/doctor.sh

# 3. Configura GitHub (labels de riesgo + protección de main)
bash scripts/github-setup.sh

# 4. Deja que Claude Code adapte el harness a tu repo
claude
> /init-harness
```

`/init-harness` detecta si el repo está vacío o tiene código, identifica el stack, llena `AGENTS.md`, ajusta las rutas sensibles de `scripts/riesgo.sh`, escribe el `ci.yml` real y te deja los IDs de modelo pendientes claramente marcados.

## Flujo por feature

```
/spec (Claude)  →  /codex:adversarial-review  →  /ejecutar-spec (OpenCode)
→ @revisor-gratis (siempre) → @revisor-fuerte (riesgo medio/alto)
→ PR + CI + etiqueta riesgo:*  →  /juzgar-pr (Claude, + Luna si riesgo alto)  →  merge
```

Detalle completo en `docs/PLAYBOOK.md`. Configuración por herramienta en `docs/ONBOARDING.md`.

## Estructura

```
AGENTS.md                 reglas del repo (única fuente; Claude la importa desde CLAUDE.md)
CLAUDE.md                 @AGENTS.md + reglas solo de Claude Code
HANDOFF.md                estado vivo de la rama
.claude/commands/         /init-harness /spec /juzgar-pr /handoff
.opencode/agents/         build (implícito), explorador, mecanico, contexto-largo, revisor-gratis, revisor-fuerte
.opencode/commands/       /ejecutar-spec /handoff
opencode.json             modelos por defecto + proveedor OmniRoute
scripts/                  bootstrap, doctor, github-setup, riesgo
.github/                  plantillas de issue/PR, ci.yml, riesgo.yml
docs/                     PLAYBOOK, ONBOARDING, INTEGRACION-FRAMEWORK, specs/
harness.json              versión y lista de placeholders pendientes
```

## Reglas que no se negocian

1. La suscripción de Claude solo se usa en Claude Code. Nunca detrás de un proxy.
2. OmniRoute solo con proveedores por API key que permitan uso personal. Nunca OAuth de Antigravity/Kiro ni sesiones web.
3. Un modelo por sesión. Cambio de modelo = `/compact` primero.
4. Ningún agente afirma que los tests pasan: lo dice CI.
5. El traspaso entre herramientas pasa por GitHub (spec, commits, PR, HANDOFF.md), nunca por copiar conversaciones.

Licencia MIT.
