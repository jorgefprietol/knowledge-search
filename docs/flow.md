# Flujo de operación

![Flujo de operación](diagrams/flow.svg)

[Abrir SVG](diagrams/flow.svg) · [Fuente Mermaid](diagrams/flow.mmd)


<details>
<summary>Versión Mermaid</summary>

```mermaid
flowchart TD
    Start["Recibir operación autenticada"] --> Action{"¿Ingesta o consulta?"}
    Action -->|Ingesta| Version["Validar documento y versión esperada"]
    Version --> Split["Reemplazar fragmentos de forma atómica"]
    Split --> Audit["Persistir versión y auditoría"]
    Action -->|Consulta| Access["Filtrar tenant y grupos autorizados"]
    Access --> Rank["Calcular ranking TF-IDF"]
    Rank --> Evidence{"¿Supera cobertura y puntuación?"}
    Evidence -->|No| Abstain["Abstenerse por evidencia insuficiente"]
    Evidence -->|Sí| Select["Seleccionar fuente local u Ollama"]
    Select --> Valid{"¿Identificador entre candidatos?"}
    Valid -->|Sí| Cite["Devolver extracto, documento y versión"]
    Valid -->|No| Abstain
```

</details>

- La actualización de un documento reemplaza sus fragmentos dentro de la misma transacción.
- El corpus usado para calcular TF-IDF contiene sólo documentos visibles; la puntuación no es una probabilidad.
- La selección opcional valida `source_id`; la respuesta conserva el extracto almacenado, no texto libre del modelo.

Las operaciones del dominio se guardan junto a auditoría y respuesta idempotente en la transacción del servicio local. Un error revierte los cambios de esa solicitud.

[Arquitectura](architecture.md) · [Tecnologías y alcance](technologies.md)
