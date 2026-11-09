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

def leer_con_encabezado_automatico(ruta_o_archivo):
    for h in range(5):
        try:
            df = pd.read_excel(ruta_o_archivo, header=h)
            cols_txt = " ".join([str(c).lower() for c in df.columns])
            if "codigo" in cols_txt or "descripcion" in cols_txt or "articulo" in cols_txt:
                return df, h
        except:
            continue
    return pd.read_excel(ruta_o_archivo, header=1), 1

# ================= PESTAÑA 1 =================
with tab1:
    st.write("Inventario de bodega RANSA")
    archivo1 = st.file_uploader("Cargar inventario.xlsx", type=["xlsx", "xls"], key="inv1")

    df = pd.DataFrame()
    if archivo1 is not None:
        df, _ = leer_con_encabezado_automatico(archivo1)
    elif os.path.exists("inventario.xlsx"):
        df, _ = leer_con_encabezado_automatico("inventario.xlsx")

    if df.empty:
        st.warning("Subí inventario.xlsx a GitHub")
    else:
        df.columns = columnas_unicas(df.columns)
        df = df.loc[:, ~df.columns.str.contains('UNNAMED')]
        df = df.dropna(how='all')
        cols = df.columns.tolist()

        col_cod = buscar(cols, ['codigo', 'articulo'])
        col_ean = buscar(cols, ['ean', 'barra'])
        col_desc = buscar(cols, ['descripcion', 'descrip'])
        col_cajas = buscar(cols, ['cajas'])
        col_disp = buscar(cols, ['disponible', 'existencia'])

        if col_cod is None or col_desc is None:
            st.error("⚠️ Este archivo NO es el inventario bueno. No trae CODIGO / DESCRIPCION.")
        else:
            if col_ean is None:
                col_ean = col_cod
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
            out['CODIGO'] = df_f[col_cod].astype(str)
            out['EAN'] = df_f[col_ean].astype(str)
            out['DESCRIPCION'] = df_f[col_desc].astype(str)
            out['CAJAS'] = df_f[col_cajas].astype(int)
            out['UNIDADES DISPONIBLES'] = df_f[col_disp].astype(int)

            st.dataframe(
                out,
                use_container_width=True,
                hide_index=True,
                height=600,
                column_config={
                    "CODIGO": st.column_config.TextColumn("CODIGO", width="small"),
                    "EAN": st.column_config.TextColumn("EAN", width="medium"),
                    "DESCRIPCION": st.column_config.TextColumn("DESCRIPCION", width="large"),
                    "CAJAS": st.column_config.NumberColumn("CAJAS", width="small", format="%d"),
                    "UNIDADES DISPONIBLES": st.column_config.NumberColumn("UNIDADES DISPONIBLES", width="medium", format="%d"),
                }
            )

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
        # AHORA SI: la DESCRIPCION viene en el mismo archivo de tiendas, columna E
        col_desc_tiendas = buscar(cols2, ['descripcion', 'descrip'])

        limpio = pd.DataFrame()
        limpio['ARTICULO'] = df2[col_art].astype(str).apply(limpiar) if col_art else ""
        limpio['BARRA'] = df2[col_barra].astype(str).apply(limpiar) if col_barra else ""

        # 1) PRIMERO usar la DESCRIPCION que ya viene en tiendas (la completa)
        if col_desc_tiendas:
            limpio['DESCRIPCION'] = df2[col_desc_tiendas].astype(str).str.strip()
            limpio['DESCRIPCION'] = limpio['DESCRIPCION'].replace({"nan": "", "None": ""})
        else:
            limpio['DESCRIPCION'] = ""

        # 2) Solo si en tiendas viene en blanco, buscar en inventario como respaldo
        en_blanco_antes = (limpio['DESCRIPCION'] == "").sum()
        if en_blanco_antes > 0 and os.path.exists("inventario.xlsx"):
            try:
                di, _ = leer_con_encabezado_automatico("inventario.xlsx")
                di.columns = columnas_unicas(di.columns)
                ci = buscar(di.columns.tolist(), ['codigo', 'articulo'])
                dd = buscar(di.columns.tolist(), ['descripcion', 'descrip'])
                if ci and dd:
                    mapa = {}
                    for _, r in di.iterrows():
                        mapa[limpiar(r[ci])] = str(r[dd]).strip()
                    respaldo = limpio['ARTICULO'].map(mapa).fillna("")
                    limpio.loc[limpio['DESCRIPCION'] == "", 'DESCRIPCION'] = respaldo[limpio['DESCRIPCION'] == ""].values
            except:
                pass

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

        mostrar2 = pd.DataFrame()
        mostrar2['ARTICULO'] = df_f['ARTICULO'].astype(str)
        mostrar2['BARRA'] = df_f['BARRA'].astype(str)
        mostrar2['DESCRIPCION'] = df_f['DESCRIPCION'].astype(str)
        mostrar2['EXISTENCIA'] = df_f['EXISTENCIA'].astype(int)
        mostrar2['PRECIO'] = df_f['PRECIO'].astype(float)

        st.dataframe(
            mostrar2,
            use_container_width=True,
            hide_index=True,
            height=600,
            column_config={
                "ARTICULO": st.column_config.TextColumn("ARTICULO", width="small"),
                "BARRA": st.column_config.TextColumn("BARRA", width="medium"),
                "DESCRIPCION": st.column_config.TextColumn("DESCRIPCION", width="large"),
                "EXISTENCIA": st.column_config.NumberColumn("EXISTENCIA", width="small", format="%d"),
                "PRECIO": st.column_config.NumberColumn("PRECIO", format="$ %.2f", width="small"),
            }
        )
