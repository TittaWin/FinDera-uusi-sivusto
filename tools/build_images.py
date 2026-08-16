#!/usr/bin/env python3
"""
FinDera — kuvaputki.

Lahteet: "good pictures" -kansio ja referenssikorttien omat kuvat
kansiossa "Referenssikuvat". Tiedosto etsitaan jarjestyksessa naista.
Jokaiselle kuvalle: EXIF-korjaus, rajaus kiinteaan kuvasuhteeseen,
yhtenainen savynkorjaus (valotus, kontrasti, kylläisyys) ja WebP-pakkaus.
"""
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import colorsys, os, shutil

SRC = "/Users/titta/Documents/FinDera/Findera kuvat/good pictures"
SRC_REF = "/Users/titta/Documents/FinDera/Referenssikuvat"
SRC_ILLAT = "/Users/titta/Documents/FinDera/Ravintolaillat"
SOURCES = [SRC, SRC_REF, SRC_ILLAT]
DST = "/Users/titta/Documents/FinDera/Visual Studio - FD/assets/img"

# --- Kuvasuhteet rooleittain ------------------------------------------------
AR_HERO = 16 / 9
AR_CARD = 3 / 2      # palvelu- ja referenssikortit
AR_GAL  = 4 / 3      # gallerian ruudukko (kaikki samat -> tasainen sommittelu)
AR_PORT = 3 / 4      # pystykuva (Martin)

# Etusivun kollaasin ruudut — arvot vastaavat ruutujen todellisia mittasuhteita,
# jotta kuvista ei rajaudu selaimessa enaa mitaan ylimaaraista.
AR_BAND = 2.18       # ylanauha koko leveydelta
AR_WIDE = 1.48       # matalat ruudut
AR_TALL = 0.72       # korkeat ruudut

WIDTHS = {
    "hero": [1920, 1280, 800],
    "card": [1000, 600],
    "gal":  [800, 500],
    "port": [900, 560],
}

# --- Yhtenaistavan kasittelyn tavoitteet ------------------------------------
TARGET_SAT = 0.34        # keskimaarainen kyllaisyys HSV-avaruudessa
TARGET_LUM = 0.475       # keskimaarainen kirkkaus (0-1)
SAT_RANGE  = (0.82, 1.30)
BRI_RANGE  = (0.94, 1.22)


def measure(im):
    """Keskimaarainen kyllaisyys ja kirkkaus pienennetysta kuvasta."""
    small = im.resize((60, 60))
    sat = lum = 0.0
    px = small.load()
    for x in range(60):
        for y in range(60):
            r, g, b = [v / 255 for v in px[x, y]]
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            sat += s
            lum += 0.299 * r + 0.587 * g + 0.114 * b
    n = 3600
    return sat / n, lum / n


def harmonise(im):
    """Tuo kuvan valotus, kontrasti ja kyllaisyys lahelle yhteista tasoa."""
    # 1. Valotuksen normalisointi: leikataan aarimmaiset 0.4 % kummastakin paasta
    im = ImageOps.autocontrast(im, cutoff=(0.4, 0.4), preserve_tone=True)

    sat, lum = measure(im)

    # 2. Kirkkaus kohti tavoitetta (varovaisesti, vain osa erosta)
    bri_factor = 1.0 + (TARGET_LUM - lum) * 1.15
    bri_factor = max(BRI_RANGE[0], min(BRI_RANGE[1], bri_factor))
    im = ImageEnhance.Brightness(im).enhance(bri_factor)

    # 3. Kyllaisyys kohti tavoitetta
    sat_factor = 1.0 if sat < 0.01 else 1.0 + (TARGET_SAT - sat) / max(sat, 0.12) * 0.55
    sat_factor = max(SAT_RANGE[0], min(SAT_RANGE[1], sat_factor))
    im = ImageEnhance.Color(im).enhance(sat_factor)

    # 4. Kevyt kontrastin lisays antaa kuville yhteisen ryhdin
    im = ImageEnhance.Contrast(im).enhance(1.05)
    return im, bri_factor, sat_factor


def crop_to(im, ratio, focus_y=0.42):
    """Rajaa kuvasuhteeseen. focus_y painottaa rajausta yläosaan (ihmiset/kasvot)."""
    w, h = im.size
    cur = w / h
    if abs(cur - ratio) < 0.005:
        return im
    if cur > ratio:                      # liian leveä -> kavennetaan
        nw = int(round(h * ratio))
        left = (w - nw) // 2
        return im.crop((left, 0, left + nw, h))
    nh = int(round(w / ratio))           # liian korkea -> madalletaan
    top = int(round((h - nh) * focus_y))
    top = max(0, min(h - nh, top))
    return im.crop((0, top, w, top + nh))


# Kiintea esirajaus niille kuville, joissa automaattinen keskitys ei riita.
# Arvot ovat pikseleita alkuperaisessa (EXIF-korjatussa) kuvassa.
PRECROP = {
    # Martinin kuva rajataan samaan sommitteluun kuin asiakkaan toimittama versio
    "martin": (321, 1335, 1656, 3046),
}

