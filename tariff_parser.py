"""
Sage 50 tariff parser
=====================
Loading and transformation of the tariff Excel files, plus persistence
of the product JSON. Extracted from presupuestador.py.

Directory creation is deferred to init_dirs(), called by the UI, so
importing this module has no side effects.

Autor: alfonsoautomatiza.com
"""

import datetime
import json
import os
import shutil
import sys
    
import pandas as pd

# ──────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────
def _resolver_app_dir(frozen: bool, module_dir: str, source_marker: bool) -> str:
    """Resolve the writable application directory for each deployment mode.

    Frozen applications persist beside the executable. Source checkouts use
    the repository directory; installed applications use per-user storage.
    """
    if frozen:
        return os.path.dirname(os.path.abspath(sys.executable))
    if source_marker:
        return os.path.abspath(module_dir)

    configured = os.environ.get("TARIFAS_DATA_DIR")
    if configured:
        return os.path.abspath(os.path.expanduser(configured))

    try:
        from platformdirs import user_data_dir
        return user_data_dir("tarifas-sage50", appauthor=False)
    except ImportError:
        if os.name == "nt":
                base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/AppData/Local")
        elif sys.platform == "darwin":
                base = os.path.expanduser("~/Library/Application Support")
        else:
                base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        return os.path.join(base, "tarifas-sage50")


def _resolver_app_dir_actual() -> str:
    """Resolve paths using the current runtime environment."""
    module_dir = os.path.dirname(os.path.abspath(__file__))
    source_marker = os.path.isfile(os.path.join(module_dir, "pyproject.toml"))
    return _resolver_app_dir(getattr(sys, "frozen", False), module_dir, source_marker)


APP_DIR = _resolver_app_dir_actual()
DATA_DIR = os.path.join(APP_DIR, "data")
DATA_JSON = os.path.join(DATA_DIR, "tarifas.json")
ORIGINALES_DIR = os.path.join(APP_DIR, "originales")
PDF_DIR = os.path.join(APP_DIR, "presupuestos")
BACKUP_DIR = os.path.join(APP_DIR, "backups")
OUT_XLSX = os.path.join(DATA_DIR, "tarifas_simplificadas.xlsx")
OUT_JSON = DATA_JSON
ESTADO_FILE = os.path.join(DATA_DIR, ".ultimo_hash")
ULTIMA_TARIFA_FILE = os.path.join(DATA_DIR, ".ultima_tarifa.json")
HOJA_TARIFA_PROCESOS = "Tarifa Intera Antes Añadir ISV"
TARIFA_PROCESOS_XLSX = "tarifa_intera_antes_anadir_isv.xlsx"


def _bootstrap_bundled_data():
    """One-file exe: copy the bundled tarifas.json (shipped inside the
    temp extraction dir) next to the executable on first run so it
    persists across sessions."""
    if not getattr(sys, "frozen", False):
        return
    bundled = os.path.join(getattr(sys, "_MEIPASS"), "data", "tarifas.json")
    if os.path.isfile(bundled) and not os.path.isfile(DATA_JSON):
        os.makedirs(DATA_DIR, exist_ok=True)
        shutil.copy2(bundled, DATA_JSON)


def _migrar_datos_legacy():
    """Best-effort migration of data files from the old module directory."""
    legacy_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    if os.path.abspath(legacy_dir) == os.path.abspath(DATA_DIR): return
    try: [shutil.copy2(os.path.join(legacy_dir, name), os.path.join(DATA_DIR, name)) for name in ("tarifas.json", "tarifas_simplificadas.xlsx", ".ultima_tarifa.json", ".ultimo_hash") if os.path.isfile(os.path.join(legacy_dir, name)) and not os.path.exists(os.path.join(DATA_DIR, name))]
    except OSError: pass


