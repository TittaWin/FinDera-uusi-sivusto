/* =========================================================================
   FinDera Consulting — evästesuostumusbanneri
   ----------------------------------------------------------------------------
   Erillinen, riippumaton tiedosto (ei kosketa main.js:ää eikä data-i18n-
   sisältöputkea): teksti on tässä sanakirjana kolmella kielellä, koska
   banneri on sama joka sivulla eikä siksi kuulu sivukohtaiseen
   content/-kansioon (samoin kuin Cloudflaren ja Googlen mittausskriptit
   ovat suoraan HTML:ssä, eivät content/-kansiossa).

   Näkyy heti ensimmäisellä latauksella, jos kävijä ei ole vielä valinnut
   mitään — ei viivettä, koska GA4 ei mittaa mitään ennen valintaa joka
   tapauksessa (ks. tietosuoja.html:n <head>, Consent Mode -oletus
   "denied"). Reagoi kielenvaihtoon ilman sivun uudelleenlatausta, koska
   saksa vaihtuu main.js:ssä paikallaan (<html lang>-attribuutin kautta).

   Sisääntuloanimaatio on CSS:ssä (assets/css/style.css), joka jo
   kunnioittaa prefers-reduced-motion -asetusta koko sivustolla — tätä
   tiedostoa ei siksi tarvitse erikseen haarauttaa sen mukaan.
   ========================================================================= */
(function () {
  "use strict";

  var STORAGE_KEY = "findera-evasteet";
  var VERSION = 1;

  var TEKSTIT = {
    fi: {
      teksti: "Käytämme Google Analyticsia ymmärtääksemme, miten sivustoa käytetään. Se ei käynnisty ilman lupaasi.",
      lisatietoa: "Lue lisää",
      hyvaksy: "Hyväksy",
      hylkaa: "Hylkää",
      sulje: "Sulje ja hylkää evästeet",
    },
    en: {
      teksti: "We use Google Analytics to understand how the site is used. It does not start without your permission.",
      lisatietoa: "Read more",
      hyvaksy: "Accept",
      hylkaa: "Decline",
      sulje: "Close and decline cookies",
    },
    de: {
      teksti: "Wir nutzen Google Analytics, um zu verstehen, wie die Website genutzt wird. Es startet nicht ohne Ihre Zustimmung.",
      lisatietoa: "Mehr erfahren",
      hyvaksy: "Akzeptieren",
      hylkaa: "Ablehnen",
      sulje: "Schließen und Cookies ablehnen",
    },
  };

  var LINKKI = {
    fi: "/tietosuoja#evasteet",
    en: "/en/privacy#evasteet",
    de: "/tietosuoja#evasteet",
  };

  function lueTallennettu() {
    try {
      var raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
      if (!raw || raw.version !== VERSION) return null;
      return raw.status === "granted" || raw.status === "denied" ? raw.status : null;
    } catch (e) {
      return null;
    }
  }

  function tallenna(status) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ status: status, version: VERSION }));
    } catch (e) {
      /* localStorage voi olla estetty — bannerin näkyy silloin uudelleen
         seuraavalla käynnillä, evästettä ei silti koskaan pakoteta. */
    }
  }

  function paivitaSuostumus(status) {
    if (window.gtag) {
      window.gtag("consent", "update", { analytics_storage: status });
    }
    tallenna(status);
  }

  function kieli() {
    var lang = document.documentElement.lang;
    return TEKSTIT[lang] ? lang : "fi";
  }

  function rakennaBanneri() {
    var wrap = document.createElement("div");
    wrap.className = "evaste-banneri";
    wrap.setAttribute("role", "dialog");
    wrap.setAttribute("aria-modal", "false");
    wrap.setAttribute("aria-label", "Evästeasetukset");
    wrap.tabIndex = -1;

    wrap.innerHTML =
      '<button type="button" class="evaste-banneri__sulje" aria-label=""></button>' +
      '<p class="evaste-banneri__teksti"></p>' +
      '<div class="evaste-banneri__painikkeet">' +
      '<button type="button" class="btn btn--ghost evaste-banneri__hylkaa"></button>' +
      '<button type="button" class="btn evaste-banneri__hyvaksy"></button>' +
      "</div>";

    document.body.appendChild(wrap);
    return wrap;
  }

  function paivitaTekstit(wrap) {
    var t = TEKSTIT[kieli()];
    var linkki = LINKKI[kieli()] || LINKKI.fi;

    wrap.querySelector(".evaste-banneri__sulje").setAttribute("aria-label", t.sulje);
    wrap.querySelector(".evaste-banneri__teksti").innerHTML =
      t.teksti + ' <a href="' + linkki + '" class="evaste-banneri__linkki">' + t.lisatietoa + "</a>";
    wrap.querySelector(".evaste-banneri__hylkaa").textContent = t.hylkaa;
    wrap.querySelector(".evaste-banneri__hyvaksy").textContent = t.hyvaksy;
  }

  function nayta() {
    var wrap = rakennaBanneri();
    paivitaTekstit(wrap);
    wrap.focus();

    function paata(status) {
      paivitaSuostumus(status);
      wrap.removeEventListener("keydown", onKeyDown);
      wrap.remove();
    }

    function onKeyDown(e) {
      if (e.key === "Escape") paata("denied");
    }

    wrap.querySelector(".evaste-banneri__sulje").addEventListener("click", function () {
      paata("denied");
    });
    wrap.querySelector(".evaste-banneri__hylkaa").addEventListener("click", function () {
      paata("denied");
    });
    wrap.querySelector(".evaste-banneri__hyvaksy").addEventListener("click", function () {
      paata("granted");
    });
    wrap.addEventListener("keydown", onKeyDown);

    // Saksa vaihtuu paikallaan main.js:ssä <html lang>-attribuutin kautta;
    // banneri seuraa mukana ilman sivun uudelleenlatausta.
    var tarkkailija = new MutationObserver(function () {
      paivitaTekstit(wrap);
    });
    tarkkailija.observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
  }

  function boot() {
    if (lueTallennettu() === null) nayta();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
