# PRD — Presupuestador Sage 50

| | |
| --- | --- |
| **Producto** | Presupuestador Sage 50 (`tarifas-sage50`) |
| **Versión documentada** | 0.3.0 |
| **Estado** | Implementado (documento formaliza el producto existente) |
| **Autor** | ALCA TIC S.L. — Cádiz, España |
| **Licencia** | MIT |

> **Aviso de marca:** proyecto independiente de ALCA TIC S.L., sin afiliación ni respaldo de Sage. "Sage 50" es marca de Sage Group plc. El repositorio no distribuye tarifas reales; cada usuario aporta la suya por medios legítimos.

---

## 1. Visión

Que cualquier miembro del equipo genere en segundos un presupuesto presentable (PDF o Excel) a partir de la tarifa de precios de Sage 50, sin buscar precios a mano ni calcular descuentos en una hoja de cálculo.

## 2. Problema

Armar un presupuesto desde una lista de precios con múltiples productos, planes y periodicidades es trabajo manual repetitivo y propenso a error:

1. Localizar el producto correcto entre decenas de filas y 42 columnas del Excel original.
2. Aplicar el plan y la periodicidad correctos (el precio vive en una celda cruzada).
3. Calcular descuentos en cascada (partner, tech BP, PAM).
4. Dar formato a un PDF o Excel presentable para el cliente.

Cada presupuesto cuesta minutos de copiado/pegado y cada error de precio es un problema comercial.

## 3. Objetivos y métricas de éxito

| Objetivo | Métrica |
| --- | --- |
| Reducir el tiempo de generación de un presupuesto a segundos | Un presupuesto de ~10 líneas se arma y exporta en < 2 minutos |
| Eliminar errores de precio y descuento | La lógica de precios está centralizada y cubierta por tests unitarios |
| Cero fricción de puesta en marcha | Instalable con `uv tool`/`pipx` o ejecutable `.exe` sin Python |
| Cero mantenimiento del formato de tarifa | El Excel original de Sage se transforma una vez, con backup y detección de cambios |

## 4. Usuarios objetivo

- **Comercial / administrativo de ALCA TIC** (usuario principal): genera presupuestos para clientes. No es técnico; usa la app con datos ya cargados o sube un Excel nuevo.
- **Responsable de tarifas** (secundario): actualiza la tarifa periódicamente; usa la app o el CLI de transformación.

## 5. Alcance

### Dentro del alcance

- Transformación del Excel original de Sage (42 columnas, 2 hojas) a un JSON simplificado (17 campos).
- Aplicación web local (Gradio) para armar presupuestos: filtros, líneas, totales.
- Resolución de precios por plan + periodicidad con fallbacks, y descuentos en cascada.
- Exportación a PDF (presentable) y Excel (editable).
- Distribución: paquete instalable (`uv tool`/`pipx`) y ejecutable standalone de Windows (PyInstaller), con ventana nativa opcional (pywebview).

### Fuera del alcance

- Integración con Sage 50 o cualquier API externa (la tarifa se importa manualmente).
- Gestión de clientes, histórico de presupuestos o CRM.
- Multiusuario / servidor compartido: es una herramienta de escritorio local.
- Distribución de tarifas reales (datos comerciales del usuario, no versionados).

## 6. Requisitos funcionales

Prioridad MoSCoW. Todos los RF listados están implementados en v0.3.0 salvo que se indique lo contrario.

### RF-1 — Carga y transformación de tarifas

| ID | Requisito | Prioridad |
| ---- | ----------- | ----------- |
| RF-1.1 | Acepta el Excel original de Sage (2 hojas, 42 columnas) y lo reduce a 17 campos útiles en `data/tarifas.json` + un Excel limpio de consulta. | Must |
| RF-1.2 | Al procesar una tarifa nueva, guarda backup automático del original y detecta cambios por hash MD5 (no reprocesa sin necesidad). | Must |
| RF-1.3 | En la app: desplegable con los Excel de `originales/` o raíz, y uploader para subir uno nuevo; la última tarifa usada se recuerda entre sesiones (`.ultima_tarifa.json`). | Must |
| RF-1.4 | CLI de transformación: `simplificar_tarifas.py [archivo]` con modo vigilancia `--vigilar` y forzado `--forzar`. | Should |
| RF-1.5 | Incluye tarifa de ejemplo ficticia (`examples/`) para probar sin datos reales. | Should |

