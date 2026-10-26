# Decisiones

| Decisión | Motivo | Coste |
| --- | --- | --- |
| TF-IDF local | Ranking inspeccionable, sin credenciales | No reconoce bien paráfrasis ni sinónimos |
| Respuesta extractiva | Cita contrastable con fuente y versión | Menos fluidez que una síntesis |
| Filtro previo al ranking | El corpus no mezcla grupos ni organizaciones | El integrador debe aportar permisos fiables |
| Versión optimista opcional | Detecta actualizaciones sobre una versión antigua | El cliente debe enviar `expected_version` para exigirlo |
| Sin rutas proporcionadas por el usuario | Evita lecturas arbitrarias del computador | El integrador debe enviar texto ya extraído |
| Dos métricas de evaluación | Distingue recuperación y abstención | Tres casos no permiten estimar calidad real |

Los ejemplos de orquestación y despliegue citados en referencias se usaron como material de estudio. El esquema, el ranking, los fixtures y los controles de acceso de esta implementación se definieron para este servicio.

El registro `document_revisions` conserva revisiones por organización e identificador incluso cuando se elimina el texto indexado. La baja avanza la revisión y la recreación continúa desde allí: versión 1, baja 2 y nueva publicación 3. Una escritura con `expected_version` antiguo falla antes o después de recrear el documento. La migración recoge versiones activas de bases anteriores; una baja de un documento ausente no consume revisión. La cita se identifica por documento, fragmento y versión, aunque la posición del fragmento mantenga su identificador estable.
