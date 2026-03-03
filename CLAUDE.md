# Instrucciones para Procesar Nóminas IBM
Cuando el usuario añada una nómina nueva, lee este fichero primero y sigue los pasos al pie de la letra.

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

## Flujo cuando llega una nómina nueva

```
PDF → Paso 1: Extraer datos
    → Paso 2: Calcular métricas
    → Paso 3: Detectar eventos
    → Paso 4: Actualizar data/AAAA.json   ← primero
    → Paso 5: Actualizar data/AAAA.md     ← segundo (derivado)
    → Paso 6: Actualizar dashboard.html   ← tercero (derivado)
    → Paso 7: Crear data/AAAA.json nuevo si es enero de año nuevo
```

---

## Paso 1 — Extraer datos del PDF

| Campo | Dónde está en el PDF |
|-------|---------------------|
| **Pay Period** | Cabecera (`MM/DD/YYYY - MM/DD/YYYY`) |
| **Net Payment** | Cabecera, arriba a la derecha |
| **Gross Pay** | Tabla resumen superior, columna "Gross Pay" — usar Current, no YTD |
| **Employee Taxes** | Tabla resumen, columna "Employee Taxes" — Current |
| **Pre Tax Deductions** | Tabla resumen, columna "Pre Tax Deductions" — Current |
| **Post Tax Deductions** | Tabla resumen, columna "Post Tax Deductions" — Current |
| **YTD Gross Pay** | Tabla resumen, columna "Gross Pay" — YTD (para totales anuales) |
| **YTD Employee Taxes** | Tabla resumen, columna "Employee Taxes" — YTD |
| **YTD Pre Tax** | Tabla resumen, columna "Pre Tax Deductions" — YTD |
| **YTD Post Tax** | Tabla resumen, columna "Post Tax Deductions" — YTD |
| **Earnings detalle** | Sección "Earnings" — anotar todo lo que no sea Regular Salary |
| **Taxes detalle** | Sección "Employee Taxes" — Federal, NY, NYC, SS, Medicare (Current y YTD) |
| **Pre-Tax detalle** | Sección "Pre Tax Deductions" — 401k, HSA, Health Care, LTD, Transit (Current) |
| **Post-Tax detalle** | Sección "Post Tax Deductions" — Life, Legal, ESPP (Current) |
| **Other Information** | Sección final — Employer HSA, Taxable Expenses, Awards, Merch Points |

> ⚠️ Verificar siempre: Gross − Employee Taxes − Pre Tax Ded − Post Tax Ded = Net Payment

---

## Paso 2 — Calcular métricas

```
taxRate     = Employee Taxes (Current) / Gross Pay (Current) × 100
k401        = valor "401k PreTax" en Pre Tax Deductions (Current)
hsa         = valor "Employee HSA" en Pre Tax Deductions (Current)
hc          = valor "Health Care Premium" en Pre Tax Deductions (Current)
ltd         = valor "LTD" en Pre Tax Deductions (Current)
transit     = valor "Transit Benefit" en Pre Tax Deductions (Current), o 0
espp        = valor "ESPP" en Post Tax Deductions (Current), o 0
other_post  = total Post Tax Deductions (Current) − espp
espp_dd     = "ESPP Disqualifying Disposition" en Earnings (si aparece), o 0
              → ingreso fantasma: aumenta gross y taxes sin generar efectivo
```

Un `taxRate` normal es ~30%. Si es >35%, buscar causa: Taxable Expenses, bonus, o Business Expense en Other Information.

---

## Paso 3 — Detectar eventos especiales

| Señal en el PDF | Evento a registrar en `events[]` |
|-----------------|----------------------------------|
| Earnings tiene algo además de Regular Salary | 🎁 Bonus / 🏆 Award Tax Assistance $XX |
| "GI Taxable Business Expense" en Other Information | ⚠️ GI Business Expense $X,XXX → +impuestos |
| "Taxable Expenses" en Other Information | ⚠️ Taxable Expenses $X,XXX → +impuestos |
| ESPP aparece en Post-Tax (antes era 0) | 📈 Inicio ESPP $X/q |
| ESPP desaparece de Post-Tax | 🏁 Fin ESPP |
| 401k = $0 cuando antes tenía valor | ⏸️ Suspensión 401k (y HSA si aplica) |
| 401k vuelve a tener valor tras $0 | ▶️ Reactivación 401k ($XXX) |
| Social Security = $0 en la quincena | 🎉 Tope SS alcanzado → +$XXX/q |
| "Employer HSA Contribution" en Other Information | 💰 Employer HSA $XXX IBM (regalo enero, solo info) |
| "Award Tax Assistance" en Earnings | 🏆 Award Tax Asst $XX |
| "Merchandise Points Award" en Other Information | 🎖️ Merch Points $XX (solo info) |
| "ESPP Disqualifying Disposition" en Earnings | 📈 ESPP Disqualifying Disposition $XX incluido en bruto |
| Impuesto negativo / devolución (nómina de ajuste) | 🔄 Devolución ajuste fiscal $XX |
| Gross sube respecto al período anterior (no por bonus) | 📈 Subida salarial |
| Transit Benefit aparece o cambia de valor | 🚇 Transit $XX |

