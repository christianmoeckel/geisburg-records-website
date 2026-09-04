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
import hashlib as _h
CSSV = _h.md5((ROOT / "style.css").read_bytes()).hexdigest()[:8]
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
    cache_dirty = False
    for r in data["releases"]:
        links = []
        bc_url = r.get("bandcamp_url")  # Cache — /music paginiert, einmal gefundene URLs bleiben
        if r.get("bandcamp") and not bc_url:
            key = norm(r.get("bandcamp_title", r["title"]))
            bc_url = bc.get(key)
            if not bc_url:  # Slug-Kollisionen wie heaven-2: Slug beginnt mit Titel
                slug = re.sub(r"[^a-z0-9]+", " ", key).strip().replace(" ", "-")
                bc_url = next((u for k, u in bc.items() if k.startswith(key) or u.rsplit("/", 1)[-1].rstrip("-0123456789") == slug), None)
            if bc_url:
                r["bandcamp_url"] = bc_url
                cache_dirty = True
            else:
                missing.append(r["title"])
        # Christians Endstand (30.07. nachts): „listen" führt IMMER auf unsere EIGENE
        # Smartlink-Seite listen/<slug>.html (alle Dienste dort; tools/generate_listen_pages.py).
        # Release-Routine (01.08.): unreleased (note) + presave-URL -> "Pre-Save" zur iMusician-Page;
        # am Release-Tag note/presave entfernen -> normaler listen-Link.
        # Ohne presave (04.09.: der Smartlink kommt oft erst Tage nach dem Auftrag) stand hier
        # trotzdem „listen", und wer klickte, fand ein nacktes „coming soon". Die note ist die
        # einzige Stelle, an der das Datum steht — also wird sie das Label, statt ungenutzt zu bleiben.
        if r.get("note") and r.get("presave"):
            links.append(("Pre-Save", r["presave"]))
        elif r.get("note"):
            links.append((r["note"], f"listen/{r['slug']}.html"))
        else:
            links.append(("listen", f"listen/{r['slug']}.html"))
        if r.get("musicvideo"):
            links.append(("Full Length Music Video", r["musicvideo"]))
        for l in r.get("links", []):
            if l["label"] == "listen":
                continue  # eigene Landing ersetzt alte Direkt-Smartlinks
            links.append((l["label"], l["url"]))
        a_tags = "\n".join(
            f'                <a href="{html.escape(u)}"{" class=\"mv-line\"" if lab == "Music Video" else ""}>{html.escape(lab)}</a>' for lab, u in links
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
    <link rel="stylesheet" href="style.css?v={CSSV}">
    <title>GEISBURG RECORDS</title>
</head>

<body>
    <header>
        <div class="logo-container">
            <a href="index.html"><img src="assets/logo-upscaled-hochgeschoben.png" alt="Geisburg Records"></a>
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
    if cache_dirty:
        (ROOT / "data" / "releases.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"index.html: {len(data['releases'])} Releases, {sum(1 for c in cards if 'href' in c)} mit Link")
    if missing:
        print("Noch ohne Bandcamp-Link (nicht published):", ", ".join(missing))


if __name__ == "__main__":
    sys.exit(main())
