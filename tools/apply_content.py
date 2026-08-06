#!/usr/bin/env python3
"""
FinDera — sisallon vienti sivustolle.

Lukee kansion content/ ja kirjoittaa tekstit takaisin sivustolle:

  fi.json  ->  HTML-sivujen data-i18n-elementteihin
  en.json  ->  assets/i18n/en.json
  de.json  ->  assets/i18n/de.json

Kaytto:
    python3 tools/apply_content.py --kokeile   nayttaa muutokset, ei kirjoita
    python3 tools/apply_content.py             kirjoittaa muutokset

Ennen kirjoittamista muuttuvista tiedostoista otetaan varmuuskopio kansioon
.varmuuskopiot/<paivays>/. Kirjoituksen jalkeen skripti tarkistaa, etta
sivustolta luettu sisalto vastaa content/-kansiota.
"""
import collections, datetime, io, json, os, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_content import Extractor, tidy, read_page, PAGES, LANGS, ROOT  # noqa: E402

# Varmuuskopiot kirjoitetaan projektikansion ULKOPUOLELLE, jotta ne eivat
# paady Netlifyyn julkaisun mukana.
BACKUP = os.path.join(os.path.dirname(ROOT), "FinDera-varmuuskopiot")

# Netlifyn julkaisupalvelimella varmuuskopiota ei tarvita: alkuperainen
# sisalto on tallessa versionhallinnassa ja rakennuskansio on kertakayttoinen.
ON_NETLIFY = bool(os.environ.get("NETLIFY") or os.environ.get("CI"))
META = ("_sivu", "_kieli", "_ohje")


