#!/usr/bin/env python3
"""
FinDera — sisaltorakenteen luonti.

Poimii sivuston tekstit nykyisesta lahteesta ja kirjoittaa ne kansioon
content/<sivu>/<kieli>.json selkeilla avainsanoilla ja selitteilla.

  suomi   = HTML-tiedostojen data-i18n-elementtien sisalto
  en / de = assets/i18n/en.json ja de.json

Skripti ei muuta HTML-sivuja eika kaannostiedostoja, vaan ainoastaan
kirjoittaa content/-kansion. Ajo:  python3 tools/build_content.py
"""
from html.parser import HTMLParser
import collections, io, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = [
    ("index.html",        "index"),
    ("palvelut.html",     "palvelut"),
    ("projektit.html",    "projektit"),
    ("minusta.html",      "minusta"),
    ("yhteystiedot.html", "yhteystiedot"),
    ("tietosuoja.html",   "tietosuoja"),
]
LANGS = ("fi", "en", "de")


# --------------------------------------------------------------------------
# 1. Suomenkielisen sisallon poiminta HTML:sta
# --------------------------------------------------------------------------
class Extractor(HTMLParser):
    """Kerää jokaisen data-i18n-elementin sisällön alkuperäisessä muodossaan."""

    def __init__(self, src):
        super().__init__(convert_charrefs=False)
        self.src = src
        self.line_start = [0]
        for line in src.split("\n"):
            self.line_start.append(self.line_start[-1] + len(line) + 1)
        self.stack = []          # (tagi, syvyys, avain, sisallon_alku)
        self.depth = 0
        self.values = {}
        self.attrs = {}          # data-i18n-attr -> arvo
        self.order = []

    def _pos(self):
        line, off = self.getpos()
        return self.line_start[line - 1] + off

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "data-i18n-attr" in a:
            for pair in a["data-i18n-attr"].split(","):
                attr, _, key = pair.partition(":")
                if key and attr.strip() in a:
                    self.attrs[key.strip()] = a[attr.strip()]
                    if key.strip() not in self.order:
                        self.order.append(key.strip())
        if "data-i18n" in a:
            key = a["data-i18n"]
            gt = self.src.index(">", self._pos()) + 1
            self.stack.append((tag, self.depth, key, gt))
            if key not in self.order:
                self.order.append(key)
        if tag not in ("br", "img", "input", "meta", "link", "hr", "source", "path", "circle"):
            self.depth += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)   # itsesulkeutuva ei muuta syvyytta

    def handle_endtag(self, tag):
        if tag not in ("br", "img", "input", "meta", "link", "hr", "source", "path", "circle"):
            self.depth -= 1
        while self.stack and self.stack[-1][0] == tag and self.stack[-1][1] == self.depth:
            _, _, key, start = self.stack.pop()
            self.values[key] = self.src[start:self._pos()]


def tidy(html):
    """Siistii sisennykset pois mutta sailyttaa mahdolliset HTML-tagit."""
    return re.sub(r"\s+", " ", html).strip()


def read_page(fname):
    src = io.open(os.path.join(ROOT, fname), encoding="utf-8").read()
    ex = Extractor(src)
    ex.feed(src)
    out = collections.OrderedDict()
    for key in ex.order:
        if key in ex.values:
            out[key] = tidy(ex.values[key])
        elif key in ex.attrs:
            out[key] = tidy(ex.attrs[key])
    return out