---

## Paso 4 — Actualizar data/AAAA.json (fuente de verdad)

### 4a. Estructura del JSON

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

### 4b. Estructura de cada entrada en `payslips[]`

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

**Nómina de bonus puro** (ej: Payslip-2025-04-08-bonus.pdf):
- `gross: 0`, `bonus_gross: XXXX`
- `bonus_taxes`, `bonus_net` con los valores del PDF
- Si el bonus tiene 401k asociado, ponerlo en `k401` (no se zeroed)
- `bonus_label`: "Bonus Rendimiento" o similar

**ESPP Disqualifying Disposition** (ej: dic 2025):
- El valor aparece en Earnings como ingreso fantasma
- Se pone en `espp_dd`; no hay flujo de caja real
- La fórmula de verificación resta `espp_dd` del expected

**Nómina de ajuste / devolución** (ej: Payslip-2025-12-31-refund.pdf):
- `gross` puede ser negativo o muy pequeño
- Registrar como entrada separada con id `YYYY-MM-DD-refund`
- Añadir evento 🔄 Devolución ajuste fiscal $XX

### 4c. Añadir una quincena nueva

Para la primera quincena del mes: añadir la nueva entrada al final de `payslips[]`. No hay que comprobar si existe el mes — cada entrada es independiente.

Para la segunda quincena del mismo mes: igualmente, añadir nueva entrada. El dashboard agrupa automáticamente por mes.

### 4d. Actualizar secciones anuales del JSON con valores YTD del PDF

Estas secciones usan la columna **YTD** del último PDF del año (acumulado del año en curso):

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

## Paso 5 — Actualizar data/AAAA.md (derivado legible)

Abrir el fichero `data/AAAA.md` y actualizar estas secciones:

1. **Tabla por Quincena** — añadir fila con los datos Current de la quincena nueva.
2. **Tabla Mensual Resumida** — actualizar o añadir fila del mes. Si ya existe la primera quincena, completar sumando ambas.
3. **ACUMULADO / TOTAL** — actualizar con los valores YTD.
4. **Desglose de Impuestos acumulado** — usar YTD de los taxes del PDF.
5. **Deducciones Pre-Tax acumuladas** — usar YTD del PDF.
6. **Eventos Especiales** — añadir sección nueva si hay evento relevante.

Actualizar la fecha en la cabecera: `*Año en curso — última actualización: DD de MES de AAAA*`

---

## Paso 6 — Verificar dashboard.html (derivado visual)

El dashboard carga los datos directamente desde `data/AAAA.json`, por lo que **no necesita modificaciones** cuando se añade una nueva nómina. El dashboard lee automáticamente los ficheros JSON al abrirse.

**Solo hay que actualizar el dashboard si:**
- Se añade un año nuevo (ej: 2027) → añadir el año a `AVAILABLE_YEARS` en el código
- Se modifica la estructura de datos

> ⚠️ La escala de las barras usa `cashGross = gross + bonus_gross − espp_dd` para excluir el ingreso fantasma del ESPP DD.

---

## Paso 7 — Crear fichero nuevo si es enero de año nuevo

Si la nómina es de enero de un año nuevo (ej: `2027`):

1. Crear `data/2027.json` copiando la estructura de `data/2026.json`, vaciar `payslips[]`, poner `annualTotals` y `taxBreakdown` a cero, año en `"year": 2027`, sistema `"SuccessFactors"`.
2. Crear `2027.md` con la misma estructura que `2026.md` pero en blanco.
3. En `dashboard.html`:
   - Añadir `2027` a la constante `AVAILABLE_YEARS` (ej: `const AVAILABLE_YEARS = [2024, 2025, 2026, 2027];`)
   - Añadir un nuevo botón `<button class="year-tab" data-year="2027">2027</button>` en la sección `.year-tabs`
4. Actualizar la tabla "Estructura de Ficheros" de este `CLAUDE.md` cerrando el año anterior y abriendo el nuevo.

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
- **Persistencia de preferencias:** el dashboard guarda en `localStorage` (clave `payslip-dashboard-prefs`) el año seleccionado, modo de vista (mensual/quincenas), modo de gráfico (single/dual/waterfall/divergent) y estado de los checkboxes de segmentos. Al reabrir el archivo HTML, se restauran automáticamente.

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
