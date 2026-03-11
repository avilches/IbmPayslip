---
description: Procesa una nómina IBM nueva y actualiza JSON, MD y dashboard
---

El usuario ha añadido una nómina nueva. Sigue estos pasos al pie de la letra. Lee el CLAUDE.md completo antes de empezar si no lo tienes en contexto.

## Paso 1 — Leer el PDF

Lee el fichero PDF indicado por el usuario (o el más reciente en `data/` si no especifica).

Extrae estos campos de la nómina:

- **Pay Period** (cabecera): fecha inicio y fin
- **Net Payment** (cabecera, arriba derecha)
- **Gross Pay** — columna Current (no YTD)
- **Employee Taxes** — columna Current
- **Pre Tax Deductions** — columna Current
- **Post Tax Deductions** — columna Current
- **YTD** de todos los campos anteriores (para actualizar totales anuales)
- **Earnings detalle**: todo lo que no sea Regular Salary
- **Employee Taxes detalle**: Federal, NY State, NYC Tax, SS, Medicare (Current y YTD)
- **Pre-Tax detalle**: 401k, HSA, Health Care, LTD, Transit (Current)
- **Post-Tax detalle**: ESPP, Life, Legal (Current)
- **Other Information**: Employer HSA, Taxable Expenses, Awards, Merch Points

Verifica: `Gross − Employee Taxes − Pre Tax Ded − Post Tax Ded = Net Payment`

Si no cuadra, revisa los valores antes de continuar.

## Paso 2 — Calcular métricas

```
taxRate    = Employee Taxes (Current) / Gross Pay (Current) × 100
k401       = "401k PreTax" en Pre Tax Deductions (Current)
hsa        = "Employee HSA" en Pre Tax Deductions (Current)
hc         = "Health Care Premium" en Pre Tax Deductions (Current)
ltd        = "LTD" en Pre Tax Deductions (Current)
transit    = "Transit Benefit" en Pre Tax Deductions (Current), o 0
espp       = "ESPP" en Post Tax Deductions (Current), o 0
other_post = total Post Tax Deductions (Current) − espp
espp_dd    = "ESPP Disqualifying Disposition" en Earnings, o 0
```

Un `taxRate` normal es ~30%. Si es >35%, buscar causa (Taxable Expenses, bonus, Business Expense).

## Paso 3 — Detectar eventos especiales

Añadir al campo `events[]` lo que corresponda:

| Señal en el PDF | Evento |
|-----------------|--------|
| Earnings tiene algo además de Regular Salary | 🎁 Bonus / 🏆 Award Tax Assistance $XX |
| "GI Taxable Business Expense" en Other Information | ⚠️ GI Business Expense $X,XXX → +impuestos |
| "Taxable Expenses" en Other Information | ⚠️ Taxable Expenses $X,XXX → +impuestos |
| ESPP aparece en Post-Tax (antes era 0) | 📈 Inicio ESPP $X/q |
| ESPP desaparece de Post-Tax | 🏁 Fin ESPP |
| 401k = $0 cuando antes tenía valor | ⏸️ Suspensión 401k |
| 401k vuelve a tener valor tras $0 | ▶️ Reactivación 401k ($XXX) |
| Social Security = $0 en la quincena | 🎉 Tope SS alcanzado → +$XXX/q |
| "Employer HSA Contribution" en Other Information | 💰 Employer HSA $XXX IBM |
| "ESPP Disqualifying Disposition" en Earnings | 📈 ESPP Disqualifying Disposition $XX incluido en bruto |
| Impuesto negativo / devolución | 🔄 Devolución ajuste fiscal $XX |
| Gross sube respecto al período anterior (no por bonus) | 📈 Subida salarial |
| Transit Benefit aparece o cambia de valor | 🚇 Transit $XX |

## Paso 4 — Actualizar data/AAAA.json (fuente de verdad)

Lee el fichero `data/AAAA.json` correspondiente al año de la nómina.

Añade una nueva entrada al final de `payslips[]` con esta estructura:

```json
{
  "id": "YYYY-MM-DD",
  "period_start": "YYYY-MM-DD",
  "period_end": "YYYY-MM-DD",
  "label": "Mes 'AA (DD)",
  "gross": 0.00,
  "taxes": 0.00,
  "taxRate": 0.00,
  "preTax": 0.00,
  "postTax": 0.00,
  "net": 0.00,
  "k401": 0.00,
  "hsa": 0.00,
  "hc": 0.00,
  "ltd": 0.00,
  "transit": 0,
  "espp": 0,
  "other_post": 0.00,
  "bonus_gross": 0,
  "bonus_taxes": 0,
  "bonus_net": 0,
  "bonus_label": "",
  "espp_dd": 0,
  "events": [],
  "ytd": {
    "gross": 0.00,
    "taxes": 0.00,
    "preTax": 0.00,
    "postTax": 0.00,
    "k401": 0.00,
    "hsa": 0.00,
    "hc": 0.00,
    "ltd": 0.00,
    "transit": 0,
    "espp": 0,
    "federal": 0.00,
    "nyState": 0.00,
    "nycTax": 0.00,
    "ss": 0.00,
    "medicare": 0.00
  }
}
```

**Verifica antes de guardar:**
```
net + k401 + hsa + hc + ltd + transit + espp + other_post + taxes + bonus_net + bonus_taxes
= gross + bonus_gross − espp_dd
```

Luego actualiza las secciones anuales con los valores YTD del PDF:
- `annualTotals`: gross, taxes, taxRate, preTax, postTax, net (suma de todos los net+bonus_net), k401, hsa, hc
- `taxBreakdown`: federal, nyState, nycTax, ss, medicare
- `preTaxBreakdown`: k401, hsa, healthCare, ltd, transit
- `postTaxBreakdown`: lifeIns_legal (postTax YTD − espp YTD), espp

## Paso 5 — Actualizar data/AAAA.md (derivado legible)

Lee el fichero `data/AAAA.md` y actualiza:

1. **Tabla por Quincena** — añadir fila con los datos Current
2. **Tabla Mensual Resumida** — añadir o completar la fila del mes
3. **ACUMULADO / TOTAL** — actualizar con valores YTD
4. **Desglose de Impuestos acumulado** — valores YTD de taxes
5. **Deducciones Pre-Tax acumuladas** — valores YTD pre-tax
6. **Eventos Especiales** — añadir si hay eventos relevantes
7. **Fecha en cabecera** — actualizar a la fecha de hoy

## Paso 6 — Verificar dashboard

El dashboard carga los JSON automáticamente. **No requiere cambios** salvo que:
- Sea enero de un año nuevo → añadir el año a `AVAILABLE_YEARS` y un botón `.year-tab` en `dashboard.html`

## Paso 7 — Si es enero de un año nuevo

1. Crear `data/AAAA.json` nuevo copiando la estructura del año anterior, con `payslips[]` vacío y totales a cero
2. Crear `data/AAAA.md` nuevo con la misma estructura pero en blanco
3. Añadir el año a `AVAILABLE_YEARS` en `dashboard.html` y el botón correspondiente
4. Actualizar la tabla de ficheros en `CLAUDE.md`

---

Al terminar, muestra un resumen con:
- Nómina procesada (período, gross, net, taxRate)
- Eventos detectados
- Verificación de la fórmula (✓ cuadra / ✗ no cuadra)