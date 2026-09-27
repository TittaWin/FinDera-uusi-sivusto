#!/usr/bin/env python3
"""
FinDera - lahdeaineiston sijainnin haku.

Alkuperaiset valokuvat ja logot eivat ole repossa vaan iCloud-kansiossa.
Kansio on siirtynyt paikasta toiseen, joten polkua ei kirjoiteta kiinteasti
skripteihin vaan etsitaan ajossa. Jarjestys: ymparistomuuttuja, tunnetut
sijainnit, lopuksi haku Documentsin alikansioista.
"""
import os, glob

KOTI = os.path.expanduser("~")

EHDOKKAAT = [
    os.path.join(KOTI, "Documents", "1. Studio Titta Projects", "FinDera"),
    os.path.join(KOTI, "Documents", "FinDera"),
]


def juuri():
    """Palauttaa FinDera-aineistokansion polun."""
    ymparisto = os.environ.get("FINDERA_AINEISTO")
    if ymparisto:
        if os.path.isdir(ymparisto):
            return ymparisto
        raise SystemExit(f"FINDERA_AINEISTO osoittaa kansioon jota ei ole: {ymparisto}")

    for polku in EHDOKKAAT:
        if os.path.isdir(polku):
            return polku

    for polku in sorted(glob.glob(os.path.join(KOTI, "Documents", "*", "FinDera"))):
        if os.path.isdir(polku):
            return polku

    raise SystemExit(
        "FinDera-aineistokansiota ei loytynyt. Kokeillut sijainnit:\n  "
        + "\n  ".join(EHDOKKAAT)
        + "\nAnna polku ymparistomuuttujalla FINDERA_AINEISTO."
    )


def alikansio(nimi):
    """Palauttaa aineistokansion alikansion polun ja tarkistaa etta se on olemassa."""
    polku = os.path.join(juuri(), nimi)
    if not os.path.isdir(polku):
        raise SystemExit(f"Aineistokansiota ei loydy: {polku}")
    return polku


if __name__ == "__main__":
    print(juuri())
