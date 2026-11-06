#!/usr/bin/env python3
"""Porta a la .org les rutes de les ciutats de Catalunya de la web en català.

Ús:  python3 sync_cat.py [carpeta del repositori de la .cat]   (per defecte, ../esperancaactiva)

1. Copia data/<ciutat>.json de la .cat a data/cat/ per a cada ciutat que a data/site.json
   porta "source": "cat".
2. Avisa si la .cat té ciutats que encara no són a data/site.json de la .org.
3. Després, executa python3 build.py: si hi ha textos nous sense traduir, build.py els
   deixa a data/traducciones/<ciutat>.pendientes.json.
"""
import json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "esperancaactiva"
if not (CAT / "data" / "site.json").exists():
    sys.exit(f"No trobo el repositori de la .cat a {CAT}")

site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
cat_site = json.loads((CAT / "data" / "site.json").read_text(encoding="utf-8"))
places = site["cities"] + site.get("territories", [])
ours = {c["slug"] for c in places if c.get("source") == "cat"}

(ROOT / "data" / "cat").mkdir(exist_ok=True)
for slug in sorted(ours):
    src, dst = CAT / "data" / f"{slug}.json", ROOT / "data" / "cat" / f"{slug}.json"
    if not src.exists():
        print(f"{slug}: no és a la .cat; la deixo com està")
        continue
    same = dst.exists() and dst.read_bytes() == src.read_bytes()
    if not same:
        shutil.copy(src, dst)
    print(f"{slug}: {'sense canvis' if same else 'actualitzada'}")

new = [c for c in cat_site["cities"] + cat_site.get("territories", []) if c.get("slug") and c["slug"] not in ours]
for c in new:
    print(f"La .cat té una ciutat nova: {c['name']} ({c['slug']}). Per afegir-la a la .org, posa-la a data/site.json › cities amb \"source\": \"cat\" i torna a executar aquest script.")
