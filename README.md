# PUC-Rio AI Chatbot

Assistente de análise logística com IA. Interface de chat em **Gradio** sobre um
agente **LangChain + OpenAI Functions** (`create_csv_agent`) que usa ferramentas
analíticas sobre um dataset local de eventos logísticos.

## Estrutura do projeto

```
poc_puc-rio-main/
├── app/
│   ├── agent/
│   │   └── logistics_agent.py        # Orquestra LLM + tools (create_csv_agent)
│   ├── config/
│   │   └── rules.py                  # Regras do agente (system prompt: RULES)
│   ├── dataPrep/
│   │   └── dataset_repository.py     # Carrega e trata o CSV
│   ├── tools/
│   │   ├── parse_route_tool.py       # Extrai origem/destino de texto livre
│   │   ├── main_rate_tool.py         # Calcula taxa R$/KG por evento
│   │   ├── top_offenders_tool.py     # Top N ofensores de custo
│   │   ├── get_available_dates_tool.py
│   │   └── math_operator_tools.py    # Operações matemáticas auxiliares
│   └── ui/
│       └── gradio_app.py             # Interface de chat (Gradio) — entry point
├── data/
│   ├── generate_sample_data.py       # Gera um dataset de exemplo
│   └── TestPuc-Rio.csv                   # Dataset (exemplo gerado / ou o seu real)
├── requirements.txt
├── .env.example
└── README.md
```

## Pré-requisitos

- Python **3.12** (ver `.python-version`)
- Uma chave de API da OpenAI

## Como executar

```bash
# 1) (recomendado) criar e ativar um ambiente virtual
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2) instalar as dependências
pip install -r requirements.txt

# 3) configurar a chave da OpenAI
cp .env.example .env
# edite .env e preencha OPENAI_API_KEY=sk-...

# 4) (opcional) gerar o dataset de exemplo, caso queira recriá-lo
python data/generate_sample_data.py

# 5) iniciar a interface
python -m app.ui.gradio_app
```

A UI abre em **http://127.0.0.1:7860**. Inclui histórico de conversa, exemplos de
perguntas e botões de Enviar/Limpar.

> Execute sempre a partir da **raiz do repositório** (`poc_puc-rio-main/`), pois o
> entry point usa o pacote `app` (`python -m app.ui.gradio_app`).

## Dados

Por padrão a aplicação usa o dataset de exemplo em `data/TestPuc-Rio.csv`, gerado por
`data/generate_sample_data.py` e já cobrindo os prompts de exemplo da UI. Para usar
o seu próprio CSV, defina a variável de ambiente `DATASET_CSV` (veja `.env.example`)
ou substitua o arquivo. O esquema esperado de colunas está documentado em
`app/config/rules.py` (Evento, Qt Peso Líquido (kg), Vr Frete Contab Prev, CLIENTE,
Cod. Transportadora, Cidade Emitente, Cidade, Data Emissão, etc.).

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `OPENAI_API_KEY` | — | **Obrigatória.** Chave da OpenAI. |
| `DATASET_CSV` | `data/TestPuc-Rio.csv` | Caminho do dataset. |
| `GRADIO_SERVER_NAME` | `127.0.0.1` | Use `0.0.0.0` para expor na rede local. |
| `GRADIO_SERVER_PORT` | `7860` | Porta da UI. |
| `GRADIO_SHARE` | `false` | `true` gera um link público temporário. |

## Exemplos de perguntas

- "Qual a taxa de entrega do Cliente IL257 - JA?"
- "Qual a taxa da transportadora 189720 da rota jundiai - Sao Paulo associado ao Evento DIARIA - CARRET?"
- "Quais os Top 5 ofensores associados ao Evento ENTREGA?"

## Notas técnicas

- O agente é construído com `langchain_openai.ChatOpenAI` + `create_csv_agent`
  (OpenAI Functions), com `extra_tools` para as funções analíticas.
- As regras do agente ficam em `app/config/rules.py` (`RULES`).
- Nenhuma informação sensível fica no repositório. Credenciais vão no `.env` local
  (que é ignorado pelo Git).