# --------------------------------------------------------------------------
# 2. Selitteet — osion nimi + kentan tyyppi kolmella kielella
# --------------------------------------------------------------------------
SECTION = {
    "meta":    ("Selaimen välilehti ja hakukonekuvaus",
                "Browser tab and search engine description",
                "Browser-Tab und Suchmaschinenbeschreibung"),
    "a11y":    ("Saavutettavuus", "Accessibility", "Barrierefreiheit"),
    "nav":     ("Päävalikko", "Main navigation", "Hauptnavigation"),
    "hero":    ("Etusivun pääkuva-osio", "Front page hero section", "Hero-Bereich der Startseite"),
    "stats":   ("Tunnusluvut", "Key figures", "Kennzahlen"),
    "intro":   ("Mistä on kyse -osio", "What it is about section", "Abschnitt „Worum es geht“"),
    "svc":     ("Palvelut-osio etusivulla", "Services section on the front page",
                "Leistungsbereich auf der Startseite"),
    "aii":     ("Access · Insight · Impact -osio", "Access · Insight · Impact section",
                "Abschnitt Access · Insight · Impact"),
    "who":     ("Kenelle palvelut sopivat", "Who the services suit", "Für wen die Leistungen geeignet sind"),
    "why":     ("Miksi FinDera -osio", "Why FinDera section", "Abschnitt „Warum FinDera“"),
    "pwhy":    ("Miksi FinDera -osio", "Why FinDera section", "Abschnitt „Warum FinDera“"),
    "clients": ("Asiakaslogojen nauha", "Client logo strip", "Logoleiste der Kunden"),
    "quotes":  ("Asiakassuositukset", "Client testimonials", "Kundenstimmen"),
    "gallery": ("Kuvagalleria", "Photo gallery", "Bildergalerie"),
    "steps":   ("Näin etenemme -osio", "How we proceed section", "Abschnitt „So gehen wir vor“"),
    "cta":     ("Yhteydenottokehotus", "Call to action", "Handlungsaufforderung"),
    "footer":  ("Alatunniste", "Footer", "Fußzeile"),
    "ph":      ("Sivun otsikko-osio", "Page heading section", "Seitenkopf"),
    "p1":      ("Palvelu 1 — kohdekäynnit ja ryhmämatkat",
                "Service 1 — site visits and group trips",
                "Leistung 1 — Vor-Ort-Besuche und Gruppenreisen"),
    "p2":      ("Palvelu 2 — ovien avaus ja tapaamiset",
                "Service 2 — opening doors and meetings",
                "Leistung 2 — Türen öffnen und Termine"),
    "p3":      ("Palvelu 3 — kartoitus ja kontaktien välitys",
                "Service 3 — surveys and contact brokering",
                "Leistung 3 — Recherche und Kontaktvermittlung"),
    "models":  ("Toimitusmallit", "Delivery models", "Leistungsmodelle"),
    "case":    ("Referenssikortit", "Reference cards", "Referenzkarten"),
    "about":   ("Tausta-osio", "Background section", "Abschnitt Hintergrund"),
    "career":  ("Urapolku", "Career path", "Werdegang"),
    "style":   ("Työskentelytapa", "Way of working", "Arbeitsweise"),
    "form":    ("Yhteydenottolomake", "Contact form", "Kontaktformular"),
    "contact": ("Suorat yhteystiedot", "Direct contact details", "Direkte Kontaktdaten"),
    "next":    ("Mitä seuraavaksi tapahtuu", "What happens next", "Wie es weitergeht"),
    "ts":      ("Tietosuojaseloste", "Privacy policy", "Datenschutzerklärung"),
}

FIELD = {
    "title":   ("otsikko", "heading", "Überschrift"),
    "lead":    ("ingressi", "intro paragraph", "Einleitung"),
    "desc":    ("kuvausteksti", "body text", "Beschreibungstext"),
    "desc2":   ("kuvausteksti, 2. kappale", "body text, 2nd paragraph", "Beschreibungstext, 2. Absatz"),
    "desc3":   ("kuvausteksti, 3. kappale", "body text, 3rd paragraph", "Beschreibungstext, 3. Absatz"),
    "eyebrow": ("pieni yläotsikko", "small label above the heading", "kleine Zeile über der Überschrift"),
    "when":    ("milloin palvelu sopii", "when the service fits", "wann die Leistung passt"),
    "inc":     ("luettelon otsikko", "list heading", "Listenüberschrift"),
    "who":     ("kenelle tarkoitettu", "who it is for", "für wen gedacht"),
    "note":    ("korostettu huomautus", "highlighted note", "hervorgehobener Hinweis"),
    "cases":   ("käyttötapausten otsikko", "use cases heading", "Überschrift Anwendungsfälle"),
    "more":    ("avattavan osion otsikko", "expandable section label", "Titel des aufklappbaren Bereichs"),
    "role":    ("FinDeran osuus", "FinDera's part", "Anteil von FinDera"),
    "link":    ("linkin teksti", "link text", "Linktext"),
    "book":    ("painikkeen teksti", "button text", "Beschriftung der Schaltfläche"),
    "bookFree":("painikkeen teksti", "button text", "Beschriftung der Schaltfläche"),
    "talk":    ("painikkeen teksti", "button text", "Beschriftung der Schaltfläche"),
    "quote":   ("painikkeen teksti", "button text", "Beschriftung der Schaltfläche"),
    "form":    ("painikkeen teksti", "button text", "Beschriftung der Schaltfläche"),
    "send":    ("lähetyspainikkeen teksti", "submit button text", "Beschriftung des Absendebuttons"),
    "name":    ("kentän nimi", "field label", "Feldbezeichnung"),
    "org":     ("kentän nimi", "field label", "Feldbezeichnung"),
    "email":   ("kentän nimi", "field label", "Feldbezeichnung"),
    "phone":   ("kentän nimi", "field label", "Feldbezeichnung"),
    "topic":   ("kentän nimi", "field label", "Feldbezeichnung"),
    "msg":     ("kentän nimi", "field label", "Feldbezeichnung"),
    "ph":      ("kentän vihjeteksti", "field placeholder", "Platzhalter im Feld"),
    "consent": ("suostumusteksti", "consent text", "Einwilligungstext"),
    "tagline": ("kuvausteksti", "body text", "Beschreibungstext"),
    "langs":   ("palvelukielet", "working languages", "Arbeitssprachen"),
    "nav":     ("otsikko", "heading", "Überschrift"),
    "contact": ("otsikko", "heading", "Überschrift"),
    "skip":    ("ohituslinkki näppäimistökäyttäjille", "skip link for keyboard users",
                "Sprunglink für Tastaturnutzung"),
    "trips":   ("selite", "caption", "Beschriftung"),
    "people":  ("selite", "caption", "Beschriftung"),
    "since":   ("selite", "caption", "Beschriftung"),
    "langs2":  ("selite", "caption", "Beschriftung"),
    "intro":   ("johdantoteksti", "introductory text", "Einleitungstext"),
    "services":("painikkeen teksti", "button text", "Beschriftung der Schaltfläche"),
    "scroll":  ("vieritysvihje", "scroll hint", "Scroll-Hinweis"),
    "next":    ("otsikko", "heading", "Überschrift"),
    "person":  ("kentän nimi", "field label", "Feldbezeichnung"),
    "title2":  ("otsikko", "heading", "Überschrift"),
    "title3":  ("otsikko", "heading", "Überschrift"),
    "dest":    ("tietorivin otsake: kohdemaa", "fact row label: destination",
                "Bezeichnung in der Faktenzeile: Zielland"),
    "len":     ("tietorivin otsake: kesto", "fact row label: duration",
                "Bezeichnung in der Faktenzeile: Dauer"),
    "pax":     ("tietorivin otsake: osallistujat", "fact row label: participants",
                "Bezeichnung in der Faktenzeile: Teilnehmende"),
    "sites":   ("tietorivin otsake: kohteiden määrä", "fact row label: number of sites",
                "Bezeichnung in der Faktenzeile: Anzahl der Ziele"),
    "body":    ("leipäteksti", "body text", "Fließtext"),
    "body1":   ("leipäteksti, 1. kappale", "body text, 1st paragraph", "Fließtext, 1. Absatz"),
    "body2":   ("leipäteksti, 2. kappale", "body text, 2nd paragraph", "Fließtext, 2. Absatz"),
    "updated": ("päivityspäivä", "date of last update", "Datum der letzten Aktualisierung"),
    "privacy": ("valikon linkki", "navigation link", "Navigationslink"),
}

