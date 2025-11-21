# app/metrics.py
import pandas as pd

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

def compute_hot_cold_stars(df: pd.DataFrame, window: int = 50) -> dict:
    if df.empty:
        return {}

    window_df = df.tail(window)
    star_freq_window = compute_star_freq(window_df)
    hot_star = int(star_freq_window.idxmax())
    hot_star_freq = int(star_freq_window.max())

    last_seen = {s: -1 for s in range(1, 13)}
    df_idx = df.reset_index(drop=True)

    for idx, row in df_idx.iterrows():
        for col in ["s1", "s2"]:
            star = int(row[col])
            last_seen[star] = idx

    total = len(df_idx)
    backlog = {
        s: (total - 1 - idx if idx >= 0 else total)
        for s, idx in last_seen.items()
    }
    backlog_series = pd.Series(backlog).sort_values(ascending=False)

    cold_star = int(backlog_series.idxmax())
    cold_gap = int(backlog_series.max())

    return {
        "hot_star": hot_star,
        "hot_star_freq": hot_star_freq,
        "cold_star": cold_star,
        "cold_gap": cold_gap,
    }
