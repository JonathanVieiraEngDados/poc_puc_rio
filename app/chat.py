"""
Interface de TERMINAL do chatbot de logística (RAG).

Fluxo de cada pergunta:
  1) Tenta responder via TOOLS analíticas sobre o CSV (reaproveitando as tools).
  2) Caso não case com nenhuma intenção analítica, usa o pipeline RAG
     (FAISS + flan-t5-base) sobre o corpus .txt.

O histórico de perguntas e respostas é salvo em
``data/history/qa_history.jsonl`` (bônus do trabalho).

Uso:
    python -m app.chat
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from app.dataPrep.dataset_repository import DatasetRepository
from app.rag.tools_router import try_analytical

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = os.getenv("DATASET_CSV", str(BASE_DIR / "data" / "TestPuc-Rio.csv"))
HISTORY_PATH = BASE_DIR / "data" / "history" / "qa_history.jsonl"

EXIT_WORDS = {"sair", "exit", "quit", "q", ""}


def save_history(question: str, answer: str, source: str) -> None:
    """Acrescenta a interação ao histórico (uma linha JSON por pergunta)."""
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "question": question,
        "answer": answer,
        "source": source,
    }
    with HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    print("Carregando dataset... (a 1ª execução do RAG baixa os modelos da Hugging Face)")
    repo = DatasetRepository(CSV_PATH)
    repo.load()

    pipeline = None  # carregado sob demanda (os modelos são pesados)

    print("\n=== Chatbot de Logística (RAG + tools) ===")
    print("Digite sua pergunta. Para sair: 'sair'.\n")
    print("Exemplos:")
    print("  - O que significa o evento ENTREGA?               (RAG)")
    print("  - Como a taxa de frete R$/KG é calculada?          (RAG)")
    print("  - Qual a diferença entre ZVPA e ZTPA?              (RAG)")
    print("  - Quais os Top 5 ofensores do evento ENTREGA?      (tools)")
    print("  - Qual a taxa de ENTREGA do cliente IL257 - JA?    (tools)\n")

    while True:
        try:
            question = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo!")
            break

        if question.lower() in EXIT_WORDS:
            print("Até logo!")
            break

        # 1) Caminho analítico (tools sobre o CSV)
        answer = try_analytical(question, repo)
        source = "tools(csv)"

        # 2) Fallback: pipeline RAG sobre o corpus
        if answer is None:
            if pipeline is None:
                print("(carregando pipeline RAG pela primeira vez — pode demorar)...")
                from app.rag.pipeline import RagPipeline

                pipeline = RagPipeline()
            result = pipeline.ask(question)
            answer = result["answer"]
            source = "rag(" + ", ".join(result["sources"]) + ")"

        print(f"Bot: {answer}")
        print(f"     [fonte: {source}]\n")
        save_history(question, answer, source)


if __name__ == "__main__":
    main()
