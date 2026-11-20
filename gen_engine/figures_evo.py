"""Figures for Part II of the thesis (evolution), generated from out/evolution.json and data/gen_evolution_network.json."""
from __future__ import annotations
import json, os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(HERE, "figures"); os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
                     "legend.fontsize": 7, "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42})
COL = {"S": "#2a6f97", "M": "#c05c2a", "O": "#3f7d4e", "neutral": "#555555", "light": "#dddddd"}
BCOL = {"EM": "#6a3d9a", "HEP": "#b15928", "GPT": "#d62728", "QRT": "#1f78b4"}
PCOL = {"structural": "#3f7d4e", "possibility": "#2a6f97", "no_go": "#c0392b", "open": "#999999"}
FOUR = ("EM", "HEP", "GPT", "QRT")
BT = {"EM": "EM reader (D)", "HEP": "Standard Model history (H), union of steps", "GPT": "Nonclassicality network (E)", "QRT": "Resource-theory network (E)"}
PHASES = ("observe", "deficit", "hypothesize", "restructure", "predict", "falsify", "calibrate", "reduce")


def load():
    R = json.load(open(os.path.join(HERE, "out", "evolution.json")))
    N = json.load(open(os.path.join(HERE, "data", "gen_evolution_network.json")))
    return R, N


def fig_evo_branches(R, N):
    """Cumulative node counts by layer (stacked) and route count, per branch, on the calendar axis; HEP also shows the present count."""
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 5.6))
    for ax, b in zip(axes.flat, FOUR):
        cur = R["branches"][b]["curve"]; t = [c["year"] for c in cur]
        S = np.array([c["S"] for c in cur]); M = np.array([c["M"] for c in cur]); O = np.array([c["O"] for c in cur])
        ax.fill_between(t, 0, S, color=COL["S"], alpha=0.55, step="post", label="S (states)")
        ax.fill_between(t, S, S + M, color=COL["M"], alpha=0.55, step="post", label="M (models)")
        ax.fill_between(t, S + M, S + M + O, color=COL["O"], alpha=0.55, step="post", label="O (observables)")
        ax.step(t, [c["E"] for c in cur], where="post", color="#222", lw=1.2, label="routes E")
        # closures as ticks
        cl = Counter(c["year"] for c in R["branches"][b]["decomposition"]["closures"] if "year" in c) if False else Counter()
        for row in R["branches"][b]["rows"]:
            if row["closure_edges"]:
                ax.plot([row["year"]], [0], marker="|", color="#c0392b", ms=6, mew=1.2)
        if b == "HEP":
            # present count: ever-added minus removed before T (removal placed at the start year of the removing step)
            nodes = [n for n in N["nodes"] if n["branch"] == "HEP"]
            pres = [sum(1 for n in nodes if n["year"] <= T and not (n.get("removal_year") and n["removal_year"] < T)) for T in t]
            ax.step(t, pres, where="post", color="#000", ls=":", lw=1.0, label="nodes present (after removals)")
        ax.set_title(f"{BT[b]} — V={cur[-1]['V']}, E={cur[-1]['E']}, {t[0]}–{t[-1]}")
        ax.set_xlabel("year"); ax.set_ylabel("cumulative count")
        ax.legend(frameon=False, loc="upper left")
    fig.text(0.5, -0.01, "red ticks on the axis: years with closure routes (routes between nodes that were already present)", ha="center", fontsize=7, color="#555")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_evo_branches.pdf")); plt.close(fig)


def fig_evo_polarity(R, N):
    fig, axes = plt.subplots(1, 4, figsize=(10.5, 2.5))
    for ax, b in zip(axes, FOUR):
        cur = R["branches"][b]["curve"]; t = [c["year"] for c in cur]
        for pol in ("structural", "possibility", "no_go", "open"):
            ys = [c[pol] for c in cur]
            if max(ys) > 0:
                ax.step(t, ys, where="post", color=PCOL[pol], lw=1.2, label=pol.replace("_", "-"))
        ax.set_title(b + " — routes by polarity"); ax.set_xlabel("year")
        ax.legend(frameon=False, loc="upper left")
    axes[0].set_ylabel("cumulative routes")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_evo_polarity.pdf")); plt.close(fig)


