"""
Etapa 1 do pipeline RAG: INDEXAÇÃO.

Lê o corpus de arquivos .txt em ``data/corpus/``, divide o texto em trechos
(chunks), gera embeddings com ``sentence-transformers/all-MiniLM-L6-v2`` e
constrói um índice vetorial **FAISS** persistido em ``data/faiss_index/``.

Tudo roda localmente / com modelos gratuitos da Hugging Face — sem APIs pagas.

Uso (gera/recria o índice):
    python -m app.rag.indexer
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_core.documents import Document

BASE_DIR = Path(__file__).resolve().parents[2]
CORPUS_DIR = BASE_DIR / "data" / "corpus"
INDEX_DIR = BASE_DIR / "data" / "faiss_index"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_corpus(corpus_dir: Path = CORPUS_DIR) -> List[Document]:
    """Carrega todos os arquivos .txt do corpus como Documents (um por arquivo)."""
    paths = sorted(corpus_dir.glob("*.txt"))
    if not paths:
        raise FileNotFoundError(f"Nenhum arquivo .txt encontrado em {corpus_dir}")
    return [
        Document(page_content=p.read_text(encoding="utf-8"), metadata={"source": p.name})
        for p in paths
    ]


def split_documents(
    docs: List[Document], chunk_size: int = 500, chunk_overlap: int = 80
) -> List[Document]:
    """Divide os documentos em trechos para recuperação mais granular."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(docs)


def build_embeddings():
    """Cria o modelo de embeddings (all-MiniLM-L6-v2, Hugging Face)."""
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def build_index(
    corpus_dir: Path = CORPUS_DIR,
    index_dir: Path = INDEX_DIR,
    embeddings=None,
):
    """Constrói o índice FAISS a partir do corpus e o salva em disco."""
    from langchain_community.vectorstores import FAISS

    docs = load_corpus(corpus_dir)
    chunks = split_documents(docs)
    if embeddings is None:
        embeddings = build_embeddings()

    vectorstore = FAISS.from_documents(chunks, embeddings)
    index_dir.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(index_dir))
    return vectorstore, len(chunks)


def main() -> None:
    print(f"Lendo corpus de {CORPUS_DIR} ...")
    _, n_chunks = build_index()
    print(f"Índice FAISS criado com {n_chunks} trechos em {INDEX_DIR}")


if __name__ == "__main__":
    main()
