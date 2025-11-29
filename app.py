# app.py
import random

import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import time

from app.data_loader import load_raw_data
from app.ui_theme import inject_neobrutalist_theme
from app.metrics import (
    compute_main_number_freq,
    compute_star_freq,
    compute_repeated_combinations,
    compute_hot_cold_summary,
    compute_hot_cold_stars,
)

from app.updater import update_historico_from_api
from app.generator import generate_block
from app.combinations_store import save_block
from app.generator import generate_block, SUM_RANGE_BY_SERIE
from app.combinations_store import save_block, load_last_n
from app.simulator import simulate_strategy

st.set_page_config(page_title="El dado de Schrödinger", layout="wide")
inject_neobrutalist_theme()

if "last_block" not in st.session_state:
    st.session_state["last_block"] = None
    st.session_state["last_block_meta"] = {}

if "last_manual" not in st.session_state:
    st.session_state["last_manual"] = None

@st.cache_data
def get_data() -> pd.DataFrame:
    return load_raw_data()


# --- SIDEBAR ---
CAT_IMAGE_PATH = "assets/gato_dado.png"
st.sidebar.image(CAT_IMAGE_PATH, use_container_width=True)

st.sidebar.title("El dado de Schrödinger")

cooldown_seconds = 60  # por ejemplo, 1 minuto

last_update = st.session_state.get("last_update_attempt")

if last_update is not None:
    elapsed = time.time() - last_update
else:
    elapsed = cooldown_seconds + 1  # para permitir la primera vez

if st.sidebar.button("♻️  Actualizar histórico (API)"):
    try:
        added = update_historico_from_api()
        get_data.clear()
        if added == 0:
            st.sidebar.info("Histórico ya estaba actualizado.")
        else:
            st.sidebar.success(f"Actualizado: {added} sorteos nuevos.")
    except Exception as e:
        msg = str(e)
        if "429" in msg:
            st.sidebar.warning(
                "La API externa ha devuelto 429 (Too Many Requests).\n\n"
                "Espera unos minutos antes de volver a actualizar."
            )
        else:
            st.sidebar.error(f"Error al actualizar: {e}")

df = get_data()

st.title("El dado de Schrödinger 🎲")

tab_hist, tab_gen, tab_check, tab_sim = st.tabs(
    [
        "📊 Explorador histórico",
        "🎲 Generador A/B/C",
        "✅ Comprobar resultados",
        "🎛 Simulador Monte Carlo",
    ]
)

