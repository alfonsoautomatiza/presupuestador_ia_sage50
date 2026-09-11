# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static HTML/CSS in `docs/`, served by GitHub Pages from the same repository (user decision: single repo, public code). No build tooling.

## Users

Partners, distribuidores y asesorías del ecosistema Sage que necesitan preparar presupuestos a partir de la tarifa oficial de Sage 50. Uso por Alfonso Automatiza (alfonsoautomatiza.com, Cádiz) y por cualquier socio que quiera auditar o reutilizar el código.

## Product Purpose

psage es una aplicación de escritorio que lee una tarifa Excel oficial de Sage 50, la transforma en catálogo filtrable, calcula precios y descuentos en cascada, arma presupuestos (con agrupación, plantillas y papelera por línea) y exporta PDF, Excel y JSON versionado — todo 100% local. La página web explica qué hace el código, lo posiciona ante la comunidad de partners de Sage y comunica su licencia libre con atribución.

## Positioning

Código fuente público y auditable que procesa la tarifa 100% en local — ninguna tarifa ni presupuesto sale de la máquina del socio. Un vecino no puede copiar esa combinación de transparencia + privacidad.

## Operating Context

- Cada socio aporta su propia tarifa Excel oficial (.xlsx/.xlsm/.xls); el proyecto nunca distribuye tarifas.
- Windows y Linux; entrada única `psage` (navegador o ventana nativa vía `psage --window`).
- Datos del usuario en directorio por-usuario (`tarifas-sage50`), nunca en el repositorio.
- Distribución: `pip install .`, pipx, o `uv`; `.exe` compilable con wertybuild (fuera del alcance del repo).

## Capabilities and Constraints

- Catálogo con filtros (plan, periodicidad, módulo, sabor, plataforma, texto) y botón 📌 Todo.
- Presupuesto con papelera por línea, agrupación (plan/periodicidad), plantillas, totales con IVA.
- Exportación PDF, Excel y JSON schema `tarifas-sage50/oferta/v1`.
- Prohibido commitear cualquier dato comercial, real o ficticio (norma del PRD).
- "Sage 50" es marca de Sage Group plc; proyecto independiente, sin afiliación.

## Brand Commitments

- Marca: **Alfonso Automatiza** — posicionamiento proactivo en la comunidad de partners de Sage.
- Contacto: alfonsoautomatiza.com/colaboramos · github.com/alfonsoautomatiza · LinkedIn (URL pendiente).
- Sin logo: identidad tipográfica (fuente de la app: Inter, "Segoe UI", sans-serif).
- Licencia MIT (© alfonsoautomatiza.com): uso libre con obligación de mantener el aviso de copyright — la página debe comunicarlo explícitamente.
- Idioma del sitio: español.

## Evidence on Hand

- PRD.md y README.md del repositorio (requisitos y flujo).
- App ejecutable localmente; capturas reales PENDIENTES: se generarán con tarifa 100% ficticia vía Chrome headless. Lista definitiva de vistas a confirmar por el usuario.
- No hay testimonios, métricas ni clientes publicables; no fabricar.

## Product Principles

1. Transparencia radical: todo lo que la página afirma se puede verificar en el código.
2. Privacidad local primero: los datos nunca salen de la máquina.
3. Profesional partner-ready: el público decide si confiar; cero tono amateur.
4. Libre con atribución: MIT explicado en lenguaje claro.
