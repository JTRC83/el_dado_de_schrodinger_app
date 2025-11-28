# app/generator.py
from __future__ import annotations

from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd

from app.metrics import compute_main_number_freq, compute_star_freq


# Inicio de la era de 12 estrellas
ERA_12_STARS_START = pd.Timestamp("2016-09-27")

# Rangos de suma por serie (solo suma de los 5 números)
# C: bajo, B: medio, A: alto dentro del rango global ~[100,158]
SUM_RANGE_BY_SERIE: dict[str, tuple[int, int]] = {
    "A": (141, 158),  # alto
    "B": (121, 140),  # medio
    "C": (100, 120),  # bajo
}


# ---------- utilidades de pesos ----------

def _uniform_weights(n: int) -> np.ndarray:
    w = np.ones(n, dtype=float)
    return w / w.sum()


def _freq_to_hot_weights(freq: pd.Series, power: float = 1.5) -> np.ndarray:
    """Más frecuencia => más peso (modo Momentum)."""
    # Nos aseguramos de cubrir todo el rango de índices (1..max)
    max_idx = int(freq.index.max())
    values = freq.reindex(
        range(1, max_idx + 1), fill_value=0
    ).to_numpy(dtype=float)

    values = values + 1.0  # suavizado para evitar ceros
    weights = np.power(values, power)
    weights = weights / weights.sum()
    return weights


def _freq_to_cold_weights(freq: pd.Series, power: float = 1.5) -> np.ndarray:
    """Menos frecuencia => más peso (modo Rareza)."""
    max_idx = int(freq.index.max())
    values = freq.reindex(
        range(1, max_idx + 1), fill_value=0
    ).to_numpy(dtype=float)

    values = values + 1.0
    max_v = values.max()
    inv = (max_v - values) + 1.0
    weights = np.power(inv, power)
    weights = weights / weights.sum()
    return weights


# ---------- anti-clon: combinaciones ya usadas ----------

def _build_seen_combos(
    df_hist: pd.DataFrame,
) -> tuple[set[tuple[int, ...]], set[tuple[int, ...]]]:
    """
    Devuelve dos sets:

    - seen_numbers: todas las quintetas de números (n1..n5) que han salido
      en cualquier momento del histórico (2004 → hoy).

    - seen_full_era12: todas las combinaciones completas (5 números + 2 estrellas)
      que han salido en la era de 12 estrellas (desde 2016-09-27).

    Así:
      - nunca repetimos 5 números vistos en el histórico completo;
      - y evitamos repetir una combinación entera (números+estrellas) de la era 12.
    """
    if df_hist.empty or "date" not in df_hist.columns:
        return set(), set()

    cols_nums = ["n1", "n2", "n3", "n4", "n5"]
    cols_stars = ["s1", "s2"]

    seen_numbers: set[tuple[int, ...]] = set()
    seen_full_era12: set[tuple[int, ...]] = set()

    for _, row in df_hist.iterrows():
        try:
            nums = sorted(int(row[c]) for c in cols_nums)
        except Exception:
            continue

        num_key = tuple(nums)
        seen_numbers.add(num_key)

        # Para la parte de estrellas, solo contamos la era 12
        if row["date"] >= ERA_12_STARS_START:
            try:
                stars = sorted(int(row[c]) for c in cols_stars)
            except Exception:
                continue
            combo_key = tuple(nums + stars)
            seen_full_era12.add(combo_key)

    return seen_numbers, seen_full_era12


# ---------- sampling de una línea con constraints ----------

def _sample_line(
    weights_main: np.ndarray,
    weights_stars: np.ndarray,
    serie: str,
    seen_numbers: set[tuple[int, ...]],
    seen_full_era12: set[tuple[int, ...]],
    block_seen_full: set[tuple[int, ...]],
    max_tries: int = 500,
) -> Tuple[List[int], List[int]]:
    """
    Genera una línea que:
      - respeta el rango de suma por serie
      - no repite ninguna quinteta de números del histórico completo
      - no repite combinaciones completas (números+estrellas) de la era 12
      - no repite combinaciones completas dentro del mismo bloque
    """
    min_sum, max_sum = SUM_RANGE_BY_SERIE.get(serie, (100, 158))

    last_nums: List[int] | None = None
    last_stars: List[int] | None = None

    for _ in range(max_tries):
        nums = np.random.choice(
            np.arange(1, 51),
            size=5,
            replace=False,
            p=weights_main,
        )
        nums = sorted(int(x) for x in nums)

        stars = np.random.choice(
            np.arange(1, 13),
            size=2,
            replace=False,
            p=weights_stars,
        )
        stars = sorted(int(x) for x in stars)

        last_nums, last_stars = nums, stars

        suma = sum(nums)

        # Rango de suma por serie
        if not (min_sum <= suma <= max_sum):
            continue

        num_key = tuple(nums)
        combo_key = tuple(nums + stars)

        # 1) Nunca repetir 5 números ya vistos en TODO el histórico
        if num_key in seen_numbers:
            continue

        # 2) No repetir combinación completa de la era 12
        if combo_key in seen_full_era12:
            continue

        # 3) No repetir combinación dentro del mismo bloque
        if combo_key in block_seen_full:
            continue

        block_seen_full.add(combo_key)
        return nums, stars

    # Fallback defensivo: si no se ha encontrado nada “válido” en max_tries
    if last_nums is None:
        last_nums = sorted(
            np.random.choice(np.arange(1, 51), size=5, replace=False)
        )
        last_stars = sorted(
            np.random.choice(np.arange(1, 13), size=2, replace=False)
        )

    return last_nums, last_stars


