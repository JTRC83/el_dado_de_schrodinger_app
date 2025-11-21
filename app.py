# app.py
import random

import streamlit as st
import pandas as pd

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

        st.markdown('<div class="neocard neocard--accent1">', unsafe_allow_html=True)
        st.subheader("Filtros de rango")

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
        st.markdown("</div>", unsafe_allow_html=True)

        if isinstance(date_range, tuple) and len(date_range) == 2:
            start, end = date_range
            mask = (df["date"] >= pd.to_datetime(start)) & (df["date"] <= pd.to_datetime(end))
            df_filtered = df.loc[mask].copy()
        else:
            df_filtered = df.copy()

        # --- Resumen ---
        st.markdown('<div class="neocard neocard--accent2">', unsafe_allow_html=True)
        st.subheader("Resumen histórico")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Sorteos en rango", len(df_filtered))
        with c2:
            st.metric("Primera fecha", df_filtered["date"].min().strftime("%d/%m/%Y"))
        with c3:
            st.metric("Última fecha", df_filtered["date"].max().strftime("%d/%m/%Y"))
        st.markdown("</div>", unsafe_allow_html=True)

        # --- Frecuencias y curiosidades ---
        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.markdown('<div class="neocard">', unsafe_allow_html=True)
            st.subheader("Frecuencia de números (1–50)")
            main_freq = compute_main_number_freq(df_filtered)
            st.bar_chart(main_freq)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="neocard">', unsafe_allow_html=True)
            st.subheader("Frecuencia de estrellas (1–12)")
            star_freq = compute_star_freq(df_filtered)
            st.bar_chart(star_freq)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_right:
            st.markdown('<div class="neocard neocard--accent3">', unsafe_allow_html=True)
            st.subheader("Curiosidades (números)")
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
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="neocard neocard--accent4">', unsafe_allow_html=True)
            st.subheader("Curiosidades (estrellas)")
            hot_cold_s = compute_hot_cold_stars(df_filtered, window=window)
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
            st.markdown("</div>", unsafe_allow_html=True)

        # --- Combinaciones repetidas ---
        st.markdown('<div class="neocard">', unsafe_allow_html=True)
        st.subheader("Combinaciones repetidas")
        repeated = compute_repeated_combinations(df_filtered)
        min_count = st.slider("Mostrar combinaciones con al menos N repeticiones", 2, 5, 2)
        repeated_view = repeated[repeated["count"] >= min_count]
        st.dataframe(repeated_view)
        st.markdown("</div>", unsafe_allow_html=True)

        # --- Vista rápida del histórico ---
        st.markdown('<div class="neocard">', unsafe_allow_html=True)
        st.subheader("Vista del histórico (primeros 20 registros en rango)")
        st.dataframe(df_filtered.head(20))
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# 🎲 TAB: GENERADOR A/B/C (v0)
# -------------------------------------------------------------------
with tab_gen:
    st.markdown('<div class="neocard neocard--accent2">', unsafe_allow_html=True)
    st.subheader("Generador de combinaciones A/B/C (v0)")

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

    st.caption("Más adelante aquí meteremos todos los pesos, bandas de suma y reglas avanzadas.")

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

    st.markdown("</div>", unsafe_allow_html=True)
