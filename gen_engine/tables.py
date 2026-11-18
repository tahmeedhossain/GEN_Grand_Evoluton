"""LaTeX tables for the thesis, generated from out/results.json."""
from __future__ import annotations
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB = os.path.join(HERE, "thesis", "tables"); os.makedirs(TAB, exist_ok=True)


def esc(s) -> str:
    s = str(s)
    for a, b in (("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("#", "\\#"), ("_", "\\_"), ("{", "\\{"), ("}", "\\}"), ("^", "\\^{}"), ("~", "\\~{}")):
        s = s.replace(a, b)
    return s


def w(name, text):
    with open(os.path.join(TAB, name), "w", encoding="utf-8") as f:
        f.write(text)


def tab_instances(R):
    rows = []
    meta = {"UP": ("GEN\\_Learning", "v2", "D", "paragraph (620)"), "EM": ("GEN\\_epistemic\\_evolution", "v3.1", "D", "paragraph (78)"),
            "LG": ("GEN\\_LocGlob\\_Flow", "v6.1", "D", "version"), "HEP": ("GEN\\_HEP", "v1.2", "H", "step (12)"),
            "GPT": ("GEN\\_GPT\\_Level", "v2.6", "E", "release"), "QRT": ("GEN\\_QRT\\_Level", "v1.2", "E", "release")}
    for b in ("UP", "EM", "LG", "HEP", "GPT", "QRT"):
        c = R["counts"]["per_branch"][b]; m = meta[b]
        rows.append(f"{b} & {m[0]} & {m[1]} & {m[2]} & {m[3]} & {c['nodes']} & {c['S']} & {c['M']} & {c['O']} & {c['routes']} & {c['AND']} & {c['or_targets']} \\\\")
    w("tab_instances.tex", "\\begin{tabular}{@{}lllllrrrrrrr@{}}\\toprule\nBranch & Repository & Version & Type & Time axis & Nodes & S & M & O & Routes & AND & OR targets \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_signatures(R):
    L = ["S", "M", "O"]; rows = []
    for b in ("UP", "EM", "LG", "HEP", "GPT", "QRT"):
        pm = R["signatures"][b]["pair_matrix"]
        cells = [str(pm.get(f"{a}->{t}", 0)) for a in L for t in L]
        rows.append(f"{b} & " + " & ".join(cells) + " \\\\")
    rec = R["signatures"]["HEP"]["record_level_final_step"]
    rows.append("HEP (records) & " + " & ".join([ "0", str(rec.get("S->M", 0) + rec.get("S->M (AND routes)", 0)), "0", str(rec.get("M->S", 0)), str(rec.get("M->M", 0)), str(rec.get("M->O", 0)), "0", "0", str(R['signatures']['HEP']['pair_matrix'].get('O->O', 0))]) + " \\\\")
    head = "\\begin{tabular}{@{}l" + "r" * 9 + "@{}}\\toprule\n & \\multicolumn{3}{c}{S $\\to$} & \\multicolumn{3}{c}{M $\\to$} & \\multicolumn{3}{c}{O $\\to$} \\\\\n & S & M & O & S & M & O & S & M & O \\\\\\midrule\n"
    w("tab_signatures.tex", head + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_rulematrix(R):
    h = R["hep"]; auto = {int(k): v for k, v in h["auto_matrix"].items()}; hand = {int(k): v for k, v in h["hand_matrix"].items()}
    names = {1: "One-particle QM", 2: "Wigner's classification", 3: "Production anomaly", 4: "Fields on Fock space", 5: "QED vertex", 6: "Fermi's contact term",
             7: "Muon and universality", 8: "Parity violation, V$-$A", 9: "W, Z and gauge theory", 10: "Higgs sector", 11: "Neutrino-mass frontier", 12: "SM as clusters"}
    rows = []
    for k in range(1, 13):
        cells = []
        for r in range(1, 11):
            a = auto.get(k, {}).get(str(r), auto.get(k, {}).get(r, "")); hv = hand[k].get(str(r), hand[k].get(r, ""))
            sym = {"●": "$\\bullet$", "○": "$\\circ$", "": ""}[a]
            if a != hv:
                sym = "\\textbf{" + (sym if sym else "--") + "}$^{" + ({"●": "\\bullet", "○": "\\circ", "": "-"}[hv]) + "}$"
            cells.append(sym)
        rows.append(f"{k} {names[k]} & " + " & ".join(cells) + " \\\\")
    w("tab_rulematrix.tex", "\\begin{tabular}{@{}l" + "c" * 10 + "@{}}\\toprule\nStep & R1 & R2 & R3 & R4 & R5 & R6 & R7 & R8 & R9 & R10 \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_oplog(R):
    rows = []
    for d in R["hep"]["diffs"]:
        first = True
        for op, layer, desc in d["ops"]:
            rows.append(f"{d['index'] if first else ''} & \\texttt{{{op}}} & {esc(layer)} & {esc(desc)} \\\\")
            first = False
        rows.append("\\addlinespace[2pt]")
    w("tab_oplog.tex", "\\begin{longtable}{@{}p{0.6cm}p{1.9cm}p{1.3cm}p{10.5cm}@{}}\\toprule\nStep & Operation & Layer & Decomposition read off the data \\\\\\midrule\\endhead\n" + "\n".join(rows) + "\n\\bottomrule\\end{longtable}\n")


def tab_steps(R):
    rows = []
    cum = {c["step"]: c for c in R["hep"]["cumulative"]}
    for s in R["hep"]["steps"]:
        c = cum[s["index"]]
        rows.append(f"{s['index']} & {esc(s['id'])} & {s['S']} & {s['M']} & {s['O']} & {c['O_cumulative']} & {s['records']} & {s['AND']} & {s['eff']} & {s['fund']} & {s['cluster']} & {s['calibrations']} & {len(s['unexplained'])} & {len(c['unexplained_cumulative'])} \\\\")
    w("tab_steps.tex", "{\\setlength{\\tabcolsep}{3.5pt}\\begin{tabular}{@{}rlrrrrrrrrrrrr@{}}\\toprule\nStep & id & S & M & O$_{\\rm shown}$ & O$_{\\rm cum}$ & records & AND & eff & fund & cl. & F & def.$_{\\rm shown}$ & def.$_{\\rm cum}$ \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}}\n")


def tab_predictive(R):
    rows = []
    for k, v in R["hep"]["predictive_content"].items():
        rows.append(f"{esc(k)} & {v['n_pred']} & {v['n_fit']} & {v['n_frame']} & {esc(', '.join(v['pred']))} & {esc(', '.join(v['fit']))} \\\\")
    w("tab_predictive.tex", "\\begin{tabular}{@{}lrrrp{6.2cm}p{2.6cm}@{}}\\toprule\nNode & predictions & calibrations & framework & predicted observables & calibrating observables \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_failed(R):
    rows = []
    for b in ("EM", "UP"):
        for x in R["typeD"][b]["failed"]["rows"]:
            rows.append(f"{b} & {esc(x['failed'])} & {esc(x['target'])} & {x['t_failed']} & {esc(x['resolved_by'] or '--')} & {x['t_resolved'] if x['t_resolved'] is not None else '--'} & {x['distance'] if x['distance'] is not None else '--'} & {esc(x.get('resolver_kind') or '--')} & {esc(x.get('earlier') or '--')} ({x['t_earlier'] if x.get('t_earlier') is not None else '--'}) \\\\")
    w("tab_failed.tex", "\\begin{tabular}{@{}lllllllll@{}}\\toprule\nBranch & failed route & target & $t$ & forward resolver & $t'$ & $t'-t$ & resolver kind & preceding route ($t$) \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_witness(R):
    pw = R["typeE"]["GPT"]["witness_census"]["per_witness"]
    rows = [f"{esc(w_)} & {v['settled']} & {v['fires']} & {v['hidden']} & {v['blind']} & {v['uncharted']} \\\\" for w_, v in pw.items()]
    w("tab_witness.tex", "\\begin{tabular}{@{}lrrrrr@{}}\\toprule\nWitness & settled & fires & hidden & blind & uncharted \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_pairs(R):
    bl = R["typeE"]["GPT"]["pair_census"]["by_native_layer_pair"]
    rows = []
    for k, v in bl.items():
        a, b = k.split("|")
        rows.append(f"{esc(a)} & {esc(b)} & {v['pairs']} & {v['connected']} & {100*v['connected']/v['pairs']:.1f} \\\\")
    w("tab_pairs.tex", "\\begin{longtable}{@{}llrrr@{}}\\toprule\nlayer & layer & pairs & connected & \\% \\\\\\midrule\\endhead\n" + "\n".join(rows) + "\n\\bottomrule\\end{longtable}\n")


def tab_concepts(R):
    rows = []
    for c in R["concepts"]:
        mem = "; ".join(f"{b}: {', '.join(sorted(m.split(':')[1] for m in c['members'] if m.startswith(b + ':')))}" for b in c["roles"])
        roles = ", ".join(f"{b}={'/'.join(r)}" for b, r in c["roles"].items())
        flag = "$\\ast$" if c["flip"] else ""
        rows.append(f"\\texttt{{{esc(c['id']).replace(chr(92)+'_', chr(92)+'_'+chr(92)+'allowbreak{{}}')}}}{flag} & {esc(c['label'])} & {esc(mem)} & {esc(roles)} \\\\")
    w("tab_concepts.tex", "\\begin{longtable}{@{}p{3.1cm}p{3.6cm}p{5.0cm}p{2.9cm}@{}}\\toprule\nConcept & Label & Members (branch: native ids) & Roles \\\\\\midrule\\endhead\n" + "\n".join(rows) + "\n\\bottomrule\\end{longtable}\n")


def tab_flips(R):
    rows = []
    for c in R["concepts"]:
        if c["flip"]:
            roles = ", ".join(f"{b}: {'/'.join(r)}" for b, r in c["roles"].items())
            rows.append(f"{esc(c['label'])} & {esc(roles)} & {esc(c['note'].replace('ROLE FLIP: ', ''))} \\\\")
    w("tab_flips.tex", "\\begin{longtable}{@{}p{3.2cm}p{3.0cm}p{8.4cm}@{}}\\toprule\nConcept & Role per branch & Why the role differs \\\\\\midrule\\endhead\n" + "\n".join(rows) + "\n\\bottomrule\\end{longtable}\n")


def tab_ops(R):
    rows = [f"\\texttt{{{esc(k)}}} & {esc(v[0])} & {esc(v[1])} & {esc(v[2])} & {esc(v[3])} \\\\" for k, v in R["ops"].items()]
    w("tab_ops.tex", "\\begin{longtable}{@{}p{1.7cm}p{2.2cm}p{2.3cm}p{3.0cm}p{5.4cm}@{}}\\toprule\nOperation & layer & $\\Delta$ nodes & $\\Delta$ routes & meaning \\\\\\midrule\\endhead\n" + "\n".join(rows) + "\n\\bottomrule\\end{longtable}\n")


def tab_qrt_matrix(R):
    q = R["typeE"]["QRT"]["conversion_census"]; th = q["theories"]
    rows = []
    for a in th:
        cells = []
        for b in th:
            v = q["matrix"][a][b]
            cells.append("--" if a == b else {"C": "$\\blacksquare$", "s": "$\\square$", "x": "$\\cdot$", "": ""}[v])
        rows.append(f"{a} & " + " & ".join(cells) + " \\\\")
    w("tab_qrt_matrix.tex", "\\begin{tabular}{@{}l" + "c" * len(th) + "@{}}\\toprule\nfrom $\\backslash$ to & " + " & ".join(th) + " \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_order(R):
    oc = R["typeD"]["order_EM_vs_UP"]
    rows = [f"{esc(p['concept'])} & {p['t_EM']} & {p['t_UP']} \\\\" for p in sorted(oc["pairs"], key=lambda p: p["t_EM"])]
    w("tab_order.tex", "\\begin{longtable}{@{}lrr@{}}\\toprule\nConcept & EM paragraph & UP paragraph \\\\\\midrule\\endhead\n" + "\n".join(rows) + "\n\\bottomrule\\end{longtable}\n")


def tab_chapters(R):
    rows = [f"{r['vol']}.{r['ch']} & {esc(r['title'])} & {r['new_nodes']} & {r['routes']} & {r['carried_in']} & {r['carried_in_by_layer']['S']}/{r['carried_in_by_layer']['M']}/{r['carried_in_by_layer']['O']} \\\\" for r in R["typeD"]["UP"]["chapters"]]
    w("tab_chapters.tex", "\\begin{longtable}{@{}llrrrl@{}}\\toprule\nChapter & Title & new nodes & routes & carried in & S/M/O \\\\\\midrule\\endhead\n" + "\n".join(rows) + "\n\\bottomrule\\end{longtable}\n")


def tab_drivers(R):
    lab = {"found": "foundation", "sym": "symmetry (theory-internal)", "anom": "anomaly: observed, unexplained", "resp": "model response to the anomaly", "pred": "prediction (theory-internal)", "syn": "synthesis"}
    rows = []
    for d in R["hep"]["driver_consistency"]:
        rows.append(f"{d['step']} & {esc(d['id'])} & {esc(lab.get(d['driver'], d['driver']))} & {'yes' if d['deficit_before'] else 'no'} & {esc(d.get('r2_form') or '--')} \\\\")
    w("tab_drivers.tex", "\\begin{tabular}{@{}rlllp{4cm}@{}}\\toprule\nStep & id & recorded driver & deficit before the step & R2 form detected \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def tab_sector_term(R):
    h = R["hep"]["sector_term_census"]; M = h["matrix"]; terms = list(next(iter(M.values())).keys())
    rows = [f"{esc(s)} & " + " & ".join("$\\blacksquare$" if M[s][t] else "" for t in terms) + " \\\\" for s in M]
    w("tab_sector_term.tex", "\\begin{tabular}{@{}l" + "c" * len(terms) + "@{}}\\toprule\nsector & " + " & ".join(esc(t) for t in terms) + " \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")


def main():
    R = json.load(open(os.path.join(HERE, "out", "results.json")))
    for f in (tab_instances, tab_signatures, tab_rulematrix, tab_oplog, tab_steps, tab_predictive, tab_failed, tab_witness, tab_pairs, tab_concepts, tab_flips, tab_ops, tab_qrt_matrix, tab_order, tab_chapters, tab_sector_term, tab_drivers):
        f(R)
    print("tables written to", TAB)


if __name__ == "__main__":
    main()
