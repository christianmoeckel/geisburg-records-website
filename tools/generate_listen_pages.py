#!/usr/bin/env python3
"""Erzeugt pro Release eine eigene Smartlink-Seite listen/<slug>.html (Christians Vorgabe 30.07.:
„listen führt auf eine Hyperlink-Seite, von der man zum Streaming-Dienst seiner Wahl kommt" —
eigene Seiten statt song.link/iMusician: volle Kontrolle, Bandcamp+SoundCloud drin, Track-Links).

Quellen: data/releases.json — Felder bandcamp_url, spotify, applemusic, soundcloud, deezer, youtube.
Fehlende Dienste erscheinen einfach nicht; manuell fixbar in der JSON (bald: trackwerk).

Seit 11.08. zusaetzlich data/artist_socials.json: darunter eine kleine Follow-Zeile mit
Instagram und, wo vorhanden, TikTok des Artists. Bewusst als Textlinks unter den
Streaming-Buttons und nicht als weiterer grosser Button: die Seite hat eine Aufgabe,
naemlich zur Musik zu fuehren, und jeder gleichrangige Knopf daneben kostet davon Klicks.
Aus demselben Grund steht dort KEIN Label-Instagram (Christians Frage vom 11.08.):
das Geisburg-Logo im Fuss verlinkt bereits aufs Label, ein zweiter Label-Link wuerde nur
mit dem Artist-Link konkurrieren, dem die Aufmerksamkeit hier gehoert.
Bei Mehrfach-Artists ("A & B", "A feat. B") bekommt jeder genannte Artist mit Handle
seinen eigenen Link.

Aufruf: python3 tools/generate_listen_pages.py  (danach generate_index.py + push)
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import hashlib as _h
CSSV = _h.md5((ROOT / "style.css").read_bytes()).hexdigest()[:8]

# Christians Reihenfolge (30.07. nachts): Spotify, Apple Music, Bandcamp, SoundCloud — dann Rest
# (31.07.: + YouTube/Deezer/Amazon unten; Musikvideo als hervorgehobener Extra-Button oben)
SERVICES = [
    ("spotify", "Spotify"),
    ("applemusic", "Apple Music"),
    ("bandcamp_url", "Bandcamp"),
    ("soundcloud", "SoundCloud"),
    ("youtube", "YouTube"),
    ("deezer", "Deezer"),
    ("amazonmusic", "Amazon Music"),
    ("musicvideo", "Music Video"),
]


def socials_fuer(name: str, tabelle: dict):
    """Handles aller im Artist-Feld genannten Acts, in der genannten Reihenfolge.
    'Shlomes feat. DJ Krille' liefert also beide, sofern beide hinterlegt sind."""
    treffer, gesehen = [], set()
    teile = [name] + re.split(r",|\s+&\s+|\s+feat\.?\s+|\s+x\s+|\s+and\s+", name)
    for teil in teile:
        teil = teil.strip()
        if not teil:
            continue
        for schluessel, eintrag in tabelle.items():
            if schluessel.startswith("_") or schluessel.lower() != teil.lower():
                continue
            if schluessel.lower() in gesehen:
                continue
            gesehen.add(schluessel.lower())
            treffer.append((teil, eintrag))
    return treffer


def folgen_zeile(name: str, tabelle: dict) -> str:
    eintraege = socials_fuer(name, tabelle)
    if not eintraege:
        return ""
    stuecke = []
    for act, e in eintraege:
        links = []
        if e.get("instagram"):
            links.append(f'<a href="https://instagram.com/{html.escape(e["instagram"])}">Instagram</a>')
        if e.get("tiktok"):
            links.append(f'<a href="https://tiktok.com/@{html.escape(e["tiktok"])}">TikTok</a>')
        if not links:
            continue
        vorsatz = f"{html.escape(act)} " if len(eintraege) > 1 else ""
        stuecke.append(vorsatz + " · ".join(links))
    if not stuecke:
        return ""
    return ('\n        <div class="follow">follow '
            + " &nbsp;|&nbsp; ".join(stuecke) + "</div>")


def main():
    d = json.loads((ROOT / "data" / "releases.json").read_text())
    socials = json.loads((ROOT / "data" / "artist_socials.json").read_text())
    out_dir = ROOT / "listen"
    out_dir.mkdir(exist_ok=True)
    n_pages = 0
    for r in d["releases"]:
        slug = r["slug"]
        buttons = "\n".join(
            f'            <a class="listen-btn{" listen-btn-small" if f == "musicvideo" else ""}" href="{html.escape(r[f])}">{label}</a>'
            for f, label in SERVICES if r.get(f)
        )
        if not buttons:
            if r.get("presave"):
                buttons = f'            <a class="listen-btn" href="{html.escape(r["presave"])}">Pre-Save</a>'
            else:
                buttons = '            <p class="listen-note">coming soon</p>'
        folgen = folgen_zeile(r["artist"], socials)
        page = f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="../style.css?v={CSSV}">
    <title>{html.escape(r['title'])} — {html.escape(r['artist'])} | GEISBURG RECORDS</title>
</head>

<body>
    <main class="listen-page">
        <div class="listen-title">{html.escape(r['title'])}</div>
        <div class="listen-artist">{html.escape(r['artist'])}</div>
        <img class="listen-cover" src="../{html.escape(r['cover'])}" alt="Cover">
        <div class="listen-buttons">
{buttons}
        </div>{folgen}
    </main>
    <div class="impressum">
        <a href="../index.html"><img class="listen-footer-logo" src="../assets/logo-upscaled-hochgeschoben.png" alt="Geisburg Records"></a>
    </div>
</body>

</html>
"""
        (out_dir / f"{slug}.html").write_text(page)
        n_pages += 1
    print(f"{n_pages} listen-Seiten geschrieben")


if __name__ == "__main__":
    main()
