# app/simulator.py
from __future__ import annotations

from typing import Dict, Any
import numpy as np
import pandas as pd

from app.generator import generate_block


def simulate_strategy(
    mode: str,
    df_hist: pd.DataFrame,
    lines_A: int,
    lines_B: int,
    lines_C: int,
    n_trials: int = 1000,
    seed: int | None = None,
) -> pd.DataFrame:
    """
    Simula n_trials sorteos de Euromillones para un modo dado (Estándar, Momentum,
    Rareza, Experimental), usando tu generador real (generate_block).

    Para cada simulación:
      - genera un bloque A/B/C con las líneas indicadas
      - genera un sorteo "real" aleatorio (5 números, 2 estrellas)
      - calcula aciertos (números y estrellas) de cada línea

    Devuelve un DataFrame de resumen:
      hits_n (aciertos números), hits_s (aciertos estrellas),
      count (veces que aparece ese patrón),
      prob (aprox. probabilidad relativa).
    """
    rng = np.random.default_rng(seed)
    records: list[Dict[str, Any]] = []

    total_lines_por_trial = lines_A + lines_B + lines_C
    if total_lines_por_trial <= 0:
        return pd.DataFrame(columns=["hits_n", "hits_s", "count", "prob"])

    for _ in range(n_trials):
        # 1) bloque generado por tu lógica real
        block = generate_block(
            mode=mode,
            df_hist=df_hist,
            lines_A=lines_A,
            lines_B=lines_B,
            lines_C=lines_C,
        )

        # 2) sorteo aleatorio "real"
        draw_nums = rng.choice(np.arange(1, 51), size=5, replace=False)
        draw_stars = rng.choice(np.arange(1, 13), size=2, replace=False)

        set_draw_nums = set(int(x) for x in draw_nums)
        set_draw_stars = set(int(x) for x in draw_stars)

        # 3) aciertos por línea
        for line in block:
            nums = set(line["nums"])
            stars = set(line["stars"])
            hits_n = len(nums & set_draw_nums)
            hits_s = len(stars & set_draw_stars)
            records.append(
                {
                    "hits_n": hits_n,
                    "hits_s": hits_s,
                }
            )

    if not records:
        return pd.DataFrame(columns=["hits_n", "hits_s", "count", "prob"])

    df = pd.DataFrame(records)
    summary = (
        df.groupby(["hits_n", "hits_s"])
        .size()
        .reset_index(name="count")
        .sort_values(["hits_n", "hits_s"], ascending=[False, False])
    )

    total_lines_simuladas = len(df)
    summary["prob"] = summary["count"] / total_lines_simuladas

    return summary