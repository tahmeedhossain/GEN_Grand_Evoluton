"""Build the self-contained explorer page gen_grand_explorer.html from the merged network and the results."""
from __future__ import annotations
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Grand Epistemic Network</title>
<style>
/* layout: top bar, three layer columns (states / models / observables) and a detail rail */
:root{--s:#2a6f97;--m:#c05c2a;--o:#3f7d4e;--bg:#fafaf8;--ink:#1e1e1e;--line:#d8d8d2;--rail:#ffffff;--chip:#ffffff;--mute:#666666;--btn:#f4f4f0;--btnon:#1e1e1e;--btnon-fg:#ffffff;--th:#f1f1ec;--flip:#b5651d;--link:#2a6f97;--sel:#1e1e1e}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--s:#5a9bc4;--m:#d98557;--o:#6fae7e;--bg:#15171a;--ink:#e6e6e2;--line:#3a3d42;--rail:#1d2024;--chip:#1d2024;--mute:#9a9a94;--btn:#24272c;--btnon:#e6e6e2;--btnon-fg:#15171a;--th:#24272c;--flip:#e9a23b;--link:#8ec3e6;--sel:#e6e6e2;color-scheme:dark}}
:root[data-theme="dark"]{--s:#5a9bc4;--m:#d98557;--o:#6fae7e;--bg:#15171a;--ink:#e6e6e2;--line:#3a3d42;--rail:#1d2024;--chip:#1d2024;--mute:#9a9a94;--btn:#24272c;--btnon:#e6e6e2;--btnon-fg:#15171a;--th:#24272c;--flip:#e9a23b;--link:#8ec3e6;--sel:#e6e6e2;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 "DejaVu Sans",system-ui,sans-serif;color:var(--ink);background:var(--bg)}
header{padding-block:10px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));border-bottom:1px solid var(--line);background:var(--rail);display:flex;flex-wrap:wrap;gap:10px;align-items:baseline}
header h1{font-size:17px;margin:0 12px 0 0}header .sub{color:var(--mute);font-size:12px}
nav{display:flex;flex-wrap:wrap;gap:6px;padding-block:8px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));border-bottom:1px solid var(--line);background:var(--rail)}
nav button{border:1px solid var(--line);background:var(--btn);color:var(--ink);border-radius:6px;padding:5px 10px;cursor:pointer;font-size:13px}
nav button.on{background:var(--btnon);color:var(--btnon-fg);border-color:var(--btnon)}
nav button:focus-visible,.chip:focus-visible{outline:2px solid var(--link);outline-offset:1px}
nav input{border:1px solid var(--line);border-radius:6px;padding:5px 8px;font-size:13px;min-width:200px;background:var(--chip);color:var(--ink)}
main{display:grid;grid-template-columns:1fr 1fr 1fr 380px;gap:0;min-height:calc(100vh - 100px);padding-left:max(0px,env(safe-area-inset-left,0px));padding-right:max(0px,env(safe-area-inset-right,0px))}
.col{border-right:1px solid var(--line);padding:8px;overflow:auto;max-height:calc(100vh - 100px);min-width:0}
.col h2{font-size:13px;margin:4px 0 8px;padding:4px 8px;border-radius:6px;color:#fff}
.col.S h2{background:var(--s)}.col.M h2{background:var(--m)}.col.O h2{background:var(--o)}
.sub{font-size:11px;color:var(--mute);margin:8px 0 3px;text-transform:uppercase;letter-spacing:.04em}
.chip{display:block;width:100%;text-align:left;border:1px solid var(--line);background:var(--chip);color:var(--ink);border-radius:6px;padding:4px 7px;margin:3px 0;cursor:pointer;font-size:12.5px}
.chip:hover{border-color:var(--mute)}.chip.sel{outline:2px solid var(--sel)}.chip .t{color:var(--mute);font-size:11px;margin-left:4px}
.chip.glued{border-left:4px solid var(--mute)}.chip.flip{border-left:4px solid var(--flip)}
#rail{background:var(--rail);padding:10px 12px;overflow:auto;max-height:calc(100vh - 100px);font-size:13px;min-width:0}
#rail h3{margin:4px 0 2px;font-size:15px}#rail .k{color:var(--mute);font-size:11px;text-transform:uppercase;letter-spacing:.04em;margin-top:10px}
#rail .r{border-left:3px solid var(--line);padding:3px 8px;margin:4px 0;font-size:12px;overflow-wrap:anywhere}
#rail .r b{font-family:"DejaVu Sans Mono",monospace;font-size:11px}
#rail a,.view a{color:var(--link);cursor:pointer;text-decoration:underline dotted}
.pill{display:inline-block;border-radius:10px;padding:1px 7px;font-size:11px;color:#fff;margin-right:4px}.pill.S{background:var(--s)}.pill.M{background:var(--m)}.pill.O{background:var(--o)}
table{border-collapse:collapse;font-size:12px}td,th{border:1px solid var(--line);padding:3px 6px;text-align:left;vertical-align:top}th{background:var(--th)}
.view{padding-block:12px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));overflow:auto;max-height:calc(100vh - 100px);grid-column:1/5;min-width:0}
.view .tw{overflow-x:auto}
.mat td.v{text-align:right;font-variant-numeric:tabular-nums}
.flip{color:var(--flip);font-weight:bold}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
@media (max-width:900px){main{grid-template-columns:1fr}.col{max-height:none;border-right:none;border-bottom:1px solid var(--line)}#rail{max-height:none}.view{grid-column:1/2;max-height:none}}
</style></head><body>
<header><h1>Grand Epistemic Network</h1><span class="sub" id="counts"></span></header>
<nav id="nav"></nav>
<main id="main"></main>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const byUid = {}; D.nodes.forEach(n => byUid[n.uid] = n);
const inR = {}, outR = {}; D.routes.forEach(r => { (inR[r.target] = inR[r.target] || []).push(r); r.inputs.forEach(u => (outR[u] = outR[u] || []).push(r)); });
const conceptOf = {}; D.concepts.forEach(c => c.members.forEach(u => conceptOf[u] = c));
const BT = {UP:'University Physics reader (D)', EM:'EM history reader (D)', LG:'LocGlob energy flow (D)', HEP:'Standard Model history (H)', GPT:'Nonclassicality network (E)', QRT:'Resource-theory network (E)'};
const ORDER = ['UP','EM','LG','HEP','GPT','QRT'];
let state = {view:'branch', branch:'HEP', sel:null, q:'', flipsOnly:false, era:'all'};
document.getElementById('counts').textContent = `${D.counts.branches} branches · ${D.counts.nodes} nodes · ${D.counts.routes} routes · ${D.counts.concepts} shared concepts (${D.counts.role_flips} role flips)`;
function esc(s){return String(s==null?'':s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function rich(s){return esc(s).replace(/\^\{([^}]*)\}/g,'<sup>$1</sup>').replace(/_\{([^}]*)\}/g,'<sub>$1</sub>');}
const SUBORDER=['S.point','S.field','S.hilbert','S.uir','S.sector','S.cluster','S.free','S.resource','S.dist','M.law','M.frame','M.axiom','M.model','M.fund','M.eff','M.cand','M.cluster','M.process','O.direct','O.effect','O.witness','O.task'];
function nav(){
  const n = document.getElementById('nav'); n.innerHTML = '';
  const mk = (label, on, fn) => { const b = document.createElement('button'); b.textContent = label; if(on) b.className='on'; b.onclick = fn; n.appendChild(b); };
  ORDER.forEach(b => mk(b, state.view==='branch' && state.branch===b, () => { state.view='branch'; state.branch=b; state.sel=null; render(); }));
  mk('Concepts', state.view==='concepts', () => { state.view='concepts'; render(); });
  mk('Signatures', state.view==='sig', () => { state.view='sig'; render(); });
  mk('Agenda', state.view==='agenda', () => { state.view='agenda'; render(); });
  mk('About', state.view==='about', () => { state.view='about'; render(); });
  const inp = document.createElement('input'); inp.placeholder = 'search label / id'; inp.value = state.q; inp.oninput = e => { state.q = e.target.value.toLowerCase(); render(); }; n.appendChild(inp);
  mk(state.flipsOnly ? 'glued only ✓' : 'glued only', state.flipsOnly, () => { state.flipsOnly = !state.flipsOnly; render(); });
}
function nodeMatches(n){ if(state.flipsOnly && !n.concept) return false; if(!state.q) return true; return (n.label+' '+n.native_id+' '+(n.concept||'')).toLowerCase().includes(state.q); }
function chip(n){
  const c = conceptOf[n.uid]; const cls = ['chip']; if(c) cls.push(c.flip ? 'flip' : 'glued'); if(state.sel===n.uid) cls.push('sel');
  return `<button class="${cls.join(' ')}" data-uid="${n.uid}">${rich(n.label)}<span class="t">${n.t!=null?('t='+n.t):''}</span></button>`;
}
function renderBranch(){
  const main = document.getElementById('main'); const nodes = D.nodes.filter(n => n.branch===state.branch && nodeMatches(n));
  const br = D.branches.find(b => b.id===state.branch);
  let html = '';
  for (const L of ['S','M','O']) {
    const groups = {}; nodes.filter(n => n.layer===L).forEach(n => (groups[n.sublayer] = groups[n.sublayer] || []).push(n));
    html += `<section class="col ${L}"><h2>${{S:'States',M:'Models',O:'Observables'}[L]} · ${nodes.filter(n=>n.layer===L).length}</h2>`;
    Object.keys(groups).sort((a,b)=>SUBORDER.indexOf(a)-SUBORDER.indexOf(b)).forEach(g => { html += `<div class="sub">${esc(g)} (${groups[g].length})</div>` + groups[g].sort((a,b)=>(a.t??0)-(b.t??0)).map(chip).join(''); });
    html += '</section>';
  }
  html += `<aside id="rail">${state.sel ? railNode(byUid[state.sel]) : railBranch(br)}</aside>`;
  main.innerHTML = html;
  main.querySelectorAll('.chip').forEach(b => b.onclick = () => { state.sel = b.dataset.uid; render(); });
  main.querySelectorAll('a[data-uid]').forEach(a => a.onclick = () => { const u = a.dataset.uid; state.branch = u.split(':')[0]; state.sel = u; state.view='branch'; render(); });
}
function railBranch(br){
  const pb = D.counts.per_branch[br.id];
  return `<h3>${esc(BT[br.id])}</h3><div>${esc(br.title)}</div><div class="k">source</div><div>${esc(br.source)} · version ${esc(br.version)}</div><div class="k">time axis</div><div>${esc(br.time_axis)}</div>
  <div class="k">layer map</div><div>${Object.entries(br.layer_map).map(([k,v])=>`${esc(k)} → ${v}`).join('; ')}</div><div class="k">counts</div><div>${pb.nodes} nodes (S ${pb.S}, M ${pb.M}, O ${pb.O}), ${pb.routes} routes, ${pb.AND} AND routes, ${pb.or_targets} OR targets</div>
  <div class="k">notes</div><div>${esc(br.notes)}</div><div class="k">legend</div><div>grey left bar: node glued to a concept in another branch; orange left bar: the concept changes layer across branches (role flip). Click a node for its routes and its concept.</div>`;
}
function routeLine(r, dir){
  const legs = r.inputs.map(u => `<a data-uid="${u}">${rich(byUid[u].label)}</a>`).join(' ∧ ');
  const tgt = `<a data-uid="${r.target}">${rich(byUid[r.target].label)}</a>`;
  const txt = r.extra.rel || r.extra.statement || r.extra.formula || r.extra.title || r.extra.label || '';
  return `<div class="r"><b>${esc(r.native_id)}</b> ${esc(r.kind)}${r.kind_native!==r.kind?' ('+esc(r.kind_native)+')':''} · ${esc(r.status)} · ${esc(r.polarity)}<br>${legs} → ${tgt}${txt?'<br><span style="color:#444">'+esc(String(txt).slice(0,420))+'</span>':''}</div>`;
}
function railNode(n){
  const c = conceptOf[n.uid]; const ex = n.extra || {};
  const desc = ex.desc || ex.description || ex.statement || ex.def || '';
  let h = `<h3>${rich(n.label)}</h3><span class="pill ${n.layer}">${n.layer} · ${esc(n.sublayer)}</span><span style="color:#666;font-size:12px">${esc(n.branch)}:${esc(n.native_id)} · native layer ${esc(n.native_layer)}${n.era?' · '+esc(n.era):''}${n.t!=null?' · t='+n.t:''}</span>`;
  if (desc) h += `<div class="k">description</div><div>${esc(desc)}</div>`;
  if (ex.formula || ex.math_structure) h += `<div class="k">mathematics</div><div>${esc(ex.formula||'')} ${esc(ex.math_structure||'')}</div>`;
  if (ex.properties && ex.properties.length) h += `<div class="k">properties</div><div>${ex.properties.map(esc).join('; ')}</div>`;
  if (ex.refs && ex.refs.length) h += `<div class="k">references</div><div>${ex.refs.map(esc).join('; ')}</div>`;
  if (ex.steps_present) h += `<div class="k">steps present</div><div>${ex.steps_present.join(', ')}${ex.in_final?' (in the final graph)':''}</div>`;
  if (c) { h += `<div class="k">concept</div><div><b>${esc(c.label)}</b> <code>${esc(c.id)}</code>${c.flip?' <span class="flip">role flip</span>':''}<br>${esc(c.note)}</div><div class="k">members in other branches</div>`;
    h += c.members.filter(u => u!==n.uid).map(u => `<div class="r"><span class="pill ${byUid[u].layer}">${byUid[u].layer}</span><a data-uid="${u}">${rich(byUid[u].label)}</a> <span style="color:#666">(${esc(u)})</span></div>`).join('') || '<div>—</div>'; }
  const cx = D.cross_edges.filter(e => e.from===n.uid || e.to===n.uid || (c && e.to==='c:'+c.id));
  if (cx.length) h += `<div class="k">cross-edges</div>` + cx.map(e => `<div class="r">${esc(e.from)} —${esc(e.relation)}→ ${esc(e.to)}${e.note?'<br><span style="color:#444">'+esc(e.note)+'</span>':''}</div>`).join('');
  const ins = inR[n.uid] || [], outs = outR[n.uid] || [];
  h += `<div class="k">routes into this node (${ins.length})</div>` + (ins.map(r => routeLine(r)).join('') || '<div>— primitive in this branch</div>');
  h += `<div class="k">routes out of this node (${outs.length})</div>` + (outs.map(r => routeLine(r)).join('') || '<div>—</div>');
  return h;
}
function renderConcepts(){
  const main = document.getElementById('main'); const cs = D.concepts.filter(c => !state.q || (c.label+' '+c.id+' '+c.members.join(' ')).toLowerCase().includes(state.q)).filter(c => !state.flipsOnly || c.flip);
  let h = `<div class="view"><p>${cs.length} concepts. A concept is one physical idea that appears in two or more branches; the role (layer) of its member nodes is read from the data. <span class="flip">Orange</span> rows are role flips. Click a member to open it.</p><div class="tw"><table><tr><th>concept</th><th>label</th><th>members (branch: role · node)</th><th>note</th></tr>`;
  cs.forEach(c => { h += `<tr><td><code>${esc(c.id)}</code>${c.flip?'<br><span class="flip">flip</span>':''}</td><td>${esc(c.label)}</td><td>${c.members.map(u => `${u.split(':')[0]}: <span class="pill ${byUid[u].layer}">${byUid[u].layer}</span><a data-uid="${u}">${rich(byUid[u].label)}</a>`).join('<br>')}</td><td style="max-width:360px">${esc(c.note)}</td></tr>`; });
  h += '</table></div></div>'; main.innerHTML = h;
  main.querySelectorAll('a[data-uid]').forEach(a => a.onclick = () => { const u = a.dataset.uid; state.branch = u.split(':')[0]; state.sel = u; state.view='branch'; render(); });
}
function renderSig(){
  const main = document.getElementById('main'); const R = D.results; let h = '<div class="view"><p>Layer-pair signatures: leg–route incidences from the input layer (row) to the target layer (column). The support of the matrix defines the branch type. For HEP the expanded routes (generic layer edges expanded to every sector) and the record-level counts of the final step are both given.</p><div style="display:flex;flex-wrap:wrap;gap:18px">';
  ORDER.forEach(b => { const pm = R.signatures[b].pair_matrix; h += `<table class="mat"><tr><th>${b}</th><th>→S</th><th>→M</th><th>→O</th></tr>` + ['S','M','O'].map(a => `<tr><th>${a}→</th>` + ['S','M','O'].map(t => `<td class="v">${pm[a+'->'+t]||''}</td>`).join('') + '</tr>').join('') + '</table>'; });
  const rec = R.signatures.HEP.record_level_final_step; h += `<table class="mat"><tr><th>HEP records (final step)</th><th>n</th></tr>` + Object.entries(rec).map(([k,v]) => `<tr><td>${esc(k)}</td><td class="v">${v}</td></tr>`).join('') + '</table>';
  h += '</div></div>'; main.innerHTML = h;
}
function renderAgenda(){
  const R = D.results; const main = document.getElementById('main'); let h = '<div class="view"><p>The research agenda computed from the data (Theorem: computable in linear time in the graph plus the census). Nothing here is a claim of novelty: an item is a place where the compiled data record no edge.</p>';
  const hep = R.hep; const last = hep.cumulative[hep.cumulative.length-1];
  h += `<h3>HEP (type H)</h3><ul><li>unexplained observables (cumulative, with family closure): ${last.unexplained_cumulative.join(', ')||'none'}</li><li>candidate model node: m_numass (candidate route ν(2)∧H(2))</li><li>untested prediction: o_lam (λ_HHH)</li><li>effective nodes surviving: ${hep.steps[hep.steps.length-1].eff}; shared calibrations: ${hep.steps[hep.steps.length-1].shared_calibrations.length}</li><li>sector × term census: ${hep.sector_term_census.entered} of ${hep.sector_term_census.cells} cells filled (${hep.sector_term_census.empty} empty, to be labelled forbidden or omitted)</li><li>rule detection: ${hep.comparison.agree}/120 cells agree with the hand matrix; disagreements ${JSON.stringify(hep.comparison.details.map(d=>'step '+d.step+' R'+d.rule+' auto='+(d.auto||'·')+' hand='+(d.hand||'·')))}</li></ul>`;
  for (const b of ['EM','UP','LG']) { const t = R.typeD[b]; h += `<h3>${b} (type D)</h3><ul><li>forward links: ${t.filtration.forward_links} (filtration holds)</li><li>failed routes: ${t.failed.n_failed}, forward-resolved ${t.failed.n_resolved}${t.failed.max_distance!=null?', max distance '+t.failed.max_distance:''}</li><li>primitive nodes: S ${t.agenda.n_primitive.S}, M ${t.agenda.n_primitive.M}, O ${t.agenda.n_primitive.O} (${t.agenda.primitive_nodes.O.join(', ')||'no primitive observable'})</li><li>2-section: ${t.depth.edges_2section} edges, ${t.depth.acyclic?'acyclic':'cycles: '+t.depth.nodes_in_cycles+' nodes in '+t.depth.n_nontrivial_sccs+' component(s)'}</li></ul>`; }
  const g = R.typeE.GPT; h += `<h3>GPT (type E)</h3><ul><li>witness matrix: ${g.witness_census.settled} of ${g.witness_census.cells} cells settled, ${g.witness_census.uncharted} uncharted</li><li>node pairs: ${g.pair_census.connected_pairs} of ${g.pair_census.pairs} connected</li><li>open edges: ${g.agenda.open_edges.join(', ')}; partial: ${g.agenda.partial_edges.join(', ')}; recorded gaps: ${g.agenda.recorded_gaps}</li></ul>`;
  const q = R.typeE.QRT; h += `<h3>QRT (type E)</h3><ul><li>conversion matrix: ${q.conversion_census.charted_conversion_group} of ${q.conversion_census.cells} cells charted (${q.conversion_census.charted_state_to_state} with any state-to-state cross-theory edge, ${q.conversion_census.cross_theory_any} with any cross-theory edge)</li><li>partial: ${q.agenda.partial_edges.join(', ')}; recorded gaps: ${q.agenda.recorded_gaps}</li></ul>`;
  h += '</div>'; main.innerHTML = h;
}
function renderAbout(){
  document.getElementById('main').innerHTML = `<div class="view"><h3>About</h3><p>This page is generated by <code>gen_engine/page.py</code> from <code>data/gen_grand_network.json</code> and <code>out/results.json</code>: six released GEN instances normalised into one schema (states, models, observables with sub-layers; routes as directed hyperedges with universal and native kinds), glued on ${D.counts.concepts} curated concepts. Branch types: D (dynamic/pedagogical readers), H (historical theory-building), E (effect/resource networks). Sources: ${D.branches.map(b=>esc(b.source)).join('; ')}.</p><p>The thesis (<code>thesis/main.pdf</code>) states the definitions, the operations and rules, the replay of the Standard Model history, the filtration checks of the readers, the census of the quantum networks and the pedagogical comparison. Generated with Claude (Anthropic) for Tahmeed Hossain, Department of Theoretical Physics, University of Dhaka, November 2026.</p></div>`;
}
function render(){ nav(); ({branch:renderBranch, concepts:renderConcepts, sig:renderSig, agenda:renderAgenda, about:renderAbout})[state.view](); }
render();
</script></body></html>
"""


def main():
    atlas = json.load(open(os.path.join(HERE, "data", "gen_grand_network.json"), encoding="utf-8"))
    results = json.load(open(os.path.join(HERE, "out", "results.json"), encoding="utf-8"))
    # slim the results for the page
    slim = {"signatures": results["signatures"],
            "hep": {"cumulative": results["hep"]["cumulative"], "steps": results["hep"]["steps"], "sector_term_census": {k: v for k, v in results["hep"]["sector_term_census"].items() if k != "matrix"}, "comparison": results["hep"]["comparison"]},
            "typeD": {b: {"filtration": results["typeD"][b]["filtration"], "failed": {k: v for k, v in results["typeD"][b]["failed"].items() if k != "rows"},
                          "agenda": results["typeD"][b]["agenda"], "depth": {k: v for k, v in results["typeD"][b]["depth"].items() if k not in ("cycles_sample", "longest_chain_nodes")}} for b in ("EM", "UP", "LG")},
            "typeE": {"GPT": {"witness_census": {k: v for k, v in results["typeE"]["GPT"]["witness_census"].items() if k != "per_witness"}, "pair_census": {k: v for k, v in results["typeE"]["GPT"]["pair_census"].items() if k != "by_native_layer_pair"}, "agenda": results["typeE"]["GPT"]["agenda"]},
                      "QRT": {"conversion_census": {k: v for k, v in results["typeE"]["QRT"]["conversion_census"].items() if k not in ("matrix", "via", "charted_cells")}, "agenda": results["typeE"]["QRT"]["agenda"]}}}
    atlas["results"] = slim
    # drop heavy per-node extras that the page does not show
    for n in atlas["nodes"]:
        ex = n.get("extra", {})
        for k in ("book_terms", "mentioned_in", "coverage"):
            ex.pop(k, None)
    data = json.dumps(atlas, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("__DATA__", data)
    out = os.path.join(HERE, "gen_grand_explorer.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", out, len(html) // 1024, "kB")
    # artifact form: no document skeleton (the host adds it); title and viewport meta first
    body_start = html.index("<style>")
    body_end = html.index("</body>")
    art = "<title>Grand Epistemic Network</title>\n<meta name=\"claude:viewport-fit-sides\" content=\"cover\">\n" + html[body_start:body_end]
    art = art.replace("</head><body>", "")
    out2 = os.path.join(HERE, "out", "artifact_explorer.html")
    with open(out2, "w", encoding="utf-8") as f:
        f.write(art)
    print("wrote", out2, len(art) // 1024, "kB")


if __name__ == "__main__":
    main()
