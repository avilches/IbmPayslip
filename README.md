# IBM Payslip Dashboard

Dashboard interactivo para visualizar y analizar nóminas de IBM.

## Estructura

```
├── dashboard.html     ← Abrir en navegador para ver el dashboard
├── CLAUDE.md          ← Instrucciones para procesar nóminas con Claude
└── data/              ← Carpeta privada (no en git)
    ├── *.json         ← Datos de nóminas por año (fuente de verdad)
    ├── *.md           ← Resúmenes legibles por año
    └── *.pdf          ← PDFs originales de las nóminas
```

## Cómo empezar

1. **Crear la carpeta `data/`** con los ficheros JSON de cada año (ver estructura en CLAUDE.md)

2. **Abrir `dashboard.html`** en el navegador para visualizar los datos

3. **Para añadir una nómina nueva**, usar Claude Code:
   ```
   claude
   > [arrastra el PDF de la nómina]
   ```
   Claude leerá CLAUDE.md y procesará la nómina automáticamente.

## Funcionalidades del dashboard

- Vista mensual o por quincena
- Múltiples modos de visualización (barras, cascada, divergente)
- Desglose de impuestos y deducciones
- Histórico por año (2024, 2025, 2026...)
- Persistencia de preferencias en localStorage
