# Lecciones del método (heredadas, aplicar siempre)

Cada lección tiene origen real. Si aprendes una nueva, agrégala aquí con fecha, qué pasó, por qué pasó y la regla que la previene, y llévala a `openspec/config.yaml` si la IA debe leerla al generar artefactos.

## 1. `validate` en verde no significa que `archive` vaya a funcionar
`openspec validate --all` revisa la **forma** del delta; quien lo compara contra `openspec/specs/` es el merge del archive, que falla después de escribir el código y desplegar. Verificar antes de `/opsx:archive`:
1. Todo encabezado bajo `## MODIFIED Requirements` existe **literal** en la spec publicada (`grep '^### Requirement:' openspec/specs/<cap>/spec.md`, carácter por carácter).
2. Si el nombre del requisito cambia, bloque `## RENAMED Requirements` con `- FROM:` / `- TO:`, y el `MODIFIED` apunta al nombre **nuevo**.
3. Un bloque `MODIFIED` lleva **todos** los escenarios publicados del requisito, más los nuevos.
4. Si cambia lo que describe el `## Purpose` de una capacidad ya publicada, se edita a mano `openspec/specs/<cap>/spec.md` como tarea del change (el delta solo siembra specs nuevas).
5. La lista de deudas se verifica contra su fuente (lección 3).

## 2. La muestra real antes del design
Un change que depende de un artefacto externo (correo, PDF, respuesta de API, webhook) exige la **muestra real** antes del design: el `.eml`, `pdfinfo`, un `curl`. Si no existe todavía, el design lo declara *Open Question* y una tarea **temprana** lo resuelve. Diseñar sobre la documentación produjo dos supuestos falsos (remitente y cifrado) que se descubrieron en la verificación final.

## 3. Una lista de deudas que nadie tacha miente, y siempre hacia el mismo lado
Anotar una deuda es parte natural del trabajo que la descubre; tacharla ocurre en otra sesión, otro día, otro archivo, y no le toca a nadie. La lista siempre se queda **larga**: se reporta como pendiente algo terminado y se manda a otra sesión como tarea algo que ya hizo. Regla: **verificar contra la fuente, no contra la lista.** `ls -la` del archivo dueño da la fecha; si es posterior a la anotación, mira dentro antes de afirmar nada.

## 4. El cierre de un change alcanza el runtime real
Si parte del sistema sirve una versión congelada (un deployment, una imagen, un caché, un CDN), la tarea de despliegue del change termina en el paso que **cambia lo que se sirve**, no en el que sube el código. Si no, la verificación manual mide el código viejo. Cada repo documenta su tabla "punto de entrada → qué hace falta para que llegue" en `AGENTS.md`.

## 5. El primer change de producto siembra el harness
Cuando el repo nace con el harness antes que el producto, sembrar `openspec/config.yaml` (producto, stack, capas, AD-*, convenciones, qué nunca entra al repo), `AGENTS.md` y `docs/harness/MAPA.md` es un **bloque de tareas del primer change**, con verificación. Así el segundo change ya se propone con contexto.

## 6. La spec fija la verificación; el código la cumple, no al revés
Si un escenario resulta literalmente inverificable, se precisa el escenario en el delta antes de archivar. Nunca se afloja el test en silencio.

## 7. BMAD que aplica sus propias conclusiones rompe la trazabilidad
Si BMAD edita, el cambio ocurre fuera de `propose → apply → archive` y la spec deja de ser la fuente de verdad. El revisor y el ejecutor tienen que ser capas distintas, o la revisión se autoaprueba.

## 8. Las reglas que se cargan siempre tienen que ser cortas
El estado del proyecto y las deudas crecen con cada change. Si viven en una regla "siempre relevante", cada sesión paga ese contexto y la regla se diluye. Estado → `docs/ESTADO.md`; reglas → `.claude/rules/workflow-routing.md`, corta.

## 9. Lo que el ejecutor no ve no existe
El ejecutor trabaja en un worktree: los archivos ignorados por git no están ahí. Si el contrato (SPEC, spine) está en `.gitignore`, OpenCode implementa sin él. Versiona los artefactos de contrato de `_bmad-output/`, o destila lo esencial en `openspec/config.yaml`.

