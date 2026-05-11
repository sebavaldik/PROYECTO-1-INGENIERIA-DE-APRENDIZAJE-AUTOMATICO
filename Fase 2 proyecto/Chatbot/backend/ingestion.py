"""
Pipeline de ingestión de datos para el chatbot RAG de Mecánica de Bicicletas.
Carga PDFs/Markdown desde data/sources, los fragmenta y almacena en ChromaDB.
"""

import os
import sys
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

SOURCES_DIR = Path(__file__).parent.parent / "data" / "pdfs"
CHROMA_DIR = Path(__file__).parent.parent / "data" / "chroma_db"

EMBEDDING_MODEL = "BAAI/bge-m3"

CHUNK_SIZE = 512
CHUNK_OVERLAP = 100


def load_documents(sources_dir: Path) -> list:
    docs = []
    files = list(sources_dir.iterdir()) if sources_dir.exists() else []

    if not files:
        print(f"[AVISO] No se encontraron archivos en {sources_dir}")
        print("Coloca archivos .pdf o .md en esa carpeta y vuelve a ejecutar.")
        return docs

    for path in files:
        try:
            if path.suffix.lower() == ".pdf":
                loader = PyPDFLoader(str(path))
                docs.extend(loader.load())
                print(f"  [OK] PDF cargado: {path.name}")
            elif path.suffix.lower() in (".md", ".markdown"):
                loader = UnstructuredMarkdownLoader(str(path))
                docs.extend(loader.load())
                print(f"  [OK] Markdown cargado: {path.name}")
            else:
                print(f"  [SKIP] Formato no soportado: {path.name}")
        except Exception as e:
            print(f"  [ERROR] {path.name}: {e}")

    return docs


def split_documents(docs: list) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"  Chunks generados: {len(chunks)}")
    return chunks


def build_vectorstore(chunks: list) -> Chroma:
    print(f"  Generando embeddings con '{EMBEDDING_MODEL}'...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name="bike_mechanics",
    )
    print(f"  Vector store guardado en: {CHROMA_DIR}")
    return db


def main():
    print("=== Pipeline de Ingestión RAG ===\n")
    print(f"Fuentes: {SOURCES_DIR}")

    print("\n[1/3] Cargando documentos...")
    docs = load_documents(SOURCES_DIR)
    if not docs:
        sys.exit(0)

    print(f"\n[2/3] Fragmentando {len(docs)} páginas/secciones...")
    chunks = split_documents(docs)

    print("\n[3/3] Construyendo vector store...")
    build_vectorstore(chunks)

    print("\n[LISTO] Ingestión completada. El chatbot ya puede responder preguntas.")


if __name__ == "__main__":
    main()
