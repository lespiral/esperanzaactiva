#!/usr/bin/env python3
"""Rutas desde miradores (curso «Cuando el mundo te preocupa») de España, Catalunya Nord e Iparralde: 1.653 rutas (núms. 1272–2197, 5001–5751, 6001–6039).
Lee tools/miradores_espana.tsv (inventario de Drive «Inventari miradors (Wikiloc i My Maps)» + nombres y tiempos de «Rutes per ciutat i curs», pestanya «Rutes»).
- Una página de territorio por provincia (data/provincia-de-<x>.json; Ceuta y Melilla, Catalunya Nord e Iparralde, una cada una):
  un grupo por mapa de My Maps y una sección por municipio.
- Los municipios que ya tienen página propia (Madrid, Segovia, Cuenca, Málaga, Santa Cruz de Tenerife, Viveiro, Cervera de Pisuerga y Béjar)
  reciben un grupo nuevo por mapa en su página.
- Actualiza data/lugares.json (comunidad › provincia › comarca; las comarcas están asignadas de memoria: revisar) y data/site.json › territories.
Se puede volver a ejecutar. Vista inicial de los mapas (ll, z): aproximada, a partir del centro de la comarca (el full no tiene coordenadas)."""
import csv, json, re, sys, unicodedata
from collections import OrderedDict, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from miradores_espana_comarcas import C, XY, COMUNIDAD
rows = list(csv.DictReader((ROOT / "tools/miradores_espana.tsv").open(encoding="utf-8"), delimiter="\t"))
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()).strip("-")
km = lambda k: f"{float(str(k).replace(',', '.')):.2f}".replace(".", ",")
SHEET2PROV = {"Màlaga": "Málaga", "Còrdova": "Córdoba", "Múrcia": "Murcia", "Almeria": "Almería", "Cadis": "Cádiz", "Tenerife": "Santa Cruz de Tenerife",
              "La Palma": "Santa Cruz de Tenerife", "La Gomera": "Santa Cruz de Tenerife", "El Hierro": "Santa Cruz de Tenerife",
              "Gran Canaria": "Las Palmas", "Lanzarote": "Las Palmas", "Fuerteventura": "Las Palmas"}
CITY_PAGE = {"Segovia": "segovia", "Madrid": "madrid", "Cuenca": "cuenca", "Málaga": "malaga", "Santa Cruz de Tenerife": "santa-cruz-de-tenerife",
             "Viveiro": "viveiro", "Cervera de Pisuerga": "cervera-de-pisuerga", "Béjar": "bejar"}
FIX = {"1365": "Comillas", "1388": "Santander"}   # el full los tiene con el municipio «Cantabria»
CN = {"Cerdanya": "Dorres; Oceja; Santa Llocaia; Sallagosa; Llo; Sant Pere dels Forcats", "Conflent": "Castell de Vernet",
      "Vallespir": "Prats de Molló i la Presta; la Menera; Serrallonga; Sant Llorenç de Cerdans; Montboló; els Banys d'Arles i Palaldà; Ceret; Morellàs i les Illes",
      "Albera y Costa Vermella": "la Roca d'Albera; Argelers; Portvendres; Banyuls de la Marenda"}
IP = {"Baja Navarra": "Aldude; Baigorri; Donibane-Garazi; Mendibe; Larraine; Uharte-Garazi", "Labort": "Biriatu; Sara; Azkaine; Hendaia"}
LUG_EXTRA = {}
for com, ms in CN.items():
    for m in ms.split("; "): LUG_EXTRA[m] = ("Catalunya Nord (Francia)", "Pirineos Orientales", com)
for com, ms in IP.items():
    for m in ms.split("; "): LUG_EXTRA[m] = ("Iparralde (País Vasco francés)", "Pirineos Atlánticos", com)
LOOK = {}
for p, d in C.items():
    for com, ms in d.items():
        for m in ms.split("; "): LOOK[(p, m)] = (COMUNIDAD[p], p, com)
