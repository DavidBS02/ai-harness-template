Vas a adaptar este harness de copilotos al repo actual. Si aún no corriste /descubrir, hazlo primero: ese comando entiende el proyecto y decide el routing; este solo aplica la configuración. No implementes features. Sigue estos pasos y ve confirmando conmigo en los puntos marcados.

1. Diagnóstico. Lee harness.json. Determina si el repo es VERDE (sin código de aplicación) o EXISTENTE. Si es existente, detecta el stack leyendo package.json, pyproject.toml, go.mod, Cargo.toml, pom.xml, Gemfile, composer.json, Makefile, Dockerfile y la estructura de carpetas. Resume en 5 líneas: stack, cómo se instala, cómo se prueba, cómo se lintea, cómo se despliega. Si algo no está claro, pregúntame. [CONFIRMAR]

2. Si es VERDE: pregúntame stack, si habrá datos personales o pagos, y cómo quiero probar. Con eso crea un esqueleto mínimo (solo lo necesario para que `install` y `test` corran en CI).

3. AGENTS.md: reemplaza los placeholders `<...>` con lo real. Añade la lista "No tocar" con rutas sensibles reales (auth, pagos, migraciones, infra, secretos). Mantén el archivo corto: reglas, no prosa.

4. Routing: asegúrate de que `.harness/rutas-alto.txt` y `rutas-bajo.txt` reflejen la lista "No tocar" (si ya corriste /descubrir, ya están; si no, edítalas). Prueba con `bash scripts/riesgo.sh` y muéstrame la salida.

5. .github/workflows/ci.yml: reemplaza el paso de ejemplo con instalar + lint + test reales del stack. El job debe llamarse `test` (github-setup.sh lo exige como check).

6. Placeholders de modelo: NO los inventes. Lista los que quedan (`grep -rn REEMPLAZA-CON-ID .opencode opencode.json`) y dime exactamente qué ID pegar en cada uno y de dónde sacarlo (OmniRoute → Combos / Providers).

7. Si es EXISTENTE: propone 3 primeros specs candidatos a partir de TODOs, issues abiertos (`gh issue list`) o deuda evidente, cada uno con su riesgo estimado. No los crees todavía. [CONFIRMAR]

8. Commit: `chore: init harness de copilotos`. Termina con un checklist de lo que queda manual (logins, IDs de modelo, protección de main).
