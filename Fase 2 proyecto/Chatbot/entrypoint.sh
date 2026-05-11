#!/bin/bash
# =============================================================================
# Entrypoint del contenedor API
# 1. Espera a que Ollama esté listo
# 2. Descarga llama3.2 si no está disponible
# 3. Ejecuta la ingestión si chroma_db no existe
# 4. Arranca el servidor FastAPI
# =============================================================================
set -e

OLLAMA_BASE="http://ollama:11434"
CHROMA_DB="/app/data/chroma_db/chroma.sqlite3"
MODEL="llama3.2"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   Bike Mechanics RAG Chatbot — arranque      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── 1. Esperar a Ollama ────────────────────────────────────────────────────
echo "[1/4] Esperando al servicio Ollama en $OLLAMA_BASE ..."
until curl -sf "$OLLAMA_BASE/api/version" > /dev/null; do
    echo "      Ollama no está listo aún, reintentando en 5 s..."
    sleep 5
done
echo "      ✓ Ollama disponible"
echo ""

# ── 2. Descargar el modelo si no está presente ─────────────────────────────
echo "[2/4] Verificando modelo '$MODEL' ..."
if curl -sf -X POST "$OLLAMA_BASE/api/show" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$MODEL\"}" > /dev/null 2>&1; then
    echo "      ✓ Modelo '$MODEL' ya presente"
else
    echo "      Descargando '$MODEL' (puede tardar varios minutos la primera vez)..."
    curl -X POST "$OLLAMA_BASE/api/pull" \
         -H "Content-Type: application/json" \
         -d "{\"name\":\"$MODEL\",\"stream\":false}" \
         --max-time 1200
    echo ""
    echo "      ✓ Modelo '$MODEL' descargado"
fi
echo ""

# ── 3. Ingestión de PDFs → ChromaDB ───────────────────────────────────────
if [ ! -f "$CHROMA_DB" ]; then
    echo "[3/4] Base vectorial no encontrada. Ejecutando ingestión de PDFs..."
    echo "      (Esto tarda ~20-30 min la primera vez por el modelo bge-m3)"
    cd /app && python backend/ingestion.py
    echo "      ✓ Ingestión completada"
else
    echo "[3/4] Base vectorial encontrada — omitiendo ingestión."
fi
echo ""

# ── 4. Arrancar FastAPI ───────────────────────────────────────────────────
echo "[4/4] Iniciando servidor FastAPI en 0.0.0.0:8000 ..."
echo ""
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
