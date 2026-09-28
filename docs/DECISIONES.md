# Decisiones vigentes del usuario (append-only)

No se vuelven a preguntar. Si algo las contradice, es un **cambio de decisión**, no un olvido: se añade una entrada nueva que la reemplaza, citando la anterior. Nunca se borra ni se edita una entrada.

Formato:
```
## AAAA-MM-DD — <título corto>
- Decisión: …
- Por qué: …
- Reemplaza a: (fecha y título, si aplica)
- Dónde se aplica: (AD-*, CAP-*, change, archivo)
```