def fig_evo_merged(R, N):
    mc = R["merged_curve"]; t = [r["year"] for r in mc]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.2))
    ax = axes[0]
    base = np.zeros(len(t))
    for b in FOUR:
        ys = np.array([r[b] for r in mc])
        ax.fill_between(t, base, base + ys, color=BCOL[b], alpha=0.6, step="post", label=f"{b} nodes")
        base = base + ys
    ax.step(t, [r["V_collapsed"] for r in mc], where="post", color="#000", lw=1.2, ls="--", label="V after collapsing shared concepts")
    ax.step(t, [r["glue"] for r in mc], where="post", color="#000", lw=0.8, ls=":", label="glue identifications")
    ax.set_title("Merged four-branch network: nodes by branch"); ax.set_xlabel("year"); ax.set_ylabel("nodes")
    ax.legend(frameon=False, loc="upper left")
    ax = axes[1]
    base = np.zeros(len(t))
    for b in FOUR:
        ys = np.array([r[b + "_E"] for r in mc])
        ax.fill_between(t, base, base + ys, color=BCOL[b], alpha=0.6, step="post", label=f"{b} routes")
        base = base + ys
    ax.set_title("Merged four-branch network: routes by branch"); ax.set_xlabel("year"); ax.set_ylabel("routes")
    ax.legend(frameon=False, loc="upper left")
    for ax in axes:
        ax.set_xlim(1680, 2030)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_evo_merged.pdf")); plt.close(fig)
    # zoom 1890-2026
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.2))
    sel = [i for i, y in enumerate(t) if y >= 1890]
    tz = [t[i] for i in sel]
    for ax, key, lab in zip(axes, ("", "_E"), ("nodes", "routes")):
        base = np.zeros(len(tz))
        for b in FOUR:
            ys = np.array([mc[i][b + key] for i in sel])
            ax.fill_between(tz, base, base + ys, color=BCOL[b], alpha=0.6, step="post", label=f"{b} {lab}")
            base = base + ys
        if key == "":
            ax.step(tz, [mc[i]["V_collapsed"] for i in sel], where="post", color="#000", lw=1.2, ls="--", label="V collapsed")
            ax.step(tz, [mc[i]["glue"] for i in sel], where="post", color="#000", lw=0.8, ls=":", label="glue")
        ax.set_title(f"Merged network since 1890: {lab} by branch"); ax.set_xlabel("year"); ax.set_ylabel(lab)
        ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_evo_merged_zoom.pdf")); plt.close(fig)


def fig_evo_concepts(R, N):
    ct = R["concepts"]
    fig, ax = plt.subplots(figsize=(10.5, 0.16 * len(ct) + 1.2))
    for i, c in enumerate(ct):
        ys = c["years"]
        lo, hi = min(ys.values()), max(ys.values())
        ax.plot([lo, hi], [i, i], color="#bbb", lw=1.0, zorder=1)
        for b, y in ys.items():
            prov = c["prov"].get(b, [])
            mk = "x" if "project" in prov else "o"
            ax.scatter([y], [i], color=BCOL[b], s=14, marker=mk, zorder=2)
        ax.text(1680, i, c["label"][:38], fontsize=5.5, va="center", ha="left")
    ax.set_yticks([]); ax.set_xlim(1675, 2032); ax.set_ylim(-1, len(ct)); ax.invert_yaxis()
    ax.set_xlabel("year of first appearance in each branch (x = project-dated member, no cited source)")
    from matplotlib.lines import Line2D
    ax.legend([Line2D([0], [0], marker="o", color=BCOL[b], ls="") for b in FOUR], list(FOUR), frameon=False, loc="lower right", ncol=4)
    ax.set_title(f"{len(ct)} concepts shared between two or more of the four branches, by year of appearance in each branch")
    fig.savefig(os.path.join(FIG, "fig_evo_concepts.pdf")); plt.close(fig)


