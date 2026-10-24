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

  /* ---------- Book 2: ready-made animated scenes ----------
     Each takes the id of an empty <figure class="scene"> and builds the stage itself.
     caps: [[en, hi], ...] one per step. Items carry `step`: shown once the scene reaches it. */
  function wrapText(t, n) {
    var words = String(t).split(" "), lines = [], line = "";
    words.forEach(function (w) {
      if ((line + " " + w).trim().length > n && line) { lines.push(line.trim()); line = w; } else line += " " + w;
    });
    if (line.trim()) lines.push(line.trim());
    return lines;
  }
  function stage(figId, label) {
    var fig = document.getElementById(figId);
    var st = document.createElement("div"); st.className = "stage";
    var svg = document.createElementNS(NS, "svg");
    svg.id = figId + "-svg"; svg.setAttribute("width", 760); svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", label || "");
    st.appendChild(svg); fig.insertBefore(st, fig.firstChild);
    return { fig: fig, svg: svg, height: function (h) { svg.setAttribute("viewBox", "0 0 760 " + Math.ceil(h)); } };
  }
  // multi-line bilingual text; returns the number of lines used (max of both languages)
  function mtext(p, x, y, en, hi, n, attrs, lh) {
    lh = lh || 17;
    var a = wrapText(en, n), b = wrapText(hi == null ? en : hi, n);
    [[a, "l-en"], [b, "l-hi"]].forEach(function (pair) {
      var t = E(p, "text", Object.assign({ x: x, y: y }, attrs || {}));
      t.setAttribute("class", ((attrs && attrs["class"]) ? attrs["class"] + " " : "") + pair[1]);
      pair[0].forEach(function (ln, i) { E(t, "tspan", { x: x, dy: i ? lh : 0 }, ln); });
    });
    return Math.max(a.length, b.length);
  }

  var WHO = {
    user: { en: "You", hi: "Aap", c: "box-sig", right: true },
    ai: { en: "Haron", hi: "Haron", c: "box", right: false },
    bad: { en: "Haron", hi: "Haron", c: "box-amb", right: false },
    good: { en: "Haron", hi: "Haron", c: "box-sig", right: false },
    sys: { en: "System prompt", hi: "System prompt", c: "box-plm", wide: true },
    tool: { en: "Tool", hi: "Tool", c: "box-amb", wide: true, mono: true },
    note: { en: "", hi: "", c: "box", wide: true }
  };
  // chat(figId, msgs[{who,en,hi,step}], caps, opts)
  function chat(figId, msgs, caps, opts) {
    opts = opts || {};
    var S = stage(figId, opts.label || "conversation"), s = S.svg, y = 14, items = [];
    msgs.forEach(function (m, k) {
      var w = WHO[m.who] || WHO.note, g = E(s, "g", { "class": "anim" });
      var n = w.wide ? 92 : 62, fs = w.mono ? 11.5 : 13;
      var lines = Math.max(wrapText(m.en, n).length, wrapText(m.hi == null ? m.en : m.hi, n).length);
      var longest = Math.max.apply(null, wrapText(m.en, n).concat(wrapText(m.hi == null ? m.en : m.hi, n)).map(function (l) { return l.length; }));
      var bw = w.wide ? 700 : Math.min(560, Math.max(140, longest * (fs * 0.56) + 30));
      var bh = lines * 18 + 20;
      var x = w.wide ? 40 : (w.right ? 750 - bw : 58);
      if (!w.wide && !w.right) tokku(g, 8, y, 40);
      E(g, "rect", { x: x, y: y, width: bw, height: bh, rx: w.wide ? 6 : 14, "class": m.cls || w.c });
      if (w.en) BI(g, { x: x + 12, y: y - 3, "font-size": 10, "class": "mono muted" }, m.label || w.en, m.label || w.hi);
      mtext(g, x + 14, y + 22, m.en, m.hi, n, { "font-size": fs, "class": w.mono ? "mono" : "" }, 18);
      items.push({ g: g, step: m.step == null ? k : m.step });
      y += bh + 18;
    });
    S.height(y);
    return scene(S.fig, caps, function (i) { items.forEach(function (it) { show(it.g, it.step <= i); }); }, opts);
  }

  // flow(figId, nodes[{en,hi,sen,shi}], caps, opts{perRow, all})
  function flow(figId, nodes, caps, opts) {
    opts = opts || {};
    var S = stage(figId, opts.label || "flow"), s = S.svg;
    var per = opts.perRow || Math.min(nodes.length, 4), gap = 34;
    var w = (740 - (per - 1) * gap) / per, h = opts.h || 74, gs = [];
    nodes.forEach(function (nd, k) {
      var r = Math.floor(k / per), c = k % per, x = 10 + c * (w + gap), y = 14 + r * (h + 40);
      var g = E(s, "g", { "class": "anim" });
      E(g, "rect", { x: x, y: y, width: w, height: h, rx: 6, "class": "box" });
      BI(g, { x: x + w / 2, y: y + 24, "text-anchor": "middle", "font-weight": 600, "font-size": 13 }, nd.en, nd.hi);
      if (nd.sen) mtext(g, x + w / 2, y + 43, nd.sen, nd.shi, Math.floor(w / 6.2), { "text-anchor": "middle", "font-size": 11, "class": "muted" }, 14);
      if (k < nodes.length - 1) {
        if (c < per - 1) arrow(s, g, x + w + 2, y + h / 2, x + w + gap - 2, y + h / 2, "");
        else arrow(s, g, x + w / 2, y + h + 2, 10 + w / 2, y + h + 38, "", 0);
      }
      gs.push(g);
    });
    S.height(14 + Math.ceil(nodes.length / per) * (h + 40));
    return scene(S.fig, caps, function (i) {
      gs.forEach(function (g, k) {
        show(g, opts.all || k <= i);
        cls(g.firstChild, k === i ? "box-amb" : (k < i ? "box-sig" : "box"));
      });
    }, opts);
  }

  // bars(figId, rows[{en,hi,v,txt,cls,step}], caps, opts{max})
  function bars(figId, rows, caps, opts) {
    opts = opts || {};
    var S = stage(figId, opts.label || "comparison"), s = S.svg, items = [];
    var max = opts.max || Math.max.apply(null, rows.map(function (r) { return r.v; }));
    // the bar track shrinks so the longest value label still fits inside the 760-wide stage
    var longest = Math.max.apply(null, rows.map(function (r) { return String(r.txt == null ? r.v : r.txt).length; }));
    var track = Math.max(160, Math.min(420, 740 - 250 - 10 - longest * 7));
    rows.forEach(function (r, k) {
      var y = 14 + k * 44, g = E(s, "g", { "class": "anim" });
      mtext(g, 10, y + 20, r.en, r.hi, 30, { "font-size": 12.5, "font-weight": 600 }, 14);
      E(g, "rect", { x: 250, y: y, width: track, height: 30, rx: 3, "class": "box" });
      var b = E(g, "rect", { x: 250, y: y, width: 0, height: 30, rx: 3, "class": r.cls || "box-sig" });
      b.style.transition = "width .9s cubic-bezier(.2,.8,.2,1)";
      E(g, "text", { x: 250 + track + 8, y: y + 20, "font-size": 11.5, "font-weight": 700, "class": "mono" }, r.txt == null ? String(r.v) : r.txt);
      items.push({ g: g, b: b, w: Math.max(3, r.v / max * track), step: r.step == null ? k : r.step });
    });
    S.height(14 + rows.length * 44);
    return scene(S.fig, caps, function (i) {
      items.forEach(function (it) { var on = it.step <= i; show(it.g, on); it.b.setAttribute("width", on ? it.w : 0); });
    }, opts);
  }

  // stack(figId, layers[{en,hi,sen,shi,cls,step}], caps) - top to bottom
  function stack(figId, layers, caps, opts) {
    opts = opts || {};
    var S = stage(figId, opts.label || "layers"), s = S.svg, items = [];
    layers.forEach(function (L, k) {
      var g = box(s, { x: 60, y: 14 + k * 58, w: 640, h: 48, cls: L.cls || "box", fs: 13, en: L.en, hi: L.hi, sen: L.sen, shi: L.shi });
      items.push({ g: g, step: L.step == null ? k : L.step });
    });
    S.height(14 + layers.length * 58);
    return scene(S.fig, caps, function (i) { items.forEach(function (it) { show(it.g, it.step <= i); }); }, opts);
  }

  // columns(figId, cols[{en,hi,cls,items[{en,hi,cls,step}]}], caps) - side-by-side lists
  function columns(figId, cols, caps, opts) {
    opts = opts || {};
    var S = stage(figId, opts.label || "comparison"), s = S.svg, items = [], maxY = 0;
    var cw = (740 - (cols.length - 1) * 20) / cols.length, n = Math.floor(cw / 7.4);
    // rows line up across columns: each row is as tall as its tallest cell
    var rowH = [];
    cols.forEach(function (c) {
      c.items.forEach(function (it, r) {
        var lines = Math.max(wrapText(it.en, n).length, wrapText(it.hi == null ? it.en : it.hi, n).length);
        rowH[r] = Math.max(rowH[r] || 0, lines * 17 + 16);
      });
    });
    cols.forEach(function (c, ci) {
      var x = 10 + ci * (cw + 20), y = 14;
      var head = box(s, { x: x, y: y, w: cw, h: 40, cls: c.cls || "box-plm", fs: 14, en: c.en, hi: c.hi });
      items.push({ g: head, step: c.step == null ? 0 : c.step });
      y += 52;
      c.items.forEach(function (it, r) {
        var g = E(s, "g", { "class": "anim" });
        var h = rowH[r];
        E(g, "rect", { x: x, y: y, width: cw, height: h, rx: 6, "class": it.cls || "box" });
        mtext(g, x + 12, y + 20, it.en, it.hi, n, { "font-size": 12.5 }, 17);
        items.push({ g: g, step: it.step == null ? 0 : it.step });
        y += h + 10;
      });
      maxY = Math.max(maxY, y);
    });
    S.height(maxY + 4);
    return scene(S.fig, caps, function (i) { items.forEach(function (it) { show(it.g, it.step <= i); }); }, opts);
  }

  window.Book = { E: E, BI: BI, show: show, move: move, scene: scene, reduced: reduced,
    tokku: tokku, box: box, arrow: arrow, cls: cls, onLang: onLang,
    chat: chat, flow: flow, bars: bars, stack: stack, columns: columns, stage: stage, mtext: mtext, wrapText: wrapText,
    lang: function () { return root.getAttribute("data-lang") || "en"; } };
})();

/* Light/dark switch: a round button at the bottom right. Follows the system until the reader
   picks a theme; the choice is saved per browser. */
(function () {
  var KEY = "harness-book-theme", root = document.documentElement;
  var mq = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
  var choice = null;
  try { choice = localStorage.getItem(KEY); } catch (e) {}
  var SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="12" r="4.5"/>' +
    '<path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>';
  var MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>';
  var btn = document.createElement("button");
  btn.className = "tbtn"; btn.type = "button";
  function current() { return choice || (mq && mq.matches ? "dark" : "light"); }
  function apply() {
    var t = current();
    root.setAttribute("data-theme", t);
    btn.innerHTML = t === "dark" ? SUN : MOON;
    btn.setAttribute("aria-label", t === "dark" ? "Switch to light mode" : "Switch to dark mode");
    btn.title = btn.getAttribute("aria-label");
  }
  btn.addEventListener("click", function () {
    choice = current() === "dark" ? "light" : "dark";
    try { localStorage.setItem(KEY, choice); } catch (e) {}
    apply();
  });
  if (mq) { if (mq.addEventListener) mq.addEventListener("change", apply); else if (mq.addListener) mq.addListener(apply); }
  apply();
  document.body.appendChild(btn);
})();
