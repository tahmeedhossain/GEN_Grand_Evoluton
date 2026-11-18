"""Build the evolutionary explorer page (year slider over the four-branch network) from data/gen_evolution_network.json and out/evolution.json.

Writes gen_evolution_explorer.html (standalone) and out/artifact_evolution.html (body for the Artifact tool)."""
from __future__ import annotations
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HEAD = r"""<title>Evolutionary Epistemic Network</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root{--s:#2a6f97;--m:#c05c2a;--o:#3f7d4e;--em:#6a3d9a;--hep:#b15928;--gpt:#d62728;--qrt:#1f78b4;--bg:#fafaf8;--ink:#1e1e1e;--line:#d8d8d2;--rail:#ffffff;--chip:#ffffff;--mute:#666666;--btn:#f4f4f0;--btnon:#1e1e1e;--btnon-fg:#ffffff;--th:#f1f1ec;--link:#2a6f97;--sel:#e0a800;--future:#cfcfca;--now:#c0392b;--glue:#9a9a94;--lane:#f1f1ec}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--s:#5a9bc4;--m:#d98557;--o:#6fae7e;--em:#a98ad0;--hep:#d99a6a;--gpt:#f07070;--qrt:#6fa8dc;--bg:#15171a;--ink:#e6e6e2;--line:#3a3d42;--rail:#1d2024;--chip:#1d2024;--mute:#9a9a94;--btn:#24272c;--btnon:#e6e6e2;--btnon-fg:#15171a;--th:#24272c;--link:#7fb3d5;--sel:#f0c040;--future:#3a3d42;--now:#ff6b5b;--glue:#6f6f69;--lane:#1a1d21;color-scheme:dark}}
:root[data-theme="dark"]{--s:#5a9bc4;--m:#d98557;--o:#6fae7e;--em:#a98ad0;--hep:#d99a6a;--gpt:#f07070;--qrt:#6fa8dc;--bg:#15171a;--ink:#e6e6e2;--line:#3a3d42;--rail:#1d2024;--chip:#1d2024;--mute:#9a9a94;--btn:#24272c;--btnon:#e6e6e2;--btnon-fg:#15171a;--th:#24272c;--link:#7fb3d5;--sel:#f0c040;--future:#3a3d42;--now:#ff6b5b;--glue:#6f6f69;--lane:#1a1d21;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 "DejaVu Sans",system-ui,sans-serif;color:var(--ink);background:var(--bg)}
header{padding-block:10px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));border-bottom:1px solid var(--line);background:var(--rail);display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 12px}
header h1{font-size:17px;margin:0}header .sub{color:var(--mute);font-size:12px}
nav{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding-block:8px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));border-bottom:1px solid var(--line);background:var(--rail)}
nav button,.ctl button{border:1px solid var(--line);background:var(--btn);color:var(--ink);border-radius:6px;padding:5px 10px;cursor:pointer;font-size:13px}
nav button.on,.ctl button.on{background:var(--btnon);color:var(--btnon-fg);border-color:var(--btnon)}
nav button:focus-visible,.ctl button:focus-visible,.chip:focus-visible{outline:2px solid var(--link);outline-offset:1px}
.ctl{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding-block:8px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));border-bottom:1px solid var(--line);background:var(--rail)}
.ctl input[type=range]{flex:1 1 240px;min-width:160px;accent-color:var(--now)}
.ctl .year{font-size:22px;font-weight:bold;font-variant-numeric:tabular-nums;min-width:64px}
.ctl .cnt{font-size:12px;color:var(--mute);min-width:0;overflow-wrap:anywhere}
.ctl .b{display:inline-block;border-radius:10px;padding:1px 7px;font-size:11px;color:#fff;margin-right:2px}
.b.EM{background:var(--em)}.b.HEP{background:var(--hep)}.b.GPT{background:var(--gpt)}.b.QRT{background:var(--qrt)}
main{display:grid;grid-template-columns:minmax(0,1fr) 380px;gap:0;min-height:calc(100vh - 150px);padding-left:max(0px,env(safe-area-inset-left,0px));padding-right:max(0px,env(safe-area-inset-right,0px))}
#stage{min-width:0;overflow:auto;max-height:calc(100vh - 150px);padding:8px 8px 8px max(8px,env(safe-area-inset-left,0px))}
#rail{background:var(--rail);border-left:1px solid var(--line);padding:10px 12px;overflow:auto;max-height:calc(100vh - 150px);font-size:13px;min-width:0}
#rail h3{margin:4px 0 2px;font-size:15px}#rail .k,.view .k{color:var(--mute);font-size:11px;text-transform:uppercase;letter-spacing:.04em;margin-top:10px}
#rail .r,.view .r{border-left:3px solid var(--line);padding:3px 8px;margin:4px 0;font-size:12px;overflow-wrap:anywhere}
#rail .r b,.view .r b{font-family:"DejaVu Sans Mono",monospace;font-size:11px}
a[data-uid],a[data-year]{color:var(--link);cursor:pointer;text-decoration:underline dotted}
.pill{display:inline-block;border-radius:10px;padding:1px 7px;font-size:11px;color:#fff;margin-right:4px}.pill.S{background:var(--s)}.pill.M{background:var(--m)}.pill.O{background:var(--o)}
.tag{display:inline-block;border:1px solid var(--line);border-radius:4px;padding:0 5px;font-size:11px;color:var(--mute);margin-right:3px}
table{border-collapse:collapse;font-size:12px}td,th{border:1px solid var(--line);padding:3px 6px;text-align:left;vertical-align:top}th{background:var(--th)}td.v,th.v{text-align:right;font-variant-numeric:tabular-nums}
.tw{overflow-x:auto;max-width:100%}
.view{padding-block:12px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));overflow:auto;max-height:calc(100vh - 150px);grid-column:1/3;min-width:0}
.view p,.view li{max-width:72ch}
.cols{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}
.col{border:1px solid var(--line);border-radius:6px;padding:6px;min-width:0;background:var(--rail)}
.col h2{font-size:13px;margin:2px 0 6px;color:#fff;padding:3px 8px;border-radius:6px}
.col.EM h2{background:var(--em)}.col.HEP h2{background:var(--hep)}.col.GPT h2{background:var(--gpt)}.col.QRT h2{background:var(--qrt)}
.sub{font-size:11px;color:var(--mute);margin:8px 0 3px;text-transform:uppercase;letter-spacing:.04em}
.chip{display:block;width:100%;text-align:left;border:1px solid var(--line);background:var(--chip);color:var(--ink);border-radius:6px;padding:3px 7px;margin:3px 0;cursor:pointer;font-size:12px}
.chip:hover{border-color:var(--mute)}.chip.sel{outline:2px solid var(--sel)}.chip .t{color:var(--mute);font-size:11px;margin-left:4px}.chip.new{border-left:4px solid var(--now)}.chip.rm{opacity:.55;text-decoration:line-through}
.chip.S{border-left-color:var(--s)}.chip.M{border-left-color:var(--m)}.chip.O{border-left-color:var(--o)}
svg text{font-family:"DejaVu Sans",system-ui,sans-serif}
.legend{font-size:12px;color:var(--mute);margin:6px 0}
.sw{display:inline-block;width:10px;height:10px;border-radius:5px;vertical-align:middle;margin:0 3px 0 8px}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
@media (max-width:900px){main{grid-template-columns:1fr}#stage,#rail{max-height:none}#rail{border-left:none;border-top:1px solid var(--line)}.view{grid-column:1/2;max-height:none}.cols{grid-template-columns:1fr 1fr}}
@media (max-width:560px){.cols{grid-template-columns:1fr}}
</style>"""

