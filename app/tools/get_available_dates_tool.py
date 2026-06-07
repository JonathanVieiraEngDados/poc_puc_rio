import pandas as pd


class GetAvailableDatesTool:
    """
    Tool orientada a objetos que retorna as datas disponíveis no dataset.
    Mantém a assinatura e comportamento originais.
    """

    def __init__(self, repo):
        self.repo = repo

    def run(self, date_col: str = "Data Emissão", fmt: str = "%Y-%m-%d") -> dict:
        """
        Retorna {'availableDates': [YYYY-MM-DD, ...]} ordenadas.
        """

        df = self.repo.get().copy()

        if date_col not in df.columns:
            return {"error": f"Coluna '{date_col}' não encontrada no dataset."}

        ser = pd.to_datetime(df[date_col], errors="coerce")
        valid = ser.dropna().sort_values().dt.normalize().drop_duplicates()

        return {"availableDates": [d.strftime(fmt) for d in valid]}