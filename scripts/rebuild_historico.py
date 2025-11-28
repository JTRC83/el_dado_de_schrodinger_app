from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]

# 🔴 PON AQUÍ EL NOMBRE REAL DEL CSV GRANDE QUE YA TIENES
RAW = BASE / "data" / "Historico_Resultados_Euromillones_2004_2025.csv"

OUT = BASE / "data" / "historico_euromillones.csv"

df_raw = pd.read_csv(RAW)

# ⬇️ ADAPTA ESTOS NOMBRES SI EN TU CSV SON DISTINTOS
df_out = pd.DataFrame(
    {
        "date": pd.to_datetime(df_raw["Fecha"], dayfirst=True, errors="coerce"),
        "n1": df_raw["N1"],
        "n2": df_raw["N2"],
        "n3": df_raw["N3"],
        "n4": df_raw["N4"],
        "n5": df_raw["N5"],
        "s1": df_raw["E1"],
        "s2": df_raw["E2"],
    }
)

# Limpiamos
df_out = df_out.dropna(subset=["date"])
for c in ["n1", "n2", "n3", "n4", "n5", "s1", "s2"]:
    df_out[c] = pd.to_numeric(df_out[c], errors="coerce")

df_out = df_out.dropna(subset=["n1", "n2", "n3", "n4", "n5", "s1", "s2"])
df_out = df_out.sort_values("date").reset_index(drop=True)

df_out.to_csv(OUT, index=False)
print("Guardado:", OUT, "filas:", len(df_out))