ICONS = ["tree", "plant", "map", "buildings", "sun", "footprints", "globe"]
NOTICE = {"title": "Accesibilidad y seguridad", "html": [
    "Los trazados están reconstruidos sobre OpenStreetMap a partir de la ubicación de cada mirador y no se han revisado a pie: son orientativos. "
    "Los tiempos son aproximados, caminando a un ritmo tranquilo y con pausas para descansar. Algunos caminos tienen escaleras o pendientes y no son accesibles para sillas de ruedas ni cochecitos. "
    "Camina con atención al tráfico y al estado de los caminos.",
    "El mirador es solo el punto de referencia del recorrido. Más información en <a href=\"https://elarasocial.com/es/\" target=\"_blank\" rel=\"noopener\">elarasocial.com</a>."]}

# --- datos por ruta -------------------------------------------------------
for r in rows:
    r["n"] = int(r["n"])
    if r["mun"] == "Cantabria": r["mun"] = FIX[str(r["n"])]
    g = r["grupo_hoja"]
    if g.startswith("Miradors Catalunya Nord"): r["prov"], r["page"] = "Catalunya Nord", "catalunya-nord"
    elif g.startswith("Miradors Iparralde"): r["prov"], r["page"] = "Iparralde", "iparralde"
    elif g == "Ceuta y Melilla": r["prov"], r["page"] = "Ceuta y Melilla", "ceuta-y-melilla"
    else: r["prov"] = SHEET2PROV.get(g, g); r["page"] = "provincia-de-" + slug(r["prov"])
    if r["mun"] in CITY_PAGE: r["page"] = CITY_PAGE[r["mun"]]
    if r["prov"] in ("Catalunya Nord", "Iparralde"): r["lug"] = LUG_EXTRA[r["mun"]]
    elif r["prov"] == "Ceuta y Melilla": r["lug"] = ("Ciudades autónomas", r["mun"], r["mun"])
    elif r["mun"] in CITY_PAGE: r["lug"] = None
    else: r["lug"] = LOOK[(r["prov"], r["mun"])]
    r["xy"] = XY[r["lug"][2]] if r["lug"] else None
by_map = defaultdict(list)
for r in sorted(rows, key=lambda r: r["n"]): by_map[r["mid"]].append(r)
CITY_XY = {"segovia": (40.95, -4.12), "madrid": (40.42, -3.70), "cuenca": (40.07, -2.14), "malaga": (36.72, -4.42), "santa-cruz-de-tenerife": (28.46, -16.25),
           "viveiro": (43.66, -7.60), "cervera-de-pisuerga": (42.86, -4.50), "bejar": (40.39, -5.76)}


def xy_of(r): return r["xy"] or CITY_XY[r["page"]]


def titol(muns):
    if len(muns) <= 2: return " y ".join(muns)
    rest = len(muns) - 2
    return f"{muns[0]}, {muns[1]} y {rest} {'municipio' if rest == 1 else 'municipios'} más"


def map_meta(mid):
    rs = by_map[mid]
    la = [xy_of(r)[0] for r in rs]; lo = [xy_of(r)[1] for r in rs]
    span = max(max(la) - min(la), (max(lo) - min(lo)) * 0.75)
    z = 7
    for lim, zz in ((0.08, 12), (0.16, 11), (0.32, 10), (0.64, 9), (1.3, 8)):
        if span < lim: z = zz; break
    muns = list(OrderedDict.fromkeys(r["mun"] for r in rs))
    return {"mid": mid, "ll": f"{(max(la) + min(la)) / 2:.4f},{(max(lo) + min(lo)) / 2:.4f}", "z": z,
            "title": f"{titol(muns)} · miradores", "label": f"Mapa de miradores · {len(rs)} rutas"}


def route(r):
    d = {"n": r["n"], "name": r["name"], "start": "Inicio y final: " + r["name"],
         "info": f'{km(r["km"])} km · {r["caminar"]} min caminando · {r["pausas"]} min con pausas · {r["tipo"]}',
         "wikiloc": "https://www.wikiloc.com/wikiloc/view.do?id=" + r["wikiloc"]}
    notes = []
    if r["sin_nombre"]: notes.append("El mirador no tiene nombre en el IGN.")
    if r["dist_osm"]: notes.append(f"El mirador está a unos {r['dist_osm']} m del camino más cercano en OSM.")
    if notes: d["note"] = " ".join(notes)
    return d


