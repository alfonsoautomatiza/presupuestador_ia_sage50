"""
Presupuestador Sage 50 — Aplicación Streamlit
=============================================
Genera presupuestos profesionales a partir de las tarifas de Sage 50.
Salida en PDF.

Autor: ALCA TIC S.L.
"""

import datetime
import glob
import os

import pandas as pd
import streamlit as st

# Pure business logic, re-exported so `from presupuestador import ...` keeps working
from models import (  # noqa: F401
    PERIODICIDADES_FILTRABLES,
    PERIODICIDAD_LABELS,
    PERIODICIDAD_PRIORIDAD,
    PLAN_LABELS,
    calcular_dto,
    csv_a_set,
    cumple_filtro_periodicidad,
    obtener_precio,
    precio_referencia_por_periodicidad,
    resolver_periodicidad_referencia,
)
from tariff_parser import (
    APP_DIR,
    DATA_JSON,
    HOJA_TARIFA_PROCESOS,
    ORIGINALES_DIR,
    PDF_DIR,
    cargar_productos as _cargar_productos_sin_cache,
    guardar_ultima_tarifa,
    init_dirs,
    leer_ultima_tarifa,
    normalizar_ruta_usuario,
    procesar_tarifa,
)
from pdf_generator import generar_pdf
from excel_generator import generar_excel


# ──────────────────────────────────────────────
# CARGA DE DATOS
# ──────────────────────────────────────────────
@st.cache_data
def cargar_productos():
    return _cargar_productos_sin_cache()


