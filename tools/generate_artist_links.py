#!/usr/bin/env python3
"""Erzeugt die Link-in-Bio-Seite eines ARTISTS (Christian 26.08.2026, zuerst bland & pale).

Gegenstueck zu generate_links_page.py, das dasselbe fuer das Label tut. Quelle ist
data/artist_links.json; die Reihenfolge der Eintraege dort ist die Reihenfolge auf der
Seite, weil bei einer Bio-Seite die oberste Zeile den Grossteil der Klicks bekommt.

Aufbau (Christian 27.08.): oben NUR der Artist-Name, darunter der Release und die Links,
das Geisburg-Logo klein als Fussnote unten. Kein Untertitel unter dem Namen und kein Label-
Logo im Kopf: die Seite gehoert dem Artist, das Label steht darunter. Der Untertitel bleibt
in den og-Metadaten, damit die Vorschau beim Teilen etwas hergibt.

Zwei weitere Entscheidungen, die hier bewusst so getroffen sind:

1. Der Release oben verlinkt IMMER auf die eigene Listen-Page, nie direkt auf Spotify und
   nie auf den Pre-Save. Vor Erscheinen zeigt die Listen-Page den Pre-Save, danach alle
   Streaming-Buttons. Der Link im Instagram-Profil bleibt damit gueltig, ohne dass ihn
   jemand am Release-Tag nachzieht. Ein Pre-Save-Link im Profil ist zwei Tage spaeter eine
   Sackgasse, und genau das faellt niemandem auf.

2. Das Etikett auf der Karte kommt aus dem Release-Datum, nicht aus der Datei. Steht in
   releases.json noch eine 'note' wie "out 27.08.2026" und liegt das Datum in der Zukunft,
   heisst die Karte "OUT 27.08."; ab dem Tag selbst "NEW SINGLE". Sonst muesste jemand
   daran denken, und niemand denkt daran.

Aufruf: python3 tools/generate_artist_links.py
Schreibt <slug>.html und <slug>/index.html je Artist.
"""
import hashlib
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSSV = hashlib.md5((ROOT / "style.css").read_bytes()).hexdigest()[:8]

# Icons aus dem Listen-Generator uebernehmen, damit es nur eine Quelle dafuer gibt.
import importlib.util
_spec = importlib.util.spec_from_file_location("_gl", Path(__file__).parent / "generate_listen_pages.py")
_gl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gl)
ICONS = _gl.ICONS


def release_etikett(rel: dict):
    """(Etikett, ist_vorab) aus der note-Angabe des Releases."""
    note = str(rel.get("note") or "")
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", note)
    if m:
        tag, monat, jahr = (int(x) for x in m.groups())
        erscheint = date(jahr, monat, tag)
        if erscheint > date.today():
            return f"OUT {tag:02d}.{monat:02d}.", True
    return "NEW SINGLE", False


def seite(a: dict, rel: dict, prefix: str) -> str:
    etikett, vorab = release_etikett(rel)
    untertitel = "pre-save now" if vorab else "listen everywhere"
    knoepfe = "\n".join(
        f'            <a class="listen-btn bio-btn" href="{html.escape(l["url"])}">'
        f'<span class="ic">{ICONS.get(l.get("icon"), "")}</span>{html.escape(l["label"])}</a>'
        for l in a["links"])
    return f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="{prefix}style.css?v={CSSV}">
    <title>{html.escape(a["artist"])} | GEISBURG RECORDS</title>
    <meta property="og:title" content="{html.escape(a["artist"])}">
    <meta property="og:description" content="{html.escape(a.get("subtitle") or "")}">
    <meta property="og:type" content="website">
    <meta property="og:image" content="https://geisburgrecords.com/{html.escape(rel["cover"])}">
</head>

<body>
    <main class="listen-page">
        <div class="listen-title">{html.escape(a["artist"])}</div>
        <a class="bio-release" href="{prefix}listen/{rel["slug"]}.html">
            <img src="{prefix}{html.escape(rel["cover"])}" alt="Cover {html.escape(rel["title"])}">
            <div>
                <div class="bio-tag">{etikett}</div>
                <div class="bio-release-title">{html.escape(rel["title"])}</div>
                <div class="bio-release-sub">{untertitel}</div>
            </div>
        </a>
        <div class="listen-buttons">
{knoepfe}
        </div>
    </main>
    <div class="impressum">
        <a href="{prefix}index.html"><img class="listen-footer-logo" src="{prefix}assets/logo-upscaled-hochgeschoben.png" alt="Geisburg Records"></a>
    </div>
</body>

</html>
"""


def main():
    daten = json.loads((ROOT / "data" / "artist_links.json").read_text())
    releases = json.loads((ROOT / "data" / "releases.json").read_text())["releases"]
    for a in daten["artists"]:
        treffer = [r for r in releases if r["slug"] == a["release"]]
        if not treffer:
            raise SystemExit(f"Release '{a['release']}' steht nicht in releases.json")
        rel = treffer[0]
        (ROOT / f"{a['slug']}.html").write_text(seite(a, rel, ""))
        unter = ROOT / a["slug"]
        unter.mkdir(exist_ok=True)
        (unter / "index.html").write_text(seite(a, rel, "../"))
        etikett, _ = release_etikett(rel)
        print(f"{a['slug']}.html + {a['slug']}/index.html — {rel['title']} [{etikett}] "
              f"+ {len(a['links'])} Links")


if __name__ == "__main__":
    main()
