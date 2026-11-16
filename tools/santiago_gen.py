#!/usr/bin/env python3
"""Genera data/santiago-de-compostela.json (rutas de Santiago de Compostela) a partir de tools/santiago_rutas.tsv.

El TSV es una copia de la hoja de Drive «Rutes Santiago de Compostela» (una fila por ruta; la hoja es la
fuente de verdad). Uso:  python3 tools/santiago_gen.py
No se inventa ningún dato: la dirección sale solo si la hoja la da (entre paréntesis) y no está marcada
como dudosa o sin confirmar. Las observaciones internas de la hoja no se publican.
"""
import csv, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# clave -> (curso, mid, título del mapa en My Maps, etiqueta, ll, z)
MAPS = {
    "CS":  ("vida",   "1Au67JpD2T1cHjbozWmj8cSumv9g7N2k", "Centros de salud", "42.8759,-8.5441", 14),
    "SC1": ("cuidar", "1fIayboncZ9ETL94AbdJZFRngTFrzIjE", "Centros socioculturales (1)", "42.8782,-8.5448", 13),
    "SC2": ("cuidar", "1Hk6PIFSGXNDCSHZ9Mdcb5IRcwiwb09w", "Centros socioculturales (2)", "42.8782,-8.5448", 13),
    "PP1": ("mon",    "18rxxjHYFlAlPuvDZlq2Csi3T6gUG1Fk", "Parques y plazas (1)", "42.8813,-8.5484", 14),
    "PP2": ("mon",    "1VreJ4nwjLDNXMoaDU31V4dRbTE1l2RM", "Parques y plazas (2)", "42.8782,-8.5448", 13),
}

rows = list(csv.DictReader((ROOT / "tools" / "santiago_rutas.tsv").open(encoding="utf-8"), delimiter="\t"))
assert len(rows) == 33 and len({r["wikiloc"] for r in rows}) == 33, "deberían ser 33 rutas con Wikiloc distinto"
assert {r["mapa"] for r in rows} == set(MAPS)
assert not any("PENDIENTE" in m[1] for m in MAPS.values())


def km_fmt(k):
    return f"{float(k.replace(',', '.')):.2f}".replace(".", ",")


def walk(k):
    """Tiempo aproximado caminando: 12-15 min por km."""
    km = float(k.replace(",", "."))
    return f"{round(km * 12)}–{round(km * 15)} min caminando"


def route(r):
    d = {
        "n": int(r["n"]),
        "name": r["nombre"],
        "info": f"{km_fmt(r['km'])} km · circular · {walk(r['km'])}",
        "wikiloc": f"https://www.wikiloc.com/wikiloc/view.do?id={r['wikiloc']}",
    }
    if r["direccion"]:
        d["address"] = f"{r['direccion']}, Santiago de Compostela"
    return d


COURSE = {  # curso -> (claves de mapa, título del grupo, resumen, texto, aviso)
    "vida": (["CS"], "Las 5 rutas", "5 rutas, una desde cada centro de salud",
             "{n} rutas circulares de {lo} a {hi} km, una desde cada centro de salud de Santiago de Compostela. "
             "El centro de salud es solo el punto de referencia del recorrido."),
    "cuidar": (["SC1", "SC2"], "Las 12 rutas", "12 rutas desde centros socioculturales, un centro cívico y una biblioteca",
               "{n} rutas circulares de {lo} a {hi} km, desde los centros socioculturales de los barrios, un centro cívico y una biblioteca pública. "
               "Cada equipamiento es solo el punto de referencia del recorrido."),
    "mon": (["PP1", "PP2"], "Las 16 rutas", "16 rutas desde parques, plazas y espacios verdes",
            "{n} rutas circulares de {lo} a {hi} km, desde parques, plazas y espacios verdes de Santiago de Compostela."),
}
NOTICE_EXTRA = {
    "vida": "El centro de salud es solo el punto de referencia del recorrido: no organiza ni recomienda esta actividad.",
    "cuidar": "El equipamiento es solo el punto de referencia del recorrido: no organiza ni recomienda esta actividad.",
    "mon": "El parque o la plaza es solo el punto de referencia del recorrido.",
}

fmt = lambda x: (f"{x:.1f}".replace(".", ",")).replace(",0", "")
blocks, total = [], 0
for course, (keys, gtitle, summary, text, ) in [(c, (v[0], v[1], v[2], v[3])) for c, v in COURSE.items()]:
    rs = [r for r in rows if r["mapa"] in keys]
    kms = [float(r["km"].replace(",", ".")) for r in rs]
    maps = []
    for k in keys:
        mrows = [r for r in rs if r["mapa"] == k]
        ns = [int(r["n"]) for r in mrows]
        maps.append({
            "mid": MAPS[k][1], "ll": MAPS[k][3], "z": MAPS[k][4],
            "title": f"Santiago de Compostela · {MAPS[k][2]}",
            "label": f"Rutas {min(ns)} a {max(ns)} · {MAPS[k][2]}" if len(ns) > 1 else f"Rutas {min(ns)} a {max(ns)} · {MAPS[k][2]}",
            "routes": ns,
        })
    total += len(rs)
    blocks.append({
        "course": course,
        "text": text.format(n=len(rs), lo=fmt(min(kms)), hi=fmt(max(kms))),
        "summary": summary,
        "parts": [{
            "id": f"rutas-{course}",
            "notice": {
                "title": "Accesibilidad y seguridad",
                "html": [
                    "Es un paseo urbano: respeta los semáforos y los pasos de peatones.",
                    "Los tiempos son aproximados, caminando a un ritmo tranquilo (entre 12 y 15 minutos por kilómetro) y sin contar las pausas.",
                    NOTICE_EXTRA[course] + " Más información en <a href=\"https://elarasocial.com/es/\" target=\"_blank\" rel=\"noopener\">elarasocial.com</a>.",
                ],
            },
            "groups": [{"id": course, "title": gtitle, "maps": maps, "routes": [route(r) for r in sorted(rs, key=lambda r: int(r["n"]))]}],
        }],
    })

city = {
    "slug": "santiago-de-compostela",
    "name": "Santiago de Compostela",
    "region": "Galicia",
    "summary": "33 rutas circulares y cortas desde centros de salud, centros socioculturales y parques y plazas de la ciudad.",
    "intro": "Paseos urbanos para hacer el tiempo de reflexión de cada paso. Elige el curso, busca el punto de salida que te quede más cerca de casa, abre el mapa y camina. Las rutas son independientes de los equipamientos: solo los usan como punto de referencia.",
    "blocks": blocks,
}
(ROOT / "data" / "santiago-de-compostela.json").write_text(json.dumps(city, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("rutas:", total, [(b["course"], len(b["parts"][0]["groups"][0]["routes"])) for b in blocks])
