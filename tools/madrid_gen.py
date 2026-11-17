#!/usr/bin/env python3
"""Genera data/madrid.json (rutas de Madrid) a partir de tools/madrid_rutas.tsv.

El TSV es una copia de la hoja de Drive «Rutes Madrid» (una fila por ruta; la hoja es la
fuente de verdad). Ús:  python3 tools/madrid_gen.py
Los mids de My Maps son los de los 19 mapas «Rutas de Esperanza Activa - Madrid · {zona}».
No se inventa ningún dato: la dirección sale solo si la hoja la da y no está marcada
como dudosa; los tiempos no están en la hoja y no se ponen.
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# clave -> (zona, distrito del desplegable, mid)
MAPS = {
    "ARG": ("Arganzuela", "Arganzuela", "1yrNrrX8uj81QOvLGIX0oUCfUjhsbgWY"),
    "CAR": ("Carabanchel", "Carabanchel", "1FIUsWU9bzFHw_M9DN2qhMB20IfuT9Q0"),
    "CEN": ("Centro", "Centro", "1AKRbPRFHtnDr7fOxQ_BpUwlxZ9RsWh4"),
    "CHM": ("Chamartín", "Chamartín", "1qERg5cXECiQyG8GGknezqFca2sIiBxY"),
    "CHB": ("Chamberí", "Chamberí", "1eIokyAl1ubTmkSp8cRPUEWZTqStGEms"),
    "CLI": ("Ciudad Lineal", "Ciudad Lineal", "18XXUQtQtdjBO_hj4RakS9ntaYIU_FSw"),
    "FUE": ("Fuencarral-El Pardo", "Fuencarral-El Pardo", "1ZpPKZptFuA2flSDURrseoFvxFOPwvl4"),
    "HOR": ("Hortaleza", "Hortaleza", "1LBb3lX3SVyZhX4emHY-0RV8CFqnbHkE"),
    "LAT": ("Latina", "Latina", "147FFwnfvP4YfbQZqvd2b_U6oMn0ioEk"),
    "MON": ("Moncloa-Aravaca", "Moncloa-Aravaca", "1dsqt4L3Lt7GJmxDVo0aeeyafW0fdQ1c"),
    "MVB": ("Moratalaz, Vicálvaro y Barajas", "Moratalaz, Vicálvaro y Barajas", "1CYN6l45sl_e0156_L35BIr3GmOOHZJ4"),
    "RET": ("Retiro", "Retiro", "11KvqxZp6XKzb-OdCqWUs9H59GLPahLU"),
    "SAL": ("Salamanca", "Salamanca", "1d0abPSjoTfJi8NYfi45UUiW0X8_FbYQ"),
    "SBC": ("San Blas-Canillejas", "San Blas-Canillejas", "1GSTlbVkAnqPqTitvlTEwKYdpzc92zEQ"),
    "TET": ("Tetuán", "Tetuán", "1qn_3AOcqSRNrz7HPXAmnH6lkmtjHIC4"),
    "USE": ("Usera", "Usera", "1031PFXOvro-mkhWTe4RwpOvbdjOI-0A"),
    "V1": ("Vallecas (1)", "Vallecas", "1tlXWB-hcZdUiUYYxa-pXMXXP1K6Ivu4"),
    "V2": ("Vallecas (2)", "Vallecas", "15e6CqGRl3QoOjLB6Cc0XbrsmewKV4OQ"),
    "VIL": ("Villaverde", "Villaverde", "19tGaLDRdRjPGbh0QX7eH-9IGgpMdzts"),
}
assert len(MAPS) == 19

# Vista inicial del mapa incrustado (centro aproximado del distrito y zoom). La hoja no tiene
# coordenadas: sin ll/z, My Maps abre el mapa con toda España a la vista.
VIEW = {
    "ARG": ("40.3975,-3.6955", 13), "CAR": ("40.3780,-3.7370", 13), "CEN": ("40.4150,-3.7060", 14),
    "CHM": ("40.4620,-3.6770", 13), "CHB": ("40.4350,-3.7040", 14), "CLI": ("40.4500,-3.6500", 13),
    "FUE": ("40.4950,-3.7100", 12), "HOR": ("40.4720,-3.6400", 13), "LAT": ("40.3900,-3.7500", 13),
    "MON": ("40.4400,-3.7500", 12), "MVB": ("40.4300,-3.6100", 12), "RET": ("40.4090,-3.6750", 14),
    "SAL": ("40.4310,-3.6770", 14), "SBC": ("40.4350,-3.6150", 13), "TET": ("40.4600,-3.7030", 13),
    "USE": ("40.3830,-3.7050", 13), "V1": ("40.3800,-3.6200", 13), "V2": ("40.3900,-3.6550", 13),
    "VIL": ("40.3500,-3.7050", 13),
}
assert set(VIEW) == set(MAPS)


def slug(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def km_fmt(k):
    return f"{float(k.replace(',', '.')):.2f}".replace(".", ",")


def walk(k):
    """Tiempo aproximado caminando: 12-15 min por km."""
    km = float(k.replace(",", "."))
    return f"{round(km * 12)}–{round(km * 15)} min caminando"


rows = list(csv.DictReader((ROOT / "tools" / "madrid_rutas.tsv").open(encoding="utf-8"), delimiter="\t"))
assert [int(r["n"]) for r in rows] == list(range(1, 129)), "faltan o sobran rutas"
wl = [int(r["wikiloc"]) for r in rows]
assert wl == sorted(wl) and len(set(wl)) == 128, "los ids de Wikiloc deberían ir en orden creciente"

groups = {}
for r in rows:
    zona, district, mid = MAPS[r["mapa"]]
    g = groups.setdefault(r["mapa"], {"id": slug(zona), "title": zona, "district": district, "routes": []})
    route = {
        "n": int(r["n"]),
        "name": f"Centro de Salud {r['centro']}",
        "start": f"Distrito de {r['distrito']}",
        "info": f"{km_fmt(r['km'])} km · circular · {walk(r['km'])}",
        "wikiloc": f"https://www.wikiloc.com/wikiloc/view.do?id={r['wikiloc']}",
    }
    if r["direccion"]:
        route["address"] = f"{r['direccion']}, Madrid"
    if r["n"] == "28":
        route["note"] = ("Desde el 2/3/2026, el centro de salud Castelló está en la 5.ª planta del Centro de Salud Goya "
                         "(calle de O'Donnell 55). La ruta sale de ese edificio.")
    g["routes"].append(route)

order = sorted(groups, key=lambda k: slug(MAPS[k][0]))
kms = [float(r["km"].replace(",", ".")) for r in rows]
lo, hi = min(kms), max(kms)
fmt = lambda x: (f"{x:.1f}".replace(".", ",")).replace(",0", "")

out_groups = []
for k in order:
    zona, district, mid = MAPS[k]
    g = groups[k]
    n = len(g["routes"])
    g["maps"] = [{
        "mid": mid,
        "ll": VIEW[k][0],
        "z": VIEW[k][1],
        "title": f"Rutas de Esperanza Activa - Madrid · {zona}",
        "label": f"{zona} · {n} {'ruta' if n == 1 else 'rutas'}",
    }]
    out_groups.append({"id": g["id"], "title": g["title"], "district": g["district"], "maps": g["maps"], "routes": g["routes"]})

centros = sorted(rows, key=lambda r: slug(r["centro"]))
options = []
for r in centros:
    g = groups[r["mapa"]]
    options.append([f"Centro de Salud {r['centro']} · {r['distrito']}", f"{g['id']}-ruta-{int(r['n'])}"])

city = {
    "slug": "madrid",
    "name": "Madrid",
    "region": "Comunidad de Madrid",
    "summary": "128 rutas circulares y cortas, una desde cada centro de salud de la ciudad, organizadas por distrito.",
    "intro": "Paseos urbanos para hacer el tiempo de reflexión de cada paso. Elige tu distrito o busca el centro de salud que te quede más cerca de casa, abre el mapa y camina.",
    "zones": {"label": "Ve directamente a tu distrito", "placeholder": "Elige un distrito", "back": "Cambia de distrito"},
    "blocks": [{
        "course": "vida",
        "text": (f"128 rutas circulares de {fmt(lo)} a {fmt(hi)} km, una desde cada centro de salud de Madrid. "
                 "El centro de salud es solo el punto de referencia del recorrido. "
                 "Elige tu distrito o busca el centro más cercano a tu casa y camina."),
        "summary": "128 rutas, una desde cada centro de salud",
        "parts": [
            {   # buscador por centro de salud (desplegable que lleva a la ruta)
                "zones": {"id": "madrid-centros", "label": "Busca tu centro de salud",
                          "placeholder": "Elige un centro de salud", "options": options},
                "groups": [],
            },
            {
                "id": "rutas-por-distrito",
                "title": "Rutas por distrito",
                "zones": {"by": "district"},
                "notice": {
                    "title": "Accesibilidad y seguridad",
                    "html": [
                        "Es un paseo urbano: respeta los semáforos y los pasos de peatones.",
                        "Los tiempos son aproximados, caminando a un ritmo tranquilo (entre 12 y 15 minutos por kilómetro) y sin contar las pausas.",
                        "El centro de salud es solo el punto de referencia del recorrido: no organiza ni recomienda esta actividad. "
                        "Más información en <a href=\"https://elarasocial.com/es/\" target=\"_blank\" rel=\"noopener\">elarasocial.com</a>.",
                    ],
                },
                "groups": out_groups,
            },
        ],
    }],
}


# ---------------------------------------------------------------------------------------------
# Otros tres cursos (17/11/2026): centros culturales y bibliotecas (cuidar), parques y jardines (mon)
# y entidades de economía social (dia). Datos: tools/madrid_cuidar.tsv, madrid_mon.tsv, madrid_dia.tsv y
# madrid_dia_desc.tsv (copias de las hojas de Drive; las hojas son la fuente de verdad).
# Sin tiempos «con pausas»; observaciones internas de las hojas, sin publicar.
# ---------------------------------------------------------------------------------------------
def tsv(name):
    return list(csv.DictReader((ROOT / "tools" / name).open(encoding="utf-8"), delimiter="\t"))


def route_common(r, name, start=None, addr_city="Madrid"):
    d = {
        "n": int(r["n"]),
        "name": name,
        "info": f"{km_fmt(r['km'])} km · circular · {walk(r['km'])}",
        "wikiloc": f"https://www.wikiloc.com/wikiloc/view.do?id={r['wikiloc']}",
    }
    if start:
        d["start"] = start
    if r["direccion"].strip():
        d["address"] = f"{r['direccion'].strip()}, {addr_city}"
    return d


# (primer n, último n, id, título, mid, ll, z)
MAPS_CUIDAR = [
    (401, 406, "arganzuela-barajas", "Arganzuela-Barajas", "1zLh8PaJ7ty8gi0sZwjUrYmxiRGWJ0M0", "40.4300,-3.6400", 12),
    (407, 415, "carabanchel", "Carabanchel", "1nYWwd6Pd7dDF2Hkmuv-jlbsSveU6_pk", "40.3780,-3.7370", 13),
    (416, 422, "centro", "Centro", "1w-y-XtHL7J2vrsStsom3xEbodkFzxkc", "40.4150,-3.7060", 14),
    (423, 429, "chamartin-chamberi", "Chamartín-Chamberí", "1VB4Ro05GaL_n7G3XULtQDyom6dRh-wQ", "40.4500,-3.6900", 13),
    (430, 435, "ciudad-lineal", "Ciudad Lineal", "1H72qOL1unRe1Uv5kqjwZ41LpDVxtCFM", "40.4500,-3.6500", 13),
    (436, 444, "fuencarral-el-pardo", "Fuencarral-El Pardo", "1MRfZXB8-da_tJ9ruxFj9LB3rd6VY7h0", "40.5000,-3.7100", 12),
    (445, 452, "hortaleza", "Hortaleza", "1t5-noS4d02la0KY61-byQqsgPwEyn58", "40.4720,-3.6400", 13),
    (453, 458, "latina-1", "Latina (1/2)", "1QtqgkAaaZ8TJgBD7xDgownmFc4Wz1ow", "40.3900,-3.7500", 13),
    (459, 463, "latina-2", "Latina (2/2)", "1ccJiufW_gTV-Cc5yTj_t6Id0qjhZLTE", "40.3900,-3.7600", 13),
    (464, 473, "moncloa-aravaca-moratalaz", "Moncloa-Aravaca-Moratalaz", "1AyEk0j5ZqmuUDK32EHFar5ighzPoRcg", "40.4350,-3.7000", 12),
    (474, 482, "puente-de-vallecas", "Puente de Vallecas", "1U-9xEOrs1MktUw4PlmC85YBNgKf7AQo", "40.3850,-3.6600", 13),
    (483, 492, "retiro-salamanca", "Retiro-Salamanca", "1YEi87JSBrt6YH200PuUx07SBQzgM56s", "40.4200,-3.6750", 14),
    (493, 499, "san-blas-canillejas", "San Blas-Canillejas", "18j8M85D9reOBDtPvi-nY7CK3gehK2aI", "40.4350,-3.6150", 13),
    (500, 509, "tetuan-usera-1", "Tetuán-Usera (1/2)", "1CpA4G1TMV4tWDOTfXTCMi_qr8VFMCnE", "40.4200,-3.7000", 12),
    (510, 516, "usera-vicalvaro-2", "Usera-Vicálvaro (2/2)", "1sZ4yqRwALXIpN7v6SBFgK986SNDpeCM", "40.4000,-3.6200", 12),
    (517, 526, "villa-de-vallecas-villaverde-1", "Villa de Vallecas-Villaverde (1/2)", "1FEWsbE3lnOQ7XWAzfo4U2W_vCDrfpnM", "40.3600,-3.6500", 12),
    (527, 529, "villaverde-2", "Villaverde (2/2)", "1I0jnJQdhmEaSAy0u7pHPvGXb0Tr1Jew", "40.3500,-3.7050", 13),
]
MAPS_MON = [
    (600, 609, "centro-arganzuela", "Centro-Arganzuela", "1Of8V3cOtlXz02UsLcRXOW9mhx_L9kMg", "40.4050,-3.7000", 13),
    (610, 619, "retiro-salamanca", "Retiro-Salamanca", "1T5F6ZHOomnwvIKNp-zW9DMpSD7FhBzo", "40.4200,-3.6750", 14),
    (620, 627, "chamartin-tetuan", "Chamartín-Tetuán", "1CXqJXXVfaQQIWuuRo-sYatHX3PER-bA", "40.4600,-3.6900", 13),
    (629, 637, "chamberi-fuencarral-el-pardo", "Chamberí-Fuencarral-El Pardo", "1bUjTZDpWMjUejF8VbeX9hKs2TtQKUjQ", "40.4600,-3.7000", 12),
    (638, 646, "moncloa-aravaca-latina", "Moncloa-Aravaca-Latina", "1uzPjj4NYjCRAmkaUL6ve8l8Vm8MWRho", "40.4200,-3.7500", 12),
    (647, 656, "carabanchel-usera", "Carabanchel-Usera", "1OZk59gXGSFDu79OEpo_cFHwJN1xe9L8", "40.3800,-3.7200", 13),
    (657, 666, "puente-de-vallecas-moratalaz", "Puente de Vallecas-Moratalaz", "1wcPxh6LmrreKN0o-XtjKmWdvvR826Y4", "40.4000,-3.6400", 13),
    (667, 674, "ciudad-lineal-hortaleza", "Ciudad Lineal-Hortaleza", "1Bx05a9XhLS1F7hW1srUR79jiYJX1GwE", "40.4600,-3.6500", 13),
    (675, 684, "villaverde-villa-de-vallecas", "Villaverde-Villa de Vallecas", "1VhZoT1AtIxdNQkG26DkbwHuRIHikMwI", "40.3600,-3.6600", 12),
    (685, 694, "vicalvaro-san-blas-canillejas-barajas", "Vicálvaro-San Blas-Canillejas-Barajas", "1A0ZU2Zi_QcVdmsHQfl1NJX8JFx86jv0", "40.4400,-3.6000", 12),
]
MAPS_DIA = [
    (201, 210, "centro-1", "Centro (1/4)", "1lsskGCdQlOSEpejCyZ1h1VQw8umX5Iw", "40.4150,-3.7050", 15),
    (211, 220, "centro-2", "Centro (2/4)", "1z4uVNdZ39b01xDXgnJC_gwOQVzbjHc8", "40.4150,-3.7050", 15),
    (221, 230, "centro-3", "Centro (3/4)", "1aAbkci945Wv-coIK1iehLdPNs4O8U6Q", "40.4150,-3.7050", 15),
    (231, 240, "centro-4", "Centro (4/4)", "1NUomTE6reLOUXeBgttBGMkJM8rDiAS0", "40.4150,-3.7050", 15),
    (241, 248, "arganzuela-1", "Arganzuela (1/3)", "1IxoAPVEyro0iR2Uj0sUNvFP1_aQOqZ8", "40.3950,-3.6950", 14),
    (249, 256, "arganzuela-2", "Arganzuela (2/3)", "1SfmrmIOUEewgLFxaN5dCYS8SI4wCZl0", "40.3950,-3.6950", 14),
    (257, 263, "arganzuela-3", "Arganzuela (3/3)", "1GZdRWuQNyIiqr_AVM-MxziEsQWstzCQ", "40.3950,-3.6950", 14),
    (264, 269, "vallecas-usera-villaverde-1", "Vallecas-Usera-Villaverde (1/2)", "1QwxbnQ4s_Y8CPvkAl2hZIvQQNR9vNnk", "40.3700,-3.6800", 12),
    (270, 275, "vallecas-usera-villaverde-2", "Vallecas-Usera-Villaverde (2/2)", "1Sxk1FeZo55C2LxDUCJ36y06L95A9ixM", "40.3700,-3.6800", 12),
    (276, 284, "chamberi-moncloa", "Chamberí-Moncloa", "1NLG9b7EoxEhIX2p9e_Iu6LTEGRLyhi8", "40.4350,-3.7100", 13),
    (285, 292, "tetuan-fuencarral", "Tetuán-Fuencarral", "1yXleH6YHqDpnpM81EdAUlXxBjFTyMQo", "40.4700,-3.7000", 12),
    (293, 299, "carabanchel-latina", "Carabanchel-Latina", "1jxlHOwJYy6YGCUcHwXNuHkVVmx-mP7s", "40.3900,-3.7400", 13),
    (300, 309, "retiro-salamanca-moratalaz-hortaleza-ciudad-lineal", "Retiro-Salamanca-Moratalaz-Hortaleza-Ciudad Lineal", "1sH9zk_UsuPGYh1MzS8evqS6GADyQdnM", "40.4400,-3.6600", 12),
    (310, 318, "comunidad-de-madrid", "Comunidad de Madrid", "1GvvhZYzMPCJC6zSVnyNAJATjtPbEvDk", "40.5000,-3.7000", 9),
]
ZONAS = {"label": "Ve directamente a tu zona", "placeholder": "Elige una zona", "back": "Cambia de zona"}
MORE_INFO = " Más información en <a href=\"https://elarasocial.com/es/\" target=\"_blank\" rel=\"noopener\">elarasocial.com</a>."
TIMES = "Los tiempos son aproximados, caminando a un ritmo tranquilo (entre 12 y 15 minutos por kilómetro) y sin contar las pausas."


def build_block(course, rows, maps, mk_route, text, summary, extra_notice, prefix):
    by = {int(r["n"]): r for r in rows}
    assert len(by) == len(rows), "números repetidos"
    groups, used = [], set()
    for lo, hi, gid, title, mid, ll, z in maps:
        assert len(mid) == 32, (title, mid)
        ns = sorted(n for n in by if lo <= n <= hi)
        assert ns, f"mapa sin rutas: {title}"
        used |= set(ns)
        groups.append({
            "id": f"{prefix}-{gid}", "title": title,
            "maps": [{"mid": mid, "ll": ll, "z": z, "title": f"Rutas de Esperanza Activa - Madrid · {title}",
                      "label": f"{title} · {len(ns)} {'ruta' if len(ns) == 1 else 'rutas'}"}],
            "routes": [mk_route(by[n]) for n in ns],
        })
    assert used == set(by), f"rutas sin mapa: {sorted(set(by) - used)}"
    kms = [float(r["km"]) for r in rows]
    lo_, hi_ = min(kms), max(kms)
    return {
        "course": course,
        "text": text.format(n=len(rows), lo=fmt(lo_), hi=fmt(hi_)),
        "summary": summary,
        "zones": ZONAS,
        "parts": [{
            "id": f"rutas-{course}",
            "notice": {"title": "Accesibilidad y seguridad", "html": [
                "Es un paseo urbano: respeta los semáforos y los pasos de peatones.", TIMES, extra_notice + MORE_INFO]},
            "groups": groups,
        }],
    }


cuidar = tsv("madrid_cuidar.tsv")
mon = tsv("madrid_mon.tsv")
dia = tsv("madrid_dia.tsv")
desc = {int(r["n"]): r["desc"].strip() for r in tsv("madrid_dia_desc.tsv")}
assert (len(cuidar), len(mon), len(dia), len(desc)) == (129, 89, 118, 114), (len(cuidar), len(mon), len(dia), len(desc))
assert [int(r["n"]) for r in cuidar] == list(range(401, 530))
assert [int(r["n"]) for r in dia] == list(range(201, 319))
assert {int(r["n"]) for r in mon} == set(range(600, 695)) - {613, 614, 623, 628, 636, 682}
for rs in (cuidar, mon, dia):
    assert len({r["wikiloc"] for r in rs}) == len(rs), "Wikiloc repetido"
    assert all(re.fullmatch(r"\d{9}", r["wikiloc"]) for r in rs)
assert len({r["wikiloc"] for r in cuidar + mon + dia + rows}) == 129 + 89 + 118 + 128, "Wikiloc repetido entre cursos"
assert set(desc) <= {int(r["n"]) for r in dia}
assert {int(r["n"]) for r in dia} - set(desc) == {232, 241, 278, 289}   # sin descripción: se dejan sin texto


def r_cuidar(r):
    return route_common(r, r["nombre"], start=f"Distrito de {r['distrito']}")


def r_mon(r):
    return route_common(r, r["nombre"], start=f"Distrito de {r['distrito']}")


def r_dia(r):
    d = route_common(r, r["entidad"], addr_city=r["municipio"])
    if int(r["n"]) in desc:
        d["desc"] = desc[int(r["n"])]
    return d


extra = [
    build_block("cuidar", cuidar, MAPS_CUIDAR, r_cuidar,
                "{n} rutas circulares de {lo} a {hi} km, una desde cada centro cultural, centro sociocultural y biblioteca pública de Madrid. "
                "Si un centro cultural y una biblioteca comparten edificio, es una sola ruta. El equipamiento es solo el punto de referencia del recorrido.",
                "129 rutas desde centros culturales y bibliotecas",
                "El equipamiento es solo el punto de referencia del recorrido: no organiza ni recomienda esta actividad.", "cuidar"),
    build_block("mon", mon, MAPS_MON, r_mon,
                "{n} rutas circulares de {lo} a {hi} km, desde parques, jardines y plazas de los distritos de Madrid.",
                "89 rutas desde parques y jardines",
                "El parque o el jardín es solo el punto de referencia del recorrido.", "mon"),
    build_block("dia", dia, MAPS_DIA, r_dia,
                "{n} rutas circulares de {lo} a {hi} km, desde entidades de la economía social y solidaria del Mercado Social de Madrid: "
                "cooperativas, asociaciones y empresas de la ciudad, y también de Alcalá de Henares, Collado Villalba, Getafe, Torrelodones y Villaviciosa de Odón. "
                "Cada ruta lleva una breve descripción de lo que hace la entidad.",
                "118 rutas desde entidades de economía social",
                "La entidad es solo el punto de referencia del recorrido: no organiza ni recomienda esta actividad.", "dia"),
]
city["blocks"] += extra
city["summary"] = ("464 rutas circulares y cortas en Madrid y su comunidad: desde centros de salud, centros culturales y bibliotecas, "
                   "parques y jardines, y entidades de la economía social y solidaria.")
city["intro"] = ("Paseos urbanos para hacer el tiempo de reflexión de cada paso. Cada curso tiene sus rutas: elige el tuyo, busca el punto de salida "
                 "que te quede más cerca de casa, abre el mapa y camina. Las rutas son una iniciativa de Caminos de Esperanza [Activa]: "
                 "los centros, los equipamientos y las entidades solo marcan el inicio y el final, y no las organizan ni las recomiendan.")

(ROOT / "data" / "madrid.json").write_text(json.dumps(city, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("rutas:", sum(len(g["routes"]) for g in out_groups), "mapas:", len(out_groups))
for g in out_groups:
    print(f"  {g['title']}: {len(g['routes'])}")
print(f"km: {lo}–{hi}")
print("cuidar", sum(len(g["routes"]) for g in extra[0]["parts"][0]["groups"]), "mon", sum(len(g["routes"]) for g in extra[1]["parts"][0]["groups"]), "dia", sum(len(g["routes"]) for g in extra[2]["parts"][0]["groups"]))
