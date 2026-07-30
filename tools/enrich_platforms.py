#!/usr/bin/env python3
"""Ergänzt releases.json um direkte Plattform-Links (spotify, applemusic) via Odesli-API.

Nutzt das vorhandene "songlink"-Feld (song.link/i/<id> bzw. album.link/i/<id>) als Einstieg.
Idempotent: Einträge, die schon "spotify" ODER "applemusic" haben, werden übersprungen.
Aufruf: python3 tools/enrich_platforms.py
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.song.link/v1-alpha.1/links?userCountry=DE&url="


def fetch(itunes_url):
    req = urllib.request.Request(API + urllib.parse.quote(itunes_url, safe=""),
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as f:
        return json.load(f)


def main():
    p = ROOT / "data" / "releases.json"
    d = json.loads(p.read_text())
    changed = 0
    for r in d["releases"]:
        sl = r.get("songlink")
        if not sl or ("spotify" in r or "applemusic" in r):
            continue
        m = re.search(r"(song|album)\.link/i/(\d+)", sl)
        if not m:
            continue
        kind = "album" if m.group(1) == "album" else "song"
        itunes_url = (f"https://music.apple.com/de/{'album' if kind == 'album' else 'song'}/{m.group(2)}"
                      if kind == "album" else f"https://music.apple.com/de/song/{m.group(2)}")
        try:
            data = fetch(itunes_url)
        except Exception as e:
            print(f"WARN {r['title']}: {e}")
            time.sleep(8)
            continue
        links = data.get("linksByPlatform", {})
        sp = (links.get("spotify") or {}).get("url")
        am = (links.get("appleMusic") or {}).get("url")
        if sp: r["spotify"] = sp
        if am: r["applemusic"] = am
        if data.get("pageUrl"): r["songlink"] = data["pageUrl"]
        changed += 1
        print(f"{'✓' if sp else '—'}S {'✓' if am else '—'}A  {r['title']}")
        time.sleep(6.5)  # Odesli ~10 req/min ohne Key
    if changed:
        p.write_text(json.dumps(d, indent=2, ensure_ascii=False))
        print(f"{changed} Einträge angereichert.")


if __name__ == "__main__":
    main()
