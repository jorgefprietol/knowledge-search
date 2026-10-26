# Knowledge Search

Búsqueda sobre documentación interna con separación por organización, permisos por grupo, versiones y citas. El servicio conserva el documento que respalda cada respuesta y se abstiene cuando la consulta no tiene suficiente coincidencia textual.

La implementación local usa SQLite y TF-IDF; funciona sin credenciales ni descargas. El modo Ollama utiliza un modelo para seleccionar una fuente entre las recuperadas y devuelve su fragmento original. Así, una respuesta siempre se puede contrastar con un documento y una versión.

## Ejecutar

Requiere Python 3.10 o superior. Desde la carpeta del repositorio:

```powershell
python -m app demo
python -m unittest discover -s tests -v
$env:SERVICE_TOKEN = [guid]::NewGuid().ToString('N')
python -m app serve
```

Abre `http://127.0.0.1:8080` e introduce el token de esa terminal. La demo usa una base temporal con políticas ficticias; el servidor conserva su base en `var/service.db`.

Para mantener una colección y ejecutar la evaluación:

```powershell
python -m app run --input data/seed.json --key seed-v1
python -m app run --input data/query.json --key query-1
python -m app run --input data/evaluation.json --key eval-1
python -m app metrics
```

## Contrato

`POST /api/run` requiere `Authorization: Bearer <SERVICE_TOKEN>`, `Content-Type: application/json` e `Idempotency-Key`. Repetir una clave con el mismo cuerpo devuelve el resultado guardado; cambiar el cuerpo produce un conflicto.

| Acción | Campos relevantes | Resultado |
| --- | --- | --- |
| `ingest` | `tenant`, `documents[]`: `id`, `title`, `text`, `access_group`, `expected_version` opcional | Documento y versión; lote atómico |
| `query` | `tenant`, `query`, `access_groups[]` opcional | Fragmento, fuente, versión, puntuación o abstención |
| `delete` | `tenant`, `document_id` | Retira documento y fragmentos del índice |
| `evaluate` | `tenant` | Resultados por consulta sobre el fixture incluido |
| `demo` | `tenant`, `query` | Carga políticas de ejemplo y consulta |

Los grupos se filtran antes de calcular las estadísticas y ordenar resultados. `public` significa visible dentro de la organización solicitada. Los identificadores de fragmento permanecen estables al actualizar la misma posición; `version` distingue el contenido recuperado.

## Evaluación y límites

El fixture contiene dos preguntas respondibles y una sin respuesta. Se calculan acierto de recuperación en primera posición y acierto de abstención por separado. Son medidas sobre ejemplos sintéticos, sin equivalencia con precisión empresarial. `/api/metrics` registra latencias de transacciones únicas completadas y eventos locales.

El token de servicio autentica al integrador. `tenant` y `access_groups` son afirmaciones de ese integrador: un despliegue multiusuario debe derivarlas de una identidad verificada, sin aceptar que el navegador las elija. La API local no sustituye ese control.

El índice se procesa en memoria por consulta y está pensado para colecciones pequeñas. No se implementan embeddings, Qdrant, LangChain ni AWS en este repositorio. La búsqueda semántica distribuida requiere un adaptador y nuevas evaluaciones. La conexión Ollama necesita un servidor y un modelo configurados; las pruebas locales no validan ese servicio externo.

Consulta [arquitectura](docs/architecture.md), [decisiones](docs/decisions.md), [operación](docs/operations.md) y [referencias](docs/references.md).
