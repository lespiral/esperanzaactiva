#!/usr/bin/env python3
"""Porta a la .org (esperanzaactiva) les pàgines de l'economia social de la .cat i en tradueix els textos.
Ús:
  python3 -I ess_org.py site ORG CAT          → site.json de la .org: territoris, l'Hospitalet i la FAQ
  python3 -I ess_org.py tr ORG ROUTES DESC_CA DESC_ES  → tradueix els *.pendientes.json (després de sync_cat i build)"""
import json, re, sys, os, glob

mode, ORG = sys.argv[1], sys.argv[2]


def es_join(s):
    """«A, B i C» → «A, B y C» (només l'última unió)."""
    if " i " not in s:
        return s
    a, b = s.rsplit(" i ", 1)
    return f"{a} y {b}"


if mode == "site":
    CAT = sys.argv[3]
    cat = json.load(open(os.path.join(CAT, "data", "site.json"), encoding="utf-8"))
    p = os.path.join(ORG, "data", "site.json")
    s = open(p, encoding="utf-8").read()
    rows = []
    for t in cat["territories"]:
        reg = t["region"]
        m = re.match(r"^(.*?)( \(sense (.*)\))?$", reg)
        reg_es = es_join(m.group(1)) + (f" (sin {m.group(3)[0].upper() + m.group(3)[1:]})" if m.group(2) else "")
        rows.append("    " + json.dumps({"slug": t["slug"], "name": t["name"], "region": reg_es, "icon": t["icon"], "source": "cat"}, ensure_ascii=False))
    s, k = re.subn(r'"territories": \[\n.*?\n  \]', '"territories": [\n' + ",\n".join(rows) + "\n  ]", s, count=1, flags=re.S)
    assert k == 1
    if '"slug": "l-hospitalet"' not in s:
        old = '    {"slug": "olot",'
        assert old in s
        s = s.replace(old, '    {"slug": "l-hospitalet", "name": "L\'Hospitalet de Llobregat", "region": "Barcelonès", "icon": "users-three", "source": "cat"},\n' + old, 1)
    add = (" Las rutas de la economía social y solidaria, en Barcelona, L'Hospitalet y muchos pueblos y ciudades de Cataluña, "
           "miden de 1,5 a 2,3 km (unos 18–35 minutos).")
    anchor = " En cada ruta encontrarás los kilómetros y el tiempo aproximado, caminando y con pausas."
    if "Las rutas de la economía social y solidaria" not in s:
        assert s.count(anchor) == 1
        s = s.replace(anchor, add + anchor)
    open(p, "w", encoding="utf-8").write(s)
    print("site.json de la .org: fet")
    sys.exit()

# ---------- traduccions ----------
ROUTES, DCA, DES = sys.argv[3:6]
R = json.load(open(ROUTES, encoding="utf-8"))
ca, es = json.load(open(DCA, encoding="utf-8")), json.load(open(DES, encoding="utf-8"))
assert len(ca) == len(es)


def clean(d):
    return re.sub(r"\s*Font actual:[^)]*\)\.?", "", d).strip()


DESC = {clean(c): e for c, e in zip(ca, es)}
NAMES = set()
for r in R:
    for k in ("municipality", "district"):
        if r[k]:
            NAMES.add(r[k].replace("’", "'"))

