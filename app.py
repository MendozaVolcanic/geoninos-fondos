"""
Dashboard Geoniños — Fondos para publicar un libro infantil de geología
=======================================================================

Versión pública para desplegar en Streamlit Community Cloud.
Los datos vienen de data/fondos_divulgacion.csv, generado por scan.py
(catálogo curado + recálculo automático del estado según la fecha).

Proyecto independiente — NO comparte datos con el dashboard OVDAS.
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Geoniños — Fondos para el libro",
    page_icon="🪨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.estado-abierto      { background:#16a34a; color:white; padding:2px 10px; border-radius:12px; font-size:0.8em; font-weight:bold; }
.estado-proximo      { background:#d97706; color:white; padding:2px 10px; border-radius:12px; font-size:0.8em; font-weight:bold; }
.estado-cerrado      { background:#dc2626; color:white; padding:2px 10px; border-radius:12px; font-size:0.8em; }
.estado-desconocido  { background:#6b7280; color:white; padding:2px 10px; border-radius:12px; font-size:0.8em; }
</style>
""", unsafe_allow_html=True)

CATEGORIAS = {
    "creacion": "✍️ Crear (escribir + ilustrar)",
    "edicion": "🖨️ Editar / imprimir / distribuir",
    "divulgacion_ciencia": "🔬 Divulgación científica",
    "patrocinio": "🤝 Patrocinio / aval (sin $)",
    "auspicio_privado": "🏭 Auspicio privado (RSE minera)",
    "editorial": "📚 Vía editorial directa",
    "premio_compra": "🏆 Premios y compra estatal",
    "internacional": "🌍 Internacional",
}


# ─── Helpers ─────────────────────────────────────────────────────────────────
def badge_estado(estado: str) -> str:
    m = {"abierto": "🟢 ABIERTO", "proximo": "🟡 PRÓXIMO", "cerrado": "🔴 CERRADO"}
    return m.get(str(estado).lower(), "⚪ S/FECHA")


def formato_monto(row) -> str:
    mn, mx, mon = row.get("monto_min"), row.get("monto_max"), row.get("moneda", "CLP")
    def _num(v):
        try:
            return float(v) if v not in ["", "nan", "None", None] and not pd.isna(v) else None
        except (TypeError, ValueError):
            return None
    mn, mx = _num(mn), _num(mx)
    if not mn and not mx:
        return "según gestión / regalías"
    if mon == "CLP":
        if mn and mx and mn != mx:
            return f"${mn/1e6:.1f}M – ${mx/1e6:.1f}M CLP"
        val = mx or mn
        return f"hasta ${val/1e6:.1f}M CLP" if (mx and not mn) else f"${val/1e6:.1f}M CLP"
    if mn and mx:
        return f"{mn:,.0f} – {mx:,.0f} {mon}"
    return f"{(mx or mn):,.0f} {mon}"


def parse_list(val) -> list:
    if isinstance(val, list):
        return val
    if val in [None, "", "nan", "None", "[]"] or pd.isna(val):
        return []
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return []


@st.cache_data(ttl=1800)
def load_data() -> pd.DataFrame:
    csv_path = Path(__file__).parent / "data" / "fondos_divulgacion.csv"
    if not csv_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df["score_geoninos"] = pd.to_numeric(df.get("score_geoninos", 0), errors="coerce").fillna(0)
    df["internacional"] = pd.to_numeric(df.get("internacional", 0), errors="coerce").fillna(0)
    return df.sort_values("score_geoninos", ascending=False)


