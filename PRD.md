# PRD — Presupuestador Sage 50

## Norma rígida de publicación pública

**MUST:** el repositorio público contiene únicamente código fuente, tests y documentación. Nunca se deben commitear ni distribuir datos JSON de tarifas, clientes o negocios, ni archivos `.xlsx`, `.xlsm` o `.xls`, sean reales o ficticios. También están prohibidos backups, exportaciones, salidas generadas, ejemplos, fixtures con datos, credenciales y cualquier información comercial. Los tests deben usar datos en memoria o fixtures temporales fuera de rutas trackeadas. **Cualquier violación bloquea la publicación.**

La lista oficial de precios de Sage debe obtenerse por cada usuario o socio mediante un acceso legítimo y proporcionarse localmente; este proyecto no la distribuye.

| | |
| --- | --- |
| **Producto** | Presupuestador Sage 50 (`psage`) |
| **Versión documentada** | 0.3.0 |
| **Estado** | Implementado (documento formaliza el producto existente) |
| **Autor** | alfonsoautomatiza.com — Cádiz, España |
| **Licencia** | MIT |

> **Aviso de marca:** proyecto independiente de alfonsoautomatiza.com, sin afiliación ni respaldo de Sage. “Sage 50” es marca de Sage Group plc.

---

## 1. Visión

Que cualquier miembro del equipo genere en segundos un presupuesto presentable a partir de una lista de precios de Sage 50 obtenida legítimamente, sin buscar precios a mano ni calcular descuentos en una hoja de cálculo.

## 2. Problema

Armar un presupuesto desde una lista de precios con múltiples productos, planes y periodicidades es trabajo manual repetitivo y propenso a error:

1. Localizar el producto correcto entre decenas de filas y columnas del Excel original.
2. Aplicar el plan y la periodicidad correctos.
3. Calcular descuentos en cascada (partner, tech BP, PAM).
4. Dar formato a un presupuesto presentable para el cliente.

Cada presupuesto cuesta minutos de copiado/pegado y cada error de precio es un problema comercial.

## 3. Objetivos y métricas de éxito

| Objetivo | Métrica |
| --- | --- |
| Reducir el tiempo de generación de un presupuesto a segundos | Un presupuesto de ~10 líneas se arma y exporta en < 2 minutos |
| Eliminar errores de precio y descuento | La lógica de precios está centralizada y cubierta por tests unitarios |
| Cero fricción de puesta en marcha | Instalable desde el código fuente con `uv tool`/`pipx` |
| Cero mantenimiento del formato de tarifa | El Excel original de Sage se transforma localmente cuando corresponde |

## 4. Usuarios objetivo

- **Comercial / administrativo de Alfonso Automatiza** (usuario principal): genera presupuestos con una tarifa obtenida legítimamente.
- **Responsable de tarifas** (secundario): actualiza localmente la tarifa y usa la app o el CLI de transformación.

## 5. Alcance

### Dentro del alcance

- Transformación local del Excel original de Sage a un formato simplificado.
- Aplicación web local (Gradio) para armar presupuestos: filtros, líneas y totales.
- Resolución de precios por plan + periodicidad con fallbacks y descuentos en cascada.
- Exportación local a PDF y Excel.
- Distribución pública únicamente como instalación desde el código fuente mediante `uv tool`/`pipx`.

### Fuera del alcance

- Integración con Sage 50 o cualquier API externa.
- Distribución o inclusión de tarifas, clientes, negocios, ejemplos o fixtures con datos.
- Gestión de clientes, histórico de presupuestos o CRM.
- Multiusuario / servidor compartido: es una herramienta de escritorio local.
- Ejecutables standalone, PyInstaller, wertybuild o cualquier sistema privado de compilación.

## 6. Requisitos funcionales

Prioridad MoSCoW. Todos los RF listados están implementados en v0.3.0 salvo que se indique lo contrario.

### RF-1 — Carga y transformación de tarifas

| ID | Requisito | Prioridad |
| ---- | ----------- | --------- |
| RF-1.1 | Acepta localmente el Excel original de Sage y lo transforma a un formato simplificado para uso local. | Must |
| RF-1.2 | Al procesar una tarifa nueva, puede guardar backup local y detectar cambios; estos archivos nunca se versionan. | Must |
| RF-1.3 | La app permite seleccionar o subir localmente una tarifa legítimamente obtenida y recordar la última utilizada sin publicarla. | Must |
| RF-1.4 | CLI de transformación: `simplificar_tarifas.py [archivo]` con modo vigilancia `--vigilar` y forzado `--forzar`. | Should |
| RF-1.5 | No incluye tarifas de ejemplo ni datos ficticios en el repositorio público; las pruebas usan datos en memoria o temporales. | Must |

### RF-2 — Armado del presupuesto (UI Gradio)

