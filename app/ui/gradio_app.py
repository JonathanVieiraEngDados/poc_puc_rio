"""
README (short)
---------------
Run:
  python -m app.ui.gradio_app

Env vars required:
  - OPENAI_API_KEY

Streaming:
  - This UI calls agent.ask() which returns the full response. If streaming is desired later,
    a LangChain callback handler can be plugged without changing business logic.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple

import gradio as gr
from dotenv import load_dotenv

# Pydantic v2 compatibility: ensure ChatOpenAI models are rebuilt before use
try:
    from langchain_core.caches import BaseCache  # noqa: F401  (required before model_rebuild)
    from langchain_core.callbacks import Callbacks  # noqa: F401
    from langchain_openai import ChatOpenAI  # type: ignore
    try:
        ChatOpenAI.model_rebuild()
    except Exception:
        pass
except Exception:
    ChatOpenAI = None  # not needed directly; agent will import it

try:
    # Robust import of RULES
    from app.config.rules import RULES  # preferred path
except Exception:
    try:
        from config.rules import RULES  # fallback if run from app/
    except Exception:
        RULES = "You are a logistics assistant. Use only the provided dataset and tools."

try:
    from app.agent.logistics_agent import LogisticsAgent
except Exception:  # fallback when running in different cwd
    from agent.logistics_agent import LogisticsAgent


# Repo root = parent of the `app` package (app/ui/gradio_app.py -> app/ui -> app -> repo root)
BASE_DIR = Path(__file__).resolve().parents[2]
# Allow overriding the dataset via env var; default to the bundled sample dataset.
CSV_PATH = os.getenv("DATASET_CSV", str(BASE_DIR / "data" / "TestPuc-Rio.csv"))


def _format_history_text(history: List[Tuple[str, str]], last_user: str) -> str:
    """Optionally compact recent turns for more context; keep simple to avoid changing logic."""
    # We won't alter agent rules, just provide minimal context if desired.
    # Keep short to avoid bloating prompt.
    turns = []
    for u, a in history[-3:]:
        if u:
            turns.append(f"User: {u}")
        if a:
            turns.append(f"Assistant: {a}")
    turns.append(last_user)
    return "\n".join(turns)


def build_agent() -> LogisticsAgent:
    # Ensure environment variables are loaded (supports both repo root and parent of app/)
    # 1) default .env search
    load_dotenv()
    # 2) explicit paths as fallback
    try:
        this_dir = os.path.dirname(__file__)
        repo_root_env = os.path.normpath(os.path.join(this_dir, "..", "..", ".env"))
        app_parent_env = os.path.normpath(os.path.join(this_dir, "..", ".env"))
        if os.path.isfile(repo_root_env):
            load_dotenv(dotenv_path=repo_root_env, override=False)
        if os.path.isfile(app_parent_env):
            load_dotenv(dotenv_path=app_parent_env, override=False)
    except Exception:
        pass

    # LLM config is inside the agent per project requirements
    agent = LogisticsAgent(
        csv_path=CSV_PATH,
        rules=RULES,
        model="gpt-4o-mini",
        temperature=0.0,
        verbose=True,
    )
    return agent


def respond(user_message: str, history: List[Tuple[str, str]], agent: LogisticsAgent):
    if not user_message:
        return history

    # Append user turn with empty assistant reply first
    history = history + [(user_message, "")]

    try:
        # Pass only the current user message to avoid confusing the agent's tool selection
        answer = agent.ask(user_message)
        history[-1] = (history[-1][0], answer)
    except Exception as e:
        # Show a concise error; avoid stacktrace in UI
        history[-1] = (history[-1][0], f"[Erro ao processar a solicitação] {e}")

    return history


def clear_chat():
    return []


def main():
    agent = build_agent()

    with gr.Blocks(title="📦 Logistics AI Agent") as demo:
        gr.Markdown("""
        # 📦 Logistics AI Agent
        Converse com o assistente logístico usando o dataset carregado.
        """
        )

        chatbot = gr.Chatbot(label="Assistente de Logística")
        with gr.Row():
            msg = gr.Textbox(
                placeholder="Digite sua pergunta (Ex: Qual a taxa de ENTREGA?)",
                show_label=False,
                scale=4,
            )
        with gr.Row():
            submit_btn = gr.Button("Enviar", variant="primary")
            clear_btn = gr.Button("Limpar Conversa")

        examples = gr.Examples(
            examples=[
                "Qual a taxa de entrega do Cliente IL257 - JA?",
                "Qual a taxa da transportadora 189720 da rota jundiai - Sao Paulo Associado ao Evento DIARIA - CARRET?",
                "Qual os Top 5 Ofensores associados ao Evento ENTREGA?",
            ],
            inputs=msg,
        )

        def on_submit(user_input, chat_state):
            updated = respond(user_input, chat_state or [], agent)
            return gr.update(value=""), updated

        submit_btn.click(
            on_submit,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
        )
        msg.submit(
            on_submit,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
        )

        clear_btn.click(lambda: clear_chat(), inputs=None, outputs=chatbot)

    # Local-friendly defaults. Override via env vars when a public link is needed.
    share = os.getenv("GRADIO_SHARE", "false").lower() in ("1", "true", "yes")
    demo.launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
        share=share,
    )


if __name__ == "__main__":
    main()


