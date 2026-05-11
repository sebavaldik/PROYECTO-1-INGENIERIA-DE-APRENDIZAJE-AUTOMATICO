# ── Base image ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# ── System dependencies ──────────────────────────────────────────────────────
# build-essential → compilar paquetes nativos (chromadb, etc.)
# curl            → health checks y llamadas a la API de Ollama en entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ──────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir \
        langchain-huggingface>=0.1.0 \
        cryptography>=43.0.0

# ── Application code ─────────────────────────────────────────────────────────
COPY backend/   ./backend/
COPY data/pdfs/ ./data/pdfs/
COPY eval/      ./eval/
COPY frontend/  ./frontend/

# ── Entrypoint ───────────────────────────────────────────────────────────────
COPY entrypoint.sh .
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
