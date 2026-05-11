# Bike Mechanic AI — Chatbot RAG

Chatbot especializado en **mecánica y mantenimiento de bicicletas**, construido con RAG (Retrieval-Augmented Generation). Combina una base de conocimiento local (33 manuales PDF de Shimano, SRAM, Park Tool y RockShox) con un LLM local vía Ollama para dar respuestas técnicas precisas **sin depender de Internet ni de APIs de pago**.

---

## Arquitectura

```
Usuario → Frontend (HTML + TailwindCSS)
               ↓  POST /chat
          Backend FastAPI
               ↓  búsqueda semántica (BAAI/bge-m3)
          ChromaDB  ←── ingestion.py ←── data/pdfs/*.pdf
               ↓  contexto relevante
          Ollama (llama3.2) ──→ Respuesta en español
```

| Componente | Tecnología |
|------------|-----------|
| LLM local | llama3.2 vía Ollama |
| Embeddings | BAAI/bge-m3 (multilingüe) |
| Vector store | ChromaDB |
| Backend | FastAPI + Python 3.11 |
| Frontend | HTML + TailwindCSS (sin build) |

---

## Opción A — Con Docker (recomendada)

Esta opción instala y configura todo automáticamente. Solo necesitas Docker.

### Prerequisitos

| Herramienta | Para qué sirve | Descarga |
|-------------|---------------|---------|
| Docker Desktop | Correr los contenedores | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| Git | Clonar el repositorio | [git-scm.com](https://git-scm.com) |

> **Requisitos de hardware:** al menos 8 GB de RAM y ~6 GB de espacio libre en disco (modelo llama3.2 ~2 GB + embeddings bge-m3 ~1.5 GB + ChromaDB).

### Paso 1 — Instalar Docker Desktop

1. Descarga Docker Desktop desde [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
2. Ejecuta el instalador y sigue los pasos (puede pedir reiniciar el equipo)
3. Abre Docker Desktop y espera a que el ícono de la ballena en la barra de tareas quede en verde
4. Verifica la instalación abriendo una terminal y ejecutando:
   ```bash
   docker --version
   docker compose version
   ```

### Paso 2 — Clonar el repositorio

```bash
git clone https://github.com/sebavaldik/PROYECTO-1-INGENIERIA-DE-APRENDIZAJE-AUTOMATICO.git
cd bike-mechanic-chatbot
```

### Paso 3 — Levantar el sistema

```bash
docker compose up --build
```

Este comando hace todo automáticamente en orden:
1. Construye la imagen del backend con todas las dependencias Python
2. Levanta el servidor Ollama
3. Descarga el modelo `llama3.2` (~2 GB, solo la primera vez)
4. Genera los embeddings con `BAAI/bge-m3` e indexa los 33 PDFs en ChromaDB (~20-30 min, solo la primera vez)
5. Levanta el servidor FastAPI en el puerto 8000

Cuando veas este mensaje en la terminal, el sistema está listo:

```
bike_chatbot_api  | [4/4] Iniciando servidor FastAPI en 0.0.0.0:8000 ...
bike_chatbot_api  | INFO:     Application startup complete.
```

> En los **reinicios siguientes** los pasos 3 y 4 se omiten gracias a los volúmenes de Docker, por lo que el arranque tarda solo unos segundos.

### Paso 4 — Abrir el frontend

Abre el archivo `frontend/index.html` directamente en tu navegador (doble clic o arrastrar al navegador).

La burbuja verde en la esquina superior derecha del chat confirma que el backend está conectado.

### Comandos útiles de Docker

```bash
# Detener los servicios (conserva los datos)
docker compose down

# Detener y eliminar todos los datos descargados (modelos, ChromaDB, embeddings)
docker compose down -v

# Ver los logs en tiempo real
docker compose logs -f api

# Reiniciar solo el backend
docker compose restart api
```

---

## Opción B — Instalación local (sin Docker)

Esta opción requiere instalar Python y Ollama manualmente.

### Prerequisitos

| Herramienta | Versión mínima | Descarga |
|-------------|---------------|---------|
| Python | 3.10 o superior | [python.org/downloads](https://www.python.org/downloads/) |
| Ollama | 0.3 o superior | [ollama.com/download](https://ollama.com/download) |
| Git | Cualquier versión reciente | [git-scm.com](https://git-scm.com) |

> **Requisitos de hardware:** al menos 8 GB de RAM y ~6 GB de espacio libre en disco.

### Paso 1 — Instalar Python

1. Descarga Python desde [python.org/downloads](https://www.python.org/downloads/) (versión 3.10 o superior)
2. Durante la instalación, **marca la casilla "Add Python to PATH"** (importante)
3. Verifica la instalación:
   ```bash
   python --version
   pip --version
   ```

### Paso 2 — Instalar Ollama

1. Descarga Ollama desde [ollama.com/download](https://ollama.com/download)
2. Ejecuta el instalador
3. Verifica la instalación:
   ```bash
   ollama --version
   ```

### Paso 3 — Clonar el repositorio

```bash
git clone https://github.com/sebavaldik/PROYECTO-1-INGENIERIA-DE-APRENDIZAJE-AUTOMATICO.git
cd bike-mechanic-chatbot
```

### Paso 4 — Crear un entorno virtual

```bash
# Crear el entorno
python -m venv .venv

# Activarlo en Windows
.venv\Scripts\activate

# Activarlo en Linux / Mac
source .venv/bin/activate
```

Sabrás que está activo porque el prompt de la terminal mostrará `(.venv)` al inicio.

### Paso 5 — Instalar las dependencias Python

```bash
pip install -r requirements.txt
```

Esto puede tardar varios minutos la primera vez.

### Paso 6 — Descargar el modelo LLM

```bash
ollama pull llama3.2
```

Descarga ~2 GB. Solo se hace una vez.

### Paso 7 — Indexar los PDFs (solo la primera vez)

```bash
python backend/ingestion.py
```

Este proceso genera los embeddings con `BAAI/bge-m3` y almacena los vectores en `data/chroma_db/`. Tarda entre 20-30 minutos la primera vez por el tamaño del modelo de embeddings.

### Paso 8 — Iniciar el servidor

Necesitas **dos terminales abiertas**:

**Terminal 1 — Servidor Ollama** (si no está corriendo como servicio):
```bash
ollama serve
```

**Terminal 2 — Backend FastAPI** (con el entorno virtual activo):
```bash
python backend/main.py
```

Verás este mensaje cuando esté listo:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Paso 9 — Abrir el frontend

Abre el archivo `frontend/index.html` directamente en tu navegador (doble clic o arrastrar al navegador).

La burbuja verde en la esquina superior derecha del chat confirma que el backend está conectado.

---

## Probar el chatbot

### Opción 1 — Interfaz de chat (frontend)

1. Asegúrate de que el servidor esté corriendo (ver sección de instalación)
2. Abre `frontend/index.html` en tu navegador
3. Verifica que el indicador de estado en la esquina superior derecha esté en **verde** (backend conectado)
4. Escribe tu pregunta en el cuadro de texto y presiona **Enter** o el botón de enviar

Puedes usar las preguntas de ejemplo que aparecen como botones en la pantalla, o escribir las tuyas propias. Algunas preguntas sugeridas para probar el sistema:

| # | Pregunta de prueba | Tema |
|---|-------------------|------|
| 1 | ¿Cuál es el procedimiento para purgar frenos de disco hidráulicos Shimano con kit de embudo? | Frenos |
| 2 | ¿Cómo se ajustan los tornillos de límite H y L de un desviador delantero? | Transmisión |
| 3 | ¿Qué herramientas necesito para extraer un cassette de 11 velocidades y cuál es el torque de instalación? | Transmisión |
| 4 | ¿Qué presión PSI necesita una horquilla RockShox Lyrik para un ciclista de 85 kg con 25% de sag? | Suspensión |
| 5 | ¿Cómo diagnostico y elimino un crujido en el headset de una bicicleta de ruta? | Dirección |
| 6 | ¿Cuál es la diferencia entre una caída y una subida del cambio trasero indexado? | Transmisión |
| 7 | ¿Qué señales indican que una cadena está desgastada según el calibrador chain checker? | Cadena |
| 8 | ¿Cómo reemplazo una cámara pinchada en la rueda trasera sin dañar el desviador? | Ruedas |
| 9 | ¿Qué lubricante se recomienda para la cadena bajo lluvia y cada cuántos km se reaaplica? | Mantenimiento |
| 10 | ¿Cuáles son los pasos para retirar e instalar un pedalier Hollowtech II con el torque correcto? | Pedalier |

> Cada respuesta puede tardar entre 30 y 90 segundos dependiendo del hardware. Esto es normal ya que el modelo corre localmente.

---

### Opción 2 — Benchmark automático (10 preguntas)

El script `eval/test_bench.py` envía las 10 preguntas de la tabla anterior al backend de forma automática, mide la latencia de cada una y guarda los resultados.

**Con instalación local** (asegúrate de que el servidor esté corriendo):
```bash
# Abre una nueva terminal con el entorno virtual activo
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Linux / Mac

python eval/test_bench.py
```

**Con Docker** (en una nueva terminal, mientras `docker compose up` sigue corriendo):
```bash
docker compose exec api python eval/test_bench.py
```

La salida en terminal se verá así:
```
============================================================
  BENCHMARK RAG - Mecánica de Bicicletas
============================================================

[OK] Backend conectado. Enviando 10 preguntas...

[01/10] ¿Cuál es el procedimiento paso a paso para purgar unos frenos de disco...
       → OK (61.98s) | Según el manual técnico de SHIMANO, el procedimiento...

[02/10] ¿Cómo se ajustan los tornillos de límite (H y L) en un desviador delan...
       → OK (43.12s) | Según el manual, para ajustar los tornillos de límite...
...
============================================================
  Completado: 10/10 exitosas
  Resultados guardados en: eval/results.json
============================================================
```

Los resultados completos (pregunta, respuesta, fuentes citadas y latencia) quedan guardados en `eval/results.json`.

Resultado actual del sistema: **10/10 preguntas exitosas**, latencia promedio ~38 s/pregunta.

---

### Opción 3 — API directamente (para desarrolladores)

Con el servidor corriendo, puedes hacer consultas directamente al endpoint `/chat`:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "¿Cómo se purgan los frenos Shimano?", "history": []}'
```

También puedes explorar la documentación interactiva de la API en:
```
http://localhost:8000/docs
```

---

## Estructura del proyecto

```
chatbot/
├── backend/
│   ├── ingestion.py       # Pipeline: carga PDF → fragmenta → embeddings → ChromaDB
│   └── main.py            # Servidor FastAPI + cadena RAG
├── frontend/
│   └── index.html         # Interfaz de chat (sin dependencias de build)
├── data/
│   └── pdfs/              # 33 manuales PDF (Shimano, SRAM, Park Tool, RockShox)
├── eval/
│   ├── test_bench.py      # Benchmark automático (10 preguntas)
│   ├── results.json       # Resultados del último benchmark
│   └── Informe_Pruebas.md # Análisis de resultados
├── Dockerfile             # Imagen del backend + ingestión
├── docker-compose.yml     # Orquestación: ollama + api
├── entrypoint.sh          # Script de arranque del contenedor api
├── requirements.txt
└── README.md
```

---

## Parámetros configurables

### `backend/ingestion.py`
| Variable | Valor actual | Descripción |
|----------|-------------|-------------|
| `CHUNK_SIZE` | 512 | Tamaño de fragmentos en caracteres |
| `CHUNK_OVERLAP` | 100 | Solapamiento entre fragmentos |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Modelo de embeddings multilingüe |

### `backend/main.py`
| Variable | Valor actual | Descripción |
|----------|-------------|-------------|
| `OLLAMA_MODEL` | `llama3.2` | Modelo LLM local |
| `TOP_K` | 8 | Chunks recuperados por consulta |
| `temperature` | 0.2 | Creatividad del LLM (0 = determinista) |

---

## Notas técnicas

- El frontend se conecta a `http://localhost:8000` — no requiere servidor web, solo abrir el HTML en el navegador.
- ChromaDB persiste en `data/chroma_db/` (local) o en el volumen `chroma_db` (Docker).
- El historial de conversación se mantiene en el navegador (últimas 6 interacciones enviadas al LLM).
- Cada pregunta del benchmark se evalúa de forma independiente (sin historial compartido entre preguntas).
- Si agregas nuevos PDFs a `data/pdfs/`, vuelve a ejecutar `ingestion.py` para reindexarlos.
