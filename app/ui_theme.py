# app/ui_theme.py
import streamlit as st

NEOBRUTALIST_CSS = """
<style>
:root {
  --primary-bg: #fdfdfd;
  --accent-1: #ffde59;  /* amarillo vivo */
  --accent-2: #5de4c7;  /* verde menta */
  --accent-3: #ff6b6b;  /* rojo coral */
  --accent-4: #4d7fff;  /* azul intenso */
  --card-radius: 14px;
  --card-border: 3px solid #111111;
}

body {
  background-color: var(--primary-bg);
}

/* Contenedor principal */
.block-container {
  padding-top: 2rem;
}

/* Tarjetas base */
.neocard {
  border: var(--card-border);
  border-radius: var(--card-radius);
  padding: 1rem 1.2rem;
  box-shadow: 6px 6px 0 #111111;
  background-color: #ffffff;
  margin-bottom: 1rem;
}

.neocard--accent1 { background-color: var(--accent-1); }
.neocard--accent2 { background-color: var(--accent-2); }
.neocard--accent3 { background-color: var(--accent-3); }
.neocard--accent4 { background-color: var(--accent-4); }

/* Títulos */
h1, h2, h3 {
  font-weight: 800 !important;
  letter-spacing: 0.03em;
}

/* Sidebar */
[data-testid="stSidebar"] {
  border-right: 3px solid #111111;
  background-color: #f4f4f4;
}

/* Botones */
.stButton>button {
  border-radius: 999px;
  border: 3px solid #111111;
  box-shadow: 4px 4px 0 #111111;
  font-weight: 700;
}
</style>
"""

def inject_neobrutalist_theme():
    st.markdown(NEOBRUTALIST_CSS, unsafe_allow_html=True)