### RF-2 — Armado del presupuesto (UI Gradio)

| ID | Requisito | Prioridad |
| ---- | ----------- | ----------- |
| RF-2.1 | Datos del cliente en el sidebar: empresa, CIF, contacto, email, condiciones de pago y % de IVA. | Must |
| RF-2.2 | Filtros por Módulo, Sabor, Plataforma, Plan, Periodicidad y búsqueda por texto libre. | Must |
| RF-2.3 | Añadir líneas: producto + plan (Standard/Extra/Complete/Sin Nivel) + periodicidad (Mensual/Anual/Bianual/Trienal/Puntual) + cantidad. | Must |
| RF-2.4 | Resumen del presupuesto: líneas, subtotal, IVA y total, editables (quitar líneas). | Must |
| RF-2.5 | Permite guardar, cargar y eliminar plantillas con nombre que contienen líneas y observaciones, nunca IVA ni datos del cliente. | Must |
| RF-2.6 | Permite agrupar el presupuesto por plan o periodicidad y muestra subtotales por grupo en la UI y exportaciones. | Must |

### RF-3 — Lógica de precios y descuentos (sin dependencias de UI)

| ID | Requisito | Prioridad |
| ---- | ----------- | ----------- |
| RF-3.1 | Resolución de precio unitario en orden de prioridad: (1) plan + periodicidad exactos, (2) Sin Nivel de Servicio + periodicidad, (3) SSRS para servicios puntuales; 0 si no hay coincidencia. | Must |
| RF-3.2 | Descuentos en cascada: `Neto = Precio × (1 − dto_partner) × (1 − dto_tech_bp) × (1 − dto_pam)`, redondeado a 2 decimales. | Must |
| RF-3.3 | Filtro de periodicidad: un producto pasa si declara la periodicidad filtrada; "Puntual" pasa siempre cualquier filtro. | Must |
| RF-3.4 | Precio de referencia: mínimo del período; para puntuales usa SSRS; 0 si no hay candidatos. | Should |
| RF-3.5 | Toda esta lógica vive en módulos puros (`models.py`, `tariff_parser.py`) testeables sin depender de Gradio. | Must |

### RF-4 — Exportación

| ID | Requisito | Prioridad |
| ---- | ----------- | ----------- |
| RF-4.1 | PDF profesional (reportlab) con datos del cliente, líneas, código Sage, subtotal y una fila única `TOTAL + IVA`; se guarda en `presupuestos/` y se puede descargar. | Must |
| RF-4.2 | Excel editable (openpyxl) con los mismos datos, estilos, código Sage y fila única `TOTAL + IVA`. | Must |
| RF-4.3 | JSON estricto y versionado (`tarifas-sage50/oferta/v1`) con datos completos de tarifa, cliente, líneas, agrupaciones y totales, disponible para descarga y cálculos de IA. | Must |

### RF-5 — Ejecución y distribución

| ID | Requisito | Prioridad |
| ---- | ----------- | ----------- |
| RF-5.1 | CLI `psage`: detecta puerto (8599 por defecto; si está ocupado, primer libre en 8600–9000), opciones `--port` y `--no-browser`. | Must |
| RF-5.2 | Comando único `psage`: instalado con uv/pipx abre el navegador por defecto vía subprocess; `--window` usa una ventana nativa con pywebview; el ejecutable congelado usa `psage` como entrada y conserva el bootstrap programático con datos en `sys._MEIPASS`. | Must |
| RF-5.3 | `.exe` standalone de Windows (~80–120 MB) generado con `wertybuild` y `psage.spec`; sin Python instalado en el equipo destino. Por defecto abre ventana nativa. | Must |
| RF-5.4 | Instalación como tool: `uv tool install` o `pipx install .` (Python ≥ 3.11). | Should |

## 7. Requisitos no funcionales

