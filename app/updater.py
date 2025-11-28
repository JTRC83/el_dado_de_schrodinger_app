# app/updater.py
from pathlib import Path
from datetime import date
from typing import Optional

import requests
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "historico_euromillones.csv"
API_URL = "https://euromillions.api.pedromealha.dev/v1/draws"


# ------------ Utilidades de normalización ------------

def _normalize_local_df(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza un DataFrame local cualquiera al esquema:
    date (datetime64[ns]), n1..n5, s1, s2
    Acepta variantes: Fecha/date, N1..N5/n1..n5, E1/E2/S1/S2, etc.
    """
    df = df_raw.copy()

    # Normalizar columna de fecha
    date_col = None
    if "date" in df.columns:
        date_col = "date"
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    elif "Fecha" in df.columns:
        date_col = "Fecha"
        df["date"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")

    if date_col is None:
        # No hay columna reconocible → devolvemos vacío con esquema estándar
        return pd.DataFrame(columns=["date", "n1", "n2", "n3", "n4", "n5", "s1", "s2"])

    # Mapeo flexible de números
    num_map_candidates = {
        "n1": ["n1", "N1", "Num1", "NUM1"],
        "n2": ["n2", "N2", "Num2", "NUM2"],
        "n3": ["n3", "N3", "Num3", "NUM3"],
        "n4": ["n4", "N4", "Num4", "NUM4"],
        "n5": ["n5", "N5", "Num5", "NUM5"],
    }

    star_map_candidates = {
        "s1": ["s1", "S1", "E1", "Est1", "STAR1"],
        "s2": ["s2", "S2", "E2", "Est2", "STAR2"],
    }

    norm_cols = {"date": "date"}

    for target, candidates in num_map_candidates.items():
        for c in candidates:
            if c in df.columns:
                norm_cols[target] = c
                break

    for target, candidates in star_map_candidates.items():
        for c in candidates:
            if c in df.columns:
                norm_cols[target] = c
                break

    # Construimos DataFrame normalizado
    needed = ["date", "n1", "n2", "n3", "n4", "n5", "s1", "s2"]
    data = {}
    for col in needed:
        if col in norm_cols:
            data[col] = df[norm_cols[col]]
        else:
            # columna que falta → la rellenamos con NaN
            data[col] = pd.Series([pd.NA] * len(df))

    df_norm = pd.DataFrame(data)

    # Tipos
    df_norm["date"] = pd.to_datetime(df_norm["date"], errors="coerce")
    for c in ["n1", "n2", "n3", "n4", "n5", "s1", "s2"]:
        df_norm[c] = pd.to_numeric(df_norm[c], errors="coerce")

    df_norm = df_norm.dropna(subset=["date"])
    df_norm = df_norm.sort_values("date").reset_index(drop=True)

    return df_norm[needed]


def _load_local_normalized() -> pd.DataFrame:
    """Carga el CSV local (si existe) y lo normaliza al esquema estándar."""
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=["date", "n1", "n2", "n3", "n4", "n5", "s1", "s2"])

    df_raw = pd.read_csv(DATA_PATH)
    return _normalize_local_df(df_raw)


def _get_last_local_date() -> Optional[date]:
    df_local = _load_local_normalized()
    if df_local.empty:
        return None
    return df_local["date"].max().date()


# ------------ API externa ------------

def _fetch_all_draws_from_api() -> pd.DataFrame:
    """
    Descarga todos los sorteos desde la API externa y devuelve
    un DataFrame YA normalizado a:
    date, n1..n5, s1, s2
    """
    resp = requests.get(API_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for d in data:
        date_str = d.get("date") or d.get("draw_date")
        if not date_str:
            continue

        draw_ts = pd.to_datetime(date_str, errors="coerce")
        if pd.isna(draw_ts):
            continue

        nums = d.get("numbers") or []
        stars = d.get("stars") or []
        if len(nums) != 5 or len(stars) != 2:
            continue

        nums = sorted(nums)
        stars = sorted(stars)

        rows.append(
            {
                "date": draw_ts,
                "n1": nums[0],
                "n2": nums[1],
                "n3": nums[2],
                "n4": nums[3],
                "n5": nums[4],
                "s1": stars[0],
                "s2": stars[1],
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in ["n1", "n2", "n3", "n4", "n5", "s1", "s2"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    return df[["date", "n1", "n2", "n3", "n4", "n5", "s1", "s2"]]


# ------------ Función principal ------------

def update_historico_from_api() -> int:
    """
    Actualiza el CSV de histórico con los sorteos nuevos obtenidos desde la API.
    Trabaja siempre con el esquema: date, n1..n5, s1, s2.
    Devuelve el número de sorteos añadidos.
    """
    df_api = _fetch_all_draws_from_api()
    if df_api.empty:
        return 0

    df_local = _load_local_normalized()
    last_local = _get_last_local_date()

    if last_local is not None:
        df_new = df_api[df_api["date"].dt.date > last_local].copy()
    else:
        df_new = df_api.copy()

    if df_new.empty:
        return 0

    combined = pd.concat([df_local, df_new], ignore_index=True)

    combined = (
        combined.drop_duplicates(
            subset=["date", "n1", "n2", "n3", "n4", "n5", "s1", "s2"],
            keep="first",
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    # Guardamos SIEMPRE en el esquema estándar: date,n1..n5,s1,s2
    combined.to_csv(DATA_PATH, index=False)

    return len(df_new)