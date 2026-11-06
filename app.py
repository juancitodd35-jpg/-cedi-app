import streamlit as st
import pandas as pd

st.set_page_config(page_title="CEDI - Existencia", layout="wide", page_icon="📦")

st.markdown("""
<style>
.main { background-color: #F2F4F7; }
div[data-testid="stMetric"] { background: white; border-radius: 12px; padding: 12px; border: 1px solid #D0D7E3; }
</style>
""", unsafe_allow_html=True)

st.title("📦 CEDI • EXISTENCIA")
st.caption("KELLOGG EL SALVADOR - Actualiza subiendo el Excel del día")

uploaded = st.file_uploader("SUBIR EXCEL DEL DÍA (solo admin)", type=["xlsx","xls"])

# Si no suben nada, usa el archivo que está en el repo
@st.cache_data
def load_data(file):
    df = pd.read_excel(file, header=0)
    # Limpia nombres de columnas
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df

if uploaded is not None:
    df = load_data(uploaded)
else:
    try:
        df = load_data("existencia.xlsx")
    except:
        st.warning("Sube el Excel del CEDI para empezar. Usa el botón de arriba.")
        st.stop()

# Renombrar para que funcione aunque vengan con espacios
# Columnas reales tuyas: COD PROVEE, PROVEEDOR, FAMILIA, CODIGO, EAN, U CAJAS, U PACKS, PACKS CAJA, UNIDADES PALLET, DESCRIPCION, CAJAS, UNIDADES, FACTOR DESPACHO, U. SUELTAS, U. BLOQUEADAS, C. BLOQUEADAS, TOTAL CAJAS, TOTAL UNIDADES, EN PREPARACION, NO DISPONIBLE, UNID. DISPONIBLE
# Buscamos las columnas por nombre parcial
def find_col(contains):
    for c in df.columns:
        if contains in c:
            return c
    return None

col_codigo = find_col("CODIGO")
col_ean = find_col("EAN")
col_desc = find_col("DESCRIPCION")
col_fam = find_col("FAMILIA")
col_disp = find_col("DISPONIBLE")  # UNID. DISPONIBLE
col_total = find_col("TOTAL UNIDADES")
col_cajas = find_col("TOTAL CAJAS")
col_nodisp = find_col("NO DISPONIBLE")
col_prep = find_col("PREPARACION")
col_bloq = find_col("U. BLOQUEADAS")

# Convertir a número
for c in [col_disp, col_total, col_cajas, col_nodisp, col_prep, col_bloq]:
    if c:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

# Filtros
busqueda = st.text_input("🔍 Buscar por CODIGO / EAN / DESCRIPCION", placeholder="Ej: 388151, 75010..., CORN FLAKES...")
familias = ["Todas"] + sorted(df[col_fam].dropna().unique().tolist()) if col_fam else ["Todas"]
fam_sel = st.selectbox("FAMILIA", familias)
solo_criticos = st.checkbox("Solo ver CRITICOS y AGOTADOS")
solo_bloqueados = st.checkbox("Solo ver BLOQUEADOS")

df_f = df.copy()
if busqueda:
    b = busqueda.strip().lower()
    df_f = df_f[df_f.apply(lambda r: b in str(r[col_codigo]).lower() or b in str(r[col_ean]).lower() or b in str(r[col_desc]).lower(), axis=1)]
if fam_sel != "Todas":
    df_f = df_f[df_f[col_fam] == fam_sel]
if solo_criticos:
    df_f = df_f[df_f[col_disp] <= 300]
if solo_bloqueados:
    df_f = df_f[df_f[col_nodisp] > 0]

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("UNID. DISPONIBLE", f"{int(df_f[col_disp].sum()):,}")
c2.metric("TOTAL CAJAS", f"{int(df_f[col_cajas].sum()):,}")
c3.metric("NO DISPONIBLE", f"{int(df_f[col_nodisp].sum()):,}")
c4.metric("AGOTADOS", f"{int((df_f[col_disp]==0).sum())}")

# Estado
def estado(row):
    if row[col_disp] == 0:
        return "🔴 AGOTADO"
    if row[col_nodisp] > 0 or row[col_bloq] > 0:
        return "🟠 BLOQUEADO PARCIAL"
    if row[col_disp] <= 300:
        return "🟡 CRITICO"
    return "🟢 OK"

df_f["ESTADO"] = df_f.apply(estado, axis=1)

# Mostrar tabla
cols_mostrar = [col_codigo, col_ean, col_desc, col_fam, col_cajas, col_total, col_nodisp, col_prep, col_disp, "ESTADO"]
cols_mostrar = [c for c in cols_mostrar if c in df_f.columns]
st.dataframe(
    df_f[cols_mostrar].sort_values(by=col_disp),
    use_container_width=True,
    hide_index=True
)

st.caption(f"Mostrando {len(df_f)} de {len(df)} SKUs • Fuente: existencia.xlsx • La cifra válida para vender es UNID. DISPONIBLE")