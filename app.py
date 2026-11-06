import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="CEDI - EXISTENCIA", layout="wide")
st.title("📦 CEDI • EXISTENCIA")
st.caption("KELLOGG EL SALVADOR - Actualiza subiendo el Excel del día")

def normalizar(s):
    s = str(s).upper().strip()
    s = s.replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U")
    s = re.sub(r'[^A-Z0-9 ]',' ',s)
    s = re.sub(r'\s+',' ',s).strip()
    return s

def buscar_columna(cols_norm, palabras):
    for i, c in enumerate(cols_norm):
        for p in palabras:
            if p in c:
                return i
    return None

def cargar_df(file):
    # Intenta leer buscando la fila de encabezado real
    for h in [0,1,2,3]:
        try:
            df_tmp = pd.read_excel(file, header=h)
            cols = [normalizar(c) for c in df_tmp.columns.astype(str)]
            # Si encuentra CODIGO y DISPONIBLE en esa fila, esa es la buena
            if any("CODIGO" in c or "COD" in c for c in cols) and any("DISPONIBLE" in c or "DISP" in c for c in cols):
                df_tmp.columns = cols
                return df_tmp
        except:
            pass
    # Si no encontró, lee con header 1 por defecto
    df = pd.read_excel(file, header=1)
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

if uploaded is not None:
    df = cargar_df(uploaded)
else:
    df = cargar_base()

if df is None:
    st.error("No se pudo cargar existencia.xlsx")
    st.stop()

# Detectar columnas
cols = list(df.columns)
i_cod = buscar_columna(cols, ["CODIGO", "COD"])
i_ean = buscar_columna(cols, ["EAN", "BARRA"])
i_desc = buscar_columna(cols, ["DESCRIPCION", "DESCRIP", "PRODUCTO", "ARTICULO"])
i_disp = buscar_columna(cols, ["DISPONIBLE", "DISP", "EXISTENCIA"])
i_cajas = buscar_columna(cols, ["CAJA"])
i_fam = buscar_columna(cols, ["FAMILIA", "CATEGORIA", "LINEA"])

# Si no encontró DISPONIBLE, muestra qué columnas sí encontró para arreglarlo
if i_disp is None:
    st.error("No encontré la columna DISPONIBLE. Estas son las columnas que tiene tu Excel:")
    st.write(cols)
    st.stop()

col_cod = cols[i_cod] if i_cod is not None else cols[0]
col_desc = cols[i_desc] if i_desc is not None else cols[1]
col_disp = cols[i_disp]
col_cajas = cols[i_cajas] if i_cajas is not None else None
col_fam = cols[i_fam] if i_fam is not None else None
col_ean = cols[i_ean] if i_ean is not None else None

# Limpiar datos
df = df.dropna(subset=[col_disp])
df[col_disp] = pd.to_numeric(df[col_disp], errors="coerce").fillna(0)

# Buscador
st.subheader("🔍 Buscar por CODIGO / EAN / DESCRIPCION")
busqueda = st.text_input("", placeholder="Ej: 388151, 75010..., CORN FLAKES...", label_visibility="collapsed")

# Filtros
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
    if col_cod:
        mask = mask | df_f[col_cod].astype(str).str.contains(b, na=False)
    if col_ean:
        mask = mask | df_f[col_ean].astype(str).str.contains(b, na=False)
    df_f = df_f[mask]

if familia != "Todas" and col_fam:
    df_f = df_f[df_f[col_fam].astype(str) == familia]

if solo_criticos:
    df_f = df_f[df_f[col_disp] <= 50]

# Métricas
c1, c2, c3 = st.columns(3)
c1.metric("UNID. DISPONIBLE", f"{int(df_f[col_disp].sum()):,}")
if col_cajas:
    df_f[col_cajas] = pd.to_numeric(df_f[col_cajas], errors="coerce").fillna(0)
    c2.metric("CAJAS", f"{int(df_f[col_cajas].sum()):,}")
else:
    c2.metric("PRODUCTOS", f"{len(df_f):,}")
c3.metric("AGOTADOS", f"{int((df_f[col_disp]==0).sum()):,}")

# Tabla
mostrar = pd.DataFrame()
mostrar["CODIGO"] = df_f[col_cod] if col_cod in df_f else ""
mostrar["DESCRIPCION"] = df_f[col_desc]
mostrar["DISPONIBLE"] = df_f[col_disp].astype(int)
if col_cajas:
    mostrar["CAJAS"] = df_f[col_cajas].astype(int)
if col_fam:
    mostrar["FAMILIA"] = df_f[col_fam]

st.dataframe(mostrar, use_container_width=True, hide_index=True)
st.caption(f"Mostrando {len(mostrar)} productos")
