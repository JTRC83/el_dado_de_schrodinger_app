# app.py
import random

import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

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


st.set_page_config(page_title="El dado de Schrödinger", layout="wide")
inject_neobrutalist_theme()


@st.cache_data
def get_data() -> pd.DataFrame:
    return load_raw_data()


# --- SIDEBAR ---
CAT_IMAGE_PATH = "assets/gato_dado.png"  # imagen gato
st.sidebar.image(CAT_IMAGE_PATH, use_container_width=True)

st.sidebar.title("El dado de Schrödinger")
st.sidebar.caption("Panel Euromillones")



if st.sidebar.button("🔄 Actualizar histórico desde la API"):
    try:
        added = update_historico_from_api()
        get_data.clear()
        if added == 0:
            st.sidebar.success("Histórico ya estaba actualizado.")
        else:
            st.sidebar.success(f"Actualizado: {added} sorteos nuevos.")
    except Exception as e:
        st.sidebar.error(f"Error al actualizar: {e}")

df = get_data()

st.title("El dado de Schrödinger – Panel Euromillones")

tab_hist, tab_gen = st.tabs(["📊 Explorador histórico", "🎲 Generador A/B/C"])

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
                '<div class="neocard">'
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
                .properties(height=300)
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
                '<div class="neocard">'
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
                    .properties(height=250)
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
                '<div class="neocard">'
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

                # Números "fríos" por gap de sorteos sin salir en TODO el rango
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
                '<div class="neocard neocard--accent4">'
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

            # Curiosidades combinaciones repetidas
            st.markdown(
                '<div class="neocard neocard--accent5">'
                '<p class="neocard-title">Curiosidades (combinaciones repetidas)</p>'
                "</div>",
                unsafe_allow_html=True,
            )
            rep_df = compute_repeated_combinations(df_filtered)
            if rep_df.empty:
                st.write("No hay combinaciones repetidas en el rango seleccionado.")
            else:
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

            # Curiosidades sumas de los 5 números
            st.markdown(
                '<div class="neocard neocard--accent6">'
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
            '<div class="neocard">'
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
            '<div class="neocard">'
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
            '<div class="neocard">'
            '<p class="neocard-title">'
            'Vista del histórico (últimos 20 registros en rango)'
            '</p></div>',
            unsafe_allow_html=True,
        )
        df_sorted = df_filtered.sort_values("date")
        st.dataframe(df_sorted.tail(20))


# -------------------------------------------------------------------
# 🎲 TAB: GENERADOR A/B/C (v0)
# -------------------------------------------------------------------
with tab_gen:
    # Barra título Generador
    st.markdown(
        '<div class="neocard neocard--accent2">'
        '<p class="neocard-title">Generador de combinaciones A/B/C (v0)</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Modo de generación",
        ["Estándar", "Momentum (futuro)", "Rareza (futuro)", "Experimental (futuro)"],
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
        "Más adelante aquí meteremos todos los pesos, bandas de suma y reglas avanzadas."
    )

    def generar_linea_simple():
        nums = sorted(random.sample(range(1, 51), 5))
        stars = sorted(random.sample(range(1, 13), 2))
        return nums, stars

    if st.button("🎲 Generar bloque de combinaciones"):
        block = []
        for serie, n_lines in [("A", lines_A), ("B", lines_B), ("C", lines_C)]:
            for _ in range(n_lines):
                nums, stars = generar_linea_simple()
                block.append({"serie": serie, "nums": nums, "stars": stars})

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