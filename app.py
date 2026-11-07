import streamlit as st
import pandas as pd
from PIL import Image
from pyzbar.pyzbar import decode
import os

# --- CONFIGURACION ---
st.set_page_config(page_title="RANSA - EXISTENCIA", layout="wide")

# --- ESTILO ---
st.markdown("""
<style>
    .main { background-color: #ffffff; }
    div.stButton > button { background-color: #FFC500; color: black; font-weight: bold; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- HEADER CON LOGO ---
col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    # Si tenés logo.png en GitHub lo muestra, si no, muestra a&p en amarillo
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
# Tu archivo de inventario debe llamarse inventario.xlsx y estar en GitHub
@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df = pd.read_excel("inventario.xlsx")
        # Limpiamos nombres de columnas
        df.columns = [c.strip().upper() for c in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.warning("No se encontró inventario.xlsx. Subilo a GitHub con ese nombre.")
    st.stop()

# Detectamos columnas automáticamente
col_codigo = [c for c in df.columns if 'COD' in c][0] if any('COD' in c for c in df.columns) else df.columns[0]
col_desc = [c for c in df.columns if 'DESC' in c or 'PRODUCTO' in c or 'NOMBRE' in c][0] if any('DESC' in c or 'PRODUCTO' in c or 'NOMBRE' in c for c in df.columns) else df.columns[1]
col_exis = [c for c in df.columns if 'EXIST' in c or 'STOCK' in c or 'CANT' in c][0] if any('EXIST' in c or 'STOCK' in c or 'CANT' in c for c in df.columns) else df.columns[-1]

# --- ESCANER DE CODIGO DE BARRAS ---
st.subheader("📷 Escanear código de barras")

# Inicializamos el buscador en session_state
if 'buscador' not in st.session_state:
    st.session_state['buscador'] = ""

usar_camara = st.checkbox("Activar cámara para escanear")

if usar_camara:
    foto = st.camera_input("Apuntá al código de barras y tomá la foto")
    if foto:
        imagen = Image.open(foto)
        codigos = decode(imagen)
        if codigos:
            codigo_escaneado = codigos[0].data.decode('utf-8')
            st.success(f"✅ Código detectado: {codigo_escaneado}")
            st.session_state['buscador'] = codigo_escaneado
        else:
            st.warning("⚠️ No se pudo leer el código, intentá con más luz y que no esté arrugado")

# --- BUSCADOR ---
st.subheader("🔍 Buscar producto")
busqueda = st.text_input(
    "Escribí código o descripción, o escaneá arriba:",
    value=st.session_state['buscador'],
    key="input_busqueda",
    placeholder="Ej: 12345 o Jugo de Naranja..."
)

# Si el usuario escribe, actualizamos buscador
if busqueda != st.session_state['buscador']:
    st.session_state['buscador'] = busqueda

# --- FILTRAR ---
if st.session_state['buscador']:
    texto = str(st.session_state['buscador']).lower().strip()
    # Busca en código o descripción
    df_filtrado = df[
        df[col_codigo].astype(str).str.lower().str.contains(texto, na=False) |
        df[col_desc].astype(str).str.lower().str.contains(texto, na=False)
    ]
else:
    df_filtrado = df

# --- MOSTRAR RESULTADOS ---
st.write(f"**{len(df_filtrado)} productos encontrados**")

# Mostramos solo columnas importantes
st.dataframe(
    df_filtrado,
    use_container_width=True,
    hide_index=True
)

# Botón para limpiar
if st.button("🔄 Limpiar búsqueda"):
    st.session_state['buscador'] = ""
    st.rerun()

st.caption("App RANSA - Existencia en vivo | Datos actualizados cada 60 segundos")
