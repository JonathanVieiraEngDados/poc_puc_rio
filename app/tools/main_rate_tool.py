import re
import unicodedata
import pandas as pd


class MainRateTool:
    """
    Calcula la tasa R$/KG para un evento logístico,
    usando el peso total de ENTREGA como denominador.
    Mantiene la lógica original, solo estructurada en POO.
    """

    def __init__(self, repo):
        self.repo = repo

    def _sum_entrega_weight(
        self,
        dff: pd.DataFrame,
        weight_col: str = "Qt Peso Líquido (kg)",
        entrega_label: str = "ENTREGA",
    ) -> float:
        """Suma el peso total (kg) para los eventos de tipo ENTREGA."""
        denom = dff.loc[dff["Evento"] == entrega_label, weight_col].sum()
        return float(denom)

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
        """Crea columnas normalizadas si no existen (origen/destino)."""
        if "_origem_norm" not in dff.columns:
            dff["_origem_norm"] = dff["Cidade Emitente"].map(self._norm_text)
        if "_destino_norm" not in dff.columns:
            dff["_destino_norm"] = dff["Cidade"].map(self._norm_text)
        if "_tipoop_norm" not in dff.columns:
            dff["_tipoop_norm"] = dff["Tipo de Operação"].map(self._norm_text)
        return dff

    def run(
        self,
        evento: str,
        cliente: str | None = None,
        origem: str | None = None,
        destino: str | None = None,
        tipo_operacao: list[str] | None = None,
        carrier: list[int] | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        value_col: str = "Vr Frete Contab Prev",
        weight_col: str = "Qt Peso Líquido (kg)",
        entrega_label: str = "ENTREGA",
    ) -> float | str:
        """
        Calcula la tasa R$/KG para `evento`, usando denominador = peso total de `ENTREGA`.
        Filtros opcionales:
          - cliente (igualdad exacta)
          - origem/destino: coincidencia parcial
          - tipo_operacao: contains (ZVPA, ZTPA, etc.)
          - carrier: .isin(lista)
          - date_start/date_end: rango inclusivo
        """

        df = self.repo.get().copy()
        dff = self._ensure_norm_cols(df)

        # Convertir numéricos
        dff[value_col] = pd.to_numeric(dff[value_col], errors="coerce")
        dff[weight_col] = pd.to_numeric(dff[weight_col], errors="coerce")

        # --- filtros opcionales ---
        if cliente:
            dff = dff[dff["CLIENTE"] == cliente]

        if origem:
            origem_pat = re.escape(self._norm_text(origem))
            dff = dff[
                dff["_origem_norm"].str.contains(origem_pat, case=False, na=False)
            ]

        if destino:
            destino_pat = re.escape(self._norm_text(destino))
            dff = dff[
                dff["_destino_norm"].str.contains(destino_pat, case=False, na=False)
            ]

        if tipo_operacao:
            regex = "|".join(map(str, tipo_operacao))
            dff = dff[
                dff["Tipo de Operação"]
                .astype(str)
                .str.contains(regex, case=False, na=False)
            ]

        if carrier:
            dff = dff[dff["Cod. Transportadora"].isin(carrier)]

        if date_start or date_end:
            ser = pd.to_datetime(dff["Data Emissão"], errors="coerce")
            start = (
                pd.to_datetime(date_start, errors="coerce") if date_start else ser.min()
            )
            end = pd.to_datetime(date_end, errors="coerce") if date_end else ser.max()
            dff = dff[(ser >= start) & (ser <= end)]

        # --- cálculo ---
        evento_pattern = str(evento).strip()
        numer = dff.loc[
            dff["Evento"].astype(str).str.contains(
                evento_pattern, case=False, na=False
            ),
            value_col,
        ].sum()
        denom = self._sum_entrega_weight(dff, weight_col, entrega_label)

        if denom <= 0:
            return "ERROR: ENTREGA net weight is zero/missing. Cannot compute rate."

        return float(numer / denom)