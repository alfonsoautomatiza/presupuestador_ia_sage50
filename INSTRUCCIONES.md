# Presupuestador Sage 50 — Instrucciones técnicas

## Estructura del proyecto

```
pytarifas_sage50/
├── presupuestador.py          ← Presentación Gradio (presupuestador.py mantiene compatibilidad)
├── simplificar_tarifas.py     ← Script de transformación del Excel original
├── cli.py                     ← Entry point único (puerto, browser y ventana nativa)
├── psage.spec                 ← Configuración del ejecutable PyInstaller
├── pydobj.toml                ← Configuración de wertybuild
├── c/product.json             ← Fuente de verdad de versión y metadatos
├── pyproject.toml             ← Metadata del paquete, dependencias, entry point
├── requirements.txt           ← Dependencias Python (desarrollo)
├── INSTRUCCIONES.md           ← Este archivo
├── data/
│   ├── tarifas.json           ← Datos simplificados (productos, 17 campos)
│   ├── tarifas_simplificadas.xlsx  ← Excel limpio de consulta
│   └── .ultima_tarifa.json    ← Recordar última tarifa seleccionada
├── originales/                ← Excel originales de Sage
├── backups/                   ← Backups automáticos
└── presupuestos/              ← PDFs y Excel generados
```

En desarrollo estas carpetas viven en el repositorio. El `.exe` guarda sus datos junto al ejecutable; las instalaciones con `uv` o `pipx` usan una carpeta de datos por usuario. Se puede cambiar con `TARIFAS_DATA_DIR` y se migran automáticamente los datos de instalaciones anteriores.

## Qué se ha simplificado

El Excel original tiene **2 hojas y 42 columnas** con mucha redundancia. Se reduce a **17 campos útiles**:

| Campo original (42 cols)                          | Campo simplificado              |
|---------------------------------------------------|---------------------------------|
| StartPack/ Cuota Recurrente                       | `codigo`                        |
| Descripción Producto                              | `descripcion`                   |
| Tipo Articulo (RR/SSRS)                           | `tipo_articulo`                 |
| Plataforma                                        | `plataforma`                    |
| ISV                                               | `isv`                           |
| Sabor de producto                                 | `sabor`                         |
| Módulo                                            | `modulo`                        |
| Tipo                                              | `tipo`                          |
| Articulo Exclusivo Migracion                      | `exclusivo_migracion`           |
| Articulo SAA                                      | `saa`                           |
| Dto Partner + Dto Tech BP + Dto Pam Base          | `dto_partner`, `dto_tech_bp`, `dto_pam` |
| 12 cols de tarifa × periodicidad × plan           | `precios_json` (diccionario)    |
| Periodicidades y niveles servicio (8 cols)         | `periodicidades`, `planes`      |
| Precio más representativo                         | `precio_referencia`             |

**Columnas eliminadas** (vacías o sin datos): Tarifa 2AÑOS (todas), Tarifa Bienal sin NS, columna "(Vacio)", ISV Classificacion (redundante con Módulo).

## Instalación y ejecución

### Instalación con uv tool (recomendado)

```bash
# Si el path tiene #, usar symlink:
mkdir -p /tmp/pytarifas
ln -sfn "/ruta/a/pytarifas_sage50" /tmp/pytarifas/pytarifas_sage50
uv tool install --force "psage @ file:///tmp/pytarifas/pytarifas_sage50"

# Ejecutar:
psage              # puerto 8599 o primer libre
psage --port 9000  # puerto fijo
psage --no-browser # sin abrir navegador
psage --window     # ventana nativa con pywebview
```

El ejecutable congelado usa `psage` como entrada y abre la ventana nativa por defecto; `--window` fuerza ese modo y `--no-browser` evita el navegador.

### Generar el ejecutable

Los builds del `.exe` se ejecutan únicamente en Windows. Requieren `uv` y `pydobj` disponibles en `PATH`:

```powershell
uv sync
wertybuild exe
# Salida: dist/psage/psage.exe
```

