# psage — Presupuestador Sage 50

**psage** es una aplicación de código fuente público para preparar presupuestos localmente a partir de una lista de precios de Sage 50. Usa Gradio, calcula precios y descuentos, permite revisar líneas y exporta PDF, Excel o JSON.

El proyecto se publica para facilitar la transparencia y la colaboración en [alfonsoautomatiza.com/colaboramos](https://alfonsoautomatiza.com/colaboramos).

> **Independencia:** psage es un proyecto independiente de alfonsoautomatiza.com. No está afiliado, patrocinado ni respaldado oficialmente por Sage. “Sage 50” es una marca de Sage Group plc.

## Autor y contacto

**Alfonso Automatiza** — herramientas abiertas y automatización para la comunidad de partners de Sage.

- 🌐 Colaboración y contacto: [alfonsoautomatiza.com/colaboramos](https://alfonsoautomatiza.com/colaboramos)
- 🐙 GitHub: [github.com/alfonsoautomatiza](https://github.com/alfonsoautomatiza)
- 💼 LinkedIn: <!-- TODO(linkedin): pegar la URL exacta del perfil -->

¿Trabajás con Sage 50 y querés preparar presupuestos en minutos? Escribime: dudas, sugerencias y colaboraciones son bienvenidas.

## Norma de datos

Este repositorio contiene **solo código fuente, tests y documentación**.

No se publica ni se debe commitear nunca:

- ninguna tarifa de Sage, real o ficticia;
- ningún archivo `.xlsx`, `.xlsm` o `.xls`;
- ningún JSON con tarifas, clientes, precios o presupuestos;
- exportaciones PDF/Excel/JSON, backups o datos generados;
- credenciales, tokens, información comercial o datos personales.

Esta regla es obligatoria para cualquier contribución. Los tests deben usar datos en memoria o ficheros temporales fuera de las rutas versionadas.

Las tarifas originales, la tarifa simplificada, plantillas, backups y presupuestos viven en carpetas locales ignoradas por Git. La ubicación se puede configurar con la variable de entorno `TARIFAS_DATA_DIR`.

## Requisito indispensable: acceso legítimo a la tarifa

psage **no incluye ni distribuye una lista de precios de Sage**. Para usarlo, cada usuario o socio debe tener acceso legítimo a su propia tarifa oficial y cargarla localmente.

El usuario es responsable de:

- obtener la tarifa por medios autorizados;
- comprobar que puede utilizarla para preparar presupuestos;
- no subirla al repositorio;
- no compartirla con terceros sin autorización.

## Qué hace

- Lee una tarifa Excel local (`.xlsx`, `.xlsm` o `.xls`).
- Filtra por módulo, sabor, plataforma, plan, periodicidad y texto, con botón «📌 Todo» para marcar todos los valores de una vez.
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

## Instalación

### Opción 1 · Desde cero (sin herramientas previas)

No hace falta saber programar: solo Python y un comando.

1. **Instalá Python 3.11 o superior**
   - Windows: descargalo de [python.org/downloads](https://www.python.org/downloads/). En el instalador, marcá **"Add python.exe to PATH"** antes de pulsar *Install Now*.
   - macOS: descargalo de [python.org/downloads](https://www.python.org/downloads/) e instalá el paquete.
   - Linux: normalmente ya está incluido; si falta, `sudo apt install python3-pip` (Debian/Ubuntu).
   - Comprobalo en una terminal nueva: `python --version` (en Windows también vale `py --version`).
2. **Descargá el proyecto**: en GitHub, botón verde **Code → Download ZIP**, y descomprimilo.
3. **Instalá la aplicación**: abrí una terminal dentro de la carpeta descomprimida y ejecutá:

   ```bash
   python -m pip install .
   ```

   En Windows también vale `py -m pip install .`.

4. **Arrancá**:

   ```bash
   psage
   ```

   Si el comando no se reconoce, abrí una terminal nueva y probá de nuevo.

### Opción 2 · Con pipx (entorno aislado, si ya usás Python)

```bash
cd /ruta/al/repositorio/presupuestador_ia_sage50
pipx install --force .
psage
```

### Opción 3 · Desarrollo con uv

```bash
uv sync
uv run psage
```

Opciones de arranque:

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

## Flujo de uso

1. En **📂 Tarifa y cliente**, cargá el Excel oficial autorizado y seleccioná la hoja.
2. Completá los datos del cliente y el IVA.
3. En **🔍 Catálogo**, aplicá los filtros (o pulsá **📌 Todo** para marcar todos los valores).
4. En **📝 Presupuesto**, elegí producto, plan, periodicidad y cantidad.
5. También podés añadir todas las líneas resultantes de los filtros del catálogo.
6. Revisá líneas, papelera, agrupación, subtotal, IVA y total.
7. En **📤 Exportar**, generá el PDF, Excel o JSON que necesites.

Los archivos generados se guardan localmente en la carpeta de datos del usuario. Revisá siempre el contenido antes de compartirlo: puede contener CIF, emails, precios y otra información sensible.

## Lógica de precios

La resolución busca primero la combinación exacta de plan y periodicidad, después los fallbacks definidos por el modelo y finalmente las tarifas de servicios puntuales. Los descuentos se aplican en cascada:

```text
Neto = Precio × (1 - dto_partner) × (1 - dto_tech_bp) × (1 - dto_pam)
```

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
└── LICENSE                  # Licencia MIT
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
