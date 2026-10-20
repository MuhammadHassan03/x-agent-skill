/* x-agent-skill landing page. No dependencies, no network. */
(function () {
  "use strict";
  var root = document.documentElement;
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- theme toggle ---------- */
  var themeBtn = document.getElementById("theme-toggle");
  function syncThemeBtn() {
    var light = root.getAttribute("data-theme") === "light";
    themeBtn.setAttribute("aria-pressed", light ? "true" : "false");
    themeBtn.setAttribute("aria-label", light ? "Light theme on, switch to dark" : "Dark theme on, switch to light");
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) { meta.setAttribute("content", light ? "#f7f6f2" : "#0c0e12"); }
  }
  themeBtn.addEventListener("click", function () {
    var next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) {}
    syncThemeBtn();
  });
  syncThemeBtn();

  /* ---------- header shadow on scroll ---------- */
  var bar = document.getElementById("top-bar");
  function onScroll() { bar.classList.toggle("scrolled", window.scrollY > 8); }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- mobile menu ---------- */
  var menuBtn = document.getElementById("menu-toggle");
  var links = document.getElementById("nav-links");
  function setMenu(open) {
    links.classList.toggle("open", open);
    menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    menuBtn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  }
  menuBtn.addEventListener("click", function () { setMenu(menuBtn.getAttribute("aria-expanded") !== "true"); });
  links.addEventListener("click", function (e) { if (e.target.tagName === "A") { setMenu(false); } });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && menuBtn.getAttribute("aria-expanded") === "true") { setMenu(false); menuBtn.focus(); }
  });

  /* ---------- tabs: arrow keys, Home, End; roving tabindex ---------- */
  function tabs(listId, opts) {
    var list = document.getElementById(listId);
    if (!list) { return; }
    var btns = Array.prototype.slice.call(list.querySelectorAll('[role="tab"]'));
    var vertical = list.getAttribute("aria-orientation") === "vertical";
    function select(i, focus) {
      btns.forEach(function (b, j) {
        var on = i === j;
        b.setAttribute("aria-selected", on ? "true" : "false");
        b.tabIndex = on ? 0 : -1;
        var panel = document.getElementById(b.getAttribute("aria-controls"));
        if (panel) { panel.hidden = !on; }
      });
      if (focus) { btns[i].focus(); }
    }
    btns.forEach(function (b, i) { b.addEventListener("click", function () { select(i, false); }); });
    list.addEventListener("keydown", function (e) {
      var i = btns.indexOf(document.activeElement);
      if (i < 0) { return; }
      var next = -1;
      var fwd = vertical ? "ArrowDown" : "ArrowRight";
      var back = vertical ? "ArrowUp" : "ArrowLeft";
      if (e.key === fwd) { next = (i + 1) % btns.length; }
      else if (e.key === back) { next = (i - 1 + btns.length) % btns.length; }
      else if (e.key === "Home") { next = 0; }
      else if (e.key === "End") { next = btns.length - 1; }
      if (next >= 0) { e.preventDefault(); select(next, true); }
    });
    if (opts && opts.numberKeys) {
      document.addEventListener("keydown", function (e) {
        var t = e.target;
        if (e.ctrlKey || e.metaKey || e.altKey) { return; }
        if (t && (/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || t.isContentEditable)) { return; }
        var n = parseInt(e.key, 10);
        if (n >= 1 && n <= btns.length) { select(n - 1, false); }
      });
    }
  }
  tabs("hero-tabs", { numberKeys: true });
  tabs("tool-tabs");
  tabs("measure-tabs");
  tabs("install-tabs");

  /* ---------- skill filter ---------- */
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
  var items = Array.prototype.slice.call(document.querySelectorAll("#skill-grid > li"));
  var status = document.getElementById("filter-status");
  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      var f = c.getAttribute("data-filter");
      chips.forEach(function (o) { o.setAttribute("aria-pressed", o === c ? "true" : "false"); });
      var shown = 0;
      items.forEach(function (li) {
        var ok = f === "all" || li.getAttribute("data-cat") === f;
        li.hidden = !ok;
        if (ok) { shown += 1; li.classList.add("in"); }
      });
      status.textContent = "Showing " + shown + " of " + items.length + " skills";
    });
  });

  /* ---------- copy buttons ---------- */
  var copyStatus = document.getElementById("copy-status");
  Array.prototype.forEach.call(document.querySelectorAll(".copy"), function (btn) {
    btn.addEventListener("click", function () {
      var el = document.getElementById(btn.getAttribute("data-target"));
      var text = el ? el.textContent : "";
      function done(ok) {
        btn.textContent = ok ? "Copied" : "Press Ctrl+C";
        copyStatus.textContent = ok ? "Copied to clipboard" : "Copy failed, select the text and copy it";
        setTimeout(function () { btn.textContent = "Copy"; }, 1800);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
      } else {
        try {
          var ta = document.createElement("textarea");
          ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
          document.body.appendChild(ta); ta.select();
          var ok = document.execCommand("copy");
          document.body.removeChild(ta); done(ok);
        } catch (e) { done(false); }
      }
    });
  });

  /* ---------- dogfood meter: day count from the real dates ---------- */
  (function () {
    var start = Date.UTC(2026, 9, 21), end = Date.UTC(2026, 10, 19);
    var now = new Date(), today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
    var day = Math.floor((today - start) / 86400000) + 1;
    var line = document.getElementById("dog-line"), fill = document.getElementById("dog-fill");
    if (today < start) { line.textContent = "Day 1 of 30 starts on 2026-10-21."; fill.style.setProperty("--p", 0); }
    else if (today <= end) { line.textContent = "Day " + day + " of 30. Numbers land 2026-11-19."; fill.style.setProperty("--p", Math.round(day / 30 * 100)); }
    else { line.textContent = "The 30 days are over. The numbers are due in the README."; fill.style.setProperty("--p", 100); }
  })();

  /* ---------- reveal on scroll (skipped under reduced motion) ---------- */
  var reveals = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
  if (reduce || !("IntersectionObserver" in window)) {
    reveals.forEach(function (r) { r.classList.add("in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });
    reveals.forEach(function (r) { io.observe(r); });
  }

  /* ---------- nav current section ---------- */
  var navLinks = Array.prototype.slice.call(document.querySelectorAll(".nav-links a"));
  if ("IntersectionObserver" in window) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) { return; }
        navLinks.forEach(function (a) {
          if (a.getAttribute("href") === "#" + en.target.id) { a.setAttribute("aria-current", "true"); }
          else { a.removeAttribute("aria-current"); }
        });
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    ["skills", "tools", "measured", "fine-print", "install"].forEach(function (id) {
      var s = document.getElementById(id); if (s) { spy.observe(s); }
    });
  }
})();