def fig_evo_phases(R, N):
    rows = [r for r in R["merged_phases"] if r["total"] > 0]
    decs = [r["decade"] for r in rows]
    M = np.array([[r[p] for p in PHASES] for r in rows], dtype=float)
    frac = M / M.sum(axis=1, keepdims=True)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), gridspec_kw={"width_ratios": [1.6, 1]})
    ax = axes[0]
    im = ax.imshow(frac.T, aspect="auto", cmap="Blues", vmin=0, vmax=0.7)
    ax.set_yticks(range(len(PHASES))); ax.set_yticklabels(PHASES)
    ax.set_xticks(range(len(decs))); ax.set_xticklabels([str(d) for d in decs], rotation=90, fontsize=6)
    for i in range(len(decs)):
        for j in range(len(PHASES)):
            if M[i, j] > 0:
                ax.text(i, j, str(int(M[i, j])), ha="center", va="center", fontsize=5, color="#000" if frac[i, j] < 0.4 else "#fff")
    ax.set_title("Method phases per decade, all four branches (cell = count; shade = fraction of the decade)")
    ax.set_xlabel("decade")
    # per-branch phase totals
    ax = axes[1]
    tot = {b: Counter() for b in FOUR}
    for row in R["decade_table"]:
        for p in PHASES:
            tot[row["branch"]][p] += row["phases"][p]
    # node phases
    for n in N["nodes"]:
        tot[n["branch"]][{"O": "observe", "M": "hypothesize", "S": "restructure"}[n["layer"]]] += 1
    x = np.arange(len(PHASES)); wdt = 0.2
    for k, b in enumerate(FOUR):
        s = sum(tot[b].values())
        ax.bar(x + (k - 1.5) * wdt, [tot[b][p] / s for p in PHASES], width=wdt, color=BCOL[b], label=b)
    ax.set_xticks(x); ax.set_xticklabels(PHASES, rotation=45, ha="right"); ax.set_ylabel("fraction of the branch's items")
    ax.set_title("Phase profile of each branch"); ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_evo_phases.pdf")); plt.close(fig)


def fig_evo_latency(R, N):
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 2.4))
    for ax, b in zip(axes, ("GPT", "QRT", "EM")):
        lat = [c["latency"] for c in R["branches"][b]["decomposition"]["closures"]]
        if not lat:
            continue
        ax.hist(lat, bins=range(0, max(lat) + 6, 5), color=BCOL[b], alpha=0.8)
        d = R["branches"][b]["decomposition"]
        ax.set_title(f"{b}: {d['n_closures']} closures, mean {d['latency_mean']:.1f} y, median {d['latency_median']} y, max {d['latency_max']} y")
        ax.set_xlabel("closure latency (years after the later endpoint)"); ax.set_ylabel("closure routes")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_evo_latency.pdf")); plt.close(fig)


def fig_evo_densification(R, N):
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.2))
    ax = axes[0]
    for b in FOUR:
        cur = R["branches"][b]["curve"]
        pts = [(c["V"], c["E"]) for c in cur if c["V"] >= 10 and c["E"] >= 1]
        d = R["branches"][b]["densification"]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "o", ms=2.5, color=BCOL[b], alpha=0.7,
                label=f"{b}: α={d['alpha']:.2f}, R²={d['r2']:.2f}, n={d['n']}")
        if d["alpha"]:
            xs = np.linspace(min(p[0] for p in pts), max(p[0] for p in pts), 50)
            ax.plot(xs, np.exp(d["intercept"]) * xs ** d["alpha"], color=BCOL[b], lw=0.8)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("V(T) (nodes present by year T)"); ax.set_ylabel("E(T) (routes by year T)")
    ax.set_title("Densification: E ∝ V^α on the year filtration (V ≥ 10)"); ax.legend(frameon=False, loc="upper left")
    ax = axes[1]
    for k, b in enumerate(FOUR):
        da = R["branches"][b]["decomposition"]["degree_at_arrival"]
        ks = sorted(int(x) for x in da)
        tot = sum(da.values())
        ax.plot(ks, [da[str(x)] / tot for x in ks], "-o", ms=3, color=BCOL[b], label=f"{b} (mean {R['branches'][b]['decomposition']['mean_degree_at_arrival']:.2f})")
    ax.set_xlabel("degree at arrival (routes dated the node's own year)"); ax.set_ylabel("fraction of nodes"); ax.set_title("Degree at arrival")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_evo_densification.pdf")); plt.close(fig)


