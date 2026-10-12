(function () {
  "use strict";
  var root = document.documentElement;

  /* Theme toggle (remembers the choice in this browser only) */
  var tbtn = document.getElementById("theme-toggle");
  if (tbtn) tbtn.addEventListener("click", function () {
    var cur = root.getAttribute("data-theme");
    if (!cur) cur = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    var next = cur === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) {}
  });

  /* Compact menu on narrow screens */
  var mbtn = document.getElementById("menu-btn"), nav = document.getElementById("site-nav");
  if (mbtn && nav) {
    var setOpen = function (open) { nav.classList.toggle("open", open); mbtn.setAttribute("aria-expanded", open ? "true" : "false"); };
    mbtn.addEventListener("click", function () { setOpen(!nav.classList.contains("open")); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && nav.classList.contains("open")) { setOpen(false); mbtn.focus(); } });
    nav.addEventListener("click", function (e) { if (e.target.closest("a")) setOpen(false); });
  }

  /* Copy helpers: copy the text of the element named by data-copy or data-bib */
  function copyFrom(btn, el) {
    var text = el.textContent.trim(), label = btn.textContent;
    function done() { btn.textContent = btn.getAttribute("data-done") || label; setTimeout(function () { btn.textContent = label; }, 1600); }
    function fallback() {
      el.hidden = false;
      var r = document.createRange(); r.selectNodeContents(el);
      var s = getSelection(); s.removeAllRanges(); s.addRange(r);
    }
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback);
      else fallback();
    } catch (e) { fallback(); }
  }
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-copy],[data-bib]");
    if (!b) return;
    var el = document.getElementById(b.getAttribute("data-copy") || b.getAttribute("data-bib"));
    if (el) copyFrom(b, el);
  });


  /* Publications: search + type + topic + year filters. A #topic hash preselects the topic. */
  var pq = document.getElementById("pub-q");
  if (pq) {
    var ptype = document.getElementById("pub-type"), ptopic = document.getElementById("pub-topic"), pyear = document.getElementById("pub-year");
    var items = document.querySelectorAll(".year-group .pub"), groups = document.querySelectorAll(".year-group");
    var pcount = document.getElementById("pub-count"), pempty = document.getElementById("pub-empty");
    var norm = function (s) { return s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase(); };
    items.forEach(function (p) { p._t = norm(p.querySelector(".pub-body").textContent); });
    var h = (location.hash || "").slice(1);
    if (h && ptopic.querySelector('option[value="' + h + '"]')) ptopic.value = h;
    var papply = function () {
      var terms = norm(pq.value).split(/\s+/).filter(Boolean), n = 0;
      items.forEach(function (p) {
        var ok = (ptype.value === "all" || p.dataset.type === ptype.value)
          && (ptopic.value === "all" || (" " + p.dataset.topics + " ").indexOf(" " + ptopic.value + " ") >= 0)
          && (pyear.value === "all" || p.dataset.year === pyear.value)
          && terms.every(function (t) { return p._t.indexOf(t) >= 0; });
        p.hidden = !ok; if (ok) n++;
      });
      groups.forEach(function (g) { g.hidden = !g.querySelector(".pub:not([hidden])"); });
      pcount.textContent = n + " " + pcount.dataset.label;
      pempty.hidden = n > 0;
    };
    pq.addEventListener("input", papply);
    [ptype, ptopic, pyear].forEach(function (s) { s.addEventListener("change", papply); });
    papply();
  }

  /* Projects: role + area filters */
  var prole = document.getElementById("proj-role");
  if (prole) {
    var parea = document.getElementById("proj-area"), rows = document.querySelectorAll(".project");
    var pc = document.getElementById("proj-count"), pe = document.getElementById("proj-empty");
    var japply = function () {
      var n = 0;
      rows.forEach(function (r) {
        var ok = (prole.value === "all" || r.dataset.role === prole.value) && (parea.value === "all" || r.dataset.area === parea.value);
        r.hidden = !ok; if (ok) n++;
      });
      pc.textContent = n + " " + pc.dataset.label; pe.hidden = n > 0;
    };
    prole.addEventListener("change", japply); parea.addEventListener("change", japply);
  }

  /* Research lines: highlight the matching part of the network drawing */
  var topo = document.getElementById("topo"), lines = document.getElementById("lines");
  if (topo && lines) {
    var parts = topo.querySelectorAll("[data-line]");
    var activate = function (id) {
      topo.classList.toggle("is-active", !!id);
      parts.forEach(function (p) { p.classList.toggle("on", !!id && p.getAttribute("data-line").split(" ").indexOf(id) >= 0); });
      lines.querySelectorAll(".line").forEach(function (l) { l.classList.toggle("is-on", l.getAttribute("data-line") === id); });
    };
    lines.querySelectorAll(".line").forEach(function (l) {
      var id = l.getAttribute("data-line");
      l.addEventListener("mouseenter", function () { activate(id); });
      l.addEventListener("focus", function () { activate(id); });
      l.addEventListener("mouseleave", function () { activate(null); });
      l.addEventListener("blur", function () { activate(null); });
    });
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
      topo.querySelectorAll("animateMotion").forEach(function (a) { a.remove(); });
    }
  }
})();
