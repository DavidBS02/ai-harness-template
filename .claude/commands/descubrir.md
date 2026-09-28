Fase 0: vas a ENTENDER este proyecto para decidir el routing de copilotos y dejar el método (BMAD + OpenSpec) bien sembrado. No implementes nada. Trabaja en plan mode. Ahorra contexto: lee inventarios, resúmenes y specs antes que código.

1. Diagnóstico del método. Clasifica el repo en uno de estos casos:
   - A) **Con método montado**: existen `_bmad/` u `openspec/`, y hay artefactos (SPEC, spine, `openspec/specs/`). No reinstales nada.
   - B) **Con código, sin método**: hay código de aplicación y no hay `_bmad/` ni `openspec/`.
   - C) **Verde**: no hay código de aplicación.
   Si faltan los frameworks (B o C), pide al usuario correr `bash scripts/instalar-frameworks.sh` y continúa cuando esté.

2. Inventario mecánico: `bash scripts/inventario.sh` y lee `docs/harness/INVENTARIO.md`.

3. Fuentes, según el caso:
   - A) Si hace falta leer mucho (spine largo, muchas specs), delega la lectura: `scripts/ejec` → `/recolectar bmad-deep-recon <tema>` y trabaja sobre el digest. Lee el SPEC (CAP-*) y el spine (AD-*) de `_bmad-output/` si existen en este checkout; `openspec/config.yaml`; la lista de `openspec/specs/` (una capacidad = un módulo lógico) y `openspec list`. Si `_bmad-output/` está en `.gitignore`, avísalo (`docs/LECCIONES.md` §9) y propone qué versionar.
   - B) Recomienda la skill `bmad-project-context` o `bmad-deep-recon` para el entendimiento de producto. Decide los 5–12 módulos que importan, escríbelos en `docs/harness/resumenes/_modulos.txt` y DETENTE con: "Ejecuta en OpenCode: /resumir-modulos y vuelve a correr /descubrir". Si los resúmenes ya existen, continúa.
   - C) Salta al paso 8.

4. Lectura dirigida: abre solo puntos de entrada, modelos de datos, lo que INVENTARIO marcó como sensible, los 5 archivos con más churn y los AD-* que hablen de seguridad, dinero o datos.

5. Escribe `docs/harness/MAPA.md` (plantilla incluida). En la tabla de zonas usa rutas REALES y, en el caso A, nombra también las capacidades de `openspec/specs/` y los AD-* de cada zona. Criterio por **alcance del daño**, no por etiqueta de dominio (`docs/LECCIONES.md` §11): pregunta primero quién usa el sistema (solo el usuario, un equipo, clientes) y si hay más de un entorno. Rojo = lo que puede filtrar credenciales, abrir acceso, corromper la única copia de los datos o romper el despliegue (secretos, auth, migraciones con un solo entorno, infra, workflows); amarillo = lógica importante cubierta por tests (en un proyecto personal, el dinero va aquí si tiene tests); verde = bajo impacto o bien cubierto. [CONFIRMAR CONMIGO la tabla antes de seguir]

6. Routing: reescribe `zonas.alto` y `zonas.bajo` en `harness.json` (regex sobre rutas relativas) y corre `python3 scripts/harness.py sync`. Prueba `scripts/riesgo.sh` en una rama temporal tocando un archivo rojo; debe decir alto. Descarta la rama. Si el proyecto tiene un solo entorno de producción, anota en AGENTS.md: despliegue solo desde main, uno a la vez, con respaldo previo si toca datos.

7. Escribe `docs/harness/DELEGACION.md` con ejemplos concretos de ESTE repo y los 3 primeros changes candidatos (de issues `deuda`, TODOs, `gh issue list` o zonas rojas sin tests), cada uno con zona, riesgo, nivel y si pasa primero por BMAD.

8. Si el repo es VERDE: pregúntame todo junto, una sola vez: stack, dominio, si habrá datos personales o pagos, cómo probaremos y dónde se despliega. Escribe MAPA.md como "mapa objetivo", las rutas previstas y DELEGACION.md, y deja como siguiente paso la ruta BMAD: `bmad-help` → `bmad-forge-idea` / `bmad-product-brief` → `bmad-spec` → `bmad-architecture` → primer `/cambio`, que sembrará `openspec/config.yaml` (`docs/LECCIONES.md` §5).

9. Aplica todo al harness con los pasos de `/init-harness`.

10. Crea la rama `chore/harness-descubrimiento`, haz commit (`chore: descubrimiento y routing del harness`), push y `gh pr create`. Cierra con: resumen del proyecto en 10 líneas, tabla de zonas, caso (A/B/C) y qué queda manual.