# Avaimet, jotka eivat noudata yleista kaavaa
NAV_LINK = ("valikon linkki", "navigation link", "Navigationslink")
TAG_LABEL = ("kortin merkintä (asiakas- tai matkatyyppi)",
             "card tag (client or trip type)",
             "Kennzeichnung auf der Karte (Kunden- oder Reisetyp)")
PARA = ("kappale {}", "paragraph {}", "Absatz {}")
STEP = ("vaihe {}", "step {}", "Schritt {}")
QUOTE = ("asiakkaan suositus", "client testimonial", "Kundenstimme")

ITEM = ("kohta {}", "item {}", "Punkt {}")
LIST = ("luettelokohta {}", "list item {}", "Listenpunkt {}")

SHARED = ("Yhteinen kaikille sivuille — jos muutat tätä, muuta sama teksti myös "
          "muiden sivujen tiedostoihin.",
          "Shared across all pages — if you change this, change the same text in "
          "the other page files too.",
          "Auf allen Seiten gleich — wenn Sie das ändern, ändern Sie denselben Text "
          "auch in den Dateien der anderen Seiten.")

HTML_NOTE = ("Sisältää HTML-merkintää (esim. <em> tai <strong>). Säilytä tagit "
             "ennallaan ja muuta vain niiden välissä oleva teksti.",
             "Contains HTML markup (e.g. <em> or <strong>). Keep the tags as they "
             "are and change only the text between them.",
             "Enthält HTML-Auszeichnung (z. B. <em> oder <strong>). Lassen Sie die "
             "Tags unverändert und ändern Sie nur den Text dazwischen.")

CASE_NAMES = {
    "rr": "Rosk'n Roll Oy Ab", "lsjh": "Lounais-Suomen Jätehuolto Oy",
    "seinajoki": "Seinäjoen Energia Oy", "ladec": "Lahden Seudun Kehitys LADEC Oy",
    "salpakierto": "Salpakierto Oy", "salaoja": "Salaojayhdistys ry",
    "ely": "Varsinais-Suomen ELY-keskus", "osao": "Koulutuskuntayhtymä OSAO",
    "type": None, "f": None, "more": None,
}


