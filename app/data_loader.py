# app/data_loader.py
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "historico_euromillones.csv"

def load_raw_data() -> pd.DataFrame:
    """
    Carga el histórico del Euromillón desde el CSV oficial que viene en formato:
    FECHA;COMB. GANADORA;;;;;ESTRELLAS;
    4/11/2025;6;9;25;28;45;1;4
    ...

    y lo convierte a columnas:
    date, n1..n5, s1, s2
    ordenado por fecha ascendente.
    """
    # Leemos con separador ';' y sin fiarnos del encabezado
    df = pd.read_csv(DATA_PATH, sep=";", header=None)

    # Primera fila es el pseudo-encabezado "FECHA;COMB. GANADORA;...;ESTRELLAS;"
    # La descartamos
    df = df.iloc[1:, :].reset_index(drop=True)

    # Nos quedamos con las 8 primeras columnas: Fecha, N1..N5, E1, E2
    if df.shape[1] < 8:
        raise ValueError("El CSV no tiene al menos 8 columnas esperadas (Fecha + 7 valores).")

    df = df.iloc[:, :8]
    df.columns = ["Fecha", "N1", "N2", "N3", "N4", "N5", "E1", "E2"]

    # Convertimos tipos
    df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")

    for col in ["N1", "N2", "N3", "N4", "N5", "E1", "E2"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Quitamos filas sin fecha válida y ordenamos
    df = df.dropna(subset=["Fecha"]).sort_values("Fecha").reset_index(drop=True)

    # Renombramos a los nombres que usa el resto de la app
    df = df.rename(
        columns={
            "Fecha": "date",
            "N1": "n1",
            "N2": "n2",
            "N3": "n3",
            "N4": "n4",
            "N5": "n5",
            "E1": "s1",
            "E2": "s2",
        }
    )

    return df
