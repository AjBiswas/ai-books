/* Topic search for the single-file edition (inlined by package_single_html.py).
   The index is built once, on first open, from the chapter <template>s: one entry per chapter
   and one per section (h2), in both languages. A result links to #page~n (the nth h2). */
(function () {
  var BOOK = { b2: "Book 1 · AI Engineer", b1: "Book 2 · Harness" };
  var index = null;
  // Filler words (English and Hinglish) that would otherwise have to match too.
  var STOP = {};
  ("a an the in on of to for and or is are what how why with about from by kya kaise kyun hai hain ka ki ke ko me mein se " +
   "aur karke karna karte topic topics").split(" ").forEach(function (w) { STOP[w] = 1; });

  var over = document.createElement("div");
  over.className = "sover"; over.setAttribute("role", "dialog"); over.setAttribute("aria-modal", "true");
  over.innerHTML = '<div class="sbox"><div class="shead"><input type="search" autocomplete="off" aria-label="Search topics">' +
    '<button type="button">Close</button></div><div class="slist"></div></div>';
  document.body.appendChild(over);
  var q = over.querySelector("input"), list = over.querySelector(".slist");

  function lang() { return window.Book ? window.Book.lang() : "en"; }
  function txt(el, l) {
    var c = el.cloneNode(true);
    c.querySelectorAll(l === "en" ? ".l-hi" : ".l-en").forEach(function (x) { x.remove(); });
    return c.textContent.replace(/\s+/g, " ").trim();
  }

  function build() {
    index = [];
    document.querySelectorAll("template[id^='t-b']").forEach(function (t) {
      var id = t.id.slice(2);
      if (/-index$/.test(id)) return;
      var root = document.createElement("div");
      root.appendChild(t.content.cloneNode(true));
      var h1 = root.querySelector("h1");
      var base = { id: id, book: BOOK[id.slice(0, 2)], chap: t.getAttribute("data-title").split(" · ")[0] };
      function entry(n, el) {
        var e = { id: base.id, book: base.book, chap: base.chap, n: n,
          head: { en: el ? txt(el, "en") : "", hi: el ? txt(el, "hi") : "" }, body: { en: "", hi: "" } };
        index.push(e);
        return e;
      }
      var cur = entry(0, h1), n = 0;
      root.querySelectorAll("h2, h3, h4, p, li, td, th, figcaption, summary, .gloss > div").forEach(function (el) {
        if (el.closest("svg, .topbar")) return;
        if (el.tagName === "H2") { n += 1; cur = entry(n, el); return; }
        var outer = el.parentElement && el.parentElement.closest("li, td, th, p");
        if (outer) return;   // its text is already counted by the enclosing element
        if (!el.closest(".l-hi")) cur.body.en += " " + txt(el, "en");
        if (!el.closest(".l-en")) cur.body.hi += " " + txt(el, "hi");
      });
    });
  }

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }
  function mark(s, words) {
    var out = esc(s);
    words.forEach(function (w) {
      var re = new RegExp("(" + esc(w).replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  }
  function snippet(body, words) {
    var low = body.toLowerCase(), at = -1;
    words.some(function (w) { at = low.indexOf(w); return at >= 0; });
    if (at < 0) return body.slice(0, 140) + (body.length > 140 ? "..." : "");
    var a = Math.max(0, at - 50), b = Math.min(body.length, at + 110);
    return (a ? "..." : "") + body.slice(a, b) + (b < body.length ? "..." : "");
  }

  function search() {
    if (!index) build();
    var l = lang();
    q.placeholder = l === "hi" ? "Topic dhoondhiye: RAG, MCP, tokens..." : "Search topics: RAG, MCP, tokens...";
    over.querySelector(".shead button").textContent = l === "hi" ? "Band" : "Close";
    var typed = q.value.toLowerCase().split(/[\s-]+/).filter(Boolean);   // "harness-as-code" = "harness as code"
    var words = typed.filter(function (w) { return !STOP[w]; });
    if (!words.length) words = typed;
    var phrase = typed.join(" ");
    if (!words.length) {
      list.innerHTML = '<div class="sempty">' + (l === "hi" ? "Koi topic likhiye, jaise RAG, MCP, LoRA, agents." : "Type a topic, like RAG, MCP, LoRA, agents.") + "</div>";
      return;
    }
    // Every word must match; if nothing does, fall back to sections matching most of the words.
    var hits = [], near = [], need = Math.max(1, Math.ceil(words.length / 2));
    index.forEach(function (e) {
      var head = (e.head.en + " " + e.head.hi).toLowerCase().replace(/-/g, " ");
      var all = head + " " + (e.body.en + " " + e.body.hi).toLowerCase().replace(/-/g, " ");
      var found = words.filter(function (w) { return all.indexOf(w) >= 0; }).length;
      if (found < need) return;
      var score = (e.n === 0 ? 2 : 0) + found * 20;
      if (typed.length > 1 && head.indexOf(phrase) >= 0) score += 60;
      else if (typed.length > 1 && all.indexOf(phrase) >= 0) score += 30;
      words.forEach(function (w) { if (head.indexOf(w) >= 0) score += 10; score += Math.min(5, all.split(w).length - 1); });
      (found === words.length ? hits : near).push({ e: e, score: score });
    });
    var closest = !hits.length && near.length;
    if (closest) hits = near;
    hits.sort(function (a, b) { return b.score - a.score; });
    if (!hits.length) {
      list.innerHTML = '<div class="sempty">' + (l === "hi" ? "Kuchh nahi mila. Doosra shabd try kijiye." : "Nothing found. Try another word.") + "</div>";
      return;
    }
    list.innerHTML = (closest ? '<div class="sempty">' + (l === "hi" ? "Poora match nahi mila. Sabse kareeb:" : "No exact match. Closest topics:") + "</div>" : "") +
      hits.slice(0, 40).map(function (h) {
      var e = h.e, head = e.head[l] || e.head.en, body = (e.body[l] || e.body.en).trim();
      return '<a href="#' + e.id + (e.n ? "~" + e.n : "") + '"><span class="sk">' + esc(e.book + " · " + e.chap) + "</span>" +
        '<span class="sh">' + mark(head, words) + '</span><span class="ss">' + mark(snippet(body, words), words) + "</span></a>";
    }).join("");
  }

  function open() { over.classList.add("open"); document.body.style.overflow = "hidden"; search(); q.focus(); }
  function close() { over.classList.remove("open"); document.body.style.overflow = ""; }
  over.querySelector(".shead button").addEventListener("click", close);
  over.addEventListener("click", function (e) { if (e.target === over) close(); });
  list.addEventListener("click", function (e) {
    var a = e.target.closest("a");
    if (!a) return;
    close();
    if (a.getAttribute("href") === location.hash) { e.preventDefault(); window.dispatchEvent(new HashChangeEvent("hashchange")); }
  });
  q.addEventListener("input", search);
  q.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { var a = list.querySelector("a"); if (a) a.click(); }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && over.classList.contains("open")) close();
    else if ((e.key === "k" && (e.ctrlKey || e.metaKey)) ||
             (e.key === "/" && !/INPUT|TEXTAREA/.test(document.activeElement.tagName))) { e.preventDefault(); open(); }
  });
  window.openSearch = open;                      // opened from the top bar's search icon and the menu
  if (window.Book && window.Book.decorate) window.Book.decorate();
})();
