#!/usr/bin/env python3
"""Erzeugt links.html — die eigene Link-in-Bio-Seite (Beacons-Ablösung, 01.08.2026).
Top-Eintrag = neuester Release aus releases.json[0] (automatisch aktuell!),
Rest aus data/links.json. Stil = listen-Pages (Smartlink-Optik).
"""

# Bis 05.09.2026 trug jede generierte Link-Seite einen GoatCounter-Zaehler auf
# geisburgrecords.goatcounter.com. Der Account existiert nicht mehr - der Endpunkt
# antwortet 400 "no site at this domain". Gezaehlt wurde also laengst nichts; jeder
# Seitenaufruf lud nur ein Fremdscript und schickte einen Request ins Leere. Die Zeile
# ist deshalb raus. Wer wieder zaehlen will, legt das Konto neu an und fuegt im
# <body> wieder ein:
#   <script data-goatcounter="https://<konto>.goatcounter.com/count" async
#           src="//gc.zgo.at/count.js"></script>

import html, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
import hashlib as _h
CSSV = _h.md5((ROOT / "style.css").read_bytes()).hexdigest()[:8]

def main():
    rel = json.loads((ROOT / "data" / "releases.json").read_text())["releases"]
    cfg = json.loads((ROOT / "data" / "links.json").read_text())
    # Oben stehen zuerst die ANSTEHENDEN Releases mit Pre-Save, darunter der neueste
    # veroeffentlichte. Vorher zeigte die Seite ausschliesslich Veroeffentlichtes, ein
    # Link-in-Bio soll aber genau das bewerben, was noch kommt (Christian 08.09.2026).
    #
    # Die Karte fuehrt auf unsere EIGENE listen-Seite, nicht auf music.imusician.pro.
    # Das ist kein Umweg, sondern Absicht: die Pre-Save-Knoepfe dort zeigen bereits
    # direkt auf iMusician, und sie MUESSEN das auch. Die Zuordnung eines Pre-Saves
    # laeuft ueber localStorage auf music.imusician.pro; ein von hier nachgebauter
    # Spotify-Knopf sieht richtig aus und der Pre-Save geht still verloren (ausfuehrlich
    # in tools/generate_listen_pages.py).
    def karte(r, tag, sub, ziel=None):
        return f"""        <a class="bio-release" href="{html.escape(ziel or f"listen/{r['slug']}.html")}">
            <img src="{html.escape(r['cover'])}" alt="Cover">
            <div>
                <div class="bio-tag">{html.escape(tag)}</div>
                <div class="bio-release-title">{html.escape(r['artist'])} ~ {html.escape(r['title'])}</div>
                <div class="bio-release-sub">{html.escape(sub)}</div>
            </div>
        </a>"""

    karten = []
    for r in rel:
        if r.get("presave") and r.get("note"):
            # note traegt das Datum als Freitext ("out 30.09.2026"), das ist die einzige
            # Stelle, an der es steht — also wird es das Untertitel-Label.
            #
            # Die Karte fuehrt DIREKT auf die iMusician-Seite, nicht auf unsere
            # listen-Seite (Christian 09.09.2026: "mach in den linktree nur einen link
            # zum presave, der weiterleitet auf die imusician seite"). Die Zwischenseite
            # trug bis dahin denselben einen Knopf und kostete nur einen Klick. Warum das
            # Ziel iMusician sein MUSS und nicht Spotify direkt, steht in
            # generate_listen_pages.py.
            karten.append(karte(r, "PRE-SAVE", r["note"], ziel=r["presave"]))
    newest = next(r for r in rel if not r.get("note"))
    karten.append(karte(newest, "NEW RELEASE", "listen everywhere"))
    release_card = "\n".join(karten)
    buttons = "\n".join(
        f'        <a class="listen-btn bio-btn" href="{html.escape(l["url"])}">{html.escape(l["label"])}</a>' 
        for l in cfg["links"])
    page = f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="style.css?v={CSSV}">
    <title>GEISBURG RECORDS — Links</title>
</head>

<body>
    <main class="listen-page">
        <a href="index.html"><img class="bio-logo" src="assets/logo-upscaled-hochgeschoben.png" alt="Geisburg Records"></a>
{release_card}
        <div class="listen-buttons">
{buttons}
        </div>
    </main>
</body>

</html>
"""
    (ROOT / "links.html").write_text(page)
    # Kurz-URL /links: gleiche Seite mit ../-Pfaden in links/index.html
    sub = page.replace('href="style.css', 'href="../style.css').replace('src="assets/', 'src="../assets/')
    sub = sub.replace('href="listen/', 'href="../listen/').replace('href="index.html"', 'href="../index.html"')
    sub = sub.replace('src="' + __import__('html').escape(newest['cover']) + '"', 'src="../' + __import__('html').escape(newest['cover']) + '"')
    d = ROOT / "links"
    d.mkdir(exist_ok=True)
    (d / "index.html").write_text(sub)
    vorab = [r for r in rel if r.get("presave") and r.get("note")]
    print(f"links.html + links/index.html: {len(vorab)} Pre-Save-Karten "
          f"({', '.join(r['title'] for r in vorab) or 'keine'}), dann "
          f"{newest['artist']} ~ {newest['title']}, + {len(cfg['links'])} Links")

if __name__ == "__main__":
    main()
