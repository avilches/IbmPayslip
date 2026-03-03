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

1. **Pasar las nóminas a Claude** para que las procese y genere los JSON:
   ```bash
   claude
   > [arrastra el PDF de la nómina]
   ```
   Claude leerá CLAUDE.md y procesará la nómina automáticamente, creando los ficheros JSON en `data/`.

2. **Arrancar el servidor** con uv:
   ```bash
   uv run server.py
   ```

3. **Abrir el dashboard** en el navegador:
   ```
   http://localhost:8000/dashboard.html
   ```

> **Nota:** El dashboard necesita un servidor local porque los navegadores bloquean las peticiones fetch a ficheros locales por seguridad (CORS). Por eso no se puede abrir `dashboard.html` directamente.

## Funcionalidades del dashboard

- Vista mensual o por quincena
- Múltiples modos de visualización (barras, cascada, divergente)
- Desglose de impuestos y deducciones
- Histórico por año (2024, 2025, 2026...)
- Persistencia de preferencias en localStorage
