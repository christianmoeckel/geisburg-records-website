#!/usr/bin/env python3
"""Fresh-Finds-Playlist-Landing (Christian 03.08.): Nachbau der SubmitHub-Link-Seite
(submithub.com/link/fresh-finds-berlin-1) auf der eigenen Domain — Cover, Play-Button,
Meta-Pixel. Pixel-Events EXAKT wie bei SubmitHub (PageView + ViewContent mit
content_name 'fresh-finds-berlin-1'), damit bestehende Meta-Custom-Audiences ohne
Neuaufbau weitermatchen. Dazu GoatCounter wie auf der Bio-Page.

Schreibt freshfinds.html + freshfinds/index.html (URL: geisburgrecords.com/freshfinds).
Aufruf: python3 tools/generate_freshfinds.py
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSSV = hashlib.md5((ROOT / "style.css").read_bytes()).hexdigest()[:8]

PLAYLIST_URL = "https://open.spotify.com/playlist/1owAFr1EJkehkSdwPWNy9g"
PIXEL_ID = "1337510651776548"          # Meta-Pixel, gleiche ID wie im SubmitHub-Link
CONTENT_NAME = "fresh-finds-berlin-1"  # SubmitHub-Signatur beibehalten (Audience-Kontinuität)
COVER = "assets/freshfinds_cover.jpg"


def page(prefix: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="{prefix}style.css?v={CSSV}">
    <title>FRESH FINDS ~ Berlin | GEISBURG RECORDS</title>
    <meta property="og:title" content="FRESH FINDS ~ Berlin">
    <meta property="og:description" content="Weekly Berlin Song Selection by Geisburg Records">
    <meta property="og:type" content="website">
    <meta property="og:image" content="https://geisburgrecords.com/{COVER}">
    <script>
        !function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
        n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;
        n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
        t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,
        document,'script','https://connect.facebook.net/en_US/fbevents.js');
        fbq('init','{PIXEL_ID}');
        fbq('track','PageView');
    </script>
    <noscript><img height="1" width="1" style="display:none"
        src="https://www.facebook.com/tr?id={PIXEL_ID}&ev=PageView&noscript=1"></noscript>
</head>

<body>
    <main class="listen-page">
        <div class="listen-title">FRESH FINDS ~ Berlin</div>
        <div class="listen-artist">Weekly Berlin Song Selection</div>
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
            fbq('track', 'ViewContent', {{content_name: '{CONTENT_NAME}', content_type: this.getAttribute('href')}});
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
    print("freshfinds.html + freshfinds/index.html geschrieben")


if __name__ == "__main__":
    main()
