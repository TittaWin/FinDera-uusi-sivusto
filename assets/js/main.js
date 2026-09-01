/* =========================================================================
   FinDera Consulting — käyttöliittymälogiikka
   Ei riippuvuuksia. Kunnioittaa prefers-reduced-motion -asetusta.
   ========================================================================= */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Sivuston juuriosoite paatellaan taman skriptin sijainnista, jotta
     kaannostiedostot loytyvat riippumatta siita, millaisella osoitteella
     sivu on avattu (esim. /palvelut, /palvelut.html tai alihakemisto). */
  var BASE = (function () {
    var s = document.currentScript;
    if (!s) {
      var all = document.getElementsByTagName("script");
      s = all[all.length - 1];
    }
    return s && s.src ? s.src.replace(/assets\/js\/[^\/]*$/, "") : "";
  })();

  /* --- 1. Sisääntuloanimaatiot vieritettäessä --------------------------- */
  function initReveal() {
    var items = document.querySelectorAll("[data-reveal]");
    if (!items.length) return;

    if (reduced || !("IntersectionObserver" in window)) {
      items.forEach(function (el) { el.classList.add("is-in"); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in");
        io.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });

    items.forEach(function (el) {
      // Porrastus: data-stagger antaa viiveen suhteessa sisarusten järjestykseen
      var group = el.closest("[data-stagger]");
      if (group && !el.style.getPropertyValue("--d")) {
        var sibs = Array.prototype.filter.call(
          group.querySelectorAll("[data-reveal]"),
          function (n) { return n.closest("[data-stagger]") === group; }
        );
        var i = sibs.indexOf(el);
        if (i > -1) el.style.setProperty("--d", i * 90 + "ms");
      }
      io.observe(el);
    });
  }

  /* --- 2. Lukujen laskuri ---------------------------------------------- */
  function initCounters() {
    var nums = document.querySelectorAll("[data-count]");
    if (!nums.length) return;

    function fmt(n) { return Math.round(n).toLocaleString("fi-FI"); }

    function render(el, value) {
      el.textContent = (el.getAttribute("data-prefix") || "") + fmt(value) +
        (el.getAttribute("data-suffix") || "");
    }

    function run(el) {
      var target = parseFloat(el.getAttribute("data-count"));
      if (reduced) { render(el, target); return; }

      var dur = 1500, t0 = null;
      function frame(ts) {
        if (t0 === null) t0 = ts;
        var p = Math.min((ts - t0) / dur, 1);
        render(el, target * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    }

    if (!("IntersectionObserver" in window)) {
      nums.forEach(function (el) { render(el, parseFloat(el.getAttribute("data-count"))); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        run(e.target);
        io.unobserve(e.target);
      });
    }, { threshold: 0.5 });
    nums.forEach(function (el) { io.observe(el); });
  }

  /* --- 3. Ylätunnisteen tila vieritettäessä ----------------------------- */
  function initHeader() {
    var header = document.querySelector(".site-header");
    if (!header) return;
    var ticking = false;
    function update() {
      header.classList.toggle("is-stuck", window.scrollY > 24);
      ticking = false;
    }
    window.addEventListener("scroll", function () {
      if (!ticking) { requestAnimationFrame(update); ticking = true; }
    }, { passive: true });
    update();
  }

  /* --- 4. Mobiilivalikko ------------------------------------------------ */
  function initNav() {
    var burger = document.querySelector(".burger");
    var nav = document.querySelector(".nav");
    if (!burger || !nav) return;

    var backdrop = document.createElement("div");
    backdrop.className = "nav-backdrop";
    document.body.appendChild(backdrop);

    function setOpen(open) {
      burger.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("is-open", open);
      backdrop.classList.toggle("is-on", open);
      document.body.style.overflow = open ? "hidden" : "";
    }
    burger.addEventListener("click", function () {
      setOpen(burger.getAttribute("aria-expanded") !== "true");
    });
    backdrop.addEventListener("click", function () { setOpen(false); });
    nav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () { setOpen(false); });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") setOpen(false);
    });
    window.addEventListener("resize", function () {
      if (window.innerWidth > 860) setOpen(false);
    });
  }

  /* --- 5. Hero: kevyt parallaksi ---------------------------------------- */
  function initParallax() {
    if (reduced) return;
    var media = document.querySelector(".hero__media img");
    if (!media) return;
    var ticking = false;
    function update() {
      var y = window.scrollY;
      if (y < window.innerHeight * 1.2) {
        media.style.transform = "translate3d(0," + (y * 0.16).toFixed(1) + "px,0) scale(1.02)";
      }
      ticking = false;
    }
    window.addEventListener("scroll", function () {
      if (!ticking) { requestAnimationFrame(update); ticking = true; }
    }, { passive: true });
  }

  /* --- 6. Kuvien pehmeä ilmestyminen ------------------------------------ */
  function initImages() {
    document.querySelectorAll("img.img-load").forEach(function (img) {
      if (img.complete && img.naturalWidth) img.classList.add("is-loaded");
      else img.addEventListener("load", function () { img.classList.add("is-loaded"); }, { once: true });
    });
  }

  /* --- 6b. Taustavideot: ladataan ja toistetaan vasta näkyvissä --------- */
  function initVideos() {
    var vids = document.querySelectorAll("video[data-src]");
    if (!vids.length) return;

    // "Vahenna liiketta" -asetuksella videota ei ladata lainkaan: nakyviin jaa
    // poster-kuva. Sailyttaa myos mobiilidataa.
    if (reduced) return;

    if (!("IntersectionObserver" in window)) return;

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var v = e.target;
        if (e.isIntersecting) {
          if (!v.src) { v.src = v.dataset.src; v.load(); }
          var p = v.play();
          if (p && p.catch) p.catch(function () { /* selain esti — poster jaa nakyviin */ });
        } else if (!v.paused) {
          v.pause();
        }
      });
    }, { rootMargin: "200px 0px", threshold: 0.01 });

    vids.forEach(function (v) { io.observe(v); });
  }

  /* --- 7. Logonauhan kahdennus loputonta vieritystä varten -------------- */
  function initMarquee() {
    document.querySelectorAll(".marquee__track").forEach(function (track) {
      if (track.dataset.cloned) return;
      track.dataset.cloned = "1";
      track.innerHTML += track.innerHTML;
    });
  }

  /* --- 8. Kielivalitsin ja käännökset ----------------------------------- */
  var I18N = (function () {
    var LANGS = { fi: "Suomi", en: "English", de: "Deutsch" };
    var cache = {};   // kieli -> sanakirja
    var baseFi = null;    // sivun oma, valmiiksi kirjoitettu sisältö
    // Sivun oma kieli. Suomenkieliset sivut ovat "fi", kansiossa en/ olevat
    // valmiiksi englanniksi kirjoitetut sivut "en". Tämä kieli on aina
    // sivulla itsellään, joten sitä ei haeta käännöstiedostosta.
    var PAGE_LANG = document.documentElement.lang || "fi";
    var current = PAGE_LANG;

    function snapshotFi() {
      if (baseFi) return;
      baseFi = {};
      document.querySelectorAll("[data-i18n]").forEach(function (el) {
        baseFi[el.getAttribute("data-i18n")] = el.innerHTML;
      });
      document.querySelectorAll("[data-i18n-attr]").forEach(function (el) {
        el.getAttribute("data-i18n-attr").split(",").forEach(function (pair) {
          var p = pair.trim().split(":");
          baseFi["@" + p[1]] = { el: el, attr: p[0], val: el.getAttribute(p[0]) };
        });
      });
    }

    function apply(dict, lang) {
      document.querySelectorAll("[data-i18n]").forEach(function (el) {
        var key = el.getAttribute("data-i18n");
        var val = lang === PAGE_LANG ? baseFi[key] : dict[key];
        if (typeof val === "string") el.innerHTML = val;
      });
      document.querySelectorAll("[data-i18n-attr]").forEach(function (el) {
        el.getAttribute("data-i18n-attr").split(",").forEach(function (pair) {
          var p = pair.trim(), idx = p.indexOf(":");
          var attr = p.slice(0, idx).trim(), key = p.slice(idx + 1).trim();
          var val = lang === PAGE_LANG
            ? (baseFi["@" + key] ? baseFi["@" + key].val : null)
            : dict[key];
          if (typeof val === "string") el.setAttribute(attr, val);
        });
      });
      document.documentElement.lang = lang;
      current = lang;
      try { localStorage.setItem("findera-lang", lang); } catch (e) {}

      var label = document.querySelector(".lang__current");
      if (label) label.textContent = lang.toUpperCase();
      document.querySelectorAll(".lang__menu button").forEach(function (b) {
        b.setAttribute("aria-selected", String(b.dataset.lang === lang));
      });
      document.body.classList.remove("is-translating");
    }

    // Sama avain (esim. ph.title) tarkoittaa eri asiaa eri sivuilla, joten
    // sanakirja koostuu yhteisestä osasta ja sivukohtaisesta osasta.
    // Netlify tarjoilee sivut myos ilman .html-paatetta (esim. /palvelut),
    // joten pelkka tiedostonimen tarkistus ei riita sivun tunnistamiseen.
    function pageName() {
      // Kansion en/ sivut kertovat lahtosivunsa, koska kaannosavaimet on
      // ryhmitelty suomenkielisen tiedostonimen mukaan.
      var named = document.documentElement.getAttribute("data-page");
      if (named) return named;
      var f = location.pathname.split("/").pop();
      if (!f) return "index.html";              // "/" tai "/alihakemisto/"
      if (/\.html?$/i.test(f)) return f;        // "/palvelut.html"
      return f + ".html";                       // "/palvelut"
    }

    function flatten(raw) {
      var dict = {}, page = pageName(), k;
      var common = raw.common || {};
      var pages = raw.pages || {};
      var own = pages[page] || {};
      for (k in common) if (common.hasOwnProperty(k)) dict[k] = common[k];
      for (k in own) if (own.hasOwnProperty(k)) dict[k] = own[k];
      return dict;
    }

    function set(lang) {
      if (!LANGS[lang] || lang === current) return;
      snapshotFi();
      if (lang === PAGE_LANG) { apply(null, PAGE_LANG); return; }
      if (cache[lang]) { apply(cache[lang], lang); return; }

      document.body.classList.add("is-translating");
      fetch(BASE + "assets/i18n/" + lang + ".json")
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
        .then(function (raw) {
          cache[lang] = flatten(raw);
          apply(cache[lang], lang);
        })
        .catch(function (err) {
          console.warn("Käännöstiedostoa ei voitu ladata:", err);
          document.body.classList.remove("is-translating");
        });
    }

    function init() {
      // Kampanja- ja laskeutumissivut ovat yksikielisiä: ne merkitään
      // <html data-no-i18n>. Ilman tätä aiemmin tallennettu kielivalinta
      // vaihtaisi sivun kieliattribuutin, vaikka tekstit pysyvät suomena.
      if (document.documentElement.hasAttribute("data-no-i18n")) return;
      snapshotFi();
      var wrap = document.querySelector(".lang");
      if (wrap) {
        var toggle = wrap.querySelector(".lang__toggle");
        toggle.addEventListener("click", function (e) {
          e.stopPropagation();
          wrap.classList.toggle("is-open");
          toggle.setAttribute("aria-expanded", String(wrap.classList.contains("is-open")));
        });
        wrap.querySelectorAll(".lang__menu button").forEach(function (b) {
          b.addEventListener("click", function () {
            // Kielilla, joilla on oma sivunsa, siirrytaan sivulle. Muut
            // vaihdetaan paikallaan kaannostiedostosta. Valinta talletetaan
            // ennen siirtymaa, jotta seuraava sivu ei vaihda kielta takaisin
            // aiemmin muistettuun.
            if (b.dataset.href) {
              try { localStorage.setItem("findera-lang", b.dataset.lang); } catch (e) {}
              location.href = b.dataset.href;
              return;
            }
            set(b.dataset.lang);
            wrap.classList.remove("is-open");
            toggle.setAttribute("aria-expanded", "false");
          });
        });
        document.addEventListener("click", function () {
          wrap.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
        });
      }

      // Kieli URL-parametrista tai muistista
      var q = new URLSearchParams(location.search).get("lang");
      var saved = null;
      try { saved = localStorage.getItem("findera-lang"); } catch (e) {}
      var want = q || saved;
      if (!want || want === PAGE_LANG) return;

      // Kielilla, joilla on oma sivunsa, ei vaihdeta tekstia paikallaan:
      // muuten englanti nakyisi suomenkielisessa osoitteessa. Osoitteessa
      // annettu ?lang= on tietoinen pyynto, joten se vie oikealle sivulle.
      var target = wrap && wrap.querySelector('.lang__menu button[data-lang="' + want + '"]');
      if (target && target.dataset.href) {
        if (q) location.replace(target.dataset.href);
        return;
      }
      set(want);
    }

    return { init: init, set: set };
  })();

  /* --- 9. Yhteydenottolomake -------------------------------------------- */
  function initForm() {
    var form = document.querySelector("form[data-contact]");
    if (!form) return;
    var status = form.querySelector(".form__status");
    var submit = form.querySelector("[type=submit]");

    function fieldOf(input) { return input.closest(".field"); }

    form.querySelectorAll("input, textarea, select").forEach(function (input) {
      input.addEventListener("blur", function () {
        var f = fieldOf(input);
        if (f) f.classList.toggle("is-invalid", !input.checkValidity());
      });
      input.addEventListener("input", function () {
        var f = fieldOf(input);
        if (f && input.checkValidity()) f.classList.remove("is-invalid");
      });
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      status.className = "form__status";

      // Hunajapurkki roskapostia vastaan
      var hp = form.querySelector("[name='bot-field'], [name='_gotcha']");
      if (hp && hp.value) return;

      var ok = true;
      form.querySelectorAll("input, textarea, select").forEach(function (input) {
        if (!input.checkValidity()) {
          ok = false;
          var f = fieldOf(input);
          if (f) f.classList.add("is-invalid");
        }
      });
      if (!ok) {
        var firstBad = form.querySelector(".is-invalid input, .is-invalid textarea, .is-invalid select");
        if (firstBad) firstBad.focus();
        status.className = "form__status is-err";
        status.textContent = form.dataset.msgInvalid || "Tarkista merkityt kentät.";
        return;
      }

      var endpoint = form.getAttribute("action");
      var isNetlify = form.hasAttribute("data-netlify");

      // Jos päätepistettä ei ole asetettu eikä Netlify Forms ole käytössä,
      // avataan varalta kävijän sähköpostiohjelma.
      if (!isNetlify && (!endpoint || endpoint.indexOf("PALVELUN-OSOITE") > -1)) {
        var d = new FormData(form);
        var body = [];
        d.forEach(function (v, k) {
          if (k.charAt(0) === "_" || !String(v).trim()) return;
          body.push(k + ": " + v);
        });
        window.location.href = "mailto:martin.brandt@findera.fi"
          + "?subject=" + encodeURIComponent("Yhteydenotto findera.fi-sivustolta")
          + "&body=" + encodeURIComponent(body.join("\n"));
        status.className = "form__status is-ok";
        status.textContent = form.dataset.msgMail || "Avataan sähköpostiohjelmasi…";
        return;
      }

      submit.disabled = true;
      var original = submit.querySelector("span") ? submit.querySelector("span").textContent : submit.textContent;
      if (submit.querySelector("span")) submit.querySelector("span").textContent = form.dataset.msgSending || "Lähetetään…";

      // Netlify Forms ottaa vastaan lomakedatan sivuston juuresta
      // x-www-form-urlencoded -muodossa, kun mukana on form-name-kenttä.
      var request = isNetlify
        ? fetch("/", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams(new FormData(form)).toString()
          })
        : fetch(endpoint, {
            method: "POST",
            body: new FormData(form),
            headers: { Accept: "application/json" }
          });

      request
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          form.reset();
          status.className = "form__status is-ok";
          status.textContent = form.dataset.msgOk || "Kiitos viestistäsi! Olen yhteydessä pian.";
        })
        .catch(function () {
          status.className = "form__status is-err";
          status.textContent = form.dataset.msgErr ||
            "Lähetys ei onnistunut. Lähetäthän viestin osoitteeseen martin.brandt@findera.fi.";
        })
        .finally(function () {
          submit.disabled = false;
          if (submit.querySelector("span")) submit.querySelector("span").textContent = original;
        });
    });
  }

  /* --- 10. Käynnistys ---------------------------------------------------- */
  function boot() {
    initHeader();
    initNav();
    initReveal();
    initCounters();
    initParallax();
    initImages();
    initVideos();
    initMarquee();
    initForm();
    I18N.init();
    document.documentElement.classList.add("js-ready");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  window.FinDera = { setLang: I18N.set };
})();
