# psage — Presupuestador Sage 50

**psage** es una aplicación de código fuente público para preparar presupuestos localmente a partir de una lista de precios de Sage 50. Usa Gradio, calcula precios y descuentos, permite revisar líneas y exporta PDF, Excel o JSON.

El proyecto se publica para facilitar la transparencia y la colaboración en [alfonsoautomatiza.com/colaboramos](https://alfonsoautomatiza.com/colaboramos).

> **Independencia:** psage es un proyecto independiente de ALCA TIC S.L. No está afiliado, patrocinado ni respaldado oficialmente por Sage. “Sage 50” es una marca de Sage Group plc.

## Norma de datos

Este repositorio contiene **solo código fuente, tests y documentación**.

No se publica ni se debe commitear nunca:

- ninguna tarifa de Sage, real o ficticia;
- ningún archivo `.xlsx`, `.xlsm` o `.xls`;
- ningún JSON con tarifas, clientes, precios o presupuestos;
- exportaciones PDF/Excel/JSON, backups o datos generados;
- credenciales, tokens, información comercial o datos personales.

Esta regla es obligatoria para cualquier contribución. Los tests deben usar datos en memoria o ficheros temporales fuera de las rutas versionadas.

## Requisito indispensable: acceso legítimo a la tarifa

psage **no incluye ni distribuye una lista de precios de Sage**. Para usarlo, cada usuario o socio debe tener acceso legítimo a su propia tarifa oficial y cargarla localmente.

El usuario es responsable de:

- obtener la tarifa por medios autorizados;
- comprobar que puede utilizarla para preparar presupuestos;
- no subirla al repositorio;
- no compartirla con terceros sin autorización.

## Qué hace

- Lee una tarifa Excel local (`.xlsx`, `.xlsm` o `.xls`).
- Filtra por módulo, sabor, plataforma, plan, periodicidad y texto.
- Calcula precios y descuentos en cascada.
- Añade productos y combinaciones de plan/periodicidad al presupuesto.
- Guarda y recupera plantillas de líneas y observaciones.
- Agrupa líneas por plan o periodicidad.
- Exporta PDF, Excel y JSON versionado.
- Ejecuta todo localmente; no envía tarifas ni presupuestos a un servidor externo.

## Qué no hace

- No se conecta automáticamente con Sage 50.
- No contiene precios oficiales.
- No gestiona clientes ni históricos comerciales.
- No envía datos a servicios de IA.
- No sustituye la revisión comercial, fiscal o contractual.

## Instalación con pipx

La instalación pública está pensada para usuarios con Python y `pipx`:

```bash
cd /ruta/al/repositorio/pytarifas_sage50
pipx install --force .
psage
```

Opciones:

```bash
psage                  # abre Gradio en el navegador
psage --window         # intenta abrir una ventana nativa
psage --port 9000      # usa un puerto concreto
psage --no-browser     # no abre el navegador automáticamente
```

La aplicación queda disponible normalmente en:

```text
http://localhost:8599
```

Para una instalación de desarrollo con `uv`:

```bash
uv sync
uv run psage
```

## Flujo de uso

1. En **📂 Tarifa y cliente**, cargá el Excel oficial autorizado y seleccioná la hoja.
2. Completá los datos del cliente y el IVA.
3. En **🔍 Catálogo**, aplicá los filtros disponibles.
4. En **📝 Presupuesto**, elegí producto, plan, periodicidad y cantidad.
5. También podés añadir todas las líneas resultantes de los filtros del catálogo.
6. Revisá líneas, papelera, agrupación, subtotal, IVA y total.
7. En **📤 Exportar**, generá el PDF, Excel o JSON que necesites.

Los archivos generados se guardan localmente en la carpeta de datos del usuario. Revisá siempre el contenido antes de compartirlo: puede contener CIF, emails, precios y otra información sensible.

## Desarrollo y tests

```bash
uv sync
uv run pytest -q
```

Los tests deben utilizar fixtures en memoria o temporales. No se deben añadir tarifas, hojas de cálculo ni exportaciones al repositorio.

## Estructura principal

```text
psage/
├── cli.py                   # Punto de entrada psage
├── gradio_app.py            # Interfaz Gradio y callbacks
├── presupuestador.py       # Compatibilidad y lógica de aplicación
├── models.py                # Precios, descuentos y agrupaciones
├── tariff_parser.py         # Lectura y transformación local de tarifas
├── simplificar_tarifas.py   # Conversión del Excel autorizado
├── pdf_generator.py         # Exportación PDF
├── excel_generator.py       # Exportación Excel
├── json_generator.py        # Exportación JSON versionada
├── templates.py             # Plantillas locales
├── tests/                   # Tests sin datos comerciales
├── INSTRUCCIONES.md         # Detalles técnicos
├── PRD.md                   # Requisitos y norma de publicación
└── LICENSE                 # Licencia MIT
```

## Transparencia y colaboración

El código fuente permite revisar:

- reglas de cálculo;
- filtros y agrupaciones;
- formatos de exportación;
- tratamiento local de los archivos;
- pruebas automatizadas.

Para colaborar, informar un problema o solicitar una revisión:

**[alfonsoautomatiza.com/colaboramos](https://alfonsoautomatiza.com/colaboramos)**

## Licencia

MIT — ver [`LICENSE`](LICENSE).