def text_of(rs):
    n = len(rs); kms = [float(str(r["km"]).replace(",", ".")) for r in rs]
    t = (f"{n} rutas cortas (de {km(min(kms))} a {km(max(kms))} km) que salen de un mirador. Mira el mundo desde donde estás, escucha el audio, camina y vuelve al mismo lugar, "
         "pero desde un lugar interno diferente, con una mirada diferente. Los trazados están reconstruidos sobre OpenStreetMap y todavía no se han revisado a pie: revisa el estado del camino antes de ir.")
    ida = sum(1 for r in rs if r["tipo"] != "circular")
    if ida == n: t += " Todas son de ida y vuelta, no circulares."
    elif ida: t += " Algunas son de ida y vuelta, no circulares; la ficha de cada ruta lo dice."
    return t


def groups_for(page_rows, used):
    out = []
    for mid in sorted({r["mid"] for r in page_rows}, key=lambda m: by_map[m][0]["n"]):
        here = [r for r in by_map[mid] if r in page_rows]
        secs = OrderedDict()
        for r in here: secs.setdefault(r["mun"], []).append(r)
        sections = []
        for mun, srs in secs.items():
            base = f"{slug(mun)}-miradores"
            sec = {"title": mun, "id": base + ("-" + mid[:6].lower() if base in used else ""), "routes": [route(x) for x in srs]}
            if base in used: sec["route_prefix"] = base; sec["nav"] = f"{mun} (miradores, mapa {mid[:6]})"
            used.add(base)
            sections.append(sec)
        out.append({"id": "cuando-el-mundo-miradores-" + mid[:6].lower(), "title": titol(list(secs)), "maps": [map_meta(mid)], "sections": sections})
    return out


# --- páginas de territorio --------------------------------------------------------
lug_p = ROOT / "data/lugares.json"
lug = json.loads(lug_p.read_text(encoding="utf-8"))
com = json.loads((ROOT / "data/cat/comarques.json").read_text(encoding="utf-8"))
cat_slugs = {slug(k) for k in com}
site_p = ROOT / "data/site.json"
site_txt = site_p.read_text(encoding="utf-8")
terr_lines, pages = [], OrderedDict()
for r in rows: pages.setdefault(r["page"], []).append(r)
NAME = {"catalunya-nord": ("Catalunya Nord", "Catalunya Nord (Francia)", "Caminar por Catalunya Nord"),
        "iparralde": ("Iparralde", "Iparralde (País Vasco francés)", "Caminar por Iparralde"),
        "ceuta-y-melilla": ("Ceuta y Melilla", "Ceuta y Melilla", "Caminar por Ceuta y Melilla")}
