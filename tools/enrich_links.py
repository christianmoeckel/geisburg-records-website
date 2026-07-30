#!/usr/bin/env python3
"""Ergänzt data/releases.json einmalig um songlink-URLs (song.link/album.link via iTunes-IDs).

- Nur Einträge OHNE vorhandenes "songlink"-Feld werden nachgeschlagen (idempotent).
- "match_query" im Eintrag überschreibt die Suchanfrage, "songlink": null erzwingt "keiner".
Aufruf: python3 tools/enrich_links.py [--dry]
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def norm_words(t):
    return set(re.sub(r"[^a-z0-9]+", " ", t.lower().replace("&", " ")).split())


def clean_query(q):
    return re.sub(r"\s+", " ", q.replace("&", " ").replace(",", " ").replace("'", "")).strip()


def lookup(query, want_artist):
    query = clean_query(query)
    want = norm_words(want_artist)
    for entity in ("song", "album"):
        url = ("https://itunes.apple.com/search?term=" + urllib.parse.quote(query)
               + f"&entity={entity}&limit=8&country=DE")
        with urllib.request.urlopen(url, timeout=20) as f:
            data = json.load(f)
        for r in data.get("results", []):
            got = norm_words(r.get("artistName", ""))
            if want & got:
                if r.get("wrapperType") == "collection":
                    return f"https://album.link/i/{r['collectionId']}"
                if r.get("trackId"):
                    return f"https://song.link/i/{r['trackId']}"
        time.sleep(1.0)
    return None


def main():
    dry = "--dry" in sys.argv
    p = ROOT / "data" / "releases.json"
    d = json.loads(p.read_text())
    changed = 0
    for r in d["releases"]:
        if "songlink" in r:
            continue
        q = r.get("match_query", f"{r['artist']} {r['title']}")
        try:
            link = lookup(q, r["artist"])
        except Exception as e:
            print(f"WARN {r['title']}: {e}")
            continue
        r["songlink"] = link
        changed += 1
        print(("✓ " if link else "— ") + f"{r['title']} → {link or 'kein Store-Treffer'}")
        time.sleep(1.2)  # iTunes-API-Rate schonen
    if not dry and changed:
        p.write_text(json.dumps(d, indent=2, ensure_ascii=False))
        print(f"{changed} Einträge aktualisiert.")


if __name__ == "__main__":
    main()
