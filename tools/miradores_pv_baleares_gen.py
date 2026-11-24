#!/usr/bin/env python3
"""Rutas desde miradores (curso «Cuando el mundo te preocupa») de la Comunitat Valenciana (sin la ciudad de Alacant, que tiene página propia)
y de las Illes Balears: 64 rutas, solo en la .org (la .cat solo lleva Catalunya). Lee tools/miradores_pv_baleares.tsv (full de Drive «Rutes per ciutat
i curs», pestanya «Rutes», files 390–453 y 1096 sin ruta) y crea dos páginas de territorio: data/comunitat-valenciana.json y data/illes-balears.json
(un grupo por mapa de My Maps y una sección por municipio). Actualiza data/lugares.json y data/site.json › territories. Se puede volver a ejecutar.
Los nombres de las rutas siguen en catalán (como en el resto de la web); los puntos de salida no están en el full."""
import csv, json, re, unicodedata
from collections import OrderedDict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader((ROOT / "tools/miradores_pv_baleares.tsv").open(encoding="utf-8"), delimiter="\t"))
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()).strip("-")
km = lambda k: f"{float(str(k).replace(',', '.')):.2f}".replace(".", ",")
TERR = {
    "comunitat-valenciana": {"name": "Comunitat Valenciana", "title": "Caminar por la Comunitat Valenciana", "icon": "sun", "comunidad": "Comunitat Valenciana",
                             "region": "Alacant, Castelló y València (sin la ciudad de Alacant)", "provs": {"València", "Castelló", "Alacant"}},
    "illes-balears": {"name": "Illes Balears", "title": "Caminar por las Illes Balears", "icon": "globe", "comunidad": "Illes Balears",
                      "region": "Mallorca, Menorca y Eivissa", "provs": {"Illes Balears"}},
}
NOTICE = {"title": "Accesibilidad y seguridad", "html": [
    "Los trazados están reconstruidos sobre OpenStreetMap a partir de la ubicación de cada mirador y no se han revisado a pie: son orientativos. "
    "Los tiempos son aproximados, caminando a un ritmo tranquilo y con pausas para descansar. Algunos caminos tienen escaleras o pendientes y no son accesibles para sillas de ruedas ni cochecitos. "
    "Camina con atención al tráfico y al estado de los caminos.",
    "El mirador es solo el punto de referencia del recorrido. Más información en <a href=\"https://elarasocial.com/es/\" target=\"_blank\" rel=\"noopener\">elarasocial.com</a>."]}


def route(r):
    d = {"n": int(r["n"]), "name": r["name"], "start": "Inicio y final: " + r["name"],
         "info": f'{km(r["km"])} km · {r["caminar"]} min caminando · {r["pausas"]} min con pausas · {r["tipo"]}',
         "wikiloc": "https://www.wikiloc.com/wikiloc/view.do?id=" + r["wikiloc"]}
    if r["nota"]: d["note"] = r["nota"]
    return d


def titol(muns):
    if len(muns) <= 2: return " y ".join(muns) if not any(" i " in m for m in muns) else " y ".join(muns)
    rest = len(muns) - 2
    return f"{muns[0]}, {muns[1]} y {rest} {'municipio' if rest == 1 else 'municipios'} más"


def zoom(rs):
    la = [float(r["lat"]) for r in rs]; lo = [float(r["lon"]) for r in rs]
    span = max(max(la) - min(la), (max(lo) - min(lo)) * 0.75)
    for lim, z in ((0.02, 14), (0.04, 13), (0.08, 12), (0.16, 11), (0.32, 10), (0.64, 9), (1.3, 8)):
        if span < lim: return z
    return 7


lugares_p = ROOT / "data/lugares.json"
lugares = json.loads(lugares_p.read_text(encoding="utf-8"))
site_p = ROOT / "data/site.json"
site_txt = site_p.read_text(encoding="utf-8")
for slg, T in TERR.items():
    rs = [r for r in rows if r["provincia"] in T["provs"]]
    by_map = OrderedDict()
    for r in sorted(rs, key=lambda r: int(r["n"])): by_map.setdefault(r["mid"], []).append(r)
    groups, used = [], set()
    for mid, mrs in by_map.items():
        secs = OrderedDict()
        for r in mrs: secs.setdefault(r["lugar"], []).append(r)
        sections = []
        for mun, srs in secs.items():
            sections.append({"title": mun, "id": f"{slugify}" if False else f"{slug(mun)}-miradores", "routes": [route(x) for x in srs]})
        la = [float(r["lat"]) for r in mrs]; lo = [float(r["lon"]) for r in mrs]
        groups.append({"id": "cuando-el-mundo-miradores-" + mid[:6].lower(), "title": titol(list(secs)),
                       "maps": [{"mid": mid, "ll": f"{(max(la) + min(la)) / 2:.4f},{(max(lo) + min(lo)) / 2:.4f}", "z": zoom(mrs),
                                 "title": f"{titol(list(secs))} · miradores", "label": f"Mapa de miradores · {len(mrs)} rutas"}],
                       "sections": sections})
        for r in mrs:
            lugares[r["lugar"]] = [T["comunidad"], r["provincia"], r["comarca"]]
    n = len(rs); kms = [float(str(r["km"]).replace(",", ".")) for r in rs]
    ida = sum(1 for r in rs if r["tipo"] != "circular")
    text = (f"{n} rutas cortas (de {km(min(kms))} a {km(max(kms))} km) que salen de un mirador. Mira el mundo desde donde estás, escucha el audio, camina y vuelve al mismo lugar, "
            "pero desde un lugar interno diferente, con una mirada diferente. Los trazados están reconstruidos sobre OpenStreetMap y todavía no se han revisado a pie: revisa el estado del camino antes de ir.")
    if ida: text += " Algunas son de ida y vuelta, no circulares; la ficha de cada ruta lo dice."
    nmun = len({r["lugar"] for r in rs})
    d = {"slug": slg, "name": T["name"], "kind": "territory", "title": T["title"], "region": T["region"],
         "summary": f"{n} rutas desde miradores en {nmun} municipios.",
         "intro": "Rutas a pie para hacer el tiempo de reflexión de cada paso, desde miradores.",
         "zones": {"by": "section", "label": "Ve directamente a tu pueblo", "placeholder": "Elige un pueblo", "back": "Cambia de pueblo"},
         "blocks": [{"course": "mon", "text": text, "summary": f"{n} rutas desde miradores", "notice": NOTICE, "groups": groups}]}
    (ROOT / f"data/{slg}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if f'"slug": "{slg}"' not in site_txt:
        line = f'    {{"slug": "{slg}", "name": "{T["name"]}", "region": "{T["region"]}", "icon": "{T["icon"]}"}}'
        anchor = site_txt.index('"territories": [') + len('"territories": [')
        end = site_txt.index("\n  ]", anchor)
        site_txt = site_txt[:end] + ",\n" + line + site_txt[end:]
    print(slg, n, "rutas,", nmun, "municipios,", len(groups), "mapas")
site_p.write_text(site_txt, encoding="utf-8")
lugares_p.write_text(json.dumps(lugares, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
