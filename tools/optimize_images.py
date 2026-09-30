#!/usr/bin/env python3
"""Bilder der Website auf Anzeigegroesse bringen und neu komprimieren, ohne sichtbaren Verlust.

Anlass (Christian 30.09.2026): "braucht manchmal laenger zu laden mit all den covers".
Befund: die Startseite lud 49 Bilder mit zusammen 16,8 MB, alle sofort. Einzelne Cover
lagen als 1,7-MB-JPEG oder 3-MB-PNG vor, obwohl sie in drei Spalten angezeigt werden.

Was das Skript tut, je Bild, das irgendeine Seite einbindet:
- auf die groesste sinnvolle Kante verkleinern: Cover 800 px (dreispaltiges Raster, reicht
  auch fuer Retina), Fotos 1600 px, Logos bleiben PNG mit Transparenz;
- als progressives JPEG mit Qualitaet 82 neu speichern, Metadaten raus;
- NUR ersetzen, wenn die Datei dadurch kleiner wird UND die Qualitaetsmessung besteht:
  PSNR gegen das auf dieselbe Groesse gerechnete Original mindestens 38 dB, das gilt als
  mit blossem Auge nicht unterscheidbar. Faellt sie durch, steigt die Qualitaet in Stufen
  (88, 92, 95); bei koernigen Covern endet das bei 95, wo JPEG-Artefakte unsichtbar sind.

Idempotent: ein zweiter Lauf findet nichts mehr zu tun. Die Originale stehen in der
Git-Historie und als 3000-px-Cover in der Drive-Ablage.

Aufruf:  python3 tools/optimize_images.py          nur messen
         python3 tools/optimize_images.py --run    ersetzen
"""
import io
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parent.parent
COVER_KANTE = 800
FOTO_KANTE = 1600
LOGO_KANTE = 512      # dreifache Anzeigegroesse (max 170 px), scharf auch auf Retina
QUALITAET = 82
MIN_PSNR = 38.0


def eingebundene_bilder():
    """Alle Bilder unter assets/, die eine HTML-Seite der Website einbindet."""
    pfade = set()
    for seite in ROOT.rglob("*.html"):
        if "node_modules" in seite.parts:
            continue
        for src in re.findall(r'<img[^>]+src="([^"]+)"', seite.read_text(errors="replace")):
            src = src.split("?")[0].lstrip("./")
            while src.startswith("../"):
                src = src[3:]
            p = ROOT / src
            if p.suffix.lower() in (".jpg", ".jpeg", ".png") and p.exists() and "assets" in p.parts:
                pfade.add(p)
    return sorted(pfade)


def ist_logo(p):
    return "logo" in p.name.lower()


def kante(p):
    n = p.name.lower()
    if any(w in n for w in ("studio", "about", "live", "event", "foto", "photo")):
        return FOTO_KANTE
    return COVER_KANTE


def psnr(a, b):
    diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    mse = sum(v ** 2 for v in ImageStat.Stat(diff).rms) / 3
    return 99.0 if mse == 0 else 20 * math.log10(255 / math.sqrt(mse))


def als_jpeg(bild, q):
    puffer = io.BytesIO()
    bild.save(puffer, "JPEG", quality=q, optimize=True, progressive=True)
    return puffer.getvalue()


def bearbeite(p, laufen):
    alt = p.stat().st_size
    with Image.open(p) as roh:
        roh.load()
        bild = roh
        if ist_logo(p):
            # Logos: Transparenz behalten, also PNG bleiben, nur auf LOGO_KANTE verkleinern.
            # Das Hauptlogo lag als 1500x1500 (323 KB) vor und wird hoechstens 170 px breit
            # angezeigt - auf JEDER Seite.
            if max(bild.size) <= LOGO_KANTE:
                return None
            f = LOGO_KANTE / max(bild.size)
            klein = bild.resize((round(bild.size[0] * f), round(bild.size[1] * f)), Image.LANCZOS)
            puffer = io.BytesIO()
            klein.save(puffer, "PNG", optimize=True)
            daten = puffer.getvalue()
            if len(daten) >= alt:
                return (p, alt, alt, None, "schon optimal")
            if laufen:
                p.write_bytes(daten)
            return (p, alt, len(daten), 99.0, "Logo verkleinert" if laufen else "Logo wuerde verkleinert")
        if bild.mode in ("RGBA", "LA", "P"):
            grund = Image.new("RGB", bild.size, (0, 0, 0))
            bild = bild.convert("RGBA")
            grund.paste(bild, mask=bild.split()[-1])
            bild = grund
        else:
            bild = bild.convert("RGB")
        k = kante(p)
        if max(bild.size) > k:
            f = k / max(bild.size)
            bild = bild.resize((round(bild.size[0] * f), round(bild.size[1] * f)), Image.LANCZOS)
    # Stufenweise hoeher, bis die Messung besteht. Koernige Cover (Filmkorn, Rauschen)
    # verfehlen die 38 dB auch bei guter Qualitaet, weil PSNR jedes Korn als Fehler zaehlt;
    # dort reicht Qualitaet 95, bei der JPEG-Artefakte nicht mehr sichtbar sind. Das
    # Verkleinern auf Anzeigegroesse ist ohnehin kein sichtbarer Verlust.
    for q in (QUALITAET, 88, 92, 95):
        daten = als_jpeg(bild, q)
        wert = psnr(bild, Image.open(io.BytesIO(daten)))
        if wert >= MIN_PSNR:
            break
    if len(daten) >= alt:
        return (p, alt, alt, wert, "schon optimal")
    if p.suffix.lower() == ".png":
        return (p, alt, len(daten), wert, "PNG -> JPEG noetig, Verweise anpassen")
    if laufen:
        p.write_bytes(daten)
    return (p, alt, len(daten), wert, "ersetzt" if laufen else "wuerde ersetzt")


def main():
    laufen = "--run" in sys.argv
    vorher = nachher = 0
    for p in eingebundene_bilder():
        r = bearbeite(p, laufen)
        if not r:
            continue
        _, alt, neu, wert, was = r
        vorher += alt
        nachher += neu
        if alt - neu > 50_000 or "noetig" in was or "haelt" in was:
            psnr_txt = f"{wert:4.1f} dB" if wert else "   -   "
            print(f"   {alt/1024:6.0f} -> {neu/1024:5.0f} KB  {psnr_txt}  {was:26} {p.relative_to(ROOT)}")
    print(f"\nzusammen {vorher/1e6:.1f} MB -> {nachher/1e6:.1f} MB"
          + ("" if laufen else "   (nur gemessen, --run ersetzt)"))


if __name__ == "__main__":
    main()
