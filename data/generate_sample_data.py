"""
Generate a small, deterministic sample dataset for the Logistics AI Agent.

The schema mirrors the columns documented in app/config/rules.py. Numeric
columns use plain integers so they survive the cleaning logic in
app/dataPrep/dataset_repository.py (which is tuned for pt-BR number formatting).

Run:
    python data/generate_sample_data.py

Output:
    data/TestPuc-Rio.csv
"""

from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

OUTPUT = Path(__file__).resolve().parent / "TestPuc-Rio.csv"

# (origem, UF origem, destino, UF destino, código itinerário)
ROUTES = [
    ("Jundiai", "SP", "Sao Paulo", "SP", "JUN-SAO"),
    ("Campinas", "SP", "Rio de Janeiro", "RJ", "CAM-RIO"),
    ("Sao Paulo", "SP", "Belo Horizonte", "MG", "SAO-BHZ"),
]

CLIENTS = ["IL257 - JA", "IL255 - JA", "AB100 - SP", "CD200 - RJ"]
CARRIERS = [189720, 200111, 305522]
EVENTS = ["ENTREGA", "DIARIA - CARRET", "DESCARGA", "REENTREGA"]
OPERATIONS = ["ZVPA", "ZTPA"]
DATES = ["2025-01-15", "2025-01-28", "2025-02-10", "2025-02-22", "2025-03-05"]

CARGA = "PALETIZADA"
FRETE = "FOB"
MEIO = "RODOVIARIO"
VEICULO = "TRUCK"


def build_rows() -> list[dict]:
    rng = random.Random(42)
    rows: list[dict] = []
    date_idx = 0

    for origem, uf_o, destino, uf_d, itin in ROUTES:
        for cliente in CLIENTS:
            for carrier in CARRIERS:
                for evento in EVENTS:
                    # ENTREGA carries the bulk of the net weight (it is the rate denominator).
                    if evento == "ENTREGA":
                        peso = rng.randint(800, 3000)
                        frete = rng.randint(1500, 5000)
                    else:
                        peso = rng.randint(50, 400)
                        frete = rng.randint(200, 1800)

                    date = DATES[date_idx % len(DATES)]
                    date_idx += 1

                    rows.append(
                        {
                            "Evento": evento,
                            "Qt Peso Líquido (kg)": peso,
                            "Vr Frete Contab Prev": frete,
                            "Vr Frete a pagar": frete + rng.randint(0, 200),
                            "Cidade Emitente": origem,
                            "Cidade": destino,
                            "UF Emitente": uf_o,
                            "UF": uf_d,
                            "Código Itinerário": itin,
                            "CLIENTE": cliente,
                            "Cod. Transportadora": carrier,
                            "Tipo de Operação": rng.choice(OPERATIONS),
                            "Data Emissão": date,
                            "Tipo de Carga": CARGA,
                            "Tipo de Frete": FRETE,
                            "Meio de Transporte": MEIO,
                            "Tipo de Veículo Principal": VEICULO,
                        }
                    )
    return rows


def main() -> None:
    df = pd.DataFrame(build_rows())
    df.to_csv(OUTPUT, index=False, encoding="utf-8")
    print(f"Wrote {len(df)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
