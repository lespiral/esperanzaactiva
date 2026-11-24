#!/usr/bin/env python3
"""Rutas desde miradores (curso «Cuando el mundo te preocupa») de las ciudades de fuera de Cataluña (Alacant, de momento solo aquí).
Lee tools/miradores_estado.tsv (copia del full de Drive «Rutes per ciutat i curs», pestanya «Rutes», files 172–308,
sense Amposta, Tarragona i Alacant, que són de la .cat) i:
  - crea data/<ciudad>.json (una sola parte con las rutas del mirador) para las ciudades nuevas;
  - en Madrid añade la parte «miradores» al bloque `mon` (la primera parte pasa a «Rutas desde parques y jardines»);
  - actualiza data/lugares.json y data/site.json › cities.
No toca santiago-de-compostela.json (tiene su propio generador). Los puntos de salida (data/inicis.json) no están
en el full: de momento estas rutas no salen en la búsqueda por ubicación."""
import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader((ROOT / "tools" / "miradores_estado.tsv").open(encoding="utf-8"), delimiter="\t"))

# ciudad: (slug, región, icono, lugar [comunidad, provincia, comarca], vista del mapa ll, z)
CITIES = {
    "Segovia": ("Castilla y León", "bank", ["Castilla y León", "Segovia", "Segovia"], "40.9481,-4.1184", 13),
    "Cuenca": ("Castilla-La Mancha", "bank", ["Castilla-La Mancha", "Cuenca", "Cuenca"], "40.0704,-2.1374", 13),
    "Madrid": None,
    "Santa Cruz de Tenerife": ("Canarias", "buildings", ["Canarias", "Santa Cruz de Tenerife", "Tenerife"], "28.4636,-16.2518", 12),
    "Málaga": ("Andalucía", "buildings", ["Andalucía", "Málaga", "Málaga"], "36.7213,-4.4214", 12),
    "Granada": ("Andalucía", "bank", ["Andalucía", "Granada", "Granada"], "37.1773,-3.5986", 13),
    "Córdoba": ("Andalucía", "bank", ["Andalucía", "Córdoba", "Córdoba"], "37.8882,-4.7794", 12),
    "Toledo": ("Castilla-La Mancha", "bank", ["Castilla-La Mancha", "Toledo", "Toledo"], "39.8628,-4.0273", 13),
    "Zaragoza": ("Aragón", "buildings", ["Aragón", "Zaragoza", "Zaragoza"], "41.6488,-0.8891", 12),
    "Cartagena": ("Región de Murcia", "buildings", ["Región de Murcia", "Murcia", "Cartagena"], "37.6257,-0.9966", 12),
    "Ferrol": ("Galicia", "buildings", ["Galicia", "A Coruña", "Ferrol"], "43.4845,-8.2336", 12),
    "Alacant": ("Comunitat Valenciana", "buildings", ["Comunitat Valenciana", "Alacant", "L'Alacantí"], "38.2700,-0.4800", 11),
    "Cervera de Pisuerga": ("Castilla y León", "buildings", ["Castilla y León", "Palencia", "Montaña Palentina"], "42.8636,-4.5042", 11),
    "Cazorla": ("Andalucía", "buildings", ["Andalucía", "Jaén", "Sierra de Cazorla"], "37.9100,-3.0030", 11),
    "A Coruña": ("Galicia", "buildings", ["Galicia", "A Coruña", "A Coruña"], "43.3623,-8.4115", 12),
    "Zamora": ("Castilla y León", "bank", ["Castilla y León", "Zamora", "Zamora"], "41.5034,-5.7467", 12),
    "Cangas del Narcea": ("Principado de Asturias", "buildings", ["Principado de Asturias", "Asturias", "Cangas del Narcea"], "43.1760,-6.5510", 10),
    "Ronda": ("Andalucía", "buildings", ["Andalucía", "Málaga", "Serranía de Ronda"], "36.7424,-5.1673", 12),
    "Béjar": ("Castilla y León", "buildings", ["Castilla y León", "Salamanca", "Sierra de Béjar"], "40.3861,-5.7648", 12),
    "Viveiro": ("Galicia", "buildings", ["Galicia", "Lugo", "A Mariña Oriental"], "43.6620,-7.5960", 12),
    "Valladolid": ("Castilla y León", "buildings", ["Castilla y León", "Valladolid", "Valladolid"], "41.6523,-4.7245", 12),
    "Las Palmas": ("Canarias", "buildings", ["Canarias", "Las Palmas", "Gran Canaria"], "28.1235,-15.4363", 12),
    "Gijón": ("Principado de Asturias", "buildings", ["Principado de Asturias", "Asturias", "Gijón"], "43.5322,-5.6611", 12),
}
MADRID_MAP = {"ll": "40.4168,-3.7038", "z": 12}
NUM = {1: "una", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis", 7: "siete", 8: "ocho", 9: "nueve", 10: "diez"}


def km(s): return f"{float(s.replace(',', '.')):.2f}".replace(".", ",")


def route(r):
    d = {
        "n": int(r["n"]), "name": r["name"],
        "start": "Inicio y final: " + r["name"],
        "info": f'{km(r["km"])} km · {r["caminar"]} min caminando · {r["pausas"]} min con pausas · {r["tipo"]}',
        "wikiloc": "https://www.wikiloc.com/wikiloc/view.do?id=" + r["wikiloc"],
    }
    if r["nota"]:
        d["note"] = r["nota"]
    return d


def part(city, rs, pid, titled, mapinfo):
    n = len(rs)
    kms = [float(r["km"].replace(",", ".")) for r in rs]
    ida = [r for r in rs if r["tipo"] != "circular"]
    lo, hi = km(str(min(kms))), km(str(max(kms)))
    text = (f"{n} rutas cortas (de {lo} a {hi} km) que salen de un mirador. Mira el mundo desde donde estás, escucha el audio, "
            "camina y vuelve al mismo lugar, pero desde un lugar interno diferente, con una mirada diferente. "
            "Los trazados están reconstruidos sobre OpenStreetMap y todavía no se han revisado a pie: revisa el estado del camino antes de ir.")
    if ida:
        nums = ", ".join(r["n"] for r in ida)
        text += (f" {'La ruta ' + nums + ' es' if len(ida) == 1 else 'Las rutas ' + nums + ' son'} de ida y vuelta, no circular"
                 f"{'' if len(ida) == 1 else 'es'}.")
    p = {
        "id": pid,
        "notice": {"title": "Accesibilidad y seguridad", "html": [
            "Los tiempos son aproximados: caminando a un ritmo tranquilo y con pausas para descansar. Algunos caminos tienen escaleras o pendientes y no son accesibles para sillas de ruedas ni cochecitos.",
            "El mirador es solo el punto de referencia del recorrido. Más información en <a href=\"https://elarasocial.com/es/\" target=\"_blank\" rel=\"noopener\">elarasocial.com</a>."]},
        "groups": [{"id": f"{pid}-rutas", "title": f"Las {n} rutas",
                    "maps": [{"mid": rs[0]["mid"], "ll": mapinfo["ll"], "z": mapinfo["z"],
                              "title": f"{city} · Miradores (rutas {rs[0]['n']}–{rs[-1]['n']})",
                              "label": f"Rutas {rs[0]['n']} a {rs[-1]['n']} · Miradores"}],
                    "routes": [route(r) for r in rs]}],
    }
    if titled:
        p["title"] = p["nav"] = "Rutas desde miradores"
    p["_text"] = text
    return p


def dump(path, d, indent):
    path.write_text(json.dumps(d, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")


site_p = ROOT / "data" / "site.json"
site_txt = site_p.read_text(encoding="utf-8")
site = json.loads(site_txt)
lug_p = ROOT / "data" / "lugares.json"
lug = json.loads(lug_p.read_text(encoding="utf-8"))

for city, conf in CITIES.items():
    rs = [r for r in rows if r["ciudad"] == city]
    assert rs, city
    assert len({r["mid"] for r in rs}) == 1
    slug = rs[0]["slug"]
    if city == "Madrid":
        p = ROOT / "data" / "madrid.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        b = next(b for b in d["blocks"] if b["course"] == "mon")
        first = b["parts"][0]
        if not first.get("title"):
            first["title"] = first["nav"] = "Rutas desde parques y jardines"
        pt = part(city, rs, "miradores", True, MADRID_MAP)
        pt["text"] = pt.pop("_text")
        b["parts"] = [x for x in b["parts"] if x["id"] != "miradores"] + [pt]
        total = sum(len(g["routes"]) for x in b["parts"] if x["id"] != "miradores" for g in x["groups"])
        b["text"] = (f"{total} rutas circulares de 1,6 a 3 km, desde parques, jardines y plazas de los distritos de Madrid, "
                     f"y {len(rs)} rutas cortas que salen de un mirador.")
        b["summary"] = f"{total} rutas desde parques y jardines y {len(rs)} desde miradores"
        allr = sum(len(g["routes"]) for bb in d["blocks"] for x in bb.get("parts", []) for g in x["groups"] if "routes" in g)
        allr += sum(len(g["routes"]) for bb in d["blocks"] for g in bb.get("groups", []) if "routes" in g)
        d["summary"] = d["summary"].replace(d["summary"].split()[0], str(allr), 1)
        dump(p, d, 1)
        continue
    region, icon, lugar, ll, z = conf
    pt = part(city, rs, "rutas-mon", False, {"ll": ll, "z": z})
    pt["text"] = pt.pop("_text")
    n = len(rs)
    d = {"slug": slug, "name": city, "region": region,
         "summary": f"{n} rutas cortas desde miradores de la ciudad.",
         "intro": ("Rutas cortas que salen de un mirador, para hacer el tiempo de reflexión de cada paso. Cada curso tiene sus rutas: "
                   "elige el tuyo, abre el mapa y camina. Los miradores solo marcan el inicio y el final del recorrido."),
         "blocks": [{"course": "mon", "text": pt.pop("text"), "summary": f"{n} rutas desde miradores", "parts": [pt]}]}
    dump(ROOT / "data" / f"{slug}.json", d, 1)
    lug[slug.replace("-", " ")] = lugar
    if not any(c["slug"] == slug for c in site["cities"]):
        site["cities"].append({"slug": slug, "name": city, "region": region, "icon": icon})

# site.json se edita como texto (una línea por ciudad) para no reformatear el fichero
lines = site_txt.split("\n")
a = next(i for i, l in enumerate(lines) if l.strip() == '"cities": [') + 1
b = next(i for i in range(a, len(lines)) if lines[i].strip() == "],")
cities = [json.loads(l.strip().rstrip(",")) for l in lines[a:b]]
for c in site["cities"]:
    if not any(x["slug"] == c["slug"] for x in cities):
        cities.append(c)
cities.sort(key=lambda c: c["slug"])
lines[a:b] = ["    " + json.dumps(c, ensure_ascii=False) .replace('": ', '": ').replace('", "', '", "') + ("," if i < len(cities) - 1 else "") for i, c in enumerate(cities)]
site_p.write_text("\n".join(lines), encoding="utf-8")
lug_p.write_text(json.dumps(lug, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("ok", len(rows), "rutas")