# -------------------------------------------------------------------
# 📊 TAB: EXPLORADOR HISTÓRICO
# -------------------------------------------------------------------
with tab_hist:
    if df.empty or "date" not in df.columns:
        st.error("No se pudieron cargar los datos. Revisa el CSV en /data.")
    else:
        min_date = df["date"].min().date()
        max_date = df["date"].max().date()

        # --- Barra título Filtros de rango ---
        st.markdown(
            '<div class="neocard neocard--accent1">'
            '<p class="neocard-title">Filtros de rango</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            date_range = st.date_input(
                "Rango de fechas",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
        with col_f2:
            window = st.selectbox(
                "Ventana para curiosidades (últimos N sorteos)",
                options=[50, 100, 200],
                index=0,
            )

        # Filtrado por fechas
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start, end = date_range
            mask = (df["date"] >= pd.to_datetime(start)) & (
                df["date"] <= pd.to_datetime(end)
            )
            df_filtered = df.loc[mask].copy()
        else:
            df_filtered = df.copy()

        # Para estrellas: usar solo la era de 12 estrellas (desde 2016-09-27)
        star_era_start = pd.Timestamp("2016-09-27")
        df_stars_era = df_filtered[df_filtered["date"] >= star_era_start]
        if df_stars_era.empty:
            df_stars_era = df_filtered

        # --- Barra título Resumen histórico ---
        st.markdown(
            '<div class="neocard neocard--accent2">'
            '<p class="neocard-title">Resumen histórico</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Sorteos en rango", len(df_filtered))
        with c2:
            st.metric(
                "Primera fecha",
                df_filtered["date"].min().strftime("%d/%m/%Y"),
            )
        with c3:
            st.metric(
                "Última fecha",
                df_filtered["date"].max().strftime("%d/%m/%Y"),
            )

        # --- Frecuencias y curiosidades ---
        col_left, col_right = st.columns([2, 1])

        # =============== COLUMNA IZQUIERDA ===============
        with col_left:
            # Frecuencia números
            st.markdown(
                '<div class="neocard neocard--accent5">'
                '<p class="neocard-title">Frecuencia de números (1–50)</p>'
                "</div>",
                unsafe_allow_html=True,
            )

            main_freq = compute_main_number_freq(df_filtered)
            freq_df = main_freq.reset_index()
            freq_df.columns = ["numero", "frecuencia"]

            def color_por_frecuencia(v: int) -> str:
                if v >= 200:
                    return "green"
                elif v >= 180:
                    return "blue"
                elif v >= 160:
                    return "orange"
                elif v >= 140:
                    return "pink"
                else:
                    return "lightgray"

            freq_df["color"] = freq_df["frecuencia"].apply(color_por_frecuencia)

            chart = (
                alt.Chart(freq_df)
                .mark_bar()
                .encode(
                    x=alt.X("numero:O", title="Número"),
                    y=alt.Y("frecuencia:Q", title="Frecuencia"),
                    color=alt.Color("color:N", scale=None, legend=None),
                    tooltip=["numero", "frecuencia"],
                )
                .properties(height=380)
            )
            st.altair_chart(chart, use_container_width=True)

            # Leyenda colores números
            st.markdown(
                """
<div style="
  display:flex;
  justify-content:center;
  gap:16px;
  flex-wrap:wrap;
  align-items:center;
  font-size:0.9rem;
  margin-top:0.1rem;
">
  <div style="display:flex; align-items:center; gap:4px;">
    <span style="display:inline-block; width:14px; height:14px; background-color:green; border-radius:3px; border:2px solid #111;"></span>
    <span>≥ 200 apariciones</span>
  </div>
  <div style="display:flex; align-items:center; gap:4px;">
    <span style="display:inline-block; width:14px; height:14px; background-color:blue; border-radius:3px; border:2px solid #111;"></span>
    <span>180–199 apariciones</span>
  </div>
  <div style="display:flex; align-items:center; gap:4px;">
    <span style="display:inline-block; width:14px; height:14px; background-color:orange; border-radius:3px; border:2px solid #111;"></span>
    <span>160–179 apariciones</span>
  </div>
  <div style="display:flex; align-items:center; gap:4px;">
    <span style="display:inline-block; width:14px; height:14px; background-color:pink; border-radius:3px; border:2px solid #111;"></span>
    <span>140–159 apariciones</span>
  </div>
  <div style="display:flex; align-items:center; gap:4px;">
    <span style="display:inline-block; width:14px; height:14px; background-color:lightgray; border-radius:3px; border:2px solid #111;"></span>
    <span>&lt; 140 apariciones</span>
  </div>
</div>
<hr>
                """,
                unsafe_allow_html=True,
            )

            # Frecuencia estrellas (era 12)
            st.markdown(
                '<div class="neocard neocard--accent5">'
                '<p class="neocard-title">Frecuencia de estrellas (1–12)</p>'
                "</div>",
                unsafe_allow_html=True,
            )

            star_freq = compute_star_freq(df_stars_era)
            if len(star_freq) == 0:
                st.write("No hay datos de estrellas en el rango seleccionado.")
            else:
                est_df = star_freq.reset_index()
                est_df.columns = ["estrella", "frecuencia"]
                values = est_df["frecuencia"].to_numpy(dtype=float)
                if len(values) >= 5:
                    q1, q2, q3, q4 = np.quantile(values, [0.2, 0.4, 0.6, 0.8])
                else:
                    q1 = q2 = q3 = q4 = values.min()

                def color_por_frecuencia_estrella(v: float) -> str:
                    if v >= q4:
                        return "green"
                    elif v >= q3:
                        return "blue"
                    elif v >= q2:
                        return "orange"
                    elif v >= q1:
                        return "pink"
                    else:
                        return "lightgray"

                est_df["color"] = est_df["frecuencia"].apply(
                    color_por_frecuencia_estrella
                )

                chart_stars = (
                    alt.Chart(est_df)
                    .mark_bar()
                    .encode(
                        x=alt.X("estrella:O", title="Estrella"),
                        y=alt.Y("frecuencia:Q", title="Frecuencia"),
                        color=alt.Color("color:N", scale=None, legend=None),
                        tooltip=["estrella", "frecuencia"],
                    )
                    .properties(
                        height=450
                    )
                )

                st.altair_chart(chart_stars, use_container_width=True)

                st.markdown(
                    """
<div style="
  display:flex;
  justify-content:center;
  gap:16px;
  flex-wrap:wrap;
  align-items:center;
  font-size:0.9rem;
  margin-top:0.1rem;
">
  <div style="display:flex; align-items:center; gap:4px;">
    <span style="display:inline-block; width:14px; height:14px; background-color:green; border-radius:3px; border:2px solid #111;"></span>
    <span>frecuencia muy alta (top 20%)</span>
  </div>
  <div style="display:flex; align-items:center; gap:4px;">
    <span style="display:inline-block; width:14px; height:14px; background-color:blue; border-radius:3px; border:2px solid #111;"></span>
    <span>alta (20–40%)</span>
  </div>
  <div style="display:flex; align-items:center; gap:4px;">
    <span style="display:inline-block; width:14px; height:14px; background-color:orange; border-radius:3px; border:2px solid #111;"></span>
    <span>media (40–60%)</span>
  </div>
  <div style="display:flex; align-items:center; gap:4px;">
    <span style="display:inline-block; width:14px; height:14px; background-color:pink; border-radius:3px; border:2px solid #111;"></span>
    <span>baja (60–80%)</span>
  </div>
  <div style="display:flex; align-items:center; gap:4px;">
    <span style="display:inline-block; width:14px; height:14px; background-color:lightgray; border-radius:3px; border:2px solid #111;"></span>
    <span>muy baja (último 20%)</span>
  </div>
</div>
                    """,
                    unsafe_allow_html=True,
                )

                st.caption(
                    " * Frecuencias de estrellas calculadas desde 27/09/2016 "
                    "(inicio de la era de 12 estrellas)."
                )

        # =============== COLUMNA DERECHA ===============
        with col_right:
            # Curiosidades números
            st.markdown(
                '<div class="neocard neocard--accent3">'
                '<p class="neocard-title">Curiosidades (números)</p>'
                "</div>",
                unsafe_allow_html=True,
            )
            hot_cold = compute_hot_cold_summary(df_filtered, window=window)
            if hot_cold:
                st.write(
                    f"🔥 Número más caliente (últimos {window}): "
                    f"**{hot_cold['hot_num']}** "
                    f"({hot_cold['hot_num_freq']} apariciones)"
                )
                st.write(
                    f"🧊 Número más atrasado: "
                    f"**{hot_cold['cold_num']}** "
                    f"(lleva {hot_cold['cold_gap']} sorteos sin salir)"
                )
            else:
                st.write("No hay datos suficientes.")

                            # Momentum extendido (Top 5 calientes / fríos)
            st.markdown(
                '<div class="neocard neocard--accent4">'
                '<p class="neocard-title">Momentum extendido (Top 5 calientes / fríos)</p>'
                '</div>',
                unsafe_allow_html=True,
            )

            if len(df_filtered) >= 1:
                # Ordenamos por fecha para tener el timeline claro
                df_sorted_all = df_filtered.sort_values("date")
                n_draws = len(df_sorted_all)

                # Ventana efectiva para los calientes (por si el rango es corto)
                window_eff = min(window, n_draws)
                df_recent = df_sorted_all.tail(window_eff)

                # Números recientes para "calientes"
                nums_recent = (
                    df_recent[["n1", "n2", "n3", "n4", "n5"]]
                    .apply(pd.to_numeric, errors="coerce")
                    .dropna()
                )
                if not nums_recent.empty:
                    counts_recent = (
                        pd.Series(nums_recent.to_numpy().ravel())
                        .dropna()
                        .astype(int)
                        .value_counts()
                    )
                    top_hot = counts_recent.head(5)
                else:
                    top_hot = pd.Series(dtype=int)

                # Números "fríos" por gap de sorteos sin salir en el rango
                nums_all = (
                    df_sorted_all[["n1", "n2", "n3", "n4", "n5"]]
                    .apply(pd.to_numeric, errors="coerce")
                    .dropna()
                    .to_numpy(dtype=int)
                )

                last_seen = {num: None for num in range(1, 51)}
                for idx, row_nums in enumerate(nums_all):
                    for num in row_nums:
                        last_seen[num] = idx

                gaps = {}
                for num in range(1, 51):
                    if last_seen[num] is None:
                        # No ha salido en el rango → muy frío
                        gaps[num] = n_draws
                    else:
                        gaps[num] = (n_draws - 1) - last_seen[num]

                gaps_s = pd.Series(gaps).sort_values(ascending=False)
                top_cold = gaps_s.head(5)

                col_mom1, col_mom2 = st.columns(2)

                with col_mom1:
                    st.markdown("**Top 5 números calientes**")
                    if top_hot.empty:
                        st.write("Sin datos suficientes en la ventana seleccionada.")
                    else:
                        for num, freq in top_hot.items():
                            st.write(
                                f"- **{int(num)}** → {int(freq)} apariciones "
                                f"en los últimos {window_eff} sorteos"
                            )

                with col_mom2:
                    st.markdown("**Top 5 números fríos**")
                    for num, gap in top_cold.items():
                        st.write(
                            f"- **{int(num)}** → {int(gap)} sorteos sin salir"
                        )
            else:
                st.write("No hay datos suficientes para calcular el momentum extendido.")

            # Curiosidades estrellas
            st.markdown(
                '<div class="neocard neocard--accent3">'
                '<p class="neocard-title">Curiosidades (estrellas)</p>'
                "</div>",
                unsafe_allow_html=True,
            )
            effective_window = min(window, len(df_stars_era))
            hot_cold_s = compute_hot_cold_stars(df_stars_era, window=effective_window)
            if hot_cold_s:
                st.write(
                    f"✨ Estrella más caliente (últimos {window}): "
                    f"**{hot_cold_s['hot_star']}** "
                    f"({hot_cold_s['hot_star_freq']} apariciones)"
                )
                st.write(
                    f"🧊 Estrella más atrasada: "
                    f"**{hot_cold_s['cold_star']}** "
                    f"(lleva {hot_cold_s['cold_gap']} sorteos sin salir)"
                )
            else:
                st.write("No hay datos suficientes.")

           # Curiosidades combinaciones repetidas (usando TODO el histórico)
            st.markdown(
                '<div class="neocard neocard--accent3">'
                '<p class="neocard-title">Curiosidades (combinaciones repetidas)</p>'
                "</div>",
                unsafe_allow_html=True,
            )

            # Para el resumen usamos el histórico completo df
            rep_df = compute_repeated_combinations(df)

            # (opcional) mostrar cuántas detecta para depurar
            st.caption(f"Combinaciones repetidas detectadas en el histórico: {len(rep_df)}")

            if rep_df.empty:
                st.write("No hay combinaciones repetidas en el histórico cargado.")
            else:
                # Nos aseguramos de que está ordenado por count descendente
                if "count" in rep_df.columns:
                    rep_df = rep_df.sort_values("count", ascending=False)

                max_rep = int(rep_df["count"].max())
                top_examples = rep_df.head(3)

                st.write(f"🏆 Máx repeticiones de una combinación: **{max_rep}** veces")

                for _, row in top_examples.iterrows():
                    nums = "-".join(str(int(row[f"n{i}"])) for i in range(1, 6))
                    estrellas = f"{int(row['s1'])}-{int(row['s2'])}"
                    st.write(
                        f"- Números: **{nums}** | Estrellas: **{estrellas}** "
                        f"→ {int(row['count'])} veces"
                    )

                # (muy útil para comprobar a ojo)
                st.markdown("##### Top 10 combinaciones repetidas")
                st.dataframe(rep_df.head(10))

                # Quintetos de números repetidos (ignorando estrellas)
                rep_nums = (
                    df.groupby(["n1", "n2", "n3", "n4", "n5"])
                    .size()
                    .reset_index(name="count")
                )
                rep_nums = rep_nums[rep_nums["count"] > 1].sort_values("count", ascending=False)

                if rep_nums.empty:
                    st.write("No hay quintetos de números repetidos en el histórico.")
                else:
                    top = rep_nums.head(3)
                    st.write(f"🔁 Quintetos de números repetidos (ignorando estrellas):")
                    for _, row in top.iterrows():
                        nums = "-".join(str(int(row[f"n{i}"])) for i in range(1, 6))
                        st.write(f"- **{nums}** → {int(row['count'])} apariciones")

            # Curiosidades sumas de los 5 números
            st.markdown(
                '<div class="neocard neocard--accent3">'
                '<p class="neocard-title">Curiosidades (sumas de los 5 números)</p>'
                "</div>",
                unsafe_allow_html=True,
            )
            if all(col in df_filtered.columns for col in ["n1", "n2", "n3", "n4", "n5"]):
                sums = df_filtered[["n1", "n2", "n3", "n4", "n5"]].sum(axis=1)
                total_draws = len(sums)
                if total_draws == 0:
                    st.write("No hay datos de sumas en el rango seleccionado.")
                else:
                    band_le_100 = sums <= 100
                    band_101_125 = sums.between(101, 125)
                    band_126_154 = sums.between(126, 154)
                    band_ge_155 = sums >= 155

                    def pct_simple(mask):
                        return round(mask.mean() * 100, 1)

                    p_le_100 = pct_simple(band_le_100)
                    p_101_125 = pct_simple(band_101_125)
                    p_126_154 = pct_simple(band_126_154)
                    p_ge_155 = pct_simple(band_ge_155)
                    median_sum = int(sums.median())

                    st.write(f"Mediana de la suma de los 5 números: **{median_sum}**")
                    st.markdown(
                        f"""
- 📉 Sumas muy bajas (≤ 100): **{p_le_100}%**  
- 🟡 Sumas medias-bajas (101–125): **{p_101_125}%**  
- ✅ Sumas medias-altas (126–154): **{p_126_154}%**  
- 🔺 Sumas altas (≥ 155): **{p_ge_155}%**
                        """
                    )
            else:
                st.write("No se pudieron calcular las sumas (faltan columnas n1–n5).")

        # --- Patrones de estructura (decenas, fechas, consecutivos) ---
        st.markdown(
            '<div class="neocard neocard--accent4">'
            '<p class="neocard-title">'
            'Patrones de estructura (decenas, fechas, consecutivos)'
            '</p></div>',
            unsafe_allow_html=True,
        )

        if len(df_filtered) == 0:
            st.write("No hay datos en el rango seleccionado.")
        else:
            nums_df = (
                df_filtered[["n1", "n2", "n3", "n4", "n5"]]
                .apply(pd.to_numeric, errors="coerce")
                .dropna()
            )

            if nums_df.empty:
                st.write("No se pudieron calcular los patrones (valores no numéricos o vacíos).")
            else:
                nums_arr = nums_df.to_numpy(dtype=int)

                distinct_decades_list = []
                max_same_decade_list = []
                fechas_count_list = []
                has_consec_list = []
                max_run_list = []

                for row in nums_arr:
                    decades = (row - 1) // 10
                    distinct_decades_list.append(len(np.unique(decades)))
                    counts_dec = np.bincount(decades, minlength=5)
                    max_same_decade_list.append(int(counts_dec.max()))

                    fechas_count_list.append(int((row <= 31).sum()))

                    sorted_row = np.sort(row)
                    current_run = 1
                    best_run = 1
                    has_pair = False
                    for i in range(1, len(sorted_row)):
                        if sorted_row[i] - sorted_row[i - 1] == 1:
                            has_pair = True
                            current_run += 1
                            if current_run > best_run:
                                best_run = current_run
                        else:
                            current_run = 1
                    has_consec_list.append(has_pair)
                    max_run_list.append(best_run)

                distinct_decades_arr = np.array(distinct_decades_list)
                max_same_decade_arr = np.array(max_same_decade_list)
                fechas_arr = np.array(fechas_count_list)
                has_consec_arr = np.array(has_consec_list)
                max_run_arr = np.array(max_run_list)

                def pct(mask: np.ndarray) -> float:
                    if mask.size == 0:
                        return 0.0
                    return round(mask.mean() * 100, 1)

                pct_3plus_decades = pct(distinct_decades_arr >= 3)
                pct_4plus_same_decade = pct(max_same_decade_arr >= 4)
                pct_all_le31 = pct(fechas_arr == 5)
                pct_4_le31 = pct(fechas_arr == 4)
                pct_no_consec = pct(~has_consec_arr)
                pct_with_pair = pct(has_consec_arr)
                pct_run3plus = pct(max_run_arr >= 3)
                pct_run4plus = pct(max_run_arr >= 4)

                col_pat1, col_pat2 = st.columns(2)

                with col_pat1:
                    st.markdown("**Decenas y “fechas” (≤31)**")
                    st.markdown(
                        f"""
- 🧩 Sorteos con ≥ 3 decenas distintas: **{pct_3plus_decades}%**  
- 🚫 Sorteos con ≥ 4 números en la misma decena: **{pct_4plus_same_decade}%**  
- 📅 Sorteos con 4 números ≤ 31: **{pct_4_le31}%**  
- ⛔ Sorteos con 5 números ≤ 31 (“fechas puras”): **{pct_all_le31}%**
                        """
                    )

                with col_pat2:
                    st.markdown("**Consecutivos en el sorteo**")
                    st.markdown(
                        f"""
- Sin consecutivos: **{pct_no_consec}%**  
- Con al menos un par consecutivo: **{pct_with_pair}%**  
- Con rachas de ≥ 3 consecutivos: **{pct_run3plus}%**  
- Con rachas de ≥ 4 consecutivos (vetadas en el generador): **{pct_run4plus}%**
                        """
                    )

                            # --- Top parejas de números (coocurrencias) ---
        st.markdown(
            '<div class="neocard neocard--accent6">'
            '<p class="neocard-title">Top parejas de números (coocurrencias)</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        if len(df_filtered) == 0:
            st.write("No hay datos en el rango seleccionado.")
        else:
            nums_df_pairs = (
                df_filtered[["n1", "n2", "n3", "n4", "n5"]]
                .apply(pd.to_numeric, errors="coerce")
                .dropna()
            )

            if nums_df_pairs.empty:
                st.write(
                    "No se pudieron calcular las parejas "
                    "(valores no numéricos o filas vacías)."
                )
            else:
                pair_counts: dict[tuple[int, int], int] = {}

                for _, row in nums_df_pairs.iterrows():
                    nums = sorted(int(x) for x in row.values.tolist())
                    # 5 números → 10 parejas
                    for i in range(5):
                        for j in range(i + 1, 5):
                            pair = (nums[i], nums[j])
                            pair_counts[pair] = pair_counts.get(pair, 0) + 1

                if not pair_counts:
                    st.write("No hay parejas repetidas en el rango seleccionado.")
                else:
                    pairs_df = (
                        pd.DataFrame(
                            [
                                {"a": a, "b": b, "count": c}
                                for (a, b), c in pair_counts.items()
                            ]
                        )
                        .sort_values("count", ascending=False)
                        .head(10)
                    )

                    st.write("Top 10 parejas de números más frecuentes:")
                    st.dataframe(pairs_df, hide_index=True)

        # --- Vista rápida del histórico (últimos 20) ---
        st.markdown(
            '<div class="neocard neocard--accent2">'
            '<p class="neocard-title">'
            'Vista del histórico (últimos 20 registros en rango)'
            '</p></div>',
            unsafe_allow_html=True,
        )
        df_sorted = df_filtered.sort_values("date")
        st.dataframe(df_sorted.tail(20))


with tab_gen:
    # Barra título Generador
    st.markdown(
        '<div class="neocard neocard--accent2">'
        '<p class="neocard-title">Generador de combinaciones A/B/C</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
            "Modo de generación",
            ["Estándar", "Momentum", "Rareza", "Experimental", "Game Theory"],
            index=0,
        )

    total_lines = st.slider("Total de líneas del bloque", 5, 25, 15, step=5)

    colA, colB = st.columns(2)
    with colA:
        lines_A = st.number_input(
            "Líneas Serie A",
            min_value=0,
            max_value=total_lines,
            value=5,
            step=1,
            format="%d",
        )
    with colB:
        max_B = total_lines - int(lines_A)
        lines_B = st.number_input(
            "Líneas Serie B",
            min_value=0,
            max_value=max_B,
            value=min(5, max_B),
            step=1,
            format="%d",
        )

    lines_A = int(lines_A)
    lines_B = int(lines_B)
    lines_C = int(total_lines - lines_A - lines_B)

    st.write(f"**Líneas Serie C (automático):** {lines_C}")
    st.caption(
        "Estándar aplica anti-clon con todo el histórico y rangos de suma A/B/C. "
        "Momentum favorece números/estrellas más frecuentes en el histórico. "
        "Rareza prioriza los menos frecuentes. Experimental mezcla ambos."
    )

    # --- Fila de botones: generar bloque / analizar manual ---
    # --- BOTONES DEL GENERADOR ---
    st.write("")  # pequeño espacio

    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        btn_generate = st.button(
            "🎲 Generar bloque de combinaciones",
            type="primary",
            key="btn_generate_block",
        )

    with col_btn2:
        btn_manual = st.button(
            "🧮 Analizar combinación manual",
            type="secondary",
            key="btn_manual_check",
        )

    # Lógica del botón GENERAR
    if btn_generate:
        block = generate_block(
            mode=mode,
            df_hist=df,
            lines_A=lines_A,
            lines_B=lines_B,
            lines_C=lines_C,
        )
        st.session_state["last_block"] = block  # si ya lo usas para guardar/guardar csv

        for serie in ["A", "B", "C"]:
            subset = [row for row in block if row["serie"] == serie]
            if not subset:
                continue
            st.markdown(f"### Serie {serie}")
            for row in subset:
                line_str = (
                    "Números: "
                    + "-".join(str(n) for n in row["nums"])
                    + " | Estrellas: "
                    + "-".join(str(s) for s in row["stars"])
                )
                st.code(line_str)

    # Lógica del botón ANALIZAR MANUAL
    if btn_manual:
        st.session_state["show_manual_checker"] = True

    # =========================================================
    # 1) GENERADOR AUTOMÁTICO (bloque A/B/C)
    # =========================================================

    block = st.session_state.get("last_block")
    meta = st.session_state.get("last_block_meta", {})

    if block:
        st.markdown("### Último bloque generado")
        st.markdown(
            f"_Modo_: **{meta.get('mode', '—')}** · "
            f"A: **{meta.get('lines_A', 0)}** · "
            f"B: **{meta.get('lines_B', 0)}** · "
            f"C: **{meta.get('lines_C', 0)}**"
        )

        for serie in ["A", "B", "C"]:
            subset = [row for row in block if row["serie"] == serie]
            if not subset:
                continue
            st.markdown(f"#### Serie {serie}")
            for row in subset:
                line_str = (
                    "Números: "
                    + "-".join(str(n) for n in row["nums"])
                    + " | Estrellas: "
                    + "-".join(str(s) for s in row["stars"])
                )
                st.code(line_str)

        if st.button("💾 Guardar este bloque"):
            added = save_block(
                block,
                mode=meta.get("mode", "Estándar"),
                note="",
            )
            st.success(
                f"Se han guardado {added} combinaciones en "
                "`data/combinaciones_generadas.csv`"
            )
    else:
        st.info("Genera un bloque para poder verlo y decidir si lo guardas.")

        # =========================================================
    # 2) COMBINACIÓN MANUAL
    # =========================================================
    st.markdown("### Combinación manual")

    # Inputs para 5 números y 2 estrellas
    num_cols = st.columns(5)
    manual_nums = []
    for i, col in enumerate(num_cols, start=1):
        with col:
            n_val = st.number_input(
                f"N{i}",
                min_value=1,
                max_value=50,
                value=i,
                step=1,
                key=f"manual_n{i}",
            )
            manual_nums.append(int(n_val))

    star_cols = st.columns(2)
    manual_stars = []
    for i, col in enumerate(star_cols, start=1):
        with col:
            s_val = st.number_input(
                f"E{i}",
                min_value=1,
                max_value=12,
                value=i,
                step=1,
                key=f"manual_s{i}",
            )
            manual_stars.append(int(s_val))

    if btn_manual:
        nums = sorted(manual_nums)
        stars = sorted(manual_stars)

        # Reiniciamos por si la combinación es inválida
        st.session_state["last_manual"] = None

        # Validaciones básicas
        if len(set(nums)) != 5:
            st.error("Los 5 números deben ser **distintos**.")
        elif len(set(stars)) != 2:
            st.error("Las 2 estrellas deben ser **distintas**.")
        else:
            # Clasificación por suma -> Serie A/B/C
            suma = sum(nums)
            serie_teorica = None
            rango_texto = ""
            for serie, (s_min, s_max) in SUM_RANGE_BY_SERIE.items():
                if s_min <= suma <= s_max:
                    serie_teorica = serie
                    rango_texto = f"[{s_min}–{s_max}]"
                    break

            if serie_teorica is None:
                st.warning(
                    f"📏 Suma de los 5 números: **{suma}** → "
                    "fuera de los rangos A/B/C (100–158)."
                )
            else:
                st.success(
                    f"📏 Suma de los 5 números: **{suma}** → "
                    f"caería en **Serie {serie_teorica}** {rango_texto}."
                )

            # Comprobación contra histórico
            mask_nums = (
                (df["n1"] == nums[0])
                & (df["n2"] == nums[1])
                & (df["n3"] == nums[2])
                & (df["n4"] == nums[3])
                & (df["n5"] == nums[4])
            )
            mask_full = (
                mask_nums
                & (df["s1"] == stars[0])
                & (df["s2"] == stars[1])
            )

            df_full = df[mask_full]
            df_nums = df[mask_nums]

            if not df_full.empty:
                # Combinación completa 5+2 ya salió
                fechas = df_full["date"].dt.strftime("%d/%m/%Y").tolist()
                st.error(
                    "⚠️ Esta combinación **completa** (5 números + 2 estrellas) "
                    "ya ha salido en el histórico."
                )
                st.write("Fechas:")
                for f in fechas:
                    st.write(f"-", f)
            elif not df_nums.empty:
                # Quinteto ya visto con otras estrellas
                fechas = df_nums["date"].dt.strftime("%d/%m/%Y").tolist()
                st.warning(
                    "🔁 Estos **5 números** ya han salido en el histórico "
                    "(con otras estrellas)."
                )
                st.write("Fechas:")
                for f in fechas:
                    st.write(f"-", f)
            else:
                st.success(
                    "✅ Quinteto de números y pareja de estrellas **inéditos** "
                    "en el histórico cargado."
                )

            # Guardamos la última combinación manual válida en sesión
            st.session_state["last_manual"] = {
                "nums": nums,
                "stars": stars,
                "serie": serie_teorica,  # puede ser None si está fuera de rango
                "sum": suma,
            }

    # Botón para guardar la última combinación manual válida
    manual_data = st.session_state.get("last_manual")
    if manual_data:
        if st.button("💾 Guardar combinación manual"):
            serie_guardada = manual_data["serie"] or "M"  # "M" si está fuera de A/B/C
            block_manual = [
                {
                    "serie": serie_guardada,
                    "nums": manual_data["nums"],
                    "stars": manual_data["stars"],
                }
            ]
            added = save_block(
                block_manual,
                mode="Manual",
                note=f"Introducida a mano; suma={manual_data['sum']}",
            )
            st.success(
                f"Combinación manual guardada en "
                "`data/combinaciones_generadas.csv` "
                f"(serie={serie_guardada}, suma={manual_data['sum']})."
            )
    else:
        st.caption("Introduce una combinación y pulsa “Analizar combinación manual” para poder guardarla.")

# -------------------------------------------------------------------
# ✅ TAB: COMPROBAR RESULTADOS
# -------------------------------------------------------------------
with tab_check:
    st.markdown(
        '<div class="neocard neocard--accent3">'
        '<p class="neocard-title">Comprobar último sorteo vs. combinaciones guardadas</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    if df.empty or "date" not in df.columns:
        st.error("No se pudieron cargar los datos históricos.")
    else:
        # Último sorteo del histórico
        df_sorted = df.sort_values("date")
        last_row = df_sorted.iloc[-1]

        fecha = last_row["date"].strftime("%d/%m/%Y")
        nums_draw = [int(last_row[f"n{i}"]) for i in range(1, 6)]
        stars_draw = [int(last_row[f"s{i}"]) for i in range(1, 3)]

        st.markdown("### Último sorteo disponible")
        st.write(f"📅 Fecha: **{fecha}**")
        st.write(
            "🎟️ Combinación ganadora: "
            f"**{'-'.join(map(str, nums_draw))}** | "
            f"Estrellas: **{'-'.join(map(str, stars_draw))}**"
        )

        # Cargamos combinaciones generadas y guardadas
        combos_df = load_last_n(5000)  # puedes subir/bajar este número si quieres

        if combos_df.empty:
            st.info(
                "Todavía no hay combinaciones guardadas en "
                "`data/combinaciones_generadas.csv`."
            )
        else:
            # --- Normalizar columnas para trabajar siempre con n1..n5 y s1..s2 ---

            # Caso 1: formato antiguo -> 'numbers' y 'stars' como strings "12-13-25-26-47", "3-12"
            if "numbers" in combos_df.columns and "stars" in combos_df.columns:
                # Separar numbers en n1..n5
                nums_split = combos_df["numbers"].astype(str).str.split("-", expand=True)
                # Aseguramos 5 columnas
                if nums_split.shape[1] == 5:
                    nums_split.columns = [f"n{i}" for i in range(1, 6)]
                    combos_df = pd.concat([combos_df, nums_split], axis=1)
                    combos_df[[f"n{i}" for i in range(1, 6)]] = combos_df[
                        [f"n{i}" for i in range(1, 6)]
                    ].astype(int)

                # Separar stars en s1..s2
                stars_split = combos_df["stars"].astype(str).str.split("-", expand=True)
                if stars_split.shape[1] == 2:
                    stars_split.columns = ["s1", "s2"]
                    combos_df = pd.concat([combos_df, stars_split], axis=1)
                    combos_df[["s1", "s2"]] = combos_df[["s1", "s2"]].astype(int)

            # Caso 2: por si en el futuro ya guardamos directamente n1..n5, s1..s2
            # (o si vienen en mayúsculas N1..N5, E1/E2)
            rename_map = {}
            if "N1" in combos_df.columns and "n1" not in combos_df.columns:
                rename_map.update(
                    {
                        "N1": "n1",
                        "N2": "n2",
                        "N3": "n3",
                        "N4": "n4",
                        "N5": "n5",
                    }
                )
            if "S1" in combos_df.columns and "s1" not in combos_df.columns:
                rename_map.update({"S1": "s1", "S2": "s2"})
            if "E1" in combos_df.columns and "s1" not in combos_df.columns:
                rename_map.update({"E1": "s1", "E2": "s2"})

            if rename_map:
                combos_df = combos_df.rename(columns=rename_map)

            required_cols = {"n1", "n2", "n3", "n4", "n5", "s1", "s2"}
            if not required_cols.issubset(combos_df.columns):
                st.error(
                    "El archivo `combinaciones_generadas.csv` no tiene las columnas "
                    "esperadas (n1–n5, s1–s2) ni se ha podido derivarlas de "
                    "`numbers`/`stars`. Columnas actuales: "
                    f"{list(combos_df.columns)}"
                )
            else:
                st.markdown("### Comparación con tus combinaciones guardadas")

                nums_draw_set = set(nums_draw)
                stars_draw_set = set(stars_draw)

                def compute_hits(row: pd.Series) -> pd.Series:
                    nums_combo = {int(row[f"n{i}"]) for i in range(1, 6)}
                    stars_combo = {int(row[f"s{i}"]) for i in range(1, 3)}

                    matched_nums = sorted(nums_draw_set & nums_combo)
                    matched_stars = sorted(stars_draw_set & stars_combo)

                    return pd.Series(
                        {
                            "aciertos_numeros": len(matched_nums),
                            "aciertos_estrellas": len(matched_stars),
                            "nums_coinciden": "-".join(map(str, matched_nums))
                            if matched_nums
                            else "",
                            "estrellas_coinciden": "-".join(map(str, matched_stars))
                            if matched_stars
                            else "",
                        }
                    )

                combos_df = combos_df.copy()
                hits_df = combos_df.apply(compute_hits, axis=1)
                combos_df = pd.concat([combos_df, hits_df], axis=1)

                # --- Resumen por categoría de aciertos ---
                resumen = (
                    combos_df.groupby(["aciertos_numeros", "aciertos_estrellas"])
                    .size()
                    .reset_index(name="lineas")
                    .sort_values(
                        ["aciertos_numeros", "aciertos_estrellas"], ascending=False
                    )
                )

                st.markdown("#### Resumen de aciertos (números + estrellas)")
                st.dataframe(resumen)

                # --- Plenos (5+2) si los hubiera ---
                exactos = combos_df[
                    (combos_df["aciertos_numeros"] == 5)
                    & (combos_df["aciertos_estrellas"] == 2)
                ]

                if exactos.empty:
                    st.success(
                        "✅ No hay pleno **5+2** en tus combinaciones guardadas "
                        "para el último sorteo."
                    )
                else:
                    st.error(
                        "⚠️ ¡Hay al menos un pleno **5+2** en tus combinaciones guardadas!"
                    )
                    st.dataframe(
                        exactos[
                            [
                                "timestamp",
                                "mode",
                                "serie",
                                "n1",
                                "n2",
                                "n3",
                                "n4",
                                "n5",
                                "s1",
                                "s2",
                                "aciertos_numeros",
                                "aciertos_estrellas",
                                "nums_coinciden",
                                "estrellas_coinciden",
                            ]
                        ]
                    )

                # --- Top 20 combinaciones que aciertan algo ---
                st.markdown(
                    "#### Top 20 combinaciones que más se acercan al último sorteo"
                )

                mask_acierto = (combos_df["aciertos_numeros"] > 0) | (
                    combos_df["aciertos_estrellas"] > 0
                )
                combos_con_acierto = combos_df[mask_acierto]

                if combos_con_acierto.empty:
                    st.info(
                        "Ninguna combinación guardada acierta números ni estrellas "
                        "en este sorteo."
                    )
                else:
                    top_hits = combos_con_acierto.sort_values(
                        ["aciertos_numeros", "aciertos_estrellas"],
                        ascending=False,
                    ).head(20)

                    st.dataframe(
                        top_hits[
                            [
                                "timestamp",
                                "mode",
                                "serie",
                                "n1",
                                "n2",
                                "n3",
                                "n4",
                                "n5",
                                "s1",
                                "s2",
                                "aciertos_numeros",
                                "aciertos_estrellas",
                                "nums_coinciden",
                                "estrellas_coinciden",
                            ]
                        ]
                    )

# -------------------------------------------------------------------
# 🎛 TAB: SIMULADOR MONTE CARLO
# -------------------------------------------------------------------
with tab_sim:
    st.markdown(
        '<div class="neocard neocard--accent2">'
        '<p class="neocard-title">Simulador Monte Carlo de estrategias</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.write(
        "Simula muchos sorteos hipotéticos para ver cómo se comporta cada modo "
        "(Estándar, Momentum, Rareza, Experimental, Game Theory) a largo plazo."
    )

    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        sim_mode = st.selectbox(
            "Modo a simular",
            ["Estándar", "Momentum", "Rareza", "Experimental", "Game Theory"],
            index=0,
        )

        sim_total_lines = st.slider(
            "Líneas por bloque en la simulación",
            5,
            25,
            15,
            step=5,
        )

        sim_lines_A = st.number_input(
            "Líneas Serie A (simulación)",
            min_value=0,
            max_value=sim_total_lines,
            value=5,
            step=1,
            format="%d",
        )
        max_B_sim = sim_total_lines - int(sim_lines_A)
        sim_lines_B = st.number_input(
            "Líneas Serie B (simulación)",
            min_value=0,
            max_value=max_B_sim,
            value=min(5, max_B_sim),
            step=1,
            format="%d",
        )

    with col_sim2:
        sim_n_trials = st.slider(
            "Número de sorteos simulados (trials)",
            100,
            5000,
            1000,
            step=100,
        )
        st.caption(
            "Cada trial genera un bloque A/B/C con el modo elegido y un sorteo "
            "real aleatorio como referencia. Se calcula cuántos aciertos harían tus líneas."
        )

    sim_lines_A = int(sim_lines_A)
    sim_lines_B = int(sim_lines_B)
    sim_lines_C = int(sim_total_lines - sim_lines_A - sim_lines_B)

    st.write(
        f"**Configuración simulada** → A: {sim_lines_A} · "
        f"B: {sim_lines_B} · C: {sim_lines_C} (total {sim_total_lines} líneas)"
    )

    # ---- EJECUTAR SIMULACIÓN Y GUARDAR RESULTADO EN SESSION_STATE ----
    if st.button("⚙️ Ejecutar simulación Monte Carlo"):
        if sim_total_lines <= 0:
            st.error("Debes tener al menos 1 línea en total para simular.")
        else:
            with st.spinner("Simulando… (puede tardar unos segundos)"):
                dist_df, summary = simulate_strategy(
                    mode=sim_mode,
                    df_hist=df,
                    n_trials=sim_n_trials,
                    lines_A=sim_lines_A,
                    lines_B=sim_lines_B,
                    lines_C=sim_lines_C,
                )

            st.session_state["sim_result"] = {
                "mode": sim_mode,
                "dist": dist_df,
                "summary": summary,
                "lines_A": sim_lines_A,
                "lines_B": sim_lines_B,
                "lines_C": sim_lines_C,
                "n_trials": sim_n_trials,
            }

    # ---- MOSTRAR RESULTADOS SI HAY ALGO EN SESSION_STATE ----
    sim_state = st.session_state.get("sim_result")

    if sim_state:
        mode_used = sim_state["mode"]
        dist_df = sim_state["dist"]
        summary = sim_state["summary"]
        sim_lines_A = sim_state["lines_A"]
        sim_lines_B = sim_state["lines_B"]
        sim_lines_C = sim_state["lines_C"]
        sim_n_trials = sim_state["n_trials"]

        st.markdown(f"### Distribución de aciertos – modo **{mode_used}**")

        if dist_df.empty:
            st.warning("La simulación no devolvió resultados (dist vacía).")
        else:
            st.dataframe(
                dist_df,
                hide_index=True,
                use_container_width=True,
            )

            # Gráfico: número de veces por patrón X+Y
            dist_plot = dist_df.copy()
            dist_plot["patron"] = (
                dist_plot["aciertos_numeros"].astype(str)
                + "+"
                + dist_plot["aciertos_estrellas"].astype(str)
            )
            st.bar_chart(
                dist_plot.set_index("patron")["veces"],
                use_container_width=True,
            )

        # ---- RESUMEN DEL MODO ACTUAL ----
        st.markdown("#### Resumen del modo simulado")

        resumen_df = pd.DataFrame(
            [
                {
                    "modo": mode_used,
                    "líneas simuladas": summary.get("total_lines", 0),
                    "P(≥3 números) %": round(summary.get("p_ge3_nums", 0.0) * 100, 3),
                    "P(al menos un premio) %": round(
                        summary.get("p_any_prize", 0.0) * 100, 3
                    ),
                }
            ]
        )
        st.dataframe(resumen_df, hide_index=True, use_container_width=True)

        # ---- COMPARACIÓN ENTRE MODOS ----
        st.markdown("### Comparación rápida entre modos")
        compare_all = st.checkbox(
            "Calcular también Estándar, Momentum, Rareza, Experimental y Game Theory",
            value=True,
        )

        if compare_all:
            modes_to_compare = [
                "Estándar",
                "Momentum",
                "Rareza",
                "Experimental",
                "Game Theory",
            ]

            rows = []
            for m in modes_to_compare:
                dist_m, summary_m = simulate_strategy(
                    mode=m,
                    df_hist=df,
                    n_trials=sim_n_trials,
                    lines_A=sim_lines_A,
                    lines_B=sim_lines_B,
                    lines_C=sim_lines_C,
                )
                rows.append(
                    {
                        "modo": m,
                        "líneas simuladas": summary_m.get("total_lines", 0),
                        "P(≥3 números) %": round(summary_m.get("p_ge3_nums", 0.0) * 100, 3),
                        "P(al menos un premio) %": round(
                            summary_m.get("p_any_prize", 0.0) * 100, 3
                        ),
                    }
                )

            comp_df = pd.DataFrame(rows)
            st.dataframe(comp_df, hide_index=True, use_container_width=True)

            st.caption(
                "Interpretación: cuanto mayor sea `P(≥3 números)` y, sobre todo, "
                "`P(al menos un premio)`, mejor se comporta la estrategia en estas "
                f"{sim_n_trials} simulaciones con bloques de "
                f"{sim_lines_A}+{sim_lines_B}+{sim_lines_C} líneas."
            )
    else:
        st.info("Lanza una simulación para ver la distribución de aciertos y la comparación entre modos.")