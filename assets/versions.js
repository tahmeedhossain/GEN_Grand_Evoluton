/* Version switch for GEN-Grand.
   Each page sets <html data-gen-version="two-tier|tierless-evolution|tierless-merged">; this script adds a
   small "Version" button (bottom left) with links to the main network, the tierless version and the texts. */
(function () {
  "use strict";
  var VERSIONS = [
    { id: "two-tier", name: "Two-tier network", tag: "main", path: "gen_two_tier_explorer.html",
      summary: "The six graphs on two tiers: system-specific nodes below, generic clusters above, cluster and descend edges between them. Year slider, zoomable map, the statement behind every line (Part III, 20 Nov 2026)." },
    { id: "tierless-evolution", name: "Tierless: evolution", tag: "Part II", path: "gen_evolution_explorer.html",
      summary: "The four dated graphs on one level with a year slider: growth, rule firings and method phases (14 Nov 2026)." },
    { id: "tierless-merged", name: "Tierless: merged network", tag: "Part I", path: "gen_grand_explorer.html",
      summary: "The six graphs merged into one state / model / observable concept graph with glue concepts and cross-edges (13 Nov 2026)." }
  ];
  var LINKS = [
    { name: "Notes on the two-tier network (TWO_TIER.md)", href: "https://github.com/tahmeedhossain/GEN_Grand_Evoluton/blob/main/TWO_TIER.md" },
    { name: "Thesis, Parts I and II (PDF)", path: "GEN_grand_thesis.pdf" },
    { name: "Source, data and README on GitHub", href: "https://github.com/tahmeedhossain/GEN_Grand_Evoluton" }
  ];
  window.GEN_VERSIONS = VERSIONS;
  var script = document.currentScript;
  var BASE = script ? script.src.replace(/assets\/versions\.js(\?.*)?$/, "") : "";
  var cur = document.documentElement.getAttribute("data-gen-version") || "";

  var css = ".genv{position:fixed;left:10px;bottom:10px;z-index:30;font-size:13px;line-height:1.3}" +
    ".genv>button{display:inline-flex;gap:6px;align-items:center;border:1px solid var(--line,#ccc);background:var(--panel,var(--rail,#fff));color:var(--ink,#111);padding:5px 11px;border-radius:999px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.14);font:inherit}" +
    ".genv>button b{font-weight:600}" +
    ".genv>button:focus-visible,.genv a:focus-visible{outline:2px solid var(--ink,#111);outline-offset:2px}" +
    ".genv .m{display:none;position:absolute;left:0;bottom:calc(100% + 6px);width:min(360px,calc(100vw - 20px));max-height:calc(100vh - 70px);overflow:auto;background:var(--panel,var(--rail,#fff));color:var(--ink,#111);border:1px solid var(--line,#ccc);border-radius:10px;box-shadow:0 8px 28px rgba(0,0,0,.2);padding:6px}" +
    ".genv.open .m{display:block}" +
    ".genv a{display:block;color:inherit;text-decoration:none;padding:7px 9px;border-radius:7px}" +
    ".genv a:hover{background:rgba(127,127,127,.12)}" +
    ".genv a.cur{background:rgba(127,127,127,.2)}" +
    ".genv a span{display:block;color:var(--ink2,var(--mute,#555));font-size:12px;margin-top:2px}" +
    ".genv .sep{border-top:1px solid var(--line,#ccc);margin:4px 0;padding-top:2px}" +
    ".genv .lk{padding:5px 9px;font-size:12px}";
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;"); }
  var c = VERSIONS.filter(function (v) { return v.id === cur; })[0];
  var box = document.createElement("div"); box.className = "genv";
  box.innerHTML = '<button type="button" aria-haspopup="true" aria-expanded="false">Version <b>' + esc(c ? c.name : "") + '</b> ▾</button>' +
    '<div class="m" role="menu">' + VERSIONS.map(function (v) {
      return '<a role="menuitem" href="' + esc(BASE + v.path) + '"' + (v.id === cur ? ' class="cur" aria-current="page"' : "") + '><b>' + esc(v.name) + " (" + esc(v.tag) + ")</b><span>" + esc(v.summary) + "</span></a>";
    }).join("") + '<div class="sep"></div>' + LINKS.map(function (l) {
      return '<a class="lk" role="menuitem" href="' + esc(l.href || BASE + l.path) + '">' + esc(l.name) + "</a>";
    }).join("") + "</div>";
  var btn = box.querySelector("button");
  function close() { box.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); }
  btn.addEventListener("click", function (e) { e.stopPropagation(); var o = box.classList.toggle("open"); btn.setAttribute("aria-expanded", o ? "true" : "false"); });
  document.addEventListener("click", function (e) { if (!box.contains(e.target)) close(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && box.classList.contains("open")) { close(); btn.focus(); } });
  function mount() { document.body.appendChild(box); }
  if (document.body) mount(); else document.addEventListener("DOMContentLoaded", mount);
})();