def fig_evo_hep_rules(R, N):
    rows = R["hep_rules_by_year"]
    rules = [str(i) for i in range(1, 11)]
    fig, ax = plt.subplots(figsize=(10.5, 2.8))
    for j, row in enumerate(rows):
        for i, rl in enumerate(rules):
            mark = row["rules"].get(rl)
            if mark == "●":
                ax.scatter([j], [i], s=28, color="#222", zorder=3)
            elif mark == "○":
                ax.scatter([j], [i], s=28, facecolors="none", edgecolors="#222", zorder=3)
    ax.set_xticks(range(len(rows))); ax.set_xticklabels([f"{r['year']}\n{r['id']} (step {r['step']})" for r in rows], fontsize=6)
    ax.set_yticks(range(len(rules))); ax.set_yticklabels([f"R{r}" for r in rules]); ax.invert_yaxis()
    ax.set_title("Standard Model history: automatically detected rule firings, steps ordered by start year (● fired, ○ partial)")
    ax.grid(True, lw=0.3, color="#ddd")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_evo_hep_rules.pdf")); plt.close(fig)


def fig_evo_census(R, N):
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 2.8))
    for ax, b in zip(axes, ("GPT", "QRT")):
        cs = R["branches"][b]["census"]; t = [c["year"] for c in cs]
        ax.step(t, [c["cells"] for c in cs], where="post", color="#999", label="cells (designated layer pairs among present nodes)")
        ax.step(t, [c["connected"] for c in cs], where="post", color=BCOL[b], label="connected cells")
        ax.step(t, [c["open"] for c in cs], where="post", color="#c0392b", ls="--", label="open cells")
        ax.set_title(f"{b}: pair census on the year axis"); ax.set_xlabel("year"); ax.set_ylabel("cells")
        ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_evo_census.pdf")); plt.close(fig)


def fig_evo_hep_removals(R, N):
    nodes = [n for n in N["nodes"] if n["branch"] == "HEP"]; routes = [r for r in N["routes"] if r["branch"] == "HEP"]
    steps = list(range(1, 13))
    fig, ax = plt.subplots(figsize=(10.5, 2.6))
    added_n = [sum(1 for n in nodes if n["step_first"] == s) for s in steps]
    rem_n = [sum(1 for n in nodes if n.get("removal_step") == s) for s in steps]
    added_r = [sum(1 for r in routes if r["step_first"] == s) for s in steps]
    rem_r = [sum(1 for r in routes if r.get("removal_step") == s) for s in steps]
    x = np.arange(len(steps)); wdt = 0.2
    ax.bar(x - 1.5 * wdt, added_n, wdt, color=COL["S"], label="nodes added")
    ax.bar(x - 0.5 * wdt, [-v for v in rem_n], wdt, color=COL["S"], alpha=0.45, label="nodes removed")
    ax.bar(x + 0.5 * wdt, added_r, wdt, color="#222", label="routes added")
    ax.bar(x + 1.5 * wdt, [-v for v in rem_r], wdt, color="#222", alpha=0.35, label="routes removed")
    ax.axhline(0, color="#000", lw=0.6)
    ax.set_xticks(x); ax.set_xticklabels([f"{s}" for s in steps]); ax.set_xlabel("step of the Standard Model history (thematic order of the source)")
    ax.set_ylabel("count"); ax.set_title("HEP: the only non-monotone branch — additions (up) and removals (down) per step")
    ax.legend(frameon=False, ncol=4)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_evo_hep_removals.pdf")); plt.close(fig)