# ---------- pesos por modo ----------

def _build_weights_for_mode(
    mode: str,
    df_hist: pd.DataFrame,
    recent_window: int = 200,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Devuelve (weights_main, weights_stars) según el modo.
    En Estándar => uniformes.
    En Momentum / Rareza / Experimental => usan frecuencias recientes.
    """
    mode_name = mode.split()[0]  # "Estándar", "Momentum", "Rareza", "Experimental"

    # Dataset reciente
    df_sorted = df_hist.sort_values("date") if not df_hist.empty else df_hist
    df_recent = (
        df_sorted.tail(recent_window)
        if len(df_sorted) > recent_window
        else df_sorted
    )

    if df_recent.empty:
        freq_recent_main = pd.Series([0] * 50, index=range(1, 51))
        freq_recent_stars = pd.Series([0] * 12, index=range(1, 13))
    else:
        freq_recent_main = compute_main_number_freq(df_recent)
        freq_recent_stars = compute_star_freq(df_recent)

    if mode_name == "Estándar":
        # Uniforme, el “cerebro” lo ponen los filtros (anti-clon + sumas)
        w_main = _uniform_weights(50)
        w_stars = _uniform_weights(12)

    elif mode_name == "Momentum":
        w_main = _freq_to_hot_weights(freq_recent_main)
        w_stars = _freq_to_hot_weights(freq_recent_stars)

    elif mode_name == "Rareza":
        w_main = _freq_to_cold_weights(freq_recent_main)
        w_stars = _freq_to_cold_weights(freq_recent_stars)

    elif mode_name == "Experimental":
        w_hot_main = _freq_to_hot_weights(freq_recent_main)
        w_cold_main = _freq_to_cold_weights(freq_recent_main)
        w_main = 0.5 * w_hot_main + 0.5 * w_cold_main
        w_main = w_main / w_main.sum()

        w_hot_stars = _freq_to_hot_weights(freq_recent_stars)
        w_cold_stars = _freq_to_cold_weights(freq_recent_stars)
        w_stars = 0.5 * w_hot_stars + 0.5 * w_cold_stars
        w_stars = w_stars / w_stars.sum()
    else:
        w_main = _uniform_weights(50)
        w_stars = _uniform_weights(12)

    return w_main, w_stars


# ---------- interfaz pública ----------

def generate_block(
    mode: str,
    df_hist: pd.DataFrame,
    lines_A: int,
    lines_B: int,
    lines_C: int,
) -> List[Dict[str, Any]]:
    """
    Genera un bloque de combinaciones para las series A/B/C según el modo.

    En Estándar (y resto, a nivel de seguridad):
      - no repite quintetas de números vistas en el histórico completo
      - no repite combinaciones completas de la era de 12 estrellas
      - respeta rangos de suma por serie
    """
    w_main, w_stars = _build_weights_for_mode(mode, df_hist)

    # Histórico usado para anti-clon: números = todo, estrellas = era 12
    seen_numbers, seen_full_era12 = _build_seen_combos(df_hist)
    block_seen_full: set[tuple[int, ...]] = set()

    block: List[Dict[str, Any]] = []

    for serie, n_lines in [("A", lines_A), ("B", lines_B), ("C", lines_C)]:
        for _ in range(int(n_lines)):
            nums, stars = _sample_line(
                weights_main=w_main,
                weights_stars=w_stars,
                serie=serie,
                seen_numbers=seen_numbers,
                seen_full_era12=seen_full_era12,
                block_seen_full=block_seen_full,
            )
            block.append(
                {
                    "serie": serie,
                    "nums": nums,
                    "stars": stars,
                }
            )

    return block