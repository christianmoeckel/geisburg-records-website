#!/usr/bin/env python3
"""Fresh-Finds-Playlist-Landing (Christian 03.08. v2, 06.08. v3): Nachbau der
SubmitHub-Link-Seite auf eigener Domain. Pixel-Code 1:1 wie SubmitHub (autoConfig aus,
optOut ESTRuleEngine, eventID auf PageView UND ViewContent — die eventID ist der
Dedup-Schluessel zur Conversions API). Meta-Ads laufen auf die Seite; bestehende Custom
Audiences matchen weiter (gleiche Pixel-ID + gleicher content_name 'fresh-finds-berlin-1').

v4 (Christian 11.08.): das Newsletter-Feld ist wieder RAUS, die Seite ist wie vorher eine
reine Weiterleitung zur Playlist. Grund ist die Aufgabe der Seite: sie bekommt bezahlten
Meta-Traffic und soll genau eine Handlung ausloesen, den Klick auf Spotify. Ein zweites
Angebot daneben teilt die Aufmerksamkeit und verschlechtert die Conversion, an der die Ads
optimiert werden. Der Aufbau des Feldes steht in der Git-Historie, falls es zurueckkommt.

Weiterhin drin, seit v3:
1. EIGENE TRAFFIC-ZAEHLUNG. Das seit 03.08. eingebundene GoatCounter-Snippet zeigte auf
   einen Account, den es nicht gibt (geprueft: "error 400: no site at this domain"), es
   wurde also nie etwas gezaehlt. Ersetzt durch einen eigenen Zaehler ins webstats-Sheet
   (geisburg-pipeline/apps_script/webstats.gs), der Seitenaufrufe UND Klicks je Ziel
   erfasst. Kein Cookie, keine IP, nur Pfad/Ereignis/Ziel/Herkunftsdomain.
2. ViewContent feuert ausschliesslich auf dem Spotify-Playlist-Link, nirgends sonst.

Conversions API: SubmitHub schickt Klicks zusaetzlich server-seitig (eigener /api-Beacon).
GitHub Pages hat keinen Server, unser Beacon ist vorbereitet aber AUS, bis der Relay auf
dem HQ-Server steht (geisburg-pipeline/server/capi_relay.py; dann CAPI_ENDPOINT auf
'https://capi.geisburgrecords.com/e' setzen und neu generieren).

Schreibt freshfinds.html + freshfinds/index.html. Aufruf: python3 tools/generate_freshfinds.py
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSSV = hashlib.md5((ROOT / "style.css").read_bytes()).hexdigest()[:8]

PLAYLIST_URL = "https://open.spotify.com/playlist/1owAFr1EJkehkSdwPWNy9g"
PIXEL_ID = "1337510651776548"          # Meta-Pixel, gleiche ID wie im SubmitHub-Link
CONTENT_NAME = "fresh-finds-berlin-1"  # SubmitHub-Signatur beibehalten (Audience-Kontinuitaet)
COVER = "assets/freshfinds_cover.jpg"
SUBTITLE = "only underground berlin sounds"
CAPI_ENDPOINT = ""                     # leer = Server-Beacon aus; HQ-Relay-URL eintragen sobald deployed


# Eigener Zaehler. Token ist oeffentlich (steht im Quelltext) und berechtigt nur zum
# Anhaengen einer Statistikzeile, siehe Kommentar in webstats.gs.
STATS_URL = ("https://script.google.com/macros/s/AKfycbwY8N1v8O_fxnK5_En_FlNklsynvnTjid59"
             "Gkeae_lEhmu7HjkrlEkyWfivlMkjU6ACKw/exec")
STATS_TOKEN = "gbr-stats-2026"


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
        // Event-IDs im SubmitHub-Format (17 alphanumerische Zeichen) — Dedup-Schluessel fuer die Conversions API
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
        // Eigene Zaehlung: feuert und vergisst, blockiert nie einen Klick.
        var STATS = '{STATS_URL}?s={STATS_TOKEN}';
        function hit(ereignis, ziel) {{
            try {{
                var b = new Blob([JSON.stringify({{p: location.pathname, e: ereignis,
                                                   t: ziel || '', r: document.referrer || ''}})],
                                 {{type: 'text/plain'}});
                navigator.sendBeacon(STATS, b);
            }} catch (err) {{}}
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
        hit('pageview', '');

        // ViewContent gilt AUSSCHLIESSLICH dem Spotify-Playlist-Link (Christian 06.08.).
        document.getElementById('play').addEventListener('click', function () {{
            var k = evid();
            fbq('track', 'ViewContent', {{content_name: '{CONTENT_NAME}', content_type: this.getAttribute('href')}}, {{eventID: k}});
            beacon('ViewContent', k, {{content_name: '{CONTENT_NAME}', content_type: this.getAttribute('href')}});
            hit('click', 'spotify');
        }});

    </script>
</body>

</html>
"""


def main():
    (ROOT / "freshfinds.html").write_text(page(""))
    sub = ROOT / "freshfinds"
    sub.mkdir(exist_ok=True)
    (sub / "index.html").write_text(page("../"))
    print("freshfinds.html + freshfinds/index.html geschrieben (v4)")


if __name__ == "__main__":
    main()
