import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="RANSA - EXISTENCIA", layout="wide")

if os.path.exists("logo.png"):
    st.image("logo.png", width=180)

st.title("RANSA • EXISTENCIA")

tab1, tab2 = st.tabs(["📦 INVENTARIO RANSA", "🏪 EXISTENCIAS EN TIENDAS"])

# ======================================================
# PESTAÑA 1 - LA QUE YA TENIAS
# ======================================================
with tab1:
    st.divider()
    archivo_subido = st.file_uploader("📂 Cargar archivo inventario.xlsx", type=["xlsx", "xls"], key="inv")

    @st.cache_data(ttl=60)
    def cargar(archivo):
        if archivo is not None:
            df = pd.read_excel(archivo, header=1)
        elif os.path.exists("inventario.xlsx"):
            df = pd.read_excel("inventario.xlsx", header=1)
        else:
            return pd.DataFrame()
        df.columns = [str(c).strip().upper() for c in df.columns]
        df = df.loc[:, ~df.columns.str.contains('UNNAMED')]
        df = df.dropna(how='all')
        return df

    df = cargar(archivo_subido)
    if df.empty:
        st.warning("Subí tu inventario.xlsx para empezar")
    else:
        col_codigo = 'CODIGO' if 'CODIGO' in df.columns else df.columns[0]
        col_ean = 'EAN'
        col_desc = 'DESCRIPCION'
        col_cajas = 'TOTAL CAJAS' if 'TOTAL CAJAS' in df.columns else 'CAJAS'
        col_disp = 'UNI. DISPONIBLES' if 'UNI. DISPONIBLES' in df.columns else 'UNIDADES'
        col_bloq_u = 'U. BLOQUEADAS' if 'U. BLOQUEADAS' in df.columns else None
        col_bloq_c = 'C. BLOQUEADAS' if 'C. BLOQUEADAS' in df.columns else None

        for c in [col_cajas, col_disp, col_bloq_u, col_bloq_c]:
            if c and c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        df = df[df[col_codigo].notna()]

        st.markdown("<p style='font-size:8px; margin-bottom:0px; color:gray;'>CODIGO DE PROVEEDOR</p>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:14px; margin-top:0px; font-weight:bold;'>004694</p>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:8px; margin-bottom:0px; color:gray;'>FECHA INICIO (YA EN TIENDA)</p>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:14px; margin-top:0px; font-weight:bold;'>4/11/2026</p>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:8px; margin-bottom:0px; color:gray;'>FECHA FIN (SALE DE ESPACIO)</p>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:14px; margin-top:0px; font-weight:bold;'>29/11/2026</p>", unsafe_allow_html=True)

        st.markdown("<p style='font-size:8px; margin-bottom:2px; color:gray;'>CONTEO POR CANAL</p>", unsafe_allow_html=True)
        c_b, c_s, c_w, c_t = st.columns(4)
        with c_b:
            st.write("BODEGA"); st.markdown("<h3 style='margin-top:-15px'>16</h3>", unsafe_allow_html=True)
        with c_s:
            st.write("SUPER"); st.markdown("<h3 style='margin-top:-15px'>17</h3>", unsafe_allow_html=True)
        with c_w:
            st.write("WALMART"); st.markdown("<h3 style='margin-top:-15px'>6</h3>", unsafe_allow_html=True)
        with c_t:
            st.write("TOTAL"); st.markdown("<h3 style='margin-top:-15px'>39</h3>", unsafe_allow_html=True)
        st.divider()

        busqueda = st.text_input("🔍 Buscar por nombre o por código", placeholder="Ej: 388151, CORN FLAKES, KELLOGS...", key="bus1")
        if busqueda:
            texto = str(busqueda).lower().strip()
            df_f = df[
                df[col_codigo].astype(str).str.lower().str.contains(texto, na=False) |
                df[col_desc].astype(str).str.lower().str.contains(texto, na=False) |
                df[col_ean].astype(str).str.lower().str.contains(texto, na=False)
            ]
        else:
            df_f = df.copy()

        c_check1, c_check2 = st.columns(2)
        with c_check1:
            solo_criticos = st.checkbox("Solo ver CRITICOS o AGOTADOS", key="crit")
        with c_check2:
            solo_bloq = st.checkbox("Solo ver BLOQUEADOS", key="bloq")

        if solo_criticos:
            df_f = df_f[df_f[col_disp] <= 50]
        if solo_bloq:
            cond = pd.Series(False, index=df_f.index)
            if col_bloq_u in df_f.columns:
                cond = cond | (df_f[col_bloq_u] > 0)
            if col_bloq_c in df_f.columns:
                cond = cond | (df_f[col_bloq_c] > 0)
            df_f = df_f[cond]

        c1, c2 = st.columns(2)
        with c1:
            st.write("TOTAL UNIDADES DISPONIBLES")
            st.markdown(f"<h1 style='margin-top:-15px'>{int(df[col_disp].sum()):,}</h1>", unsafe_allow_html=True)
        with c2:
            st.write("TOTAL CAJAS")
            st.markdown(f"<h1 style='margin-top:-15px'>{int(df[col_cajas].sum()):,}</h1>", unsafe_allow_html=True)

        st.divider()
        st.write(f"**{len(df_f)} productos encontrados**")
        df_mostrar = pd.DataFrame()
        df_mostrar['CODIGO'] = df_f[col_codigo]
        df_mostrar['EAN'] = df_f[col_ean]
        df_mostrar['DESCRIPCION'] = df_f[col_desc]
        df_mostrar['CAJAS'] = df_f[col_cajas]
        df_mostrar['UNIDADES DISPONIBLES'] = df_f[col_disp]
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

