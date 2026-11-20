"""Figures for the thesis, generated from out/results.json."""
from __future__ import annotations
import json, os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(HERE, "figures"); os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
                     "legend.fontsize": 7, "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42})
COL = {"S": "#2a6f97", "M": "#c05c2a", "O": "#3f7d4e", "neutral": "#555555", "light": "#dddddd"}
BRANCH_ORDER = ["UP", "EM", "LG", "HEP", "GPT", "QRT"]
BRANCH_TITLE = {"UP": "University Physics reader (D)", "EM": "EM history reader (D)", "LG": "LocGlob energy flow (D)",
                "HEP": "Standard Model history (H)", "GPT": "Nonclassicality network (E)", "QRT": "Resource-theory network (E)"}
BRANCH_SHORT = {"UP": "UP (D)", "EM": "EM (D)", "LG": "LG (D)", "HEP": "HEP (H)", "GPT": "GPT (E)", "QRT": "QRT (E)"}


def load():
    return json.load(open(os.path.join(HERE, "out", "results.json")))


def fig_signatures(R):
    fig, axes = plt.subplots(1, 6, figsize=(10.5, 2.3))
    L = ["S", "M", "O"]
    for ax, b in zip(axes, BRANCH_ORDER):
        pm = R["signatures"][b]["pair_matrix"]
        M = np.zeros((3, 3))
        for k, v in pm.items():
            i, j = L.index(k[0]), L.index(k[-1]); M[i, j] = v
        if b == "HEP":
            # record level: generic layer edges counted once, AND routes once, plus the observable-family edges
            rec = R["signatures"]["HEP"]["record_level_final_step"]
            M = np.zeros((3, 3))
            M[0, 1] = rec.get("S->M", 0) + rec.get("S->M (AND routes)", 0); M[1, 2] = rec.get("M->O", 0); M[1, 0] = rec.get("M->S", 0); M[1, 1] = rec.get("M->M", 0)
            M[2, 2] = pm.get("O->O", 0)
        tot = M.sum()
        im = ax.imshow(M / tot if tot else M, cmap="Blues", vmin=0, vmax=0.5)
        for i in range(3):
            for j in range(3):
                if M[i, j] > 0:
                    ax.text(j, i, f"{int(M[i, j])}", ha="center", va="center", fontsize=7, color="black" if M[i, j] / tot < 0.3 else "white")
        ax.set_xticks(range(3)); ax.set_xticklabels(L); ax.set_yticks(range(3)); ax.set_yticklabels(L)
        ax.set_xlabel("target layer"); ax.set_title(BRANCH_SHORT[b], fontsize=8)
        if b == BRANCH_ORDER[0]:
            ax.set_ylabel("input layer")
    fig.savefig(os.path.join(FIG, "fig_signatures.pdf"))
    plt.close(fig)


def fig_hep_trajectories(R):
    h = R["hep"]; T = h["trajectories"]; cum = h["cumulative"]
    x = list(range(1, 13))
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 2.6))
    ax = axes[0]
    ax.plot(x, T["S"], "-o", color=COL["S"], label="state nodes", ms=3)
    ax.plot(x, T["M"], "-s", color=COL["M"], label="model nodes", ms=3)
    ax.plot(x, T["O"], "-^", color=COL["O"], label="observables shown", ms=3)
    ax.plot(x, [c["O_cumulative"] for c in cum], "--", color=COL["O"], label="observables cumulative")
    ax.set_xlabel("step"); ax.set_ylabel("count"); ax.legend(frameon=False); ax.set_title("Layer sizes")
    ax = axes[1]
    ax.plot(x, T["eff"], "-o", color="#8a4b9c", label="effective nodes", ms=3)
    ax.plot(x, T["fund"], "-s", color="#1b7f6b", label="fundamental nodes", ms=3)
    ax.plot(x, T["cluster"], "-d", color="#777777", label="clusters", ms=3)
    ax.plot(x, T["AND"], "-^", color="#b5651d", label="AND routes", ms=3)
    ax.set_xlabel("step"); ax.legend(frameon=False); ax.set_title("Model layer and routes")
    ax = axes[2]
    ax.bar([i - 0.2 for i in x], T["unexplained"], width=0.4, color="#c33", label="unexplained (page view)")
    ax.bar([i + 0.2 for i in x], [len(c["unexplained_cumulative"]) for c in cum], width=0.4, color="#f4a", label="unexplained (cumulative)")
    ax.plot(x, T["calibrations"], "-o", color="#333", ms=3, label="calibration edges")
    ax.set_xlabel("step"); ax.legend(frameon=False); ax.set_title("Deficits and calibrations")
    for ax in axes: ax.set_xticks(x)
    fig.savefig(os.path.join(FIG, "fig_hep_trajectories.pdf"))
    plt.close(fig)


