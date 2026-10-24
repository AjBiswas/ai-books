/* Reading progress and chapter quizzes for the single-file edition (inlined by package_single_html.py).
   Progress lives in this browser only (localStorage). A chapter counts as done when the reader
   reaches its end, or presses the button. Quizzes come from window.QUIZ (quiz.js), keyed by page id. */
(function () {
  var KEY = "ai-books-progress";
  var app = document.getElementById("app");
  var TOTAL = {};
  document.querySelectorAll("template[id^='t-b']").forEach(function (t) {
    var m = t.id.match(/^t-(b[12])-ch\d\d$/);
    if (m) TOTAL[m[1]] = (TOTAL[m[1]] || 0) + 1;
  });

  function load() { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } }
  function save(d) { try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (e) {} }
  function bi(en, hi) { return '<span class="l-en">' + en + '</span><span class="l-hi">' + hi + "</span>"; }
  function count(book, d) { return Object.keys(d).filter(function (k) { return k.indexOf(book + "-ch") === 0; }).length; }

  function setDone(id, on) {
    var d = load();
    if (on) d[id] = Date.now(); else delete d[id];
    save(d);
    var btn = app.querySelector(".donebar button");
    if (btn) paintButton(btn, on);
  }
  function paintButton(btn, on) {
    btn.className = on ? "is-done" : "";
    btn.innerHTML = on ? bi("✓ Chapter done · undo", "✓ Chapter poora · wapas lo") : bi("Mark this chapter as done", "Is chapter ko poora mark karo");
  }

  function quiz(id) {
    var qs = (window.QUIZ || {})[id];
    if (!qs || !qs.length) return null;
    var box = document.createElement("section");
    box.className = "quiz";
    box.innerHTML = '<h2>' + bi("Quick check", "Jhatpat jaanch") + '</h2><p class="quiz-sub">' +
      bi("Three questions. Tap an answer to see if you're right.", "Teen sawaal. Jawab par tap karke dekho sahi hai ya nahi.") + "</p>";
    qs.forEach(function (q, n) {
      // fixed per-question shuffle (same order every visit), so the right answer isn't always first
      var seed = 0, key = id + n;
      for (var c = 0; c < key.length; c++) seed = (seed * 31 + key.charCodeAt(c)) >>> 0;
      var order = q.o.map(function (_, k) { return k; });
      for (var i = order.length - 1; i > 0; i--) {
        seed = (seed * 1103515245 + 12345) >>> 0;
        var j = seed % (i + 1), t = order[i]; order[i] = order[j]; order[j] = t;
      }
      var div = document.createElement("div");
      div.className = "quiz-q";
      div.innerHTML = '<p class="quiz-stem"><b>' + (n + 1) + ".</b> " + bi(q.q[0], q.q[1]) + "</p>" +
        order.map(function (k) { return '<button type="button" data-k="' + k + '">' + bi(q.o[k][0], q.o[k][1]) + "</button>"; }).join("") +
        '<p class="quiz-why" hidden></p>';
      div.addEventListener("click", function (e) {
        var b = e.target.closest("button");
        if (!b || div.classList.contains("answered")) return;
        var k = +b.getAttribute("data-k"), right = k === q.a;
        div.classList.add("answered");
        b.classList.add(right ? "right" : "wrong");
        div.querySelector('button[data-k="' + q.a + '"]').classList.add("right");
        var why = div.querySelector(".quiz-why");
        why.innerHTML = (right ? bi("Correct. ", "Sahi. ") : bi("Not quite. ", "Bilkul nahi. ")) + bi(q.w[0], q.w[1]);
        why.hidden = false;
      });
      box.appendChild(div);
    });
    return box;
  }

  function chapterPage(id) {
    var article = app.querySelector("article");
    var pager = app.querySelector(".pager");
    if (!article || !pager) return;
    var qz = quiz(id);
    if (qz) pager.parentNode.insertBefore(qz, pager);
    var bar = document.createElement("div");
    bar.className = "donebar";
    bar.innerHTML = "<button type=\"button\"></button>";
    pager.parentNode.insertBefore(bar, pager);
    var btn = bar.querySelector("button");
    paintButton(btn, !!load()[id]);
    btn.addEventListener("click", function () { setDone(id, !load()[id]); });
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (es) {
        if (es.some(function (x) { return x.isIntersecting; })) { if (!load()[id]) setDone(id, true); io.disconnect(); }
      });
      io.observe(pager);
    }
  }

  function contentsPage(book) {
    var d = load(), done = count(book, d), total = TOTAL[book] || 0;
    app.querySelectorAll(".chapters li").forEach(function (li) {
      var a = li.querySelector("a.ct");
      var m = a && a.getAttribute("href").match(/^#(b[12]-ch\d\d)$/);
      if (m && d[m[1]]) li.classList.add("is-done");
    });
    var parts = app.querySelector(".parts");
    if (!parts) return;
    var p = document.createElement("div");
    p.className = "progress";
    p.innerHTML = '<div class="progress-text">' + bi("You've finished " + done + " of " + total + " chapters", total + " mein se " + done + " chapters poore") +
      ' <button type="button" class="progress-reset">' + bi("reset", "reset") + '</button></div><div class="progress-track"><div class="progress-fill" style="width:' +
      (total ? Math.round(done / total * 100) : 0) + '%"></div></div>';
    parts.parentNode.insertBefore(p, parts);
    p.querySelector(".progress-reset").addEventListener("click", function () {
      if (!confirm("Clear reading progress for this book?")) return;
      var dd = load();
      Object.keys(dd).forEach(function (k) { if (k.indexOf(book + "-ch") === 0) delete dd[k]; });
      save(dd);
      location.reload();
    });
  }

  function homePage() {
    var d = load();
    app.querySelectorAll(".chapters li").forEach(function (li) {
      var a = li.querySelector("a.ct");
      var m = a && a.getAttribute("href").match(/^#(b[12])-index$/);
      if (!m) return;
      var done = count(m[1], d);
      if (!done) return;
      var s = document.createElement("span");
      s.className = "home-progress";
      s.textContent = done + " / " + TOTAL[m[1]] + " done";
      a.appendChild(s);
    });
  }

  function onRoute() {
    var id = (location.hash || "#home").slice(1).split("~")[0];
    if (/^b[12]-ch\d\d$/.test(id)) chapterPage(id);
    else if (/^b[12]-index$/.test(id)) contentsPage(id.slice(0, 2));
    else if (id === "home" || !document.getElementById("t-" + id)) homePage();
  }
  // what the menu drawer shows: where to go, and this book's chapters with done marks
  var BOOKS = { b2: ["Becoming an AI Engineer", "AI Engineer Banna"], b1: ["Building the Harness", "Harness Banana"] };
  window.BookNav = function () {
    var id = (location.hash || "#home").slice(1).split("~")[0];
    var book = (id.match(/^(b[12])-/) || [])[1];
    var links = [{ href: "#home", en: "All books", hi: "Saari books" }];
    if (!book) return { links: links.concat([{ href: "#b2-index", en: "Book 1 · AI Engineer", hi: "Book 1 · AI Engineer" },
                                           { href: "#b1-index", en: "Book 2 · Harness", hi: "Book 2 · Harness" }]) };
    links.push({ href: "#" + book + "-index", en: "Contents", hi: "Vishay-suchi" });
    var d = load(), items = [];
    document.querySelectorAll("template[id^='t-" + book + "-ch']").forEach(function (t) {
      var pid = t.id.slice(2);
      items.push({ href: "#" + pid, label: t.getAttribute("data-title"), current: pid === id, done: !!d[pid] });
    });
    return { links: links, title: bi(BOOKS[book][0], BOOKS[book][1]), items: items };
  };

  window.addEventListener("hashchange", function () { setTimeout(onRoute, 0); });   // after the router has rendered
  onRoute();
})();
