# Presupuestador Sage 50 — Instrucciones técnicas

## Estructura del proyecto

```
pytarifas_sage50/
├── presupuestador.py          ← App Streamlit principal
├── simplificar_tarifas.py     ← Script de transformación del Excel original
├── cli.py                     ← Entry point CLI (detección de puerto dinámico)
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
uv tool install --force "tarifas-sage50 @ file:///tmp/pytarifas/pytarifas_sage50"

# Ejecutar:
tarifas-sage50              # puerto 8599 o primer libre
tarifas-sage50 --port 9000  # puerto fijo
tarifas-sage50 --no-browser # sin abrir navegador
```

### Instalación con pipx

```bash
cd /ruta/a/pytarifas_sage50
pipx install --force .
tarifas-sage50
```

### Modo desarrollo

```bash
pip install -r requirements.txt
streamlit run presupuestador.py
```

### Actualizar a nueva versión

```bash
# Repite el comando de instalación con --force
uv tool install --force "tarifas-sage50 @ file:///tmp/pytarifas/pytarifas_sage50"
```

## Uso de la aplicación

### Selección de tarifa

1. En el **sidebar**, sección "📂 Tarifa de precios":
   - Si hay archivos Excel en `originales/` o en la raíz del proyecto, aparecen en el desplegable.
   - Se puede **subir un archivo nuevo** con el uploader.
   - Al seleccionar o subir un archivo, se procesa automáticamente y se recuerda para la próxima sesión.
   - La tarifa activa se muestra como referencia.

### Datos del cliente

2. **Sidebar izquierdo**: rellene los datos del cliente (empresa, CIF, contacto, email, condiciones de pago, IVA).

### Filtros y selección de productos

3. **Filtros**: use los filtros de Módulo, Sabor, Plataforma, Plan, Periodicidad o búsqueda por texto para localizar productos.
4. **Añadir líneas**: seleccione un producto, elija plan (Standard/Extra/Complete/Sin Nivel), periodicidad (Mensual/Anual/Trienal) y cantidad. Pulse "Añadir al presupuesto".

### Exportación

5. **Revisar**: el resumen muestra todas las líneas con subtotal, IVA y total.
6. **Generar PDF**: pulse 📄 para crear un PDF profesional. Se guarda en `presupuestos/` y se puede descargar.
7. **Generar Excel**: pulse 📊 para crear un `.xlsx` editable con los mismos datos, estilos y totales.

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