def init_dirs():
    """Create the application working directories."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(ORIGINALES_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    _migrar_datos_legacy()
    _bootstrap_bundled_data()


def leer_ultima_tarifa():
    """Lee metadatos de la última tarifa usada."""
    if os.path.exists(ULTIMA_TARIFA_FILE):
        try:
            with open(ULTIMA_TARIFA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def guardar_ultima_tarifa(nombre: str, ruta: str):
    """Guarda metadatos de la tarifa seleccionada."""
    with open(ULTIMA_TARIFA_FILE, "w", encoding="utf-8") as f:
        json.dump({"nombre": nombre, "ruta": ruta, "fecha": datetime.datetime.now().isoformat()}, f)


def directorio_sage50() -> str:
    """Devuelve la carpeta Sage 50 local, compatible con Windows y WSL."""
    if os.name == "nt":
        return r"C:\sage50"
    if os.path.isdir("/mnt/c"):
        return "/mnt/c/sage50"
    return os.path.join(APP_DIR, "sage50")


def normalizar_ruta_usuario(ruta: str) -> str:
    """Convierte rutas Windows C:\\... a /mnt/c/... cuando la app corre en WSL."""
    ruta = ruta.strip().strip('"')
    if os.name != "nt" and len(ruta) >= 3 and ruta[1:3] in (":\\", ":/"):
        unidad = ruta[0].lower()
        resto = ruta[3:].replace("\\", "/")
        return f"/mnt/{unidad}/{resto}"
    return ruta


def extraer_hoja_tarifa_procesos(xls: pd.ExcelFile, hoja_tarifa: str) -> str:
    """Guarda la hoja de trabajo de tarifas como un XLSX independiente."""
    if hoja_tarifa not in xls.sheet_names:
        raise ValueError(f"El Excel no contiene la hoja seleccionada '{hoja_tarifa}'.")

    df = pd.read_excel(xls, sheet_name=hoja_tarifa)
    destino_dir = directorio_sage50()
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, TARIFA_PROCESOS_XLSX)
    df.to_excel(destino, sheet_name=hoja_tarifa, index=False)
    return destino


def procesar_tarifa(ruta_excel: str, hoja_tarifa: str) -> tuple[int, int, str]:
    """Transforma un Excel de tarifas y devuelve (productos, errores, xlsx extraído)."""
    with pd.ExcelFile(ruta_excel) as xls:
        tarifa_procesos = extraer_hoja_tarifa_procesos(xls, hoja_tarifa)
        df = pd.read_excel(xls, sheet_name=hoja_tarifa)

        def buscar_col(patron, cols):
            patron_lower = patron.lower()
            for c in cols:
                if patron_lower in c.lower():
                    return c
            return None

        col_dto_partner = buscar_col('Dto Partner', df.columns) or 'Dto Partner Soluciones Tech Partner'
        col_dto_tech = buscar_col('Dto Tech BP', df.columns) or 'Dto Tech BP '
        col_dto_pam = buscar_col('Dto Pam', df.columns) or 'Dto Pam Base'

        rows = []
        errores = 0
        for _, r in df.iterrows():
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

                precios = {}
                val = r.get('Tarifa SSRS')
                if pd.notna(val):
                    precios['ssrs'] = float(val)
                for plan in ['Standard', 'Extra', 'Complete']:
                    for periodo, clave in [('mensual', 'MES'), ('anual', 'AÑO'), ('trienal', '3AÑOS'), ('bianual', '2AÑOS')]:
                        col = f'Tarifa {clave} {plan}'
                        if col in df.columns:
                            val = r.get(col)
                            if pd.notna(val):
                                precios[f'{plan.lower()}_{periodo}'] = float(val)
                mapa_sin_ns = {
                    'mensual': 'Tarifa Mes Sin Nivel Servicio',
                    'anual': 'Tarifa Año Sin Nivel Servicio',
                    'trienal': 'Tarifa Trienal Sin Nivel Servicio',
                    'bianual': 'Tarifa 2Años Sin Nivel Servicio',
                }
                for periodo, col in mapa_sin_ns.items():
                    if col in df.columns:
                        val = r.get(col)
                        if pd.notna(val):
                            precios[f'sin_ns_{periodo}'] = float(val)

                periodicidades = set()
                for k in precios:
                    if k.endswith('_mensual'): periodicidades.add('Mensual')
                    if k.endswith('_anual'): periodicidades.add('Anual')
                    if k.endswith('_bianual'): periodicidades.add('Bianual')
                    if k.endswith('_trienal'): periodicidades.add('Trienal')
                    if k == 'ssrs': periodicidades.add('Puntual')

                planes = set()
                if any(k.startswith('standard_') for k in precios): planes.add('Standard')
                if any(k.startswith('extra_') for k in precios): planes.add('Extra')
                if any(k.startswith('complete_') for k in precios): planes.add('Complete')
                if any(k.startswith('sin_ns_') for k in precios): planes.add('Sin Nivel')
                if 'ssrs' in precios: planes.add('Puntual')

                precio_ref = next((
                    precios.get(k) for k in [
                        'sin_ns_anual', 'complete_anual', 'extra_anual', 'standard_anual',
                        'sin_ns_mensual', 'complete_mensual', 'ssrs',
                    ]
                    if precios.get(k) is not None
                ), 0)

                rows.append({
                    'codigo': codigo, 'descripcion': descripcion,
                    'tipo_articulo': tipo_articulo, 'plataforma': plataforma,
                    'isv': isv, 'sabor': sabor, 'modulo': modulo, 'tipo': tipo,
                    'exclusivo_migracion': exclusivo_migracion, 'saa': saa,
                    'dto_partner': dto_partner, 'dto_tech_bp': dto_tech_bp,
                    'dto_pam': dto_pam,
                    'periodicidades': ', '.join(sorted(periodicidades)),
                    'planes': ', '.join(sorted(planes)),
                    'precio_referencia': precio_ref,
                    'precios_json': json.dumps(precios, ensure_ascii=False),
                })
            except Exception:
                errores += 1

    if not rows:
        raise ValueError("No se pudieron extraer productos del Excel. ¿Formato correcto?")

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    return len(rows), errores, tarifa_procesos


def cargar_productos():
    """Load the product list from the data JSON (UI caching is applied by the caller)."""
    if not os.path.exists(DATA_JSON):
        return []
    with open(DATA_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    for p in data:
        p["_precios"] = json.loads(p["precios_json"])
    return data
