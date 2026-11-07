import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="RANSA - EXISTENCIA", layout="wide")
st.title("RANSA • EXISTENCIA")
st.caption("RANSA • BUSCADOR EN VIVO")
st.divider()

@st.cache_data(ttl=60)
def cargar_datos():
    df = pd.read_excel("inventario.xlsx", header=1)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.loc[:, ~df.columns.str.contains('UNNAMED')]
    df = df.dropna(how='all')
    if 'CODIGO' in df.columns:
        df = df[df['CODIGO'].notna()]
    return df

df = cargar_datos()
if df.empty:
    st.warning("No se encontró inventario.xlsx")
    st.stop()

# --- BUSCAR NOMBRES REALES ---
def buscar_col(palabras):
    for c in df.columns:
        for p in palabras:
            if p in c:
                return c
    return None

col_disp = buscar_col(['DISPONIBLE'])
col_cajas = buscar_col(['TOTAL CAJAS', 'U CAJAS', 'CAJAS'])
col_bloq = buscar_col(['BLOQUEADO', 'BLOQ'])
col_fam = buscar_col(['FAMILIA'])
col_desc = buscar_col(['DESCRIPCION'])

# Limpiar números
if col_disp:
    df[col_disp] = pd.to_numeric(df[col_disp], errors='coerce').fillna(0)
if col_cajas:
    df[col_cajas] = pd.to_numeric(df[col_cajas], errors='coerce').fillna(0)

# --- BUSCADOR ---
busqueda = st.text_input("🔍 Buscar por CODIGO / EAN / DESCRIPCION", placeholder="Ej: 388151, 75010..., CORN FLAKES...")
if busqueda:
    texto = str(busqueda).lower().strip()
    df_f = df[df.astype(str).apply(lambda row: row.str.lower().str.contains(texto, na=False).any(), axis=1)]
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
if solo_criticos and col_disp:
    df_f = df_f[df_f[col_disp] <= 50]

solo_bloq = st.checkbox("Solo ver BLOQUEADOS")
if solo_bloq and col_bloq:
    df_f = df_f[df_f[col_bloq].astype(str).str.contains('BLOQ', case=False, na=False)]

# --- NUMEROTES ---
c1, c2, c3 = st.columns(3)
with c1:
    st.write("UNID. DISPONIBLE")
    st.markdown(f"<h1 style='margin-top:-15px'>{int(df_f[col_disp].sum()):,}</h1>" if col_disp else "0", unsafe_allow_html=True)
with c2:
    st.write("TOTAL CAJAS")
    st.markdown(f"<h1 style='margin-top:-15px'>{int(df_f[col_cajas].sum()):,}</h1>" if col_cajas else "0", unsafe_allow_html=True)
with c3:
    st.write("AGOTADOS")
    agot = int((df_f[col_disp]==0).sum()) if col_disp else 0
    st.markdown(f"<h1 style='margin-top:-15px'>{agot}</h1>", unsafe_allow_html=True)

st.divider()
st.write(f"**{len(df_f)} productos encontrados**")

# --- TABLA EN ORDEN DEL VIDEO ---
orden = ['CODIGO','EAN',col_desc,col_disp,col_cajas,col_fam,'PROVEEDOR','U PACKS','BLOQUEADO']
orden_final = []
for c in orden:
    if c and c in df_f.columns and c not in orden_final:
        orden_final.append(c)
for c in df_f.columns:
    if c not in orden_final:
        orden_final.append(c)

st.dataframe(df_f[orden_final], use_container_width=True, hide_index=True)
