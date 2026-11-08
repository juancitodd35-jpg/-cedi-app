import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="RANSA - EXISTENCIA", layout="wide")

if os.path.exists("logo.png"):
    st.image("logo.png", width=180)

st.title("RANSA • EXISTENCIA")

tab1, tab2 = st.tabs(["📦 INVENTARIO RANSA", "🏪 EXISTENCIAS EN TIENDAS"])

# ======================================================
# PESTAÑA 1 - NO SE TOCA, YA ESTABA BIEN
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
# - Se quitó la columna de proveedor KELLOGG...
# - Tabla: ARTICULO, BARRA, DESCRIPCION, EXISTENCIA, PRECIO
# - Buscador ya busca por ALMACEN, no por proveedor
# ======================================================
with tab2:
    st.divider()

    archivo2 = st.file_uploader("📂 Cargar archivo existencias en las tiendas", type=["xlsx", "xls", "csv"], key="tiendas")

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
            df2.columns = [str(c).strip().upper() for c in df2.columns]
            cols = df2.columns.tolist()

            # MOSTRAR QUE COLUMNAS TRAE TU ARCHIVO - solo para que verifiquemos
            # Cuando ya quede bien, borramos esta línea
            st.caption(f"Columnas que trae tu archivo: {', '.join(cols)}")

            # --- BUSCAR COLUMNAS REALES ---
            # ARTICULO, BARRA, EXISTENCIA, PRECIO por nombre
            def buscar(palabras):
                for c in cols:
                    cl = c.lower()
                    for p in palabras:
                        if p in cl:
                            return c
                return None

            col_articulo = buscar(['articulo', 'artículo'])
            col_barra = buscar(['barra', 'ean'])
            col_existencia = buscar(['existencia'])
            col_precio = buscar(['precio'])

            # DESCRIPCION = el segundo NOMBRE (el primero es el proveedor KELLOGG, ese lo ignoramos)
            idx_nombre = [i for i, c in enumerate(cols) if c == 'NOMBRE']
            if len(idx_nombre) >= 2:
                col_descripcion = cols[idx_nombre[1]]
            elif 'DESCRIPCION' in cols:
                col_descripcion = 'DESCRIPCION'
            else:
                col_descripcion = buscar(['descripcion', 'desc', 'producto'])

            # ALMACEN REAL = buscar columna que diga ALMACEN, SUCURSAL, TIENDA, LOCAL, BODEGA
            col_almacen = buscar(['almacen', 'almacén', 'sucursal', 'tienda', 'local', 'bodega', 'punto'])
            # Si no hay columna de almacén con ese nombre, puede que venga como CODIGO ALMACEN / NUMERO, etc.
            if col_almacen is None:
                col_almacen = buscar(['cod almacen', 'codigo almacen', 'num almacen', 'alm'])

            if col_almacen is None:
                st.warning("⚠️ No encontré una columna que se llame ALMACEN / SUCURSAL / TIENDA en tu archivo. Arriba te puse todas las columnas que trae, mandame captura de esa línea para ver cuál es.")
                # Si no hay almacén, mostramos todo sin filtrar por almacén
                df_limpio = pd.DataFrame()
                df_limpio['ARTICULO'] = df2[col_articulo]
                df_limpio['BARRA'] = df2[col_barra]
                df_limpio['DESCRIPCION'] = df2[col_descripcion]
                df_limpio['EXISTENCIA'] = pd.to_numeric(df2[col_existencia], errors='coerce').fillna(0)
                df_limpio['PRECIO VENTA CON IVA'] = pd.to_numeric(df2[col_precio], errors='coerce').fillna(0)
                df_limpio['ALMACEN'] = "SIN COLUMNA ALMACEN"
            else:
                df_limpio = pd.DataFrame()
                df_limpio['ARTICULO'] = df2[col_articulo]
                df_limpio['BARRA'] = df2[col_barra]
                df_limpio['DESCRIPCION'] = df2[col_descripcion]
                df_limpio['EXISTENCIA'] = pd.to_numeric(df2[col_existencia], errors='coerce').fillna(0)
                df_limpio['PRECIO VENTA CON IVA'] = pd.to_numeric(df2[col_precio], errors='coerce').fillna(0)
                df_limpio['ALMACEN'] = df2[col_almacen]

            # --- BUSCADOR POR CODIGO O NOMBRE DE ALMACEN ---
            bus = st.text_input("🔍 Buscar almacén por código o nombre", placeholder="Ej: GIGANTE, 123...", key="bus_almacen")
            if bus:
                t = str(bus).lower().strip()
                df_f = df_limpio[df_limpio['ALMACEN'].astype(str).str.lower().str.contains(t, na=False)]
            else:
                df_f = df_limpio.copy()

            # --- TARJETA TOTAL EXISTENCIAS ---
            if bus and len(df_f) > 0:
                titulo = f"TOTAL EXISTENCIAS - {df_f['ALMACEN'].iloc[0]}"
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

            # --- TABLA FINAL SIN PROVEEDOR ---
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
        st.warning("Subí el archivo de existencias en las tiendas para verlo")
