/* Shared book runtime: language toggle, animated-scene player, SVG helpers. */
(function () {
  var KEY = "harness-book-lang";
  var root = document.documentElement;
  function load() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function save(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  function apply(l) {
    root.setAttribute("data-lang", l);
    root.setAttribute("lang", l === "hi" ? "hi-Latn" : "en");
    document.querySelectorAll("[data-setlang]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-setlang") === l));
    });
    (typeof langListeners !== "undefined" ? langListeners : []).forEach(function (fn) { fn(l); });
  }
  apply(load() === "hi" ? "hi" : "en");
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest("[data-setlang]");
    if (!b) return;
    var l = b.getAttribute("data-setlang");
    save(l); apply(l);
  });

  var NS = "http://www.w3.org/2000/svg";
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Haron the robot: one sprite for every page. viewBox 0 0 120 140.
     The face screen uses fixed colours so it reads the same in light and dark themes. */
  var SPRITE =
    '<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>' +
    '<linearGradient id="tk-shell" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:var(--signal-soft)"/><stop offset="1" style="stop-color:var(--fig-bg)"/></linearGradient>' +
    '<radialGradient id="tk-eye" cx="0.5" cy="0.4" r="0.6"><stop offset="0" stop-color="#e8fdff"/><stop offset="0.55" stop-color="#5fe3f2"/><stop offset="1" stop-color="#1aa7b8"/></radialGradient>' +
    '<symbol id="tokku" viewBox="0 0 120 140">' +
      '<ellipse cx="60" cy="134" rx="30" ry="4" style="fill:var(--ink);opacity:.12"/>' +
      // antenna
      '<path d="M60 24 V12" style="stroke:var(--ink-2);stroke-width:3;stroke-linecap:round"/>' +
      '<circle cx="60" cy="9" r="6.5" style="fill:var(--amber)"/><circle cx="58" cy="7" r="2" fill="#fff" opacity=".8"/>' +
      // ears
      '<rect x="7" y="44" width="13" height="24" rx="6" style="fill:var(--signal)"/>' +
      '<rect x="100" y="44" width="13" height="24" rx="6" style="fill:var(--signal)"/>' +
      // head
      '<rect x="16" y="22" width="88" height="66" rx="28" style="fill:url(#tk-shell);stroke:var(--signal);stroke-width:3"/>' +
      '<path d="M30 30 Q60 22 90 30" style="fill:none;stroke:#fff;stroke-width:3;stroke-linecap:round;opacity:.55"/>' +
      // face screen
      '<rect x="27" y="36" width="66" height="40" rx="18" fill="#10222c"/>' +
      '<ellipse class="tk-eyes" cx="45" cy="53" rx="7" ry="8.5" fill="url(#tk-eye)"/>' +
      '<ellipse class="tk-eyes" cx="75" cy="53" rx="7" ry="8.5" fill="url(#tk-eye)"/>' +
      '<circle cx="47" cy="50" r="2" fill="#fff"/><circle cx="77" cy="50" r="2" fill="#fff"/>' +
      '<path d="M52 66 Q60 72 68 66" fill="none" stroke="#5fe3f2" stroke-width="3" stroke-linecap="round"/>' +
      // cheeks
      '<ellipse cx="25" cy="72" rx="5" ry="3.2" style="fill:var(--c6);opacity:.55"/>' +
      '<ellipse cx="95" cy="72" rx="5" ry="3.2" style="fill:var(--c6);opacity:.55"/>' +
      // neck + body
      '<rect x="51" y="87" width="18" height="7" rx="2" style="fill:var(--signal)"/>' +
      '<rect x="31" y="93" width="58" height="38" rx="16" style="fill:url(#tk-shell);stroke:var(--signal);stroke-width:3"/>' +
      '<rect x="45" y="102" width="30" height="18" rx="6" fill="#10222c"/>' +
      '<path d="M50 111 h6 l3 -5 l4 10 l3 -5 h5" fill="none" stroke="#5fe3f2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>' +
      // arms: left resting, right waving
      '<path d="M32 104 Q20 110 18 122" style="fill:none;stroke:var(--signal);stroke-width:7;stroke-linecap:round"/>' +
      '<circle cx="18" cy="123" r="5" style="fill:var(--amber)"/>' +
      '<path d="M88 104 Q101 98 104 86" style="fill:none;stroke:var(--signal);stroke-width:7;stroke-linecap:round"/>' +
      '<circle cx="104" cy="84" r="5" style="fill:var(--amber)"/>' +
    '</symbol></defs></svg>';
  function injectSprite() {
    if (document.getElementById("tokku")) return;
    var d = document.createElement("div");
    d.innerHTML = SPRITE;
    document.body.insertBefore(d.firstChild, document.body.firstChild);
  }
  if (document.body) injectSprite(); else document.addEventListener("DOMContentLoaded", injectSprite);
  var langListeners = [];

  // E(parent, tag, attrs, text) -> new SVG element
  function E(p, tag, a, txt) {
    var e = document.createElementNS(NS, tag);
    if (a) for (var k in a) e.setAttribute(k, a[k]);
    if (txt != null) e.textContent = txt;
    if (p) p.appendChild(e);
    return e;
  }
  // BI(parent, attrs, english, hinglish) -> <g> holding both language variants of an SVG <text>
  function BI(p, a, en, hi) {
    var g = E(p, "g");
    var base = a["class"] ? a["class"] + " " : "";
    var ae = Object.assign({}, a, { "class": base + "l-en" });
    var ah = Object.assign({}, a, { "class": base + "l-hi" });
    E(g, "text", ae, en);
    E(g, "text", ah, hi == null ? en : hi);
    return g;
  }
  function show(el, on) { el.style.opacity = on ? 1 : 0; }
  function move(el, x, y) { el.style.transform = "translate(" + x + "px," + (y || 0) + "px)"; }

  /* Scene player.
     scene(figureEl, captions, render)
     captions: [[en, hi], ...] one per step; render(i) must set the WHOLE state for step i
     (so Prev/Next/jumps all work). Autoplays once when first scrolled into view. */
  function scene(fig, caps, render, opts) {
    opts = opts || {};
    var n = caps.length, i = 0, timer = null, delay = opts.delay || 2800;
    var bar = document.createElement("div"); bar.className = "scene-bar";
    bar.innerHTML =
      '<button type="button" class="prev" aria-label="Previous step">◀</button>' +
      '<button type="button" class="play"><span class="l-en">Play</span><span class="l-hi">Chalao</span></button>' +
      '<button type="button" class="next" aria-label="Next step">▶</button>' +
      '<button type="button" class="restart"><span class="l-en">Restart</span><span class="l-hi">Dobara</span></button>' +
      '<div class="dots" aria-hidden="true"></div>';
    var cap = document.createElement("p"); cap.className = "scene-cap"; cap.setAttribute("aria-live", "polite");
    fig.appendChild(bar); fig.appendChild(cap);
    var dots = bar.querySelector(".dots");
    for (var d = 0; d < n; d++) dots.appendChild(document.createElement("span"));
    var playBtn = bar.querySelector(".play");

    function go(k) {
      i = Math.max(0, Math.min(n - 1, k));
      render(i);
      cap.innerHTML = '<span class="stp"><span class="l-en">Step</span><span class="l-hi">Step</span> ' + (i + 1) + " / " + n + "</span>" +
        '<span class="l-en">' + caps[i][0] + '</span><span class="l-hi">' + caps[i][1] + "</span>";
      [].forEach.call(dots.children, function (s, j) { s.className = j <= i ? "on" : ""; });
      bar.querySelector(".prev").disabled = i === 0;
      bar.querySelector(".next").disabled = i === n - 1;
    }
    function stop() {
      clearInterval(timer); timer = null;
      playBtn.innerHTML = '<span class="l-en">Play</span><span class="l-hi">Chalao</span>';
    }
    function play() {
      if (i === n - 1) go(0);
      playBtn.innerHTML = '<span class="l-en">Pause</span><span class="l-hi">Roko</span>';
      timer = setInterval(function () { if (i >= n - 1) { stop(); return; } go(i + 1); }, delay);
    }
    playBtn.addEventListener("click", function () { timer ? stop() : play(); });
    bar.querySelector(".prev").addEventListener("click", function () { stop(); go(i - 1); });
    bar.querySelector(".next").addEventListener("click", function () { stop(); go(i + 1); });
    bar.querySelector(".restart").addEventListener("click", function () { stop(); go(0); play(); });

    go(0);
    langListeners.push(function () { render(i); });   // re-draw language-dependent SVG text
    if (!reduced && "IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (ents) {
        ents.forEach(function (en) { if (en.isIntersecting) { io.disconnect(); if (!timer && i === 0) play(); } });
      }, { threshold: 0.6 });
      io.observe(fig);
    }
    return { go: go };
  }

  /* ---------- drawing helpers shared by chapters ---------- */
  function tokku(p, x, y, w) { return E(p, "use", { href: "#tokku", x: x, y: y, width: w, height: w * 140 / 120 }); }
  // box(p, {x,y,w,h,cls,en,hi,sen,shi,fs,mono}) -> <g class="anim"> with a rect and 1-2 bilingual lines
  function box(p, o) {
    var g = E(p, "g", { "class": "anim" });
    E(g, "rect", { x: o.x, y: o.y, width: o.w, height: o.h, rx: o.rx == null ? 6 : o.rx, "class": o.cls || "box" });
    var cy = o.y + o.h / 2 + (o.sen ? -4 : 5);
    BI(g, { x: o.x + o.w / 2, y: cy, "text-anchor": "middle", "font-weight": 600, "font-size": o.fs || 13,
            "class": o.mono ? "mono" : "" }, o.en, o.hi);
    if (o.sen) BI(g, { x: o.x + o.w / 2, y: cy + 17, "text-anchor": "middle", "class": "muted", "font-size": 11 }, o.sen, o.shi);
    return g;
  }
  function arrowDefs(svg) {
    if (svg.querySelector("marker")) return;
    var d = E(svg, "defs");
    [["ah", "var(--ink-2)"], ["ah-sig", "var(--signal)"], ["ah-amb", "var(--amber)"], ["ah-plm", "var(--plum)"]].forEach(function (m) {
      var mk = E(d, "marker", { id: svg.id + "-" + m[0], viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse" });
      E(mk, "path", { d: "M0,0 L10,5 L0,10 z", style: "fill:" + m[1] });
    });
  }
  // arrow(svg, parent, x1,y1,x2,y2, kind) kind: "" | "sig" | "amb" | "plm"; optional curve offset
  function arrow(svg, p, x1, y1, x2, y2, kind, bend) {
    arrowDefs(svg);
    var cls = kind ? "line-" + (kind === "plm" ? "sig" : kind) : "line";
    var d = bend ? "M" + x1 + " " + y1 + " Q" + ((x1 + x2) / 2) + " " + ((y1 + y2) / 2 + bend) + " " + x2 + " " + y2
                 : "M" + x1 + " " + y1 + " L" + x2 + " " + y2;
    var a = E(p, "path", { d: d, "class": cls + " anim", "stroke-width": 1.8, fill: "none",
      "marker-end": "url(#" + svg.id + "-ah" + (kind ? "-" + kind : "") + ")" });
    if (kind === "plm") a.style.stroke = "var(--plum)";
    return a;
  }
  function cls(el, c) { el.setAttribute("class", "anim " + c); }
  function onLang(fn) { langListeners.push(fn); }

  window.Book = { E: E, BI: BI, show: show, move: move, scene: scene, reduced: reduced,
    tokku: tokku, box: box, arrow: arrow, cls: cls, onLang: onLang,
    lang: function () { return root.getAttribute("data-lang") || "en"; } };
})();