# --- Kuvakartta: slug -> (tiedosto, rooli, kuvasuhde, rajauksen painopiste) --
MANIFEST = {
    # Etusivun paakuva
    "hero-rotterdam":     ("20240410_114642.jpg",        "hero", AR_HERO, 0.85),

    # Martin — Ajax-stadion (asiakkaan valinta)
    "martin":             ("20190522_142147.jpg",        "port", AR_PORT, 0.50),

    # Palvelut
    "palvelu-matkat":     ("20190405_144405.jpg",        "card", AR_CARD, 0.55),
    "palvelu-tapaamiset": ("20240926_153621.jpg",        "card", AR_CARD, 0.50),
    "palvelu-kartoitus":  ("20240416_160711.jpg",        "card", AR_CARD, 0.62),

    # Referenssit
    # Osalla korteista on oma referenssikuva kansiossa Referenssikuvat/,
    # loput tulevat edelleen "good pictures" -kansiosta.
    "case-rosknroll":     ("Rosk'n Roll_referenssikuva.png",              "card", AR_CARD, 0.55),
    "case-lsjh":          ("20250307_104431.jpg",                        "card", AR_CARD, 0.85),
    "case-seinajoki":     ("20240926_092539.jpg",                        "card", AR_CARD, 0.50),
    "case-ladec":         ("Lahden seudun kierrätys_referenssikuva.png", "card", AR_CARD, 0.60),
    "case-salpakierto":   ("Salpakierto_referenssikuva.png",             "card", AR_CARD, 0.60),
    "case-salaoja":       ("20250415_110936.jpg",                        "card", AR_CARD, 0.55),
    "case-ely":           ("20230525_123954.jpg",                        "card", AR_CARD, 0.80),
    "case-osao":          ("Koulutuskuntayhtymä ASAO_referenssikuva.png","card", AR_CARD, 0.55),
    "case-turkuamk":      ("Turun AMK_referenssikuva.png",               "card", AR_CARD, 0.50),
    "case-muhos":         ("Muhoksen kunta_referenssikuva.png",          "card", AR_CARD, 0.62),

    # Etusivun esittelykuva
    "intro-ryhma":        ("20180525_102657.jpg",        "card", AR_CARD, 0.90),

    # Etusivu, "Miksi paikan päällä" — kollaasi ravintolaillasta.
    # Jarjestys vastaa ruutuja: 1 ylanauha, 2 korkea vasen, 3 matala oikea,
    # 4 korkea oikea, 5 matala vasen.
    "illat-1":            ("hieno ravintola.png",        "gal",  AR_BAND, 0.55),
    "illat-2":            ("musiikki.png",               "gal",  AR_TALL, 0.50),
    "illat-3":            ("oluttuopit.png",             "gal",  AR_WIDE, 0.45),
    "illat-4":            ("ruokahetki.png",             "gal",  AR_TALL, 0.45),
    "illat-5":            ("20240410_122743.jpg",        "gal",  AR_WIDE, 0.55),

    # Galleria — kaikki samassa 4:3-suhteessa, jotta ruudukko on tasainen
    "galleria-1":         ("PL_D95B3192.jpg",            "gal",  AR_GAL, 0.40),
    "galleria-2":         ("20190521_152810.jpg",        "gal",  AR_GAL, 0.38),
    "galleria-3":         ("IMG_4511.JPG",               "gal",  AR_GAL, 0.42),
    "galleria-4":         ("20170825_094032.jpg",        "gal",  AR_GAL, 0.45),
    "galleria-5":         ("20240416_154440.jpg",        "gal",  AR_GAL, 0.90),
    "galleria-6":         ("IMG_1101.JPG",               "gal",  AR_GAL, 0.42),
    "galleria-7":         ("20190405_110141.jpg",        "gal",  AR_GAL, 0.40),
    "galleria-8":         ("20170913_121044.jpg",        "gal",  AR_GAL, 0.40),
}


def main():
    os.makedirs(DST, exist_ok=True)
    # Siivotaan vanhat kuvat, favicon sailytetaan
    for f in os.listdir(DST):
        if f.endswith((".webp", ".jpg", ".json")):
            os.remove(os.path.join(DST, f))

    print(f"{'slug':<20} {'lahde':<28} {'kirkkaus':>9} {'kyll.':>7}")
    print("-" * 70)
    for slug, (fname, role, ratio, focus) in MANIFEST.items():
        path = next((p for p in (os.path.join(d, fname) for d in SOURCES)
                     if os.path.exists(p)), None)
        if path is None:
            print(f"  PUUTTUU: {fname}")
            continue

        im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        if slug in PRECROP:
            im = im.crop(PRECROP[slug])
        im = crop_to(im, ratio, focus)
        im, bri, sat = harmonise(im)

        for w in WIDTHS[role]:
            w = min(w, im.width)
            out = im.resize((w, int(round(w / ratio))), Image.LANCZOS)
            # kevyt teravoitys pienennyksen jalkeen
            out = out.filter(ImageFilter.UnsharpMask(radius=0.8, percent=52, threshold=3))
            out.save(os.path.join(DST, f"{slug}-{w}.webp"), "WEBP", quality=82, method=6)

        w0 = min(WIDTHS[role][0], im.width)
        fb = im.resize((w0, int(round(w0 / ratio))), Image.LANCZOS)
        fb = fb.filter(ImageFilter.UnsharpMask(radius=0.8, percent=52, threshold=3))
        fb.save(os.path.join(DST, f"{slug}.jpg"), "JPEG", quality=80,
                optimize=True, progressive=True)

        print(f"{slug:<20} {fname[:28]:<28} {bri:>9.2f} {sat:>7.2f}")

    total = sum(os.path.getsize(os.path.join(DST, f)) for f in os.listdir(DST))
    print("-" * 70)
    print(f"{len(os.listdir(DST))} tiedostoa, {total/1024/1024:.1f} MB")


if __name__ == "__main__":
    main()
