# FinDera Consulting — ohjeet Claudelle

FinDera Consultingin verkkosivusto, **https://www.findera.fi**. Staattinen
sivusto: HTML, CSS ja JavaScript ilman riippuvuuksia. Keskustele suomeksi.

Tämä tiedosto kertoo, mitä pitää tietää ennen muutoksia. Ylläpito-ohje on
`README.md`, tekstien muokkausohje `content/README.md`.

## Tärkeää: repo on julkinen ja juuri julkaistaan

- **Repo on julkinen.** Älä lisää tänne sisäisiä muistiinpanoja, asiakastietoja
  äläkä salaisuuksia.
- **Netlify julkaisee koko repon juuren** (`publish = "."`). Jokainen juureen
  lisätty tiedosto näkyy sivustolla osoitteessa `www.findera.fi/<tiedosto>`.
  Tämä tiedosto on estetty `netlify.toml`:n säännöllä — älä poista sitä.

## Ennen kuin muutat mitään

- **Hae uusin versio ensin:** `git fetch && git status -sb`. Sisältöä muokataan
  myös GitHubin selaimessa. Jos `behind` > 0, rebase ennen omia muutoksia.
- **`main` on tuotanto.** Netlify rakentaa ja julkaisee jokaisen `main`-commitin.
  Kysy ennen kuin pushaat `main`iin.
- Julkaisun build-komento (`netlify.toml`) ajaa `tools/apply_content.py` ja
  `tools/build_lang.py`. Jos kumpi tahansa epäonnistuu, julkaisu keskeytyy ja
  edellinen versio jää pystyyn.

## Kielet

- **Suomi on ensisijainen kieli.** Suomenkieliset tekstit ovat suoraan
  HTML-sivuilla, jotta ne toimivat ilman JavaScriptiä ja indeksoituvat.
- **Englanti:** `tools/build_lang.py` luo staattiset sivut kansioon `en/`
  suomenkielisistä sivuista ja tiedostosta `assets/i18n/en.json`.
  **Älä muokkaa `en/`-kansiota käsin** — muutokset ylikirjoitetaan.
- **Saksa** ladataan selaimessa tiedostosta `assets/i18n/de.json` kielivalinnan yhteydessä.

## Tekstien muokkaaminen

Suositeltu tapa on `content/<sivu>/<kieli>.json`. Kaikissa kolmessa
kielitiedostossa on täsmälleen samat kentät.

```bash
python3 tools/apply_content.py --kokeile   # näyttää mitä muuttuisi
python3 tools/apply_content.py             # vie tekstit sivuille
python3 tools/build_lang.py                # päivittää en/-sivut
```

Suomenkielisen tekstin voi korjata myös suoraan HTML:ään. **Älä koske
`data-i18n`-attribuutteihin** — niiden avulla käännökset löytävät paikkansa.

## Sivujen yhteiset osat

Sivuilla ei ole yhteistä layout-tiedostoa. Yläosan skriptit (esim. Google
Analytics), ylä- ja alatunniste sekä logo-SVG on kopioitu jokaiselle sivulle
erikseen. Muutos tehdään kaikkiin suomenkielisiin lähdesivuihin (`index`,
`palvelut`, `projektit`, `minusta`, `yhteystiedot`, `tietosuoja`, `kiitos`,
`landing1`, `404`), ja sen jälkeen ajetaan `tools/build_lang.py`.

## Kuvat ja logot

- `tools/build_images.py`, `tools/build_logos.py` ja
  `tools/build_landing_images.py` lukevat lähdekuvia ylläpitäjän koneelta
  repon ulkopuolelta. **Niitä ei voi ajaa pilvi- tai selainistunnossa.**
- Kuvat yhtenäistetään tarkoituksella: sama sävynkorjaus ja kiinteät kuvasuhteet,
  jotta eri vuosien kuvat näyttävät yhtenäisiltä.
- `build_images.py`:n `MANIFEST`-rivin viimeinen luku on rajauksen pystypainopiste
  (0 = ylhäältä, 1 = alhaalta). Ihmiset ovat kuvien pääosassa, joten rajaa
  mieluummin alempaa kuin ylempää (tyypillisesti 0.5–0.95).
- Referenssilogot: etusivun nauhassa yksivärisinä, Projektit-sivun korteissa
  omissa väreissään. Tietoinen jako.
- Logo on vektoroitu SVG. **Logovideota ei käytetä**, koska siinä ei ole
  läpinäkyvyyttä ja se näkyisi harmaana laatikkona tummalla taustalla.

## Osoitteet, välimuisti ja lomake

- Osoitteet ovat päätteettömiä (`/palvelut`). Vanhat `.html`-osoitteet ohjataan
  `netlify.toml`:ssa. Ohjaussäännöt tarvitsevat `force = true`, muuten olemassa
  oleva tiedosto voittaa. `404.html`:lle ei tehdä ohjausta.
- Kuvatiedostojen nimet pysyvät samoina päivitysten välillä, joten
  `assets/`-tiedostoille on tarkoituksella `no-cache`. Fonteilla on pitkä välimuisti.
- Yhteydenottolomake käyttää Netlify Formsia (lomakkeen nimi `yhteydenotto`).
  Lomakkeen tunnistus ja sähköposti-ilmoitus asetetaan Netlifyn hallinnasta,
  eivät tiedostoista.
- Verkkotunnuksen DNS ei ole Netlifyssä. **Älä ota Netlify DNS:ää käyttöön** —
  se poistaisi verkkotunnuksen sähköpostitietueet.

## Paikallinen esikatselu

```bash
python3 -m http.server 8765
```

Päätteettömät linkit eivät toimi paikallisesti, joten avaa sivut tiedostonimellä,
esim. `http://localhost:8765/palvelut.html`.
