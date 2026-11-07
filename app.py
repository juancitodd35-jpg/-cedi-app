import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="RANSA - EXISTENCIA", layout="wide")
st.title("RANSA • EXISTENCIA")
st.divider()

# --- 1. BOTON PARA CARGAR ARCHIVO ---
archivo_subido = st.file_uploader("📂 Cargar archivo inventario.xlsx", type=["xlsx", "xls"])

@st.cache_data(ttl=60)
def cargar(archivo):
    if archivo is not None:
        df = pd.read_excel(archivo, header=1)
    elif os.path.exists("inventario.xlsx"):
        df = pd.read_excel("inventario.xlsx", header=1)
    else:
        return pd.DataFrame()
    # Limpiar nombres: mayúsculas y sin espacios de más
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains('UNNAMED')]
    df = df.dropna(how='all')
    return df

df = cargar(archivo_subido)

if df.empty:
    st.warning("Subí tu inventario.xlsx para empezar")
    st.stop()

# --- 2. NOMBRES EXACTOS DE TU EXCEL (DE LA FOTO) ---
# Tu Excel tiene estas columnas:
# CODIGO | EAN | DESCRIPCION | CAJAS | UNIDADES | TOTAL CAJAS | TOTAL UNIDADES | EN PREPARACION | UNI. DISPONIBLES | U. BLOQUEADAS | C. BLOQUEADAS

col_codigo = 'CODIGO' if 'CODIGO' in df.columns else df.columns[0]
col_ean = 'EAN'
col_desc = 'DESCRIPCION'
# CAJAS que querés ver = TOTAL CAJAS
col_cajas = 'TOTAL CAJAS' if 'TOTAL CAJAS' in df.columns else 'CAJAS'
# UNIDADES DISPONIBLES = UNI. DISPONIBLES
col_disp = 'UNI. DISPONIBLES' if 'UNI. DISPONIBLES' in df.columns else 'UNIDADES'
col_bloq_u = 'U. BLOQUEADAS' if 'U. BLOQUEADAS' in df.columns else None
col_bloq_c = 'C. BLOQUEADAS' if 'C. BLOQUEADAS' in df.columns else None

# Números
for c in [col_cajas, col_disp, col_bloq_u, col_bloq_c]:
    if c and c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

# Quitar filas sin código
df = df[df[col_codigo].notna()]

# --- 3. ARRIBA: SOLO CODIGO CON DESCRIPCION ---
st.write("### Código de Proveedor")
# Lista: CODIGO - DESCRIPCION
df['CODIGO_DESC'] = df[col_codigo].astype(str) + " - " + df[col_desc].astype(str)
opcion = st.selectbox("Seleccionar código", ["Todos"] + sorted(df['CODIGO_DESC'].unique().tolist()))
if opcion != "Todos":
    codigo_sel = opcion.split(" - ")[0]
    df = df[df[col_codigo].astype(str) == codigo_sel]

# --- 4. BUSCADOR POR NOMBRE O POR CODIGO ---
busqueda = st.text_input("🔍 Buscar por nombre o por código", placeholder="Ej: 388151, CORN FLAKES, KELLOGS...")
if busqueda:
    texto = str(busqueda).lower().strip()
    df_f = df[
        df[col_codigo].astype(str).str.lower().str.contains(texto, na=False) |
        df[col_desc].astype(str).str.lower().str.contains(texto, na=False) |
        df[col_ean].astype(str).str.lower().str.contains(texto, na=False)
    ]
else:
    df_f = df.copy()

# --- 5. OPCIONES ---
c_check1, c_check2 = st.columns(2)
with c_check1:
    solo_criticos = st.checkbox("Solo ver CRITICOS o AGOTADOS")
with c_check2:
    solo_bloq = st.checkbox("Solo ver BLOQUEADOS")

if solo_criticos:
    # Critico = 50 o menos, Agotado = 0
    df_f = df_f[df_f[col_disp] <= 50]

if solo_bloq:
    # Bloqueado si tiene unidades o cajas bloqueadas
    cond = pd.Series(False, index=df_f.index)
    if col_bloq_u in df_f.columns:
        cond = cond | (df_f[col_bloq_u] > 0)
    if col_bloq_c in df_f.columns:
        cond = cond | (df_f[col_bloq_c] > 0)
    df_f = df_f[cond]

# --- 6. TOTALES (SIEMPRE DEL TOTAL, NO DEL FILTRO) ---
c1, c2 = st.columns(2)
with c1:
    st.write("TOTAL UNIDADES DISPONIBLES")
    st.markdown(f"<h1 style='margin-top:-15px'>{int(df[col_disp].sum()):,}</h1>", unsafe_allow_html=True)
with c2:
    st.write("TOTAL CAJAS")
    st.markdown(f"<h1 style='margin-top:-15px'>{int(df[col_cajas].sum()):,}</h1>", unsafe_allow_html=True)

st.divider()
st.write(f"**{len(df_f)} productos encontrados**")

# --- 7. TABLA FINAL ---
df_mostrar = pd.DataFrame()
df_mostrar['CODIGO'] = df_f[col_codigo]
df_mostrar['EAN'] = df_f[col_ean]
df_mostrar['DESCRIPCION'] = df_f[col_desc]
df_mostrar['CAJAS'] = df_f[col_cajas]
df_mostrar['UNIDADES DISPONIBLES'] = df_f[col_disp]

st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