TITLES = {
    "Caminar per l'Alt Pirineu i Aran": "Caminar por el Alt Pirineu y Aran",
    "Caminar per l'Anoia, el Penedès i el Garraf": "Caminar por el Anoia, el Penedès y el Garraf",
    "Caminar pel Baix Llobregat": "Caminar por el Baix Llobregat",
    "Caminar pel Barcelonès Nord": "Caminar por el Barcelonès Nord",
    "Caminar pel Camp de Tarragona": "Caminar por el Camp de Tarragona",
    "Caminar per la Catalunya Central": "Caminar por la Catalunya Central",
    "Caminar pel Maresme": "Caminar por el Maresme",
    "Caminar per Ponent": "Caminar por Ponent",
    "Caminar per les Terres de l'Ebre": "Caminar por las Terres de l'Ebre",
    "Caminar per les Terres Gironines": "Caminar por las Terres Gironines",
    "Caminar pel Vallès Occidental": "Caminar por el Vallès Occidental",
    "Caminar pel Vallès Oriental": "Caminar por el Vallès Oriental",
    "Rutes a peu per fer el temps de reflexió de cada passa, des d'entitats de l'economia social i solidària.":
        "Rutas a pie para hacer el tiempo de reflexión de cada paso, desde entidades de la economía social y solidaria.",
    "Rutes a peu per fer el temps de reflexió de cada passa. Cada curs té les seves rutes: tria el teu i camina.":
        "Rutas a pie para hacer el tiempo de reflexión de cada paso. Cada curso tiene sus rutas: elige el tuyo y camina.",
    "Vés directament al teu poble": "Ve directamente a tu pueblo",
    "Tria un poble": "Elige un pueblo",
    "Canvia de poble": "Cambia de pueblo",
    "La ruta": "La ruta",
    # resums de les ciutats
    "17 circuits urbans, 7 rutes des dels equipaments, 9 pel Delta del Llobregat i 8 des de l'economia social.":
        "17 circuitos urbanos, 7 rutas desde los equipamientos, 9 por el Delta del Llobregat y 8 desde la economía social.",
    "45 rutes curtes i circulars: pels parcs, des dels CAP i hospitals, des dels equipaments comunitaris i des de l'economia social.":
        "45 rutas cortas y circulares: por los parques, desde los centros de salud y hospitales, desde los equipamientos comunitarios y desde la economía social.",
    "14 rutes curtes i circulars, des dels CAP, l'hospital, places, ponts i parcs, i des de l'economia social.":
        "14 rutas cortas y circulares, desde los centros de salud, el hospital, plazas, puentes y parques, y desde la economía social.",
    "447 rutes repartides pels 10 districtes de la ciutat.": "447 rutas repartidas por los 10 distritos de la ciudad.",
    "10 rutes des d'entitats de l'economia social i solidària.": "10 rutas desde entidades de la economía social y solidaria.",
}


def names_es(s):
    """Llista de noms de municipis o districtes («A, B i C») → castellà, o None."""
    if s in NAMES:
        return s
    # «A, B i C»: prova cada « i » (hi ha noms com «Vilanova i la Geltrú»)
    for m in re.finditer(" i ", s):
        a, b = s[:m.start()], s[m.end():]
        parts = a.split(", ") + [b]
        if all(p in NAMES for p in parts):
            return ", ".join(parts[:-1]) + " y " + parts[-1]
    return None


def rutas(n):
    return "1 ruta" if n == "1" else f"{n} rutas"


