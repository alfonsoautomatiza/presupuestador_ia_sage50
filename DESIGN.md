---
name: psage — Presupuestador Sage 50
description: Certificado de instrumento libre — folio documental español para la web pública de psage
colors:
  papel: "#F8F6EE"
  papel-hondo: "#F1EDE0"
  tinta: "#0F4C3A"
  tinta-suave: "#2A5C4B"
  oro: "#B08C3D"
  grafito: "#22211E"
  grafito-suave: "#55534C"
  mat-blanco: "#FFFFFF"
typography:
  display:
    fontFamily: "Archivo, Inter, sans-serif"
    fontSize: "clamp(3rem, 9vw, 6rem)"
    fontWeight: 900
    lineHeight: 0.96
    letterSpacing: "-0.028em"
  headline:
    fontFamily: "Archivo, sans-serif"
    fontSize: "clamp(1.5rem, 3.4vw, 2.2rem)"
    fontWeight: 800
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Archivo, sans-serif"
    fontSize: "clamp(1.05rem, 2.2vw, 1.45rem)"
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: "Inter, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Fragment Mono, monospace"
    fontSize: "0.72rem"
    letterSpacing: "0.14em"
    fontWeight: 400
rounded:
  sm: "3px"
  xs: "2px"
spacing:
  sm: "10px"
  md: "22px"
  lg: "44px"
  seccion: "clamp(36px, 6vw, 64px)"
components:
  button-primary:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.papel}"
    rounded: "{rounded.sm}"
    padding: "16px 34px"
---

# Design System: psage — Certificado de Instrumento Libre

## Overview

**Creative North Star: "El Certificado Notarial"**

La web de psage es un folio acreditado: la página entera se comporta como un documento notarial español que certifica al instrumento (software) como libre, local y auditable. La licencia MIT es protagonista visual, no letra chica. Densidad contenida, aire de papel, una sola tinta de grabado y oro de foil. La personalidad es institucional sin frialdad: hay exactamente una zona cálida (la firma humana de Alfonso).

**Características clave:**

- Un solo folio central con borde de guilloche SVG arriba y abajo.
- Sellos circulares con texto en arco que se "estampan" al entrar en vista.
- Numeración seriada y revisión fechada en monoespaciada.
- Las capturas del producto entran como anexos rotulados (ANEXO A/B/C) con mat blanco.

## Colors

Una tinta de grabado verde sobre papel cálido, con oro de foil como único acento. Estrategia: Restrained (neutros de papel + un acento portador).

### Primary

