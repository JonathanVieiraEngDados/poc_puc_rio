import pandas as pd
from pathlib import Path
from math import nan

class DatasetRepository:
    """
    Classe responsável por carregar e tratar o dataset logístico.
    O tratamento converte colunas numéricas formatadas como texto para float
    e substitui valores ausentes pela média.
    """

    def __init__(self, csv_path: str):
        """
        Parameters
        ----------
        csv_path : str
            Caminho para o arquivo CSV original (ex: 'dataPrep/TestPuc-Rio.csv').
        """
        self.csv_path = Path(csv_path).resolve()
        self._df = None

    # -----------------------------
    # MÉTODOS PÚBLICOS
    # -----------------------------
    def load(self):
        """Carrega o dataset original, aplica tratamento e guarda em memória."""
        if self._df is None:
            df = pd.read_csv(self.csv_path, low_memory=False)
            df = self._treat_dataset(df)
            self._df = df
        return self._df

    def get(self):
        """Retorna o DataFrame já carregado e tratado."""
        if self._df is None:
            return self.load()
        return self._df

    # -----------------------------
    # MÉTODOS PRIVADOS
    # -----------------------------
    def _float_treat(self, df: pd.DataFrame, variable: str) -> pd.DataFrame:
        """Normaliza colunas numéricas escritas como texto."""
        if variable not in df.columns:
            return df

        df[variable] = (
            df[variable]
            .astype(str)
            .str.strip()
            .str.replace('.', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.replace('-', 'nan', regex=False)
        )
        df[variable] = pd.to_numeric(df[variable], errors='coerce')
        df[variable] = df[variable].fillna(df[variable].mean())

        return df

    def _treat_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aplica todas as transformações de limpeza conhecidas."""
        # Colunas principais que precisam de tratamento numérico
        numeric_cols = [
            "Qt Peso Líquido (kg)",
            "Vr Frete Contab Prev",
            "Vr Frete a pagar",
        ]

        # Tratamento das três colunas principais
        for col in numeric_cols:
            if col == "Vr Frete a pagar" and col in df.columns:
                df[col] = df[col].astype(str).str.replace("R$", "", regex=False)
            df = self._float_treat(df, col)

        return df