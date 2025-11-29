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


def _freq_to_hot_weights(
    freq: pd.Series,
    power: float = 1.5,
    n_total: int | None = None,
) -> np.ndarray:
    """
    Más frecuencia => más peso (modo Momentum).
    n_total = 50 para números, 12 para estrellas.
    """
    if n_total is None:
        if freq.empty:
            raise ValueError("n_total requerido cuando freq está vacía.")
        n_total = int(freq.index.max())

    if freq.empty:
        return _uniform_weights(n_total)

    values = (
        freq.reindex(range(1, n_total + 1), fill_value=0)
        .astype(float)
        .to_numpy()
    )
    values = values + 1.0  # suavizado
    weights = np.power(values, power)
    return weights / weights.sum()


def _freq_to_cold_weights(
    freq: pd.Series,
    power: float = 1.5,
    n_total: int | None = None,
) -> np.ndarray:
    """
    Menos frecuencia => más peso (modo Rareza).
    n_total = 50 para números, 12 para estrellas.
    """
    if n_total is None:
        if freq.empty:
            raise ValueError("n_total requerido cuando freq está vacía.")
        n_total = int(freq.index.max())

    if freq.empty:
        return _uniform_weights(n_total)

    values = (
        freq.reindex(range(1, n_total + 1), fill_value=0)
        .astype(float)
        .to_numpy()
    )
    values = values + 1.0
    max_v = values.max()
    inv = (max_v - values) + 1.0
    weights = np.power(inv, power)
    return weights / weights.sum()


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
    recent_window: int = 200,  # ya no se usa, pero lo dejamos por compatibilidad
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Devuelve (weights_main, weights_stars) según el modo.

    Ahora:
      - usamos TODO el histórico para números (1–50)
      - para estrellas (1–12) usamos solo la era de 12 estrellas (>= ERA_12_STARS_START)
    """
    mode_name = mode.split()[0]  # "Estándar", "Momentum", "Rareza", "Experimental"

    # --- Frecuencias base ---
    if df_hist.empty:
        freq_main_all = pd.Series([0] * 50, index=range(1, 51))
        freq_stars_all = pd.Series([0] * 12, index=range(1, 13))
    else:
        # Números → todo el histórico
        freq_main_all = compute_main_number_freq(df_hist)

        # Estrellas → solo era de 12 estrellas
        if "date" in df_hist.columns:
            df_stars_base = df_hist[df_hist["date"] >= ERA_12_STARS_START]
            if df_stars_base.empty:
                df_stars_base = df_hist
        else:
            df_stars_base = df_hist

        freq_stars_all = compute_star_freq(df_stars_base)

        if freq_main_all.empty:
            freq_main_all = pd.Series([0] * 50, index=range(1, 51))
        if freq_stars_all.empty:
            freq_stars_all = pd.Series([0] * 12, index=range(1, 13))

    # --- Pesos según modo ---
    if mode_name == "Estándar":
        w_main = _uniform_weights(50)
        w_stars = _uniform_weights(12)

    elif mode_name == "Momentum":
        # Más frecuencia histórica => más peso
        w_main = _freq_to_hot_weights(freq_main_all, n_total=50)
        w_stars = _freq_to_hot_weights(freq_stars_all, n_total=12)

    elif mode_name == "Rareza":
        # Menos frecuencia histórica => más peso
        w_main = _freq_to_cold_weights(freq_main_all, n_total=50)
        w_stars = _freq_to_cold_weights(freq_stars_all, n_total=12)

    elif mode_name == "Experimental":
        # Mezcla 50% caliente + 50% frío
        w_hot_main = _freq_to_hot_weights(freq_main_all, n_total=50)
        w_cold_main = _freq_to_cold_weights(freq_main_all, n_total=50)
        w_main = 0.5 * w_hot_main + 0.5 * w_cold_main
        w_main = w_main / w_main.sum()

        w_hot_stars = _freq_to_hot_weights(freq_stars_all, n_total=12)
        w_cold_stars = _freq_to_cold_weights(freq_stars_all, n_total=12)
        w_stars = 0.5 * w_hot_stars + 0.5 * w_cold_stars
        w_stars = w_stars / w_stars.sum()

    else:
        # Cualquier modo desconocido → uniforme
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