def tr(s):
    if s in TITLES:
        return TITLES[s]
    if s in DESC:
        return DESC[s]
    # descripció de ruta amb diverses entitats: frases de DESC unides per espais
    parts, rest = [], s
    for c in sorted(DESC, key=len, reverse=True):
        pass
    best = []
    i = 0
    keys = sorted(DESC, key=len, reverse=True)
    while i < len(s):
        k = next((k for k in keys if s.startswith(k, i)), None)
        if not k:
            break
        best.append(DESC[k]); i += len(k)
        if s.startswith(" ", i):
            i += 1
    if best and i >= len(s):
        return " ".join(best)
    n = names_es(s)
    if n:
        return n
    m = re.match(r"^(\d+) rut(?:a|es) des de l'economia social$", s)
    if m:
        return f"{rutas(m.group(1))} desde la economía social"
    m = re.match(r"^Les (\d+) rutes$", s)
    if m:
        return f"Las {m.group(1)} rutas"
    m = re.match(r"^(\d+) rut(?:a|es) de l'economia social i solidària en (\d+) municipis?\.$", s)
    if m:
        mun = "1 municipio" if m.group(2) == "1" else f"{m.group(2)} municipios"
        return f"{rutas(m.group(1))} de la economía social y solidaria en {mun}."
    m = re.match(r"^(.+) · mapa (\d+) de (\d+)$", s)
    if m and names_es(m.group(1)):
        return f"{names_es(m.group(1))} · mapa {m.group(2)} de {m.group(3)}"
    m = re.match(r"^(.+?)(?: · (.+))? · economia social i solidària( \(mapa \d+ de \d+\))?$", s)
    if m:
        mid = f" · {names_es(m.group(2))}" if m.group(2) else ""
        if not m.group(2) or names_es(m.group(2)):
            return f"{m.group(1)}{mid} · economía social y solidaria{m.group(3) or ''}"
    m = re.match(r"^(.+) té pàgina pròpia, amb (\d+) rut(?:a|es) d'aquest curs\.$", s)
    if m:
        return f"{m.group(1)} tiene página propia, con {rutas(m.group(2))} de este curso."
    m = re.match(r"^(\d+) rutes circulars curtes, (?:d'|de )([\d,]+)(?: a ([\d,]+))? km \(uns (\d+)–(\d+) minuts caminant\), que surten d'una entitat de l'economia social i solidària i hi tornen: cooperatives, associacions i fundacions que treballen per l'habitatge, la feina, la cultura o les cures\. Comencen i acaben al carrer, davant de l'entitat: no cal entrar-hi\.( En alguns punts hi ha diverses entitats al mateix lloc\.)?$", s)
    if m:
        t = (f"{m.group(1)} rutas circulares cortas, de {m.group(2)}{" a " + m.group(3) if m.group(3) else ""} km (unos {m.group(4)}–{m.group(5)} minutos caminando), "
             "que salen de una entidad de la economía social y solidaria y vuelven a ella: cooperativas, asociaciones y fundaciones que "
             "trabajan por la vivienda, el trabajo, la cultura o los cuidados. Empiezan y acaban en la calle, delante de la entidad: no hace falta entrar.")
        if m.group(6):
            t += " En algunos puntos hay varias entidades en el mismo lugar."
        return t
    m = re.match(r"^Una ruta circular curta, (?:d'|de )([\d,]+) km \(uns (\d+)–(\d+) minuts caminant\), que surt d'una entitat de l'economia social i solidària i hi torna\. Comença i acaba al carrer, davant de l'entitat: no cal entrar-hi\.( Al mateix lloc hi ha diverses entitats\.)?$", s)
    if m:
        t = (f"Una ruta circular corta, de {m.group(1)} km (unos {m.group(2)}–{m.group(3)} minutos caminando), que sale de una entidad "
             "de la economía social y solidaria y vuelve a ella. Empieza y acaba en la calle, delante de la entidad: no hace falta entrar.")
        if m.group(4):
            t += " En el mismo lugar hay varias entidades."
        return t
    return None


left = {}
for f in sorted(glob.glob(os.path.join(ORG, "data", "traducciones", "*.pendientes.json"))):
    slug = os.path.basename(f).split(".")[0]
    pend = json.load(open(f, encoding="utf-8"))
    keys = list(pend.keys()) if isinstance(pend, dict) else list(pend)
    out = os.path.join(ORG, "data", "traducciones", f"{slug}.json")
    cur = json.load(open(out, encoding="utf-8")) if os.path.exists(out) else {}
    n = 0
    for k in keys:
        v = tr(k)
        if v is None:
            left.setdefault(slug, []).append(k)
        else:
            cur[k] = v; n += 1
    open(out, "w", encoding="utf-8").write(json.dumps(cur, ensure_ascii=False, indent=2) + "\n")
    print(f"{slug}: {n} traduccions noves")
for slug, ks in left.items():
    print("SENSE TRADUIR", slug, ks)
