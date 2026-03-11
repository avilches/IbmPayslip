# Instrucciones para Procesar Nóminas IBM
Cuando el usuario añada una nómina nueva, usa el comando `/add-payslip` (skill en `.claude/commands/add-payslip.md`). Este fichero contiene solo la referencia estructural (JSON, dashboard, glosario).

---

## Arquitectura de Ficheros

```
CLAUDE.md          ← Este fichero (instrucciones maestras)
.gitignore         ← Excluye data/ del repositorio
server.py          ← Servidor HTTP local para el dashboard
dashboard.html     ← Visualización gráfica (carga JSONs dinámicamente)
│
└── data/          ← CARPETA PRIVADA (no en git)
    ├── SOURCE OF TRUTH
    │   ├── 2024.json        ← Datos 2024 (año cerrado)
    │   ├── 2025.json        ← Datos 2025 (año cerrado)
    │   ├── 2026.json        ← Datos 2026 (año en curso)
    │   └── 2027.json        ← Crear cuando llegue enero 2027
    │
    ├── DERIVADOS LEGIBLES
    │   ├── 2024.md          ← Resumen legible del 2024.json
    │   ├── 2025.md          ← Resumen legible del 2025.json
    │   └── 2026.md          ← Resumen legible del 2026.json
    │
    └── ORIGINALES
        └── Payslip-*.pdf    ← PDFs de las nóminas originales
```

**Regla fundamental:** el JSON es la única fuente de verdad. El `.md` y el `dashboard.html` se derivan siempre del JSON. Si hay discrepancia, el JSON manda.

**Nota sobre git:** La carpeta `data/` está en `.gitignore` porque contiene información personal sensible (nóminas). Solo se versionan CLAUDE.md, server.py y dashboard.html.

---

## Ejecutar el dashboard

El dashboard necesita un servidor local para cargar los ficheros JSON. Desde la carpeta del proyecto:

```bash
uv run server.py
```

Abrir http://localhost:8000/dashboard.html en el navegador.

Para usar un puerto diferente:

```bash
uv run server.py 3000
```

> **Nota:** Abrir el fichero `dashboard.html` directamente (sin servidor) mostrará un error porque los navegadores bloquean las peticiones `fetch` a ficheros locales por seguridad (CORS).

---

## Estructura del JSON

Cada archivo contiene una lista `payslips[]` donde **cada entrada representa exactamente un PDF**. No se agregan quincenas en el JSON — la agregación mensual la hace el dashboard.

```json
{
  "year": 2026,
  "system": "SuccessFactors",
  "currency": "USD",
  "notes": "...",
  "payslips": [ ... ],
  "annualTotals": { ... },
  "taxBreakdown": { ... },
  "preTaxBreakdown": { ... },
  "postTaxBreakdown": { ... }
}
```

Cada archivo contiene una lista `payslips[]` donde **cada entrada representa exactamente un PDF**. No se agregan quincenas en el JSON — la agregación mensual la hace el dashboard.

```json
{
  "year": 2026,
  "system": "SuccessFactors",
  "currency": "USD",
  "notes": "...",
  "payslips": [ ... ],
  "annualTotals": { ... },
  "taxBreakdown": { ... },
  "preTaxBreakdown": { ... },
  "postTaxBreakdown": { ... }
}
```

### Estructura de cada entrada en `payslips[]`

```json
{
  "id": "2026-03-15",
  "period_start": "2026-03-01",
  "period_end": "2026-03-15",
  "label": "Mar '26 (15)",
  "gross": 1000.00,
  "taxes": 300.00,
  "taxRate": 30.00,
  "preTax": 80.00,
  "postTax": 20.00,
  "net": 600.00,
  "k401": 50.00,
  "hsa": 15.00,
  "hc": 10.00,
  "ltd": 5.00,
  "transit": 0,
  "espp": 0,
  "other_post": 20.00,
  "bonus_gross": 0,
  "bonus_taxes": 0,
  "bonus_net": 0,
  "bonus_label": "",
  "espp_dd": 0,
  "events": [],
  "ytd": {
    "gross": 6000.00,
    "taxes": 1800.00,
    "preTax": 480.00,
    "postTax": 120.00,
    "k401": 300.00,
    "hsa": 90.00,
    "hc": 60.00,
    "ltd": 30.00,
    "transit": 0,
    "espp": 0,
    "federal": 900.00,
    "nyState": 330.00,
    "nycTax": 220.00,
    "ss": 250.00,
    "medicare": 100.00
  }
}
```

