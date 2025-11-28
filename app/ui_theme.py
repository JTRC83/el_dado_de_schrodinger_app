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
  --accent-5: #ffb347;  /* naranja suave para combinaciones */
  --accent-6: #9cf594;  /* verde suave para sumas */
  --card-radius: 24px;
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
.neocard--accent5 { background-color: var(--accent-5); }
.neocard--accent6 { background-color: var(--accent-6); }

.neocard-title {
  font-size: 1.1rem;
  font-weight: 800;
  margin: 0;
  text-align: left;
}

/* Títulos */
h1, h2, h3 {
  font-weight: 900 !important;
  letter-spacing: 0.03em;
}

/* Sidebar */
[data-testid="stSidebar"] {
  border-right: 3px solid #111111;
  background-color: #f4f4f4;
}

[data-testid="stSidebar"] img {
  max-width: 180px;
  margin-top: 1rem;
  margin-bottom: 1rem;
}

/* Botones generales (contenido principal) */
.stButton>button {
  border-radius: 999px;
  border: 3px solid #111111;
  box-shadow: 4px 4px 0 #111111;
  font-weight: 700;
  background-color: #ffffff;
  color: #111111;
}

/* Botón de la SIDEBAR (Actualizar API) estilo "botón rojo" */
[data-testid="stSidebar"] .stButton > button {
  border-radius: 999px;
  padding: 0.8rem 1.8rem;
  border: 4px solid #111111;
  background: radial-gradient(circle at 30% 30%, #ff8080, #ff1f1f);
  color: #ffffff;
  font-weight: 800;
  font-size: 0.95rem;
  box-shadow: 6px 6px 0 #111111;
  transition: transform 0.05s ease-out,
              box-shadow 0.05s ease-out,
              filter 0.1s ease-out;
}

[data-testid="stSidebar"] .stButton > button:hover {
  filter: brightness(1.05);
  transform: translateY(1px);
  box-shadow: 4px 4px 0 #111111;
}

[data-testid="stSidebar"] .stButton > button:active {
  transform: translateY(3px);
  box-shadow: 2px 2px 0 #111111;
}
</style>
"""

def inject_neobrutalist_theme():
    st.markdown(NEOBRUTALIST_CSS, unsafe_allow_html=True)
