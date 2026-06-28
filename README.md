# 🪨 Geoniños — Fondos para el libro infantil de geología

Dashboard público de **fondos concursables, auspicios y vías editoriales** para
financiar un libro álbum de geología para niñas y niños en Chile.

Proyecto **independiente** del dashboard OVDAS — aquí solo hay fondos de
divulgación, libro y cultura.

### 🔗 En vivo: **https://geoninos-fondos.streamlit.app/**

[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://geoninos-fondos.streamlit.app/)

---

## ¿Qué hace?

- Cataloga fondos para **crear** (escribir+ilustrar), **editar/imprimir**,
  **divulgar**, conseguir **patrocinios/avales**, **auspicios privados** (RSE minera)
  y **vías editoriales** directas.
- **Escaneo constante:** `scan.py` recalcula el estado de cada convocatoria
  (🟢 abierto / 🟡 próximo / 🔴 cerrado) comparando las fechas con la fecha de hoy.
  Un GitHub Action lo corre 2×/día y commitea el CSV; Streamlit Cloud redespliega solo.

## Estructura

```
geoninos-fondos/
├── app.py                      # dashboard Streamlit
├── scan.py                     # scanner: catálogo curado + recálculo de estado → CSV
├── pages/2_Acerca_de.py        # página "Acerca de"
├── data/fondos_divulgacion.csv # datos (generados por scan.py)
├── requirements.txt
├── .gitignore
└── .github/workflows/scan.yml  # cron de escaneo automático
```

## Uso local

```bash
pip install -r requirements.txt
python scan.py            # genera/actualiza data/fondos_divulgacion.csv
streamlit run app.py      # abre http://localhost:8501
```

`python scan.py --sin-red` usa solo el catálogo curado (sin tocar internet).

## Desplegar público (gratis)

1. Crear un repo en GitHub (p. ej. `geoninos-fondos`) y subir esta carpeta.
2. En [share.streamlit.io](https://share.streamlit.io) → New app → elegir el repo,
   rama `main`, archivo `app.py`. Queda en `https://<usuario>-geoninos-fondos.streamlit.app`.
3. El GitHub Action ya corre solo (también se puede lanzar a mano en la pestaña Actions).

## Datos

Catálogo curado y **verificado al 2026-06-26** a partir del catastro del proyecto
(`02_fondos/catastro_fondos_libro.md`). Lo no confirmado contra fuente oficial está
marcado como *por verificar* (`verificado = no/parcial`) en cada ficha. No se inventaron
montos ni plazos.

## Cómo agregar o corregir un fondo

Edita la lista `CATALOGO` en `scan.py` (un dict por fondo) y corre `python scan.py`.
Los campos de fecha (`fecha_apertura`, `fecha_cierre`) en formato `YYYY-MM-DD` activan
el recálculo automático de estado.
