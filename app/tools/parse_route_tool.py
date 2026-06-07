import re
import unicodedata
import pandas as pd


class ParseRouteTool:
    """
    Tool responsável por extrair origem e destino de um texto de rota.
    Mantém a lógica e formato originais.
    """

    def __init__(self):
        pass

    def _norm_text(self, s: str) -> str:
        """Mayúsculas, sin acentos, sin dobles espacios."""
        if s is None:
            return ""
        s = str(s).strip()
        # elimina acentos
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        # mayúsculas + colapsar espacios
        s = re.sub(r"\s+", " ", s.upper())
        return s

    def _ensure_norm_cols(self, dff: pd.DataFrame) -> pd.DataFrame:
        """Crea columnas normalizadas si no existen (origen/destino/tipo_op)."""
        if "_origem_norm" not in dff.columns and "Cidade Emitente" in dff.columns:
            dff["_origem_norm"] = dff["Cidade Emitente"].map(self._norm_text)
        if "_destino_norm" not in dff.columns and "Cidade" in dff.columns:
            dff["_destino_norm"] = dff["Cidade"].map(self._norm_text)
        if "_tipoop_norm" not in dff.columns and "Tipo de Operação" in dff.columns:
            dff["_tipoop_norm"] = dff["Tipo de Operação"].map(self._norm_text)
        return dff

    def run(self, route_text: str) -> dict:
        """
        Extrae origen y destino desde texto libre de ruta.
        Ejemplos de entrada:
          "jundiaí - são paulo", "Jundiai -> Sao Paulo", "de Jundiaí para São Paulo"
        Devuelve:
          {'origem': 'JUNDIAI', 'destino': 'SAO PAULO'}
        """
        if not route_text or not isinstance(route_text, str):
            raise ValueError("route_text deve ser uma string não vazia.")

        txt = self._norm_text(route_text)

        # separadores y conectores comunes entre origen/destino
        parts = re.split(r"\s*(?:-|–|—|->|=>| A | PARA | TO )\s*", txt)
        parts = [p for p in parts if p]  # limpia vacíos

        if len(parts) >= 2:
            origem = parts[0]
            destino = parts[1]
        else:
            # fallback: intenta "DE X PARA Y"
            m = re.search(r"\bDE\s+(.+?)\s+(?:A|PARA|TO)\s+(.+)$", txt)
            if not m:
                raise ValueError("Formato de rota inválido. Use 'Origem - Destino'.")
            origem, destino = m.group(1), m.group(2)

        # quita posibles sufijos UF si el usuario los colocó (ej: " - SP")
        origem = re.sub(r"\s*-\s*[A-Z]{2}$", "", origem).strip()
        destino = re.sub(r"\s*-\s*[A-Z]{2}$", "", destino).strip()

        return {"origem": origem, "destino": destino}