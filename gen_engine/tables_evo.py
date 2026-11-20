"""LaTeX tables for Part II (evolution), generated from out/evolution.json and data/gen_evolution_network.json."""
from __future__ import annotations
import json, os
from collections import Counter, defaultdict
from .tables import esc, w, TAB

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOUR = ("EM", "HEP", "GPT", "QRT")
PHASES = ("observe", "deficit", "hypothesize", "restructure", "predict", "falsify", "calibrate", "reduce")


def load():
    return json.load(open(os.path.join(HERE, "out", "evolution.json"))), json.load(open(os.path.join(HERE, "data", "gen_evolution_network.json")))


def tt(s):
    return "\\texttt{" + esc(s).replace("\\_", "\\_\\allowbreak{}") + "}"


def tab_evo_provenance(R):
    rows = []
    keys = sorted({k for b in FOUR for k in R["provenance"][b]})
    for b in FOUR:
        p = R["provenance"][b]
        node = ", ".join(f"{k.split(':')[1]} {v}" for k, v in sorted(p.items()) if k.startswith("node:"))
        route = ", ".join(f"{k.split(':')[1]} {v}" for k, v in sorted(p.items()) if k.startswith("route:"))
        rows.append(f"{b} & {esc(node)} & {esc(route)} \\\\")
    w("tab_evo_provenance.tex", "\\begin{tabular}{@{}lp{5.6cm}p{6.2cm}@{}}\\toprule\nBranch & Node years (provenance: count) & Route years (provenance: count) \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_evo_summary(R):
    rows = []
    for b in FOUR:
        p = R["branches"][b]; d = p["decomposition"]; c = p["curve"][-1]; dn = p["densification"]; pa = p["preferential"]
        lat = f"{d['latency_mean']:.1f} / {d['latency_median']} / {d['latency_max']}" if d["latency_mean"] is not None else "--"
        rows.append(f"{b} & {p['years'][0]}--{p['years'][1]} & {c['V']} & {c['S']}/{c['M']}/{c['O']} & {c['E']} & {d['n_closures']} & {100*d['closure_fraction']:.0f}\\% & {lat} & "
                    f"{d['mean_degree_at_arrival']:.2f} & {dn['alpha']:.2f} ({dn['r2']:.2f}) & {pa['ratio']:.2f} ({pa['n_closure']}) \\\\")
    w("tab_evo_summary.tex", "\\begin{tabular}{@{}llrrrrrlrll@{}}\\toprule\nBranch & Years & $V$ & S/M/O & $E$ & Closures & Frac. & Latency mean/med/max (y) & $\\bar d_{\\mathrm{arr}}$ & $\\alpha$ ($R^2$) & PA ratio ($n$) \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_evo_identity(R):
    rows = []
    for b in FOUR:
        i = R["branches"][b]["decomposition"]["identity"]
        rows.append(f"{b} & {i['sum_arrival_degree']} & {i['excess_multi_arrival']} & {i['closures']} & {i['check']} & {i['E']} & {'yes' if i['holds'] else 'no'} \\\\")
    w("tab_evo_identity.tex", "\\begin{tabular}{@{}lrrrrrl@{}}\\toprule\nBranch & $\\sum_v d_{\\mathrm{arr}}(v)$ & $\\sum_r (a(r)-1)^+$ & closures & $\\sum_v d_{\\mathrm{arr}} - \\sum_r (a(r)-1)^+ + \\text{closures}$ & $E$ & holds \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_evo_layer_half(R):
    rows = []
    for b in FOUR:
        h = R["branches"][b]["layer_half"]; c = R["branches"][b]["curve"][-1]
        order = sorted("SMO", key=lambda L: h[L])
        rows.append(f"{b} & {h['S']} & {h['M']} & {h['O']} & {'$<$'.join(order)} \\\\")
    w("tab_evo_layer_half.tex", "\\begin{tabular}{@{}lrrrl@{}}\\toprule\nBranch & S half-year & M half-year & O half-year & order \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_evo_first_polarity(R):
    rows = []
    for b in FOUR:
        fp = R["branches"][b]["first_edge_polarity"]
        cells = []
        for L in "SMO":
            tot = sum(fp[L].values())
            parts = sorted(fp[L].items(), key=lambda kv: -kv[1])
            cells.append(esc(", ".join(f"{k.replace('_', '-')} {v}" for k, v in parts)).replace("+", "+\\allowbreak{}") + f" ({tot})")
        rows.append(f"{b} & " + " & ".join(cells) + " \\\\")
    w("tab_evo_first_polarity.tex", "\\begin{tabular}{@{}l>{\\raggedright\\arraybackslash}p{3.6cm}>{\\raggedright\\arraybackslash}p{4.6cm}>{\\raggedright\\arraybackslash}p{4.2cm}@{}}\\toprule\nBranch & S nodes & M nodes & O nodes \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_evo_decades(R):
    rows = []
    for r in R["decade_table"]:
        ph = r["phases"]
        rows.append(f"{r['decade']}s & {r['branch']} & {r['nodes']} & {r['S']}/{r['M']}/{r['O']} & {r['routes']} & " + " & ".join(str(ph[p]) for p in PHASES) + " \\\\")
    head = "\\begin{longtable}{@{}llrlr" + "r" * len(PHASES) + "@{}}\\toprule\nDecade & Branch & $\\Delta V$ & S/M/O & $\\Delta E$ & " + " & ".join(p[:5] + "." if len(p) > 6 else p for p in PHASES) + " \\\\\\midrule\\endhead\n"
    w("tab_evo_decades.tex", head + "\n".join(rows) + "\n\\bottomrule\\end{longtable}\n")


def tab_evo_events(R, N, b):
    rows = []
    nodes = {n["uid"]: n for n in N["nodes"]}
    for r in R["branches"][b]["rows"]:
        ns = ", ".join(tt(x) for x in r["nodes"])
        es = ", ".join(tt(x) for x in r["edges"])
        rows.append(f"{r['year']} & {r['arrivals']} & {r['arrival_edges']} & {r['closure_edges']} & {ns} & {es} \\\\")
    w(f"tab_evo_events_{b}.tex", "\\begin{longtable}{@{}lrrrp{3.4cm}p{5.6cm}@{}}\\toprule\nYear & nodes & arr.\\ routes & closures & nodes added & routes added \\\\\\midrule\\endhead\n" + "\n".join(rows) + "\n\\bottomrule\\end{longtable}\n")


def tab_evo_witness(R):
    rows = []
    for x in R["branches"]["GPT"]["witness_effect"]["rows"]:
        rel = "same" if x["t_witness"] == x["t_effect"] else ("witness first" if x["t_witness"] < x["t_effect"] else "effect first")
        rows.append(f"{tt(x['witness'])} & {tt(x['effect'])} & {x['t_witness']} & {x['t_effect']} & {x['t_edge']} & {rel} \\\\")
    w("tab_evo_witness.tex", "\\begin{tabular}{@{}llrrrl@{}}\\toprule\nWitness & Effect & $t$(witness) & $t$(effect) & $t$(pair edge) & order \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_evo_explanation(R):
    rows = []
    for x in sorted(R["branches"]["GPT"]["explanation_lag"]["rows"], key=lambda r: r["t"]):
        rows.append(f"{tt(x['effect'])} & {x['t']} & {x['first_model_edge'] or '--'} & {x['lag_model'] if x['lag_model'] is not None else '--'} & {x['first_state_edge'] or '--'} & {x['lag_state'] if x['lag_state'] is not None else '--'} \\\\")
    w("tab_evo_explanation.tex", "\\begin{tabular}{@{}lrrrrr@{}}\\toprule\nEffect & $t$(effect) & first M$\\to$effect & lag (y) & first S$\\to$effect & lag (y) \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_evo_concepts(R):
    rows = []
    for c in R["concepts"]:
        ys = "; ".join(f"{b} {y}" + ("$^{p}$" if "project" in c["prov"].get(b, []) else "") for b, y in sorted(c["years"].items(), key=lambda kv: kv[1]))
        lag = c["lag_dated"] if c["lag_dated"] is not None else "--"
        rows.append(f"{tt(c['id'])} & {esc(c['label'])} & {esc(ys)} & {c['first_dated'] or '--'} & {lag} \\\\")
    w("tab_evo_concepts.tex", "\\begin{longtable}{@{}p{3.1cm}p{3.6cm}p{4.3cm}lr@{}}\\toprule\nConcept & Label & Year by branch & first & lag (y) \\\\\\midrule\\endhead\n" + "\n".join(rows) + "\n\\bottomrule\\end{longtable}\n")


def tab_evo_merged_phases(R):
    rows = []
    for r in R["merged_phases"]:
        if r["total"] == 0:
            continue
        rows.append(f"{r['decade']}s & " + " & ".join(str(r[p]) for p in PHASES) + f" & {r['total']} \\\\")
    tot = Counter()
    for r in R["merged_phases"]:
        for p in PHASES:
            tot[p] += r[p]
    rows.append("\\midrule total & " + " & ".join(str(tot[p]) for p in PHASES) + f" & {sum(tot.values())} \\\\")
    w("tab_evo_merged_phases.tex", "\\begin{tabular}{@{}l" + "r" * (len(PHASES) + 1) + "@{}}\\toprule\nDecade & " + " & ".join(PHASES) + " & total \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_evo_hep_removals(R, N):
    nodes = [n for n in N["nodes"] if n["branch"] == "HEP"]; routes = [r for r in N["routes"] if r["branch"] == "HEP"]
    rows = []
    for s in range(1, 13):
        an = [n["native_id"] for n in nodes if n["step_first"] == s]; rn = [n["native_id"] for n in nodes if n.get("removal_step") == s]
        ar = sum(1 for r in routes if r["step_first"] == s); rr = sum(1 for r in routes if r.get("removal_step") == s)
        rows.append(f"{s} & {len(an)} & {ar} & {len(rn)} & {rr} & {esc(', '.join(rn))} \\\\")
    w("tab_evo_hep_removals.tex", "\\begin{tabular}{@{}lrrrrp{6.2cm}@{}}\\toprule\nStep & nodes added & routes added & nodes removed & routes removed & nodes removed (native ids) \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_evo_rules_decade(R):
    rows = []
    for b in FOUR:
        rd = R["branches"][b]["rules_by_decade"]
        rules = sorted({r for d in rd.values() for r in d})
        for rl in rules:
            cells = [str(rd[d].get(rl, 0)) if rd[d].get(rl, 0) else "" for d in sorted(rd)]
            rows.append(f"{b} & {esc(rl)} & " + ", ".join(f"{d}s:\\,{rd[d][rl]}" for d in sorted(rd) if rd[d].get(rl)) + " \\\\")
    w("tab_evo_rules_decade.tex", "\\begin{longtable}{@{}llp{10cm}@{}}\\toprule\nBranch & Rule & firings by decade (decade:count) \\\\\\midrule\\endhead\n" + "\n".join(rows) + "\n\\bottomrule\\end{longtable}\n")


def tab_evo_hep_rules_year(R):
    rows = []
    for r in R["hep_rules_by_year"]:
        fired = ", ".join(f"R{k}" + ("" if v == "●" else "$^{\\circ}$") for k, v in sorted(r["rules"].items(), key=lambda kv: int(kv[0])))
        rows.append(f"{r['year']} & {r['step']} & {tt(r['id'])} & {fired or '--'} \\\\")
    w("tab_evo_hep_rules_year.tex", "\\begin{tabular}{@{}rrlp{7cm}@{}}\\toprule\nYear & Step & id & rules detected ($^{\\circ}$ = partial) \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_evo_census(R):
    rows = []
    for b in ("GPT", "QRT"):
        cs = R["branches"][b]["census"]
        pick = [c for c in cs if c["year"] % 10 == 0 or c is cs[-1]]
        # choose a few milestone years
        for c in cs:
            if c["year"] in (1990, 2000, 2005, 2010, 2015, 2020, 2026) or c is cs[-1]:
                rows.append(f"{b} & {c['year']} & {c['cells']} & {c['connected']} & {c['open']} & {100*c['connected']/c['cells']:.1f}\\% \\\\" if c["cells"] else f"{b} & {c['year']} & 0 & 0 & 0 & -- \\\\")
    w("tab_evo_census.tex", "\\begin{tabular}{@{}lrrrrr@{}}\\toprule\nBranch & Year & cells & connected & open & filled \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def main():
    R, N = load()
    tab_evo_provenance(R); tab_evo_summary(R); tab_evo_identity(R); tab_evo_layer_half(R); tab_evo_first_polarity(R); tab_evo_decades(R)
    tab_evo_events(R, N, "GPT"); tab_evo_events(R, N, "QRT"); tab_evo_witness(R); tab_evo_explanation(R); tab_evo_concepts(R); tab_evo_merged_phases(R)
    tab_evo_hep_removals(R, N); tab_evo_rules_decade(R); tab_evo_hep_rules_year(R); tab_evo_census(R)
    print("evolution tables written")


if __name__ == "__main__":
    main()
