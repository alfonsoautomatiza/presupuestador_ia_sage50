"""
Limpiador de Tarifas Sage 50
=============================
Transforma el Excel original de tarifas (42 columnas, 2 hojas)
en una estructura simplificada (17 campos) para el Presupuestador.

Uso:
    python simplificar_tarifas.py                          # busca .xlsx/.xlsm/.xls en la carpeta actual
    python simplificar_tarifas.py tarifas_nuevas.xlsm      # archivo específico
    python simplificar_tarifas.py --vigilar                # modo vigilancia automática

Ejemplo:
    1. Descargue el nuevo Excel de tarifas de Sage 50
    2. Cópielo en esta carpeta (o en la subcarpeta "originales/")
    3. Ejecute: python simplificar_tarifas.py
    4. Los datos actualizados estarán en data/tarifas.json

Autor: ALCA TIC S.L. — Cádiz, España
"""

import pandas as pd  # pyright: ignore[reportMissingImports]
import json
import os
import sys
import shutil
import hashlib
import datetime
import argparse
import time
import glob

from tariff_parser import (
    APP_DIR,
    BACKUP_DIR,
    DATA_DIR,
    ESTADO_FILE,
    ORIGINALES_DIR,
    OUT_JSON,
    OUT_XLSX,
    init_dirs,
)

# Nombre de hoja esperado (puede variar entre versiones)
HOJAS_VALIDAS = ["Tarifa Intera Antes Añadir ISV", "Tarifa Intera", "Tarifa Interanual", "Tarifas"]


