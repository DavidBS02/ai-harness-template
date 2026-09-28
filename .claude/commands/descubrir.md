Fase 0: vas a ENTENDER este proyecto para decidir el routing de copilotos. No implementes nada. Trabaja en plan mode. Ahorra contexto: lee inventarios y resúmenes antes que archivos completos; abre archivos solo cuando el resumen no alcance.

1. Inventario mecánico. Ejecuta `bash scripts/inventario.sh` y lee `docs/harness/INVENTARIO.md`. Si el repo está VACÍO (verde), salta al paso 7.

2. Resúmenes por módulo (delegado). Decide los 5–12 módulos/carpetas que importan. Escribe la lista en `docs/harness/resumenes/_modulos.txt` (uno por línea) y DETENTE con este mensaje: "Ejecuta en OpenCode: /resumir-modulos y vuelve a correr /descubrir cuando existan los resúmenes". Si los resúmenes ya existen en `docs/harness/resumenes/*.md`, continúa.

3. Lectura dirigida. Lee los resúmenes. Abre SOLO: puntos de entrada, modelos de datos, todo lo que INVENTARIO marcó como sensible, y los 5 archivos con más churn. Anota reglas no escritas que veas.

4. Escribe `docs/harness/MAPA.md` completo, siguiendo su plantilla. En la tabla de zonas pon rutas REALES (globs o regex), no categorías genéricas. Criterio: rojo = auth, dinero, datos personales, migraciones/esquema, infra, secretos, o código crítico sin tests; amarillo = lógica de negocio o integraciones con pocos tests; verde = bien cubierto por tests o de bajo impacto. [CONFIRMAR CONMIGO la tabla de zonas antes de seguir]

5. Routing. Reescribe `.harness/rutas-alto.txt` y `.harness/rutas-bajo.txt` con las rutas de la tabla (una regex por línea, mantén los comentarios). Si este repo necesita otros umbrales, anótalos en DELEGACION.md. Prueba: `bash scripts/riesgo.sh` sobre un diff de prueba (crea una rama temporal, toca un archivo rojo, verifica que diga alto, descarta la rama).

6. Escribe `docs/harness/DELEGACION.md` con ejemplos concretos de ESTE repo en cada fila, y 3 primeros specs candidatos (de TODOs, `gh issue list`, deuda o zonas rojas sin tests), cada uno con zona y riesgo.

7. Si el repo es VERDE: pregúntame (una sola vez, todo junto): stack, dominio, si habrá datos personales o pagos, cómo probaremos, dónde se despliega. Con eso escribe MAPA.md como "mapa objetivo" (zonas previstas), rutas de riesgo previstas y DELEGACION.md.

8. Aplica el entendimiento al harness: ejecuta los pasos de `/init-harness` (AGENTS.md con la sección "No tocar" = zona roja y las reglas no escritas; ci.yml real; lista de IDs de modelo pendientes).

9. Commit `chore: descubrimiento y routing del harness` y cierra con: resumen de 10 líneas del proyecto, tabla de zonas, y qué queda manual.