/* Theme: follows the system until the reader picks light or dark in the menu; saved per browser. */
(function () {
  var KEY = "harness-book-theme", root = document.documentElement;
  var mq = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
  var choice = null;
  try { choice = localStorage.getItem(KEY); } catch (e) {}
  function current() { return choice || (mq && mq.matches ? "dark" : "light"); }
  function apply() {
    root.setAttribute("data-theme", current());
    document.querySelectorAll("[data-settheme]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-settheme") === current()));
    });
  }
  window.Book.getTheme = current;
  window.Book.setTheme = function (t) {
    choice = t;
    try { localStorage.setItem(KEY, t); } catch (e) {}
    apply();
  };
  if (mq) { if (mq.addEventListener) mq.addEventListener("change", apply); else if (mq.addListener) mq.addListener(apply); }
  apply();
})();

/* Menu: a slim top bar with a menu button; navigation, language and theme live in a left drawer,
   so the reading view stays clean. The single-file edition adds a chapter list (window.BookNav)
   and search (window.openSearch). */
(function () {
  var B = window.Book;
  var MENU = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>';
  var CLOSE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>';
  var FIND = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/></svg>';
  function bi(en, hi) { return '<span class="l-en">' + en + '</span><span class="l-hi">' + hi + "</span>"; }

  var veil = document.createElement("div");
  veil.className = "drawer-veil";
  var dr = document.createElement("aside");
  dr.className = "drawer";
  dr.setAttribute("aria-label", "Menu");
  dr.setAttribute("aria-hidden", "true");
  document.body.appendChild(veil);
  document.body.appendChild(dr);

  function build() {
    var nav = window.BookNav ? window.BookNav() : null;
    var links = nav ? nav.links : [];
    if (!nav) {                                    // separate-page edition: reuse the top bar's own links
      var bar = document.querySelector(".topbar");
      (bar ? bar.querySelectorAll(".crumbs a") : []).forEach(function (a) { links.push({ href: a.getAttribute("href"), html: a.innerHTML }); });
    }
    var t = B.getTheme(), l = B.lang();
    var h = '<div class="drawer-head"><span>' + bi("Menu", "Menu") + '</span><button type="button" class="drawer-x" aria-label="Close menu">' + CLOSE + "</button></div>" +
      '<div class="drawer-body">';
    if (links.length || window.openSearch) {
      h += "<h3>" + bi("Go to", "Kahan jaana hai") + '</h3><nav class="drawer-links">' +
        links.map(function (k) { return '<a href="' + k.href + '">' + (k.html || bi(k.en, k.hi)) + "</a>"; }).join("") +
        (window.openSearch ? '<a href="#" data-opensearch>' + bi("Search topics", "Topic dhoondho") + "</a>" : "") + "</nav>";
    }
    // language and mode sit in a collapsed "Options" section, so the chapter list gets the room
    h += '<details class="drawer-opts"' + (optsOpen ? " open" : "") + '><summary><span class="opt-name">' + bi("Options", "Options") +
      '</span><span class="opt-now"></span></summary>' +
      '<div class="opt-label">' + bi("Language", "Bhasha") + '</div><div class="seg" role="group" aria-label="Language">' +
      '<button type="button" data-setlang="en" aria-pressed="' + (l === "en") + '">English</button>' +
      '<button type="button" data-setlang="hi" aria-pressed="' + (l === "hi") + '">Hinglish</button></div>' +
      '<div class="opt-label">' + bi("Mode", "Mode") + '</div><div class="seg" role="group" aria-label="Theme">' +
      '<button type="button" data-settheme="light" aria-pressed="' + (t === "light") + '">' + bi("Light", "Light") + "</button>" +
      '<button type="button" data-settheme="dark" aria-pressed="' + (t === "dark") + '">' + bi("Dark", "Dark") + "</button></div></details>";
    if (nav && nav.items && nav.items.length) {
      h += "<h3>" + nav.title + '</h3><nav class="drawer-links drawer-chapters">' + nav.items.map(function (it) {
        return '<a href="' + it.href + '"' + (it.current ? ' class="current" aria-current="page"' : "") + ">" + it.label + (it.done ? ' <span class="dn">✓</span>' : "") + "</a>";
      }).join("") + "</nav>";
    }
    dr.innerHTML = h + "</div>";
    var opts = dr.querySelector(".drawer-opts");
    opts.addEventListener("toggle", function () { optsOpen = opts.open; });
    showNow();
  }
  var optsOpen = false;                            // remembered while the page is open
  function showNow() {                             // "English · Dark" next to the Options heading
    var now = dr.querySelector(".opt-now");
    if (now) now.textContent = (B.lang() === "hi" ? "Hinglish" : "English") + " · " + (B.getTheme() === "dark" ? "Dark" : "Light");
  }

  function open() {
    build();
    dr.classList.add("open"); veil.classList.add("open");
    dr.setAttribute("aria-hidden", "false");
    var cur = dr.querySelector(".current"), list = dr.querySelector(".drawer-chapters");
    if (cur && list) list.scrollTop = cur.offsetTop - list.offsetTop - list.clientHeight / 2;   // centre this chapter in the list
    dr.querySelector(".drawer-x").focus();
  }
  function close() {
    dr.classList.remove("open"); veil.classList.remove("open");
    dr.setAttribute("aria-hidden", "true");
  }
  veil.addEventListener("click", close);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && dr.classList.contains("open")) close(); });
  dr.addEventListener("click", function (e) {
    var t = e.target.closest("button, a");
    if (!t) return;
    if (t.classList.contains("drawer-x")) return close();
    if (t.hasAttribute("data-setlang")) return setTimeout(showNow, 0);   // the page's own handler switches the language
    if (t.hasAttribute("data-settheme")) { B.setTheme(t.getAttribute("data-settheme")); return showNow(); }
    if (t.hasAttribute("data-opensearch")) { e.preventDefault(); close(); return window.openSearch(); }
    if (t.tagName === "A") close();                // navigating away
  });

  // Turn the page's top bar into the slim bar. Safe to call again (e.g. after the single-file router renders).
  B.decorate = function () {
    var bar = document.querySelector(".topbar");
    if (!bar) return;
    if (!bar.classList.contains("has-drawer")) {
      bar.classList.add("has-drawer");
      var m = document.createElement("button");
      m.type = "button"; m.className = "bar-btn menu-btn"; m.innerHTML = MENU;
      m.setAttribute("aria-label", "Open menu"); m.title = "Menu";
      m.addEventListener("click", open);
      bar.insertBefore(m, bar.firstChild);
    }
    if (window.openSearch && !bar.querySelector(".find-btn")) {
      var f = document.createElement("button");
      f.type = "button"; f.className = "bar-btn find-btn"; f.innerHTML = FIND;
      f.setAttribute("aria-label", "Search topics"); f.title = "Search topics";
      f.addEventListener("click", function () { window.openSearch(); });
      bar.appendChild(f);
    }
  };
  B.openMenu = open;
  B.decorate();
})();