# ======================================================
# PESTAÑA 2 - EXISTENCIAS EN TIENDAS - COMO PEDISTE
# ======================================================
with tab2:
    st.divider()
    archivo2 = st.file_uploader("📂 Cargar archivo existencias en las tiendas", type=["xlsx", "xls", "csv"], key="tiendas")

    def buscar_columna(columnas, palabras):
        for col in columnas:
            c = str(col).lower()
            for p in palabras:
                if p in c:
                    return col
        return None

    if archivo2 is not None:
        try:
            if archivo2.name.endswith(".csv"):
                df2 = pd.read_csv(archivo2)
            else:
                df2 = pd.read_excel(archivo2, header=0)
                if sum(['unnamed' in str(c).lower() for c in df2.columns]) > 3:
                    df2 = pd.read_excel(archivo2, header=1)
        except Exception as e:
            st.error(f"No pude leer el archivo: {e}")
            df2 = pd.DataFrame()

        if not df2.empty:
            df2.columns = [str(c).strip() for c in df2.columns]
            cols = df2.columns.tolist()

            # Detectar columnas
            col_suc = buscar_columna(cols, ["sucursal", "tienda", "numero tienda", "num tienda", "cod tienda", "codigo tienda"])
            col_suc_desc = buscar_columna(cols, ["desc tienda", "descripcion tienda", "nombre tienda", "nombre sucursal", "desc sucursal", "descripcion sucursal", "tienda desc", "sucursal desc"])
            col_art = buscar_columna(cols, ["articulo", "artículo", "cod articulo", "codigo articulo", "item", "codigo", "cod producto"])
            col_barra = buscar_columna(cols, ["barra", "ean", "codigo barra", "cod barra", "upc", "codigo de barra"])
            col_desc = buscar_columna(cols, ["descripcion", "desc ", "desc", "nombre", "producto"])
            col_exis = buscar_columna(cols, ["existencia", "existencias", "stock", "saldo", "cantidad", "unidades"])
            col_precio = buscar_columna(cols, ["precio venta", "precio con iva", "precio iva", "pvp", "precio", "venta con iva"])

            # Si la descripción de sucursal no existe, usamos la misma de sucursal
            if col_suc_desc is None:
                col_suc_desc = col_suc

            st.write("**Si alguna columna está mal, la corregís aquí:**")
            cc1, cc2, cc3, cc4 = st.columns(4)
            with cc1:
                col_suc = st.selectbox("SUCURSAL (código)", cols, index=cols.index(col_suc) if col_suc in cols else 0, key="csuc")
            with cc2:
                col_suc_desc = st.selectbox("NOMBRE SUCURSAL", cols, index=cols.index(col_suc_desc) if col_suc_desc in cols else 0, key="csucd")
            with cc3:
                col_art = st.selectbox("ARTÍCULO", cols, index=cols.index(col_art) if col_art in cols else 0, key="cart")
            with cc4:
                col_barra = st.selectbox("BARRA", cols, index=cols.index(col_barra) if col_barra in cols else 0, key="cbarra")
            cc5, cc6, cc7 = st.columns(3)
            with cc5:
                col_desc = st.selectbox("DESCRIPCIÓN", cols, index=cols.index(col_desc) if col_desc in cols else 0, key="cdesc")
            with cc6:
                col_exis = st.selectbox("EXISTENCIA", cols, index=cols.index(col_exis) if col_exis in cols else 0, key="cexis")
            with cc7:
                col_precio = st.selectbox("PRECIO VENTA CON IVA", cols, index=cols.index(col_precio) if col_precio in cols else 0, key="cprecio")

            # Tabla limpia en el orden que pediste
            df2_clean = pd.DataFrame()
            df2_clean['SUCURSAL'] = df2[col_suc]
            df2_clean['NOMBRE_SUCURSAL'] = df2[col_suc_desc]
            df2_clean['ARTICULO'] = df2[col_art]
            df2_clean['BARRA'] = df2[col_barra]
            df2_clean['DESCRIPCION'] = df2[col_desc]
            df2_clean['EXISTENCIA'] = pd.to_numeric(df2[col_exis], errors='coerce').fillna(0)
            df2_clean['PRECIO VENTA CON IVA'] = pd.to_numeric(df2[col_precio], errors='coerce').fillna(0)
            df2_clean = df2_clean[df2_clean['SUCURSAL'].notna()]

            # --- BUSCADOR DE SUCURSAL ---
            bus_suc = st.text_input("🔍 Buscar sucursal por código o nombre", placeholder="Ej: 123, WALMART SOYAPANGO...", key="bussuc")
            if bus_suc:
                t = str(bus_suc).lower().strip()
                df_suc_f = df2_clean[
                    df2_clean['SUCURSAL'].astype(str).str.lower().str.contains(t, na=False) |
                    df2_clean['NOMBRE_SUCURSAL'].astype(str).str.lower().str.contains(t, na=False)
                ]
            else:
                df_suc_f = df2_clean.copy()

            # --- TARJETA TOTAL EXISTENCIAS DE LA TIENDA ELEGIDA ---
            # Si el buscador encontró 1 sola tienda, esa es la elegida
            tiendas_unicas = df_suc_f['SUCURSAL'].astype(str).unique()
            if bus_suc and len(tiendas_unicas) == 1:
                nombre_tienda = df_suc_f['NOMBRE_SUCURSAL'].iloc[0]
                total_tienda = df_suc_f['EXISTENCIA'].sum()
                st.markdown(f"""
                <div style="background-color:#e8f5e9; padding:15px; border-radius:10px; border:1px solid #4CAF50; margin-top:10px;">
                    <p style="font-size:12px; color:gray; margin:0;">TOTAL EXISTENCIAS - TIENDA ELEGIDA</p>
                    <p style="font-size:18px; font-weight:bold; margin:0;">{tiendas_unicas[0]} - {nombre_tienda}</p>
                    <p style="font-size:32px; font-weight:bold; margin:0; color:#2E7D32;">{int(total_tienda):,}</p>
                </div>
                """, unsafe_allow_html=True)
            elif bus_suc and len(tiendas_unicas) > 1:
                st.info(f"Encontré {len(tiendas_unicas)} sucursales con ese texto. Escribí el código exacto para ver la tarjeta de una sola tienda. Total de esas tiendas: {int(df_suc_f['EXISTENCIA'].sum()):,}")
            else:
                st.markdown(f"""
                <div style="background-color:#f1f1f1; padding:15px; border-radius:10px; margin-top:10px;">
                    <p style="font-size:12px; color:gray; margin:0;">TOTAL EXISTENCIAS - TODAS LAS TIENDAS</p>
                    <p style="font-size:32px; font-weight:bold; margin:0;">{int(df2_clean['EXISTENCIA'].sum()):,}</p>
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            st.write(f"**{len(df_suc_f)} artículos encontrados**")

            # --- TABLA FINAL EN EL ORDEN QUE PEDISTE ---
            # A la izquierda: ARTICULO, BARRA, DESCRIPCION - luego EXISTENCIA, PRECIO
            df_mostrar2 = df_suc_f[['ARTICULO', 'BARRA', 'DESCRIPCION', 'EXISTENCIA', 'PRECIO VENTA CON IVA']].copy()

            st.dataframe(
                df_mostrar2,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "PRECIO VENTA CON IVA": st.column_config.NumberColumn(format="$ %.2f"),
                    "EXISTENCIA": st.column_config.NumberColumn(format="%d"),
                }
            )
    else:
        st.warning("Subí el archivo de existencias en las tiendas para verlo")