def fig_rule_matrix(R):
    h = R["hep"]; auto = {int(k): v for k, v in h["auto_matrix"].items()}; hand = {int(k): v for k, v in h["hand_matrix"].items()}
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    names = R["rules"]
    for k in range(1, 13):
        for r in range(1, 11):
            a = auto.get(k, {}).get(str(r), auto.get(k, {}).get(r, "")); hv = hand[k].get(str(r), hand[k].get(r, ""))
            if a == hv:
                face = "#ffffff" if a == "" else ("#2a6f97" if a == "●" else "#9ec3dd")
            else:
                face = "#e9a23b"
            ax.add_patch(FancyBboxPatch((r - 0.45, k - 0.45), 0.9, 0.9, boxstyle="round,pad=0.02", fc=face, ec="#999999", lw=0.5))
            if a == "●": ax.text(r, k, "●", ha="center", va="center", color="white", fontsize=8)
            elif a == "○": ax.text(r, k, "○", ha="center", va="center", color="black", fontsize=8)
            if a != hv:
                ax.text(r + 0.3, k - 0.3, hv if hv else "·", ha="center", va="center", fontsize=6, color="black")
    ax.set_xlim(0.4, 10.6); ax.set_ylim(12.6, 0.4)
    ax.set_xticks(range(1, 11)); ax.set_xticklabels([f"R{r}" for r in range(1, 11)])
    ax.set_yticks(range(1, 13)); ax.set_yticklabels([f"{k}" for k in range(1, 13)])
    ax.set_xlabel("rule"); ax.set_ylabel("step"); ax.set_aspect("equal")
    ax.set_title("Rules detected from the data (● fires, ○ prepared); orange cells differ from the hand matrix", fontsize=8)
    fig.savefig(os.path.join(FIG, "fig_rule_matrix.pdf"))
    plt.close(fig)


def fig_growth(R):
    D = R["typeD"]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 2.8))
    for ax, b in zip(axes, ("EM", "UP")):
        G = D[b]["growth"]; t = [g["t"] for g in G]
        for L in "SMO":
            ax.plot(t, [g[L] for g in G], color=COL[L], label={"S": "states", "M": "models", "O": "observables"}[L])
        ax.plot(t, [g["routes"] for g in G], color="#999999", ls="--", label="routes")
        ax2 = ax.twinx()
        ax2.fill_between(t, 0, [g["quantum"] for g in G], color="#8a4b9c", alpha=0.12, label="quantum nodes")
        ax2.fill_between(t, 0, [g["relativistic"] for g in G], color="#1b7f6b", alpha=0.15, label="relativistic nodes")
        ax2.set_ylabel("era counts", color="#777")
        fl = [x for x in D[b]["failed"]["rows"]]
        for x in fl:
            ax.axvline(x["t_failed"], color="#c33", lw=0.6, alpha=0.6)
        ax.set_xlabel("paragraph index"); ax.set_ylabel("cumulative count"); ax.set_title(BRANCH_TITLE[b] + " — growth; red lines = failed routes")
        ax.legend(frameon=False, loc="upper left")
    fig.savefig(os.path.join(FIG, "fig_growth.pdf"))
    plt.close(fig)


def fig_census(R):
    E = R["typeE"]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.2), gridspec_kw={"width_ratios": [1.3, 1]})
    ax = axes[0]
    pw = E["GPT"]["witness_census"]["per_witness"]
    names = list(pw.keys())
    settled = [pw[w]["settled"] for w in names]; blind = [pw[w]["blind"] for w in names]; fires = [pw[w]["fires"] for w in names]; hidden = [pw[w]["hidden"] for w in names]
    y = np.arange(len(names))
    ax.barh(y, blind, color="#bbbbbb", label="blind")
    ax.barh(y, fires, left=blind, color="#2a6f97", label="fires")
    ax.barh(y, hidden, left=np.array(blind) + np.array(fires), color="#e9a23b", label="hidden")
    ax.set_yticks(y); ax.set_yticklabels([n.replace("w-", "") for n in names]); ax.invert_yaxis()
    ax.set_xlim(0, 182); ax.set_xlabel("settled cells of 182 (14 state × 13 process clusters)")
    ax.set_title(f"Nonclassicality network: witness matrix census, {E['GPT']['witness_census']['settled']} / {E['GPT']['witness_census']['cells']} cells settled")
    ax.legend(frameon=False, loc="lower right")
    ax = axes[1]
    q = E["QRT"]["conversion_census"]; th = q["theories"]; M = np.zeros((len(th), len(th)))
    for i, a in enumerate(th):
        for j, b in enumerate(th):
            v = q["matrix"][a][b]
            M[i, j] = {"C": 3, "s": 2, "x": 1, "": 0}[v] if i != j else -1
    cmap = matplotlib.colors.ListedColormap(["#eeeeee", "#ffffff", "#f7d8b5", "#9ec3dd", "#2a6f97"])
    ax.imshow(M, cmap=cmap, vmin=-1, vmax=3)
    ax.set_xticks(range(len(th))); ax.set_xticklabels(th, rotation=90); ax.set_yticks(range(len(th))); ax.set_yticklabels(th)
    ax.set_xlabel("to theory"); ax.set_ylabel("from theory")
    ax.set_title(f"QRT conversion matrix: {q['charted_conversion_group']} / {q['cells']} cells charted (dark); light = other cross-theory edges")
    fig.savefig(os.path.join(FIG, "fig_census.pdf"))
    plt.close(fig)


