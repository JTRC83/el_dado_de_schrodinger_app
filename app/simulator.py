# app/simulator.py
from __future__ import annotations

from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd

from app.generator import generate_block

# Patrones que en Euromillones dan premio (aprox)
PRIZE_PATTERNS = {
    (5, 2), (5, 1), (5, 0),
    (4, 2), (4, 1), (4, 0),
    (3, 2), (3, 1), (3, 0),
    (2, 2), (2, 1),
    (1, 2),
}


def _summary_from_dist(dist: pd.DataFrame) -> Dict[str, Any]:
    """A partir de la distribución de aciertos calcula métricas agregadas."""
    if dist.empty:
        return {
            "total_lines": 0,
            "p_ge3_nums": 0.0,
            "p_any_prize": 0.0,
        }

    total = float(dist["veces"].sum())

    # P(≥ 3 números), independientemente de estrellas
    mask_ge3 = dist["aciertos_numeros"] >= 3
    p_ge3_nums = dist.loc[mask_ge3, "veces"].sum() / total

    # P(al menos un premio) según tabla de patrones
    mask_prize = dist.apply(
        lambda r: (int(r["aciertos_numeros"]), int(r["aciertos_estrellas"])) in PRIZE_PATTERNS,
        axis=1,
    )
    p_any_prize = dist.loc[mask_prize, "veces"].sum() / total

    return {
        "total_lines": int(total),
        "p_ge3_nums": float(p_ge3_nums),
        "p_any_prize": float(p_any_prize),
    }


def simulate_strategy(
    mode: str,
    df_hist: pd.DataFrame,
    n_trials: int = 1000,
    lines_A: int = 5,
    lines_B: int = 5,
    lines_C: int = 5,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Simula muchos sorteos hipotéticos con un modo dado.

    Devuelve:
      - dist_df: distribución de (aciertos_numeros, aciertos_estrellas)
      - summary: métricas agregadas (P(≥3 números), P(al menos premio), etc.)
    """
    if df_hist.empty:
        empty = pd.DataFrame(
            columns=["aciertos_numeros", "aciertos_estrellas", "veces", "prob", "prob_%"]
        )
        return empty, _summary_from_dist(empty)

    df_sorted = df_hist.sort_values("date")
    draws = df_sorted[["n1", "n2", "n3", "n4", "n5", "s1", "s2"]].to_numpy()
    n_draws = len(draws)

    results = []

    for _ in range(int(n_trials)):
        # Elegimos un sorteo real al azar como "oficial"
        idx = np.random.randint(0, n_draws)
        row = draws[idx]
        nums_draw = set(row[:5])
        stars_draw = set(row[5:])

        # Generamos un bloque A/B/C con el modo elegido
        block = generate_block(
            mode=mode,
            df_hist=df_hist,
            lines_A=lines_A,
            lines_B=lines_B,
            lines_C=lines_C,
        )

        for line in block:
            nums = set(line["nums"])
            stars = set(line["stars"])
            hits_nums = len(nums & nums_draw)
            hits_stars = len(stars & stars_draw)
            results.append(
                {
                    "aciertos_numeros": hits_nums,
                    "aciertos_estrellas": hits_stars,
                }
            )

    if not results:
        empty = pd.DataFrame(
            columns=["aciertos_numeros", "aciertos_estrellas", "veces", "prob", "prob_%"]
        )
        return empty, _summary_from_dist(empty)

    df_res = pd.DataFrame(results)

    dist = (
        df_res.groupby(["aciertos_numeros", "aciertos_estrellas"])
        .size()
        .reset_index(name="veces")
        .sort_values(["aciertos_numeros", "aciertos_estrellas"])
        .reset_index(drop=True)
    )

    total_lines = float(df_res.shape[0])
    dist["prob"] = dist["veces"] / total_lines
    dist["prob_%"] = dist["prob"] * 100

    summary = _summary_from_dist(dist)
    return dist, summary