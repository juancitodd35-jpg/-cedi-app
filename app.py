    # --- 1. MAPA CODIGO -> DESCRIPCION REAL desde inventario.xlsx ---
    mapa_descripcion = {}
    if os.path.exists("inventario.xlsx"):
        try:
            # Probar con header=1 primero, que es el bueno
            df_inv = pd.read_excel("inventario.xlsx", header=1, dtype=str)
            df_inv.columns = [str(c).strip().upper() for c in df_inv.columns]
            # Si con header=1 salen muy pocos, probar con header=0
            if len(df_inv) < 100:
                df_inv2 = pd.read_excel("inventario.xlsx", header=0, dtype=str)
                df_inv2.columns = [str(c).strip().upper() for c in df_inv2.columns]
                if len(df_inv2) > len(df_inv):
                    df_inv = df_inv2
            col_c = 'CODIGO' if 'CODIGO' in df_inv.columns else df_inv.columns[0]
            col_d = 'DESCRIPCION' if 'DESCRIPCION' in df_inv.columns else df_inv.columns[2]
            for _, r in df_inv.iterrows():
                cod = limpiar_codigo(r[col_c])
                desc = str(r[col_d]).strip()
                if cod and desc and "KELLOGG" not in desc.upper() and desc.lower() != "nan":
                    mapa_descripcion[cod] = desc
            st.caption(f"Descripciones cargadas desde inventario.xlsx: {len(mapa_descripcion)} productos")
        except Exception as e:
            st.warning(f"No pude leer inventario.xlsx para las descripciones: {e}")
    else:
        st.warning("⚠️ Falta inventario.xlsx en GitHub. Por eso no puede poner la descripción buena.")
