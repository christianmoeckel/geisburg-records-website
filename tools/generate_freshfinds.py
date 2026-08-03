#!/usr/bin/env python3
"""Fresh-Finds-Playlist-Landing (Christian 03.08., v2): Nachbau der SubmitHub-Link-Seite
auf eigener Domain. Pixel-Code 1:1 wie SubmitHub (autoConfig aus, optOut ESTRuleEngine,
eventID auf PageView UND ViewContent — die eventID ist der Dedup-Schlüssel zur Conversions
API). Meta-Ads laufen auf die Seite; bestehende Custom Audiences matchen weiter
(gleiche Pixel-ID + gleicher content_name 'fresh-finds-berlin-1').

Conversions API: SubmitHub schickt Klicks zusätzlich server-seitig (eigener /api-Beacon).
GitHub Pages hat keinen Server → unser Beacon ist vorbereitet, aber AUS, bis der Relay
auf dem HQ-Server steht (geisburg-pipeline/server/capi_relay.py; dann CAPI_ENDPOINT
z. B. auf 'https://capi.geisburgrecords.com/e' setzen und neu generieren).

Schreibt freshfinds.html + freshfinds/index.html. Aufruf: python3 tools/generate_freshfinds.py
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSSV = hashlib.md5((ROOT / "style.css").read_bytes()).hexdigest()[:8]

PLAYLIST_URL = "https://open.spotify.com/playlist/1owAFr1EJkehkSdwPWNy9g"
PIXEL_ID = "1337510651776548"          # Meta-Pixel, gleiche ID wie im SubmitHub-Link
CONTENT_NAME = "fresh-finds-berlin-1"  # SubmitHub-Signatur beibehalten (Audience-Kontinuität)
COVER = "assets/freshfinds_cover.jpg"
SUBTITLE = "only underground berlin sounds"
CAPI_ENDPOINT = ""                     # leer = Server-Beacon aus; HQ-Relay-URL eintragen sobald deployed


def page(prefix: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="{prefix}style.css?v={CSSV}">
    <title>FRESH FINDS ~ Berlin | GEISBURG RECORDS</title>
    <meta property="og:title" content="FRESH FINDS ~ Berlin">
    <meta property="og:description" content="{SUBTITLE}">
    <meta property="og:type" content="website">
    <meta property="og:image" content="https://geisburgrecords.com/{COVER}">
    <script>
        !function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
        n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;
        n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
        t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,
        document,'script','https://connect.facebook.net/en_US/fbevents.js');
        // Event-IDs im SubmitHub-Format (17 alphanumerische Zeichen) — Dedup-Schlüssel für die Conversions API
        function evid() {{
            var c = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', s = '';
            for (var i = 0; i < 17; i++) s += c.charAt(Math.floor(Math.random() * c.length));
            return s;
        }}
        var CAPI = '{CAPI_ENDPOINT}';
        function beacon(name, id, extra) {{
            if (!CAPI) return;
            var m = document.cookie.match(/_fbp=([^;]+)/), fbc = document.cookie.match(/_fbc=([^;]+)/);
            var payload = {{event_name: name, event_id: id, event_source_url: location.href,
                           fbp: m ? m[1] : null, fbc: fbc ? fbc[1] : null, extra: extra || null}};
            navigator.sendBeacon(CAPI, new Blob([JSON.stringify(payload)], {{type: 'application/json'}}));
        }}
        fbq('set', 'autoConfig', false, '{PIXEL_ID}');
        fbq('optOut', '{PIXEL_ID}', 'ESTRuleEngine');
        fbq('init', '{PIXEL_ID}');
        var pvId = evid();
        fbq('track', 'PageView', {{}}, {{eventID: pvId}});
        beacon('PageView', pvId);
    </script>
    <noscript><img height="1" width="1" style="display:none"
        src="https://www.facebook.com/tr?id={PIXEL_ID}&ev=PageView&noscript=1"></noscript>
</head>

<body>
    <main class="listen-page">
        <div class="listen-title">FRESH FINDS ~ Berlin</div>
        <div class="listen-artist">{SUBTITLE}</div>
        <img class="listen-cover" src="{prefix}{COVER}" alt="FRESH FINDS ~ Berlin Playlist Cover">
        <div class="listen-buttons">
            <a class="listen-btn" id="play" href="{PLAYLIST_URL}">Play on Spotify</a>
        </div>
    </main>
    <div class="impressum">
        <a href="{prefix}index.html"><img class="listen-footer-logo" src="{prefix}assets/logo-upscaled-hochgeschoben.png" alt="Geisburg Records"></a>
    </div>
    <script>
        document.getElementById('play').addEventListener('click', function () {{
            var k = evid();
            fbq('track', 'ViewContent', {{content_name: '{CONTENT_NAME}', content_type: this.getAttribute('href')}}, {{eventID: k}});
            beacon('ViewContent', k, {{content_name: '{CONTENT_NAME}', content_type: this.getAttribute('href')}});
        }});
    </script>
    <script data-goatcounter="https://geisburgrecords.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>

</html>
"""


def main():
    (ROOT / "freshfinds.html").write_text(page(""))
    sub = ROOT / "freshfinds"
    sub.mkdir(exist_ok=True)
    (sub / "index.html").write_text(page("../"))
    print("freshfinds.html + freshfinds/index.html geschrieben (v2)")


if __name__ == "__main__":
    main()