# ──────────────────────────────────────────────
# INTERFAZ STREAMLIT
# ──────────────────────────────────────────────
def main():
    init_dirs()
    st.set_page_config(
        page_title="Presupuestador Sage 50",
        page_icon="📋",
        layout="wide",
    )

    st.title("📋 Presupuestador Sage 50")
    st.caption("Genera presupuestos profesionales a partir de las tarifas oficiales de Sage 50")
    hay_datos_cargados = os.path.exists(DATA_JSON)

    # ── Sidebar: Tarifa ──
    with st.sidebar:
        st.header("📂 Tarifa de precios")
        ultima = leer_ultima_tarifa()
        if ultima.get("nombre"):
            st.caption(f"Tarifa actual: **{ultima['nombre']}**")
        else:
            st.caption("No hay tarifa cargada")

        ruta_manual = ""
        procesar_ruta_manual = False
        ruta_a_procesar = None
        nombre_tarifa = None
        tarifa_pendiente = st.session_state.get("tarifa_pendiente")
        if not hay_datos_cargados:
            st.info("Indique la ubicación del último fichero tarificador para cargar los datos iniciales.")
            ruta_manual = st.text_input(
                "Ubicación del último fichero tarificador",
                value=ultima.get("ruta", ""),
                placeholder=r"C:\sage50\tarifa.xlsm",
                help=f"Se preseleccionará la hoja '{HOJA_TARIFA_PROCESOS}' si existe.",
            )
            procesar_ruta_manual = st.button("Seleccionar fichero tarificador")

        # Buscar archivos Excel locales en originales/ y en la raíz
        archivos_locales = []
        for patron in ("*.xlsx", "*.xlsm", "*.xls"):
            archivos_locales.extend(glob.glob(os.path.join(ORIGINALES_DIR, patron)))
            for f in glob.glob(os.path.join(APP_DIR, patron)):
                if "simplificadas" not in f.lower():
                    archivos_locales.append(f)
        archivos_locales = sorted(set(archivos_locales), key=os.path.getmtime, reverse=True)

        opciones = {"-- Sin cambios --": None}
        for f in archivos_locales:
            opciones[os.path.basename(f)] = f

        seleccion = st.selectbox(
            "Archivo de tarifas",
            options=list(opciones.keys()),
            index=0,
            help="Seleccione un Excel de tarifas local o suba uno nuevo",
        )

        archivo_subido = st.file_uploader(
            "📤 Subir nuevo Excel",
            type=["xlsx", "xlsm", "xls"],
            help="Suba un archivo Excel de tarifas nuevo",
        )

        if archivo_subido is not None:
            # Guardar archivo subido
            destino = os.path.join(ORIGINALES_DIR, os.path.basename(archivo_subido.name))
            with open(destino, "wb") as f:
                f.write(archivo_subido.getvalue())
            ruta_a_procesar = destino
            nombre_tarifa = archivo_subido.name
        elif procesar_ruta_manual and ruta_manual:
            ruta_manual_normalizada = normalizar_ruta_usuario(ruta_manual)
            if not os.path.isfile(ruta_manual_normalizada):
                st.error(f"❌ No se encontró el fichero: {ruta_manual}")
                return
            ruta_a_procesar = ruta_manual_normalizada
            nombre_tarifa = os.path.basename(ruta_manual_normalizada)
            st.session_state.tarifa_pendiente = {
                "ruta": ruta_a_procesar,
                "nombre": nombre_tarifa,
            }
        elif seleccion != "-- Sin cambios --":
            ruta_seleccionada = opciones[seleccion]
            ruta_a_procesar = ruta_seleccionada
            nombre_tarifa = seleccion
        elif tarifa_pendiente:
            ruta_a_procesar = tarifa_pendiente.get("ruta")
            nombre_tarifa = tarifa_pendiente.get("nombre")

        if ruta_a_procesar and nombre_tarifa:
            try:
                with pd.ExcelFile(ruta_a_procesar) as xls:
                    hojas_disponibles = xls.sheet_names
            except Exception as e:
                st.error(f"❌ No se pudieron leer las hojas de {nombre_tarifa}: {e}")
                return

            if not hojas_disponibles:
                st.error(f"❌ El Excel {nombre_tarifa} no contiene hojas.")
                return

            if HOJA_TARIFA_PROCESOS in hojas_disponibles:
                hoja_index = hojas_disponibles.index(HOJA_TARIFA_PROCESOS)
            else:
                hoja_index = 0
                st.warning(
                    f"⚠️ No se encontró la hoja predeterminada '{HOJA_TARIFA_PROCESOS}'. "
                    "Revise la hoja seleccionada antes de procesar."
                )

            hoja_tarifa = st.selectbox(
                "Hoja del Excel a procesar",
                options=hojas_disponibles,
                index=hoja_index,
                help="Seleccione la hoja que contiene la tarifa de Sage 50.",
            )
            procesar = st.button("Procesar hoja seleccionada")

            if procesar:
                with st.spinner(f"Procesando {nombre_tarifa} / {hoja_tarifa}..."):
                    try:
                        n, errores, tarifa_procesos = procesar_tarifa(ruta_a_procesar, hoja_tarifa)
                    except ValueError as e:
                        st.error(f"❌ {e}")
                        return
                    guardar_ultima_tarifa(nombre_tarifa, ruta_a_procesar)
                    st.session_state.pop("tarifa_pendiente", None)
                    st.cache_data.clear()
                    msg = f"✅ {n} productos cargados desde {nombre_tarifa}, hoja {hoja_tarifa}. Hoja extraída en {tarifa_procesos}"
                    if errores > 0:
                        msg += f" ({errores} filas con errores omitidas)"
                        st.warning(msg)
                    else:
                        st.success(msg)
                    st.rerun()

    productos = cargar_productos()
    if not productos:
        st.warning("⚠️ No hay productos cargados. Suba o seleccione un archivo Excel de tarifas en la barra lateral.")
        return

    # ── Sidebar: Datos del cliente ──
    with st.sidebar:
        st.divider()
        st.header("🏢 Datos del cliente")
        empresa = st.text_input("Empresa")
        cif = st.text_input("CIF / NIF")
        contacto = st.text_input("Persona de contacto")
        email = st.text_input("Email")
        validez = st.selectbox(
            "Validez del presupuesto", ["30 días", "15 días", "60 días", "90 días"]
        )
        condiciones = st.text_input("Condiciones de pago", value="Pago a 30 días")
        iva_pct = st.number_input("IVA (%)", min_value=0, max_value=21, value=21, step=1) / 100
        notas = st.text_area("Observaciones")

    # ── Filtros ──
    st.subheader("🔍 Buscar productos")
    col_fp1, col_fp2 = st.columns(2)
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    modulos = sorted(set(p["modulo"] for p in productos if p["modulo"]))
    sabores = sorted(set(p["sabor"] for p in productos))
    plataformas = sorted(set(p["plataforma"] for p in productos))
    tipos = sorted(set(p["tipo"] for p in productos))
    planes = sorted({plan for p in productos for plan in csv_a_set(p["planes"])})
    periodicidades = sorted(
        {
            periodicidad
            for p in productos
            for periodicidad in csv_a_set(p["periodicidades"])
            if periodicidad in PERIODICIDADES_FILTRABLES
        }
    )

    with col_fp1:
        filtro_plan = st.multiselect("Plan / Nivel", planes)
    with col_fp2:
        filtro_periodicidad = st.multiselect("Periodicidad", periodicidades)

    with col_f1:
        filtro_modulo = st.multiselect("Módulo", modulos)
    with col_f2:
        filtro_sabor = st.multiselect("Sabor", sabores)
    with col_f3:
        filtro_plataforma = st.multiselect("Plataforma", plataformas)
    with col_f4:
        filtro_texto = st.text_input("Buscar por nombre", "")

    # Aplicar filtros
    filtrados = productos
    if filtro_plan:
        filtro_plan_set = set(filtro_plan)
        filtrados = [p for p in filtrados if csv_a_set(p["planes"]) & filtro_plan_set]
    if filtro_periodicidad:
        filtrados = [p for p in filtrados if cumple_filtro_periodicidad(p, filtro_periodicidad)]
    if filtro_modulo:
        filtrados = [p for p in filtrados if p["modulo"] in filtro_modulo]
    if filtro_sabor:
        filtrados = [p for p in filtrados if p["sabor"] in filtro_sabor]
    if filtro_plataforma:
        filtrados = [p for p in filtrados if p["plataforma"] in filtro_plataforma]
    if filtro_texto:
        texto_lower = filtro_texto.lower()
        filtrados = [
            p
            for p in filtrados
            if texto_lower in p["descripcion"].lower() or texto_lower in p["codigo"].lower()
        ]

    st.info(f"Mostrando **{len(filtrados)}** productos de {len(productos)} disponibles")

    # ── Catálogo ──
    if filtrados:
        df_display = pd.DataFrame(
            [
                {
                    "Código": p["codigo"],
                    "Descripción": p["descripcion"],
                    "Módulo": p["modulo"],
                    "Sabor": p["sabor"],
                    "Plataforma": p["plataforma"],
                    "Tipo": p["tipo_articulo"],
                    "Periodicidades": p["periodicidades"],
                    "Planes": p["planes"],
                    "Precio Ref.": f"{precio_referencia_por_periodicidad(p, resolver_periodicidad_referencia(p, filtro_periodicidad)):.2f} €",
                    "Dto Partner": f"{p['dto_partner']:.0%}" if p["dto_partner"] > 0 else "-",
                }
                for p in filtrados
            ]
        )
        st.dataframe(df_display, width="stretch", height=300)

    # ── Líneas del presupuesto ──
    st.subheader("📝 Líneas del presupuesto")

    if "lineas" not in st.session_state:
        st.session_state.lineas = []

    # Formulario para añadir línea
    with st.expander("➕ Añadir producto al presupuesto", expanded=True):
        col_a1, col_a2 = st.columns([3, 1])

        # Map: disambiguated label → index into filtrados (direct, no codigo indirection)
        opciones_producto = {}
        for i, p in enumerate(filtrados):
            label = f"{p['descripcion']} [{p['codigo']}] ({p['periodicidades']})"
            disambig = label
            n = 2
            while disambig in opciones_producto:
                disambig = f"{label} #{n}"
                n += 1
            opciones_producto[disambig] = i

        if not opciones_producto:
            st.warning("No hay productos con los filtros actuales. Ajuste los filtros.")
        else:
            with col_a1:
                seleccion = st.selectbox("Producto", list(opciones_producto.keys()))
            with col_a2:
                cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)

            idx = opciones_producto[seleccion]
            prod = filtrados[idx]

            col_b1, col_b2, col_b3 = st.columns(3)

            # Planes disponibles
            planes_disp = [p.strip() for p in prod["planes"].split(",") if p.strip()]
            with col_b1:
                plan_sel = st.selectbox(
                    "Plan / Nivel", planes_disp if planes_disp else ["Sin Nivel"]
                )

            # Periodicidades disponibles
            periodos_disp = [p.strip() for p in prod["periodicidades"].split(",") if p.strip()]
            with col_b2:
                periodo_sel = st.selectbox(
                    "Periodicidad", periodos_disp if periodos_disp else ["Anual"]
                )

            precio_unit = obtener_precio(prod, plan_sel, periodo_sel)
            dto_total = 1 - (1 - prod["dto_partner"]) * (1 - prod["dto_tech_bp"]) * (
                1 - prod["dto_pam"]
            )
            precio_neto = calcular_dto(
                precio_unit, prod["dto_partner"], prod["dto_tech_bp"], prod["dto_pam"]
            )

            with col_b3:
                st.metric("Precio unitario", f"{precio_unit:.2f} €")
                if dto_total > 0:
                    st.caption(f"Dto. acumulado: {dto_total:.0%} → Neto: {precio_neto:.2f} €")

            total_linea = precio_neto * cantidad

            if st.button("✅ Añadir al presupuesto", type="primary"):
                st.session_state.lineas.append(
                    {
                        "codigo": prod["codigo"],
                        "descripcion": prod["descripcion"],
                        "plan": plan_sel,
                        "periodicidad": periodo_sel,
                        "cantidad": cantidad,
                        "precio_unitario": precio_unit,
                        "dto_total_pct": dto_total,
                        "precio_neto": precio_neto,
                        "total": total_linea,
                    }
                )
                st.success(f"Añadido: {prod['descripcion']} x{cantidad} = {total_linea:.2f} €")
                st.rerun()

    # ── Mostrar líneas actuales ──
    if st.session_state.lineas:
        st.markdown("---")
        st.subheader("📄 Resumen del presupuesto")

        for i, linea in enumerate(st.session_state.lineas):
            col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 1, 0.5])
            with col1:
                st.write(f"**{linea['descripcion']}** ({linea['plan']} / {linea['periodicidad']})")
            with col2:
                st.write(f"x{linea['cantidad']}")
            with col3:
                st.write(f"{linea['precio_unitario']:.2f} €")
            with col4:
                st.write(f"**{linea['total']:.2f} €**")
            with col5:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.lineas.pop(i)
                    st.rerun()

        subtotal = sum(l["total"] for l in st.session_state.lineas)
        iva = subtotal * iva_pct
        total = subtotal + iva

        st.markdown("---")
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            st.metric("Subtotal", f"{subtotal:.2f} €")
        with col_t2:
            st.metric(f"IVA ({iva_pct:.0%})", f"{iva:.2f} €")
        with col_t3:
            st.metric("TOTAL", f"{total:.2f} €")

        # ── Generar PDF ──
        st.markdown("---")
        col_g1, col_g2 = st.columns([1, 3])
        with col_g1:
            if st.button("📄 Generar PDF", type="primary"):
                datos_cliente = {
                    "empresa": empresa,
                    "cif": cif,
                    "contacto": contacto,
                    "email": email,
                    "validez": validez,
                    "condiciones": condiciones,
                }
                totales = {
                    "subtotal": subtotal,
                    "iva_pct": iva_pct,
                    "iva": iva,
                    "total": total,
                }

                pdf_bytes, num_pre = generar_pdf(
                    datos_cliente, st.session_state.lineas, totales, notas
                )

                # Guardar en disco
                pdf_path = os.path.join(PDF_DIR, f"{num_pre}.pdf")
                with open(pdf_path, "wb") as f:
                    f.write(pdf_bytes)

                st.session_state.ultimo_pdf = pdf_bytes
                st.session_state.ultimo_pdf_nombre = f"{num_pre}.pdf"
                st.success(f"PDF generado: {num_pre}.pdf")

        if "ultimo_pdf" in st.session_state:
            with col_g2:
                st.download_button(
                    label="⬇️ Descargar PDF",
                    data=st.session_state.ultimo_pdf,
                    file_name=st.session_state.ultimo_pdf_nombre,
                    mime="application/pdf",
                )

        # ── Generar Excel ──
        col_x1, col_x2 = st.columns([1, 3])
        with col_x1:
            if st.button("📊 Generar Excel", type="secondary"):
                excel_bytes = generar_excel(
                    datos_cliente={
                        "empresa": empresa, "cif": cif, "contacto": contacto,
                        "email": email, "validez": validez, "condiciones": condiciones,
                    },
                    lineas=st.session_state.lineas,
                    totales={"subtotal": subtotal, "iva_pct": iva_pct, "iva": iva, "total": total},
                    notas=notas,
                )
                hoy = datetime.date.today().strftime("%Y%m%d")
                excel_name = f"presupuesto_{hoy}.xlsx"
                st.session_state.ultimo_excel = excel_bytes
                st.session_state.ultimo_excel_nombre = excel_name
                st.success(f"Excel generado: {excel_name}")

        if "ultimo_excel" in st.session_state:
            with col_x2:
                st.download_button(
                    label="⬇️ Descargar Excel",
                    data=st.session_state.ultimo_excel,
                    file_name=st.session_state.ultimo_excel_nombre,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        # Botón limpiar
        if st.button("🧹 Limpiar presupuesto"):
            st.session_state.lineas = []
            for key in ["ultimo_pdf", "ultimo_pdf_nombre", "ultimo_excel", "ultimo_excel_nombre"]:
                st.session_state.pop(key, None)
            st.rerun()

    else:
        st.info("Añada productos al presupuesto utilizando los filtros y el formulario de arriba.")


if __name__ == "__main__":
    main()
