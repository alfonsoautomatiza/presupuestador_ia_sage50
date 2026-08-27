# Presupuestador Sage 50

Herramienta interna para generar presupuestos en PDF y Excel a partir de una tarifa de precios, con interfaz web local (Streamlit).

> **Aviso de marca:** este es un proyecto independiente de **ALCA TIC S.L.**, sin afiliación, patrocinio ni respaldo oficial de Sage. "Sage 50" es una marca de Sage Group plc. El repositorio no distribuye tarifas ni datos comerciales reales de Sage — usa datos de ejemplo ficticios (ver [`examples/`](examples/)) con fines ilustrativos. Cada usuario debe aportar su propia tarifa de precios, obtenida por sus propios medios legítimos.

## Por qué existe esto

Generar un presupuesto a partir de una lista de precios con múltiples productos, planes y periodicidades es un trabajo manual repetitivo: buscar el producto, aplicar el plan y la periodicidad correctos, calcular descuentos, dar formato a un PDF o Excel presentable. Esta herramienta automatiza ese flujo: se carga una tarifa una vez, y a partir de ahí añadir líneas a un presupuesto y exportarlo es cuestión de segundos.

## Decisiones técnicas

- **Launcher triple (`launcher.py`)**: el mismo comando funciona en tres contextos — como herramienta instalada con pipx/uv (lanza Streamlit vía subprocess), como ejecutable standalone empaquetado con PyInstaller (lanza Streamlit programáticamente vía `streamlit.web.bootstrap`, con los archivos de datos embebidos en `sys._MEIPASS`), y en ventana nativa (`--window`, pywebview), que es el modo por defecto del `.exe`. Todos comparten la misma lógica de resolución de puerto.
- **Detección automática de puerto**: si el puerto por defecto (8599) está ocupado, se busca automáticamente el primer puerto libre en el rango 8600-9000, sin que el usuario tenga que intervenir.
- **Separación tarifa original / tarifa simplificada**: `simplificar_tarifas.py` transforma el Excel original de Sage (42 columnas, formato complejo) en una estructura JSON simplificada (17 campos) que la app consume directamente, con backup automático del original y detección de cambios por hash MD5.

## Requisitos

