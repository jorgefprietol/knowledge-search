# Operación

La eliminación de un documento retira sus fragmentos del índice. Las respuestas ya emitidas permanecen en el registro de idempotencia y pueden contener extractos de versiones anteriores. Una política de retención o supresión debe cubrir también `requests`, copias de seguridad y exportaciones; cambiar un grupo de acceso no purga esas copias históricas.

1. Ejecutar pruebas antes de importar documentos.
2. Cargar `data/seed.json` en una base local de prueba y ejecutar `data/evaluation.json`.
3. Configurar `SERVICE_TOKEN` con al menos 24 caracteres y arrancar el servicio en loopback.
4. Consultar `/health` y `/api/metrics`; conservar los resultados de evaluación por versión de colección.

La demo no altera la base persistente. `run` y `serve` comparten `DATABASE_PATH` o `--db`. Detener el servicio antes de copiar la base para respaldos simples; si se respalda en caliente, usar la API de backup de SQLite para incluir el estado WAL correctamente.

Para usar un modelo, configurar `MODEL_BACKEND=ollama`, el servidor `OLLAMA_URL` y `OLLAMA_MODEL` según `.env.example`. No se descargan modelos automáticamente. Una caída del selector revierte la petición y puede reintentarse con la misma clave; no se convierte silenciosamente en una respuesta del modelo.

Un cambio de política se publica con `ingest` y `expected_version`. Repetir exactamente el mismo documento no incrementa su versión. Para retirar una política, ejecutar `delete` y comprobar que las consultas dejan de citarla.

En un entorno compartido, el proxy debe proporcionar TLS, identidad y límites de tráfico, y el adaptador debe fijar organización y grupos desde las credenciales. Separar la administración documental de las consultas de empleados antes de exponer la API.

No publicar bases locales, datos internos ni tokens. Los ejemplos incluidos son ficticios. El índice conserva solo la última versión; la retención histórica exige almacenamiento adicional.