def tarjeta(row, mostrar_score=True):
    score = int(row.get("score_geoninos", 0))
    estado = str(row.get("estado", "desconocido")).lower()
    col_main, col_score = st.columns([5, 1]) if mostrar_score else (st.container(), None)
    with col_main:
        st.markdown(
            f"**{row.get('nombre','—')}** "
            f"<span class='estado-{estado}'>{badge_estado(estado)}</span>",
            unsafe_allow_html=True,
        )
        verif = {"si": "✔ verificado", "parcial": "◐ parcial", "no": "⚠ por verificar"}.get(
            str(row.get("verificado", "")), "")
        ventana = str(row.get("ventana", "")).strip()
        st.caption(
            f"🏛 {row.get('organismo','—')}  |  💰 {formato_monto(row)}"
            + (f"  |  📅 {ventana}" if ventana and ventana not in ['nan', 'None'] else "")
            + (f"  |  {verif}" if verif else "")
        )
        desc = str(row.get("descripcion", ""))
        if desc not in ["", "nan", "None"]:
            st.markdown(f"<small>{desc}</small>", unsafe_allow_html=True)
        reqs = parse_list(row.get("requisitos", []))
        if reqs:
            st.caption("📋 " + " · ".join(reqs))
        if str(row.get("url", "")) not in ["", "nan", "None"]:
            st.markdown(f"[🔗 Ver más]({row['url']})")
    if mostrar_score and col_score is not None:
        with col_score:
            color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 40 else "#94a3b8"
            st.markdown(
                f"<div style='text-align:center;padding-top:6px'>"
                f"<span style='color:{color};font-size:1.4em;font-weight:bold'>{score}</span>"
                f"<br><small style='color:#94a3b8'>relevancia</small></div>",
                unsafe_allow_html=True,
            )
            st.progress(score / 100)
    st.divider()


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🪨 Geoniños")
    st.markdown("**Libro infantil de geología de Chile**")
    st.caption("Fondos para crear, editar y publicar")
    st.divider()
    st.subheader("Filtros")
    estado_filter = st.multiselect(
        "Estado", ["abierto", "proximo", "cerrado", "desconocido"],
        default=["abierto", "proximo", "desconocido"],
    )
    cats = st.multiselect(
        "Categoría", list(CATEGORIAS.keys()),
        format_func=lambda k: CATEGORIAS[k], default=[],
    )
    score_min = st.slider("Relevancia mínima", 0, 100, 0)
    st.divider()
    st.caption("Datos: catálogo curado verificado (2026-06-26). "
               "El estado se recalcula automáticamente según la fecha.")


df = load_data()
if df.empty:
    st.warning("Sin datos. Ejecuta `python scan.py` para generar el CSV.")
    st.stop()

filtered = df.copy()
if estado_filter:
    filtered = filtered[filtered["estado"].isin(estado_filter)]
if cats:
    filtered = filtered[filtered["categoria"].isin(cats)]
filtered = filtered[filtered["score_geoninos"] >= score_min]


# ─── Header ───────────────────────────────────────────────────────────────────
st.title("🪨 Fondos para publicar Geoniños")
st.caption("Libro álbum de geología para niñas y niños · Chile · scan automático de convocatorias")

abiertos = df[df["estado"] == "abierto"]
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Total fondos", len(df))
with c2: st.metric("🟢 Abiertos hoy", len(abiertos))
with c3: st.metric("🟡 Próximos", len(df[df["estado"] == "proximo"]))
with c4: st.metric("✍️ Para crear el libro", len(df[df["categoria"] == "creacion"]))

# Alerta de cierres próximos
prox_cierres = abiertos[abiertos["fecha_cierre"].astype(str).str.match(r"\d{4}-\d{2}-\d{2}")]
if not prox_cierres.empty:
    proximos = prox_cierres.sort_values("fecha_cierre").head(3)
    avisos = " · ".join(
        f"**{r['nombre'].split('—')[0].strip()}** cierra {r['fecha_cierre']}"
        for _, r in proximos.iterrows()
    )
    st.warning(f"⏰ Cierres próximos: {avisos}")

st.divider()

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_prio, tab_ruta, tab_cat, tab_tabla = st.tabs([
    "⭐ Por prioridad", "🧭 Ruta recomendada", "🗂️ Por categoría", "📊 Tabla y descarga",
])

with tab_prio:
    st.caption(f"{len(filtered)} fondos · ordenados por relevancia para el libro")
    if filtered.empty:
        st.info("Sin fondos con los filtros actuales.")
    for _, row in filtered.iterrows():
        tarjeta(row)

