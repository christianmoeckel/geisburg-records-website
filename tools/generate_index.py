#!/usr/bin/env python3
"""Generiert index.html aus data/releases.json.

- Reihenfolge im JSON = Reihenfolge im Grid.
- "bandcamp": true  -> Titel wird live gegen geisburgrecords.bandcamp.com/music
  gematcht; published => "listen"-Link auf die Bandcamp-Seite, sonst kein Link
  (Eintrag erscheint mit Cover/Titel, Link kommt beim naechsten Lauf nach Publish).
- "links": feste Zusatz-Links (iMusician-Smartlinks, YouTube, ...).

Aufruf:  python3 tools/generate_index.py   (dann git diff pruefen, committen, pushen)
Deployed wird der Branch test_rebuild (GitHub Pages).
"""
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BC = "https://geisburgrecords.bandcamp.com"


def norm(t):
    t = t.lower().replace("’", "").replace("'", "").strip()
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def fetch_bandcamp_map():
    req = urllib.request.Request(BC + "/music", headers={"User-Agent": "Mozilla/5.0"})
    page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    pairs = {}
    # WICHTIG: /music rendert nur die neuesten ~16 serverseitig — der VOLLE Katalog steckt
    # im data-client-items-JSON des Grids (HTML-escaped). Zuerst das parsen:
    m = re.search(r'data-client-items="([^"]+)"', page)
    if m:
        items = json.loads(html.unescape(m.group(1)))
        for it in items:
            url = it.get("page_url") or ""
            title = it.get("title") or ""
            if url and title:
                pairs[norm(title)] = url if url.startswith("http") else BC + url
    for mm in re.finditer(r'href="(/(?:album|track)/[^"]+)"[^>]*>\s*<p class="title">\s*([^<]+?)\s*<', page):
        pairs.setdefault(norm(mm.group(2)), BC + mm.group(1))
    for mm in re.finditer(r'href="(/(?:album|track)/([^"/?]+))"', page):
        pairs.setdefault(norm(mm.group(2).replace("-", " ")), BC + mm.group(1))
    return pairs


def main():
    data = json.loads((ROOT / "data" / "releases.json").read_text())
    bc = fetch_bandcamp_map()
    cards, missing = [], []
    for r in data["releases"]:
        links = []
        bc_url = None
        if r.get("bandcamp"):
            key = norm(r.get("bandcamp_title", r["title"]))
            bc_url = bc.get(key)
            if not bc_url:  # Slug-Kollisionen wie heaven-2: Slug beginnt mit Titel
                slug = re.sub(r"[^a-z0-9]+", " ", key).strip().replace(" ", "-")
                bc_url = next((u for k, u in bc.items() if k.startswith(key) or u.rsplit("/", 1)[-1].rstrip("-0123456789") == slug), None)
            if not bc_url:
                missing.append(r["title"])
        # Christians Vorgabe (30.07. abends): GENAU EIN „listen"-Hyperlink pro Release.
        # Ziel-Priorität: Bandcamp (published) > fester Smartlink (iMusician, Feld "links"/"smartlink").
        # song.link/spotify/apple-Felder in der JSON werden bewusst NICHT gerendert (Odesli-Seiten
        # zeigen Fremd-UI wie „Edit this page" und teils kein Spotify — untauglich für Fans).
        if bc_url:
            links.append((r.get("bandcamp_label", "listen"), bc_url))
        elif r.get("smartlink"):
            links.append(("listen", r["smartlink"]))
        for l in r.get("links", []):
            if links and l["label"] == "listen":
                continue  # nur EIN listen-Link
            links.append((l["label"], l["url"]))
        a_tags = "\n".join(
            f'                <a href="{html.escape(u)}">{html.escape(lab)}</a>' for lab, u in links
        )
        cards.append(f"""        <div class="release">
            <img src="{html.escape(r['cover'])}" alt="Release Cover">
            <div class="release-info">
                <div class="release-title">{html.escape(r['title'])}</div>
                <div class="release-artist">{html.escape(r['artist'])}</div>
{a_tags}
            </div>
        </div>""")
    grid = "\n".join(cards)
    out = f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="style.css">
    <title>GEISBURG RECORDS</title>
</head>

<body>
    <header>
        <div class="logo-container">
            <img src="assets/logo-upscaled-hochgeschoben.png" alt="Logo">
        </div>
        <nav>
            <a href="index.html">Releases</a>
            <a href="about.html">About</a>
            <a href="events.html">Events</a>
            <a href="studio.html">Studio</a>
            <a href="newsletter.html">Newsletter</a>
        </nav>
    </header>

    <main class="grid-container">
{grid}
    </main>
    <div class="impressum">
        <p>info@geisburgrecords.com</p>
    </div>
</body>

</html>
"""
    (ROOT / "index.html").write_text(out)
    print(f"index.html: {len(data['releases'])} Releases, {sum(1 for c in cards if 'href' in c)} mit Link")
    if missing:
        print("Noch ohne Bandcamp-Link (nicht published):", ", ".join(missing))


if __name__ == "__main__":
    sys.exit(main())
