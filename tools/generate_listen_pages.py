#!/usr/bin/env python3
"""Erzeugt pro Release eine eigene Smartlink-Seite listen/<slug>.html (Christians Vorgabe 30.07.:
„listen führt auf eine Hyperlink-Seite, von der man zum Streaming-Dienst seiner Wahl kommt" —
eigene Seiten statt song.link/iMusician: volle Kontrolle, Bandcamp+SoundCloud drin, Track-Links).

Quellen: data/releases.json — Felder bandcamp_url, spotify, applemusic, soundcloud, deezer, youtube.
Fehlende Dienste erscheinen einfach nicht; manuell fixbar in der JSON (bald: trackwerk).
Aufruf: python3 tools/generate_listen_pages.py  (danach generate_index.py + push)
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SERVICES = [
    ("bandcamp_url", "Bandcamp"),
    ("spotify", "Spotify"),
    ("applemusic", "Apple Music"),
    ("soundcloud", "SoundCloud"),
    ("deezer", "Deezer"),
    ("youtube", "YouTube"),
]


def main():
    d = json.loads((ROOT / "data" / "releases.json").read_text())
    out_dir = ROOT / "listen"
    out_dir.mkdir(exist_ok=True)
    n_pages = 0
    for r in d["releases"]:
        slug = r["slug"]
        buttons = "\n".join(
            f'            <a class="listen-btn" href="{html.escape(r[f])}">{label}</a>'
            for f, label in SERVICES if r.get(f)
        )
        if not buttons:
            buttons = '            <p class="listen-note">coming soon</p>'
        page = f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="../style.css">
    <title>{html.escape(r['title'])} — {html.escape(r['artist'])} | GEISBURG RECORDS</title>
</head>

<body>
    <header>
        <div class="logo-container">
            <a href="../index.html"><img src="../assets/logo-upscaled-hochgeschoben.png" alt="Geisburg Records"></a>
        </div>
    </header>
    <main class="listen-page">
        <img class="listen-cover" src="../{html.escape(r['cover'])}" alt="Cover">
        <div class="release-info">
            <div class="release-title">{html.escape(r['title'])}</div>
            <div class="release-artist">{html.escape(r['artist'])}</div>
        </div>
        <div class="listen-buttons">
{buttons}
        </div>
    </main>
    <div class="impressum">
        <p>info@geisburgrecords.com</p>
    </div>
</body>

</html>
"""
        (out_dir / f"{slug}.html").write_text(page)
        n_pages += 1
    print(f"{n_pages} listen-Seiten geschrieben")


if __name__ == "__main__":
    main()