## 10. El proceso no garantiza correctitud
BMAD y OpenSpec dan estructura y trazabilidad; los bugs reales los atrapa la **verificación contra la realidad**. Cada tarea termina con "verificar con …" concreto.

## 11. Las zonas se calibran por alcance del daño, no por dominio
Marcar rojo todo lo que "toca dinero" dejó a un proyecto personal casi entero en rojo: todo pasaba por Claude y el reparto de trabajo desaparecía. La pregunta correcta es qué puede salir mal y a quién le afecta: filtrar credenciales, abrir acceso, corromper la única copia de los datos o romper el despliegue es rojo en cualquier proyecto; la lógica importante cubierta por tests es amarilla en un proyecto de un usuario. `/descubrir` pregunta primero quién usa el sistema y cuántos entornos hay.

## 12. Lo mecánico se hace con scripts, no con el LLM
Crear issues, ramas, worktrees, etiquetas, calcular riesgo o regenerar el estado no requiere juicio: un script lo hace sin gastar tokens y sin equivocarse. El LLM se reserva para pensar. Por eso existen `scripts/nuevo.sh`, `scripts/harness.py` y sus envoltorios.

## 13. Una lista mantenida a mano es la forma más cara de guardar estado
Deudas y verificaciones diferidas en un Markdown se desincronizan (lección 3). Como issues, se cierran con el PR que las resuelve y se consultan con `gh`; el estado se **genera** (`harness.py estado`) en vez de mantenerse. Regla: si un dato puede derivarse de otra fuente, se genera; solo se mantiene a mano lo que no se puede derivar (reglas, decisiones, contrato).

## 14. Probar el paquete, no solo la lógica
Los hooks funcionaban en todas las pruebas locales y habrían fallado en silencio al clonar: git los tenía registrados sin permiso de ejecución y el bootstrap los "arreglaba" con `chmod` en el destino. La suite del harness incluye una prueba de empaquetado (modos en git), y el workflow `harness-selftest` la corre en CI.

## 15. Lo desconocido se bloquea, no se adivina
Enrutar una skill nueva por su prefijo es adivinar: `bmad-build` empieza como cualquier skill de redacción y, sin embargo, implementa código fuera de OpenSpec. Regla: lista blanca. Una skill que no está clasificada no corre en ninguna herramienta, CI falla si hay alguna instalada sin clasificar, y la clasificación deja evidencia (`skills_motivos`). Clasificar cuesta una sesión corta una vez; una skill mal enrutada cuesta en cada uso.

## 16. Un gate que se ejecuta desde el PR se puede reescribir desde el PR
El workflow `proceso` corría el `harness.py` y el `harness.json` de la rama del PR: bastaba vaciar las zonas rojas en la misma rama para bajar el riesgo. Regla: el gate corre con `pull_request_target`, y el motor y la config vienen de la rama base; el PR solo se lee. Lo mismo en local: los hooks usan el motor de `HEAD` y los guardias la config de `origin/main`.

## 17. Un guardia que falla abierto no es un guardia
Claude Code solo bloquea cuando el hook sale con 2; una excepción de Python sale con 1 y la acción pasa. Lo mismo el plugin de OpenCode, que capturaba el error y seguía. Regla: todo guardia de acciones sensibles falla cerrado, con un mensaje que dice cómo repararlo, y se prueba rompiéndolo.

## 18. Una casilla no es una revisión
`- [x] Revisión 1` la puede escribir cualquiera. La evidencia mínima es un registro atado al commit revisado que se invalida si el código cambia después; y para lo sensible, una aprobación de otra identidad en GitHub.

## 19. Documentar como límite lo que solo es una señal
"Máximo 5 archivos / 300 líneas" se leía como límite duro y era una señal de riesgo. Regla: el README no promete controles que el código no aplica; cada control declara su nivel (política, guardia, barrera, evidencia) en `docs/SEGURIDAD.md`.

