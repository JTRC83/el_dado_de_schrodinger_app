# app/combinations_store.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd

# Ruta al CSV de combinaciones generadas
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
STORE_PATH = DATA_DIR / "combinaciones_generadas.csv"

COLUMNS = [
    "id",
    "timestamp",
    "mode",
    "serie",
    "line_index",
    "numbers",
    "stars",
    "sum_numbers",
    "block_size",
]


def _ensure_store_exists() -> None:
    """Crea el CSV vacío si aún no existe."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        df_empty = pd.DataFrame(columns=COLUMNS)
        df_empty.to_csv(STORE_PATH, index=False)


def save_block(
    block: List[Dict[str, Any]],
    mode: str,
    block_size: Optional[int] = None,
    note: str | None = None,  # por compatibilidad aunque no lo usemos
) -> int:
    """
    Guarda un bloque de combinaciones en data/combinaciones_generadas.csv

    - block: lista de dicts con claves al menos:
        {"serie": "A"/"B"/"C", "nums": [..5 ints..], "stars": [..2 ints..]}
    - mode: texto del modo ("Estándar", "Momentum", "Mix A–E", etc.)
    - block_size: tamaño total del bloque (para guardar en la columna).
                  Si es None, se usa len(block).

    Devuelve: número de combinaciones añadidas.
    """
    _ensure_store_exists()

    # Leemos lo que ya hay
    df_old = pd.read_csv(STORE_PATH) if STORE_PATH.exists() else pd.DataFrame(columns=COLUMNS)

    # Calculamos el siguiente id
    if not df_old.empty and "id" in df_old.columns:
        next_id = int(pd.to_numeric(df_old["id"], errors="coerce").max()) + 1
    else:
        next_id = 1

    if block_size is None:
        block_size = len(block)

    now_iso = datetime.now().isoformat(timespec="microseconds")

    rows = []
    for idx, row in enumerate(block):
        nums = row.get("nums", [])
        stars = row.get("stars", [])
        serie = row.get("serie", "")

        nums_str = "-".join(str(int(n)) for n in nums)
        stars_str = "-".join(str(int(s)) for s in stars)
        sum_numbers = int(sum(nums)) if nums else None

        rows.append(
            {
                "id": next_id + idx,
                "timestamp": now_iso,
                "mode": mode,
                "serie": serie,
                "line_index": idx,
                "numbers": nums_str,
                "stars": stars_str,
                "sum_numbers": sum_numbers,
                "block_size": int(block_size),
            }
        )

    df_new = pd.DataFrame(rows, columns=COLUMNS)
    df_all = pd.concat([df_old, df_new], ignore_index=True)
    df_all.to_csv(STORE_PATH, index=False)

    # 👈 ESTA línea es la que te faltaba en tu versión
    return len(df_new)


def load_last_n(n: int = 50) -> pd.DataFrame:
    """
    Devuelve las últimas n combinaciones guardadas.
    """
    _ensure_store_exists()
    df = pd.read_csv(STORE_PATH)
    if df.empty:
        return df
    return df.tail(n).copy()