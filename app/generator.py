# app/generator.py
from __future__ import annotations

from typing import List, Dict, Any, Tuple, Set

import numpy as np
import pandas as pd

from app.metrics import compute_main_number_freq, compute_star_freq

# Inicio de la era de 12 estrellas
ERA_12_STARS_START = pd.Timestamp("2016-09-27")

# Límites de suma por serie (solo suma de los 5 números)
# A: alto, B: medio, C: bajo
SUM_RANGE_BY_SERIE: Dict[str, Tuple[int, int]] = {
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
    if freq.empty:
        return _uniform_weights(50)

    # Aseguramos que el índice máximo sea entero (evitamos float64)
    max_idx = int(round(freq.index.max()))
    if max_idx <= 0:
        return _uniform_weights(len(freq) or 50)

    values = freq.reindex(
        range(1, max_idx + 1), fill_value=0
    ).to_numpy(dtype=float)

    values = values + 1.0  # suavizado
    weights = np.power(values, power)
    weights = weights / weights.sum()
    return weights


def _freq_to_cold_weights(freq: pd.Series, power: float = 1.5) -> np.ndarray:
    """Menos frecuencia => más peso (modo Rareza / Game Theory)."""
    if freq.empty:
        return _uniform_weights(50)

    max_idx = int(round(freq.index.max()))
    if max_idx <= 0:
        return _uniform_weights(len(freq) or 50)

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
) -> Tuple[Set[Tuple[int, ...]], Set[Tuple[int, ...]]]:
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

    seen_numbers: Set[Tuple[int, ...]] = set()
    seen_full_era12: Set[Tuple[int, ...]] = set()

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


# ---------- score de "popularidad visual" ----------

def _popularity_score(nums: List[int]) -> int:
    """
    Score heurístico de "popularidad visual" de una combinación.

    Cuanto más alto, más probable que sea una combinación elegida por mucha gente:
      - muchas "fechas" (≤31),
      - rachas largas de consecutivos,
      - muchos números en la misma decena,
      - muchos múltiplos de 5.

    No es una verdad absoluta, pero sirve para evitar patrones muy típicos.
    """
    nums = sorted(nums)
    score = 0

    # 1) "Fechas": números 1–31
    count_le31 = sum(1 for x in nums if x <= 31)
    if count_le31 == 5:
        score += 4   # súper típica de fechas
    elif count_le31 == 4:
        score += 2

    # 2) Consecutivos
    max_run = 1
    current_run = 1
    for i in range(1, len(nums)):
        if nums[i] - nums[i - 1] == 1:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 1

    if max_run >= 4:
        score += 4   # ya lo vetas por hard limit, pero marcamos igualmente alto
    elif max_run == 3:
        score += 2
    elif max_run == 2:
        score += 1

    # 3) Decenas: 4 o más en la misma decena (muy "recto" en el boleto)
    decades = [(n - 1) // 10 for n in nums]  # 0..4
    counts: Dict[int, int] = {}
    for d in decades:
        counts[d] = counts.get(d, 0) + 1
    max_same_decade = max(counts.values())
    if max_same_decade >= 4:
        score += 3
    elif max_same_decade == 3:
        score += 1

    # 4) Múltiplos de 5
    mult5 = sum(1 for x in nums if x % 5 == 0)
    if mult5 >= 4:
        score += 3
    elif mult5 == 3:
        score += 1

    return score


# ---------- sampling de una línea con constraints ----------

def _sample_line(
    weights_main: np.ndarray,
    weights_stars: np.ndarray,
    serie: str,
    seen_numbers: Set[Tuple[int, ...]],
    seen_full_era12: Set[Tuple[int, ...]],
    block_seen_full: Set[Tuple[int, ...]],
    mode_name: str | None = None,
    max_tries: int = 500,
) -> Tuple[List[int], List[int]]:
    """
    Muestra una línea (5 números + 2 estrellas) respetando:

      - pesos de números y estrellas
      - rango de suma por serie
      - anti-clon sobre histórico y bloque
      - en modo "Game" (Game Theory): penaliza combinaciones "populares visualmente".
    """
    # Rango de suma por serie (A/B/C)
    min_sum, max_sum = SUM_RANGE_BY_SERIE.get(serie, (100, 158))

    last_nums: List[int] | None = None
    last_stars: List[int] | None = None

    for _ in range(max_tries):
        # 1) muestreamos números y estrellas según los pesos
        nums_arr = np.random.choice(
            np.arange(1, 51),
            size=5,
            replace=False,
            p=weights_main,
        )
        nums = sorted(int(x) for x in nums_arr)

        stars_arr = np.random.choice(
            np.arange(1, 13),
            size=2,
            replace=False,
            p=weights_stars,
        )
        stars = sorted(int(x) for x in stars_arr)

        last_nums, last_stars = nums, stars

        suma = sum(nums)

        # 2) rango de suma por serie
        if not (min_sum <= suma <= max_sum):
            continue

        # 3) penalización "Game Theory" (solo para modo Game)
        if mode_name == "Game":
            pop_score = _popularity_score(nums)
            # umbral: descartamos combinaciones demasiado "populares"
            if pop_score >= 3:
                continue

        num_key = tuple(nums)
        combo_key = tuple(nums + stars)

        # 4) Nunca repetir quinteta de números ya vista en TODO el histórico
        if num_key in seen_numbers:
            continue

        # 5) No repetir combinación completa de la era 12
        if combo_key in seen_full_era12:
            continue

        # 6) No repetir combinación dentro del mismo bloque
        if combo_key in block_seen_full:
            continue

        block_seen_full.add(combo_key)
        return nums, stars

    # Fallback defensivo si no encontró nada que cumpla todo
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
    En Momentum / Rareza / Experimental / Game Theory => usan frecuencias.
    """
    # "Game Theory" → "Game"
    mode_name = mode.split()[0]  # "Estándar", "Momentum", "Rareza", "Experimental", "Game"

    # Dataset reciente
    df_sorted = df_hist.sort_values("date") if not df_hist.empty else df_hist
    df_recent = (
        df_sorted.tail(recent_window)
        if len(df_sorted) > recent_window
        else df_sorted
    )

    if not df_recent.empty:
        freq_recent_main = compute_main_number_freq(df_recent)
        freq_recent_stars = compute_star_freq(df_recent)
    else:
        freq_recent_main = pd.Series([0] * 50, index=range(1, 51))
        freq_recent_stars = pd.Series([0] * 12, index=range(1, 13))

    if mode_name == "Estándar":
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

    elif mode_name == "Game":
        # Base "Rareza": preferimos números y estrellas fríos
        w_main = _freq_to_cold_weights(freq_recent_main)
        w_stars = _freq_to_cold_weights(freq_recent_stars)

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

    En todos los modos:
      - no repite quintetas de números vistas en el histórico completo
      - no repite combinaciones completas de la era de 12 estrellas
      - respeta límites de suma por serie

    En "Game Theory":
      - además penaliza combinaciones visualmente populares
        (muchas fechas, consecutivos largos, decenas saturadas, muchos múltiplos de 5).
    """
    w_main, w_stars = _build_weights_for_mode(mode, df_hist)
    mode_name = mode.split()[0]  # "Estándar", "Momentum", "Rareza", "Experimental", "Game"

    # Histórico usado para anti-clon
    seen_numbers, seen_full_era12 = _build_seen_combos(df_hist)
    block_seen_full: Set[Tuple[int, ...]] = set()

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
                mode_name=mode_name,
            )
            block.append(
                {
                    "serie": serie,
                    "nums": nums,
                    "stars": stars,
                }
            )

    return block