## 20. El costo de un agente es contexto × pasos, no tamaño del diff
*Origen: change `add-codebase-memory-mcp` (2026-10-01). Con 36 tareas en 8 subsistemas y artefactos de ~11 000 tokens, GLM-5.3 gastó el 52 % de la ventana de 5 h de OpenCode Go en el 15 % de las tareas.* Cada llamada a una herramienta reenvía el contexto acumulado: una sesión larga cuesta mucho más que varias cortas con el mismo trabajo, y un change grande no ahorra por tener un solo proposal. Reglas, que hoy son **política** (las aplican los comandos `/cambio` y `/ejecutar-cambio`, no el motor; ver §19):
- **Changes de ≤ ~12 tareas** del ejecutor; si no, se parten.
- **Grupos de ≤ 5 tareas** etiquetados `(build)` o `(@mecanico)`, y una sesión de OpenCode por grupo.
- **Modelo por costo:** el más barato para tests, docs y repetición; `build` para diseño y seguridad; Claude solo para decidir y juzgar (cómo elegir el modelo: §21).
- **Leer rangos, no archivos enteros**; tests enfocados y la suite al cerrar el grupo; tres fallos seguidos → HANDOFF.md y parar.
- **Artefactos concisos:** el design lleva decisiones y evidencia, no repite el spec.
- **La revisión adversarial del plan se paga sola**: en el mismo change encontró dos fallos críticos de diseño antes de escribir código. No se recorta; lo que se recorta es la longitud de las sesiones.

## 21. En un agente se paga la caché, no la entrada
*Origen: el mismo change. `opencode stats` de la sesión: 200 K tokens de entrada, 21 K de salida y **7,1 M de lectura de caché** (97 %), unos 85 K de contexto por paso.* El precio de entrada que muestran las tablas engaña: lo que domina es el precio de **lectura de caché** multiplicado por el contexto reenviado en cada paso. Con los precios de OpenCode Go del 2026-10-01, esa misma sesión cuesta $2,22 con GLM-5.3 (caché $0,26/M), $0,33 con DeepSeek V4 Pro ($0,022/M), $0,13 con MiMo-V2.6-Pro ($0,0036/M) y $0,05 con MiMo-V2.6-Flash ($0,0028/M). Además, en Go las ventanas (5 h = 20 % del mensual, semana = 50 %) son **compartidas entre modelos**, pero cada modelo las llena a distinto ritmo: la tabla le da un tope mensual en dólares (GLM-5.3 y DeepSeek V4 Pro: $15; los Flash: $30–60), así que $1 de GLM-5.3 consume 4 veces más ventana que $1 de un Flash de $60. Lo observado cuadra: $2,36 de GLM-5.3 ≈ 78 % de la ventana de 5 h ($3), y al agotarla tampoco respondió DeepSeek. Un modelo caro paga dos veces: precio por token más alto y más ventana por dólar. Regla:
- Elige el modelo de cada agente por **precio de caché y peticiones por ventana** (tabla de opencode.ai/docs/go), no por el precio de entrada. Revísalo cuando cambien los precios.
- **El modelo de `build` sigue al riesgo** (`modelo_por_riesgo`): barato en riesgo bajo y medio, porque los tests atrapan los errores y la diferencia es ~5×; fuerte en riesgo alto, porque ahí un test verde no prueba que el código sea seguro y cada reintento de un modelo débil reenvía todo el contexto. Si el barato falla 3 veces, se escala.
- Cambiar de modelo no exime de la calidad: el modelo nuevo se prueba en un grupo de tareas con tests como juez antes de darlo por bueno, y el anterior queda en `fallbacks`.
- Los precios «Off-Peak» (DeepSeek) son de horario valle; en hora punta sube el costo. Los modelos DeepSeek de Go exigen activar la región «Global» en la cuenta: revisa a dónde van los prompts antes de usarlos con código privado.
- En OpenCode el modelo se cambia con `/models` (selector); `/model <id>` no lo cambia. Una sesión conserva el modelo con que arrancó aunque cambie `harness.json`.
- Los modelos gratis (`*-free`) ahorran poco frente a uno barato de Go, y pueden tener límites cambiantes y condiciones de datos distintas. Solo en repos sin datos sensibles y en roles verificables (`@mecanico`, `@explorador`).
