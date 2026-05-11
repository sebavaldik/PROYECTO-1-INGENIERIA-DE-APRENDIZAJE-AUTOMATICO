"""
Benchmark automático: envía las 10 preguntas del dominio al chatbot RAG
y guarda las respuestas en eval/results.json.
"""

import json
import time
import sys
import io
from datetime import datetime
from pathlib import Path

# Forzar UTF-8 en la salida para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import httpx

API_URL = "http://localhost:8000"
OUTPUT_FILE = Path(__file__).parent / "results.json"
TIMEOUT = 300  # segundos por pregunta

QUESTIONS = [
    "¿Cuál es el procedimiento paso a paso para purgar unos frenos de disco hidráulicos Shimano usando el kit de embudo?",
    "¿Cómo se ajustan los tornillos de límite (H y L) en un desviador delantero para evitar que la cadena se salga?",
    "¿Qué herramientas específicas se necesitan para extraer un cassette de 11 velocidades y cuál es el torque recomendado para volver a instalarlo?",
    "¿Cuál es la presión de aire (PSI) recomendada para una horquilla RockShox Lyrik si el ciclista pesa 85 kg y busca un sag del 25%?",
    "¿Cómo se diagnostica y elimina un crujido en la dirección (headset) de una bicicleta de ruta con cableado interno?",
    "¿Cuál es la diferencia entre una caída y una subida del cambio trasero indexado, y cuál tornillo del desviador (H/L o tensión de cable) se debe ajustar en cada caso?",
    "¿Qué señales indican que una cadena está desgastada y qué medición entrega el calibrador 'chain checker' para determinarlo (0,5%, 0,75%, 1%)?",
    "¿Cómo se reemplaza correctamente una cámara pinchada en la rueda trasera con cambios, evitando dañar el desviador y respetando la dirección de rotación del neumático?",
    "¿Qué lubricante (seco vs. húmedo) se recomienda para una cadena bajo lluvia, y cada cuántos kilómetros conviene reaplicarlo?",
    "¿Cuáles son los pasos para retirar e instalar un pedalier Hollowtech II, incluyendo el sentido de rosca de la copa derecha y el torque final de apriete?",
]


def check_health(client: httpx.Client) -> bool:
    try:
        res = client.get(f"{API_URL}/health", timeout=5)
        return res.status_code == 200
    except Exception:
        return False


def ask(client: httpx.Client, question: str, history: list) -> dict:
    payload = {"message": question, "history": history}
    try:
        res = client.post(f"{API_URL}/chat", json=payload, timeout=TIMEOUT)
        res.raise_for_status()
        data = res.json()
        return {
            "answer": data.get("answer", ""),
            "sources": data.get("sources", []),
            "error": None,
        }
    except httpx.TimeoutException:
        return {"answer": "", "sources": [], "error": "TIMEOUT"}
    except Exception as e:
        return {"answer": "", "sources": [], "error": str(e)}


def run_benchmark():
    print("=" * 60)
    print("  BENCHMARK RAG - Mecánica de Bicicletas")
    print("=" * 60)

    with httpx.Client() as client:
        if not check_health(client):
            print(f"\n[ERROR] No se puede conectar al backend en {API_URL}")
            print("Asegúrate de que el servidor FastAPI esté en ejecución:")
            print("  python backend/main.py")
            sys.exit(1)

        print(f"\n[OK] Backend conectado. Enviando {len(QUESTIONS)} preguntas...\n")

        results = []

        for i, question in enumerate(QUESTIONS, 1):
            print(f"[{i:02d}/{len(QUESTIONS)}] {question[:70]}...")
            t0 = time.time()

            # Cada pregunta se evalúa de forma independiente (sin historial)
            result = ask(client, question, [])
            elapsed = round(time.time() - t0, 2)

            if result["error"]:
                status = f"ERROR: {result['error']}"
                print(f"       → {status} ({elapsed}s)\n")
            else:
                status = "OK"
                preview = result["answer"][:100].replace("\n", " ")
                print(f"       → {status} ({elapsed}s) | {preview}...\n")

            results.append({
                "id": i,
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"],
                "latency_s": elapsed,
                "status": status,
            })

        output = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "api_url": API_URL,
                "total_questions": len(QUESTIONS),
                "successful": sum(1 for r in results if r["status"] == "OK"),
                "failed": sum(1 for r in results if r["status"] != "OK"),
            },
            "results": results,
        }

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

        print("=" * 60)
        print(f"  Completado: {output['metadata']['successful']}/{len(QUESTIONS)} exitosas")
        print(f"  Resultados guardados en: {OUTPUT_FILE}")
        print("=" * 60)


if __name__ == "__main__":
    run_benchmark()
