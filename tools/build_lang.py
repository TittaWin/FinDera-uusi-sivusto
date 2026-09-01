#!/usr/bin/env python3
"""
FinDera — vieraskielisten sivujen luonti.

Luo kansion en/ staattiset englanninkieliset sivut. Lahteena ovat
suomenkieliset HTML-sivut ja tiedosto assets/i18n/en.json — samat tekstit
joita selain kayttaa kielenvaihdossa, mutta sijoitettuna sivuille valmiiksi.

  palvelut.html + en.json  ->  en/services.html  (osoite /en/services)

Miksi: hakukone ei paina kielivalitsinta. Kaannokset nakyvat Googlelle vasta,
kun ne ovat sivun HTML:ssa latautuessa.

Skripti ei muuta suomenkielisia sivuja. Se ylikirjoittaa kansion en/
kokonaan, joten sen sisaltoa ei pida muokata kasin.

Ajo:  python3 tools/build_lang.py
      python3 tools/build_lang.py --kokeile   nayttaa mita syntyisi
"""
import io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_content import Extractor, ROOT  # noqa: E402

LANG = "en"
LOCALE = "en_GB"
SITE = "https://www.findera.fi"

# suomenkielinen tiedosto -> (englanninkielinen tiedosto, suomen osoite,
#                             englannin osoite, kuuluuko hakutuloksiin)
PAGES = [
    ("index.html",        "index.html",     "/",             "/en/",         True),
    ("palvelut.html",     "services.html",  "/palvelut",     "/en/services", True),
    ("projektit.html",    "projects.html",  "/projektit",    "/en/projects", True),
    ("minusta.html",      "about.html",     "/minusta",      "/en/about",    True),
    ("yhteystiedot.html", "contact.html",   "/yhteystiedot", "/en/contact",  True),
    ("tietosuoja.html",   "privacy.html",   "/tietosuoja",   "/en/privacy",  True),
    ("kiitos.html",       "thank-you.html", "/kiitos",       "/en/thank-you", False),
]

URLMAP = {fi_url: en_url for _, _, fi_url, en_url, _ in PAGES}

HEADER = """<!DOCTYPE html>
<!-- GENEROITU TIEDOSTO — ÄLÄ MUOKKAA.
     Luodaan komennolla python3 tools/build_lang.py suomenkielisestä
     sivusta {src} ja tiedostosta assets/i18n/en.json.
     Muokkaa tekstit kansiossa content/{slug}/en.json. -->
"""


def dictionary():
    raw = json.load(io.open(os.path.join(ROOT, "assets/i18n/%s.json" % LANG),
                            encoding="utf-8"))
    return raw.get("common", {}), raw.get("pages", {})


VOID = ("br", "img", "input", "meta", "link", "hr", "source", "path", "circle")


def all_spans(src):
    """Kaikkien data-i18n-kohtien sijainnit — sama avain voi esiintya monesti.

    apply_content.spans() palauttaa avainta kohti vain yhden osuman, mika
    riittaa suomen kirjoittamiseen takaisin sivulle. Kaannettaessa se ei riita:
    esimerkiksi nav.services on seka ylavalikossa etta alatunnisteessa, ja
    molemmat pitaa kaantaa.
    """
    ex = Extractor(src)
    found = []

    def endtag(tag):
        if tag not in VOID:
            ex.depth -= 1
        while ex.stack and ex.stack[-1][0] == tag and ex.stack[-1][1] == ex.depth:
            _, _, key, begin = ex.stack.pop()
            found.append((key, begin, ex._pos()))

    ex.handle_endtag = endtag
    ex.feed(src)
    return found


def all_attr_spans(src):
    """Kaikkien data-i18n-attr -kohtien sijainnit samalla periaatteella."""
    found = []
    for m in re.finditer(r'<[a-zA-Z][^>]*data-i18n-attr="([^"]+)"[^>]*>', src):
        tag = m.group(0)
        for pair in m.group(1).split(","):
            attr, _, key = pair.partition(":")
            attr, key = attr.strip(), key.strip()
            am = re.search(r'\b%s="([^"]*)"' % re.escape(attr), tag)
            if key and am:
                found.append((key, m.start() + am.start(1), m.start() + am.end(1)))
    return found


