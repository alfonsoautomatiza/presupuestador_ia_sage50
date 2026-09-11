# psage — Presupuestador Sage 50

**psage** es una herramienta independiente para preparar presupuestos a partir de un fichero Excel de tarifas. Permite seleccionar productos, aplicar planes, periodicidades y descuentos, revisar los totales y exportar el presupuesto a PDF, Excel o JSON.

Este proyecto se publica como parte de la iniciativa de transparencia y colaboración de [alfonsoautomatiza.com/colaboramos](https://alfonsoautomatiza.com/colaboramos), para que cualquier socio pueda revisar qué hace el programa y cómo se construye.

> **Importante:** psage es un proyecto independiente de **ALCA TIC S.L.** No está afiliado, patrocinado ni respaldado oficialmente por Sage. “Sage 50” es una marca de Sage Group plc. El repositorio no contiene tarifas reales, credenciales ni datos comerciales de clientes.

## Para qué sirve

psage evita repetir manualmente estas tareas:

1. Buscar un producto en una tarifa extensa.
2. Elegir el plan y la periodicidad correctos.
3. Aplicar descuentos acumulados.
4. Calcular subtotal, IVA y total.
5. Preparar un documento presentable para el cliente.

La aplicación funciona localmente en el equipo del usuario. No necesita enviar la tarifa ni el presupuesto a un servidor externo.

## Qué hace

- Lee tarifas Excel (`.xlsx`, `.xlsm` o `.xls`).
- Permite filtrar el catálogo por módulo, sabor, plataforma, plan, periodicidad o texto.
- Calcula precios netos aplicando los descuentos configurados en la tarifa.
- Permite añadir varias líneas, cantidades y observaciones.
- Agrupa las líneas por plan o periodicidad y muestra subtotales.
- Guarda y recupera plantillas de líneas y observaciones.
- Genera:
  - **PDF** para enviar o presentar al cliente.
  - **Excel** para revisar o editar manualmente.
  - **JSON versionado** para integración técnica o cálculos asistidos por IA.
- Recuerda la última tarifa utilizada.
- Busca automáticamente un puerto local libre si el puerto habitual está ocupado.

## Qué no hace

- No se conecta automáticamente con Sage 50.
- No modifica el Excel original.
- No envía datos a Sage ni a servicios de IA.
- No incluye una lista oficial de precios de Sage.
- No sustituye la validación comercial, fiscal o contractual de un presupuesto.
- No debe usarse para compartir información personal con terceros sin autorización.

## Uso rápido — recomendado para usuarios no técnicos

### Opción A: ejecutable para Windows

El responsable del proyecto puede entregar una carpeta con:

```text
psage/
└── psage.exe
```

Para usarlo:

1. Copiá la carpeta en el equipo Windows.
2. Abrí `psage.exe`.
3. Se abrirá la aplicación en una ventana local.
4. Cargá tu fichero Excel de tarifas desde **📂 Tarifa de precios**.
5. Completá **🏢 Datos del cliente**.
6. En **🔍 Catálogo**, buscá y añadí los productos.
7. Revisá las líneas y los totales en **📝 Presupuesto**.
8. Generá el documento desde **📤 Exportar**.

El ejecutable no requiere instalar Python ni pipx. La primera ejecución puede tardar unos segundos más.

### Opción B: instalación con pipx

Esta opción requiere tener Python y pipx instalados. Desde una terminal ubicada en la carpeta del proyecto:

```bash
pipx install --force .
psage
```

Comandos disponibles:

```bash
psage                  # abre la aplicación en el navegador
psage --window         # intenta abrir una ventana nativa
psage --port 9000      # usa un puerto concreto
psage --no-browser     # no abre el navegador automáticamente
```

La aplicación se ejecuta localmente, normalmente en `http://localhost:8599`.

## Cómo usar la aplicación

### 1. Cargar la tarifa

En la barra lateral **📂 Tarifa de precios**:

- Seleccioná una tarifa ya disponible; o
- subí un Excel nuevo; o
- indicá manualmente la ubicación del archivo.

Después elegí la hoja que contiene los productos y pulsá **Procesar hoja seleccionada**.

> psage conserva el Excel original y trabaja con una copia de datos procesada. No sobrescribe el archivo original.

### 2. Completar los datos del cliente

En **🏢 Datos del cliente** introducí, cuando corresponda:

- Empresa.
- CIF/NIF.
- Persona de contacto.
- Email.
- Validez del presupuesto.
- Condiciones de pago.
- Porcentaje de IVA.

Estos datos pueden aparecer en las exportaciones. Revisalos antes de compartir un PDF, Excel o JSON.

### 3. Buscar productos

En **🔍 Catálogo** usá los filtros disponibles. También podés buscar por nombre o código.

Seleccioná un producto, su plan, periodicidad y cantidad. El programa muestra el precio unitario, el descuento acumulado y el precio neto antes de añadirlo al presupuesto.

### 4. Revisar el presupuesto

En **📝 Presupuesto** podés:

- revisar las líneas;
- eliminar productos;
- agrupar por plan o periodicidad;
- comprobar subtotales, IVA y total.

### 5. Exportar

En **📤 Exportar** elegí el formato necesario:

| Formato | Para qué sirve |
| --- | --- |
| PDF | Presentación profesional para el cliente |
| Excel | Revisión y edición manual |
| JSON | Integraciones, automatizaciones y cálculos técnicos |

El JSON usa el schema estable `tarifas-sage50/oferta/v1`. Puede contener CIF, email y otros datos del cliente: tratá ese archivo como información sensible.

## Datos y privacidad

psage funciona localmente. Los archivos se guardan en el equipo del usuario:

- En modo desarrollo: `data/`, `originales/`, `backups/` y `presupuestos/` dentro del proyecto.
- En instalaciones con pipx: una carpeta de datos del usuario, por ejemplo `~/.local/share/tarifas-sage50` en Linux o `%LOCALAPPDATA%\\tarifas-sage50` en Windows.
- En el ejecutable: junto al ejecutable, según la configuración de distribución.

La ubicación se puede cambiar con la variable `TARIFAS_DATA_DIR`.

Antes de publicar o enviar un presupuesto:

- verificá los datos del cliente;
- no compartas la tarifa si no tenés autorización;
- no envíes el JSON a una IA externa sin revisar su contenido y la política aplicable;
- no subas credenciales, tokens ni archivos comerciales al repositorio público.

## Cómo se construye el ejecutable

El `.exe` se genera con **wertybuild**, el motor unificado de compilación usado por los proyectos de AlfonsoAutomatiza. wertybuild ejecuta PyInstaller dentro del entorno bloqueado por `uv` y usa `c/product.json` como fuente de verdad de la versión y los metadatos.

La compilación de Windows debe hacerse en Windows. El proyecto no intenta compilar un `.exe` de Windows desde Linux o macOS.

### Requisitos para compilar

En el equipo de compilación se necesita:

- Windows.
- Python instalado para las herramientas de desarrollo.
- [uv](https://docs.astral.sh/uv/).
- `wertybuild` instalado y disponible en `PATH`.
- `pydobj` disponible en `PATH`.
- Una copia completa del repositorio.

### Compilación completa

Desde la raíz del proyecto:

```powershell
uv sync
wertybuild exe --edition base
```

El resultado esperado es:

```text
dist/psage/psage.exe
```

Para actualizar únicamente los componentes compilados incrementales, cuando corresponda:

```powershell
wertybuild pyd --edition base
```

Para crear un paquete de distribución:

```powershell
wertybuild zip --edition base
```

La configuración de compilación está en:

- `c/product.json`: identidad, versión y metadatos del producto.
- `pydobj.toml`: script principal y configuración de preparación.
- `psage.spec`: configuración de PyInstaller.
- `cli.py`: punto de entrada único de la aplicación.

No se debe editar manualmente la versión generada en `c/version.py` o `c/version.txt`; wertybuild la genera a partir de `c/product.json`.

## Desarrollo y comprobaciones

Para ejecutar la aplicación desde el código fuente:

```bash
uv sync
uv run psage
```

Para ejecutar las pruebas:

```bash
uv run pytest -q
```

La suite actual contiene pruebas de cálculo, exportación JSON, rutas de datos y plantillas.

## Estructura principal

```text
psage/
├── presupuestador.py        # Presentación Gradio
├── cli.py                   # Punto de entrada único: psage
├── models.py                # Modelos y reglas de cálculo
├── tariff_parser.py         # Lectura y transformación de tarifas
├── simplificar_tarifas.py   # Conversión del Excel original
├── pdf_generator.py         # Exportación PDF
├── excel_generator.py       # Exportación Excel
├── json_generator.py        # Exportación JSON versionada
├── templates.py             # Plantillas de presupuestos
├── psage.spec               # Configuración PyInstaller
├── pydobj.toml              # Configuración wertybuild/pydobj
├── c/product.json           # Fuente de verdad del producto
├── examples/                # Datos ficticios de demostración
├── tests/                   # Pruebas automatizadas
└── LICENSE                  # Licencia MIT
```

## Transparencia y revisión del código

El código fuente está publicado para permitir una revisión independiente de:

- las reglas de cálculo;
- los formatos de exportación;
- el tratamiento local de los archivos;
- la configuración de compilación;
- las pruebas automatizadas.

Para colaborar, informar un problema o solicitar una revisión, visitá:

**[alfonsoautomatiza.com/colaboramos](https://alfonsoautomatiza.com/colaboramos)**

Antes de aceptar una versión compilada, un socio puede revisar `cli.py`, `presupuestador.py`, los generadores de exportación, `c/product.json`, `pydobj.toml` y `psage.spec`, y comparar la versión declarada con el ejecutable entregado.

## Licencia y autoría

El código se distribuye bajo licencia MIT; consultá [`LICENSE`](LICENSE).

**ALCA TIC S.L.** — Cádiz, España
