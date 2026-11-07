import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="RANSA - EXISTENCIA", layout="wide")
st.title("RANSA • EXISTENCIA")
st.caption("RANSA • BUSCADOR EN VIVO")
st.divider()

# --- BOTON PARA SUBIR ARCHIVO ---
archivo_subido = st.file_uploader("📂 Subir inventario.xlsx", type=["xlsx","xls"])

@st.cache_data(ttl=60)
def cargar_datos(archivo):
    if archivo is not None:
        df = pd.read_excel(archivo, header=1)
    else:
        if not os.path.exists("inventario.xlsx"):
            return pd.DataFrame()
        df = pd.read_excel("inventario.xlsx", header=1)
    # Limpiar nombres: quitar espacios, tildes, mayúsculas
    df.columns = [str(c).strip().upper().replace("  "," ").replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U") for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains('UNNAMED')]
    df = df.dropna(how='all')
    if 'CODIGO' in df.columns:
        df = df[df['CODIGO'].notna()]
    return df

df = cargar_datos(archivo_subido)

if df.empty:
    st.warning("Subí tu archivo inventario.xlsx para ver la existencia")
    st.stop()

# --- BUSCAR NOMBRES REALES EN TU EXCEL ---
def buscar(palabras):
    for c in df.columns:
        for p in palabras:
            if p in c:
                return c
    return None

# Mapeo a lo que vos querés ver
col_codigo = buscar(['CODIGO'])
col_ean = buscar(['EAN'])
col_ucajas = buscar(['U CAJAS', 'UCAJAS'])
col_cajas = buscar(['TOTAL CAJAS', 'CAJAS'])
# Si U CAJAS y CAJAS son la misma, buscamos la otra
if col_ucajas == col_cajas:
    col_cajas = None
    for c in df.columns:
        if 'CAJAS' in c and c != col_ucajas:
            col_cajas = c
            break
col_unidades = buscar(['UNIDADES', 'DISPONIBLE', 'UNID'])
col_prep = buscar(['PREPARACION', 'PREPARA'])
col_fam = buscar(['FAMILIA'])
col_bloq = buscar(['BLOQUEADO', 'BLOQ'])

# Si no encuentra CAJAS, usa UCAJAS para no dejar vacío
if not col_cajas:
    col_cajas = col_ucajas

# Limpiar números para que sumen bien
for col in [col_ucajas, col_cajas, col_unidades]:
    if col and col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# --- BUSCADOR ---
busqueda = st.text_input("🔍 Buscar por CODIGO / EAN / DESCRIPCION", placeholder="Ej: 388151, 75010..., CORN FLAKES...")
if busqueda:
    texto = str(busqueda).lower().strip()
    df_f = df[df.astype(str).apply(lambda row: row.str.lower().str.contains(texto, na=False).any(), axis=1)]
    col_desc = buscar(['DESCRIPCION', 'DESCRIP'])
else:
    df_f = df.copy()

# --- FAMILIA ---
if col_fam:
    familias = ["Todas"] + sorted(df[col_fam].dropna().astype(str).unique().tolist())
    fam_sel = st.selectbox("FAMILIA", familias)
    if fam_sel != "Todas":
        df_f = df_f[df_f[col_fam].astype(str) == fam_sel]

# --- CHECKS ---
solo_criticos = st.checkbox("Solo ver CRITICOS y AGOTADOS")
if solo_criticos and col_unidades:
    df_f = df_f[df_f[col_unidades] <= 50]

solo_bloq = st.checkbox("Solo ver BLOQUEADOS")
if solo_bloq and col_bloq:
    df_f = df_f[df_f[col_bloq].astype(str).str.contains('BLOQ', case=False, na=False)]

# --- NUMEROTES ---
c1, c2, c3 = st.columns(3)
with c1:
    st.write("UNID. DISPONIBLE")
    val = int(df_f[col_unidades].sum()) if col_unidades else 0
    st.markdown(f"<h1 style='margin-top:-15px'>{val:,}</h1>", unsafe_allow_html=True)
with c2:
    st.write("TOTAL CAJAS")
    val2 = int(df_f[col_cajas].sum()) if col_cajas else 0
    st.markdown(f"<h1 style='margin-top:-15px'>{val2:,}</h1>", unsafe_allow_html=True)
with c3:
    st.write("AGOTADOS")
    agot = int((df_f[col_unidades]==0).sum()) if col_unidades else 0
    st.markdown(f"<h1 style='margin-top:-15px'>{agot}</h1>", unsafe_allow_html=True)

st.divider()
st.write(f"**{len(df_f)} productos encontrados**")

# --- TABLA EXACTA QUE PEDISTE ---
# CODIGO, EAN, DESCRIPCION, CAJAS, UNIDADES, PREPARACIÓN
orden = [col_codigo, col_ean, col_desc, col_cajas, col_unidades, col_prep]

# Renombrar para que se vea bonito
nombres_bonitos = {}
if col_codigo: nombres_bonitos[col_codigo] = "CODIGO"
if col_ean: nombres_bonitos[col_ean] = "EAN"
if col_desc: nombres_bonitos[col_desc] = "DESCRIPCION"
if col_cajas: nombres_bonitos[col_cajas] = "CAJAS"
if col_unidades: nombres_bonitos[col_unidades] = "UNIDADES"
if col_prep: nombres_bonitos[col_prep] = "PREPARACIÓN"

orden_final = [c for c in orden if c and c in df_f.columns]
# Si falta alguna columna, avisar
if len(orden_final) < 6:
    st.info(f"Columnas encontradas: {orden_final}. Si falta alguna, revisá que en tu Excel se llame igual: CODIGO, EAN, U CAJAS, CAJAS, UNIDADES, PREPARACION")

df_mostrar = df_f[orden_final].rename(columns=nombres_bonitos)
st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
