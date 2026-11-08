# Web de Caminos de Esperanza [Activa] · esperanzaactiva.org

Web estàtica en castellà dels cursos i les rutes a peu de Caminos de Esperanza [Activa] (L'Espiral i Elara Social).
És la germana de la web en català (esperançaactiva.cat, repositori `lespiral/esperancaactiva`): el disseny és el mateix, però cada web té les seves ciutats.
Es publica amb GitHub Pages des de la carpeta `docs/`.

## On és cada cosa

- `data/site.json`: tots els textos en castellà (inici, cursos, preguntes, peu de pàgina, contacte, enllaços de Thinkific) i la llista de ciutats.
- `data/cat/`: les rutes de les ciutats de Catalunya (Barcelona, el Prat, Olot i Vic), copiades de la .cat. No s'editen a mà: es porten amb `sync_cat.py`.
- `data/traducciones/<ciutat>.json`: la traducció al castellà dels textos d'aquestes ciutats (català → castellà).
- `data/<ciutat>.json`: les rutes de les ciutats de la resta de l'Estat, directament en castellà (encara no n'hi ha cap).
- `src/templates/`: les plantilles de les pàgines; `src/templates/infografies/`: les infografies, traduïdes.
- `src/site.css` i `src/site.js`: l'aspecte i el menú del mòbil. Al final de `site.css` hi ha els estils que només té la .org.
- `src/img/`: el logo i altres imatges. `lespiral-elara.png` és el de la .cat retallat, sense el lema en català; el lema surt en text.
- `docs/`: la web generada. No s'edita a mà: es torna a generar.

## Com es fa un canvi

1. Canvia el text a `data/site.json` (o la plantilla a `src/`).
2. Genera la web: `python3 build.py`.
3. Desa i puja els canvis. Pujar a `main` és publicar: abans, es revisa en una branca a part.

Els canvis de disseny es fan als dos repositoris alhora.

## Les rutes de Catalunya

Surten a la .org amb les mateixes dades que a la .cat. Els mapes de My Maps són els mateixos, amb les fitxes en català; a cada ciutat de Catalunya hi ha un avís que ho diu.

Per portar a la .org els canvis de rutes de la .cat:

1. Amb tots dos repositoris clonats l'un al costat de l'altre: `python3 sync_cat.py` (o `python3 sync_cat.py <carpeta de la .cat>`). També avisa si la .cat té una ciutat nova.
2. `python3 build.py`. Si hi ha textos nous sense traduir, surten en català i `build.py` els deixa a `data/traducciones/<ciutat>.pendientes.json`. Tradueix-los, passa'ls a `data/traducciones/<ciutat>.json` i torna a generar la web.

Què es tradueix: els títols, els resums, les notes, les etiquetes dels mapes i els avisos. Els noms de les rutes i les adreces són noms propis i es deixen com són (si cal, també s'hi pot posar una traducció al mateix fitxer). Els temps es tradueixen sols: «caminant» → «caminando», «amb pauses» → «con pausas».

Els ids de les ciutats de Catalunya (districtes, barris, mapes i rutes) es treuen dels títols en català abans de traduir, de manera que són els mateixos que a la .cat i no canvien si es retoca una traducció. Només canvia el tros del curs: `#quan-la-vida` → `#cuando-la-vida`, `#quan-cuidar-nos` → `#cuando-cuidarnos`, `#quan-el-mon` → `#cuando-el-mundo` i `#quan-sostenir` → `#cuando-sostener`. Per exemple, `/vic/#cuando-el-mundo-ruta-5` o `/barcelona/#equipaments-el-raval-ruta-2`.

Els territoris (pàgines de «Pueblos y comarcas», p. ex. el Baix Llobregat) es porten igual: a `data/site.json`, la llista `territories` amb `"source": "cat"`; `sync_cat.py` copia `data/<territori>.json` a `data/cat/` i les traduccions van a `data/traducciones/<territori>.json`. Els ids dels municipis i de les rutes són els de la .cat (`/baix-llobregat/#olesa-de-montserrat-ruta-1`). Com funcionen, al README de la .cat («Pobles i comarques»).

**Menú «Elige dónde quieres caminar» (8 de novembre de 2026).** A Inicio, a dalt de «Ciudades, pueblos y comarcas» i a la pàgina del curs «Cuando sostener la vida se hace difícil», en lloc del desplegable llarg de tots els pobles: provincia › comarca › pueblo o ciudad, amb un cercador. Mateix codi que a la .cat (`place_tree()` a `build.py`, macro `place_nav` a `parts.html`, `.placenav` a `site.css` i `site.js`); textos a `data/site.json` › `place_nav`. La comarca i la província de cada lloc són a `data/cat/comarques.json`, que `sync_cat.py` copia de la .cat: un poble nou s'afegeix a la .cat. Si falta un lloc, `build.py` s'atura i diu quin. Quan hi hagi ciutats de la resta de l'Estat, caldrà un nivell més (comunidad › provincia › municipio) o una taula pròpia.

## Afegir una ciutat de la resta de l'Estat

1. Crea `data/<ciutat>.json` en castellà, amb la mateixa estructura que `data/cat/olot.json` (rutes agrupades per curs, amb el `mid`, el centre `ll` i el zoom `z` de cada mapa de My Maps). No s'han d'inventar dades: si en falta alguna, es deixa marcada amb `[PENDIENTE]`.
2. A `data/site.json`, a `cities`, afegeix-hi la ciutat (`slug`, `name`, `region`, `icon`, sense `source`), en ordre alfabètic.
3. El menú «Elige dónde quieres caminar» encara només coneix Catalunya: abans, cal afegir-hi la comunitat i la província (vegeu més amunt).
4. Genera la web.

Cada ruta té el botó «Abrir el mapa», que obre a pantalla completa el mapa de My Maps on és (`google.com/maps/d/viewer?mid=…`). Si un grup té diversos mapes, cada mapa diu quines rutes té amb `"routes": [1, 2, ...]`.

## Adreces de la web

- Pàgines: `/cursos/`, `/ciudades/`, `/preguntas/` i els cursos `/malestar-emocional/`, `/cuidado-colectivo/`, `/accion-climatica/` i `/economia-social/`.
- A cada ciutat, cada bloc de curs té la seva adreça (`/el-prat/#cuando-la-vida`) i cada ruta, la seva (`/olot/#cuando-la-vida-ruta-2`); la resta, com a la .cat (vegeu el README de la .cat).

## Enllaços als cursos de Thinkific

- De moment, els cursos només són en català: el botó «Empieza el curso gratuito» porta a la inscripció (`https://espiral-elara-social.thinkific.com/enroll/<número>`) i a sota hi diu «De momento, el curso está en catalán» (`lang_note` a `data/site.json`).
- Un curs que encara no està obert porta `"soon": true` i surt amb la marca «Próximamente», sense botó.

## Criteris de contingut

- Avís «Antes de empezar»: «habla con tu centro de salud», el 024 i el 112 (el 061 és de Catalunya). A l'avís de les rutes «Caminant fem salut» de Barcelona es manté el 061 (CatSalut Respon), perquè aquestes rutes són a Catalunya.
- «CAP» és «centro de salud» als textos; els noms propis dels centres (CAP Garrotxa) es mantenen.
- No es parla de «prescripción social».
- Colors i lletres, els de la .cat: verd #1A4D40, groc #E2C668, crema #F8F5EF; Montserrat i Lato.