# --------------------------------------------------------------------------
# Sisallon lukeminen content/-kansiosta
# --------------------------------------------------------------------------
def load_content(slug, lang):
    path = os.path.join(ROOT, "content", slug, lang + ".json")
    doc = json.load(io.open(path, encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
    return collections.OrderedDict(
        (k, v) for k, v in doc.items()
        if k not in META and not k.endswith(".description"))


# --------------------------------------------------------------------------
# Suomi -> HTML
# --------------------------------------------------------------------------
def spans(src):
    """Palauttaa jokaiselle data-i18n-avaimelle sisallon sijainnin lahdekoodissa."""
    ex = Extractor(src)
    ex.spans = {}
    orig_end = ex.handle_endtag

    def endtag(tag):
        if tag not in ("br", "img", "input", "meta", "link", "hr", "source", "path", "circle"):
            ex.depth -= 1
        while ex.stack and ex.stack[-1][0] == tag and ex.stack[-1][1] == ex.depth:
            _, _, key, start = ex.stack.pop()
            end = ex._pos()
            ex.values[key] = src[start:end]
            ex.spans[key] = (start, end)

    ex.handle_endtag = endtag
    ex.feed(src)
    return ex


def attr_span(src, key):
    """Etsii data-i18n-attr -kentan arvon sijainnin, esim. content:meta.desc."""
    for m in re.finditer(r"<[a-zA-Z][^>]*data-i18n-attr=\"([^\"]+)\"[^>]*>", src):
        for pair in m.group(1).split(","):
            attr, _, k = pair.partition(":")
            if k.strip() != key:
                continue
            tag = m.group(0)
            am = re.search(r'\b%s="([^"]*)"' % re.escape(attr.strip()), tag)
            if am:
                return (m.start() + am.start(1), m.start() + am.end(1))
    return None


def reflow(new_value, original, single_line_limit=96):
    """Sovittaa uuden tekstin alkuperaisen sisennyksen mukaiseksi."""
    if "\n" not in original or "<" in new_value or len(new_value) <= single_line_limit:
        if "\n" not in original:
            return new_value
    lines = original.split("\n")
    body_indent = ""
    for line in lines[1:]:
        if line.strip():
            body_indent = line[: len(line) - len(line.lstrip())]
            break
    close_indent = lines[-1] if not lines[-1].strip() else ""
    if not body_indent:
        return new_value

    words, out, cur = new_value.split(), [], body_indent
    for w in words:
        if len(cur) + len(w) + 1 > 96 and cur.strip():
            out.append(cur)
            cur = body_indent + w
        else:
            cur = (cur + " " + w) if cur.strip() else cur + w
    if cur.strip():
        out.append(cur)
    return "\n" + "\n".join(out) + "\n" + close_indent


def apply_fi(fname, slug, dry):
    path = os.path.join(ROOT, fname)
    src = io.open(path, encoding="utf-8").read()
    want = load_content(slug, "fi")
    ex = spans(src)

    edits, changed = [], []
    for key, value in want.items():
        value = str(value)
        if key in ex.spans:
            start, end = ex.spans[key]
            if tidy(src[start:end]) == tidy(value):
                continue
            edits.append((start, end, reflow(value, src[start:end])))
        else:
            sp = attr_span(src, key)
            if not sp:
                print(f"    ! avainta {key} ei löydy sivulta {fname} — ohitetaan")
                continue
            start, end = sp
            if src[start:end] == value:
                continue
            edits.append((start, end, value.replace('"', "&quot;")))
        changed.append(key)

    if not edits:
        return src, []
    for start, end, text in sorted(edits, reverse=True):
        src = src[:start] + text + src[end:]
    return src, changed


# --------------------------------------------------------------------------
# EN / DE -> assets/i18n
# --------------------------------------------------------------------------
def apply_i18n(lang, dry):
    """
    Kaannostiedostossa on kaksi tasoa: common on oletus kaikille sivuille ja
    pages[<sivu>] voi ylittaa sen. Sama avain saa siis olla eri sivuilla eri
    sisallolla — nain esimerkiksi aii.*-tekstit ovat etusivulla tiiviimpia
    kuin Palvelut-sivulla. Skripti sailyttaa taman rakenteen:

      kaikki sivut samaa mielta  -> arvo menee common-osioon
      jokin sivu poikkeaa        -> poikkeava arvo menee pages[<sivu>]-osioon
    """
    path = os.path.join(ROOT, "assets", "i18n", lang + ".json")
    doc = json.load(io.open(path, encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
    old_common = dict(doc.get("common", {}))

    pages = {slug: load_content(slug, lang) for _, slug in PAGES}
    changed, overrides = [], []

    # Mille sivuille kukin avain kuuluu
    by_key = collections.OrderedDict()
    for fname, slug in PAGES:
        for key, value in pages[slug].items():
            by_key.setdefault(key, collections.OrderedDict())[fname] = value

    for key, per_page in by_key.items():
        values = set(per_page.values())
        all_agree = len(values) == 1

        if all_agree and (key in old_common or len(per_page) > 1):
            # Sama teksti kaikkialla -> yhteiseksi, sivukohtaiset poikkeukset pois
            common_value = next(iter(values))
            if doc["common"].get(key) != common_value:
                doc["common"][key] = common_value
                changed.append("common/" + key)
        else:
            # Sivut eroavat (esim. meta.title) tai avain on vain yhdella sivulla.
            # Yhteista arvoa ei kosketa, jotta mikaan sivu ei peri vaaraa tekstia.
            common_value = doc["common"].get(key)

        for fname, value in per_page.items():
            target = doc["pages"].setdefault(fname, collections.OrderedDict())
            if value == common_value:
                if key in target:               # tarpeeton poikkeus pois
                    del target[key]
                    changed.append(f"{fname}/{key} (poistettu, sama kuin yhteinen)")
            else:
                if target.get(key) != value:
                    target[key] = value
                    changed.append(f"{fname}/{key}")
                if key in doc["common"]:
                    overrides.append(f"{fname}/{key}")

    text = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    return path, text, changed, overrides


# --------------------------------------------------------------------------
def main():
    dry = "--kokeile" in sys.argv or "--dry-run" in sys.argv
    print("KOKEILU — mitään ei kirjoiteta\n" if dry else "Viedään sisältö sivustolle\n")

    writes, total, all_overrides = [], 0, []

    print("Suomi → HTML-sivut")
    for fname, slug in PAGES:
        new_src, changed = apply_fi(fname, slug, dry)
        if changed:
            writes.append((os.path.join(ROOT, fname), new_src))
            total += len(changed)
            print(f"  {fname:<20} {len(changed):>3} muutosta")
            for k in changed[:8]:
                print(f"      {k}")
            if len(changed) > 8:
                print(f"      … ja {len(changed) - 8} muuta")
        else:
            print(f"  {fname:<20}   – ei muutoksia")

    for lang in ("en", "de"):
        print(f"\n{lang.upper()} → assets/i18n/{lang}.json")
        path, text, changed, overrides = apply_i18n(lang, dry)
        all_overrides += [(lang, o) for o in overrides]
        if changed:
            writes.append((path, text))
            total += len(changed)
            print(f"  {len(changed)} muutosta")
            for k in changed[:8]:
                print(f"      {k}")
            if len(changed) > 8:
                print(f"      … ja {len(changed) - 8} muuta")
        else:
            print("  – ei muutoksia")

    if all_overrides:
        print(f"\nSivukohtaisia poikkeuksia yhteisiin teksteihin: {len(all_overrides)} kpl")
        print("  (sama avain, eri sisältö eri sivulla — tämä on sallittua)")

    if not writes:
        print("\nSivusto vastaa jo content/-kansiota. Ei tehtävää.")
        return 0

    if dry:
        print(f"\nYhteensä {total} muutosta {len(writes)} tiedostossa. "
              "Aja ilman --kokeile-valitsinta, niin muutokset kirjoitetaan.")
        return 0

    if ON_NETLIFY:
        print("\nAjetaan Netlifyn julkaisupalvelimella — varmuuskopiota ei tarvita.")
    else:
        stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        bdir = os.path.join(BACKUP, stamp)
        os.makedirs(bdir, exist_ok=True)
        for path, _ in writes:
            shutil.copy2(path, os.path.join(bdir, os.path.basename(path)))
        print(f"\nVarmuuskopio: {os.path.relpath(bdir, os.path.dirname(ROOT))}/"
              f"  (projektikansion ulkopuolella)")

    for path, text in writes:
        io.open(path, "w", encoding="utf-8").write(text)
    print(f"Kirjoitettu {len(writes)} tiedostoa, {total} muutosta.")

    # --- tarkistus ---------------------------------------------------------
    print("\nTarkistus:")
    ok = True
    for fname, slug in PAGES:
        want, got = load_content(slug, "fi"), read_page(fname)
        bad = [k for k, v in want.items() if tidy(str(v)) != tidy(got.get(k, ""))]
        print(f"  {fname:<20} {'ok' if not bad else 'POIKKEAA: ' + ', '.join(bad[:5])}")
        ok &= not bad
    for lang in ("en", "de"):
        d = json.load(io.open(os.path.join(ROOT, "assets", "i18n", lang + ".json"), encoding="utf-8"))
        merged_ok = True
        for fname, slug in PAGES:
            for key, value in load_content(slug, lang).items():
                got = d["pages"].get(fname, {}).get(key, d["common"].get(key))
                if got != value:
                    merged_ok = False
                    print(f"  {lang}: {slug}/{key} poikkeaa")
        print(f"  assets/i18n/{lang}.json   {'ok' if merged_ok else 'POIKKEAA'}")
        ok &= merged_ok

    print("\nKaikki kunnossa." if ok else "\nTarkista poikkeamat yllä.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