Para refrescar incrementalmente las fuentes empaquetadas, usa `wertybuild pyd`. La versión y los metadatos del ejecutable tienen como fuente de verdad `c/product.json`.

### Instalación con pipx

```bash
cd /ruta/a/pytarifas_sage50
pipx install --force .
psage
```

### Modo desarrollo

```bash
pip install -r requirements.txt
psage
```

### Actualizar a nueva versión

```bash
# Repite el comando de instalación con --force
uv tool install --force "psage @ file:///tmp/pytarifas/pytarifas_sage50"
```

## Uso de la aplicación

### Selección de tarifa

1. En el **sidebar**, sección "📂 Tarifa de precios":
   - Si hay archivos Excel en `originales/` o en la raíz del proyecto, aparecen en el desplegable.
   - Se puede **subir un archivo nuevo** con el uploader.
   - Al seleccionar o subir un archivo, se procesa automáticamente y se recuerda para la próxima sesión.
   - La tarifa activa se muestra como referencia.

### Datos del cliente

1. **Sidebar izquierdo**: rellene los datos del cliente (empresa, CIF, contacto, email, condiciones de pago, IVA).

### Filtros y selección de productos

1. **Filtros**: use los filtros de Módulo, Sabor, Plataforma, Plan, Periodicidad o búsqueda por texto para localizar productos.
2. **Añadir líneas**: seleccione un producto, elija plan (Standard/Extra/Complete/Sin Nivel), periodicidad (Mensual/Anual/Trienal) y cantidad. Pulse "Añadir al presupuesto".

### Exportación

1. **Revisar**: el resumen muestra todas las líneas con subtotal, IVA y total.
2. **Generar PDF**: pulse 📄 para crear un PDF profesional. Se guarda en `presupuestos/` y se puede descargar.
    3. **Generar Excel**: pulse 📊 para crear un `.xlsx` editable con los mismos datos, estilos y totales. Las exportaciones incluyen el código Sage y una fila única «TOTAL + IVA».
    4. **Generar JSON para IA**: pulse 🤖 para crear un JSON UTF-8, estricto y versionado (`tarifas-sage50/oferta/v1`) con tarifa, cliente, líneas completas, agrupaciones y totales. Conserva los valores numéricos para ingestión y cálculos automáticos; no incluye la ruta absoluta de la tarifa.

       El JSON contiene CIF y email. Revise la política de privacidad antes de enviarlo a una IA externa.

### Plantillas y agrupación

Las plantillas se guardan en `data/plantillas.json` en desarrollo; en modo `.exe` junto al ejecutable y en instalaciones con `uv` o `pipx` en la carpeta de datos de usuario configurada para el despliegue. Solo contienen líneas y observaciones. En el resumen se puede agrupar por plan o periodicidad; cada grupo muestra su subtotal y el criterio se aplica también al PDF y Excel.

## Lógica de precios

Los precios se resuelven en este orden de prioridad:

1. **Plan + Periodicidad** (ej. `complete_anual` = 949 €)
2. **Sin Nivel de Servicio + Periodicidad** (ej. `sin_ns_anual` = 132 €)
3. **SSRS** para servicios puntuales

Los descuentos se aplican en cascada: `Neto = Precio × (1 - dto_partner) × (1 - dto_tech_bp) × (1 - dto_pam)`.

## Detección de puerto dinámico

El CLI (`cli.py`) comprueba si el puerto 8599 está libre:

- **Libre**: lo usa directamente.
- **Ocupado**: busca el primer puerto libre desde 8600 hasta 9000 y lo usa.
- Se puede forzar un puerto con `--port`.
- El puerto asignado se muestra en consola.

## Regenerar datos desde el Excel original (CLI)

Si las tarifas cambian y no quieres usar la app:

```bash
python simplificar_tarifas.py                          # busca el .xlsx más reciente
python simplificar_tarifas.py tarifas_nuevas.xlsx      # archivo específico
python simplificar_tarifas.py --vigilar                # modo vigilancia automática
python simplificar_tarifas.py --forzar                 # forzar reprocesamiento
```

Esto regenerará `data/tarifas.json` y `data/tarifas_simplificadas.xlsx`.