**Regla de verificación de cada entrada:**
```
net + k401 + hsa + hc + ltd + transit + espp + other_post + taxes
+ bonus_net + bonus_taxes
= gross + bonus_gross − espp_dd
```
Verificar siempre antes de guardar.

**Casos especiales:**
- **Bonus puro** (`id: YYYY-MM-DD-bonus`): `gross: 0`, `bonus_gross/taxes/net` con los valores del PDF. `bonus_label`: "Bonus Rendimiento" o similar.
- **ESPP Disqualifying Disposition**: ingreso fantasma → poner en `espp_dd`. La fórmula de verificación lo resta del expected.
- **Nómina de ajuste/devolución** (`id: YYYY-MM-DD-refund`): `gross` puede ser negativo. Añadir evento 🔄.

### Secciones anuales del JSON (valores YTD del último PDF)

```json
"annualTotals": {
  "gross":    /* YTD Gross Pay */,
  "taxes":    /* YTD Employee Taxes */,
  "taxRate":  /* taxes / gross × 100 */,
  "preTax":   /* YTD Pre Tax Deductions */,
  "postTax":  /* YTD Post Tax Deductions */,
  "net":      /* suma de todos los net+bonus_net en payslips[] */,
  "k401":     /* YTD 401k PreTax */,
  "hsa":      /* YTD Employee HSA */,
  "hc":       /* YTD Health Care */,
  "note":     /* solo si el año está en curso: "Acumulado parcial (X meses)" */
},
"taxBreakdown": {
  "federal":  /* YTD Federal Withholding */,
  "nyState":  /* YTD NY State Tax */,
  "nycTax":   /* YTD NYC Tax */,
  "ss":       /* YTD Social Security */,
  "medicare": /* YTD Medicare */
},
"preTaxBreakdown": {
  "k401":        /* YTD 401k */,
  "hsa":         /* YTD HSA */,
  "healthCare":  /* YTD Health Care */,
  "ltd":         /* YTD LTD */,
  "transit":     /* YTD Transit */
},
"postTaxBreakdown": {
  "lifeIns_legal": /* YTD Life+Legal (total postTax − espp_ytd) */,
  "espp":          /* YTD ESPP */
}
```

---

## Formato de nóminas por sistema

| Sistema | Período | Formato numérico | Diferencias |
|---------|---------|-----------------|-------------|
| **Workday** | ago–dic 2024 | Europeo: `8.716,25` | NYC Tax no activo en ago 2024. Incluye NY SDI y NY PFL. |
| **SuccessFactors** | 2025 en adelante | Americano: `8,716.25` | NYC Tax siempre activo. Sin NY SDI/PFL. |

---

## Valores de referencia (para detectar anomalías)

Esta sección debe actualizarse con los valores reales de cada año. Ejemplo con valores ficticios:

| Concepto | Valor esperado |
|----------|---------------|
| Gross por quincena (regular) | $1,000.00 |
| Gross mensual (2 quincenas) | ~$2,000.00 |
| Impuestos quincena normal | ~$300 |
| `taxRate` quincena normal | ~30% |
| Pre-Tax quincena normal | $80.00 |
| Post-Tax quincena normal | $20.00 |
| Neto quincena normal | ~$600 |
| 401k / quincena | $50.00 |
| HSA / quincena | $15.00 |
| Health Care / quincena | $10.00 |
| LTD / quincena | $5.00 |
| Tope Social Security | ~$168,600 (varía cada año) |

> Si el neto se desvía significativamente de lo esperado sin causa aparente, revisar "Other Information" del PDF.

---

## Glosario rápido

| Término | Significado |
|---------|-------------|
| **OASDI / Social Security** | Impuesto jubilación federal (6.2%, tope anual) |
| **Medicare** | Impuesto seguro médico federal (1.45%, sin tope) |
| **HSA** | Health Savings Account — ahorro para gastos médicos, triple ventaja fiscal |
| **LTD** | Long Term Disability — seguro de incapacidad laboral |
| **ESPP** | Employee Stock Purchase Plan — compra acciones IBM con 15% descuento |
| **Disqualifying Disposition** | Venta anticipada de acciones ESPP → tributación como renta ordinaria |
| **espp_dd** | ESPP Disqualifying Disposition: ingreso fantasma que aumenta gross y taxes sin generar efectivo |
| **Taxable Expenses / GI Business Expense** | Gastos cubiertos por IBM que el fisco trata como ingreso tuyo (no cobras extra, pero pagas más impuestos) |
| **Award Tax Assistance** | IBM paga los impuestos de un premio no monetario |
| **GLI Imputed Earnings** | Valor del seguro de vida colectivo IBM > $50K (ingreso nominal, no efectivo) |
| **Employer HSA Contribution** | Regalo anual de IBM a tu cuenta HSA — aparece en Other Information, no en deducciones |
| **Transit Benefit** | Abono transporte pre-tax |
| **Pre-Tax** | Reduce base imponible → pagas menos impuestos (401k, HSA, HC, LTD, Transit) |
| **Post-Tax** | No reduce impuestos (ESPP, Life Insurance, Legal) |