n_terr = 0
for page, prs in pages.items():
    if page in CITY_PAGE.values(): continue
    prov = prs[0]["prov"]
    name, region, title = NAME.get(page, (f"Provincia de {prov}", COMUNIDAD.get(prov, ""), f"Caminar por la provincia de {prov}"))
    used = set()
    groups = groups_for(prs, used)
    nmun = len({r["mun"] for r in prs})
    d = {"slug": page, "name": name, "kind": "territory", "title": title, "region": region,
         "summary": f"{len(prs)} rutas desde miradores en {nmun} {'municipio' if nmun == 1 else 'municipios'}.",
         "intro": "Rutas a pie para hacer el tiempo de reflexión de cada paso, desde miradores.",
         "zones": {"by": "section", "label": "Ve directamente a tu pueblo", "placeholder": "Elige un pueblo", "back": "Cambia de pueblo"},
         "blocks": [{"course": "mon", "text": text_of(prs), "summary": f"{len(prs)} rutas desde miradores", "notice": NOTICE, "groups": groups}]}
    (ROOT / f"data/{page}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for r in prs:
        assert slug(r["mun"]) not in cat_slugs, f"{r['mun']} choca con un lugar de Cataluña"
        lug[r["mun"]] = list(r["lug"])
    if f'"slug": "{page}"' not in site_txt:
        terr_lines.append(f'    {{"slug": "{page}", "name": "{name}", "region": "{region}", "icon": "{ICONS[n_terr % len(ICONS)]}"}}')
    n_terr += 1
if terr_lines:
    a = site_txt.index('"territories": [') + len('"territories": [')
    e = site_txt.index("\n  ]", a)
    site_txt = site_txt[:e] + ",\n" + ",\n".join(terr_lines) + site_txt[e:]
    site_p.write_text(site_txt, encoding="utf-8")
lug_p.write_text(json.dumps(lug, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

# --- ciudades con página propia -----------------------------------------------------
def fix_text(t, rs_all):
    ida = [r for r in rs_all if r["tipo"] != "circular"]
    kms = [float(str(r["km"]).replace(",", ".")) for r in rs_all]
    t = re.sub(r"^\d+ rutas cortas", f"{len(rs_all)} rutas cortas", t)
    t = re.sub(r"\(de [\d,]+ a [\d,]+ km\)", f"(de {km(min(kms))} a {km(max(kms))} km)", t)
    t = re.sub(r" (La ruta|Las rutas) [\d, ]+ (es|son) de ida y vuelta, no circulares?\.", "", t)
    t = re.sub(r" (Todas|Algunas) son de ida y vuelta, no circulares[^.]*\.", "", t)
    if ida:
        nums = ", ".join(str(r["n"]) for r in ida)
        t += (f" {'La ruta ' + nums + ' es' if len(ida) == 1 else 'Las rutas ' + nums + ' son'} de ida y vuelta, no circular{'' if len(ida) == 1 else 'es'}.")
    return t


for page, prs in pages.items():
    if page not in CITY_PAGE.values(): continue
    p = ROOT / f"data/{page}.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    indent = 1
    b = next(b for b in d["blocks"] if b["course"] == "mon")
    part = next((x for x in b["parts"] if x["id"] == "miradores"), None) or b["parts"][-1]
    old_ids = {g["id"] for g in part["groups"] if g["id"].startswith("cuando-el-mundo-miradores-")}
    part["groups"] = [g for g in part["groups"] if g["id"] not in old_ids]
    for mid in sorted({r["mid"] for r in prs}, key=lambda m: by_map[m][0]["n"]):
        rs = [r for r in by_map[mid] if r in prs]
        part["groups"].append({"id": "cuando-el-mundo-miradores-" + mid[:6].lower(), "title": f"Las {len(rs)} rutas del mapa {mid[:6]}",
                               "maps": [dict(map_meta(mid), label=f"Mapa de miradores · {len(rs)} rutas")], "routes": [route(r) for r in rs]})
    # textos con los números nuevos (solo las rutas de miradores de la parte)
    nroutes = sum(len(g["routes"]) for g in part["groups"])
    d_text_rows = []
    for g in part["groups"]:
        for x in g["routes"]:
            d_text_rows.append({"n": x["n"], "km": x["info"].split(" km")[0], "tipo": x["info"].rsplit(" · ", 1)[1]})
    if page == "madrid":
        pass   # Madrid: la parte «miradores» ya cuenta solo miradores
    if part.get("text"): part["text"] = fix_text(part["text"], d_text_rows)
    total_page = sum(len(g["routes"]) for bb in d["blocks"] for x in (bb.get("parts") or [{"groups": bb.get("groups", [])}]) for g in x["groups"] if "routes" in g)
    if page == "madrid":
        mad_total_mir = nroutes
        b["summary"] = re.sub(r"y \d+ desde miradores", f"y {mad_total_mir} desde miradores", b["summary"])
        b["text"] = re.sub(r"y \d+ rutas cortas", f"y {mad_total_mir} rutas cortas", b["text"])
        d["summary"] = re.sub(r"^\d+", str(total_page), d["summary"])
    else:
        b["text"] = fix_text(b["text"], d_text_rows) if b.get("text") else b.get("text")
        b["summary"] = re.sub(r"^\d+", str(nroutes), b["summary"])
        d["summary"] = re.sub(r"^\d+", str(total_page), d["summary"])
    p.write_text(json.dumps(d, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")
    print(page, len(prs), "rutas añadidas;", nroutes, "en la parte")
print(len(rows), "rutas;", n_terr, "páginas de territorio;", len(by_map), "mapas")
