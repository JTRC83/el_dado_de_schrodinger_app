# app/metrics.py
import pandas as pd
import numpy as np

def compute_main_number_freq(df: pd.DataFrame) -> pd.Series:
    nums = pd.concat([df[f"n{i}"] for i in range(1, 6)], axis=0)
    return nums.value_counts().sort_index()

def compute_star_freq(df: pd.DataFrame) -> pd.Series:
    stars = pd.concat([df["s1"], df["s2"]], axis=0)
    return stars.value_counts().sort_index()

def compute_repeated_combinations(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["n1", "n2", "n3", "n4", "n5", "s1", "s2"]
    group = df.groupby(cols).size().reset_index(name="count")
    group = group[group["count"] > 1].sort_values("count", ascending=False)
    return group

def compute_backlog_numbers(df: pd.DataFrame) -> pd.Series:
    """
    Cuántos sorteos han pasado desde la última vez que salió cada número 1–50.
    """
    last_seen = {n: -1 for n in range(1, 51)}
    df_idx = df.reset_index(drop=True)

    for idx, row in df_idx.iterrows():
        for col in ["n1", "n2", "n3", "n4", "n5"]:
            num = int(row[col])
            last_seen[num] = idx

    total = len(df_idx)
    backlog = {
        n: (total - 1 - idx if idx >= 0 else total)
        for n, idx in last_seen.items()
    }
    return pd.Series(backlog).sort_values(ascending=False)

def compute_hot_cold_summary(df: pd.DataFrame, window: int = 50) -> dict:
    if df.empty:
        return {}

    window_df = df.tail(window)
    main_freq_window = compute_main_number_freq(window_df)
    hot_num = int(main_freq_window.idxmax())
    hot_num_freq = int(main_freq_window.max())

    backlog = compute_backlog_numbers(df)
    cold_num = int(backlog.idxmax())
    cold_gap = int(backlog.max())

    return {
        "hot_num": hot_num,
        "hot_num_freq": hot_num_freq,
        "cold_num": cold_num,
        "cold_gap": cold_gap,
    }

def compute_hot_cold_stars(df: pd.DataFrame, window: int = 50):
    """
    Devuelve la estrella más caliente y la más atrasada.

    hot_star: más frecuente en los últimos N sorteos (ventana limitada por len(df)).
    cold_star: estrella con mayor número de sorteos desde su última aparición
               (sobre todo el rango disponible).
    """
    if df.empty:
        return None

    df_sorted = df.sort_values("date")

    # Ventana efectiva
    n_draws = len(df_sorted)
    win = min(window, n_draws)

    # --- calientes (frecuencia en últimos N sorteos) ---
    recent = df_sorted.tail(win)

    stars_recent = recent[["s1", "s2"]].apply(pd.to_numeric, errors="coerce")
    flat_recent = stars_recent.to_numpy().ravel()
    flat_recent = [int(x) for x in flat_recent if not pd.isna(x)]

    if not flat_recent:
        return None

    counts = (
        pd.Series(flat_recent)
        .value_counts()
        .sort_values(ascending=False)
    )

    hot_star = int(counts.index[0])
    hot_star_freq = int(counts.iloc[0])

    # --- frías (gap desde última aparición en todo el rango) ---
    stars_all = df_sorted[["s1", "s2"]].apply(pd.to_numeric, errors="coerce")
    arr_all = stars_all.to_numpy()

    last_seen = {s: None for s in range(1, 13)}  # estrellas 1..12
    for idx, row in enumerate(arr_all):
        for val in row:
            if not pd.isna(val):
                v = int(val)
                last_seen[v] = idx

    gaps = {}
    for s in range(1, 13):
        if last_seen[s] is None:
            gaps[s] = n_draws
        else:
            gaps[s] = (n_draws - 1) - last_seen[s]

    cold_star = max(gaps, key=gaps.get)
    cold_gap = int(gaps[cold_star])

    return {
        "hot_star": hot_star,
        "hot_star_freq": hot_star_freq,
        "cold_star": cold_star,
        "cold_gap": cold_gap,
    }