---

## Regla de actualización del dashboard

> ⚠️ **Obligatorio:** Siempre que el usuario pida cambios en el `dashboard.html`, Claude debe actualizar también este `CLAUDE.md` documentando los cambios en la sección "Diseño del dashboard" a continuación. Esta regla se aplica sin excepción.

---

## Diseño del dashboard (dashboard.html)

Esta sección recoge las decisiones de diseño acordadas con el usuario. Al hacer cambios en el dashboard, respetar siempre estas decisiones salvo instrucción explícita en contrario.

### Gráfico principal — Barras horizontales por nómina

- **Vista doble:** el toggle "📅 Mensual / 📋 Quincenas" en la barra de controles permite ver una barra por mes (agrupando las dos quincenas del mes) o una barra por quincena. Por defecto: **Mensual**.
- **Barras horizontales** (no verticales). Implementado con HTML/CSS puro (no Chart.js), para poder colocar la columna de eventos alineada a la derecha.
- **Escala relativa al máximo bruto** del período visible: `cashGross = (gross + bonus_gross − espp_dd) / maxCashGross × 100%`. Los segmentos dentro de la barra son proporcionales a su valor respecto al mismo `maxCashGross`. El campo `espp_dd` se excluye porque es ingreso fantasma (no genera flujo de caja).
- **Columna de eventos a la derecha** de cada barra — persistente (no popup). Se muestra con `grid-template-columns: 90px 1fr 280px`. Sin tooltip flotante para los comentarios.
- **Tooltip por segmento** (pequeño, CSS `::after`): muestra "Concepto: $X,XXX.XX" al pasar el ratón. Los contenedores de barra usan `overflow: visible` para que el tooltip no se corte. Los segmentos tienen `min-width: 3px` y `cursor: pointer` para mejorar la interacción.
- **Sin animaciones** en ningún cambio de filtro o año. Los gráficos Chart.js secundarios llevan `animation: false`.
- **Persistencia de preferencias:** el dashboard guarda en `localStorage` (clave `payslip-dashboard-prefs`) el año seleccionado, modo de vista (mensual/quincenas), modo de gráfico (single/dual/waterfall/divergent), estado de los checkboxes de segmentos, y modo de ocultar importes. Al reabrir el archivo HTML, se restauran automáticamente.

### Vista Mensual vs. Quincenas

La función JS `groupByMonth(payslips)` suma todos los campos numéricos de las quincenas de un mismo mes YYYY-MM:
- Usa `period_end.slice(0,7)` para agrupar
- Suma: `gross`, `taxes`, `preTax`, `postTax`, `net`, `k401`, `hsa`, `hc`, `ltd`, `transit`, `espp`, `other_post`, `espp_dd`, `bonus_gross`, `bonus_taxes`, `bonus_net`
- Recalcula `taxRate = taxes / gross × 100`
- Label mensual: "Ene '26", "Feb '26", etc. (sin número de quincena)
- Combina los `events[]` de ambas quincenas

### Segmentos y colores

| Clave       | Label         | Color    | Por defecto |
|-------------|---------------|----------|-------------|
| net         | Neto          | #42be65  | ✓ on        |
| bonus_net   | Bonus Neto    | #6fdc8c  | ✓ on        |
| k401        | 401k          | #4589ff  | ✓ on        |
| hsa         | HSA           | #08bdba  | ✓ on        |
| hc          | Health Care   | #be95ff  | ✓ on        |
| ltd         | LTD           | #8d8d8d  | off         |
| transit     | Transit       | #ff832b  | off         |
| espp        | ESPP          | #f1c21b  | ✓ on        |
| other_post  | Life+Legal    | #6e6e6e  | off         |
| taxes       | Impuestos     | #fa4d56  | ✓ on        |
| bonus_tax   | Bonus Imp.    | #ff8389  | ✓ on        |

