import streamlit as st
import pandas as pd

st.set_page_config(page_title="Inventario RANSA", layout="wide")

st.title("📦 Inventario RANSA")

# Pestañas
tab1, tab2 = st.tabs(["📦 Pestaña 1 - INVENTARIO RANSA", "🏪 Pestaña 2 - EXISTENCIAS EN TIENDAS"])

# ============ PESTAÑA 1 ============
with tab1:
    st.subheader("INVENTARIO RANSA - Bodega")
    
    try:
        df = pd.read_excel("inventario.xlsx")
        
        # Limpiar nombres de columnas
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Buscar
        buscar = st.text_input("🔍 Buscar por CODIGO, EAN o DESCRIPCION", "", key="buscar_ransa")
        if buscar:
            buscar = buscar.upper()
            df_filtrado = df[
                df.astype(str).apply(lambda x: x.str.contains(buscar, na=False)).any(axis=1)
            ]
        else:
            df_filtrado = df
        
        # Total de UNIDADES arriba
        if "UNIDADES" in df_filtrado.columns:
            total_unidades = pd.to_numeric(df_filtrado["UNIDADES"], errors="coerce").sum()
            st.metric("TOTAL UNIDADES", f"{total_unidades:,.0f}")
        
        # Mostrar solo las columnas que querés
        columnas_mostrar = [c for c in ["CODIGO", "EAN", "DESCRIPCION", "CAJAS", "UNIDADES"] if c in df_filtrado.columns]
        st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True, hide_index=True)
        
        st.caption(f"Mostrando {len(df_filtrado)} productos")
        
    except Exception as e:
        st.error("No se pudo cargar inventario.xlsx. Revisá que el archivo esté en GitHub con ese nombre exacto.")

# ============ PESTAÑA 2 ============
with tab2:
    st.subheader("EXISTENCIAS EN TIENDAS")
    
    try:
        df2 = pd.read_excel("existencias_tiendas.xlsx")
        df2.columns = [str(c).strip().upper() for c in df2.columns]
        
        # Buscar columna de tienda
        col_tienda = None
        for posible in ["TIENDA", "SUCURSAL", "CLIENTE", "NOMBRE TIENDA"]:
            if posible in df2.columns:
                col_tienda = posible
                break
        
        if col_tienda is None:
            col_tienda = df2.columns[0]
        
        # Selector de tienda
        tiendas = sorted(df2[col_tienda].dropna().unique().tolist())
        tienda_seleccionada = st.selectbox("🏪 Elegí tu tienda:", tiendas)
        
        df_tienda = df2[df2[col_tienda] == tienda_seleccionada]
        
        # Buscar dentro de la tienda
        buscar2 = st.text_input("🔍 Buscar en esta tienda", "", key="buscar_tienda")
        if buscar2:
            buscar2 = buscar2.upper()
            df_tienda = df_tienda[
                df_tienda.astype(str).apply(lambda x: x.str.contains(buscar2, na=False)).any(axis=1)
            ]
        
        # Mostrar todo de esa tienda
        st.dataframe(df_tienda, use_container_width=True, hide_index=True)
        st.caption(f"Tienda: {tienda_seleccionada} | Productos: {len(df_tienda)}")
        
    except Exception as e:
        st.error("No se pudo cargar existencias_tiendas.xlsx. Revisá que el archivo esté en GitHub con ese nombre exacto.")
