# PUC-Rio AI Chatbot — Logística

Chatbot de **FAQ de logística** com **RAG (Retrieval-Augmented Generation)** usando
**LangChain + FAISS** e **modelos open-source gratuitos da Hugging Face**
(`sentence-transformers/all-MiniLM-L6-v2` para embeddings e `google/flan-t5-base`
para geração). **Não usa nenhuma API paga** — tudo roda localmente.

Para perguntas numéricas (taxa R$/KG, top ofensores, datas) o chatbot reaproveita
as **tools analíticas** sobre o dataset CSV; para perguntas conceituais/FAQ ele usa
o pipeline RAG sobre um corpus de documentos `.txt`.

> Há também uma interface Gradio legada que usa a API da OpenAI
> (`app/ui/gradio_app.py`) — **opcional** e fora do escopo dos requisitos (que
> proíbem APIs pagas). O entregável principal é o chatbot RAG (`app/chat.py`).

## Como os requisitos são atendidos

| Requisito | Onde |
|---|---|
| Corpus local de arquivos `.txt` | `data/corpus/*.txt` (conceitos, eventos, operações, glossário, FAQ) |
| RAG — Indexação com **FAISS** + `all-MiniLM-L6-v2` | `app/rag/indexer.py` |
| RAG — Recuperação dos trechos relevantes | `app/rag/pipeline.py` (FAISS retriever) |
| RAG — Geração com `flan-t5-base` (HF, gratuito) | `app/rag/pipeline.py` (`HuggingFacePipeline`) |
| Sem APIs pagas (só local / HF gratuito) | embeddings + LLM rodam localmente |
| Interface simples de terminal | `app/chat.py` (`python -m app.chat`) |
| **Bônus:** LangChain | `create_retrieval_chain` + `create_stuff_documents_chain` |
| **Bônus:** histórico de perguntas/respostas | salvo em `data/history/qa_history.jsonl` |
| Reaproveitamento das tools (domínio logística) | `app/rag/tools_router.py` + `app/tools/` |

## Estrutura do projeto

```
poc_puc-rio-main/
├── app/
│   ├── chat.py                       # >>> Chatbot RAG (interface de terminal) — entry point
│   ├── rag/
│   │   ├── indexer.py                # Indexação: corpus .txt -> embeddings -> FAISS
│   │   ├── pipeline.py               # Recuperação (FAISS) + Geração (flan-t5) com LangChain
│   │   └── tools_router.py           # Roteia perguntas numéricas para as tools (CSV)
│   ├── tools/                        # Tools analíticas (taxa, top ofensores, rota, datas, math)
│   ├── dataPrep/dataset_repository.py# Carrega e trata o CSV
│   ├── config/rules.py               # Regras de negócio do domínio
│   ├── agent/logistics_agent.py      # (legado) agente OpenAI sobre CSV
│   └── ui/gradio_app.py              # (legado/opcional) UI Gradio com OpenAI
├── data/
│   ├── corpus/*.txt                  # Corpus de conhecimento (base do RAG)
│   ├── TestPuc-Rio.csv               # Dataset tabular (usado pelas tools)
│   ├── generate_sample_data.py       # Gerador do dataset de exemplo
│   ├── faiss_index/                  # Índice FAISS gerado (ignorado no git)
│   └── history/qa_history.jsonl      # Histórico de Q&A (ignorado no git)
├── requirements.txt
└── README.md
```

## Pré-requisitos

- Python **3.12** (ver `.python-version`)
- Acesso à internet **na primeira execução** (para baixar os modelos gratuitos da
  Hugging Face; depois rodam offline a partir do cache local)

## Como executar (chatbot RAG)

```bash
# 1) ambiente virtual + dependências
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2) (opcional) construir o índice FAISS antecipadamente
#    Se você pular, o índice é criado automaticamente na 1ª pergunta de RAG.
python -m app.rag.indexer

# 3) iniciar o chatbot no terminal
python -m app.chat
```

Exemplos de perguntas:

- `O que significa o evento ENTREGA?` → **RAG**
- `Como a taxa de frete R$/KG é calculada?` → **RAG**
- `Qual a diferença entre ZVPA e ZTPA?` → **RAG**
- `Quais os Top 5 ofensores do evento ENTREGA?` → **tools (CSV)**
- `Qual a taxa de ENTREGA do cliente IL257 - JA?` → **tools (CSV)**

Digite `sair` para encerrar. Cada interação é gravada em
`data/history/qa_history.jsonl`.

> Execute sempre a partir da **raiz do repositório** (`poc_puc-rio-main/`), pois os
> entry points usam o pacote `app` (`python -m app.chat`).

## Como funciona o RAG

1. **Indexação** (`app/rag/indexer.py`): lê `data/corpus/*.txt`, divide em trechos
   com `RecursiveCharacterTextSplitter`, gera embeddings com
   `sentence-transformers/all-MiniLM-L6-v2` e salva um índice **FAISS** em
   `data/faiss_index/`.
2. **Recuperação** (`app/rag/pipeline.py`): a pergunta vira embedding e o FAISS
   retorna os `k` trechos mais similares.
3. **Geração** (`app/rag/pipeline.py`): `google/flan-t5-base` (via
   `HuggingFacePipeline`) responde usando **apenas** os trechos recuperados,
   orquestrado pelas chains do LangChain.

Para adicionar conhecimento, basta colocar novos `.txt` em `data/corpus/` e rodar
`python -m app.rag.indexer` de novo.

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `DATASET_CSV` | `data/TestPuc-Rio.csv` | Caminho do dataset usado pelas tools. |

(O chatbot RAG **não** precisa de nenhuma chave de API.)

## Interface Gradio legada (opcional, usa OpenAI — fora do escopo)

A versão original em `app/ui/gradio_app.py` usa a API paga da OpenAI e **não** é
necessária para os requisitos. Se quiser executá-la, defina `OPENAI_API_KEY` em um
`.env` (veja `.env.example`) e rode `python -m app.ui.gradio_app`.
