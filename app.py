import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="RANSA - EXISTENCIA", layout="wide")
st.title("RANSA • EXISTENCIA")

tab1, tab2 = st.tabs(["📦 INVENTARIO RANSA", "🏪 EXISTENCIAS EN TIENDAS"])

def limpiar(x):
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s

def buscar(cols, palabras):
    for c in cols:
        cl = str(c).lower()
        for p in palabras:
            if p in cl:
                return c
    return None

def columnas_unicas(cols):
    nuevas = []
    conteo = {}
    for c in cols:
        c = str(c).strip().upper()
        if c in conteo:
            conteo[c] += 1
            nuevas.append(f"{c}_{conteo[c]}")
        else:
            conteo[c] = 1
            nuevas.append(c)
    return nuevas

# ================= PESTAÑA 1 =================
with tab1:
    st.write("Inventario de bodega RANSA")
    archivo1 = st.file_uploader("Cargar inventario.xlsx", type=["xlsx", "xls"], key="inv1")

    df = pd.DataFrame()
    if archivo1 is not None:
        df = pd.read_excel(archivo1, header=1)
    elif os.path.exists("inventario.xlsx"):
        df = pd.read_excel("inventario.xlsx", header=1)

    if df.empty:
        st.warning("Subí inventario.xlsx a GitHub")
    else:
        df.columns = columnas_unicas(df.columns)
        df = df.loc[:, ~df.columns.str.contains('UNNAMED')]
        df = df.dropna(how='all')
        cols = df.columns.tolist()

        col_cod = buscar(cols, ['codigo', 'articulo']) or cols[0]
        col_ean = buscar(cols, ['ean', 'barra']) or cols[0]
        col_desc = buscar(cols, ['descripcion', 'descrip']) or cols[0]
        col_cajas = buscar(cols, ['cajas'])
        col_disp = buscar(cols, ['disponible', 'existencia'])

        if col_cajas is None:
            df['CAJAS_X'] = 0
            col_cajas = 'CAJAS_X'
        if col_disp is None:
            df['DISP_X'] = 0
            col_disp = 'DISP_X'

        df[col_cajas] = pd.to_numeric(df[col_cajas], errors='coerce').fillna(0)
        df[col_disp] = pd.to_numeric(df[col_disp], errors='coerce').fillna(0)
        df = df[df[col_cod].notna()]

        bus = st.text_input("🔍 Buscar por código o nombre", key="bus1")
        if bus:
            t = bus.lower().strip()
            df_f = df[
                df[col_cod].astype(str).str.lower().str.contains(t, na=False) |
                df[col_desc].astype(str).str.lower().str.contains(t, na=False) |
                df[col_ean].astype(str).str.lower().str.contains(t, na=False)
            ]
        else:
            df_f = df.copy()

        c1, c2 = st.columns(2)
        c1.metric("TOTAL UNIDADES DISPONIBLES", f"{int(df[col_disp].sum()):,}")
        c2.metric("TOTAL CAJAS", f"{int(df[col_cajas].sum()):,}")
        st.divider()
        st.write(f"**{len(df_f)} productos**")
        out = pd.DataFrame()
        out['CODIGO'] = df_f[col_cod]
        out['EAN'] = df_f[col_ean]
        out['DESCRIPCION'] = df_f[col_desc]
        out['CAJAS'] = df_f[col_cajas]
        out['UNIDADES DISPONIBLES'] = df_f[col_disp]
        st.dataframe(out, use_container_width=True, hide_index=True)