def translate(src, page_dict, fname, missing):
    """Sijoittaa kaannokset data-i18n-kohtiin, sama logiikka kuin selaimessa."""
    edits = []
    for key, start, end in all_spans(src):
        val = page_dict.get(key)
        if val is None:
            missing.append((fname, key))
            continue
        edits.append((start, end, val))
    for key, start, end in all_attr_spans(src):
        val = page_dict.get(key)
        if val is None:
            missing.append((fname, key))
            continue
        edits.append((start, end, val.replace('"', "&quot;")))

    # Sisakkaiset avaimet rikkoisivat korvaukset — sivustolla niita ei ole,
    # mutta varmistetaan se, ettei virhe jaa huomaamatta.
    ordered = sorted(edits)
    for (s1, e1, _), (s2, _, _) in zip(ordered, ordered[1:]):
        if s2 < e1:
            raise SystemExit("Sisakkainen data-i18n-avain kohdassa %d — %s" % (s1, fname))

    for start, end, text in sorted(edits, reverse=True):
        src = src[:start] + text + src[end:]
    return src


def relink(src):
    """Sisaiset linkit osoittamaan englanninkielisiin sivuihin."""
    def sub(m):
        attr, url, frag = m.group(1), m.group(2), m.group(3) or ""
        return '%s="%s%s"' % (attr, URLMAP.get(url, url), frag)
    return re.sub(r'\b(href|action)="(/[a-z0-9-]*)(#[a-z0-9-]+)?"', sub, src)


# Rakenteisessa datassa on muutama suomenkielinen kentta ja sivun oma osoite.
# Kaannokset ovat tassa, koska ne eivat ole nakyvaa sisaltoa eivatka siksi
# kuulu content/-kansioon.
LD_TEXTS = {
    "Konsultti, FinDera Consulting": "Consultant, FinDera Consulting",
    "Konsultti": "Consultant",
    "Kiertotalous": "Circular economy",
    "Kestävä kehitys": "Sustainable development",
    "Energiaratkaisut": "Energy solutions",
    "Ympäristöteknologia": "Environmental technology",
    "Markkina-avaus": "Market entry",
    "DACH-alue": "DACH region",
}


def structured(src, en_url, page_dict):
    """Rakenteinen data osoittamaan englanninkieliseen sivuun."""
    def fix(m):
        block = m.group(1)
        block = re.sub(r'"url": "%s[^"]*"' % re.escape(SITE),
                       '"url": "%s%s"' % (SITE, en_url), block)
        desc = page_dict.get("meta.desc")
        if desc:
            block = re.sub(r'"description": "[^"]*"',
                           '"description": "%s"' % desc.replace('"', '\\"'), block)
        for fi, en in LD_TEXTS.items():
            block = block.replace('"%s"' % fi, '"%s"' % en)
        return '<script type="application/ld+json">%s</script>' % block
    return re.sub(r'(?s)<script type="application/ld\+json">(.*?)</script>', fix, src)