- **Tinta de Grabado** (#0F4C3A): toda la tinta del documento — texto acentuado, reglas, sellos, botón primario, iconos SVG. Es el verde institucional del folio.
- **Tinta Suave** (#2A5C4B): variante de la tinta para series y rotulados de menor jerarquía.

### Secondary

- **Oro de Foil** (#B08C3D): anillos exteriores de sellos, numerales romanos grandes, diamante divisor y reglas de la caja de licencia. Nunca para texto de cuerpo (contraste insuficiente en papel).

### Neutral

- **Papel** (#F8F6EE): fondo del folio.
- **Papel Hondo** (#F1EDE0): campo de página alrededor del folio y fondos de caja (firma, `code`).
- **Grafito** (#22211E): texto principal y titular de obra.
- **Grafito Suave** (#55534C): texto secundario.
- **Blanco Mate** (#FFFFFF): alfombrilla de los marcos de anexos.

### Named Rules

**La Regla de la Única Tinta.** Todo lo que "está impreso" usa la tinta verde; el oro es foil decorativo en piezas grandes y nunca texto de lectura.
**La Regla del Folio.** La página es un documento: las divisiones son reglas horizontales con un diamante de oro al centro, no separadores decorativos.

## Typography

**Display Font:** Archivo (variable, expandida al 112–118%, fundición española Omnibus-Type) con fallback Inter.
**Body Font:** Inter ("Segoe UI" fallback — compromiso de marca con la propia app).
**Label/Mono Font:** Fragment Mono (series, revisión, rotulados de anexo y de unidades).

**Character:** Archivo expandida pesada da el carácter de sello institucional; Inter mantiene el cuerpo neutro y legible; Fragment Mono aporta el registro de lote (serie, fecha, numeración).

### Hierarchy

- **Display** (900, clamp(3rem–6rem), 0.96): solo el nombre de obra "PSAGE.".
- **Headline** (800, clamp(1.5–2.2rem), -0.02em): títulos de sección.
- **Title** (600, clamp(1.05–1.45rem), 1.3): bajada del hero.
- **Body** (400, 1rem, 1.6, máx 66–70ch): párrafos y leads.
- **Label** (400, 0.68–0.8rem, 0.1–0.14em, mayúsculas): series, rotulados ANEXO, unidades, tiras.

### Named Rules

**La Regla del Registro de Lote.** Todo dato de identidad del documento (serie, revisión, fecha de expedición, rotulados de anexo) va en Fragment Mono con tracking amplio; nada de eso va en proporcional.

## Layout

Folio central de máx 1120px sobre campo de página, con aire exterior (clamp 16–48px). El cuerpo usa padding fluido (clamp 28–72px vertical, 20–88px horizontal). Ritmo: más aire sobre cada título que debajo; divisiones a clamp(36–64px). Breakpoints: 860px (hero a una columna, etapas 2×2, unidades 3×2), 700px (firma apilada), 540px (etapas 1×4, unidades 2×3). Las anexas de ancho completo mantienen mat blanco y caption al pie.

## Elevation & Depth

Sombra ambiental y estructural a la vez: el folio flota sobre el campo con una sombra larga difusa; los marcos de anexo flotan menos. Sin sombras duras (la sombra dura del botón primario fue corregida durante la revisión de acabado y no es parte del sistema).

### Shadow Vocabulary

- **Folio** (`box-shadow: 0 2px 6px rgba(34,33,30,.10), 0 18px 44px rgba(34,33,30,.14)`): el documento sobre la mesa.
- **Marco de anexo** (`0 2px 6px rgba(34,33,30,.08), 0 10px 26px rgba(34,33,30,.10)`): láminas montadas sobre el folio.
- **Botón primario** (`0 2px 6px rgba(34,33,30,.16)` → hover `0 4px 12px rgba(15,76,58,.30)`): elevación de estado, con transición de 0.18s ease-out.

## Shapes

Lenguaje de documento impreso: esquinas casi rectas (radio 2–3px), keylines finas verdes al 28% y 16% como marco interior del folio (inset 10px) y bordes de cajas. Cero píldoras salvo controles pequeños. Los sellos son la única geometría circular (es lo que los hace sellos).

## Components

### Botón primario "estampado" (`btn-sello`)

- **Shape:** radio 3px, relleno pleno de tinta.
- **Primary:** fondo tinta, texto papel, Archivo 700, padding 16/34.
- **Hover / Focus:** sube 1px con sombra verde difusa; focus-ring verde 2px con offset 3px.
- **Nota:** siempre junto a una nota corta en grafito suave que aclara la condición de la oferta.

### Sellos (`sello`)

- SVG circular: anillo de oro exterior (2.5px), anillo de tinta interior, texto en arco (`textPath`), centro con sigla o icono de escudo trazado a mano.
- Entrada: única animación autoriada del sistema — estampado (escala 1.55→1, blur 5→0, opacidad 0→1, cubic-bezier(.16,1,.3,1), segundo sello con 0.28s de retardo). Desactivada con `prefers-reduced-motion`.

### Tirás de verificación (`tira`)

- Fragment Mono 0.8rem, borde keyline, icono de check SVG trazado, padding 10/16. Filas flexibles con gap 14px.

### Unidades rotuladas (`unidad`)

- Celda de catálogo de piezas: icono SVG de trazo 1.6px + rótulo mono en mayúsculas. Grid 6→3→2 columnas con keylines internas.

### Anexos (`anexo-marco`)

- Mat blanco 10px, borde keyline, sombra de lámina; caption al pie en mono (rótulo verde a la izquierda, dato a la derecha). El anexo alto usa visor con scroll interno (max-height 560px).

### Caja de licencia (`licencia-caja`)

- Doble marco: borde de oro-linea exterior + keyline interior a 6px. Única caja con tratamiento de foil.

### Firma (`firma`)

- Monograma circular "AA" con anillo de oro; fondo papel-hondo. La única zona cálida y personal del folio.

## Do's and Don'ts

### Do

- **Do** usar la tinta verde para toda línea, regla, icono y texto enfatizado del folio.
- **Do** numerar y fechar todo dato de identidad del documento en Fragment Mono.
- **Do** presentar capturas del producto como anexos rotulados con mat blanco, declarando siempre que los datos son ficticios.
- **Do** mantener el contraste del cuerpo ≥4.5:1 (grafito sobre papel) y reservar el oro para piezas grandes.

### Don't

- **Don't** usar el oro como color de texto de lectura.
- **Don't** introducir kickers/eyebrows sobre títulos: el documento no lleva antetítulos.
- **Don't** imitar física con CSS (biselados, relieve, papel arrugado): el grabado es vector plano y nítido.
- **Don't** añadir una segunda animación: el estampado de sellos es el único momento de movimiento del folio.
- **Don't** subir datos comerciales reales a los anexos: solo series DEMO.