BODY = r"""<header><h1>Evolutionary Epistemic Network</h1><span class="sub" id="counts"></span></header>
<nav id="nav"></nav>
<div class="ctl" id="ctl"></div>
<main id="main"></main>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const FOUR = ['EM','HEP','GPT','QRT'];
const BT = {EM:'EM history reader (type D)', HEP:'Standard Model history (type H), union of the 12 steps', GPT:'Nonclassicality / effect network (type E)', QRT:'Resource-theory network (type E)'};
const LCOL = {S:'var(--s)', M:'var(--m)', O:'var(--o)'}; const BCOL = {EM:'var(--em)', HEP:'var(--hep)', GPT:'var(--gpt)', QRT:'var(--qrt)'};
const byUid = {}; D.nodes.forEach(n => byUid[n.uid] = n);
const inR = {}, outR = {}; D.routes.forEach(r => { (inR[r.target] = inR[r.target] || []).push(r); r.inputs.forEach(u => (outR[u] = outR[u] || []).push(r)); });
const conceptOf = {}; D.concepts.forEach(c => c.members.forEach(u => conceptOf[u] = c));
const YEARS = D.years; // sorted filtration years (union of the four branches)
let state = {view:'timeline', T: YEARS[YEARS.length-1], sel:null, q:'', zoom:'all', branches:{EM:true,HEP:true,GPT:true,QRT:true}, showRemoved:false, playing:false, glue:true};
function esc(s){return String(s==null?'':s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function rich(s){return esc(s).replace(/\^\{([^}]*)\}/g,'<sup>$1</sup>').replace(/_\{([^}]*)\}/g,'<sub>$1</sub>');}
function present(n, T){ if(!state.branches[n.branch]) return false; if(n.year > T) return false; if(n.removed && n.removal_year < T && !state.showRemoved) return false; return true; } // a removed item is present for year <= T <= removal_year
function presentR(r, T){ if(!state.branches[r.branch]) return false; if(r.year > T) return false; if(r.removed && r.removal_year < T && !state.showRemoved) return false; return true; }
function countsAt(T){
  const c = {V:0,S:0,M:0,O:0,E:0}; FOUR.forEach(b => { c[b]={V:0,S:0,M:0,O:0,E:0}; });
  D.nodes.forEach(n => { if(present(n,T)){ c.V++; c[n.layer]++; c[n.branch].V++; c[n.branch][n.layer]++; } });
  D.routes.forEach(r => { if(presentR(r,T)){ c.E++; c[r.branch].E++; } });
  const pm = {}; D.nodes.forEach(n => { if(n.concept && present(n,T)) pm[n.concept] = (pm[n.concept]||0)+1; });
  c.glue = 0; c.shared = 0; Object.values(pm).forEach(k => { if(k>=2){ c.glue += k-1; c.shared++; } });
  c.Vc = c.V - c.glue; return c;
}
document.getElementById('counts').textContent = `${D.counts.nodes} nodes · ${D.counts.routes} routes · ${D.counts.concepts_shared} shared concepts · ${YEARS[0]}–${YEARS[YEARS.length-1]}`;
function nav(){
  const n = document.getElementById('nav'); n.innerHTML = '';
  const mk = (label, on, fn) => { const b = document.createElement('button'); b.textContent = label; if(on) b.className='on'; b.onclick = fn; n.appendChild(b); return b; };
  [['timeline','Timeline'],['snapshot','Snapshot'],['growth','Growth laws'],['concepts','Shared concepts'],['rules','Update rules'],['method','Method & philosophy'],['about','About']].forEach(([v,l]) => mk(l, state.view===v, () => { state.view=v; render(); }));
  const inp = document.createElement('input'); inp.placeholder = 'search label / id'; inp.value = state.q; inp.style.cssText='border:1px solid var(--line);border-radius:6px;padding:5px 8px;font-size:13px;min-width:160px;background:var(--chip);color:var(--ink)';
  inp.oninput = e => { state.q = e.target.value.toLowerCase(); render(); }; n.appendChild(inp);
}
let timer = null;
function ctl(){
  const c = document.getElementById('ctl'); c.innerHTML = '';
  const T = state.T; const idx = YEARS.indexOf(T);
  const mk = (label, on, fn) => { const b = document.createElement('button'); b.textContent = label; if(on) b.className='on'; b.onclick = fn; c.appendChild(b); return b; };
  mk(state.playing ? '❚❚ pause' : '▶ play', state.playing, () => { state.playing = !state.playing; if(state.playing){ timer = setInterval(() => { const i = YEARS.indexOf(state.T); if(i >= YEARS.length-1){ state.playing=false; clearInterval(timer); render(); return; } state.T = YEARS[i+1]; render(); }, 350); } else { clearInterval(timer); } ctl(); });
  mk('◀', false, () => { if(idx>0){ state.T = YEARS[idx-1]; render(); } });
  const yr = document.createElement('span'); yr.className='year'; yr.textContent = T; c.appendChild(yr);
  mk('▶', false, () => { if(idx<YEARS.length-1){ state.T = YEARS[idx+1]; render(); } });
  const rg = document.createElement('input'); rg.type='range'; rg.min=0; rg.max=YEARS.length-1; rg.value=idx; rg.setAttribute('aria-label','year'); rg.oninput = e => { state.T = YEARS[+e.target.value]; render(); }; c.appendChild(rg);
  FOUR.forEach(b => mk(b, state.branches[b], () => { state.branches[b] = !state.branches[b]; render(); }));
  mk(state.showRemoved ? 'HEP removed: shown' : 'HEP removed: hidden', state.showRemoved, () => { state.showRemoved = !state.showRemoved; render(); });
  mk(state.glue ? 'glue chords ✓' : 'glue chords', state.glue, () => { state.glue = !state.glue; render(); });
  [['all','1680–2030'],['modern','1890–2030'],['recent','1960–2030']].forEach(([z,l]) => mk(l, state.zoom===z, () => { state.zoom=z; render(); }));
  const k = countsAt(T); const cnt = document.createElement('span'); cnt.className='cnt';
  cnt.innerHTML = `at ${T}: V=${k.V} (S ${k.S}, M ${k.M}, O ${k.O}), E=${k.E}, glue ${k.glue}, V<sub>collapsed</sub>=${k.Vc} · ` + FOUR.map(b => `<span class="b ${b}">${b}</span>${k[b].V}/${k[b].E}`).join(' ');
  c.appendChild(cnt);
}
// ---------- timeline ----------
const ZOOM = {all:[1680,2030], modern:[1890,2030], recent:[1960,2030]};
function renderTimeline(){
  const main = document.getElementById('main');
  main.innerHTML = `<div id="stage"></div><aside id="rail"></aside>`;
  const stage = document.getElementById('stage'); const T = state.T;
  const W = Math.max(860, stage.clientWidth - 16), laneH = 112, left = 44, right = 16, top = 26;
  const H = top + 4*laneH + 24; const [y0, y1] = ZOOM[state.zoom];
  const x = y => left + (y - y0) / (y1 - y0) * (W - left - right);
  const laneY = {EM:0, HEP:1, GPT:2, QRT:3}; const rowOff = {S:0.22, M:0.5, O:0.78};
  // positions: nodes grouped by (branch, layer, year) spread vertically inside the row
  const groups = {}; D.nodes.forEach(n => { const k = n.branch+'|'+n.layer+'|'+n.year; (groups[k] = groups[k]||[]).push(n); });
  const pos = {};
  Object.values(groups).forEach(g => { g.sort((a,b)=>a.native_id.localeCompare(b.native_id)); g.forEach((n,i) => { const span = Math.min(26, 4.5*(g.length-1)); const dy = g.length>1 ? -span/2 + i*span/(g.length-1) : 0; pos[n.uid] = [x(n.year), top + laneY[n.branch]*laneH + rowOff[n.layer]*laneH + dy]; }); });
  let s = `<svg width="${W}" height="${H}" role="img" aria-label="timeline of the four branches">`;
  FOUR.forEach(b => { const yb = top + laneY[b]*laneH; s += `<rect x="${left}" y="${yb}" width="${W-left-right}" height="${laneH}" fill="var(--lane)" stroke="var(--line)"/>`;
    s += `<text x="${left-6}" y="${yb+laneH/2+4}" text-anchor="end" font-size="11" font-weight="bold" fill="${BCOL[b]}">${b}</text>`;
    ['S','M','O'].forEach(L => s += `<text x="${left+3}" y="${yb+rowOff[L]*laneH+3}" font-size="8" fill="${LCOL[L]}">${L}</text>`); });
  for (let yy = Math.ceil(y0/10)*10; yy <= y1; yy += (state.zoom==='all'?20:10)) s += `<line x1="${x(yy)}" y1="${top}" x2="${x(yy)}" y2="${top+4*laneH}" stroke="var(--line)" stroke-width="0.5"/><text x="${x(yy)}" y="${top-8}" text-anchor="middle" font-size="9" fill="var(--mute)">${yy}</text>`;
  // glue chords (present members)
  if (state.glue) D.concepts.forEach(c => { const ms = c.members.filter(u => present(byUid[u],T) && pos[u]).sort((a,b)=>byUid[a].year-byUid[b].year); for(let i=0;i+1<ms.length;i++){ const [x1,yy1]=pos[ms[i]], [x2,yy2]=pos[ms[i+1]]; if(byUid[ms[i]].branch!==byUid[ms[i+1]].branch) s += `<line x1="${x1}" y1="${yy1}" x2="${x2}" y2="${yy2}" stroke="var(--glue)" stroke-width="0.6" opacity="0.6"/>`; } });
  // routes of this year and of the selected node, as quadratic arcs within the lane
  const arc = (a, b, col, wdt, dash) => { const [x1,yy1]=pos[a], [x2,yy2]=pos[b]; const mx=(x1+x2)/2, my=(yy1+yy2)/2 - Math.min(30, Math.abs(x2-x1)/4) - 6; return `<path d="M${x1},${yy1} Q${mx},${my} ${x2},${yy2}" fill="none" stroke="${col}" stroke-width="${wdt}" ${dash?'stroke-dasharray="3 2"':''} opacity="0.9"/>`; };
  const PCOL = {structural:'var(--o)', possibility:'var(--s)', no_go:'var(--now)', open:'var(--mute)'};
  D.routes.forEach(r => { if(!presentR(r,T)) return; const selTouch = state.sel && (r.target===state.sel || r.inputs.includes(state.sel)); if(r.year===T || selTouch){ r.inputs.forEach(u => { if(pos[u]&&pos[r.target]) s += arc(u, r.target, selTouch ? 'var(--sel)' : PCOL[r.polarity], selTouch?1.6:1.1, r.polarity==='no_go'||r.status==='open'); }); } });
  // nodes
  D.nodes.forEach(n => { if(!state.branches[n.branch] || !pos[n.uid]) return; const [px,py] = pos[n.uid]; if(px < left || px > W-right) return;
    const isP = present(n,T); const rm = n.removed && n.removal_year < T; const match = state.q && (n.label+' '+n.native_id).toLowerCase().includes(state.q);
    const fill = isP ? LCOL[n.layer] : 'var(--future)'; const r0 = n.year===T ? 4.2 : 2.6;
    s += `<circle cx="${px}" cy="${py}" r="${match?5:r0}" fill="${rm&&state.showRemoved?'none':fill}" stroke="${state.sel===n.uid?'var(--sel)':(match?'var(--now)':(rm?LCOL[n.layer]:'none'))}" stroke-width="${state.sel===n.uid||match?2:1}" data-uid="${n.uid}" style="cursor:pointer"><title>${esc(n.label)} (${n.branch}:${n.native_id}, ${n.layer}, ${n.year}${n.removed?', removed '+n.removal_year:''})</title></circle>`; });
  s += `<line x1="${x(T)}" y1="${top-2}" x2="${x(T)}" y2="${top+4*laneH}" stroke="var(--now)" stroke-width="1.4"/><text x="${x(T)+3}" y="${top+4*laneH+14}" font-size="10" fill="var(--now)">${T}</text>`;
  s += '</svg>';
  stage.innerHTML = `<div class="legend">dot = node at its year (<span class="sw" style="background:var(--s)"></span>state <span class="sw" style="background:var(--m)"></span>model <span class="sw" style="background:var(--o)"></span>observable; grey = not yet present at ${T}; large = arrives in ${T}; hollow = removed in HEP); arcs = routes added in ${T} (green structural, blue possibility, red dashed no-go) and routes of the selected node (yellow); thin grey chords = shared concepts across branches. Click a dot.</div>` + s;
  stage.querySelectorAll('circle[data-uid]').forEach(el => el.onclick = () => { state.sel = el.dataset.uid; render(); });
  document.getElementById('rail').innerHTML = state.sel ? railNode(byUid[state.sel]) : railYear(T);
  wireLinks(document.getElementById('rail'));
}
function wireLinks(root){ root.querySelectorAll('a[data-uid]').forEach(a => a.onclick = () => { state.sel = a.dataset.uid; if(state.view!=='timeline'&&state.view!=='snapshot') state.view='timeline'; render(); }); root.querySelectorAll('a[data-year]').forEach(a => a.onclick = () => { state.T = +a.dataset.year; state.view='timeline'; render(); }); }
function routeLine(r){
  const legs = r.inputs.map(u => `<a data-uid="${u}">${rich(byUid[u].label)}</a>`).join(' ∧ ');
  return `<div class="r"><b>${esc(r.native_id)}</b> ${esc(r.kind)}${r.kind_native!==r.kind?' ('+esc(r.kind_native)+')':''} · ${esc(r.polarity)} · <span class="tag">${esc(r.rule)}</span><span class="tag">${esc(r.phase)}</span> <a data-year="${r.year}">${r.year}</a> <span style="color:var(--mute)">(${esc(r.year_prov)})</span>${r.removed?' · removed '+r.removal_year:''}<br>${legs} → <a data-uid="${r.target}">${rich(byUid[r.target].label)}</a>${r.text?'<br><span style="color:var(--mute)">'+esc(r.text)+'</span>':''}</div>`;
}
function railYear(T){
  const arr = D.nodes.filter(n => n.year===T && state.branches[n.branch]); const rts = D.routes.filter(r => r.year===T && state.branches[r.branch]);
  const rm = D.nodes.filter(n => n.removed && n.removal_year===T && state.branches[n.branch]); const rmR = D.routes.filter(r => r.removed && r.removal_year===T && state.branches[r.branch]);
  const rules = {}; rts.forEach(r => { const k = r.branch+' · '+r.rule; rules[k] = (rules[k]||0)+1; });
  const phases = {}; rts.forEach(r => phases[r.phase] = (phases[r.phase]||0)+1); arr.forEach(n => { const p = {O:'observe',M:'hypothesize',S:'restructure'}[n.layer]; phases[p] = (phases[p]||0)+1; });
  let h = `<h3>Year ${T}</h3><div>${arr.length} nodes arrive, ${rts.length} routes added${rm.length||rmR.length?`, ${rm.length} nodes and ${rmR.length} routes removed (HEP)`:''}.</div>`;
  h += `<div class="k">rules firing</div><div>${Object.entries(rules).map(([k,v]) => `<span class="tag">${esc(k)} ×${v}</span>`).join(' ')||'—'}</div>`;
  h += `<div class="k">method phases</div><div>${Object.entries(phases).map(([k,v]) => `<span class="tag">${esc(k)} ×${v}</span>`).join(' ')||'—'}</div>`;
  h += `<div class="k">nodes arriving</div>` + (arr.map(n => `<div class="r"><span class="pill ${n.layer}">${n.layer}</span><span class="b ${n.branch}">${n.branch}</span> <a data-uid="${n.uid}">${rich(n.label)}</a> <span style="color:var(--mute)">${esc(n.sublayer)} · ${esc(n.year_prov||'')}</span></div>`).join('') || '<div>—</div>');
  h += `<div class="k">routes added</div>` + (rts.map(routeLine).join('') || '<div>—</div>');
  if (rm.length) h += `<div class="k">removed (HEP)</div>` + rm.map(n => `<div class="r"><a data-uid="${n.uid}">${rich(n.label)}</a> at step ${n.removal_step}</div>`).join('');
  return h;
}
function railNode(n){
  const c = conceptOf[n.uid];
  let h = `<h3>${rich(n.label)}</h3><span class="pill ${n.layer}">${n.layer} · ${esc(n.sublayer)}</span><span class="b ${n.branch}">${n.branch}</span> <span style="color:var(--mute);font-size:12px">${esc(n.native_id)} · native layer ${esc(n.native_layer)}</span>`;
  h += `<div class="k">year</div><div><a data-year="${n.year}">${n.year}</a> (${esc(n.year_prov||'')})${n.removed?` · removed at step ${n.removal_step} (placed at ${n.removal_year})`:''}${n.step_first?` · HEP steps ${n.step_first}–${n.step_last}`:''}</div>`;
  if (n.desc) h += `<div class="k">description</div><div>${esc(n.desc)}</div>`;
  if (c) { h += `<div class="k">shared concept</div><div><b>${esc(c.label)}</b> <code>${esc(c.id)}</code> · first in ${esc(c.first_dated||'?')}${c.lag_dated!=null?`, lag ${c.lag_dated} y`:''}<br>${esc(c.note||'')}</div>`;
    h += c.members.filter(u => u!==n.uid).map(u => `<div class="r"><span class="pill ${byUid[u].layer}">${byUid[u].layer}</span><span class="b ${byUid[u].branch}">${byUid[u].branch}</span> <a data-uid="${u}">${rich(byUid[u].label)}</a> <a data-year="${byUid[u].year}">${byUid[u].year}</a></div>`).join(''); }
  const ins = (inR[n.uid]||[]).slice().sort((a,b)=>a.year-b.year), outs = (outR[n.uid]||[]).slice().sort((a,b)=>a.year-b.year);
  h += `<div class="k">routes into this node (${ins.length})</div>` + (ins.map(routeLine).join('') || '<div>—</div>');
  h += `<div class="k">routes out of this node (${outs.length})</div>` + (outs.map(routeLine).join('') || '<div>—</div>');
  h += `<div class="k"></div><button class="chip" id="back">← back to year ${state.T}</button>`;
  return h;
}
// ---------- snapshot ----------
const SUBORDER=['S.point','S.field','S.hilbert','S.uir','S.sector','S.cluster','S.free','S.resource','S.dist','M.law','M.frame','M.axiom','M.model','M.fund','M.eff','M.cand','M.cluster','M.process','O.direct','O.effect','O.witness','O.task'];
function renderSnapshot(){
  const main = document.getElementById('main'); const T = state.T;
  let h = `<div id="stage"><div class="legend">Nodes present at ${T} (red left bar = arrives in ${T}; struck = removed by ${T} in HEP, shown when "HEP removed: shown"). Click a chip.</div><div class="cols">`;
  FOUR.forEach(b => { if(!state.branches[b]) return; const nodes = D.nodes.filter(n => n.branch===b && (present(n,T) || (state.showRemoved && n.year<=T)) && (!state.q || (n.label+' '+n.native_id).toLowerCase().includes(state.q)));
    const k = countsAt(T)[b];
    h += `<section class="col ${b}"><h2>${b} · ${k.V} nodes, ${k.E} routes</h2>`;
    ['S','M','O'].forEach(L => { const groups = {}; nodes.filter(n => n.layer===L).forEach(n => (groups[n.sublayer] = groups[n.sublayer]||[]).push(n));
      Object.keys(groups).sort((a,b)=>SUBORDER.indexOf(a)-SUBORDER.indexOf(b)).forEach(g => { h += `<div class="sub">${esc(g)} (${groups[g].length})</div>` + groups[g].sort((a,b)=>a.year-b.year).map(n => `<button class="chip ${n.layer} ${n.year===T?'new':''} ${n.removed&&n.removal_year<T?'rm':''} ${state.sel===n.uid?'sel':''}" data-uid="${n.uid}">${rich(n.label)}<span class="t">${n.year}</span></button>`).join(''); }); });
    h += '</section>'; });
  h += `</div></div><aside id="rail">${state.sel ? railNode(byUid[state.sel]) : railYear(T)}</aside>`;
  main.innerHTML = h;
  main.querySelectorAll('.chip[data-uid]').forEach(bt => bt.onclick = () => { state.sel = bt.dataset.uid; render(); });
  wireLinks(main);
}
// ---------- growth ----------
function spark(curve, key, col, T){
  const W=260,H=60,l=4; const ys = curve.map(r=>r[key]); const max = Math.max(...ys)||1; const x0 = curve[0].year, x1 = curve[curve.length-1].year;
  const x = y => l + (y-x0)/(Math.max(1,x1-x0))*(W-2*l); const y = v => H-4-(v/max)*(H-10);
  let d = ''; curve.forEach((r,i) => { d += (i?'L':'M') + x(r.year).toFixed(1)+','+y(r[key]).toFixed(1); if(i+1<curve.length) d += 'L'+x(curve[i+1].year).toFixed(1)+','+y(r[key]).toFixed(1); });
  const cur = curve.filter(r=>r.year<=T).pop();
  return `<svg width="${W}" height="${H}"><path d="${d}" fill="none" stroke="${col}" stroke-width="1.4"/>${cur?`<line x1="${x(T)}" y1="4" x2="${x(T)}" y2="${H-4}" stroke="var(--now)"/><text x="${Math.min(x(T)+3,W-40)}" y="12" font-size="9" fill="var(--ink)">${key}=${cur[key]}</text>`:''}</svg>`;
}
function renderGrowth(){
  const main = document.getElementById('main'); const T = state.T; let h = '<div class="view">';
  h += `<p>Growth quantities computed on the calendar-year filtration of each branch. Arrival routes are routes dated the year of one of their endpoints; closure routes join nodes that were already present. The counting identity <i>E</i> = Σ<sub>v</sub> d<sub>arr</sub>(v) − Σ<sub>r</sub>(a(r)−1)<sup>+</sup> + closures holds in every branch (a(r) = number of endpoints of r arriving in r's year; the correction is needed because a route with several arriving endpoints is counted once per arriving endpoint).</p>`;
  h += '<div class="tw"><table><tr><th>Branch</th><th>years</th><th class="v">V</th><th>S/M/O</th><th class="v">E</th><th class="v">closures</th><th class="v">closure frac.</th><th>latency mean/median/max (y)</th><th class="v">mean degree at arrival</th><th>α (R²)</th><th>PA ratio (n)</th><th>half-years S/M/O</th></tr>';
  FOUR.forEach(b => { const p = D.branches[b]; const d = p.decomposition; const c = p.curve[p.curve.length-1]; const dn = p.densification; const pa = p.preferential; const hf = p.layer_half;
    h += `<tr><td><span class="b ${b}">${b}</span></td><td>${p.years[0]}–${p.years[1]}</td><td class="v">${c.V}</td><td>${c.S}/${c.M}/${c.O}</td><td class="v">${c.E}</td><td class="v">${d.n_closures}</td><td class="v">${(100*d.closure_fraction).toFixed(0)}%</td><td>${d.latency_mean!=null?d.latency_mean.toFixed(1)+' / '+d.latency_median+' / '+d.latency_max:'—'}</td><td class="v">${d.mean_degree_at_arrival.toFixed(2)}</td><td>${dn.alpha?dn.alpha.toFixed(2)+' ('+dn.r2.toFixed(2)+')':'—'}</td><td>${pa.ratio?pa.ratio.toFixed(2)+' ('+pa.n_closure+')':'—'}</td><td>${hf.S}/${hf.M}/${hf.O}</td></tr>`; });
  h += '</table></div>';
  h += '<div class="k">identity check</div><div class="tw"><table><tr><th>Branch</th><th class="v">Σ d_arr</th><th class="v">Σ (a(r)−1)⁺</th><th class="v">closures</th><th class="v">check</th><th class="v">E</th><th>holds</th></tr>';
  FOUR.forEach(b => { const i = D.branches[b].decomposition.identity; h += `<tr><td>${b}</td><td class="v">${i.sum_arrival_degree}</td><td class="v">${i.excess_multi_arrival}</td><td class="v">${i.closures}</td><td class="v">${i.check}</td><td class="v">${i.E}</td><td>${i.holds?'yes':'no'}</td></tr>`; });
  h += '</table></div>';
  h += `<div class="k">robustness: effect networks dated by the latest cited source instead of the earliest</div><div class="tw"><table><tr><th>branch</th><th>convention</th><th class="v">first year</th><th class="v">closure frac.</th><th class="v">latency median</th><th class="v">α</th><th class="v">PA ratio</th></tr>`;
  ['GPT','QRT'].forEach(b => { const p = D.branches[b]; const d = p.decomposition; const r = D.robustness[b];
    h += `<tr><td>${b}</td><td>earliest (thesis)</td><td class="v">${p.years[0]}</td><td class="v">${(100*d.closure_fraction).toFixed(0)}%</td><td class="v">${d.latency_median}</td><td class="v">${p.densification.alpha.toFixed(2)}</td><td class="v">${p.preferential.ratio.toFixed(2)}</td></tr>`;
    h += `<tr><td>${b}</td><td>latest</td><td class="v">${r.years[0]}</td><td class="v">${(100*r.closure_fraction).toFixed(0)}%</td><td class="v">${r.latency_median}</td><td class="v">${r.densification.alpha.toFixed(2)}</td><td class="v">${r.preferential.ratio.toFixed(2)}</td></tr>`; });
  h += '</table></div>';
  h += `<div class="k">cumulative curves (marker = ${T})</div><div style="display:flex;flex-wrap:wrap;gap:12px">`;
  FOUR.forEach(b => { const p = D.branches[b]; h += `<div><div><span class="b ${b}">${b}</span> nodes V and routes E vs year</div>${spark(p.curve,'V',BCOL[b],T)}${spark(p.curve,'E','var(--ink)',T)}</div>`; });
  h += '</div>';
  const mc = D.merged_curve; const cur = mc.filter(r=>r.year<=T).pop();
  h += `<div class="k">merged network at ${T}</div><div>${cur?`V=${cur.V} (EM ${cur.EM}, HEP ${cur.HEP}, GPT ${cur.GPT}, QRT ${cur.QRT}; S ${cur.S}, M ${cur.M}, O ${cur.O}), E=${cur.E}, glue=${cur.glue}, shared concepts live=${cur.concepts_shared_live}, V<sub>collapsed</sub>=${cur.V_collapsed}. (These merged-curve counts use ever-added HEP nodes; the control bar's counts apply the removal toggle.)`:'—'}</div>`;
  h += `<div class="k">decade table (ΔV by layer, ΔE by method phase)</div><div class="tw"><table><tr><th>decade</th><th>branch</th><th class="v">ΔV</th><th>S/M/O</th><th class="v">ΔE</th>${D.phases.map(p=>`<th class="v">${p}</th>`).join('')}</tr>`;
  D.decade_table.forEach(r => { h += `<tr><td>${r.decade}s</td><td><span class="b ${r.branch}">${r.branch}</span></td><td class="v">${r.nodes}</td><td>${r.S}/${r.M}/${r.O}</td><td class="v">${r.routes}</td>${D.phases.map(p=>`<td class="v">${r.phases[p]||''}</td>`).join('')}</tr>`; });
  h += '</table></div></div>'; main.innerHTML = h;
}
// ---------- concepts ----------
function renderConcepts(){
  const main = document.getElementById('main'); const cs = D.concepts.filter(c => !state.q || (c.label+' '+c.id).toLowerCase().includes(state.q));
  let h = `<div class="view"><p>${cs.length} concepts shared between two or more of the four branches, with the year of first appearance in each branch (earliest dated member). "first" and "lag" exclude project-dated members (marked <sup>p</sup>: no cited source in the data, dated 2026). Years are dates of the earliest cited source in the data, not historical dates.</p><div class="tw"><table><tr><th>concept</th><th>label</th><th>years by branch</th><th>first</th><th class="v">lag (y)</th><th>members</th></tr>`;
  cs.forEach(c => { const ys = Object.entries(c.years).sort((a,b)=>a[1]-b[1]).map(([b,y]) => `<span class="b ${b}">${b}</span><a data-year="${y}">${y}</a>${(c.prov[b]||[]).includes('project')?'<sup>p</sup>':''}`).join(' ');
    h += `<tr><td><code>${esc(c.id)}</code></td><td>${esc(c.label)}</td><td>${ys}</td><td>${c.first_dated||'—'}</td><td class="v">${c.lag_dated!=null?c.lag_dated:'—'}</td><td>${c.members.map(u => `<a data-uid="${u}">${esc(u)}</a>`).join(', ')}</td></tr>`; });
  h += '</table></div></div>'; main.innerHTML = h; wireLinks(main);
}
// ---------- rules ----------
function renderRules(){
  const main = document.getElementById('main'); let h = '<div class="view">';
  h += `<p>Every route of the four branches is attributed to an update rule of the grand network (Part I of the thesis) and to a method phase. Readers (EM): R11 derive / R12 fail. History (HEP): R1–R10 by the route kind (enters → R4 route; predicts → R2; calibrates → R9; backedge → R1/R3 partition-extend; lineage → R7/R10 absorb-cluster; subset → observable family). Effect and resource networks (GPT, QRT): R14 close, split by the polarity of the closing route, and R13 open cell. The tables count firings per decade (route years).</p>`;
  FOUR.forEach(b => { const rd = D.branches[b].rules_by_decade; const decs = Object.keys(rd).sort(); const rules = [...new Set(decs.flatMap(d => Object.keys(rd[d])))].sort();
    h += `<div class="k">${b}</div><div class="tw"><table><tr><th>rule</th>${decs.map(d=>`<th class="v">${d}s</th>`).join('')}<th class="v">total</th></tr>`;
    rules.forEach(rl => { let tot=0; h += `<tr><td>${esc(rl)}</td>${decs.map(d => { const v = rd[d][rl]||0; tot+=v; return `<td class="v">${v||''}</td>`; }).join('')}<td class="v">${tot}</td></tr>`; });
    h += '</table></div>'; });
  h += `<div class="k">Standard Model history: automatically detected rule firings on the year axis</div><div class="tw"><table><tr><th class="v">year</th><th class="v">step</th><th>id</th><th>rules (○ partial)</th></tr>`;
  D.hep_rules_by_year.forEach(r => { h += `<tr><td class="v"><a data-year="${r.year}">${r.year}</a></td><td class="v">${r.step}</td><td>${esc(r.id)}</td><td>${Object.entries(r.rules).sort((a,b)=>+a[0]-+b[0]).map(([k,v]) => 'R'+k+(v==='●'?'':'○')).join(', ')||'—'}</td></tr>`; });
  h += '</table></div>';
  h += `<div class="k">temporal growth rules (TE1–TE6) read off the data</div><ol>` + D.te_rules.map(t => `<li>${esc(t)}</li>`).join('') + '</ol></div>';
  main.innerHTML = h; wireLinks(main);
}
// ---------- method ----------
function renderMethod(){
  const main = document.getElementById('main'); let h = '<div class="view">';
  h += `<p>Method phases are assigned mechanically: a node arrival is an <i>observe</i> (O), <i>hypothesize</i> (M) or <i>restructure</i> (S) event; a route is assigned by its kind (derives, implies, enables, converts_to … → predict; failed, not_implies, forbids, violates … → falsify; enters, backedge, member, satisfies → restructure; frames, candidate, generates → hypothesize; lineage, subset, equiv, specializes, contains → reduce; calibrates → calibrate; witness, pairs → observe; open status → deficit). The table counts items per decade over the four branches.</p>`;
  h += `<div class="tw"><table><tr><th>decade</th>${D.phases.map(p=>`<th class="v">${p}</th>`).join('')}<th class="v">total</th></tr>`;
  D.merged_phases.forEach(r => { if(!r.total) return; h += `<tr><td>${r.decade}s</td>${D.phases.map(p=>`<td class="v">${r[p]||''}</td>`).join('')}<td class="v">${r.total}</td></tr>`; });
  h += '</table></div>';
  h += `<div class="k">philosophy of science, as graph operations</div><ul>` + D.philosophy.map(t => `<li><b>${esc(t[0])}</b> — ${esc(t[1])}</li>`).join('') + '</ul></div>';
  main.innerHTML = h;
}
function renderAbout(){
  let h = `<div class="view"><h3>About</h3><p>This page is generated by <code>gen_engine/page_evo.py</code> from <code>data/gen_evolution_network.json</code> and <code>out/evolution.json</code> (generated ${esc(D.generated)}). It places every node and route of the four branches on a calendar-year axis derived from the released data by explicit rules, and shows the merged four-branch evolutionary network.</p>`;
  h += `<div class="k">dating rules</div><pre style="white-space:pre-wrap;font-size:12px">${esc(D.dating_rules)}</pre>`;
  h += `<div class="k">provenance of the year index</div><div class="tw"><table><tr><th>branch</th><th>node years</th><th>route years</th></tr>`;
  FOUR.forEach(b => { const p = D.provenance[b]; h += `<tr><td>${b}</td><td>${Object.entries(p).filter(([k])=>k.startsWith('node:')).map(([k,v])=>k.slice(5)+' '+v).join(', ')}</td><td>${Object.entries(p).filter(([k])=>k.startsWith('route:')).map(([k,v])=>k.slice(6)+' '+v).join(', ')}</td></tr>`; });
  h += '</table></div>';
  h += `<div class="k">limitations</div><ul><li>Years are the earliest cited source in the data, not historical dates (e.g. Bell nonlocality is dated 1969 by its CHSH citation; Kochen–Specker contextuality 1990; Wigner negativity 1946 by Groenewold). The ordering of events is therefore the ordering of the sources used by the networks' authors.</li><li>${esc(D.counts.project_nodes)} nodes without any dated source are dated 2026 (project year) and flagged; they are excluded from lag statistics.</li><li>The HEP source is a thematic step sequence; years come from the nodes' own year fields; the final view (step 12) is placed at 2012. Removals are placed at the start year of the removing step, never before the item's own year.</li><li>Nothing here is a historical claim beyond the data; the thesis states every rule and every number is computed.</li></ul>`;
  h += `<div class="k">generation</div><p>The data files, the analysis code, the figures and this page were generated with the assistance of an AI model (Claude, Anthropic); the author retains responsibility for the content.</p></div>`;
  document.getElementById('main').innerHTML = h;
}
function render(){ nav(); ctl(); ({timeline:renderTimeline, snapshot:renderSnapshot, growth:renderGrowth, concepts:renderConcepts, rules:renderRules, method:renderMethod, about:renderAbout})[state.view](); const bk = document.getElementById('back'); if(bk) bk.onclick = () => { state.sel=null; render(); }; }
let rt = null; window.addEventListener('resize', () => { if(state.view==='timeline'){ clearTimeout(rt); rt = setTimeout(render, 150); } });
render();
</script>"""

