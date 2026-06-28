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
    "id", "fuente", "nombre", "organismo", "categoria", "tipo", "estado", "ventana",
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
            "HALLAZGO CLAVE (verificado 2026-06-27): la línea 'Productos de "
            "Divulgación del Conocimiento' financia explícitamente LIBROS de "
            "divulgación, hasta $25M, y admite PERSONA NATURAL (sin necesidad de "
            "editorial). Única condición fuerte: distribución gratuita (ideal para "
            "tiraje a escuelas/bibliotecas). Complementa al Fondo del Libro (que sí "
            "permite venta). Es ANUAL (abre ~mediados de año). Estado del ciclo "
            "vigente [VERIFICAR fechas en fondos.gob.cl]."
        ),
        "monto_min": 1_000_000, "monto_max": 25_000_000, "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://cienciapublica.cl/concursos/",
        "requisitos": ["persona natural elegible (sin editorial)",
                       "proyecto de divulgación científica",
                       "distribución gratuita obligatoria"],
        "score_geoninos": 80, "internacional": 0, "verificado": "parcial",
    },
    {
        "id": "SM-barco-de-vapor",
        "nombre": "Premio El Barco de Vapor — Fundación SM",
        "organismo": "Fundación SM",
        "categoria": "internacional",
        "tipo": "editorial",
        "descripcion": (
            "Premio a un original INÉDITO de literatura infantil/juvenil: funciona "
            "como financiamiento + publicación de la obra ganadora (35.000 € brutos). "
            "Es literario → el manuscrito debe tener cuerpo narrativo (encaja con "
            "'Pewma y la piedrita viajera'). Anual; bases 2026 publicadas. La vía "
            "internacional más concreta con dinero real."
        ),
        "monto_min": "", "monto_max": "", "moneda": "EUR",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://es.literaturasm.com/premios-sm",
        "requisitos": ["obra original inédita", "cuerpo narrativo (no solo informativo)"],
        "score_geoninos": 60, "internacional": 1, "verificado": "si",
    },
    {
        "id": "fundacion-la-fuente",
        "nombre": "Fundación La Fuente — patrocinio LIJ",
        "organismo": "Fundación La Fuente",
        "categoria": "auspicio_privado",
        "tipo": "privado",
        "descripcion": (
            "Fomento de la lectura. Ofrece patrocinio para proyectos de tiraje corto "
            "de literatura infantil/juvenil vía Ley de Donaciones Culturales, y opera "
            "Viva Leer Copec. Modelo: patrocinio/canal de distribución, no premio en "
            "efectivo. Bases y calendario [VERIFICAR — recurrente]. Consulta directa."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://www.fundacionlafuente.cl/",
        "requisitos": ["consulta directa", "proyecto de tiraje corto LIJ"],
        "score_geoninos": 58, "internacional": 0, "verificado": "no",
    },
    {
        "id": "fundacion-collahuasi",
        "nombre": "Fundación Educacional Collahuasi — coedición/auspicio",
        "organismo": "Fundación Educacional Collahuasi (minera)",
        "categoria": "auspicio_privado",
        "tipo": "privado",
        "descripcion": (
            "Ya editó un libro infantil de tradición oral de Tarapacá → la mayor "
            "afinidad editorial del grupo minero. No hay concurso abierto a autores "
            "con bases públicas; opera por programas propios/alianzas. Vía: contacto "
            "directo para coedición/auspicio. [NO VERIFICADO montos/plazos]."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://fundacioncollahuasi.cl/",
        "requisitos": ["contacto directo", "anclaje regional Tarapacá ayuda"],
        "score_geoninos": 47, "internacional": 0, "verificado": "no",
    },
    {
        "id": "SNBP-adquisicion",
        "nombre": "Programa de Adquisición de Libros de Autores Chilenos (SNBP)",
        "organismo": "MINCAP / Consejo Nacional del Libro (SNBP)",
        "categoria": "premio_compra",
        "tipo": "cultural",
        "descripcion": (
            "CANAL DE VENTA AL ESTADO: compra ~300 ejemplares del título seleccionado "
            "para bibliotecas públicas. EL AUTOR SÍ POSTULA (a diferencia de CRA). "
            "Requisitos: 1ª edición del año anterior, ISBN, depósito legal, 3 ejemplares. "
            "Criterios: contenidos 45% + pertinencia 20% (= 65%, donde pega geología-de-Chile). "
            "Anual (2024 abrió 9-sep, cerró 10-oct; presupuesto $620M). Convocatoria 2026 "
            "[VERIFICAR en fondosdecultura.cl]. Requiere libro ya publicado."
        ),
        "monto_min": "", "monto_max": "", "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://www.fondos.gob.cl/ficha/mincap/programa-adquisicion-libros/",
        "requisitos": ["1ª edición del año anterior", "ISBN + depósito legal",
                       "3 ejemplares físicos", "postula el autor"],
        "score_geoninos": 85, "internacional": 0, "verificado": "parcial",
    },
    {
        "id": "premio-marta-brunet",
        "nombre": "Premio Marta Brunet — Primera infancia (Premios Literarios MINCAP)",
        "organismo": "MINCAP / Fondo del Libro",
        "categoria": "premio_compra",
        "tipo": "cultural",
        "descripcion": (
            "Premio a obra YA PUBLICADA (meta postpublicación). Categoría Primera "
            "infancia (0-6). $4.330.000 + el Ministerio COMPRA el 20% de la 1ª edición "
            "del ganador (tope 100 ej.) para bibliotecas → prestigio + dinero + venta. "
            "Exige 1ª edición reciente: conviene sincronizar el lanzamiento. "
            "Convocatoria 2026 [VERIFICAR]."
        ),
        "monto_min": 4_330_000, "monto_max": 4_330_000, "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://premiosliterarios.cultura.gob.cl/marta-brunet/",
        "requisitos": ["obra publicada (1ª edición reciente)", "categoría primera infancia"],
        "score_geoninos": 72, "internacional": 0, "verificado": "si",
    },
    {
        "id": "premio-colibri",
        "nombre": "Medalla Colibrí — No ficción infantil (IBBY Chile)",
        "organismo": "IBBY Chile",
        "categoria": "premio_compra",
        "tipo": "cultural",
        "descripcion": (
            "Premio a obra YA PUBLICADA (meta postpublicación). Categoría 'No ficción "
            "infantil'. Sin dinero, pero es la MÁXIMA legitimación ante evaluadores CRA "
            "y bibliotecarios → impulsa la compra institucional. Postula la sección "
            "nacional / editorial, no el autor directo."
        ),
        "monto_min": 0, "monto_max": 0, "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://www.ibbychile.cl/premios/medalla-colibri/",
        "requisitos": ["obra publicada", "categoría no ficción infantil"],
        "score_geoninos": 50, "internacional": 0, "verificado": "si",
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
        "id": "FPA-mma",
        "nombre": "Fondo de Protección Ambiental (FPA) — MMA",
        "organismo": "Ministerio del Medio Ambiente",
        "categoria": "divulgacion_ciencia",
        "tipo": "cultural",
        "descripcion": (
            "Rescatado del catálogo del scanner OVDAS. Financia educación ambiental "
            "(líneas Establecimientos Educacionales, Pueblos Indígenas, Proyectos "
            "Sustentables), hasta ~$21M. NO financia el libro en sí, pero un proyecto "
            "de educación ambiental con base geológica (suelo, agua, geopatrimonio, "
            "cuidado del entorno) + distribución a escuelas puede entrar VÍA un colegio "
            "u organización con personalidad jurídica. [VERIFICAR convocatoria]."
        ),
        "monto_min": 1_000_000, "monto_max": 21_000_000, "moneda": "CLP",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://fondos.mma.gob.cl/fpa/",
        "requisitos": ["organización/colegio con personalidad jurídica",
                       "eje ambiental", "vía indirecta (no el autor solo)"],
        "score_geoninos": 40, "internacional": 0, "verificado": "parcial",
    },
    {
        "id": "natgeo-explorer",
        "nombre": "National Geographic — Explorer Grant (Level I)",
        "organismo": "National Geographic Society",
        "categoria": "internacional",
        "tipo": "internacional",
        "descripcion": (
            "Rescatado del catálogo del scanner OVDAS. Grant para profesionales "
            "emergentes en ciencias de la Tierra con VOLUNTAD DE DIFUSIÓN PÚBLICA "
            "(USD 5.000–20.000). Podría financiar la investigación/exploración y la "
            "divulgación detrás del libro (no la edición comercial). El autor geólogo "
            "califica por perfil. Postulación en inglés."
        ),
        "monto_min": 5_000, "monto_max": 20_000, "moneda": "USD",
        "fecha_apertura": "", "fecha_cierre": "",
        "url": "https://www.nationalgeographic.org/society/grants-and-investments/",
        "requisitos": ["ciencias de la Tierra", "voluntad de difusión pública",
                       "postulación en inglés"],
        "score_geoninos": 38, "internacional": 1, "verificado": "parcial",
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

# ──────────────────────────────────────────────────────────────────────────────
# VENTANAS ANUALES — fondos sin fecha publicada pero que abren ~el mismo mes cada
# año. El scanner avisa cuando entramos en la ventana estimada, para no perder la
# convocatoria (riesgo real del proyecto: la Beca y Ciencia Pública son anuales).
# Valor: (meses_estimados_de_apertura, etiqueta).
# ──────────────────────────────────────────────────────────────────────────────
VENTANAS_ANUALES: dict[str, tuple[set, str]] = {
    "FL-beca-creacion": ({6, 7}, "abre ~fines de junio, cierra ~fines de julio"),
    "FL-apoyo-ediciones": ({6, 7, 8}, "abre ~fines de junio, cierra ~inicios de agosto"),
    "MINCIENCIA-ciencia-publica": ({5, 6, 7}, "suele abrir mayo–junio"),
    "SNBP-adquisicion": ({9, 10}, "suele abrir sep–oct"),
}


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


def _ventana_texto(fondo: dict, estado: str) -> str:
    """Texto de plazo/ventana para mostrar en la tabla y las tarjetas, también
    cuando el fondo no tiene fecha fija (anuales sin convocatoria publicada)."""
    cierre = fondo.get("fecha_cierre")
    if cierre:
        return ("cerró " if estado == "cerrado" else "cierra ") + str(cierre)
    if fondo.get("id") in VENTANAS_ANUALES:
        return "anual: " + VENTANAS_ANUALES[fondo["id"]][1]
    return "sin fecha fija / contacto directo"


def construir_filas(hoy: date) -> list[dict]:
    filas = []
    stamp = hoy.isoformat()
    for fondo in CATALOGO:
        fila = dict(fondo)
        fila["fuente"] = "catalogo_curado"
        fila["estado"] = recalcular_estado(fondo, hoy)
        fila["ventana"] = _ventana_texto(fondo, fila["estado"])
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


def leer_estados_previos() -> dict[str, str]:
    """Lee el CSV anterior (antes de sobrescribirlo) para detectar cambios."""
    if not CSV_PATH.exists():
        return {}
    out: dict[str, str] = {}
    try:
        with CSV_PATH.open(encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                out[row.get("id", "")] = row.get("estado", "")
    except OSError:
        pass
    return out


def detectar_alertas(filas: list[dict], previos: dict[str, str], hoy: date) -> list[str]:
    """Genera alertas: (1) fondos que ACABAN de abrir; (2) fondos anuales que
    entran en su ventana estimada de apertura este mes."""
    alertas: list[str] = []
    by_id = {f["id"]: f for f in filas}
    for f in filas:
        prev = previos.get(f["id"])
        if f["estado"] == "abierto" and prev != "abierto":
            etq = "NUEVO y ABIERTO" if prev is None else "ACABA DE ABRIR"
            cierre = f.get("fecha_cierre") or "s/fecha"
            alertas.append(f"🟢 {etq}: {f['nombre']} — cierre {cierre} | {f.get('url','')}")
    for fid, (meses, etq) in VENTANAS_ANUALES.items():
        f = by_id.get(fid)
        if f and hoy.month in meses and f["estado"] in ("desconocido", "proximo"):
            alertas.append(f"🟡 VENTANA ESTIMADA ({etq}): {f['nombre']} — "
                           f"revisar si ya abrió: {f.get('url','')}")
    return alertas


def enviar_telegram(mensaje: str) -> bool:
    """Envía alerta por Telegram si hay credenciales en variables de entorno
    (TELEGRAM_TOKEN_GEONINOS / TELEGRAM_CHAT_ID_GEONINOS). Opcional: si no están,
    no hace nada."""
    import os
    import urllib.parse
    import urllib.request

    token = os.environ.get("TELEGRAM_TOKEN_GEONINOS")
    chat = os.environ.get("TELEGRAM_CHAT_ID_GEONINOS")
    if not token or not chat:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode(
            {"chat_id": chat, "text": mensaje, "disable_web_page_preview": "true"}
        ).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=20)
        return True
    except Exception as exc:  # noqa: BLE001 — opcional, nunca debe romper el scan
        print(f"[telegram] no se pudo enviar ({exc.__class__.__name__}).")
        return False


def emitir_alertas(alertas: list[str], hoy: date) -> None:
    """Imprime alertas, las guarda en data/ultimo_scan.md y, si hay credenciales,
    las manda por Telegram."""
    lineas = [f"# Último escaneo — {hoy.isoformat()}", ""]
    if alertas:
        print("\n".join(["", "=== ALERTAS ==="] + alertas))
        lineas.append("## Alertas")
        lineas += [f"- {a}" for a in alertas]
        if enviar_telegram("Geoniños — fondos:\n" + "\n".join(alertas)):
            print("[telegram] alerta enviada.")
    else:
        print("Sin alertas en este escaneo.")
        lineas.append("Sin novedades: ninguna convocatoria abrió ni entró en ventana estimada.")
    (DATA_DIR / "ultimo_scan.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")


def main() -> None:
    sin_red = "--sin-red" in sys.argv
    hoy = date.today()
    print(f"Scanner Geoniños — fecha de referencia: {hoy.isoformat()}")
    estados_previos = leer_estados_previos()   # antes de sobrescribir el CSV
    filas = construir_filas(hoy)
    if not sin_red:
        filas = augmentar_datos_gob(filas)
    escribir_csv(filas)
    alertas = detectar_alertas(filas, estados_previos, hoy)
    emitir_alertas(alertas, hoy)


if __name__ == "__main__":
    main()
