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
        "info": f"{km_fmt(r['km'])} km · circular",
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
                        "El centro de salud es solo el punto de referencia del recorrido: no organiza ni recomienda esta actividad. "
                        "Más información en <a href=\"https://elarasocial.com/es/\" target=\"_blank\" rel=\"noopener\">elarasocial.com</a>.",
                    ],
                },
                "groups": out_groups,
            },
        ],
    }],
}

(ROOT / "data" / "madrid.json").write_text(json.dumps(city, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("rutas:", sum(len(g["routes"]) for g in out_groups), "mapas:", len(out_groups))
for g in out_groups:
    print(f"  {g['title']}: {len(g['routes'])}")
print(f"km: {lo}–{hi}")
