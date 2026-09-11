# psage — Instrucciones técnicas públicas

Este documento describe el funcionamiento del código fuente público. El repositorio no contiene tarifas, clientes, precios comerciales ni archivos de prueba comerciales.

## Norma de publicación

Solo se versionan código, tests y documentación. Está prohibido añadir:

- `.xlsx`, `.xlsm` o `.xls`;
- JSON de tarifas, clientes, precios o presupuestos;
- PDF, Excel, backups o salidas generadas;
- credenciales, tokens o información comercial.

Los tests deben usar datos en memoria o archivos temporales. Cada usuario debe obtener legítimamente su propia tarifa oficial de Sage y cargarla localmente.

## Instalación pública

Requisitos: Python 3.11 o superior y `pipx`.

```bash
cd /ruta/al/repositorio/pytarifas_sage50
pipx install --force .
psage
```

Opciones:

```bash
psage                  # Gradio en el navegador
psage --port 9000      # puerto concreto
psage --no-browser     # no abre el navegador
psage --window         # intenta abrir una ventana nativa
```

Para desarrollo:

```bash
uv sync
uv run pytest -q
uv run psage
```

## Flujo de la aplicación

1. **Tarifa y cliente:** cargar localmente un Excel autorizado y completar los datos del cliente.
2. **Catálogo:** filtrar por módulo, sabor, plataforma, plan, periodicidad o texto.
3. **Presupuesto:** seleccionar producto, plan, periodicidad y cantidad; también se pueden añadir todas las líneas filtradas.
4. **Revisión:** comprobar líneas, papelera, agrupación, subtotal, IVA y total.
5. **Exportación:** generar PDF, Excel o JSON localmente.

Las exportaciones pueden contener datos personales y comerciales. Revisalas antes de compartirlas.

## Estructura técnica

```text
cli.py                   # Entrada única psage

gradio_app.py            # Interfaz Gradio y callbacks
presupuestador.py        # Compatibilidad y lógica de aplicación
models.py                # Precios, descuentos y agrupaciones
tariff_parser.py         # Lectura y transformación local de tarifas
simplificar_tarifas.py   # Conversión del Excel autorizado
pdf_generator.py         # Exportación PDF
excel_generator.py       # Exportación Excel
json_generator.py        # Exportación JSON versionada
templates.py             # Plantillas locales
tests/                   # Tests sin datos comerciales
```

## Lógica de precios

La resolución busca primero la combinación exacta de plan y periodicidad, después los fallbacks definidos por el modelo y finalmente las tarifas de servicios puntuales. Los descuentos se aplican en cascada:

```text
Neto = Precio × (1 - dto_partner) × (1 - dto_tech_bp) × (1 - dto_pam)
```

La lógica está separada de Gradio y se prueba sin levantar un servidor.

## Datos locales

Las tarifas originales, la tarifa simplificada, plantillas, backups y presupuestos viven en carpetas locales ignoradas por Git. La ubicación puede configurarse con `TARIFAS_DATA_DIR`.

Nunca subas esas carpetas al repositorio público.

## Colaboración

Para revisar el código o proponer cambios:

[alfonsoautomatiza.com/colaboramos](https://alfonsoautomatiza.com/colaboramos)