| ID | Requisito |
| ---- | ----------- |
| RNF-1 | **Usabilidad:** un usuario no técnico arma un presupuesto sin documentación; la UI es la de Gradio con flujos lineales (tarifa → cliente → filtros → líneas → exportar). |
| RNF-2 | **Rendimiento:** la tarifa se carga una vez a JSON; filtrar y añadir líneas es interactivo (< 1 s con tarifas de miles de filas). |
| RNF-3 | **Portabilidad:** funciona en Windows (`.exe`, ventana nativa), Linux/macOS vía tool install; detección de rutas Windows/WSL normalizada. |
| RNF-4 | **Mantenibilidad:** lógica de negocio pura y testeada (pytest) separada de la UI; transformación de tarifas desacoplada de la app. |
| RNF-5 | **Seguridad de datos:** las tarifas reales, presupuestos y backups viven en carpetas no versionadas (`data/`, `originales/`, `backups/`, `presupuestos/`); en modo instalado se guardan en una carpeta local por usuario y sobreviven reinstalaciones; todo es local, sin red más allá de `localhost`. El JSON de IA incluye CIF y email: debe revisarse la política de privacidad antes de compartirlo externamente. |
| RNF-6 | **Legal:** no distribuye datos comerciales de Sage ni presupuestos de terceros; datos de ejemplo ficticios. |

## 8. Restricciones y dependencias

- **Formato de entrada:** el parser asume el layout actual del Excel de Sage (42 columnas). Un cambio de formato de Sage requiere actualizar `simplificar_tarifas.py`.
- **Stack:** Python ≥ 3.11, Gradio, pandas, openpyxl, reportlab, pywebview.
- **Empaquetado:** el `.exe` solo se genera en Windows (PyInstaller); primera ejecución lenta por descompresión.
- **Instaladores:** `uv tool`/`pipx` fallan con rutas que contienen `#` (documentado, workaround con symlink).

## 9. Riesgos

| Riesgo | Impacto | Mitigación |
| -------- | --------- | ------------ |
| Sage cambia el layout del Excel de tarifas | Alto — el parser deja de producir JSON válido | Backup automático del original; transformación aislada en un solo script con detección de cambios |
| Error de precio ante el cliente | Alto — impacto comercial | Lógica centralizada + tests unitarios de precios, descuentos y filtros |
| Puerto 8599 ocupado en máquinas compartidas | Bajo — la app no arranca | Búsqueda automática de puerto libre (8600–9000) |
| Tamaño del `.exe` (80–120 MB) | Bajo — percepción de lentitud | Documentado; primera ejecución más lenta es esperada |

## 10. Backlog propuesto (no comprometido)

Ideas candidatas para futuras versiones; ninguna está en el alcance actual:

- Numeración y registro de presupuestos (histórico local con búsqueda).
- Plantillas de descuento por cliente (evitar re-teclear dto_partner/dto_tech_bp/dto_pam).
- Actualización del parser por configuración (mapeo de columnas en YAML) para absorber cambios de formato de Sage sin tocar código.
- CI con pytest + build del `.exe` (hoy el build es manual en Windows).
- Vista previa del PDF dentro de la app antes de descargar.

## 11. Glosario

| Término | Definición |
| --------- | ----------- |
| **Tarifa** | Excel de precios oficial de Sage 50 (productos × planes × periodicidades) |
| **Plan** | Nivel de servicio: Standard, Extra, Complete, Sin Nivel |
| **Periodicidad** | Mensual, Anual, Bianual, Trienal o Puntual (servicio único, SSRS) |
| **SSRS** | Servicio puntual (sin recurrencia) |
| **dto_partner / dto_tech_bp / dto_pam** | Descuentos aplicados en cascada sobre el precio de tarifa |
| **Tarifa simplificada** | JSON de 17 campos resultante de transformar el Excel original de 42 columnas |

---

*Documento generado a partir del estado real del repositorio (v0.3.0, commit `8e2acad`). Detalles técnicos de implementación en [`INSTRUCCIONES.md`](INSTRUCCIONES.md); uso diario en [`README.md`](README.md).*
