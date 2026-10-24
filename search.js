/* Topic search for the single-file edition (inlined by package_single_html.py).
   The index is built once, on first open, from the chapter <template>s: one entry per chapter
   and one per section (h2), in both languages. A result links to #page~n (the nth h2). */
(function () {
  var BOOK = { b2: "Book 1 · AI Engineer", b1: "Book 2 · Harness" };
  var index = null;

  var btn = document.createElement("button");
  btn.className = "sbtn"; btn.type = "button"; btn.setAttribute("aria-label", "Search topics"); btn.title = "Search topics";
  btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">' +
    '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/></svg>';
  var over = document.createElement("div");
  over.className = "sover"; over.setAttribute("role", "dialog"); over.setAttribute("aria-modal", "true");
  over.innerHTML = '<div class="sbox"><div class="shead"><input type="search" autocomplete="off" aria-label="Search topics">' +
    '<button type="button">Close</button></div><div class="slist"></div></div>';
  document.body.appendChild(btn);
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
      root.querySelectorAll("h2, h3, p, li, td, th, figcaption, summary").forEach(function (el) {
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
    var words = q.value.toLowerCase().split(/\s+/).filter(Boolean);
    if (!words.length) {
      list.innerHTML = '<div class="sempty">' + (l === "hi" ? "Koi topic likhiye, jaise RAG, MCP, LoRA, agents." : "Type a topic, like RAG, MCP, LoRA, agents.") + "</div>";
      return;
    }
    var hits = [];
    index.forEach(function (e) {
      var head = (e.head.en + " " + e.head.hi).toLowerCase();
      var all = head + " " + (e.body.en + " " + e.body.hi).toLowerCase();
      if (!words.every(function (w) { return all.indexOf(w) >= 0; })) return;
      var score = e.n === 0 ? 2 : 0;
      words.forEach(function (w) { if (head.indexOf(w) >= 0) score += 10; score += Math.min(5, all.split(w).length - 1); });
      hits.push({ e: e, score: score });
    });
    hits.sort(function (a, b) { return b.score - a.score; });
    if (!hits.length) {
      list.innerHTML = '<div class="sempty">' + (l === "hi" ? "Kuchh nahi mila. Doosra shabd try kijiye." : "Nothing found. Try another word.") + "</div>";
      return;
    }
    list.innerHTML = hits.slice(0, 40).map(function (h) {
      var e = h.e, head = e.head[l] || e.head.en, body = (e.body[l] || e.body.en).trim();
      return '<a href="#' + e.id + (e.n ? "~" + e.n : "") + '"><span class="sk">' + esc(e.book + " · " + e.chap) + "</span>" +
        '<span class="sh">' + mark(head, words) + '</span><span class="ss">' + mark(snippet(body, words), words) + "</span></a>";
    }).join("");
  }

  function open() { over.classList.add("open"); document.body.style.overflow = "hidden"; search(); q.focus(); }
  function close() { over.classList.remove("open"); document.body.style.overflow = ""; }
  btn.addEventListener("click", open);
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
})();
