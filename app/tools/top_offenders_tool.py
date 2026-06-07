import pandas as pd


class TopOffendersTool:
    """
    Calcula os Top N ofensores (clientes, transportadoras, etc.)
    de custo logístico com base em Vr Frete Contab Prev.
    Mantém a estrutura e comportamento originais.
    """

    def __init__(self, repo):
        self.repo = repo

    def run(
        self,
        evento: str = "ENTREGA",
        custoTotal: bool = False,
        group_by: list[str] | str = "CLIENTE",
        tipo_operacao: list[str] | None = None,
        carrier: list[int] | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        top_n: int = 5,
        value_col: str = "Vr Frete Contab Prev",
    ) -> dict:
        """
        Retorna os Top N ofensores (clientes, transportadoras, etc.) de custo logístico
        com base no campo `Vr Frete Contab Prev`.

        Parâmetros:
        ----------
        - evento: Tipo de evento (ex: 'DIARIA - CARRET', 'REENTREGA', etc.)
        - group_by: Coluna(s) pela(s) qual(is) agrupar. Pode ser string única ou lista de strings
                   (ex: 'CLIENTE', ['CLIENTE', 'Cidade'], ['Cod. Transportadora', 'Cidade Emitente'])
        - tipo_operacao: Lista de tipos de operação (ZVPA, ZTPA, etc.)
        - carrier: Lista de códigos de transportadora
        - date_start, date_end: Filtro de intervalo de datas (Data Emissão)
        - top_n: Número de ofensores a retornar
        - value_col: Coluna de custo a somar (padrão = Vr Frete Contab Prev)
        """

        dff = self.repo.get().copy()

        # --- filtros básicos ---
        if not custoTotal:
            dff = dff[
                dff["Evento"].astype(str).str.contains(evento, case=False, na=False)
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

        # --- normalizar group_by para lista ---
        if isinstance(group_by, str):
            group_by_list = [group_by]
        else:
            group_by_list = group_by

        # --- cálculo principal ---
        grouped = (
            dff.groupby(group_by_list)[value_col]
            .sum()
            .sort_values(ascending=False)
            .head(top_n)
        )

        # --- formata o retorno para exibição legível ---
        result = grouped.reset_index()
        
        # Rename columns for better readability
        if len(group_by_list) == 1:
            # Single grouping: rename to "Categoria"
            result = result.rename(columns={group_by_list[0]: "Categoria", value_col: "Custo"})
        else:
            # Multiple grouping: keep original column names, rename value column
            result = result.rename(columns={value_col: "Custo"})

        return result.to_dict(orient="records")