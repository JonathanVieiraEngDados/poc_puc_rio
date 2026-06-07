"""
Roteador analítico — reaproveita as TOOLS de logística (sobre o CSV) para
responder perguntas numéricas/objetivas antes de recorrer ao RAG.

São funções Python puras (pandas), sem nenhuma API paga. Quando a pergunta não
casa com nenhuma intenção analítica, ``try_analytical`` retorna ``None`` e o
chatbot cai no pipeline RAG.

Intenções reconhecidas:
  - "datas disponíveis"            -> GetAvailableDatesTool
  - "top N ofensores [evento]"     -> TopOffendersTool
  - "taxa / rate / R$/KG"          -> MainRateTool (+ ParseRouteTool)
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from app.tools import (
    GetAvailableDatesTool,
    MainRateTool,
    ParseRouteTool,
    TopOffendersTool,
)

# Rótulos de evento conhecidos, dos mais específicos para os mais genéricos.
EVENT_LABELS = ["DIARIA - CARRET", "REENTREGA", "DESCARGA", "ENTREGA", "DIARIA"]


def _norm(text: str) -> str:
    """Minúsculas, sem acentos."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower()


def _detect_event(question_upper: str) -> Optional[str]:
    for label in EVENT_LABELS:
        if label in question_upper:
            return label
    return None


def _extract_client(question: str) -> Optional[str]:
    # Ex.: "IL257 - JA" -> normaliza para "IL257 - JA"
    m = re.search(r"([A-Z]{2}\d{3})\s*-\s*([A-Z]{2})", question.upper())
    return f"{m.group(1)} - {m.group(2)}" if m else None


def _extract_carrier(norm_question: str) -> Optional[int]:
    m = re.search(r"transportadora\s+(\d+)", norm_question)
    return int(m.group(1)) if m else None


def _extract_route(question: str) -> Optional[str]:
    ql = question.lower()
    if "rota" in ql:
        after = question[ql.index("rota") + len("rota"):]
        # Corta no conector que indica o fim da rota (ex.: "associado ao evento ...").
        after = re.split(r"associad|do evento|ao evento|\bevento\b", after, flags=re.IGNORECASE)[0]
        after = after.strip(" :")
        return after or None
    m = re.search(r"\bde\s+(.+?\s+para\s+.+?)(?:[.,?]|$)", question, flags=re.IGNORECASE)
    return m.group(1) if m else None


def try_analytical(question: str, repo) -> Optional[str]:
    """Tenta responder com as tools; retorna None se nenhuma intenção casar."""
    q = question.strip()
    n = _norm(q)
    qu = q.upper()

    # 1) Datas disponíveis
    if "datas disponiveis" in n or "available dates" in n or "quais datas" in n:
        dates = GetAvailableDatesTool(repo).run().get("availableDates", [])
        return ("Datas disponíveis no dataset: " + ", ".join(dates)) if dates else None

    # 2) Top ofensores
    if "ofensor" in n:
        m = re.search(r"top\s+(\d+)", n)
        top_n = int(m.group(1)) if m else 5
        evento = _detect_event(qu) or "ENTREGA"
        rows = TopOffendersTool(repo).run(evento=evento, top_n=top_n)
        if not rows:
            return None
        linhas = [f"  {i+1}. {r['Categoria']}: R$ {float(r['Custo']):,.2f}" for i, r in enumerate(rows)]
        return f"Top {top_n} ofensores (evento {evento}):\n" + "\n".join(linhas)

    # 3) Taxa R$/KG
    if "taxa" in n or "rate" in n or "r$/kg" in n or "r$ /kg" in n:
        evento = _detect_event(qu) or "ENTREGA"
        cliente = _extract_client(q)
        carrier = _extract_carrier(n)
        origem = destino = None
        rota = _extract_route(q)
        if rota:
            try:
                parsed = ParseRouteTool().run(rota)
                origem, destino = parsed["origem"], parsed["destino"]
            except Exception:
                pass
        try:
            rate = MainRateTool(repo).run(
                evento=evento,
                cliente=cliente,
                origem=origem,
                destino=destino,
                carrier=[carrier] if carrier else None,
            )
        except Exception:
            return None
        if isinstance(rate, str):  # mensagem de erro da tool (ex.: denominador zero)
            return rate
        filtros = []
        if cliente:
            filtros.append(f"cliente={cliente}")
        if origem:
            filtros.append(f"rota={origem} -> {destino}")
        if carrier:
            filtros.append(f"transportadora={carrier}")
        contexto = f" [{', '.join(filtros)}]" if filtros else ""
        return f"Taxa do evento {evento}{contexto}: {rate:.4f} R$/KG"

    return None
