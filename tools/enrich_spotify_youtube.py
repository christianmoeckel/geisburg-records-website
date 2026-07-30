#!/usr/bin/env python3
"""Nachtjob: Spotify- + YouTube-Track-Links via Odesli, Einstieg über die Deezer-URL
(ISRC-exakt → bester Match; Christians Anforderung: Spotify-Link muss auf den TRACK zeigen).
Idempotent (überspringt Einträge mit spotify-Feld), 429-Backoff, ~12s-Takt.
Aufruf: python3 tools/enrich_spotify_youtube.py
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.song.link/v1-alpha.1/links?userCountry=DE&url="


def fetch(u):
    req = urllib.request.Request(API + urllib.parse.quote(u, safe=""),
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as f:
        return json.load(f)


def main():
    p = ROOT / "data" / "releases.json"
    d = json.loads(p.read_text())
    changed = 0
    for r in d["releases"]:
        src = r.get("deezer") or r.get("applemusic")
        if not src or r.get("spotify"):
            continue
        data = None
        for attempt in range(4):
            try:
                data = fetch(src)
                break
            except Exception as e:
                if "429" in str(e):
                    time.sleep(240)
                else:
                    print(f"WARN {r['title']}: {e}")
                    break
        if not data:
            time.sleep(12)
            continue
        links = data.get("linksByPlatform", {})
        sp = (links.get("spotify") or {}).get("url")
        yt = (links.get("youtube") or links.get("youtubeMusic") or {}).get("url")
        if sp: r["spotify"] = sp
        if yt and not r.get("youtube"): r["youtube"] = yt
        changed += 1
        print(f"{'✓' if sp else '—'}S {'✓' if yt else '—'}Y  {r['title']}", flush=True)
        p.write_text(json.dumps(d, indent=2, ensure_ascii=False))  # inkrementell sichern
        time.sleep(12)
    print(f"{changed} Einträge verarbeitet.")


if __name__ == "__main__":
    main()
