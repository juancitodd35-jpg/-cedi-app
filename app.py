import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="RANSA - EXISTENCIA", layout="wide")

if os.path.exists("logo.png"):
    st.image("logo.png", width=180)

st.title("RANSA • EXISTENCIA")

tab1, tab2 = st.tabs(["📦 INVENTARIO RANSA", "🏪 EXISTENCIAS EN TIENDAS"])

# ======================================================
# PESTAÑA 1 - NO SE TOCA
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
# PESTAÑA 2 - CON LISTA DESPLEGABLE DE TIENDAS
# Ya no es buscador con texto. Es lista: CODIGO - NOMBRE
# Y ya carga sola si el archivo está en GitHub
# ======================================================
with tab2:
    st.divider()
    st.write("🏪 **Selecciona tu tienda**")

    # --- Cargar mapa CODIGO -> NOMBRE desde almacenes.csv en GitHub ---
    mapa_nombres = {}
    if os.path.exists("almacenes.csv"):
        try:
            df_map = pd.read_csv("almacenes.csv")
            df_map.columns = [str(c).strip().upper() for c in df_map.columns]
            # Busca columnas CODIGO y NOMBRE
            col_cod = [c for c in df_map.columns if 'COD' in c][0]
            col_nom = [c for c in df_map.columns if 'NOM' in c or 'ALMAC' in c or 'TIENDA' in c or 'SUCURSAL' in c][0]
            for _, r in df_map.iterrows():
                mapa_nombres[str(r[col_cod]).strip()] = str(r[col_nom]).strip()
        except:
            pass

    # --- Cargar existencias ---
    # 1. Prioridad: archivo en GitHub (para que lo vean todos en el teléfono)
    # 2. Si no está en GitHub, dejar subir con botón (solo lo ve quien lo sube)
    df2_total = pd.DataFrame()

    if os.path.exists("existencias_tiendas.xlsx"):
        try:
            xl = pd.ExcelFile("existencias_tiendas.xlsx")
            lista = []
            for hoja in xl.sheet_names:
                d = pd.read_excel("existencias_tiendas.xlsx", sheet_name=hoja, header=0)
                if sum(['unnamed' in str(c).lower() for c in d.columns]) > 3:
                    d = pd.read_excel("existencias_tiendas.xlsx", sheet_name=hoja, header=1)
                d['ALMACEN_DE_HOJA'] = hoja
                lista.append(d)
            df2_total = pd.concat(lista, ignore_index=True)
            st.success("✅ Archivo cargado desde GitHub - ya lo pueden ver todos en el teléfono")
        except Exception as e:
            st.error(f"No pude leer existencias_tiendas.xlsx: {e}")
    else:
        st.warning("⚠️ Todavía no está existencias_tiendas.xlsx en GitHub. Subilo a GitHub para que lo vean los mercaderistas. Mientras tanto podés subirlo aquí, pero solo lo vas a ver vos.")
        archivo2 = st.file_uploader("📂 Cargar archivo existencias en las tiendas (solo para vos)", type=["xlsx", "xls", "csv"], key="tiendas")
        if archivo2 is not None:
            try:
                if archivo2.name.endswith(".csv"):
                    df2_total = pd.read_csv(archivo2)
                    df2_total['ALMACEN_DE_HOJA'] = "CSV"
                else:
                    xl = pd.ExcelFile(archivo2)
                    lista = []
                    for hoja in xl.sheet_names:
                        d = pd.read_excel(archivo2, sheet_name=hoja, header=0)
                        if sum(['unnamed' in str(c).lower() for c in d.columns]) > 3:
                            d = pd.read_excel(archivo2, sheet_name=hoja, header=1)
                        d['ALMACEN_DE_HOJA'] = hoja
                        lista.append(d)
                    df2_total = pd.concat(lista, ignore_index=True)
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

        idx_nombre = [i for i, c in enumerate(cols) if c == 'NOMBRE']
        if len(idx_nombre) >= 2:
            col_descripcion = cols[idx_nombre[1]]
        elif 'DESCRIPCION' in cols:
            col_descripcion = 'DESCRIPCION'
        else:
            col_descripcion = buscar_col(['descripcion', 'desc', 'producto'])

        col_almacen_col = buscar_col(['almacen', 'almacén', 'sucursal', 'tienda', 'local', 'bodega'])
        if col_almacen_col is not None:
            df2_total['ALMACEN_FINAL'] = df2_total[col_almacen_col].astype(str).str.strip()
        else:
            df2_total['ALMACEN_FINAL'] = df2_total['ALMACEN_DE_HOJA'].astype(str).str.strip()

        df_limpio = pd.DataFrame()
        df_limpio['ARTICULO'] = df2_total[col_articulo]
        df_limpio['BARRA'] = df2_total[col_barra]
        df_limpio['DESCRIPCION'] = df2_total[col_descripcion]
        df_limpio['EXISTENCIA'] = pd.to_numeric(df2_total[col_existencia], errors='coerce').fillna(0)
        df_limpio['PRECIO VENTA CON IVA'] = pd.to_numeric(df2_total[col_precio], errors='coerce').fillna(0)
        df_limpio['ALMACEN'] = df2_total['ALMACEN_FINAL']
        df_limpio = df_limpio[df_limpio['ARTICULO'].notna()]

        # --- LISTA DESPLEGABLE: CODIGO - NOMBRE ---
        # Sacar lista única de almacenes
        codigos = sorted(df_limpio['ALMACEN'].unique().tolist(), key=lambda x: str(x))

        def etiqueta(codigo):
            codigo_str = str(codigo).strip()
            # Si hay nombre en almacenes.csv, mostrar CODIGO - NOMBRE
            if codigo_str in mapa_nombres:
                return f"{codigo_str} - {mapa_nombres[codigo_str]}"
            # Si el código ya trae nombre, mostrarlo tal cual
            return codigo_str

        # Opción para ver todas
        opciones = ["— TODAS LAS TIENDAS —"] + codigos

        seleccion = st.selectbox(
            "🏪 Selecciona tu tienda",
            opciones,
            format_func=lambda x: "— TODAS LAS TIENDAS —" if x == "— TODAS LAS TIENDAS —" else etiqueta(x),
            key="select_tienda"
        )

        if seleccion == "— TODAS LAS TIENDAS —":
            df_f = df_limpio.copy()
            titulo = "TOTAL EXISTENCIAS - TODAS LAS TIENDAS"
        else:
            df_f = df_limpio[df_limpio['ALMACEN'].astype(str) == str(seleccion)]
            titulo = f"TOTAL EXISTENCIAS - {etiqueta(seleccion)}"

        total = df_f['EXISTENCIA'].sum()
        st.markdown(f"""
        <div style="background-color:#e8f5e9; padding:15px; border-radius:10px; border:1px solid #4CAF50; margin-top:10px;">
            <p style="font-size:12px; color:gray; margin:0;">{titulo}</p>
            <p style="font-size:32px; font-weight:bold; margin:0; color:#2E7D32;">{int(total):,}</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.write(f"**{len(df_f)} artículos encontrados**")

        # Tabla como ya te gustó: sin proveedor
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