- Python ≥ 3.11 (solo para instalación con uv/pipx)
- [uv](https://docs.astral.sh/uv/) (recomendado) o pipx

> Para el `.exe` standalone no se necesita Python instalado.

## Instalación

### Con `uv tool` (recomendado)

```bash
# Crear symlink si el path tiene caracteres especiales (#)
mkdir -p /tmp/pytarifas
ln -sfn "/ruta/al/proyecto/pytarifas_sage50" /tmp/pytarifas/pytarifas_sage50

# Instalar
uv tool install --force "tarifas-sage50 @ file:///tmp/pytarifas/pytarifas_sage50"
```

### Con pipx

```bash
# Desde la carpeta del proyecto
pipx install --force .
```

> **Nota sobre paths con `#`**: tanto `uv tool` como `pipx` no manejan bien rutas que contengan `#`. Usa el truco del symlink si tu carpeta tiene ese carácter.

## Ejecución

```bash
# Arranca la app en el puerto 8599 (o el primer libre si está ocupado)
tarifas-sage50-gui

# Especificar puerto
tarifas-sage50-gui --port 9000

# Sin abrir navegador
tarifas-sage50-gui --no-browser

# Ventana nativa (pywebview) en lugar del navegador
tarifas-sage50-gui --window
```

La app se abre automáticamente en `http://localhost:PUERTO`.

## Probar con datos de ejemplo

El repositorio no incluye tarifas reales. Para probar la app sin datos propios, usa el archivo de ejemplo con productos y precios ficticios:

```bash
cp examples/tarifas_demo.json data/tarifas.json
```

o sube `examples/tarifas_demo.xlsx` desde el selector de archivos de la propia app.

## Generar ejecutable .exe (standalone, no necesita Python)

Requiere Windows y que las dependencias del proyecto estén instaladas.

### Con `uv` (recomendado)

```powershell
# Desde la carpeta del proyecto
uv sync
uv run --with pyinstaller python build_exe.py
```

### Con pip + python

```powershell
# Desde la carpeta del proyecto
pip install -r requirements.txt pyinstaller
python build_exe.py
```

El script verifica las dependencias, ejecuta PyInstaller con `tarifas_sage50.spec` y genera `dist/PresupuestadorSage50.exe` (~80-120 MB). Podés copiar ese `.exe` a cualquier PC con Windows — no necesita Python instalado.

**Comportamiento del `.exe`:**

```powershell
# Por defecto: abre una ventana nativa (pywebview), sin navegador
PresupuestadorSage50.exe

# Forzar modo navegador (abre el navegador en vez de la ventana nativa)
PresupuestadorSage50.exe --no-browser

# Especificar puerto
PresupuestadorSage50.exe --port 9000
```

> La primera vez que se ejecute tardará unos segundos más (descompresión interna).

## Modo desarrollo (sin instalar)

```bash
# Con uv
uv run streamlit run presupuestador.py

# Con pip + python
pip install -r requirements.txt
streamlit run presupuestador.py
```

## Cómo usar la aplicación

1. **Tarifa de precios** (sidebar): selecciona o sube un archivo Excel de tarifas. La app recuerda la última usada.
2. **Datos del cliente** (sidebar): empresa, CIF, contacto, email, condiciones de pago, IVA.
3. **Filtros**: filtra por Módulo, Sabor, Plataforma, Plan, Periodicidad o texto libre.
4. **Añadir líneas**: selecciona producto, plan, periodicidad y cantidad. Pulsa "Añadir al presupuesto".
5. **Revisar**: el resumen muestra líneas, subtotal, IVA y total.
6. **Exportar**: PDF con formato profesional, o Excel editable con los mismos datos.

## Actualizar tarifas

### Desde la app (recomendado)

En el sidebar, usa el selector de archivos o sube un Excel nuevo. Se procesa automáticamente.

### Desde línea de comandos

```bash
# Busca el .xlsx más reciente y lo transforma
python simplificar_tarifas.py

# Archivo específico
python simplificar_tarifas.py tarifas_nuevas.xlsx

# Modo vigilancia (detecta cambios automáticamente)
python simplificar_tarifas.py --vigilar
```

## Estructura del proyecto

```
pytarifas_sage50/
├── presupuestador.py        ← App Streamlit principal
├── simplificar_tarifas.py   ← Transforma Excel original → JSON simplificado
├── cli.py                   ← Entry point CLI (detección de puerto)
├── launcher.py              ← Launcher dual (dev + PyInstaller .exe)
├── build_exe.py             ← Script para generar .exe
├── tarifas_sage50.spec      ← Configuración PyInstaller
├── pyproject.toml           ← Metadata del paquete + deps
├── requirements.txt         ← Dependencias (para desarrollo)
├── LICENSE                  ← Licencia MIT
├── README.md                ← Este archivo
├── INSTRUCCIONES.md         ← Detalles técnicos y lógica de precios
├── .streamlit/config.toml   ← Configuración Streamlit
├── examples/                ← Tarifa de ejemplo con datos ficticios
├── tests/                   ← Tests del cálculo de precios
├── data/                    ← Datos reales del usuario (no versionados)
├── originales/              ← Excel originales del usuario (no versionados)
├── backups/                 ← Backups automáticos (no versionados)
└── presupuestos/            ← PDFs generados (no versionados)
```

## Dependencias

| Paquete | Uso |
|---------|-----|
| streamlit | Interfaz web |
| pandas | Procesamiento de datos |
| openpyxl | Lectura/escritura de Excel |
| reportlab | Generación de PDF |

## Licencia

MIT — ver [`LICENSE`](LICENSE).

## Autor

**ALCA TIC S.L.** — Cádiz, España
