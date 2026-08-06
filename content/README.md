# Sisältökansio — sivuston kaikki tekstit yhdessä paikassa

Tässä kansiossa on jokaisen sivun jokainen teksti omana kenttänään, kolmella
kielellä. Tarkoitus on, että tekstejä voi muokata koskematta HTML-koodiin.

```
content/
  index/          fi.json  en.json  de.json     Etusivu
  palvelut/       fi.json  en.json  de.json     Palvelut
  projektit/      fi.json  en.json  de.json     Projektit ja referenssit
  minusta/        fi.json  en.json  de.json     Minusta
  yhteystiedot/   fi.json  en.json  de.json     Yhteystiedot
```

Kaikissa kolmessa kielitiedostossa on **täsmälleen samat kentät samassa
järjestyksessä**, joten niitä voi verrata rinnakkain.

---

## Miten tekstiä muokataan

Avaa tiedosto tekstieditorissa (esim. VS Code). Jokaista tekstiä kohti on kaksi
riviä: itse teksti ja sen selite.

```json
"hero.lead": "Yhdistän suomalaiset hankkeet ja organisaatiot oikeisiin kohteisiin…",
"hero.lead.description": "Etusivun pääkuva-osio — ingressi.",
```

**Muuta vain lainausmerkkien sisällä olevaa tekstiä.** Rivit, joiden avain
päättyy sanaan `.description`, ovat ohjeita — ne eivät näy sivustolla.

Kolme sääntöä, joita kannattaa noudattaa:

1. **Älä muuta avainten nimiä** (`"hero.lead"`). Ne kertovat, mihin kohtaan
   sivustoa teksti kuuluu.
2. **Säilytä pilkut ja lainausmerkit.** Jos tekstissä tarvitaan lainausmerkki,
   kirjoita se muodossa `\"`.
3. **Jos tekstissä on HTML-merkintää** kuten `<em>` tai `<strong>`, jätä tagit
   paikoilleen ja muuta vain niiden välissä oleva teksti. Selite kertoo aina,
   kun kentässä on merkintää.

Muutosten jälkeen kannattaa tarkistaa, että tiedosto on yhä kelvollista JSONia.
VS Code huomauttaa virheestä punaisella aaltoviivalla.

---

## Yhteiset tekstit

Osa teksteistä esiintyy kaikilla sivuilla: päävalikko, alatunniste,
painikkeiden tekstit ja yhteydenottokehotus. Ne ovat mukana jokaisen sivun
tiedostossa, jotta sivu on kokonaisuutena luettavissa yhdestä paikasta.

Selitteessä lukee tällöin: *"Yhteinen kaikille sivuille — jos muutat tätä,
muuta sama teksti myös muiden sivujen tiedostoihin."* Tämä kannattaa ottaa
tosissaan, muuten valikko lukee eri sivuilla eri tavoin.

---

## Näin muutos siirtyy sivustolle

Työnkulku on kolmivaiheinen:

```
1. Muokkaa tekstit  →  content/<sivu>/<kieli>.json
2. Vie sivustolle   →  python3 tools/apply_content.py
3. Julkaise         →  raahaa projektikansio Netlifyyn
```

Toinen vaihe kirjoittaa tekstit sinne, mistä sivusto ne oikeasti lukee:
suomenkieliset tekstit HTML-sivuille ja muut tiedostoihin
`assets/i18n/en.json` ja `de.json`.

### Katso ensin mitä muuttuisi

```bash
python3 tools/apply_content.py --kokeile
```

Tämä ei kirjoita mitään, vaan listaa muutokset. Kannattaa ajaa aina ensin.

### Vie muutokset

```bash
python3 tools/apply_content.py
```

Skripti tekee kolme asiaa itsestään:

* **Varmuuskopioi** muuttuvat tiedostot kansioon
  `FinDera-varmuuskopiot/<päiväys>/`. Se on projektikansion ulkopuolella, joten
  varmuuskopiot eivät päädy Netlifyyn.
* **Muuttaa vain ne kohdat, jotka oikeasti muuttuivat.** Muu koodi jää
  koskemattomaksi ja tekstin sisennys säilyy siistinä.
* **Tarkistaa lopuksi**, että sivustolta luettu sisältö vastaa tätä kansiota.
  Jos jokin ei täsmää, skripti kertoo mikä.

### Jos jokin menee pieleen

Kopioi tiedostot takaisin varmuuskopiokansiosta projektikansioon.

---

## Sama teksti eri sivuilla eri sisällöllä

Joissain kohdissa sama kenttä on tarkoituksella erilainen eri sivuilla.
Esimerkiksi `aii.1.desc` on etusivulla yhden rivin mittainen tiivistelmä ja
Palvelut-sivulla koko kappale. Tämä on sallittua — skripti tunnistaa tilanteen
ja tallentaa poikkeavan tekstin sivukohtaisesti.

Jos taas kirjoitat saman tekstin samaksi kaikille sivuille, skripti siivoaa
tarpeettoman poikkeuksen pois automaattisesti.

---

## Kansion päivittäminen sivustolta

Jos sivustolle lisätään uusia tekstejä suoraan HTML:ään, tämän kansion saa
päivittämään vastaamaan sivuston nykytilaa komennolla:

```bash
python3 tools/build_content.py
```

**Huom:** komento kirjoittaa kaikki tiedostot uudelleen sivuston nykyisestä
sisällöstä. Jos olet muokannut tekstejä täällä mutta et ole vielä ajanut
`apply_content.py`-skriptiä, ne katoavat. Aja tämä vain silloin, kun
`content/`-kansiossa ei ole viemättömiä muutoksia.
