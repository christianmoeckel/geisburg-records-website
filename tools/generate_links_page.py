#!/usr/bin/env python3
"""Erzeugt links.html — die eigene Link-in-Bio-Seite (Beacons-Ablösung, 01.08.2026).
Top-Eintrag = neuester Release aus releases.json[0] (automatisch aktuell!),
Rest aus data/links.json. Stil = listen-Pages (Smartlink-Optik).
"""
import html, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
import hashlib as _h
CSSV = _h.md5((ROOT / "style.css").read_bytes()).hexdigest()[:8]

def main():
    rel = json.loads((ROOT / "data" / "releases.json").read_text())["releases"]
    cfg = json.loads((ROOT / "data" / "links.json").read_text())
    newest = next(r for r in rel if not r.get("note"))  # nur RELEASED im Slot
    tag = "NEW RELEASE"
    sub = "listen everywhere"
    release_card = f"""        <a class="bio-release" href="listen/{newest['slug']}.html">
            <img src="{html.escape(newest['cover'])}" alt="Cover">
            <div>
                <div class="bio-tag">{tag}</div>
                <div class="bio-release-title">{html.escape(newest['artist'])} ~ {html.escape(newest['title'])}</div>
                <div class="bio-release-sub">{html.escape(sub)}</div>
            </div>
        </a>"""
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
    <script data-goatcounter="https://geisburgrecords.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
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
    print(f"links.html + links/index.html: Top = {newest['artist']} ~ {newest['title']} [{tag}] + {len(cfg['links'])} Links")

if __name__ == "__main__":
    main()
