# app/updater.py
from pathlib import Path
from datetime import date
from typing import Optional 
import requests
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "historico_euromillones.csv"
API_URL = "https://euromillions.api.pedromealha.dev/v1/draws"

def _fetch_all_draws_from_api() -> pd.DataFrame:
    resp = requests.get(API_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for d in data:
        date_str = d.get("date") or d.get("draw_date")
        if not date_str:
            continue

        draw_date = pd.to_datetime(date_str).date()
        nums = sorted(d["numbers"])
        stars = sorted(d["stars"])
        if len(nums) != 5 or len(stars) != 2:
            continue

        rows.append(
            {
                "Fecha_dt": draw_date,
                "N1": nums[0],
                "N2": nums[1],
                "N3": nums[2],
                "N4": nums[3],
                "N5": nums[4],
                "E1": stars[0],
                "E2": stars[1],
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.sort_values("Fecha_dt")
    df["Fecha"] = df["Fecha_dt"].dt.strftime("%d/%m/%Y")
    return df

def _get_last_local_date() -> date | None:
    if not DATA_PATH.exists():
        return None

    df_local = pd.read_csv(DATA_PATH)
    if "Fecha" not in df_local.columns:
        return None

    fechas = pd.to_datetime(df_local["Fecha"], dayfirst=True, errors="coerce")
    if fechas.isna().all():
        return None

    return fechas.max().date()

def update_historico_from_api() -> int:
    df_api = _fetch_all_draws_from_api()
    if df_api.empty:
        return 0

    last_local = _get_last_local_date()

    if last_local is not None:
        df_new = df_api[df_api["Fecha_dt"] > last_local]
    else:
        df_new = df_api

    if df_new.empty:
        return 0

    if DATA_PATH.exists():
        df_local = pd.read_csv(DATA_PATH)
    else:
        df_local = pd.DataFrame(columns=["Fecha", "N1", "N2", "N3", "N4", "N5", "E1", "E2"])

    df_new_to_save = df_new[["Fecha", "N1", "N2", "N3", "N4", "N5", "E1", "E2"]]

    combined = pd.concat([df_local, df_new_to_save], ignore_index=True)
    combined = combined.drop_duplicates(
        subset=["Fecha", "N1", "N2", "N3", "N4", "N5", "E1", "E2"],
        keep="first",
    ).sort_values("Fecha")

    combined.to_csv(DATA_PATH, index=False)

    return len(df_new_to_save)
