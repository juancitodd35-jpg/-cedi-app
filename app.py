# ======================================================
# PESTAÑA 2 - YA CON COD ALMACEN + NOMBRE ALMACEN
# ======================================================
with tab2:
    st.divider()
    st.write("🏪 **Selecciona tu tienda**")

    # Mapa COD -> NOMBRE desde almacenes.csv
    mapa_nombres = {}
    if os.path.exists("almacenes.csv"):
        try:
            df_map = pd.read_csv("almacenes.csv", dtype=str)
            df_map.columns = [str(c).strip().upper() for c in df_map.columns]
            col_cod = [c for c in df_map.columns if 'COD' in c][0]
            col_nom = [c for c in df_map.columns if 'NOM' in c][0]
            for _, r in df_map.iterrows():
                mapa_nombres[str(r[col_cod]).strip().zfill(4)] = str(r[col_nom]).strip()
        except:
            pass

    # Cargar existencias desde GitHub para que lo vean todos en el teléfono
    df2_total = pd.DataFrame()
    if os.path.exists("existencias_tiendas.xlsx"):
        try:
            xl = pd.ExcelFile("existencias_tiendas.xlsx")
            lista = []
            for hoja in xl.sheet_names:
                d = pd.read_excel("existencias_tiendas.xlsx", sheet_name=hoja, header=0, dtype=str)
                if sum(['unnamed' in str(c).lower() for c in d.columns]) > 3:
                    d = pd.read_excel("existencias_tiendas.xlsx", sheet_name=hoja, header=1, dtype=str)
                d['ALMACEN_DE_HOJA'] = hoja
                lista.append(d)
            df2_total = pd.concat(lista, ignore_index=True)
            st.success("✅ Archivo cargado - ya lo pueden ver todos en el teléfono")
        except Exception as e:
            st.error(f"No pude leer existencias_tiendas.xlsx: {e}")
    else:
        st.warning("⚠️ Subí existencias_tiendas.xlsx a GitHub para que lo vean los mercaderistas.")
        archivo2 = st.file_uploader("📂 Cargar archivo (solo para vos)", type=["xlsx", "xls", "csv"], key="tiendas")
        if archivo2 is not None:
            try:
                if archivo2.name.endswith(".csv"):
                    df2_total = pd.read_csv(archivo2, dtype=str)
                    df2_total['ALMACEN_DE_HOJA'] = "CSV"
                else:
                    xl = pd.ExcelFile(archivo2)
                    lista = []
                    for hoja in xl.sheet_names:
                        d = pd.read_excel(archivo2, sheet_name=hoja, header=0, dtype=str)
                        if sum(['unnamed' in str(c).lower() for c in d.columns]) > 3:
                            d = pd.read_excel(archivo2, sheet_name=hoja, header=1, dtype=str)
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

        # Columnas exactas de tu archivo
        col_cod_alm = buscar_col(['cod almacen'])
        col_nom_alm = buscar_col(['nombre almacen'])
        col_articulo = buscar_col(['articulo'])
        col_barra = buscar_col(['barra', 'ean'])
        col_existencia = buscar_col(['existencia'])
        col_precio = buscar_col(['precio'])

        # DESCRIPCION = columna NOMBRE que NO sea NOMBRE ALMACEN
        # Si tu archivo trae NOMBRE ALMACEN y NOMBRE (producto), agarramos el segundo
        cols_nombre = [c for c in cols if c.startswith('NOMBRE')]
        if col_nom_alm in cols_nombre:
            cols_nombre.remove(col_nom_alm)
        if len(cols_nombre) > 0:
            col_descripcion = cols_nombre[0]
        else:
            col_descripcion = buscar_col(['descripcion', 'desc', 'producto'])

        # Armar tabla limpia
        df_limpio = pd.DataFrame()
        df_limpio['ARTICULO'] = df2_total[col_articulo] if col_articulo else ""
        df_limpio['BARRA'] = df2_total[col_barra] if col_barra else ""
        df_limpio['DESCRIPCION'] = df2_total[col_descripcion] if col_descripcion else ""
        df_limpio['EXISTENCIA'] = pd.to_numeric(df2_total[col_existencia], errors='coerce').fillna(0) if col_existencia else 0
        df_limpio['PRECIO VENTA CON IVA'] = pd.to_numeric(df2_total[col_precio], errors='coerce').fillna(0) if col_precio else 0

        # COD ALMACEN con ceros: 0001, no 1
        if col_cod_alm is not None:
            df_limpio['COD_ALMACEN'] = df2_total[col_cod_alm].astype(str).str.strip().str.zfill(4)
        else:
            df_limpio['COD_ALMACEN'] = df2_total['ALMACEN_DE_HOJA'].astype(str).str.strip().str.zfill(4)

        if col_nom_alm is not None:
            df_limpio['NOMBRE_ALMACEN'] = df2_total[col_nom_alm].astype(str).str.strip()
        else:
            df_limpio['NOMBRE_ALMACEN'] = df_limpio['COD_ALMACEN'].map(mapa_nombres).fillna("")

        df_limpio = df_limpio[df_limpio['ARTICULO'].notna() & (df_limpio['ARTICULO'].astype(str) != "")]

        # LISTA DESPLEGABLE: 0001 - Gigante
        codigos = sorted(df_limpio['COD_ALMACEN'].unique().tolist())

        def etiqueta(codigo):
            cs = str(codigo).strip().zfill(4)
            nombre = mapa_nombres.get(cs, "")
            if not nombre:
                # Si no hay mapa, usar el nombre que viene en el archivo
                fila = df_limpio[df_limpio['COD_ALMACEN'] == cs]
                if len(fila) > 0:
                    nombre = str(fila.iloc[0]['NOMBRE_ALMACEN'])
            return f"{cs} - {nombre}" if nombre else cs

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
            df_f = df_limpio[df_limpio['COD_ALMACEN'].astype(str) == str(seleccion)]
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
