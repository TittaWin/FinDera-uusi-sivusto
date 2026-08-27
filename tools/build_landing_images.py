#!/usr/bin/env python3
"""
FinDera - laskeutumissivun (landing1.html) kuvaputki.

Lahde: kansio "Landing Pages". Paakuva ja Martinin kuva ovat omina
tiedostoinaan; loput on irrotettu kuvakollaasista skriptin alussa maaritellyilla
pikselirajoilla (kollaasin valkoiset erotinviivat).

Ajo:  python3 tools/build_landing_images.py

Tulos: assets/img/lp-*.webp (+ jpg-varmistus). Tiedostot ovat valmiiksi
oikean kokoisia, joten selain ei lataa turhaa dataa.
"""
from PIL import Image, ImageOps
import os

SRC = "/Users/titta/Documents/FinDera/Landing Pages"
DST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets", "img")

# --- Kollaasin ruutujen rajat -----------------------------------------------
# (vasen, ylä, oikea, ala) alkuperäisessä kuvakollaasi.png-tiedostossa.
# Rajat on haettu automaattisesti ruutujen välisistä valkoisista viivoista ja
# kavennettu 2 pikselia joka reunasta, jotta valkoista ei jaa nakyviin.
KOLLAASI = "kuvakollaasi.png"
RUUDUT = {
    "lp-band":            (7, 286, 1758, 490),   # tuulivoima-kukkulat, leveä kaista
    "lp-aihe-kierto":     (6, 499, 438, 681),    # kiertotalous & materiaalit
    "lp-aihe-energia":  (446, 499, 878, 681),    # energia & vihreä siirtymä
    "lp-aihe-rakennus": (886, 499, 1318, 681),   # rakennettu ympäristö
    "lp-aihe-teknologia": (1326, 499, 1758, 681),# uudet teknologiat
}

# --- Omat tiedostot ---------------------------------------------------------
# slug -> (tiedosto, kuvasuhde tai None, rajauksen painopiste pystysuunnassa)
OMAT = {
    "lp-hero":   ("ensimmäinen kuva_bechmarking vierailu.png", None, 0.5),
    "lp-martin": ("Martin.JPG",                                3 / 4, 0.30),
}

# --- Muista kansioista poimitut kuvat ---------------------------------------
# Ryhman oppimisymparistoa kasitteleva osio kayttaa samaa ravintolakuvaa kuin
# etusivun galleria (illat-3), mutta omana, leveampana rajauksenaan.
# slug -> (koko polku, kuvasuhde tai None, rajauksen painopiste pystysuunnassa)
MUUALTA = {
    "lp-ryhma": ("/Users/titta/Documents/FinDera/Ravintolaillat/"
                 "20240410_122743.jpg", 4 / 3, 0.50),
}

# --- Leveydet rooleittain ---------------------------------------------------
LEVEYDET = {
    "lp-hero":   [1600, 1200, 800],
    "lp-band":   [1600, 1200, 800],
    "lp-martin": [900, 560],
    "lp-ryhma":  [1000, 600],
    "aihe":      [430, 300],
}


def crop_to(im, ratio, focus_y=0.42):
    """Rajaa kuvasuhteeseen. focus_y: 0 = ylareunasta, 1 = alareunasta."""
    w, h = im.size
    if abs(w / h - ratio) < 0.005:
        return im
    if w / h > ratio:                       # liian leveä -> kavennetaan
        nw = int(round(h * ratio))
        left = (w - nw) // 2
        return im.crop((left, 0, left + nw, h))
    nh = int(round(w / ratio))              # liian korkea -> madalletaan
    top = max(0, min(h - nh, int(round((h - nh) * focus_y))))
    return im.crop((0, top, w, top + nh))


def tallenna(im, slug, leveydet):
    """Kirjoittaa WebP-versiot ja yhden jpg-varmistuksen."""
    tehdyt = []
    for w in leveydet:
        if w > im.width:                    # ei suurenneta koskaan
            w = im.width
        h = int(round(im.height * w / im.width))
        out = im.resize((w, h), Image.LANCZOS)
        polku = os.path.join(DST, f"{slug}-{w}.webp")
        out.save(polku, "WEBP", quality=82, method=6)
        tehdyt.append((w, h))
    fb_w, fb_h = tehdyt[0]
    im.resize((fb_w, fb_h), Image.LANCZOS).save(
        os.path.join(DST, f"{slug}.jpg"), "JPEG", quality=80,
        optimize=True, progressive=True)
    print(f"  {slug:<20} {' '.join(f'{w}x{h}' for w, h in tehdyt)}")
    return tehdyt


def main():
    print("Kollaasin ruudut:")
    kollaasi = Image.open(os.path.join(SRC, KOLLAASI)).convert("RGB")
    for slug, laatikko in RUUDUT.items():
        ruutu = kollaasi.crop(laatikko)
        tallenna(ruutu, slug, LEVEYDET.get(slug, LEVEYDET["aihe"]))

    print("Omat tiedostot:")
    for slug, (tiedosto, suhde, focus) in OMAT.items():
        im = ImageOps.exif_transpose(
            Image.open(os.path.join(SRC, tiedosto))).convert("RGB")
        if suhde:
            im = crop_to(im, suhde, focus)
        tallenna(im, slug, LEVEYDET[slug])

    print("Muista kansioista:")
    for slug, (polku, suhde, focus) in MUUALTA.items():
        im = ImageOps.exif_transpose(Image.open(polku)).convert("RGB")
        if suhde:
            im = crop_to(im, suhde, focus)
        tallenna(im, slug, LEVEYDET[slug])


if __name__ == "__main__":
    main()
