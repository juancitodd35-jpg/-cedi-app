import streamlit as st
import pandas as pd

st.set_page_config(page_title="Inventario RANSA", layout="wide")
st.title("📦 Inventario RANSA")

tab1, tab2 = st.tabs(["📦 Pestaña 1 - INVENTARIO RANSA", "🏪 Pestaña 2 - EXISTENCIAS EN TIENDAS"])

# ============ PESTAÑA 1 ============
with tab1:
    st.subheader("INVENTARIO RANSA - Bodega")
    try:
        df = pd.read_excel("inventario.xlsx")
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        buscar = st.text_input("🔍 Buscar por CODIGO, EAN o DESCRIPCION", "", key="buscar_ransa")
        if buscar:
            buscar = buscar.upper()
            df_filtrado = df[df.astype(str).apply(lambda x: x.str.contains(buscar, na=False)).any(axis=1)]
        else:
            df_filtrado = df
        
        if "UNIDADES" in df_filtrado.columns:
            total = pd.to_numeric(df_filtrado["UNIDADES"], errors="coerce").sum()
            st.metric("TOTAL UNIDADES", f"{total:,.0f}")
        
        cols = [c for c in ["CODIGO", "EAN", "DESCRIPCION", "CAJAS", "UNIDADES"] if c in df_filtrado.columns]
        st.dataframe(df_filtrado[cols], use_container_width=True, hide_index=True)
    except Exception as e:
        st.error("No se pudo cargar inventario.xlsx")

# ============ PESTAÑA 2 - ARREGLADA ============
with tab2:
    st.subheader("EXISTENCIAS EN TIENDAS")
    try:
        df2 = pd.read_excel("existencias_tiendas.xlsx")
        df2.columns = [str(c).strip().upper() for c in df2.columns]

        # --- Detectar columna de tienda (código) ---
        # Tu archivo tiene la tienda como código 4694, puede estar como TIENDA, CODIGO TIENDA, SUCURSAL, etc.
        col_tienda = None
        for c in df2.columns:
            if "TIENDA" in c or "SUCURSAL" in c or "CLIENTE" in c or "CODIGO TIENDA" in c or c == "4694":
                col_tienda = c
                break
        if col_tienda is None:
            col_tienda = df2.columns[0]

        # --- Detectar columna de nombre de tienda si existe ---
        col_nombre_tienda = None
        for c in df2.columns:
            if "NOMBRE" in c and ("TIENDA" in c or "SUCURSAL" in c or "CLIENTE" in c):
                col_nombre_tienda = c
                break
            if c in ["DESCRIPCION TIENDA", "NOMBRE SUCURSAL", "SUCURSAL NOMBRE"]:
                col_nombre_tienda = c
                break

        # --- Crear lista bonita: "4694 - NOMBRE" si hay nombre, si no solo "4694" ---
        df_tiendas_unicas = df2[[col_tienda] + ([col_nombre_tienda] if col_nombre_tienda else [])].drop_duplicates()
        
        def etiqueta_tienda(row):
            codigo = str(row[col_tienda])
            if col_nombre_tienda and pd.notna(row[col_nombre_tienda]):
                return f"{codigo} - {row[col_nombre_tienda]}"
            return codigo
        
        df_tiendas_unicas["ETIQUETA"] = df_tiendas_unicas.apply(etiqueta_tienda, axis=1)
        df_tiendas_unicas = df_tiendas_unicas.sort_values("ETIQUETA")
        
        # Buscador de tienda por código O por nombre
        tienda_elegida_etiqueta = st.selectbox("🏪 Elegí tu tienda (podés buscar por código o por nombre):", df_tiendas_unicas["ETIQUETA"].tolist())
        
        # Sacar el código de la etiqueta elegida
        codigo_elegido = df_tiendas_unicas[df_tiendas_unicas["ETIQUETA"] == tienda_elegida_etiqueta][col_tienda].values[0]
        df_tienda = df2[df2[col_tienda] == codigo_elegido].copy()

        # Buscar producto dentro de la tienda
        buscar2 = st.text_input("🔍 Buscar producto por CODIGO o DESCRIPCION en esta tienda", "", key="buscar_tienda")
        if buscar2:
            buscar2 = buscar2.upper()
            df_tienda = df_tienda[df_tienda.astype(str).apply(lambda x: x.str.contains(buscar2, na=False)).any(axis=1)]

        # --- SOLO MOSTRAR LAS COLUMNAS QUE SIRVEN, NO TODAS ---
        # Si tu Excel tiene estos nombres, solo muestra estos
        columnas_buenas = []
        for c in ["CODIGO", "EAN", "DESCRIPCION", "DESCRIPCION PRODUCTO", "NOMBRE PRODUCTO", "UNIDAD MEDIDA", "UNIDAD", "EXISTENCIA", "EXISTENCIAS", "PRECIO VENTA CON IVA", "PRECIO VENTA", "PRECIO"]:
            if c in df_tienda.columns and c not in columnas_buenas:
                columnas_buenas.append(c)
        
        # Si no encontró ninguna, muestra las primeras 6 para no dejarlo vacío
        if not columnas_buenas:
            columnas_buenas = list(df_tienda.columns[:6])

        st.dataframe(df_tienda[columnas_buenas], use_container_width=True, hide_index=True)
        st.caption(f"Tienda: {tienda_elegida_etiqueta} | Productos: {len(df_tienda)}")

    except Exception as e:
        st.error(f"No se pudo cargar existencias_tiendas.xlsx: {e}")
