# Tecnologías y alcance

Python 3.10+, SQLite y recuperación TF-IDF con normalización de acentos. Ollama puede seleccionar una fuente; n8n y Docker se incluyen como opciones de integración.

| Tecnología | Estado | Uso en este proyecto |
| --- | --- | --- |
| Python 3.10+ / unicodedata / collections | Implementado | Normalización lexical, tokenización y corpus local. |
| SQLite / sqlite3 | Implementado | Documentos, versiones, grupos, fragmentos, auditoría e idempotencia. |
| TF-IDF y similitud coseno | Implementado | Recuperación lexical con filtros previos y umbrales de evidencia. |
| Ollama / HTTP JSON | Opcional | Selecciona una fuente candidata válida; requiere servidor y modelo. |
| n8n | Workflow incluido | Entrada hacia el contrato HTTP; requiere credenciales e importación. |
| Docker / Compose | Archivos incluidos | Servicio y perfil de orquestación local; necesita validación de contenedores. |
| unittest / GitHub Actions | Implementado | Aislamiento, versiones, abstención, evaluación y contrato HTTP. |
| Embeddings, base vectorial y repositorios externos | No implementados | La versión actual no usa Qdrant, LangChain ni conectores cloud de documentos. |

“Implementado” describe código disponible y comprobable en el repositorio. “Opcional” requiere un proveedor configurado; “incluido” identifica un archivo o adaptador entregado, sin afirmar una integración externa ejecutada.

[Arquitectura](architecture.md) · [Flujo de operación](flow.md) · [Integraciones](integrations.md)
