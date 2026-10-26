# Arquitectura

![Arquitectura del servicio](diagrams/architecture.svg)

[Abrir SVG](diagrams/architecture.svg) · [Fuente Mermaid](diagrams/architecture.mmd)


La ingesta genera documentos versionados y fragmentos citables. La consulta aplica permisos antes del ranking y devuelve un extracto verificable o una abstención.

<details>
<summary>Versión Mermaid</summary>

```mermaid
flowchart TB
    Client["CLI o consola web"] --> API["API con token e idempotencia"]
    subgraph Local["Servicio local implementado"]
        API --> Ingest["Ingesta y control de versión"]
        Ingest --> Chunks["Fragmentos e identificadores estables"]
        Chunks --> DB["SQLite y auditoría"]
        API --> Access["Filtro de organización y grupos"]
        DB --> Access
        Access --> Rank["Ranking TF-IDF y umbrales"]
        Rank --> Answer["Extracto citado o abstención"]
        API --> Eval["Evaluación sobre fixture"]
    end
    subgraph Optional["Componentes opcionales por configurar"]
        N8N["Workflow n8n incluido"]
        Model["Selector de fuentes Ollama"]
    end
    N8N -.-> API
    Rank -.-> Model
    Model -.-> Answer
```

</details>

Las líneas continuas muestran el recorrido implementado dentro de cada límite. Las líneas discontinuas indican componentes opcionales, entregados para configurar o aún por conectar; su estado se precisa en [tecnologías](technologies.md).

`documents` almacena la última versión y su grupo. `chunks` conserva segmentos de aproximadamente 700 caracteres y sus posiciones. Una actualización reemplaza los segmentos dentro de la misma transacción; no quedan citas antiguas en el índice. La auditoría registra organización, cantidad y resultado, sin guardar la consulta completa en el evento.

El ranking normaliza acentos, elimina palabras frecuentes y calcula coseno de vectores TF-IDF. Exige cobertura mínima de términos y una puntuación mínima. Es una heurística lexical explícita, sin interpretar las puntuaciones como probabilidades. Los filtros SQL se aplican antes de construir el corpus de ranking.

En modo Ollama se admite únicamente un `source_id` de los candidatos. El texto de respuesta procede del fragmento almacenado: el modelo no puede sustituirlo por una afirmación libre. Las instrucciones incrustadas en documentos se presentan como datos. Esto reduce la superficie generativa; no convierte el contenido documental en confiable.

El host HTTP abre una conexión por petición. SQLite serializa escrituras y la transacción incluye cambios, auditoría y registro de idempotencia. Los adaptadores de identidad y los repositorios documentales externos quedan fuera del límite local.

[Flujo de operación](flow.md) · [Tecnologías y alcance](technologies.md)
