#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scanner de fondos — Geoniños (libro infantil de geología)
==========================================================

Genera/actualiza data/fondos_divulgacion.csv a partir de un catálogo curado y
verificado de fondos relevantes para CREAR, EDITAR, IMPRIMIR y DIFUNDIR un libro
infantil de geología en Chile.

El "escaneo constante" real y robusto de este scanner es **recalcular el estado**
(abierto / próximo / cerrado) de cada fondo comparando las fechas de apertura y
cierre con la fecha de hoy. Así el dashboard refleja automáticamente qué
convocatorias siguen vivas sin intervención manual.

Opcionalmente intenta enriquecer el catálogo con una consulta best-effort a la
API CKAN de datos.gob.cl (envuelta en try/except: si no hay red o falla, el
catálogo curado queda como base garantizada).

Uso:
    python scan.py              # regenera el CSV (catálogo + recálculo de estado)
    python scan.py --sin-red    # solo catálogo curado, sin tocar internet

Fuente de los datos curados: 02_fondos/catastro_fondos_libro.md (2026-06-26).
Lo no verificado contra fuente oficial está marcado en 'descripcion'.
"""
from __future__ import annotations

import csv
import io
import json
import sys
from datetime import date, datetime
from pathlib import Path

# En Windows la consola por defecto es cp1252 y rompe con tildes/emoji.
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except (AttributeError, ValueError):
    pass

DATA_DIR = Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "fondos_divulgacion.csv"

# Columnas del CSV (estables — el dashboard depende de estos nombres)
COLUMNS = [
    "id", "fuente", "nombre", "organismo", "categoria", "tipo", "estado",
    "descripcion", "monto_min", "monto_max", "moneda",
    "fecha_apertura", "fecha_cierre", "url", "requisitos",
    "score_geoninos", "internacional", "verificado", "updated_at",
]

# ──────────────────────────────────────────────────────────────────────────────
# CATÁLOGO CURADO Y VERIFICADO
#
# categoria ∈ {creacion, edicion, divulgacion_ciencia, patrocinio,
#              auspicio_privado, editorial, internacional}
# tipo      ∈ {cultural, ciencia, privado, internacional, editorial}
# score_geoninos: relevancia heurística 0–100 para un libro infantil de geología.
# 'estado' aquí es el estado BASE; scan.py lo recalcula con las fechas si existen.
# ──────────────────────────────────────────────────────────────────────────────
CATALOGO: list[dict] = [
    {
        "id": "FL-beca-creacion",
        "nombre": "Beca de Creación Literaria — Fondo del Libro y la Lectura",
        "organismo": "MINCAP (Ministerio de las Culturas)",
        "categoria": "creacion",
        "tipo": "cultural",
        "descripcion": (
            "EJE DEL PROYECTO. Financia finalizar una obra inédita en género "
            "Literatura Infantil / Libro Álbum: cubre escribir + ilustrar. "
            "Unipersonal $5M (sin ilustraciones). Coautoría $7,5M (Libro Álbum y "
            "Lit. Infantil con equipo OBLIGAN ilustraciones; vía natural con un/a "
            "ilustrador/a). Evaluación CIEGA (no pesa trayectoria). "
            "ESTADO (verificado 2026-06-26): la convocatoria de ejecución 2026 "
            "CERRÓ el 31-jul-2025. La línea es anual (abre ~fines de junio, cierra "
            "~fines de julio). La próxima (ejecución 2027) aún NO se publica → "
            "MONITOREAR fondosdecultura.cl. Preparar dummy + Perfil Cultura ahora."
        ),
        "monto_min": 5_000_000, "monto_max": 7_500_000, "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://www.fondosdecultura.cl/fondos/fondo-libro-lectura/lineas-de-concurso/",
        "requisitos": ["obra inédita", "Perfil Cultura del autor e ilustrador",
                       "muestra 8-30 págs (Infantil) / 8-20 (Álbum)",
                       "cartas de compromiso del equipo"],
        "score_geoninos": 98, "internacional": 0, "verificado": "si",
    },
    {
        "id": "FL-apoyo-ediciones",
        "nombre": "Fomento a la Industria — Apoyo a Ediciones (Fondo del Libro)",
        "organismo": "MINCAP (Ministerio de las Culturas)",
        "categoria": "edicion",
        "tipo": "cultural",
        "descripcion": (
            "Financia editar, imprimir, distribuir y difundir la obra. Requisito "
            "decisivo: el postulante debe acreditar giro editorial (Inicio de "
            "Actividades SII) → en la práctica un autor persona natural NO postula "
            "solo: necesita una editorial que presente el proyecto. "
            "ESTADO (verificado 2026-06-26): la convocatoria de ejecución 2026 "
            "CERRÓ el 4-ago-2025. Línea anual → la próxima (ejecución 2027) aún NO "
            "se publica. MONITOREAR. Monto por modalidad [NO VERIFICADO en bases]. "
            "Fondo global $5M–$75M."
        ),
        "monto_min": 5_000_000, "monto_max": 75_000_000, "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://www.fondosdecultura.cl/fondos/fondo-libro-lectura/lineas-de-concurso/",
        "requisitos": ["editorial con giro SII", "carta de cesión del autor",
                       "compromiso de distribución"],
        "score_geoninos": 90, "internacional": 0, "verificado": "parcial",
    },
    {
        "id": "SGM-coedicion",
        "nombre": "SERNAGEOMIN — Coedición / aval institucional (Oficina de Edición)",
        "organismo": "SERNAGEOMIN",
        "categoria": "patrocinio",
        "tipo": "ciencia",
        "descripcion": (
            "No es un fondo: es la palanca institucional más natural por tu "
            "condición de funcionario. La Oficina de Edición ya produjo divulgación "
            "propia (ej. 'Geositios de Chile'). Vía: proponer la obra para coedición "
            "o aval temático. Aporta credibilidad científica y posible "
            "cofinanciamiento. Requiere gestión interna (jefatura + Oficina de "
            "Edición) y revisar propiedad intelectual y uso del nombre institucional."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://www.sernageomin.cl/oficina-de-edicion-y-biblioteca/",
        "requisitos": ["gestión interna jefatura", "revisión de propiedad intelectual",
                       "acuerdo de uso del nombre institucional"],
        "score_geoninos": 88, "internacional": 0, "verificado": "parcial",
    },
    {
        "id": "MINCAP-patrocinio",
        "nombre": "Patrocinio MINCAP (aval institucional, sin dinero)",
        "organismo": "MINCAP (Ministerio de las Culturas)",
        "categoria": "patrocinio",
        "tipo": "cultural",
        "descripcion": (
            "Carta de patrocinio institucional (no entrega dinero) que fortalece "
            "otras postulaciones y auspicios. Se solicita en línea con al menos "
            "30 días hábiles de anticipación al hito. Gratis."
        ),
        "monto_min": 0, "monto_max": 0, "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://patrocinio.cultura.gob.cl/",
        "requisitos": ["solicitud 30 días hábiles antes", "descripción del proyecto"],
        "score_geoninos": 70, "internacional": 0, "verificado": "si",
    },
    {
        "id": "MINCIENCIA-ciencia-publica",
        "nombre": "Concursos Ciencia Pública — Divulgación del Conocimiento",
        "organismo": "Ministerio de Ciencia (MinCiencia)",
        "categoria": "divulgacion_ciencia",
        "tipo": "ciencia",
        "descripcion": (
            "Instrumento público natural para divulgación científica. Líneas "
            "históricas: Productos de Divulgación (hasta ~$20M), Exposiciones y "
            "Espacios Públicos, Conocimiento Local. No se confirmó si financia "
            "libros directamente ni convocatoria 2026 [NO VERIFICADO: confirmar "
            "en cienciapublica.cl]."
        ),
        "monto_min": 1_000_000, "monto_max": 40_000_000, "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://cienciapublica.cl/concursos/",
        "requisitos": ["proyecto de divulgación científica",
                       "persona natural, institución u organización"],
        "score_geoninos": 65, "internacional": 0, "verificado": "no",
    },
    {
        "id": "CMP-fondo-cultura",
        "nombre": "Fondo de Cultura CMP (grupo CAP)",
        "organismo": "Compañía Minera del Pacífico — CMP",
        "categoria": "auspicio_privado",
        "tipo": "privado",
        "descripcion": (
            "Mayor afinidad temática del grupo minero (hierro, desierto de Atacama). "
            "Financia expresión artística y patrimonial de organizaciones cercanas a "
            "sus operaciones (valles de Copiapó, Huasco, Elqui). 'Patrimonial' puede "
            "abarcar patrimonio geológico/minero. [NO VERIFICADO: si financia libros, "
            "montos y estado 2026]. Contacto: comunidadeselqui@cmp.cl."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://www.cmp.cl/",
        "requisitos": ["organización cercana a operaciones CMP",
                       "ángulo patrimonial/cultural"],
        "score_geoninos": 55, "internacional": 0, "verificado": "no",
    },
    {
        "id": "SNPC-fondo-patrimonio",
        "nombre": "Fondo del Patrimonio Cultural",
        "organismo": "Servicio Nacional del Patrimonio Cultural (SNPC)",
        "categoria": "edicion",
        "tipo": "cultural",
        "descripcion": (
            "Financia proyectos de difusión, valoración y educación en patrimonio "
            "cultural; una publicación de divulgación patrimonial-geológica PODRÍA "
            "encajar como producto. Última convocatoria conocida: 2024. "
            "Convocatoria 2026 [NO VERIFICADO]."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://www.sfgp.gob.cl/fondos/fondo-del-patrimonio-cultural",
        "requisitos": ["proyecto de educación/difusión patrimonial"],
        "score_geoninos": 50, "internacional": 0, "verificado": "no",
    },
    {
        "id": "FME-BHP",
        "nombre": "Fundación Minera Escondida (BHP) — donación directa",
        "organismo": "BHP / Fundación Minera Escondida",
        "categoria": "auspicio_privado",
        "tipo": "privado",
        "descripcion": (
            "Músculo grande pero afinidad temática baja (foco educativo digital). "
            "El concurso +Unidos 2026 cerró (1-jun) y es para organizaciones "
            "sociales de Antofagasta, no autores. Vía realista: auspicio/donación "
            "directa (donataria Ley 21.440), todo el año, enmarcando el libro como "
            "educación/cultura regional."
        ),
        "monto_min": "", "monto_max": 5_000_000, "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://fme.cl/contacto/",
        "requisitos": ["contacto directo", "enmarque educación/cultura regional"],
        "score_geoninos": 45, "internacional": 0, "verificado": "parcial",
    },
    {
        "id": "CMN-carta",
        "nombre": "Consejo de Monumentos Nacionales — carta de apoyo / patrocinio",
        "organismo": "Consejo de Monumentos Nacionales (CMN)",
        "categoria": "patrocinio",
        "tipo": "cultural",
        "descripcion": (
            "No administra fondo concursable para publicaciones. Puede otorgar "
            "patrocinio/carta de apoyo a divulgación patrimonial si el libro se "
            "vincula a geositios, Santuarios de la Naturaleza o patrimonio protegido. "
            "Sin procedimiento publicado: solicitud directa "
            "(oficinadepartes@monumentos.gob.cl)."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://www.monumentos.gob.cl/",
        "requisitos": ["vínculo a patrimonio/geositios protegidos", "solicitud directa"],
        "score_geoninos": 42, "internacional": 0, "verificado": "parcial",
    },
    {
        "id": "MLP-pelambres",
        "nombre": "Fundación Minera Los Pelambres (Antofagasta Minerals)",
        "organismo": "Antofagasta Minerals",
        "categoria": "auspicio_privado",
        "tipo": "privado",
        "descripcion": (
            "Línea 'Educación y Patrimonio' hoy centrada en becas. Encaje plausible "
            "solo con anclaje territorial Choapa (Coquimbo). Vía directa. "
            "[NO VERIFICADO fondo para libros]."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://www.fundacionmlp.cl/",
        "requisitos": ["anclaje territorial Choapa", "contacto directo"],
        "score_geoninos": 40, "internacional": 0, "verificado": "no",
    },
    {
        "id": "EXPLORA-PAR",
        "nombre": "Programa Explora — Proyecto Asociativo Regional (PAR)",
        "organismo": "ANID",
        "categoria": "divulgacion_ciencia",
        "tipo": "ciencia",
        "descripcion": (
            "Divulgación CTCI territorial vía PAR adjudicados a instituciones, no a "
            "autores. Un libro podría ser producto de un PAR aliado, no postulación "
            "directa. Montos/plazos 2026 [NO VERIFICADO]."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://www.conicyt.cl/explora/",
        "requisitos": ["alianza con institución ejecutora de un PAR"],
        "score_geoninos": 48, "internacional": 0, "verificado": "no",
    },
    {
        "id": "AGUAS-ANDINAS",
        "nombre": "Fondos Concursables Aguas Andinas",
        "organismo": "Aguas Andinas",
        "categoria": "auspicio_privado",
        "tipo": "privado",
        "descripcion": (
            "Para organizaciones de base de 4 comunas RM (Maipú, Pudahuel, Padre "
            "Hurtado, Tiltil). Aplica solo con vínculo territorial RM + ángulo hídrico "
            "(geología ↔ cuencas), vía organización local. Fechas 2026 [verificar]."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://fondosconcursables.aguasandinas.cl/",
        "requisitos": ["organización de base de 4 comunas RM", "ángulo hídrico"],
        "score_geoninos": 33, "internacional": 0, "verificado": "no",
    },
    {
        "id": "FONDART-regional",
        "nombre": "FONDART Nacional / Regional",
        "organismo": "MINCAP (Ministerio de las Culturas)",
        "categoria": "edicion",
        "tipo": "cultural",
        "descripcion": (
            "RELEVANCIA BAJA. FONDART NO financia la publicación de libros (compete "
            "al Fondo del Libro). Solo tangencial para un proyecto de diseño o de "
            "ilustración como obra visual desligado de la edición. Incluido para "
            "descartar conscientemente."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://www.fondosdecultura.cl/fondos/fondart-nacional/lineas-de-concurso/",
        "requisitos": ["proyecto de artes visuales/diseño (no edición de libro)"],
        "score_geoninos": 18, "internacional": 0, "verificado": "si",
    },
    {
        "id": "UNESCO-participacion",
        "nombre": "UNESCO — Programa de Participación (vía institución)",
        "organismo": "UNESCO (Comisión Nacional Chilena)",
        "categoria": "internacional",
        "tipo": "internacional",
        "descripcion": (
            "No otorga fondos directos a personas naturales. Cofinancia proyectos "
            "presentados por el Estado vía Comisión Nacional. Ciclo 2026-27 YA CERRÓ "
            "(27-feb-2026); próximo ciclo 2028-29. Requiere institución adoptante. "
            "Útil solo como auspicio simbólico."
        ),
        "monto_min": 26_000, "monto_max": 38_000, "moneda": "USD",
        "fecha_apertura": "", "fecha_cierre": "2026-02-27",
        "url": "https://www.unesco.org/en/member-states-portal/participation-programme",
        "requisitos": ["institución adoptante (universidad/museo/SERNAGEOMIN)"],
        "score_geoninos": 25, "internacional": 1, "verificado": "si",
    },
    {
        "id": "BID-lab",
        "nombre": "BID / BID Lab",
        "organismo": "Banco Interamericano de Desarrollo",
        "categoria": "internacional",
        "tipo": "internacional",
        "descripcion": (
            "NO VIABLE para un autor individual. Financia gobiernos, grandes "
            "operaciones y startups tecnológicas escalables. Un libro no califica "
            "salvo desnaturalizándolo como plataforma EdTech. Descartar."
        ),
        "monto_min": "", "monto_max": "", "moneda": "USD",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://bidlab.org/",
        "requisitos": ["gobierno o startup tecnológica escalable"],
        "score_geoninos": 10, "internacional": 1, "verificado": "si",
    },
    # ── Vía editorial directa (no son fondos, son puertas de publicación) ──
    {
        "id": "ED-amanuta",
        "nombre": "Editorial Amanuta — vía editorial directa (maqueta)",
        "organismo": "Amanuta",
        "categoria": "editorial",
        "tipo": "editorial",
        "descripcion": (
            "La candidata más natural: especialista en libro ilustrado infantil; "
            "publican explícitamente no-ficción sobre naturaleza, animales y ciencia. "
            "Modelo tradicional (no cobra al autor; paga regalías/anticipo). Recepción "
            "de manuscritos todo el año, solo digital: publicaciones@amanuta.cl. "
            "Una editorial comprometida habilita además la línea Apoyo a Ediciones."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://amanuta.cl/pages/envio-de-manuscrito",
        "requisitos": ["maqueta/dummy", "envío digital"],
        "score_geoninos": 80, "internacional": 0, "verificado": "si",
    },
    {
        "id": "ED-ekare-sur",
        "nombre": "Ediciones Ekaré Sur — vía editorial directa (maqueta)",
        "organismo": "Ekaré Sur",
        "categoria": "editorial",
        "tipo": "editorial",
        "descripcion": (
            "Álbum ilustrado de prestigio con tradición de informativos sobre "
            "naturaleza y territorio; enfoque narrativo/divulgativo (no técnico). "
            "Modelo tradicional. Contacto: info@ekaresur.cl."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://ekaresur.cl/contacto/",
        "requisitos": ["maqueta/dummy", "enfoque narrativo"],
        "score_geoninos": 75, "internacional": 0, "verificado": "si",
    },
    {
        "id": "ED-pehuen",
        "nombre": "Pehuén Editores — vía editorial directa",
        "organismo": "Pehuén Editores",
        "categoria": "editorial",
        "tipo": "editorial",
        "descripcion": (
            "Histórico, línea infantil con vocación de patrimonio y territorio chileno "
            "(afín a geología nacional). Modelo tradicional. Canal de originales "
            "[NO VERIFICADO]."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://tienda.pehuen.cl/collections/infantil",
        "requisitos": ["maqueta/dummy"],
        "score_geoninos": 55, "internacional": 0, "verificado": "parcial",
    },
    {
        "id": "ED-ril",
        "nombre": "RIL Editores — coedición (institución + editorial)",
        "organismo": "RIL Editores",
        "categoria": "editorial",
        "tipo": "editorial",
        "descripcion": (
            "Fuerte en coediciones académicas/universitarias y obras de valor "
            "patrimonial. Infantil ilustrado no es su foco [NO VERIFICADO]. Útil si se "
            "va por coedición con SERNAGEOMIN. Registrar en Propiedad Intelectual antes; "
            "ediciones@rileditores.com."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://rileditores.com/postular/",
        "requisitos": ["registro Propiedad Intelectual", "modelo coedición"],
        "score_geoninos": 50, "internacional": 0, "verificado": "parcial",
    },
    {
        "id": "ED-sm",
        "nombre": "Ediciones SM Chile — vía editorial directa (plan lector)",
        "organismo": "Ediciones SM",
        "categoria": "editorial",
        "tipo": "editorial",
        "descripcion": (
            "Grupo grande (El Barco de Vapor), fuerte en plan lector escolar; interesa "
            "no-ficción con potencial escolar. Canal formal de originales "
            "[NO VERIFICADO]. chile@grupo-sm.com."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://literaturasm.cl/",
        "requisitos": ["potencial plan lector escolar"],
        "score_geoninos": 50, "internacional": 0, "verificado": "parcial",
    },
]


def recalcular_estado(fondo: dict, hoy: date) -> str:
    """Recalcula el estado de la convocatoria comparando fechas con hoy.

    Esta es la lógica de 'escaneo constante': el dashboard refleja
    automáticamente qué convocatorias siguen abiertas a medida que pasa el tiempo.
    """
    apertura = _parse(fondo.get("fecha_apertura"))
    cierre = _parse(fondo.get("fecha_cierre"))
    if cierre and hoy > cierre:
        return "cerrado"
    if apertura and hoy < apertura:
        return "proximo"
    if apertura or cierre:
        return "abierto"
    return "desconocido"  # sin fechas (vía directa / auspicio permanente)


def _parse(value) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def construir_filas(hoy: date) -> list[dict]:
    filas = []
    stamp = hoy.isoformat()
    for fondo in CATALOGO:
        fila = dict(fondo)
        fila["fuente"] = "catalogo_curado"
        fila["estado"] = recalcular_estado(fondo, hoy)
        fila["requisitos"] = json.dumps(fondo.get("requisitos", []), ensure_ascii=False)
        fila["updated_at"] = stamp
        filas.append({col: fila.get(col, "") for col in COLUMNS})
    return filas


def augmentar_datos_gob(filas: list[dict]) -> list[dict]:
    """Best-effort: consulta la API CKAN de datos.gob.cl por señales de fondos.

    Si no hay red o la API cambia, NO rompe: el catálogo curado queda como base.
    """
    try:
        import urllib.request

        url = ("https://datos.gob.cl/api/3/action/package_search"
               "?q=fondo+libro+lectura+divulgaci%C3%B3n&rows=5")
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        results = data.get("result", {}).get("results", [])
        print(f"[datos.gob.cl] {len(results)} datasets encontrados (señal, no se "
              f"agregan como fondos automáticamente).")
    except Exception as exc:  # noqa: BLE001 — best-effort, nunca debe romper el scan
        print(f"[datos.gob.cl] omitido ({exc.__class__.__name__}). "
              f"Catálogo curado intacto.")
    return filas


def escribir_csv(filas: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    filas_ordenadas = sorted(filas, key=lambda f: f["score_geoninos"], reverse=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(filas_ordenadas)
    abiertos = sum(1 for f in filas if f["estado"] == "abierto")
    print(f"✅ {len(filas)} fondos escritos en {CSV_PATH.name} "
          f"({abiertos} abiertos hoy).")


def main() -> None:
    sin_red = "--sin-red" in sys.argv
    hoy = date.today()
    print(f"Scanner Geoniños — fecha de referencia: {hoy.isoformat()}")
    filas = construir_filas(hoy)
    if not sin_red:
        filas = augmentar_datos_gob(filas)
    escribir_csv(filas)


if __name__ == "__main__":
    main()