def fig_order(R):
    oc = R["typeD"]["order_EM_vs_UP"]
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    xs = [p["t_EM"] for p in oc["pairs"]]; ys = [p["t_UP"] for p in oc["pairs"]]
    ax.scatter(xs, ys, s=14, color=COL["neutral"])
    for p in oc["pairs"]:
        ax.annotate(p["concept"], (p["t_EM"], p["t_UP"]), fontsize=5, xytext=(2, 2), textcoords="offset points")
    ax.set_xlabel("first paragraph in the EM history reader"); ax.set_ylabel("first paragraph in the University Physics reader")
    ax.set_title(f"Historical vs pedagogical order on {oc['n']} shared concepts: Kendall τ_b = {oc['kendall_tau_b']:.2f}")
    fig.savefig(os.path.join(FIG, "fig_order.pdf"))
    plt.close(fig)


def fig_sector_term(R):
    h = R["hep"]["sector_term_census"]; M = h["matrix"]
    secs = list(M.keys()); terms = list(next(iter(M.values())).keys())
    A = np.array([[1 if M[s][t] else 0 for t in terms] for s in secs])
    fig, ax = plt.subplots(figsize=(4.2, 3.2))
    ax.imshow(A, cmap=matplotlib.colors.ListedColormap(["#ffffff", "#2a6f97"]), vmin=0, vmax=1)
    ax.set_xticks(range(len(terms))); ax.set_xticklabels(terms, rotation=45, ha="right"); ax.set_yticks(range(len(secs))); ax.set_yticklabels(secs)
    for i in range(len(secs)):
        for j in range(len(terms)):
            ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, ec="#cccccc", lw=0.4))
    ax.set_title(f"Sector × term routes in the final SM graph: {h['entered']} of {h['cells']} cells")
    fig.savefig(os.path.join(FIG, "fig_sector_term.pdf"))
    plt.close(fig)


def fig_atlas(R):
    """Schematic of the grand network: branch blocks on a circle, glue chords with shared-concept counts."""
    counts = R["counts"]["per_branch"]; concepts = R["concepts"]
    order = ["UP", "EM", "LG", "HEP", "QRT", "GPT"]
    fig, ax = plt.subplots(figsize=(9.5, 7.2))
    W, H, Rr = 1.05, 0.72, 2.2
    centers = {}
    for i, b in enumerate(order):
        ang = math.pi / 2 - 2 * math.pi * i / len(order)
        cx, cy = Rr * math.cos(ang), Rr * math.sin(ang)
        centers[b] = (cx, cy)
    # chords first (below the blocks)
    pair_counts = {}
    for c in concepts:
        bs = sorted(c["roles"].keys())
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                pair_counts[(bs[i], bs[j])] = pair_counts.get((bs[i], bs[j]), 0) + 1
    for (a, b), n in pair_counts.items():
        (x1, y1), (x2, y2) = centers[a], centers[b]
        ax.plot([x1, x2], [y1, y2], color="#888888", lw=0.6 + 0.1 * n, alpha=0.75, zorder=1, solid_capstyle="round")
        f = 0.5 if (a, b) != ("HEP", "UP") else 0.62
        mx, my = x1 + f * (x2 - x1), y1 + f * (y2 - y1)
        ax.text(mx, my, str(n), ha="center", va="center", fontsize=7.5, zorder=6, bbox=dict(fc="white", ec="#888", boxstyle="round,pad=0.18"))
    for b, (cx, cy) in centers.items():
        ax.add_patch(FancyBboxPatch((cx - W / 2, cy - H / 2), W, H, boxstyle="round,pad=0.03", fc="#f7f7f7", ec="#444444", lw=0.8, zorder=3))
        ax.text(cx, cy + H / 2 - 0.06, BRANCH_TITLE[b], ha="center", va="top", fontsize=7.5, fontweight="bold", zorder=5)
        for i, L in enumerate("OMS"):
            yy = cy + H / 2 - 0.2 - i * 0.16
            ax.add_patch(FancyBboxPatch((cx - W / 2 + 0.07, yy - 0.06), W - 0.14, 0.12, boxstyle="round,pad=0.01", fc=COL[L], ec="none", alpha=0.85, zorder=4))
            ax.text(cx, yy, f"{ {'S':'states','M':'models','O':'observables'}[L]}: {counts[b][L]}", ha="center", va="center", color="white", fontsize=7, zorder=5)
        ax.text(cx, cy - H / 2 + 0.035, f"{counts[b]['nodes']} nodes · {counts[b]['routes']} routes", ha="center", va="bottom", fontsize=6.5, color="#333", zorder=5)
    ax.set_xlim(-3.1, 3.1); ax.set_ylim(-2.9, 2.9); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"The Grand Epistemic Network: {R['counts']['branches']} branches, {R['counts']['nodes']} nodes, {R['counts']['routes']} routes, "
                 f"{R['counts']['concepts']} shared concepts\n(chord labels = number of concepts the two branches share)", fontsize=8.5)
    fig.savefig(os.path.join(FIG, "fig_atlas.pdf"))
    plt.close(fig)


