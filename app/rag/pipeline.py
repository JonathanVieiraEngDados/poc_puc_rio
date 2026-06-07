"""
Pipeline RAG com LangChain (etapas 2 e 3).

- Etapa 2 (RECUPERAÇÃO): índice FAISS + embeddings all-MiniLM-L6-v2 buscam os
  trechos mais relevantes do corpus para a pergunta.
- Etapa 3 (GERAÇÃO): o modelo ``google/flan-t5-base`` (Hugging Face, gratuito,
  roda localmente) gera a resposta usando apenas os trechos recuperados.

A orquestração usa as chains do LangChain (``create_retrieval_chain`` +
``create_stuff_documents_chain``). Nenhuma API paga é utilizada.
"""

from __future__ import annotations

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate

from app.rag.indexer import INDEX_DIR, build_embeddings, build_index

LLM_MODEL = "google/flan-t5-base"

PROMPT = PromptTemplate.from_template(
    "Você é um assistente de logística. Responda à pergunta em português, "
    "usando APENAS o contexto fornecido. Se a resposta não estiver no contexto, "
    "responda que não encontrou a informação no material disponível.\n\n"
    "Contexto:\n{context}\n\n"
    "Pergunta: {input}\n"
    "Resposta:"
)


class RagPipeline:
    """Carrega embeddings, índice FAISS e o LLM, e responde via RAG."""

    def __init__(self, k: int = 4, max_new_tokens: int = 256):
        self.embeddings = build_embeddings()
        self.vectorstore = self._load_or_build_index()
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
        self.llm = self._build_llm(max_new_tokens)

        combine_chain = create_stuff_documents_chain(self.llm, PROMPT)
        self.chain = create_retrieval_chain(self.retriever, combine_chain)

    def _load_or_build_index(self):
        from langchain_community.vectorstores import FAISS

        if (INDEX_DIR / "index.faiss").exists():
            return FAISS.load_local(
                str(INDEX_DIR),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
        # Índice ainda não existe: cria reaproveitando os embeddings já carregados.
        vectorstore, _ = build_index(embeddings=self.embeddings)
        return vectorstore

    def _build_llm(self, max_new_tokens: int):
        from langchain_huggingface import HuggingFacePipeline

        return HuggingFacePipeline.from_model_id(
            model_id=LLM_MODEL,
            task="text2text-generation",
            pipeline_kwargs={"max_new_tokens": max_new_tokens},
        )

    def ask(self, question: str) -> dict:
        """Retorna {'answer': str, 'sources': [arquivos do corpus usados]}."""
        result = self.chain.invoke({"input": question})
        sources = [d.metadata.get("source", "?") for d in result.get("context", [])]
        return {"answer": str(result["answer"]).strip(), "sources": sorted(set(sources))}
