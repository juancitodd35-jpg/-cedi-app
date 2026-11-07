import streamlit as st
import pandas as pd
import os

# --- CONFIGURACION ---
st.set_page_config(page_title="RANSA - EXISTENCIA", layout="wide")

# --- HEADER ---
col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=100)
    else:
        st.markdown("""
        <div style="background-color:#FFC500; width:100px; height:100px; border-radius:15px; display:flex; align-items:center; justify-content:center; font-size:32px; font-weight:bold;">
        a&p
        </div>
        """, unsafe_allow_html=True)

with col_titulo:
    st.title("RANSA • EXISTENCIA")
    st.caption("RANSA • BUSCADOR EN VIVO")

st.divider()

# --- CARGAR DATOS ---
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        # header=1 le dice: saltate la primera fila de título, los encabezados están en la fila 2
        df = pd.read_excel("inventario.xlsx", header=1)
        df.columns = [str(c).strip().upper() for c in df.columns]
        # Borramos columnas vacías tipo UNNAMED
        df = df.loc[:, ~df.columns.str.contains('UNNAMED')]
        # Borramos filas totalmente vacías
        df = df.dropna(how='all')
        # Borramos filas donde no hay CODIGO
        if 'CODIGO' in df.columns:
            df = df[df['CODIGO'].notna()]
        return df
    except Exception as e:
        return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.warning("No se encontró inventario.xlsx. Subilo a GitHub con ese nombre.")
    st.stop()

# --- BUSCADOR SIMPLE ---
st.subheader("🔍 Buscar producto")
busqueda = st.text_input(
    "Escribí código o descripción:",
    placeholder="Ej: 12345 o Jugo de Naranja..."
)

if busqueda:
    texto = str(busqueda).lower().strip()
    df_filtrado = df[
        df.astype(str).apply(lambda row: row.str.lower().str.contains(texto, na=False).any(), axis=1)
    ]
else:
    df_filtrado = df

st.write(f"**{len(df_filtrado)} productos encontrados**")
st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

st.caption("App RANSA - Existencia en vivo")
