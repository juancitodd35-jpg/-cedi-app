import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="CEDI - EXISTENCIA", layout="wide")
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    st.image("logo.png", width=65)
with col_titulo:
    st.title("CEDI • EXISTENCIA")
st.caption("KELLOGG EL SALVADOR - Actualiza subiendo el Excel del día")

def normalizar(s):
    s = str(s).upper().strip()
    s = s.replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U")
    s = re.sub(r'[^A-Z0-9 ]',' ',s)
    s = re.sub(r'\s+',' ',s).strip()
    return s

def cargar_df(file):
    for h in [0,1,2,3]:
        try:
            df_tmp = pd.read_excel(file, header=h)
            cols = [normalizar(c) for c in df_tmp.columns.astype(str)]
            if "CODIGO" in cols and any("DISPONIBLE" in c for c in cols):
                df_tmp.columns = cols
                return df_tmp
        except:
            pass
    df = pd.read_excel(file, header=0)
    df.columns = [normalizar(c) for c in df.columns.astype(str)]
    return df

@st.cache_data
def cargar_base():
    try:
        return cargar_df("existencia.xlsx")
    except:
        return None

st.subheader("SUBIR EXCEL DEL DÍA (solo admin)")
uploaded = st.file_uploader("Upload", type=["xlsx","xls"], label_visibility="collapsed")
df = cargar_df(uploaded) if uploaded is not None else cargar_base()

if df is None:
    st.error("No se pudo cargar existencia.xlsx")
    st.stop()

cols = list(df.columns)
# MAPEO EXACTO SEGUN TU EXCEL - NO USAR COD PROVEE NI U CAJAS
def col_exacta(nombre):
    return nombre if nombre in cols else None
def col_con(palabra, excluir=[]):
    for c in cols:
        if palabra in c and all(e not in c for e in excluir):
            return c
    return None

col_cod = col_exacta("CODIGO")
col_ean = col_exacta("EAN")
col_desc = col_exacta("DESCRIPCION")
col_fam = col_exacta("FAMILIA")
# DISPONIBLE es UNI DISPONIBLE, NUNCA NO DISPONIBLE
col_disp = col_exacta("UNI DISPONIBLE")
if col_disp is None:
    col_disp = col_exacta("UNID DISPONIBLE")
if col_disp is None:
    col_disp = col_exacta("UNIDADES DISPONIBLE")
if col_disp is None:
    col_disp = col_con("DISPONIBLE", excluir=["NO"])
# CAJAS es TOTAL CAJAS, no U CAJAS ni CAJAS suelta
col_cajas = col_exacta("TOTAL CAJAS")
col_total_unid = col_exacta("TOTAL UNIDADES")
col_bloq = col_con("BLOQUEADAS")

if col_disp is None or col_cod is None:
    st.error(f"No encontré columnas. Columnas detectadas: {cols}")
    st.stop()

df = df.dropna(subset=[col_desc])
df[col_disp] = pd.to_numeric(df[col_disp], errors="coerce").fillna(0)
if col_cajas:
    df[col_cajas] = pd.to_numeric(df[col_cajas], errors="coerce").fillna(0)

# Buscador
st.subheader("🔍 Buscar por CODIGO / EAN / DESCRIPCION")
busqueda = st.text_input("", placeholder="Ej: 388151, 75010..., CORN FLAKES...", label_visibility="collapsed")

fam_opciones = ["Todas"]
if col_fam:
    fam_opciones += sorted(df[col_fam].dropna().astype(str).unique().tolist())
familia = st.selectbox("FAMILIA", fam_opciones)
solo_criticos = st.checkbox("Solo ver CRITICOS y AGOTADOS")
solo_bloq = st.checkbox("Solo ver BLOQUEADOS")

df_f = df.copy()
if busqueda:
    b = busqueda.upper().strip()
    mask = df_f[col_desc].astype(str).str.upper().str.contains(b, na=False)
    mask = mask | df_f[col_cod].astype(str).str.contains(b, na=False)
    if col_ean:
        mask = mask | df_f[col_ean].astype(str).str.contains(b, na=False)
    df_f = df_f[mask]
if familia != "Todas" and col_fam:
    df_f = df_f[df_f[col_fam].astype(str) == familia]
if solo_criticos:
    df_f = df_f[df_f[col_disp] <= 50]
if solo_bloq and col_bloq:
    df_f = df_f[pd.to_numeric(df_f[col_bloq], errors="coerce").fillna(0) > 0]

c1, c2, c3 = st.columns(3)
c1.metric("UNID. DISPONIBLE", f"{int(df_f[col_disp].sum()):,}")
if col_cajas:
    c2.metric("TOTAL CAJAS", f"{int(df_f[col_cajas].sum()):,}")
else:
    c2.metric("PRODUCTOS", f"{len(df_f):,}")
c3.metric("AGOTADOS", f"{int((df_f[col_disp]==0).sum()):,}")

mostrar = pd.DataFrame()
mostrar["CODIGO"] = df_f[col_cod]
mostrar["EAN"] = df_f[col_ean] if col_ean else ""
mostrar["DESCRIPCION"] = df_f[col_desc]
mostrar["DISPONIBLE"] = df_f[col_disp].astype(int)
if col_cajas:
    mostrar["TOTAL CAJAS"] = df_f[col_cajas].astype(int)
if col_fam:
    mostrar["FAMILIA"] = df_f[col_fam]

st.dataframe(mostrar, use_container_width=True, hide_index=True)
st.caption(f"Mostrando {len(mostrar)} productos")
