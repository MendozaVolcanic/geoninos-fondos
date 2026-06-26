"""Página: Acerca de — Geoniños Fondos."""
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Acerca de — Geoniños", page_icon="🪨", layout="wide")

st.title("🪨 Geoniños — Libro infantil de geología de Chile")
st.caption("Dashboard de fondos para crear, editar y publicar")
st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
## ¿Qué es este dashboard?

Sistema de monitoreo de **fondos concursables, auspicios y vías editoriales** para
financiar un **libro álbum de geología para niñas y niños** (3–8 años), ambientado en
el paisaje chileno. Autor: geólogo de SERNAGEOMIN.

Es un proyecto **independiente** del dashboard OVDAS (que cubre equipamiento de
monitoreo volcánico): aquí solo hay fondos relevantes para **divulgación y libro**.

### ¿Qué cubre?

| Categoría | Para qué |
|-----------|----------|
| ✍️ Crear | Escribir + ilustrar la obra (Beca de Creación Literaria) |
| 🖨️ Editar | Imprimir, distribuir y difundir (Apoyo a Ediciones) |
| 🔬 Divulgación científica | MinCiencia (Ciencia Pública), Explora |
| 🤝 Patrocinio | Avales sin dinero que fortalecen postulaciones (MINCAP, SERNAGEOMIN, CMN) |
| 🏭 Auspicio privado | RSE minera por afinidad temática (CMP, FME/BHP, Los Pelambres) |
| 📚 Vía editorial | Llegar con una maqueta a una editorial (Amanuta, Ekaré Sur…) |

### Hallazgo rector

En Chile **los libros se financian por el Fondo del Libro y la Lectura del MINCAP,
no por FONDART**. Ese fondo es el eje del proyecto. El BID no es viable para un autor
individual; UNESCO solo sirve como auspicio simbólico.

### Cómo se calcula la relevancia

Cada fondo recibe un **score de 0 a 100** según su afinidad con un libro infantil de
geología (qué financia, afinidad temática, viabilidad para un autor/funcionario).

### Cómo se actualiza ("escaneo constante")

El scanner (`scan.py`) **recalcula el estado** de cada convocatoria (abierto / próximo
/ cerrado) comparando las fechas de apertura y cierre con la fecha de hoy. Corre
automáticamente vía GitHub Actions, así el tablero refleja qué convocatorias siguen
vivas sin intervención manual.
    """)

with col2:
    st.markdown("### 📊 Estado del sistema")
    csv_path = Path(__file__).parent.parent / "data" / "fondos_divulgacion.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        df["score_geoninos"] = pd.to_numeric(df.get("score_geoninos", 0), errors="coerce").fillna(0)
        st.metric("Total fondos", len(df))
        st.metric("🟢 Abiertos hoy", len(df[df["estado"] == "abierto"]))
        st.metric("🟡 Próximos", len(df[df["estado"] == "proximo"]))
        st.metric("Relevancia promedio", f"{df['score_geoninos'].mean():.0f}")
        st.divider()
        st.markdown("**Top por relevancia**")
        for _, r in df.nlargest(5, "score_geoninos")[["nombre", "score_geoninos"]].iterrows():
            st.progress(int(r["score_geoninos"]) / 100,
                        text=f"{r['nombre'][:34]}… {int(r['score_geoninos'])}")

st.divider()
st.markdown("""
## 📬 Sobre el proyecto

**Geoniños** — libro de divulgación geológica infantil. Hilo narrativo propuesto:
*"Pewma y la piedrita viajera"*, una niña que sigue una piedrita por el tiempo
geológico y el territorio de Chile (volcán → tectónica → agua → fósiles → suelo →
minería → geopatrimonio).

Datos verificados al 2026-06-26. Lo no confirmado contra fuente oficial está marcado
como *por verificar* en cada ficha.
""")