def fig_evo_lanes(R, N):
    """Four lanes x three layers: every node as a dot at its year; glue chords for shared concepts (drawn between lanes)."""
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    lane_y = {"EM": 3, "HEP": 2, "GPT": 1, "QRT": 0}; off = {"S": 0.25, "M": 0.0, "O": -0.25}
    rng = np.random.default_rng(1)
    pos = {}
    for n in N["nodes"]:
        y = lane_y[n["branch"]] + off[n["layer"]] + rng.uniform(-0.07, 0.07)
        pos[n["uid"]] = (n["year"], y)
        ax.scatter([n["year"]], [y], s=6, color=COL[n["layer"]], alpha=0.8, zorder=3, marker="x" if n.get("removed") else "o")
    # glue chords
    members = defaultdict(list)
    for n in N["nodes"]:
        if n.get("concept"):
            members[n["concept"]].append(n["uid"])
    for cid, us in members.items():
        us = sorted(us, key=lambda u: pos[u][0])
        for a, b in zip(us, us[1:]):
            (x1, y1), (x2, y2) = pos[a], pos[b]
            if a.split(":")[0] != b.split(":")[0]:
                ax.plot([x1, x2], [y1, y2], color="#888", lw=0.4, alpha=0.5, zorder=1)
    for b, y in lane_y.items():
        ax.text(1678, y, b, fontsize=9, va="center", ha="right", color=BCOL[b], fontweight="bold")
        ax.axhspan(y - 0.4, y + 0.4, color=BCOL[b], alpha=0.05)
    ax.set_yticks([3.25, 3, 2.75, 2.25, 2, 1.75, 1.25, 1, 0.75, 0.25, 0, -0.25]); ax.set_yticklabels(["S", "M", "O"] * 4, fontsize=6)
    ax.set_xlim(1670, 2032); ax.set_xlabel("year"); ax.set_title("The four-branch evolutionary network: nodes by year, lane = branch, row = layer; grey chords = shared concepts (glue); × = removed in HEP")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_evo_lanes.pdf")); plt.close(fig)


def fig_evo_events(R, N):
    """GPT and QRT: per-year arrivals (nodes) and routes split into arrival vs closure, with polarity."""
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 4.8), sharex=True)
    for ax, b in zip(axes, ("GPT", "QRT")):
        rows = R["branches"][b]["rows"]; t = [r["year"] for r in rows]
        ax.bar(t, [r["arrivals"] for r in rows], color="#bbb", width=0.8, label="nodes arriving")
        ax.bar(t, [r["arrival_edges"] for r in rows], bottom=0, color=BCOL[b], alpha=0.5, width=0.5, label="routes with an arriving endpoint")
        ax.bar(t, [r["closure_edges"] for r in rows], bottom=[r["arrival_edges"] for r in rows], color="#c0392b", alpha=0.7, width=0.5, label="closure routes")
        ax.set_title(f"{b}: yearly events"); ax.set_ylabel("count"); ax.legend(frameon=False, loc="upper left")
    axes[1].set_xlabel("year"); axes[1].set_xlim(1930, 2028)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_evo_events.pdf")); plt.close(fig)


def main():
    R, N = load()
    for f in (fig_evo_branches, fig_evo_polarity, fig_evo_merged, fig_evo_concepts, fig_evo_phases, fig_evo_latency, fig_evo_densification,
              fig_evo_hep_rules, fig_evo_census, fig_evo_hep_removals, fig_evo_lanes, fig_evo_events):
        f(R, N)
    print("evolution figures written")


if __name__ == "__main__":
    main()
