#!/usr/bin/env python3
"""Santiago de Compostela · curso «Cuando el mundo te preocupa» · parte «Rutas desde miradores» (rutas 201–204).
Lee tools/santiago_miradoiros.tsv (fichas y KML del Drive «Quan el món et preocupa - Miradors» de Santiago)
y añade/sustituye la parte «miradores» en el bloque `mon` de data/santiago-de-compostela.json y los puntos de
salida en data/inicis.json. Ejecutar DESPUÉS de santiago_gen.py (que regenera el JSON entero sin los miradores).
La ruta 205 (Campus Universitario) queda fuera de momento."""
import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader((ROOT / "tools" / "santiago_miradoiros.tsv").open(encoding="utf-8"), delimiter="\t"))
assert [r["n"] for r in rows] == ["201", "202", "203", "204"]

MAP = {"mid": "1tHKiKKvl0l4k6AoGULflLRBQ4aD9aj8", "ll": "42.9080,-8.5650", "z": 11,
       "title": "Santiago de Compostela · Miradores (rutas 201–204)",
       "label": "Rutas 201 a 204 · Miradores"}

def route(r):
    tipo = "circular" if r["tipus"] == "circular" else "ida y vuelta"
    return {
        "n": int(r["n"]),
        "name": r["name"],
        "start": "Inicio y final: " + r["name"],
        "info": f'{r["km"]} km · {r["caminar"]} min caminando · {r["pausas"]} min con pausas · {tipo}',
        "desc": r["desc"],
        "note": "Accesibilidad y seguridad: " + r["access"],
        "wikiloc": "https://www.wikiloc.com/wikiloc/view.do?id=" + r["wikiloc"],
    }

part = {
    "id": "miradores",
    "title": "Rutas desde miradores",
    "nav": "Rutas desde miradores",
    "text": ("4 rutas cortas (de 1,0 a 1,5 km) que salen de un mirador y vuelven a él. Mira el mundo desde donde estás, escucha el audio, "
             "camina y vuelve al mismo lugar, pero desde un lugar interno diferente, con una mirada diferente. "
             "Los trazados están reconstruidos sobre OpenStreetMap y todavía no se han revisado a pie: "
             "revisa el estado del camino antes de ir. La ruta 204 es de ida y vuelta y está en un entorno rural, lejos del casco urbano."),
    "notice": {
        "title": "Accesibilidad y seguridad",
        "html": [
            "Los tiempos son aproximados: caminando a un ritmo tranquilo y con pausas para descansar. Algunos caminos tienen escaleras o pendientes y no son accesibles para sillas de ruedas ni cochecitos.",
            "El mirador es solo el punto de referencia del recorrido. Más información en <a href=\"https://elarasocial.com/es/\" target=\"_blank\" rel=\"noopener\">elarasocial.com</a>.",
        ],
    },
    "groups": [{"id": "miradores-rutas", "title": "Las 4 rutas", "maps": [MAP], "routes": [route(r) for r in rows]}],
}

p = ROOT / "data" / "santiago-de-compostela.json"
d = json.loads(p.read_text(encoding="utf-8"))
b = next(b for b in d["blocks"] if b["course"] == "mon")
first = b["parts"][0]
if not first.get("title"):   # con dos partes, la primera necesita título
    first["title"] = "Rutas desde parques y plazas"
    first["nav"] = "Rutas desde parques y plazas"
b["parts"] = [x for x in b["parts"] if x["id"] != "miradores"] + [part]
b["text"] = ("Hay dos tipos de rutas: 16 rutas circulares de 1,8 a 2,2 km, desde parques, plazas y espacios verdes de Santiago de Compostela, "
             "y 4 rutas cortas que salen de un mirador.")
b["summary"] = "16 rutas desde parques y plazas y 4 desde miradores"
d["summary"] = "37 rutas cortas desde centros de salud, centros socioculturales, parques y plazas y miradores de la ciudad."
p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

pi = ROOT / "data" / "inicis.json"
txt = pi.read_text(encoding="utf-8")
ini = json.loads(txt)
for r in rows:
    ini["santiago-de-compostela"][f"cuando-el-mundo-ruta-{r['n']}"] = r["dest"]
out = "{\n" + ",\n".join('"%s":{\n%s\n}' % (k, ",\n".join('"%s":"%s"' % (a, b) for a, b in v.items())) for k, v in ini.items()) + "\n}"
pi.write_text(out + ("\n" if txt.endswith("\n") else ""), encoding="utf-8")
print("ok")