TE_RULES = [
    "TE1 (arrival rule). A new node enters with its arrival routes, dated the same year; the mean degree at arrival is branch-specific (EM {EMMeanArrDeg}, HEP {HEPMeanArrDeg}, GPT {GPTMeanArrDeg}, QRT {QRTMeanArrDeg}) and is the dominant term of E in the reader and the history (closure fractions {EMClosureFrac}% and {HEPClosureFrac}%).",
    "TE2 (closure rule). In the effect and resource networks a large share of routes are closures between nodes already present (GPT {GPTClosureFrac}%, QRT {QRTClosureFrac}%), with latencies of median {GPTLatMedian} years (GPT) and {QRTLatMedian} years (QRT): the census of open cells (R13) is worked off years after the nodes appear.",
    "TE3 (preferential closure). Closure routes attach to nodes whose degree is above the mean degree of the nodes present (endpoint/present degree ratio GPT {GPTPAratio}, QRT {QRTPAratio}, EM {EMPAratio}; HEP has only {HEPPAn} closures): the open cells closed first are those adjacent to the best-connected nodes.",
    "TE4 (densification). On the year filtration E grows faster than V: E ∝ V^α with α = {EMAlpha} (EM), {HEPAlpha} (HEP), {GPTAlpha} (GPT), {QRTAlpha} (QRT); routes accumulate super-linearly in the node count.",
    "TE5 (removal rule). Only the history branch removes items: {hepRemovedNodes} of {HEPVfin} nodes and {hepRemovedRoutes} of {hepUnionRoutes} routes of the Standard Model union are removed at some step (absorption into a successor model, R7/R10, or the final clustering); the reader and the effect networks are monotone.",
    "TE6 (transfer rule). A concept shared by two branches appears in the second branch with a lag (median {lagMedian} years over the {nSharedDated} dated shared concepts; GPT precedes QRT in {firstGPTamongGQ} of {nSharedGPTQRT} GPT–QRT concepts, QRT precedes in {firstQRTamongGQ}, {tieGQ} tie); glue identifications accumulate to {mergedGlue} by 2026.",
]
PHILOSOPHY = [
    ("Popper (falsification)", "a no-go or failed route: R12 fail in the reader ({emFailedTotal} failed derivations in EM), the no_go polarity of R14 closures in the effect networks (the first incident edge of {gptMnoGoFirst} of the {gptMtotal} GPT model nodes is a pure no-go, {gptMnoGoAny} include one), and the anomaly steps of the history (R2 fires on an observable without a model edge)."),
    ("Lakatos (research programmes)", "nodes that survive every restructuring versus nodes that are replaced: in HEP the cluster nodes ({hepMclusterRemoved} of {hepMclusterAll} removed) and the frames ({hepMframeRemoved} of {hepMframeAll} removed) persist, while the fundamental model nodes ({hepMfundRemoved} of {hepMfundAll}), the effective and candidate models ({hepMeffRemoved} of {hepMeffAll}, {hepMcandRemoved} of {hepMcandAll}) and the UIR state nodes ({hepSuirRemoved} of {hepSuirAll}) are absorbed; the effect networks never remove their {gptAxioms} (GPT) and {qrtAxioms} (QRT) axiom nodes. The data distinguishes absorption by a successor (reduce) from refutation (falsify)."),
    ("Kuhn (paradigm change)", "restructuring events in the state layer: R1/R3 partition-extend and backedges (the Hilbert → Fock → UIR re-partition of HEP in 1926–1939; the free/resource partitions of QRT), counted in the restructure phase, rather than the accumulation of routes."),
    ("Duhem–Quine (holism)", "AND routes: {emDeriveAND} of {emDeriveTotal} EM derivations and {emFailedAND} of {emFailedTotal} failed EM routes have two or more inputs (model and state jointly), and {hepEntersAND} of {hepEntersTotal} HEP state→model routes are AND routes with occupation numbers; a failed AND route cannot by itself locate the faulty input."),
    ("Hempel (explanation)", "an M→O route into an effect: the explanation lag measures the years between an effect's first appearance and its first model edge (GPT: {gptEffectsWithM} of {gptEffects} effects have one; mean lag {gptLagMean} y, Bell nonlocality {gptLagBell} y, Kirkwood–Dirac family {gptLagKD} y; {gptLagZero} explained in their first year). HEP predictions are all single M→O routes ({hepPredictsMO} of {hepPredictsTotal})."),
    ("Carnap / Reichenbach (reduction; discovery vs justification)", "reduce routes (lineage, subset, equiv, specializes, contains) collapse a cluster into its successor; the status field of a route records justification, its year records discovery."),
]