with tab_ruta:
    st.markdown("""
### 🧭 Ruta recomendada de financiamiento

El financiamiento de un libro infantil en Chile se arma por **etapas**, no con un
solo fondo. El eje es el **Fondo del Libro y la Lectura (MINCAP)** — *no* FONDART.

**Paso 0 — Estar listos para cuando abra (ciclo 2027):**
La Beca de Creación Literaria es **anual**; la convocatoria de ejecución 2026 ya cerró
(jul-2025) y la próxima aún no se publica. Tener lista la muestra para postular apenas
abra. Género Literatura Infantil / Libro Álbum, modalidad Coautoría ($7,5M) con
ilustrador/a. *Registrar Perfil Cultura del autor y del ilustrador cuanto antes.*

**Paso 1 — En paralelo (jul–ago):**
Conseguir **aval/coedición de SERNAGEOMIN** (tu palanca institucional más natural) y
**Patrocinio MINCAP** (gratis). Ambos potencian todo lo demás.

**Paso 2 — Vía editorial con maqueta (ago en adelante):**
Preparar una **dummy** y presentarla a **Amanuta** y **Ekaré Sur**. Con una editorial
comprometida, postular **Apoyo a Ediciones** del Fondo del Libro (imprime + distribuye;
esa línea exige editorial con giro SII).

**Paso 3 — Auspicios complementarios:**
RSE minera por contacto directo, priorizando **CMP** (afinidad hierro-Atacama) y
**FME/BHP**. Sumar **carta del CMN** si el libro se vincula a geositios.

**Descartar:** BID (no viable para autor), UNESCO directo (cerrado hasta 2028-29),
FONDART (no financia libros), Fondo Barros Arana (no es concursable).
    """)
    st.info("Las **dos cartas críticas**: (1) compromiso de una editorial y "
            "(2) aval/coedición de SERNAGEOMIN.")

with tab_cat:
    for cat_key, cat_label in CATEGORIAS.items():
        sub = filtered[filtered["categoria"] == cat_key]
        if sub.empty:
            continue
        with st.expander(f"{cat_label} — {len(sub)} fondos", expanded=cat_key in ["creacion", "edicion"]):
            for _, row in sub.iterrows():
                tarjeta(row, mostrar_score=True)

with tab_tabla:
    st.caption(f"{len(filtered)} fondos · clic en «abrir» para ir a la convocatoria · ordená por cualquier columna")
    cat_corto = {
        "creacion": "✍️ Crear", "edicion": "🖨️ Editar", "divulgacion_ciencia": "🔬 Divulgación",
        "patrocinio": "🤝 Patrocinio", "auspicio_privado": "🏭 Auspicio", "editorial": "📚 Editorial",
        "premio_compra": "🏆 Premio/compra", "internacional": "🌍 Internac.",
    }
    est_emoji = {"abierto": "🟢 abierto", "proximo": "🟡 próximo", "cerrado": "🔴 cerrado", "desconocido": "⚪ s/fecha"}
    ver_emoji = {"si": "✔", "parcial": "◐", "no": "⚠"}
    tabla = pd.DataFrame({
        "Fondo": filtered["nombre"],
        "Categoría": filtered["categoria"].map(lambda c: cat_corto.get(c, c)),
        "Estado": filtered["estado"].map(lambda e: est_emoji.get(str(e).lower(), e)),
        "Monto": filtered.apply(formato_monto, axis=1),
        "Plazo / ventana": filtered.get("ventana", ""),
        "Relev.": pd.to_numeric(filtered["score_geoninos"], errors="coerce").fillna(0),
        "Ver.": filtered["verificado"].map(lambda v: ver_emoji.get(str(v), "")),
        "URL": filtered["url"],
    })
    st.dataframe(
        tabla, use_container_width=True, height=640, hide_index=True,
        column_config={
            "Fondo": st.column_config.TextColumn(width="large"),
            "Categoría": st.column_config.TextColumn(width="small"),
            "Estado": st.column_config.TextColumn(width="small"),
            "Monto": st.column_config.TextColumn(width="small"),
            "Plazo / ventana": st.column_config.TextColumn(width="medium"),
            "Relev.": st.column_config.ProgressColumn("Relev.", min_value=0, max_value=100, format="%d", width="small"),
            "Ver.": st.column_config.TextColumn(width="small", help="✔ verificado · ◐ parcial · ⚠ por verificar"),
            "URL": st.column_config.LinkColumn("Link", display_text="abrir", width="small"),
        },
    )
    st.download_button(
        "⬇️ Descargar CSV", filtered.to_csv(index=False, encoding="utf-8-sig"),
        "fondos_divulgacion.csv", "text/csv",
    )
