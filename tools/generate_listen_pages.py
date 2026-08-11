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
# Monochrome Inline-SVGs (currentColor), damit die Icons die Textfarbe erben und
# ohne zusaetzliche Requests auskommen. Pfade sind die offiziellen Markenumrisse,
# einfarbig wiedergegeben (Christian 11.08.: "Icons in monochrom").
ICONS = {
    "spotify": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.5 17.3a.75.75 0 01-1.03.25c-2.82-1.72-6.37-2.11-10.55-1.16a.75.75 0 11-.33-1.46c4.57-1.04 8.5-.59 11.66 1.34a.75.75 0 01.25 1.03zm1.47-3.27a.94.94 0 01-1.29.31c-3.23-1.98-8.15-2.56-11.97-1.4a.94.94 0 11-.54-1.8c4.36-1.32 9.78-.68 13.49 1.6a.94.94 0 01.31 1.29zm.13-3.4C15.23 8.33 8.9 8.12 5.2 9.24a1.12 1.12 0 11-.65-2.15c4.25-1.29 11.24-1.04 15.67 1.59a1.12 1.12 0 11-1.14 1.93z"/></svg>',
    "applemusic": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.99 6.12c0-.51-.05-1.03-.15-1.53a5.07 5.07 0 00-.5-1.4A4.9 4.9 0 0021.2.85a5.6 5.6 0 00-1.4-.5c-.5-.1-1.01-.14-1.52-.15h-12.5c-.51.01-1.02.05-1.52.15a5.6 5.6 0 00-1.4.5A4.9 4.9 0 00.65 3.19c-.22.44-.39.9-.5 1.4-.1.5-.14 1.02-.15 1.53v11.76c.01.51.05 1.03.15 1.53.11.5.28.96.5 1.4a4.9 4.9 0 002.15 2.34c.44.22.9.39 1.4.5.5.1 1.01.14 1.52.15h12.5c.51-.01 1.02-.05 1.52-.15a5.6 5.6 0 001.4-.5 4.9 4.9 0 002.14-2.34c.22-.44.39-.9.5-1.4.1-.5.14-1.02.15-1.53V6.12zM17.3 5.3v10.02c0 .35-.02.7-.1 1.04-.13.54-.42.98-.88 1.29-.35.24-.75.37-1.17.44l-.77.14c-.94.14-1.75-.5-1.83-1.42-.06-.75.4-1.42 1.14-1.63l1.2-.3c.5-.14.75-.44.79-.96V8.05c0-.2-.09-.26-.28-.22l-6.1 1.23c-.17.04-.24.12-.24.3v7.42c0 .35-.03.7-.11 1.04-.13.54-.42.98-.88 1.29-.35.24-.75.37-1.17.44l-.78.14c-.93.14-1.74-.5-1.82-1.42-.07-.75.4-1.42 1.13-1.63.4-.11.8-.2 1.2-.3.5-.14.76-.44.8-.96V6.83c0-.44.2-.7.62-.79l8.6-1.73c.09-.2.18-.3.27-.4.35-.5.68.24.68.62z"/></svg>',
    "bandcamp_url": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M0 18.75l7.437-13.5H24l-7.438 13.5H0z"/></svg>',
    "soundcloud": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M1.18 15.6c-.04 0-.08-.03-.09-.08l-.24-1.83.24-1.87c0-.05.05-.08.1-.08.04 0 .08.03.09.08l.28 1.87-.28 1.83c-.1.05-.5.08-.1.08zm-.9-.83c-.05 0-.09-.04-.1-.09l-.18-1 .19-1.03c0-.5.04-.9.09-.9.05 0 .09.04.1.09l.22 1.03-.22 1c-.1.06-.5.1-.1.1zm1.85.4c-.05 0-.1-.04-.1-.1l-.22-1.4.22-1.47c.01-.6.05-.1.1-.1.06 0 .1.04.11.1l.25 1.47-.25 1.4c-.1.06-.5.1-.1.1zm.94.1c-.06 0-.11-.05-.12-.11l-.2-1.5.2-1.55c0-.6.06-.11.12-.11.06 0 .11.05.12.11l.23 1.55-.23 1.5c-.1.06-.6.11-.12.11zm.96.05c-.07 0-.12-.05-.13-.12l-.19-1.55.19-1.6c0-.7.06-.12.13-.12.06 0 .12.05.13.12l.21 1.6-.21 1.55c-.1.07-.7.12-.13.12zm.97.02c-.07 0-.13-.06-.14-.13l-.18-1.57.18-1.62c.01-.7.07-.13.14-.13.07 0 .13.06.14.13l.2 1.62-.2 1.57c-.1.07-.7.13-.14.13zm1-.01c-.08 0-.14-.06-.15-.14l-.17-1.56.17-1.6c.01-.8.07-.14.15-.14.07 0 .14.06.15.14l.19 1.6-.19 1.56c-.1.08-.8.14-.15.14zm1-.03c-.08 0-.15-.07-.16-.15l-.16-1.53.16-1.58c.01-.8.08-.15.16-.15.08 0 .15.07.16.15l.18 1.58-.18 1.53c-.1.08-.8.15-.16.15zm1.03.55c-.09 0-.16-.07-.17-.16l-.15-2.08.15-4.36c.01-.9.08-.16.17-.16.09 0 .16.07.17.16l.17 4.36-.17 2.08c-.1.09-.8.16-.17.16zm1.04.03c-.1 0-.17-.08-.18-.17l-.14-2.11.14-4.6c.01-.1.08-.17.18-.17.09 0 .17.08.18.17l.16 4.6-.16 2.11c-.1.1-.9.17-.18.17zm1.06.01c-.1 0-.18-.08-.19-.18l-.13-2.12.13-4.7c.01-.1.09-.18.19-.18.1 0 .18.08.19.18l.15 4.7-.15 2.12c-.1.1-.9.18-.19.18zm1.08.01c-.11 0-.19-.09-.2-.19l-.13-2.13.13-4.66c.01-.1.09-.19.2-.19.1 0 .19.09.2.19l.14 4.66-.14 2.13c-.1.1-.9.19-.2.19zm1.09 0c-.11 0-.2-.09-.21-.2l-.12-2.12.12-4.5c.01-.11.1-.2.21-.2.11 0 .2.09.21.2l.14 4.5-.14 2.12c-.1.11-.1.2-.21.2zM24 13.98c0 1.1-.9 2-2 2h-8.02a.35.35 0 01-.35-.35V7.6c0-.17.08-.28.24-.34.42-.16.9-.25 1.4-.25 2.15 0 3.93 1.6 4.2 3.68.35-.15.74-.23 1.14-.23 1.55 0 2.81 1.26 2.81 2.81 0 .24-.3.47-.8.7z"/></svg>',
    "youtube": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.5 6.2a3 3 0 00-2.12-2.12C19.5 3.55 12 3.55 12 3.55s-7.5 0-9.38.53A3 3 0 00.5 6.2C0 8.07 0 12 0 12s0 3.93.5 5.8a3 3 0 002.12 2.12c1.88.53 9.38.53 9.38.53s7.5 0 9.38-.53a3 3 0 002.12-2.12C24 15.93 24 12 24 12s0-3.93-.5-5.8zM9.6 15.6V8.4l6.2 3.6-6.2 3.6z"/></svg>',
    "deezer": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.81 4.16h5.19v2.7h-5.19v-2.7zm0 3.94h5.19v2.7h-5.19V8.1zm0 3.95h5.19v2.7h-5.19v-2.7zm-6.2 0h5.18v2.7H12.6v-2.7zm0 3.94h5.18v2.7H12.6v-2.7zm-6.21 0h5.19v2.7H6.4v-2.7zm-6.4 0h5.19v2.7H0v-2.7zm18.81 0h5.19v2.7h-5.19v-2.7zm-6.2-7.89h5.18v2.7H12.6V8.1z"/></svg>',
    "amazonmusic": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.42 17.6c-1.9 1.4-4.65 2.15-7.02 2.15-3.32 0-6.31-1.23-8.57-3.27-.18-.16-.02-.38.19-.26 2.44 1.42 5.46 2.28 8.58 2.28 2.1 0 4.42-.44 6.55-1.34.32-.14.59.21.27.44zm.79-.9c-.24-.31-1.6-.15-2.22-.07-.18.02-.21-.14-.05-.26 1.09-.76 2.87-.54 3.08-.29.21.26-.06 2.04-1.08 2.89-.16.13-.3.06-.24-.11.22-.57.7-1.85.51-2.16zM16.65 6.9V5.85c0-.16.12-.27.27-.27h4.7c.15 0 .28.11.28.27v.9c0 .15-.13.35-.36.67l-2.44 3.47c.9-.02 1.86.12 2.68.58.18.11.23.26.25.42v1.12c0 .16-.17.34-.35.25-1.44-.76-3.35-.84-4.95.01-.16.09-.34-.1-.34-.25v-1.06c0-.17 0-.47.18-.74l2.82-4.05h-2.46c-.15 0-.28-.11-.28-.27zM8.13 14.4H6.7a.27.27 0 01-.26-.24V5.87c0-.14.12-.26.27-.26h1.33c.14 0 .25.11.26.24v1.09h.03c.35-.93 1-1.36 1.87-1.36.89 0 1.44.43 1.84 1.36.35-.93 1.13-1.36 1.97-1.36.6 0 1.25.25 1.66.8.46.62.36 1.51.36 2.29v4.61c0 .14-.12.26-.27.26h-1.42a.27.27 0 01-.26-.26V9.4c0-.31.03-1.08-.04-1.37-.11-.49-.43-.63-.84-.63-.35 0-.71.23-.86.6-.15.37-.13 1-.13 1.4v4.14c0 .14-.12.26-.27.26h-1.43a.27.27 0 01-.26-.26V9.4c0-.82.13-2.02-.88-2.02-1.02 0-.98 1.17-.98 2.02v4.14c0 .14-.12.26-.27.26z"/></svg>',
    "musicvideo": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 4h16a2 2 0 012 2v12a2 2 0 01-2 2H4a2 2 0 01-2-2V6a2 2 0 012-2zm5.5 4v8l6-4-6-4z"/></svg>',
    "instagram": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.16c3.2 0 3.58.01 4.85.07 1.17.05 1.8.25 2.23.41.56.22.96.48 1.38.9.42.42.68.82.9 1.38.16.42.36 1.06.41 2.23.06 1.27.07 1.65.07 4.85s-.01 3.58-.07 4.85c-.05 1.17-.25 1.8-.41 2.23-.22.56-.48.96-.9 1.38-.42.42-.82.68-1.38.9-.42.16-1.06.36-2.23.41-1.27.06-1.65.07-4.85.07s-3.58-.01-4.85-.07c-1.17-.05-1.8-.25-2.23-.41a3.7 3.7 0 01-1.38-.9 3.7 3.7 0 01-.9-1.38c-.16-.42-.36-1.06-.41-2.23-.06-1.27-.07-1.65-.07-4.85s.01-3.58.07-4.85c.05-1.17.25-1.8.41-2.23.22-.56.48-.96.9-1.38.42-.42.82-.68 1.38-.9.42-.16 1.06-.36 2.23-.41C8.42 2.17 8.8 2.16 12 2.16zM12 0C8.74 0 8.33.01 7.05.07 5.78.13 4.9.33 4.14.63a5.9 5.9 0 00-2.13 1.38A5.9 5.9 0 00.63 4.14c-.3.76-.5 1.64-.56 2.9C.01 8.33 0 8.74 0 12s.01 3.67.07 4.95c.06 1.27.26 2.15.56 2.91.31.79.72 1.46 1.38 2.13a5.9 5.9 0 002.13 1.38c.76.3 1.64.5 2.91.56C8.33 23.99 8.74 24 12 24s3.67-.01 4.95-.07c1.27-.06 2.15-.26 2.91-.56a5.9 5.9 0 002.13-1.38 5.9 5.9 0 001.38-2.13c.3-.76.5-1.64.56-2.91.06-1.28.07-1.69.07-4.95s-.01-3.67-.07-4.95c-.06-1.27-.26-2.15-.56-2.91a5.9 5.9 0 00-1.38-2.13A5.9 5.9 0 0019.86.63c-.76-.3-1.64-.5-2.91-.56C15.67.01 15.26 0 12 0zm0 5.84a6.16 6.16 0 100 12.32 6.16 6.16 0 000-12.32zM12 16a4 4 0 110-8 4 4 0 010 8zm7.85-10.41a1.44 1.44 0 11-2.88 0 1.44 1.44 0 012.88 0z"/></svg>',
    "tiktok": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 013.16-4.51V9.4a6.33 6.33 0 00-5.4 10.71 6.33 6.33 0 0010.86-4.43V8.69a8.16 8.16 0 004.77 1.52V6.69z"/></svg>',
}

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
            links.append(f'<a class="soc" href="https://instagram.com/{html.escape(e["instagram"])}" '
                         f'aria-label="{html.escape(act)} auf Instagram" title="Instagram">{ICONS["instagram"]}</a>')
        if e.get("tiktok"):
            links.append(f'<a class="soc" href="https://tiktok.com/@{html.escape(e["tiktok"])}" '
                         f'aria-label="{html.escape(act)} auf TikTok" title="TikTok">{ICONS["tiktok"]}</a>')
        if not links:
            continue
        vorsatz = f"{html.escape(act)} " if len(eintraege) > 1 else ""
        stuecke.append(vorsatz + "".join(links))
    if not stuecke:
        return ""
    return ('\n        <div class="follow">'
            + '<span class="follow-sep"></span>'.join(stuecke) + "</div>")


def main():
    d = json.loads((ROOT / "data" / "releases.json").read_text())
    socials = json.loads((ROOT / "data" / "artist_socials.json").read_text())
    out_dir = ROOT / "listen"
    out_dir.mkdir(exist_ok=True)
    n_pages = 0
    for r in d["releases"]:
        slug = r["slug"]
        buttons = "\n".join(
            f'            <a class="listen-btn{" listen-btn-small" if f == "musicvideo" else ""}" '
            f'href="{html.escape(r[f])}"><span class="ic">{ICONS.get(f, "")}</span>{label}</a>'
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