def build():
    net = json.load(open(os.path.join(HERE, "data", "gen_evolution_network.json")))
    R = json.load(open(os.path.join(HERE, "out", "evolution.json")))
    N = json.load(open(os.path.join(HERE, "out", "numbers_evo.json")))
    years = sorted({n["year"] for n in net["nodes"]} | {r["year"] for r in net["routes"]} | {n["removal_year"] for n in net["nodes"] if n.get("removal_year")})
    concepts = []
    for c in R["concepts"]:
        members = [n["uid"] for n in net["nodes"] if n.get("concept") == c["id"]]
        concepts.append({**c, "members": members})
    branches = {}
    for b in ("EM", "HEP", "GPT", "QRT"):
        p = R["branches"][b]
        branches[b] = {"years": p["years"], "curve": p["curve"], "decomposition": {k: v for k, v in p["decomposition"].items() if k != "closures"},
                       "densification": p["densification"], "preferential": p["preferential"], "layer_half": p["layer_half"], "rules_by_decade": p["rules_by_decade"]}
    # fill the TE rules with the computed numbers (the strings above are templates checked against numbers_evo.json)
    te = [t.format(**N) for t in TE_RULES]
    phil = [(a, b.format(**N)) for a, b in PHILOSOPHY]
    data = {"generated": R["generated"], "nodes": net["nodes"], "routes": net["routes"], "concepts": concepts, "years": years, "branches": branches,
            "robustness": {b: {k: v for k, v in R["robustness_max_dating"][b].items() if k != "provenance"} for b in ("GPT", "QRT")},
            "merged_curve": R["merged_curve"], "decade_table": R["decade_table"], "merged_phases": R["merged_phases"], "hep_rules_by_year": R["hep_rules_by_year"],
            "phases": ["observe", "deficit", "hypothesize", "restructure", "predict", "falsify", "calibrate", "reduce"], "provenance": R["provenance"],
            "dating_rules": net["dating_rules"], "counts": {**net["counts"], "project_nodes": N["gptProjectNodes"] + N["qrtProjectNodes"]}, "te_rules": te, "philosophy": phil}
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    body = HEAD + "\n" + BODY.replace("__DATA__", payload)
    standalone = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n' + body.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "") + "\n</body></html>\n"
    # the standalone head must contain the title/style; move the body part after </head><body>
    standalone = standalone.replace("</style>\n<header>", "</style></head><body>\n<header>", 1)
    with open(os.path.join(HERE, "gen_evolution_explorer.html"), "w", encoding="utf-8") as f:
        f.write(standalone)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    with open(os.path.join(HERE, "out", "artifact_evolution.html"), "w", encoding="utf-8") as f:
        f.write(body)
    print("evolution explorer written:", len(standalone), "bytes")


if __name__ == "__main__":
    build()
