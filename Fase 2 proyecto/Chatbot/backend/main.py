"""
Servidor FastAPI con cadena RAG para el chatbot de Mecánica de Bicicletas.
Recupera contexto desde ChromaDB y genera respuestas con Ollama (llama3.2).
"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ── Configuración ───────────────────────────────────────────────────────────
CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma_db"
EMBEDDING_MODEL = "BAAI/bge-m3"
OLLAMA_MODEL = "llama3.2"
TOP_K = 8  # Número de chunks recuperados

SYSTEM_PROMPT = """Eres un mecánico experto en bicicletas con acceso a manuales técnicos oficiales de Shimano, SRAM, Park Tool y RockShox.

INSTRUCCIONES:
- Usa el contexto de los manuales como tu fuente principal. Responde siempre en español.
- Si el contexto contiene la información solicitada, explícala con pasos numerados y precisión técnica.
- Si hay valores numéricos exactos en el contexto (torques N·m, PSI, km), cítalos tal como aparecen.
- Si el contexto tiene información parcial, úsala y complementa con tu conocimiento técnico general de mecánica de bicicletas, dejando claro qué parte viene del manual y qué parte es conocimiento general.
- Nunca inventes marcas, modelos o números de parte específicos que no estén en el contexto."""

# ── Inicialización ──────────────────────────────────────────────────────────
app = FastAPI(
    title="Bike Mechanics RAG Chatbot",
    description="Chatbot especializado en mecánica y mantenimiento de bicicletas",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_vectorstore: Optional[Chroma] = None


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        if not CHROMA_DIR.exists():
            raise RuntimeError(
                "Vector store no encontrado. Ejecuta primero: python backend/ingestion.py"
            )
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        _vectorstore = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=embeddings,
            collection_name="bike_mechanics",
        )
    return _vectorstore


# ── Esquemas ────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []  # [{"role": "user"|"assistant", "content": "..."}]


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


# ── Lógica RAG ──────────────────────────────────────────────────────────────
def retrieve_context(query: str) -> tuple[str, list[str]]:
    db = get_vectorstore()
    results = db.similarity_search(query, k=TOP_K)

    context_parts = []
    sources = []
    for doc in results:
        context_parts.append(doc.page_content)
        source = doc.metadata.get("source", "desconocido")
        if source not in sources:
            sources.append(source)

    return "\n\n---\n\n".join(context_parts), sources


def build_messages(history: list[dict], context: str, user_message: str) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for turn in history[-6:]:  # Mantener las últimas 6 interacciones
        messages.append({"role": turn["role"], "content": turn["content"]})

    user_content = f"""Contexto del manual:
{context}

Pregunta del usuario:
{user_message}"""

    messages.append({"role": "user", "content": user_content})
    return messages


def generate_answer(messages: list[dict]) -> str:
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=messages,
        options={"temperature": 0.2},
    )
    try:
        return response.message.content
    except AttributeError:
        return response["message"]["content"]


# ── Endpoints ───────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "model": OLLAMA_MODEL}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    try:
        context, sources = retrieve_context(request.message)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    messages = build_messages(request.history, context, request.message)

    try:
        answer = generate_answer(messages)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error al conectar con Ollama. ¿Está en ejecución? Detalle: {e}",
        )

    return ChatResponse(answer=answer, sources=sources)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