def describe(key, lang_i, shared, has_html):
    """Rakentaa kentan selitteen avaimen rakenteesta."""
    parts = key.split(".")
    head = parts[0]
    sec = SECTION.get(head)
    sec_name = sec[lang_i] if sec else head

    tail = parts[1:]
    bits, field = [], None

    if head == "nav":
        field = NAV_LINK[lang_i]
    elif head == "q":
        sec_name = SECTION["quotes"][lang_i]
        field = QUOTE[lang_i]
        if tail:
            bits.append(CASE_NAMES.get(tail[0]) or tail[0].upper())
    elif head == "case" and len(tail) >= 2 and tail[0] == "type":
        field = TAG_LABEL[lang_i]
    elif not tail:
        field = FIELD["title"][lang_i]

    # numeroitu kohta, esim. svc.1.title, why.3.desc, about.p2, contact.n1
    for p in tail:
        if p.isdigit():
            bits.append(ITEM[lang_i].format(p))
        elif re.fullmatch(r"li\d+", p):
            bits.append(LIST[lang_i].format(p[2:]))
        elif re.fullmatch(r"c\d+", p):
            bits.append(LIST[lang_i].format(p[1:]))
        elif re.fullmatch(r"p\d[a-z]?", p):
            bits.append(PARA[lang_i].format(p[1:]))
        elif re.fullmatch(r"n\d", p):
            bits.append(STEP[lang_i].format(p[1:]))
        elif head == "case" and CASE_NAMES.get(p):
            bits.append(CASE_NAMES[p])

    if field is None:
        for p in reversed(tail):
            if p in FIELD:
                field = FIELD[p][lang_i]
                break

    text = sec_name
    if bits:
        text += ", " + ", ".join(bits)
    if field:
        text += " — " + field
    elif not bits:
        text += " — " + {0: "teksti", 1: "text", 2: "Text"}[lang_i]

    if not text.endswith("."):
        text += "."
    if shared:
        text += " " + SHARED[lang_i]
    if has_html:
        text += " " + HTML_NOTE[lang_i]
    return text


# --------------------------------------------------------------------------
# 3. Kirjoitus
# --------------------------------------------------------------------------
HEADER = {
    "fi": ("Tämän tiedoston tekstit näkyvät sivustolla. Muuta vain lainausmerkkien "
           "sisällä olevaa tekstiä. Rivit, joiden avain päättyy sanaan .description, "
           "ovat ohjeita sinulle — niitä ei näytetä sivustolla eikä niitä tarvitse muuttaa."),
    "en": ("The texts in this file appear on the website. Change only the text inside "
           "the quotation marks. Lines whose key ends in .description are guidance for "
           "you — they are not shown on the site and do not need to be changed."),
    "de": ("Die Texte in dieser Datei erscheinen auf der Website. Ändern Sie nur den Text "
           "innerhalb der Anführungszeichen. Zeilen, deren Schlüssel auf .description endet, "
           "sind Hinweise für Sie — sie erscheinen nicht auf der Website."),
}
PAGE_NAME = {
    "index":        ("Etusivu", "Home page", "Startseite"),
    "palvelut":     ("Palvelut", "Services", "Leistungen"),
    "projektit":    ("Projektit ja referenssit", "Projects and references", "Projekte und Referenzen"),
    "minusta":      ("Minusta", "About", "Über mich"),
    "yhteystiedot": ("Yhteystiedot", "Contact", "Kontakt"),
    "tietosuoja":   ("Tietosuojaseloste", "Privacy policy", "Datenschutzerklärung"),
}


def main():
    en = json.load(io.open(os.path.join(ROOT, "assets/i18n/en.json"), encoding="utf-8"))
    de = json.load(io.open(os.path.join(ROOT, "assets/i18n/de.json"), encoding="utf-8"))
    src = {"en": en, "de": de}

    total = 0
    for fname, slug in PAGES:
        fi_vals = read_page(fname)
        shared_keys = set(en["common"])
        outdir = os.path.join(ROOT, "content", slug)
        os.makedirs(outdir, exist_ok=True)

        for li, lang in enumerate(LANGS):
            doc = collections.OrderedDict()
            doc["_sivu"] = PAGE_NAME[slug][li]
            doc["_kieli"] = {"fi": "suomi", "en": "English", "de": "Deutsch"}[lang]
            doc["_ohje"] = HEADER[lang]

            for key, fi_text in fi_vals.items():
                if lang == "fi":
                    value = fi_text
                else:
                    d = src[lang]
                    value = d["pages"].get(fname, {}).get(key, d["common"].get(key, ""))
                has_html = bool(re.search(r"<[a-z/]", str(value)))
                doc[key] = value
                doc[key + ".description"] = describe(key, li, key in shared_keys, has_html)

            path = os.path.join(outdir, lang + ".json")
            io.open(path, "w", encoding="utf-8").write(
                json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
            total += 1
        print(f"  content/{slug:<13} {len(fi_vals):>3} kenttää × 3 kieltä")

    print(f"\n{total} tiedostoa kirjoitettu kansioon content/")


if __name__ == "__main__":
    main()