**Separación neto / bonus:** el campo `net` es el neto de la nómina regular; `bonus_net` es el neto del bonus. Nunca mezclarlos. Si una quincena tiene bonus, sus campos `bonus_gross`, `bonus_taxes`, `bonus_net` deben ser no-cero.

### Nóminas de bonus (ejemplo)

Si hay un bonus en entrada separada (ej: `id: "YYYY-MM-DD-bonus"`):
- `gross: 0`, `bonus_gross: XXX`, `bonus_taxes: YYY`, `bonus_net: ZZZ`
- `k401` puede tener valor si hay 401k asociado al bonus

En vista **Mensual**, las quincenas y el bonus del mismo mes se suman en una sola barra.

Fórmula de verificación por entrada: `net + k401 + hsa + hc + ltd + transit + espp + other_post + taxes + bonus_net + bonus_taxes = gross + bonus_gross − espp_dd`

### Gráficos secundarios (Chart.js)

- **% Impuestos nómina a nómina** (línea): dos series, `taxRate` (rojo) y `netRate` (verde punteado).
- **Desglose de impuestos** (donut): Federal, NY State, NYC Tax, SS, Medicare. Usa datos `taxBreakdown` YTD.
- Ambos con `animation: false`.

### Estructura HTML del gráfico principal

```
.ps-grid  (display:grid, 3 columnas: 90px | 1fr | 280px)
  ├── .ps-col-header × 3      (cabecera: Período | Desglose | Eventos)
  └── por cada entry:
      ├── .ps-label            (etiqueta del período)
      ├── .ps-bar-cell
      │   ├── .ps-bar          (flex row, width = barWidthPct%)
      │   │   └── .ps-seg × N (segmentos activos, tooltip CSS ::after)
      │   └── .ps-val          (texto "$X neto [· $Y bonus]")
      ├── .ps-events-cell      (columna de eventos, borde izquierdo)
      │   └── .ps-event × N
      └── .ps-divider × 3     (separador entre filas, no tras la última)
```

### Selector de modo de vista

El gráfico principal tiene 4 modos de visualización, controlados por la variable `chartMode`:

| Modo | Botón | Descripción |
|------|-------|-------------|
| `single` | Actual | Barra única horizontal con todos los segmentos (comportamiento original) |
| `dual` | Dual | Bruto arriba como barra de referencia semitransparente, desglose abajo |
| `waterfall` | Cascada | Flujo waterfall: Bruto → − Impuestos → − Pre-Tax → − Post-Tax → = Neto |
| `divergent` | Divergente | Neto a la izquierda del eje central, deducciones a la derecha |

**Funciones de renderizado:**
- `renderSingleBar()` — modo actual (default)
- `renderDualBars()` — bruto + desglose apilados verticalmente
- `renderWaterfall()` — 5 filas por nómina mostrando el flujo
- `renderDivergent()` — barras bidireccionales desde un eje central

Los selectores están en `.controls-panel` junto a los checkboxes de segmentos.

### Cálculo de anchos de segmentos

Los segmentos dentro de cada barra usan **porcentajes relativos al cashGross de esa entrada**, no al maxGross global. Esto es necesario porque la barra contenedora ya tiene `width: barWidthPct%` (donde `barWidthPct = cashGross / maxGross`). Si los segmentos usaran porcentajes de maxGross, se "comprimirían" doblemente.

```javascript
// Correcto: segmentos llenan la barra al 100%
const segPct = (v / cashGross * 100).toFixed(3);

// Incorrecto: segmentos más pequeños de lo debido
// const segPct = (v / maxGross * 100).toFixed(3);
```

### Modo privacidad (ocultar importes)

- **Botón toggle** en el panel de controles (sección "Privacidad"): `👁️ Importes` / `🙈 Importes`
- **Estado:** la variable `hideAmounts` controla si los importes se ocultan. Se guarda en localStorage junto con las demás preferencias.
- **Comportamiento:** cuando está activo, todos los valores monetarios y porcentajes se reemplazan por `•••` o `••%`
- **Funciones helper:**
  - `fmtH(n)` — versión de `fmt()` que muestra `•••` si `hideAmounts` es true
  - `fmt2H(n)` — versión de `fmt2()` con ocultación
  - `pctH(n)` — versión de `pct()` que muestra `••%` si `hideAmounts` es true
- **Áreas afectadas:** KPIs, tooltips de segmentos, valores "neto/bonus" junto a las barras, tabla comparativa, panel de ahorro, tooltips de gráficos Chart.js
- **Las barras mantienen su proporción visual** aunque los valores estén ocultos, permitiendo ver la distribución sin revelar cifras exactas
