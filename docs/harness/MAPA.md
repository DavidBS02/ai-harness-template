# Mapa del proyecto (lo escribe Claude Code en /descubrir)

## 1. Qué es y para quién (3 líneas)

## 2. Arquitectura en una página
<!-- módulos principales, cómo se conectan, dónde entran datos, dónde salen -->

## 3. Zonas por sensibilidad
| Zona | Rutas | Por qué | Quién implementa | Quién revisa |
|---|---|---|---|---|
| 🔴 Roja | | auth, dinero, datos personales, migraciones, infra, sin tests | Claude Code (o OpenCode con spec muy cerrado) | revisor-gratis + revisor-fuerte + Luna + humano |
| 🟡 Amarilla | | lógica de negocio, integraciones, poco cubierta por tests | OpenCode build (GLM-5.3) | revisor-gratis + revisor-fuerte |
| 🟢 Verde | | UI simple, docs, tests, utilidades, bien cubierto por tests | OpenCode @mecanico (GLM-Flash) | revisor-gratis |

## 4. Zonas calientes (churn alto) y deuda
<!-- de INVENTARIO.md + lectura; qué se rompe seguido y por qué -->

## 5. Cobertura de tests: dónde hay red y dónde no

## 6. Reglas no escritas
<!-- convenciones que el código sigue pero nadie documentó; van a AGENTS.md -->

## 7. Lo que Claude NO entendió / dudas para el humano