def log(msg, nivel="INFO"):
    """Muestra un mensaje con timestamp."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    simbolo = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERROR": "❌"}.get(nivel, "")
    print(f"[{ts}] {simbolo}  {msg}")


def calcular_hash(filepath):
    """Calcula MD5 del archivo para detectar cambios."""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for bloque in iter(lambda: f.read(8192), b""):
            h.update(bloque)
    return h.hexdigest()


def buscar_excel(ruta_arg=None):
    """Busca el Excel de tarifas en distintas ubicaciones."""
    candidatos = []

    # 1. Ruta explícita por argumento
    if ruta_arg and os.path.isfile(ruta_arg):
        return os.path.abspath(ruta_arg)

    # 2. Carpeta "originales/"
    for ext in ("*.xlsx", "*.xlsm", "*.xls"):
        candidatos.extend(glob.glob(os.path.join(ORIGINALES_DIR, ext)))

    # 3. Carpeta raíz del proyecto
    for ext in ("*.xlsx", "*.xlsm", "*.xls"):
        for f in glob.glob(os.path.join(APP_DIR, ext)):
            if "simplificadas" not in f.lower():
                candidatos.append(f)

    if not candidatos:
        return None

    # Devolver el más reciente
    candidatos.sort(key=os.path.getmtime, reverse=True)
    return candidatos[0]


def detectar_hoja(xls):
    """Detecta automáticamente la hoja principal de tarifas."""
    for nombre in HOJAS_VALIDAS:
        if nombre in xls.sheet_names:
            return nombre
    # Fallback: la primera hoja
    return xls.sheet_names[0]


def hacer_backup(src_path):
    """Crea un backup con fecha del archivo original."""
    fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = os.path.basename(src_path)
    base, ext = os.path.splitext(nombre)
    destino = os.path.join(BACKUP_DIR, f"{base}_{fecha}{ext}")
    shutil.copy2(src_path, destino)
    log(f"Backup creado: {os.path.basename(destino)}", "OK")
    return destino


def ya_procesado(filepath):
    """Comprueba si este archivo ya fue procesado (mismo hash)."""
    nuevo_hash = calcular_hash(filepath)
    if os.path.exists(ESTADO_FILE):
        with open(ESTADO_FILE, "r") as f:
            ultimo = f.read().strip()
        if ultimo == nuevo_hash:
            return True
    return False


def guardar_estado(filepath):
    """Guarda el hash del archivo procesado."""
    h = calcular_hash(filepath)
    with open(ESTADO_FILE, "w") as f:
        f.write(h)


# ──────────────────────────────────────────────
# TRANSFORMACIÓN PRINCIPAL
# ──────────────────────────────────────────────
def transformar(filepath):
    """Lee el Excel original y genera los archivos simplificados."""
    log(f"Leyendo: {os.path.basename(filepath)}")

    xls = pd.ExcelFile(filepath)
    hoja = detectar_hoja(xls)
    log(f"Hoja detectada: '{hoja}' (de {len(xls.sheet_names)} hojas)")

    df = pd.read_excel(xls, sheet_name=hoja)
    log(f"Datos cargados: {df.shape[0]} filas × {df.shape[1]} columnas")

    # Validar columnas mínimas esperadas
    cols_requeridas = ['StartPack/ Cuota Recurrente', 'Descripción Producto', 'Tipo Articulo']
    faltantes = [c for c in cols_requeridas if c not in df.columns]
    if faltantes:
        log(f"Columnas faltantes: {faltantes}. ¿Formato correcto?", "ERROR")
        sys.exit(1)

    # --- Mapeo flexible de columnas ---
    # Busca columnas por patrones en caso de que cambien ligeramente los nombres
    def buscar_col(patron, cols):
        patron_lower = patron.lower()
        for c in cols:
            if patron_lower in c.lower():
                return c
        return None

    col_dto_partner = buscar_col('Dto Partner', df.columns) or 'Dto Partner Soluciones Tech Partner'
    col_dto_tech = buscar_col('Dto Tech BP', df.columns) or 'Dto Tech BP '
    col_dto_pam = buscar_col('Dto Pam', df.columns) or 'Dto Pam Base'

    # --- Procesar filas ---
    rows = []
    errores = 0

    for idx, r in df.iterrows():
        try:
            codigo = str(r['StartPack/ Cuota Recurrente']).strip()
            descripcion = str(r['Descripción Producto']).strip()
            tipo_articulo = str(r['Tipo Articulo']).strip()
            plataforma = str(r.get('Plataforma', '')).strip()
            isv = str(r.get('ISV', 'No')).strip()
            sabor = str(r.get('Sabor de producto', '')).strip()
            modulo = str(r.get('Módulo', '')).strip() if pd.notna(r.get('Módulo')) else ''
            tipo = str(r.get('Tipo', '')).strip()
            exclusivo_migracion = str(r.get('Articulo Exclusivo Migracion', 'No')).strip()
            saa = str(r.get('Articulo SAA', 'No')).strip()

            dto_partner = float(r.get(col_dto_partner, 0) or 0)
            dto_tech_bp = float(r.get(col_dto_tech, 0) or 0)
            dto_pam = float(r.get(col_dto_pam, 0) or 0)

            # --- Precios ---
            precios = {}

            # SSRS (servicio puntual)
            val = r.get('Tarifa SSRS')
            if pd.notna(val):
                precios['ssrs'] = float(val)

            # CON nivel de servicio
            for plan in ['Standard', 'Extra', 'Complete']:
                for periodo, clave in [('mensual', 'MES'), ('anual', 'AÑO'), ('trienal', '3AÑOS')]:
                    col = f'Tarifa {clave} {plan}'
                    if col in df.columns:
                        val = r.get(col)
                        if pd.notna(val):
                            precios[f'{plan.lower()}_{periodo}'] = float(val)

            # SIN nivel de servicio
            mapa_sin_ns = {
                'mensual': 'Tarifa Mes Sin Nivel Servicio',
                'anual': 'Tarifa Año Sin Nivel Servicio',
                'trienal': 'Tarifa Trienal Sin Nivel Servicio',
            }
            for periodo, col in mapa_sin_ns.items():
                if col in df.columns:
                    val = r.get(col)
                    if pd.notna(val):
                        precios[f'sin_ns_{periodo}'] = float(val)

            # Periodicidades y planes
            periodicidades = set()
            for k in precios:
                if 'mensual' in k: periodicidades.add('Mensual')
                if 'anual' in k: periodicidades.add('Anual')
                if 'trienal' in k: periodicidades.add('Trienal')
                if k == 'ssrs': periodicidades.add('Puntual')

            planes = set()
            if any(k.startswith('standard_') for k in precios): planes.add('Standard')
            if any(k.startswith('extra_') for k in precios): planes.add('Extra')
            if any(k.startswith('complete_') for k in precios): planes.add('Complete')
            if any(k.startswith('sin_ns_') for k in precios): planes.add('Sin Nivel')
            if 'ssrs' in precios: planes.add('Puntual')

            precio_ref = (
                precios.get('sin_ns_anual') or precios.get('complete_anual') or
                precios.get('extra_anual') or precios.get('standard_anual') or
                precios.get('sin_ns_mensual') or precios.get('complete_mensual') or
                precios.get('ssrs') or 0
            )

            rows.append({
                'codigo': codigo,
                'descripcion': descripcion,
                'tipo_articulo': tipo_articulo,
                'plataforma': plataforma,
                'isv': isv,
                'sabor': sabor,
                'modulo': modulo,
                'tipo': tipo,
                'exclusivo_migracion': exclusivo_migracion,
                'saa': saa,
                'dto_partner': dto_partner,
                'dto_tech_bp': dto_tech_bp,
                'dto_pam': dto_pam,
                'periodicidades': ', '.join(sorted(periodicidades)),
                'planes': ', '.join(sorted(planes)),
                'precio_referencia': precio_ref,
                'precios_json': json.dumps(precios, ensure_ascii=False),
            })

        except Exception as e:
            errores += 1
            log(f"Error en fila {idx + 2}: {e}", "WARN")

    if errores:
        log(f"{errores} filas con errores (se han omitido)", "WARN")

    # --- Guardar resultados ---
    result = pd.DataFrame(rows)

    with pd.ExcelWriter(OUT_XLSX, engine='openpyxl') as writer:
        result.to_excel(writer, sheet_name='Productos', index=False)

    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    guardar_estado(filepath)

    # --- Informe ---
    log(f"Productos procesados: {len(rows)}", "OK")
    log(f"Excel simplificado:   {OUT_XLSX}", "OK")
    log(f"JSON para la app:     {OUT_JSON}", "OK")

    # Estadísticas
    con_precio = sum(1 for r in rows if json.loads(r['precios_json']))
    sin_precio = len(rows) - con_precio
    modulos = len(set(r['modulo'] for r in rows if r['modulo']))
    log(f"Resumen: {con_precio} con precios, {sin_precio} sin precios, {modulos} módulos distintos")

    return len(rows)


# ──────────────────────────────────────────────
# MODO VIGILANCIA (--vigilar)
# ──────────────────────────────────────────────
def vigilar(intervalo=30):
    """Vigila las carpetas en busca de archivos nuevos o modificados."""
    log(f"Modo vigilancia activo. Comprobando cada {intervalo}s...", "INFO")
    log(f"Carpetas vigiladas: '{APP_DIR}' y '{ORIGINALES_DIR}'", "INFO")
    log("Pulse Ctrl+C para detener.\n")

    while True:
        try:
            archivo = buscar_excel()
            if archivo:
                if not ya_procesado(archivo):
                    log(f"Cambio detectado en: {os.path.basename(archivo)}")
                    hacer_backup(archivo)
                    transformar(archivo)
                    log("Esperando nuevos cambios...\n")
            time.sleep(intervalo)
        except KeyboardInterrupt:
            log("Vigilancia detenida.", "INFO")
            break
        except Exception as e:
            log(f"Error durante vigilancia: {e}", "ERROR")
            time.sleep(intervalo)


# ──────────────────────────────────────────────
# PUNTO DE ENTRADA
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Limpiador de Tarifas Sage 50 → JSON + Excel simplificado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python simplificar_tarifas.py                       Busca el Excel más reciente (.xlsx/.xlsm/.xls)
  python simplificar_tarifas.py tarifas_v2.xlsm       Archivo específico
  python simplificar_tarifas.py --vigilar             Vigila cambios automáticamente
  python simplificar_tarifas.py --vigilar --cada 60   Comprueba cada 60 segundos
        """,
    )
    parser.add_argument("archivo", nargs="?", default=None,
                        help="Ruta al Excel de tarifas (opcional, busca automáticamente)")
    parser.add_argument("--vigilar", action="store_true",
                        help="Modo vigilancia: detecta cambios automáticamente")
    parser.add_argument("--cada", type=int, default=30,
                        help="Segundos entre comprobaciones en modo vigilancia (defecto: 30)")
    parser.add_argument("--forzar", action="store_true",
                        help="Forzar reprocesamiento aunque no haya cambios")

    args = parser.parse_args()
    init_dirs()
    
    print("=" * 55)
    print("  LIMPIADOR DE TARIFAS SAGE 50")
    print("  ALCA TIC S.L. — Cádiz, España")
    print("=" * 55)
    print()

    if args.vigilar:
        vigilar(args.cada)
        return

    # Modo ejecución única
    archivo = buscar_excel(args.archivo)

    if not archivo:
        log("No se encontró ningún archivo Excel de tarifas.", "ERROR")
        log(f"Opciones:", "INFO")
        log(f"  1. Copie el Excel en: {ORIGINALES_DIR}")
        log(f"  2. O indíquelo: python simplificar_tarifas.py mi_archivo.xlsm")
        sys.exit(1)

    log(f"Archivo encontrado: {os.path.basename(archivo)}")

    if not args.forzar and ya_procesado(archivo):
        log("Este archivo ya fue procesado (sin cambios). Use --forzar para reprocesar.", "INFO")
        return

    hacer_backup(archivo)
    n = transformar(archivo)
    print()
    log(f"Proceso completado. {n} productos listos para el Presupuestador.", "OK")


if __name__ == "__main__":
    main()
