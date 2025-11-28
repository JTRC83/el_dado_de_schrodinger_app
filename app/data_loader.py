# app/data_loader.py
from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "historico_euromillones.csv"


def _normalize_df(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza el DataFrame del CSV al esquema estándar:

        date (datetime64[ns]), n1..n5, s1, s2  (numéricos)

    Admite dos formatos principales en el CSV:
    - Formato "español":  Fecha, N1..N5, E1, E2
    - Formato "estándar": date, n1..n5, s1, s2

    Cualquier otra columna extra se ignora.
    """

    # Caso 1: ya viene en formato estándar
    if "date" in df_raw.columns:
        df = df_raw.copy()

        # Aseguramos que todas las columnas esperadas existen
        for target, candidates in {
            "n1": ["n1", "N1"],
            "n2": ["n2", "N2"],
            "n3": ["n3", "N3"],
            "n4": ["n4", "N4"],
            "n5": ["n5", "N5"],
            "s1": ["s1", "S1", "E1"],
            "s2": ["s2", "S2", "E2"],
        }.items():
            if target not in df.columns:
                for c in candidates:
                    if c in df_raw.columns:
                        df[target] = df_raw[c]
                        break

    # Caso 2: formato español (Fecha, N1..N5, E1, E2)
    elif "Fecha" in df_raw.columns:
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    df_raw["Fecha"], dayfirst=True, errors="coerce"
                ),
                "n1": df_raw.get("N1"),
                "n2": df_raw.get("N2"),
                "n3": df_raw.get("N3"),
                "n4": df_raw.get("N4"),
                "n5": df_raw.get("N5"),
                "s1": df_raw.get("E1"),
                "s2": df_raw.get("E2"),
            }
        )
    else:
        # No reconocemos el formato → devolvemos un DF vacío con el esquema correcto
        return pd.DataFrame(
            columns=["date", "n1", "n2", "n3", "n4", "n5", "s1", "s2"]
        )

    # Tipos y limpieza
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    for c in ["n1", "n2", "n3", "n4", "n5", "s1", "s2"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["date", "n1", "n2", "n3", "n4", "n5", "s1", "s2"])
    df = df.sort_values("date").reset_index(drop=True)

    # Nos quedamos solo con las columnas estándar en el orden esperado
    return df[["date", "n1", "n2", "n3", "n4", "n5", "s1", "s2"]]


def load_raw_data() -> pd.DataFrame:
    """
    Carga el CSV de histórico y lo devuelve normalizado al esquema estándar
    para el resto de la app.
    """
    if not DATA_PATH.exists():
        # Esquema vacío pero compatible con el resto de la app
        return pd.DataFrame(
            columns=["date", "n1", "n2", "n3", "n4", "n5", "s1", "s2"]
        )

    df_raw = pd.read_csv(DATA_PATH)
    df_norm = _normalize_df(df_raw)
    return df_norm