def head(src, fi_url, en_url, page_dict, indexable):
    title = page_dict.get("meta.title", "")
    desc = page_dict.get("meta.desc", "")

    # Suomenkielisella sivulla on jo omat hreflang-rivinsa; ne kirjoitetaan
    # taalla uusiksi, jotta rivit eivat kahdennu.
    src = re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n?', "", src)

    src = src.replace('<meta property="og:locale" content="fi_FI">',
                      '<meta property="og:locale" content="%s">' % LOCALE)
    src = re.sub(r'<link rel="canonical" href="[^"]*">',
                 '<link rel="canonical" href="%s%s">' % (SITE, en_url), src)
    src = re.sub(r'<meta property="og:url" content="[^"]*">',
                 '<meta property="og:url" content="%s%s">' % (SITE, en_url), src)
    if title:
        src = re.sub(r'<meta property="og:title" content="[^"]*">',
                     '<meta property="og:title" content="%s">' % title.replace('"', "&quot;"), src)
    if desc:
        src = re.sub(r'<meta property="og:description" content="[^"]*">',
                     '<meta property="og:description" content="%s">' % desc.replace('"', "&quot;"), src)

    if indexable:
        alt = ('<link rel="alternate" hreflang="fi" href="%s%s">\n'
               '<link rel="alternate" hreflang="en" href="%s%s">\n'
               '<link rel="alternate" hreflang="x-default" href="%s%s">'
               % (SITE, fi_url, SITE, en_url, SITE, fi_url))
        src = src.replace('<link rel="canonical" href="%s%s">' % (SITE, en_url),
                          '<link rel="canonical" href="%s%s">\n%s' % (SITE, en_url, alt))
    return src


def switcher(src, fi_url):
    """Kielivalitsin kaantyy: suomi vie takaisin, englanti on nykyinen kieli."""
    src = src.replace('<span class="lang__current">FI</span>',
                      '<span class="lang__current">EN</span>')
    src = re.sub(r'<button type="button" data-lang="fi"[^>]*>',
                 '<button type="button" data-lang="fi" data-href="%s" '
                 'role="option" aria-selected="false">' % fi_url, src)
    src = re.sub(r'<button type="button" data-lang="en"[^>]*>',
                 '<button type="button" data-lang="en" role="option" '
                 'aria-selected="true">', src)
    return src


def build(dry=False):
    common, pages = dictionary()
    outdir = os.path.join(ROOT, LANG)
    if not dry:
        os.makedirs(outdir, exist_ok=True)

    missing, written = [], []
    for fi_name, en_name, fi_url, en_url, indexable in PAGES:
        src = io.open(os.path.join(ROOT, fi_name), encoding="utf-8").read()
        page_dict = dict(common)
        page_dict.update(pages.get(fi_name, {}))

        src = translate(src, page_dict, fi_name, missing)
        src = relink(src)
        src = head(src, fi_url, en_url, page_dict, indexable)
        src = switcher(src, fi_url)
        src = structured(src, en_url, page_dict)

        src = re.sub(r'<html lang="fi">',
                     '<html lang="en" data-page="%s">' % fi_name, src)
        src = re.sub(r"(?s)^<!DOCTYPE html>\n<!--.*?-->\n",
                     HEADER.format(src=fi_name, slug=fi_name[:-5]), src)

        # Tarkistus: jokaisen kaannoskohdan sisallon on vastattava sanakirjaa.
        # Nain esimerkiksi kahdesti esiintyva avain ei voi jaada suomeksi.
        checked = 0
        for key, start, end in all_spans(src) + all_attr_spans(src):
            want = page_dict.get(key)
            if want is None:
                continue
            got = src[start:end]
            if got != want and got != want.replace('"', "&quot;"):
                raise SystemExit("Kaannos ei mennyt perille: %s / %s" % (en_name, key))
            checked += 1

        path = os.path.join(outdir, en_name)
        if not dry:
            io.open(path, "w", encoding="utf-8").write(src)
        written.append((os.path.relpath(path, ROOT), en_url, checked))

    print("KOKEILU — mitään ei kirjoiteta\n" if dry else "Luodaan englanninkieliset sivut\n")
    for path, url, size in written:
        print("  %-22s %-16s %4d käännettyä kohtaa" % (path, url, size))
    if missing:
        print("\n  ! käännös puuttuu %d kohdasta — suomi jää näkyviin:" % len(missing))
        for fname, key in missing[:20]:
            print("      %s / %s" % (fname, key))
    else:
        print("\n  Kaikki tekstit käännetty.")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(build("--kokeile" in sys.argv or "--dry-run" in sys.argv))
