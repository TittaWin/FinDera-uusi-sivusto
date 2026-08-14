#!/usr/bin/env python3
"""
FinDera — referenssilogojen kasittely.

Tuottaa kaksi versiota jokaisesta asiakaslogosta:
  mono/  yksivarinen tummanvihrea (etusivun liukuva nauha)
  vari/  alkuperaiset varit lapinakyvalla taustalla (Projektit-sivun kortit)

Kaikki logot skaalataan samaan optiseen painoon (musteen maara), jotta rivi
nayttaa tasapainoiselta vaikka logojen muodot ja kuvasuhteet vaihtelevat.
Kuvat renderoidaan 2x-kokoisina, jotta ne ovat teravia myos tarkoilla naytoilla.
"""
from PIL import Image, ImageOps
import os, math

SRC = "/Users/titta/Documents/FinDera/Referenssit"
DST = "/Users/titta/Documents/FinDera/Visual Studio - FD/assets/logos"

INK = (0x16, 0x40, 0x2A)          # --forest

# nakyva koko CSS-pikseleina; tiedostot tehdaan 2x-kokoisina
MONO_BOX = (150, 32)
COLOR_BOX = (118, 30)

LOGOS = [
    ("rosknroll",   "RosknRoll_RR_logo_2014 2.jpg",            "Rosk'n Roll Oy Ab"),
    ("osao",        "OSAO_RGB_sininen.png",                    "Koulutuskuntayhtymä OSAO"),
    ("seinajoki",   "Seinäjoen energia logo.png",              "Seinäjoen Energia Oy"),
    ("ladec",       "Ladec_fi_mv_250px.png",                   "Lahden Seudun Kehitys LADEC Oy"),
    ("salpakierto", "Salpakierto_logo.png",                    "Salpakierto Oy"),
    ("salaoja",     "salaoja_logo_90.png",                     "Salaojayhdistys ry"),
    ("ely",         "ELY_LA01_Logo___FI_B3___RGB.png",         "Varsinais-Suomen ELY-keskus"),
    ("lsjh",        "LSJH_LOGO_HIRES_VÄRI_SUOMI_RGB.jpg",      "Lounais-Suomen Jätehuolto Oy"),
    ("klj",         "KLJ_tunnus_vihreä.png",                   "Kymenlaakson Jäte Oy"),
    ("turkuamk",    "turun_amk_logo.jpg",                      "Turun ammattikorkeakoulu"),
]


# Esirajaus niille logoille, joiden alkuperaistiedosto on liian korkea nauhaan.
# Arvot ovat pikseleita alkuperaisessa kuvassa (vasen, ylä, oikea, ala).
CROP = {
    # Turun AMK: tiedostossa on nelirivinen pystyversio. Englanninkielinen
    # alarivi jaa 32 pikselin nauhassa lukukelvottomaksi, joten kaytetaan
    # suomenkielista versiota: tahti + TURKU AMK.
    "turkuamk": (0, 70, 1342, 425),
}


def load(fname):
    """Lataa logo, muuntaa RGBA:ksi ja tekee valkoisesta taustasta lapinakyvan."""
    im = Image.open(os.path.join(SRC, fname))
    if im.mode == "CMYK":
        im = im.convert("RGB")
    if im.mode == "P":
        im = im.convert("RGBA")
    if im.mode != "RGBA":
        im = im.convert("RGBA")

    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            # lahes valkoinen -> lapinakyva, valialue -> pehmea reuna.
            # Varit sailyvat muuttumattomina, joten savyt eivat vaaristy.
            if lum >= 250:
                px[x, y] = (r, g, b, 0)
            elif lum > 238:
                px[x, y] = (r, g, b, int(a * (250 - lum) / 12))
    return im


def trim(im):
    bb = im.getchannel("A").getbbox()
    return im.crop(bb) if bb else im


def ink_mass(im):
    """Musteen maara: alfan summa suhteessa pinta-alaan."""
    a = im.getchannel("A")
    return sum(a.getdata()) / 255.0