# ================= PESTAÑA 2 =================
with tab2:
    st.write("Existencias en tiendas")
    archivo2 = st.file_uploader("Cargar existencias_tiendas.xlsx", type=["xlsx", "xls", "csv"], key="inv2")

    df2 = pd.DataFrame()
    if archivo2 is not None:
        if archivo2.name.endswith(".csv"):
            df2 = pd.read_csv(archivo2, dtype=str)
        else:
            xl = pd.ExcelFile(archivo2)
            lista = []
            for hoja in xl.sheet_names:
                d = pd.read_excel(archivo2, sheet_name=hoja, header=0, dtype=str)
                d.columns = columnas_unicas(d.columns)
                if sum(['UNNAMED' in str(c) for c in d.columns]) > 3:
                    d = pd.read_excel(archivo2, sheet_name=hoja, header=1, dtype=str)
                    d.columns = columnas_unicas(d.columns)
                d['HOJA'] = hoja
                lista.append(d)
            df2 = pd.concat(lista, ignore_index=True)
    elif os.path.exists("existencias_tiendas.xlsx"):
        xl = pd.ExcelFile("existencias_tiendas.xlsx")
        lista = []
        for hoja in xl.sheet_names:
            d = pd.read_excel("existencias_tiendas.xlsx", sheet_name=hoja, header=0, dtype=str)
            d.columns = columnas_unicas(d.columns)
            if sum(['UNNAMED' in str(c) for c in d.columns]) > 3:
                d = pd.read_excel("existencias_tiendas.xlsx", sheet_name=hoja, header=1, dtype=str)
                d.columns = columnas_unicas(d.columns)
            d['HOJA'] = hoja
            lista.append(d)
        df2 = pd.concat(lista, ignore_index=True)
        st.success("✅ Cargado desde GitHub")

    if df2.empty:
        st.warning("Subí existencias_tiendas.xlsx a GitHub")
    else:
        df2.columns = columnas_unicas(df2.columns)
        cols2 = df2.columns.tolist()

        col_alm = buscar(cols2, ['cod almacen'])
        col_nom_alm = buscar(cols2, ['nombre almacen'])
        col_art = buscar(cols2, ['articulo'])
        col_barra = buscar(cols2, ['barra', 'ean'])
        col_ex = buscar(cols2, ['existencia'])
        col_prec = buscar(cols2, ['precio'])

        # Descripción desde inventario.xlsx, nunca desde NOMBRE (KELLOGG)
        mapa_desc = {}
        if os.path.exists("inventario.xlsx"):
            try:
                di = pd.read_excel("inventario.xlsx", header=1, dtype=str)
                di.columns = columnas_unicas(di.columns)
                ci = buscar(di.columns.tolist(), ['codigo', 'articulo'])
                dd = buscar(di.columns.tolist(), ['descripcion', 'descrip'])
                if ci and dd:
                    for _, r in di.iterrows():
                        mapa_desc[limpiar(r[ci])] = str(r[dd]).strip()
            except:
                pass

        limpio = pd.DataFrame()
        limpio['ARTICULO'] = df2[col_art].astype(str).apply(limpiar) if col_art else ""
        limpio['BARRA'] = df2[col_barra].astype(str) if col_barra else ""
        limpio['DESCRIPCION'] = limpio['ARTICULO'].map(mapa_desc).fillna("")
        limpio['EXISTENCIA'] = pd.to_numeric(df2[col_ex], errors='coerce').fillna(0) if col_ex else 0
        limpio['PRECIO'] = pd.to_numeric(df2[col_prec], errors='coerce').fillna(0) if col_prec else 0
        if col_alm:
            limpio['COD_ALMACEN'] = df2[col_alm].astype(str).str.strip().str.zfill(4)
        else:
            limpio['COD_ALMACEN'] = df2['HOJA'].astype(str).str.strip().str.zfill(4)
        if col_nom_alm:
            limpio['NOMBRE_ALMACEN'] = df2[col_nom_alm].astype(str).str.strip()
        else:
            limpio['NOMBRE_ALMACEN'] = ""

        limpio = limpio[limpio['ARTICULO'] != ""]
        limpio = limpio[limpio['ARTICULO'] != "nan"]

        codigos = sorted(limpio['COD_ALMACEN'].unique().tolist())
        def etiqueta(c):
            f = limpio[limpio['COD_ALMACEN'] == c]
            n = str(f.iloc[0]['NOMBRE_ALMACEN']) if len(f) > 0 else ""
            return f"{c} - {n}" if n else c

        opciones = ["TODAS LAS TIENDAS"] + codigos
        sel = st.selectbox("🏪 Selecciona tu tienda", opciones, format_func=lambda x: "— TODAS LAS TIENDAS —" if x == "TODAS LAS TIENDAS" else etiqueta(x), key="tienda")

        if sel == "TODAS LAS TIENDAS":
            df_f = limpio.copy()
        else:
            df_f = limpio[limpio['COD_ALMACEN'] == sel]

        st.metric("TOTAL EXISTENCIAS", f"{int(df_f['EXISTENCIA'].sum()):,}")
        st.divider()
        st.write(f"**{len(df_f)} artículos**")
        st.dataframe(df_f[['ARTICULO', 'BARRA', 'DESCRIPCION', 'EXISTENCIA', 'PRECIO']], use_container_width=True, hide_index=True, column_config={"PRECIO": st.column_config.NumberColumn(format="$ %.2f")})
