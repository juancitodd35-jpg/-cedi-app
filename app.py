import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="RANSA - EXISTENCIA", layout="wide")

if os.path.exists("logo.png"):
    st.image("logo.png", width=180)

st.title("RANSA • EXISTENCIA")

tab1, tab2 = st.tabs(["📦 INVENTARIO RANSA", "🏪 EXISTENCIAS EN TIENDAS"])

# ======================================================
# PESTAÑA 1 - NO SE TOCA, SOLO QUE YA CARGA SOLA SI EL ARCHIVO ESTA EN GITHUB
# ======================================================
with tab1:
    st.divider()
    # Si ya subiste inventario.xlsx a GitHub, carga solo. Si no, te deja subirlo
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
        st.warning("Subí tu inventario.xlsx a GitHub para que cargue solo en compu y teléfono")
    else:
        col_codigo = 'CODIGO' if 'CODIGO' in df.columns else df.columns[0]
        col_ean = 'EAN' if 'EAN' in df.columns else df.columns[1]
        col_desc = 'DESCRIPCION' if 'DESCRIPCION' in df.columns else df.columns[2]
        col_cajas = 'TOTAL CAJAS' if 'TOTAL CAJAS' in df.columns else 'CAJAS'
        col_disp = 'UNI. DISPONIBLES' if 'UNI. DISPONIBLES' in df.columns else 'UNIDADES'
        col_bloq_u = 'U. BLOQUEADAS' if 'U. BLOQUEADAS' in df.columns else None
        col_bloq_c = 'C. BLOQUEADAS' if 'C. BLOQUEADAS' in df.columns else None

        for c in [col_cajas, col_disp, col_bloq_u, col_bloq_c]:
            if c and c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        df = df[df[col_codigo].notna()]

        busqueda = st.text_input("🔍 Buscar por nombre o por código", placeholder="Ej: 388151, CORN FLAKES...", key="bus1")
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
# PESTAÑA 2 - ARREGLADA
# - Ya carga sola si existencias_tiendas.xlsx está en GitHub
# - Buscador busca por ALMACEN aunque el almacén sea el nombre de la hoja del Excel
# - Tabla: ARTICULO, BARRA, DESCRIPCION, EXISTENCIA, PRECIO (sin proveedor)
# ======================================================
with tab2:
    st.divider()

    # Si el archivo ya está en GitHub, no pide Upload. Si no, te deja subirlo
    archivo2 = st.file_uploader("📂 Cargar archivo existencias en las tiendas", type=["xlsx", "xls", "csv"], key="tiendas")

    df2_total = pd.DataFrame()
    hojas_encontradas = []

    # 1. Intentar cargar desde GitHub primero
    if os.path.exists("existencias_tiendas.xlsx"):
        try:
            xl = pd.ExcelFile("existencias_tiendas.xlsx")
            hojas_encontradas = xl.sheet_names
            lista_dfs = []
            for hoja in hojas_encontradas:
                d = pd.read_excel("existencias_tiendas.xlsx", sheet_name=hoja, header=0)
                if sum(['unnamed' in str(c).lower() for c in d.columns]) > 3:
                    d = pd.read_excel("existencias_tiendas.xlsx", sheet_name=hoja, header=1)
                d['ALMACEN_DE_HOJA'] = hoja  # El nombre de la hoja es el almacén
                lista_dfs.append(d)
            df2_total = pd.concat(lista_dfs, ignore_index=True)
        except Exception as e:
            st.error(f"No pude leer existencias_tiendas.xlsx de GitHub: {e}")

    # 2. Si subiste con el botón, ese tiene prioridad
    elif archivo2 is not None:
        try:
            if archivo2.name.endswith(".csv"):
                df2_total = pd.read_csv(archivo2)
                df2_total['ALMACEN_DE_HOJA'] = "ARCHIVO CSV"
            else:
                xl = pd.ExcelFile(archivo2)
                hojas_encontradas = xl.sheet_names
                lista_dfs = []
                for hoja in hojas_encontradas:
                    d = pd.read_excel(archivo2, sheet_name=hoja, header=0)
                    if sum(['unnamed' in str(c).lower() for c in d.columns]) > 3:
                        d = pd.read_excel(archivo2, sheet_name=hoja, header=1)
                    d['ALMACEN_DE_HOJA'] = hoja
                    lista_dfs.append(d)
                df2_total = pd.concat(lista_dfs, ignore_index=True)
        except Exception as e:
            st.error(f"No pude leer el archivo: {e}")

    if not df2_total.empty:
        df2_total.columns = [str(c).strip().upper() for c in df2_total.columns]
        cols = df2_total.columns.tolist()

        def buscar_col(palabras):
            for c in cols:
                cl = c.lower()
                for p in palabras:
                    if p in cl:
                        return c
            return None

        col_articulo = buscar_col(['articulo', 'artículo'])
        col_barra = buscar_col(['barra', 'ean'])
        col_existencia = buscar_col(['existencia'])
        col_precio = buscar_col(['precio'])

        # DESCRIPCION = 2do NOMBRE (1er NOMBRE es KELLOGG, proveedor, lo ignoramos)
        idx_nombre = [i for i, c in enumerate(cols) if c == 'NOMBRE']
        if len(idx_nombre) >= 2:
            col_descripcion = cols[idx_nombre[1]]
        elif 'DESCRIPCION' in cols:
            col_descripcion = 'DESCRIPCION'
        else:
            col_descripcion = buscar_col(['descripcion', 'desc', 'producto'])

        # ALMACEN: primero buscar columna que diga ALMACEN / SUCURSAL / TIENDA
        col_almacen_columna = buscar_col(['almacen', 'almacén', 'sucursal', 'tienda', 'local', 'bodega'])
        # Si no hay columna, usamos el nombre de la hoja
        if col_almacen_columna is not None:
            df2_total['ALMACEN_FINAL'] = df2_total[col_almacen_columna].astype(str)
        else:
            df2_total['ALMACEN_FINAL'] = df2_total['ALMACEN_DE_HOJA'].astype(str)

        df_limpio = pd.DataFrame()
        df_limpio['ARTICULO'] = df2_total[col_articulo]
        df_limpio['BARRA'] = df2_total[col_barra]
        df_limpio['DESCRIPCION'] = df2_total[col_descripcion]
        df_limpio['EXISTENCIA'] = pd.to_numeric(df2_total[col_existencia], errors='coerce').fillna(0)
        df_limpio['PRECIO VENTA CON IVA'] = pd.to_numeric(df2_total[col_precio], errors='coerce').fillna(0)
        df_limpio['ALMACEN'] = df2_total['ALMACEN_FINAL']
        df_limpio = df_limpio[df_limpio['ARTICULO'].notna()]

        # Mostrar qué almacenes encontró, para que verifiques
        almacenes = sorted(df_limpio['ALMACEN'].astype(str).unique().tolist())
        st.caption(f"Almacenes que encontré: {', '.join(almacenes)}")

        # --- BUSCADOR POR CODIGO O NOMBRE DE ALMACEN ---
        bus = st.text_input("🔍 Buscar almacén por código o nombre", placeholder="Ej: GIGANTE, WALMART...", key="bus_almacen")
        if bus:
            t = str(bus).lower().strip()
            # Busca en ALMACEN, y también en DESCRIPCION por si escribís un producto
            df_f = df_limpio[
                df_limpio['ALMACEN'].astype(str).str.lower().str.contains(t, na=False) |
                df_limpio['DESCRIPCION'].astype(str).str.lower().str.contains(t, na=False) |
                df_limpio['ARTICULO'].astype(str).str.lower().str.contains(t, na=False) |
                df_limpio['BARRA'].astype(str).str.lower().str.contains(t, na=False)
            ]
        else:
            df_f = df_limpio.copy()

        # --- TARJETA TOTAL EXISTENCIAS ---
        if bus and len(df_f) > 0:
            # Si el buscador encontró 1 solo almacén, mostrar ese nombre
            almacenes_f = df_f['ALMACEN'].unique()
            if len(almacenes_f) == 1:
                titulo = f"TOTAL EXISTENCIAS - {almacenes_f[0]}"
            else:
                titulo = f"TOTAL EXISTENCIAS - BUSQUEDA: {bus}"
            total = df_f['EXISTENCIA'].sum()
        elif bus and len(df_f) == 0:
            titulo = f"SIN RESULTADOS PARA: {bus}"
            total = 0
        else:
            titulo = "TOTAL EXISTENCIAS - TODAS LAS TIENDAS"
            total = df_limpio['EXISTENCIA'].sum()

        st.markdown(f"""
        <div style="background-color:#e8f5e9; padding:15px; border-radius:10px; border:1px solid #4CAF50; margin-top:10px;">
            <p style="font-size:12px; color:gray; margin:0;">{titulo}</p>
            <p style="font-size:32px; font-weight:bold; margin:0; color:#2E7D32;">{int(total):,}</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.write(f"**{len(df_f)} artículos encontrados**")

        # TABLA FINAL SIN PROVEEDOR
        df_mostrar2 = df_f[['ARTICULO', 'BARRA', 'DESCRIPCION', 'EXISTENCIA', 'PRECIO VENTA CON IVA']].copy()
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
        st.warning("Subí existencias_tiendas.xlsx a GitHub para que cargue solo en compu y teléfono, o usá el botón de arriba")