def to_mono(im):
    """Yksivarinen versio: alfa muodostetaan tummuudesta."""
    flat = Image.new("RGBA", im.size, (255, 255, 255, 255))
    flat.alpha_composite(im)
    g = flat.convert("L")
    lo, hi = g.getextrema()
    span = max(hi - lo, 1)
    # Alfa muodostetaan kahdesta signaalista:
    #  1) tummuus  -> teksti ja mustat elementit
    #  2) varikylläisyys -> kirkkaat kuvamerkit (lehdet, terälehdet, tunnukset),
    #     jotka olisivat pelkan tummuuden perusteella lahes lapinakyvia.
    # Puhdas valkoinen ja harmaa tausta jaavat molemmissa nollaan.
    rgb = flat.convert("RGB")
    mx = rgb.convert("L")  # varataan; lasketaan pikselikohtaisesti alla
    px = rgb.load()
    w, h = rgb.size
    alpha = Image.new("L", rgb.size, 0)
    ap = alpha.load()
    for y in range(h):
        for x in range(w):
            r, gg, b = px[x, y]
            lum = 0.299 * r + 0.587 * gg + 0.114 * b
            if lum >= 249:
                continue
            a_dark = min(1.0, ((hi - lum) / span) ** 0.45)
            sat = (max(r, gg, b) - min(r, gg, b)) / 255.0
            a_sat = min(1.0, sat ** 0.7)
            ap[x, y] = int(255 * max(a_dark, a_sat))
    out = Image.new("RGBA", im.size, INK + (0,))
    out.putalpha(alpha)
    return trim(out)


def fit(im, box, scale=1.0):
    """Skaalaa laatikkoon, ei koskaan suurenna yli alkuperaisen tarkkuuden."""
    bw, bh = box
    s = min(bw / im.width, bh / im.height) * scale
    nw, nh = max(1, round(im.width * s)), max(1, round(im.height * s))
    return im.resize((nw, nh), Image.LANCZOS)


def render(variants, box, subdir):
    """Tasapainottaa optisen painon ja piirtaa kaikki samankokoiselle kankaalle."""
    os.makedirs(os.path.join(DST, subdir), exist_ok=True)
    W, H = box[0] * 2, box[1] * 2                 # 2x tarkkuus
    inner = (int(W * 0.96), int(H * 0.96))

    fitted = {k: fit(v, inner) for k, v in variants.items()}
    masses = {k: ink_mass(v) for k, v in fitted.items()}
    target = sorted(masses.values())[len(masses) // 2]      # mediaani

    for k, v in variants.items():
        # sqrt, koska musteen maara kasvaa skaalan nelionä
        s = math.sqrt(target / masses[k]) if masses[k] else 1.0
        s = max(0.72, min(1.12, s))                          # ei liian rajuja eroja
        im = fit(v, inner, s)
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.paste(im, ((W - im.width) // 2, (H - im.height) // 2), im)
        canvas.save(os.path.join(DST, subdir, k + ".png"), optimize=True)
        print(f"  {k:<14} {im.width:>3}x{im.height:<3} paino {masses[k]/target:5.2f} -> skaala {s:.2f}")


def main():
    mono, color = {}, {}
    print("Ladataan:")
    for key, fname, _ in LOGOS:
        im = load(fname)
        if key in CROP:
            im = im.crop(CROP[key])
        im = trim(im)
        print(f"  {key:<14} {im.width}x{im.height}")
        color[key] = im
        mono[key] = to_mono(im)

    print("\nYksivariset (nauha):")
    render(mono, MONO_BOX, "mono")
    print("\nVarilliset (kortit):")
    render(color, COLOR_BOX, "vari")

    tot = sum(os.path.getsize(os.path.join(r, f))
              for r, _, fs in os.walk(DST) for f in fs)
    print(f"\nYhteensa {tot/1024:.0f} kt")


if __name__ == "__main__":
    main()
