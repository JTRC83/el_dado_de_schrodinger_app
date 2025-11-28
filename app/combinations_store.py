from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

import pandas as pd

COMBOS_PATH = Path(__file__).resolve().parents[1] / "data" / "combinaciones_generadas.csv"


def save_block(
    block: List[Dict[str, Any]],
    mode: str,
    note: str | None = None,
) -> int:
    ...
    # (tu código de save_block tal cual lo tenías)
    ...


def load_last_n(n: int = 50) -> pd.DataFrame:
    """
    Devuelve un DataFrame con las últimas n combinaciones guardadas.
    """
    if not COMBOS_PATH.exists():
        cols = [
            "timestamp",
            "block_id",
            "mode",
            "serie",
            "n1",
            "n2",
            "n3",
            "n4",
            "n5",
            "s1",
            "s2",
            "sum_nums",
            "note",
        ]
        return pd.DataFrame(columns=cols)

    df = pd.read_csv(COMBOS_PATH)
    if "timestamp" in df.columns:
        df = df.sort_values("timestamp")

    return df.tail(n).reset_index(drop=True)