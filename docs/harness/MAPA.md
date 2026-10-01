# Mapa del proyecto (lo escribe Claude Code en /descubrir)

## 1. Qué es y para quién (3 líneas)

## 2. Arquitectura en una página
<!-- módulos principales, cómo se conectan, dónde entran datos, dónde salen -->

## 3. Zonas por alcance del daño (no por dominio: ver docs/LECCIONES.md §11)
<!-- Primero: ¿quién usa el sistema (solo tú / equipo / clientes)? ¿cuántos entornos hay? Las regex reales van a harness.json → zonas. -->
| Zona | Rutas | Por qué | Quién implementa | Quién revisa |
|---|---|---|---|---|
| 🔴 Roja | | puede filtrar credenciales, abrir acceso, corromper la única copia de los datos o romper el despliegue | Claude Code, u OpenCode con `OpenCode-zona-roja: autorizado` | revisor-gratis + revisor-fuerte + Luna + humano |
| 🟡 Amarilla | | lógica importante (incluido dinero en un proyecto personal) cubierta por tests | OpenCode build (GLM-5.3) | revisor-gratis + revisor-fuerte |
| 🟢 Verde | | UI simple, docs, tests, utilidades, bien cubierto por tests | OpenCode @mecanico (GLM-Flash) | revisor-gratis |

## 4. Zonas calientes (churn alto) y deuda
<!-- de INVENTARIO.md + lectura; qué se rompe seguido y por qué -->

## 5. Cobertura de tests: dónde hay red y dónde no

## 6. Reglas no escritas
<!-- convenciones que el código sigue pero nadie documentó; van a AGENTS.md -->

## 7. Memoria de código
<!-- La escribe /descubrir (paso «¿Memoria de código?») tras confirmarla con el humano. Interruptor: harness.json → mcp.codebase_memory.habilitado -->
- Decisión: encendida | apagada (confirmada por el humano el <fecha>)
- Justificación: <qué de la visión y el objetivo pesó: tamaño, módulos, lenguajes, vida esperada, trabajo en paralelo>
- Revisar: <solo en proyecto verde: «en el primer hito», con el issue verificacion-diferida #<n>>

## 8. Lo que Claude NO entendió / dudas para el humano