def fig_carry_in(R):
    rows = R["typeD"]["UP"]["chapters"]
    fig, ax = plt.subplots(figsize=(10.5, 2.6))
    x = np.arange(len(rows))
    ax.bar(x - 0.3, [r["new_nodes"] for r in rows], width=0.3, color="#2a6f97", label="new nodes")
    ax.bar(x, [r["routes"] for r in rows], width=0.3, color="#c05c2a", label="routes")
    ax.bar(x + 0.3, [r["carried_in"] for r in rows], width=0.3, color="#3f7d4e", label="earlier nodes carried in")
    ax.set_xticks(x); ax.set_xticklabels([f"{r['vol']}.{r['ch']}" for r in rows], rotation=90, fontsize=6)
    ax.set_xlabel("chapter (volume.chapter)"); ax.legend(frameon=False); ax.set_title("University Physics: per-chapter growth and carry-in of earlier concepts")
    fig.savefig(os.path.join(FIG, "fig_carry_in.pdf"))
    plt.close(fig)


def fig_cycle(R):
    """The mechanical loop (schematic)."""
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    steps = [("observe", "new observable node\n(or new theorem / paragraph)"), ("deficit", "in-degree-0 observables,\nuncharted cells, shared\ncalibrations, failed routes"),
             ("hypothesize", "candidate model node /\ncandidate edge (solver)"), ("restructure", "ADD / EXTEND / SPLIT /\nMERGE / ABSORB / CLUSTER"),
             ("predict", "new M→O edges,\nbadge P"), ("calibrate", "status fit edges"), ("reduce", "merge, absorb, cluster,\ncommutant reduction")]
    n = len(steps); cx, cy, r = 3.2, 1.7, 1.25
    for i, (a, b) in enumerate(steps):
        ang = math.pi / 2 - 2 * math.pi * i / n
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
        ax.add_patch(FancyBboxPatch((x - 0.42, y - 0.22), 0.84, 0.44, boxstyle="round,pad=0.03", fc="#eef3f8", ec="#2a6f97", lw=0.8))
        ax.text(x, y + 0.08, a, ha="center", va="center", fontsize=8, fontweight="bold")
        ax.text(x, y - 0.09, b, ha="center", va="center", fontsize=5.5)
        ang2 = math.pi / 2 - 2 * math.pi * (i + 1) / n
        x2, y2 = cx + r * math.cos(ang2), cy + r * math.sin(ang2)
        ax.annotate("", xy=(x2, y2), xytext=(x, y), arrowprops=dict(arrowstyle="->", color="#777", lw=0.8, shrinkA=24, shrinkB=24, connectionstyle="arc3,rad=-0.25"))
    ax.text(cx, cy, "agenda $A(G_t)$\ncomputed in\n$O(|V|+|R|+\\#\\mathrm{cells})$", ha="center", va="center", fontsize=7)
    ax.set_xlim(0.9, 5.5); ax.set_ylim(0.1, 3.3); ax.axis("off"); ax.set_aspect("equal")
    fig.savefig(os.path.join(FIG, "fig_cycle.pdf"))
    plt.close(fig)


def main():
    R = load()
    fig_signatures(R); fig_hep_trajectories(R); fig_rule_matrix(R); fig_growth(R); fig_census(R); fig_order(R)
    fig_sector_term(R); fig_atlas(R); fig_carry_in(R); fig_cycle(R)
    print("figures written to", FIG)


if __name__ == "__main__":
    main()