| ID | Requisito | Prioridad |
| ---- | ----------- | --------- |
| RF-2.1 | Datos del cliente en el sidebar: empresa, CIF, contacto, email, condiciones de pago y % de IVA. | Must |
| RF-2.2 | Filtros por Módulo, Sabor, Plataforma, Plan, Periodicidad y búsqueda por texto libre. | Must |
| RF-2.3 | Añadir líneas: producto + plan + periodicidad + cantidad. | Must |
| RF-2.4 | Resumen del presupuesto: líneas, subtotal, IVA y total, editables. | Must |
| RF-2.5 | Permite guardar, cargar y eliminar plantillas locales sin publicarlas. | Must |
| RF-2.6 | Permite agrupar el presupuesto por plan o periodicidad y muestra subtotales. | Must |

### RF-3 — Lógica de precios y descuentos (sin dependencias de UI)

| ID | Requisito | Prioridad |
| ---- | -------- | --------- |
| RF-3.1 | Resolución de precio unitario por plan + periodicidad, con los fallbacks definidos por el modelo. | Must |
| RF-3.2 | Descuentos en cascada: `Neto = Precio × (1 − dto_partner) × (1 − dto_tech_bp) × (1 − dto_pam)`, redondeado a 2 decimales. | Must |
| RF-3.3 | Filtro de periodicidad según la periodicidad declarada por el producto. | Must |
| RF-3.4 | Precio de referencia: mínimo del período; 0 si no hay candidatos. | Should |
| RF-3.5 | La lógica vive en módulos puros testeables sin depender de Gradio. | Must |

### RF-4 — Exportación

| ID | Requisito | Prioridad |
| ---- | -------- | --------- |
| RF-4.1 | PDF profesional con datos del cliente, líneas, subtotal y total; se guarda localmente. | Must |
| RF-4.2 | Excel editable con los mismos datos y estilos; se guarda localmente y nunca se versiona. | Must |
| RF-4.3 | JSON versionado para exportación local; puede contener datos de cliente y debe tratarse como información sensible. | Must |

### RF-5 — Ejecución y distribución

| ID | Requisito | Prioridad |
| ---- | -------- | --------- |
| RF-5.1 | CLI `psage`: detecta puerto y admite `--port` y `--no-browser`. | Must |
| RF-5.2 | Comando `psage`, instalado con `uv tool` o `pipx`, abre la aplicación Gradio local. | Must |
| RF-5.3 | Instalación como tool: `uv tool install` o `pipx install .` (Python ≥ 3.11). | Should |

## 7. Requisitos no funcionales

| ID | Requisito |
| --- | --- |
| RNF-1 | **Usabilidad:** flujo lineal tarifa → cliente → filtros → líneas → exportar. |
| RNF-2 | **Rendimiento:** la tarifa se carga una vez a un formato local; filtrar y añadir líneas es interactivo. |
| RNF-3 | **Portabilidad:** funciona en Windows, Linux y macOS vía instalación como tool. |
| RNF-4 | **Mantenibilidad:** lógica pura y testeada separada de la UI. |
| RNF-5 | **Seguridad de datos:** tarifas, presupuestos y backups viven localmente en rutas no versionadas; todo es local salvo `localhost`. |
| RNF-6 | **Legal:** cada usuario debe tener acceso legítimo a la tarifa; el repositorio no distribuye datos de Sage ni de terceros. |

## 8. Restricciones y dependencias

- **Formato de entrada:** el parser asume el layout actual del Excel de Sage; cambios requieren actualizar `simplificar_tarifas.py`.
- **Stack:** Python ≥ 3.11, Gradio, pandas, openpyxl y reportlab.
- **Instalación:** `uv tool`/`pipx` desde el código fuente.

## 9. Riesgos

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| Sage cambia el layout del Excel de tarifas | Alto | Transformación aislada y tests. |
| Error de precio ante el cliente | Alto | Lógica centralizada y tests unitarios. |
| Puerto 8599 ocupado | Bajo | Búsqueda automática de puerto libre. |
| Publicación accidental de datos | Crítico | Norma rígida de publicación y reglas de `.gitignore`; cualquier violación bloquea la publicación. |

## 10. Backlog propuesto (no comprometido)

- Numeración y registro local de presupuestos.
- Plantillas de descuento por cliente.
- Actualización del parser por configuración.
- CI con pytest.
- Vista previa del PDF dentro de la app.

## 11. Glosario

| Término | Definición |
| --- | --- |
| **Tarifa** | Excel oficial de precios de Sage 50 obtenido legítimamente y usado localmente. |
| **Plan** | Nivel de servicio. |
| **Periodicidad** | Mensual, Anual, Bianual, Trienal o Puntual. |
| **SSRS** | Servicio puntual (sin recurrencia). |
| **Tarifa simplificada** | Formato local resultante de transformar el Excel original. |

---

*Documento formalizado a partir del producto existente. Detalles técnicos y uso en [`README.md`](README.md).*
