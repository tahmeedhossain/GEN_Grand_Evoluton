"""Evolution analyses on the dated branches (EM, HEP, GPT, QRT) and the merged four-branch evolutionary network.

All quantities are computed from the year index of chrono.py.  Nothing is hand-assigned except the
mapping of route kinds to method phases (PHASE_OF_KIND), which is stated in the thesis.
"""
from __future__ import annotations
import math
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict, Counter
from .schema import Graph
from .glue import CONCEPTS

FOUR = ("EM", "HEP", "GPT", "QRT")

# method phase of a route, by universal kind (and polarity for the effect networks)
PHASE_OF_KIND = {
    # readers
    "derives": "predict", "failed": "falsify",
    # history
    "enters": "restructure", "predicts": "predict", "calibrates": "calibrate", "frames": "hypothesize",
    "candidate": "hypothesize", "backedge": "restructure", "lineage": "reduce", "subset": "reduce",
    # effect / resource networks
    "implies": "predict", "necessary": "predict", "enables": "predict", "witness": "observe", "converts_to": "predict",
    "activates": "predict", "reversible": "predict", "hosts": "predict", "generates": "hypothesize",
    "equiv": "reduce", "specializes": "reduce", "contains": "reduce", "bounds": "predict",
    "pairs": "observe", "member_free": "restructure", "member_resource": "restructure", "satisfies": "restructure",
    "not_implies": "falsify", "forbids": "falsify", "hides": "falsify", "excludes": "falsify", "distinct": "falsify",
    "violates": "falsify", "irreversible": "falsify",
    "open": "deficit",
    "transport": "predict", "conversion": "predict",
}
PHASES = ("observe", "deficit", "hypothesize", "restructure", "predict", "falsify", "calibrate", "reduce")


def phase_of_route(r) -> str:
    if r.status == "open" or r.kind == "open":
        return "deficit"
    return PHASE_OF_KIND.get(r.kind, "predict")


def phase_of_node(n) -> str:
    return {"O": "observe", "M": "hypothesize", "S": "restructure"}[n.layer]


# ---------------------------------------------------------------------------
def year_of(x) -> int:
    return x.extra["t_year"]


def filtration_years(g: Graph) -> List[int]:
    return sorted({year_of(n) for n in g.nodes.values()} | {year_of(r) for r in g.routes.values()})


def cumulative_curve(g: Graph, years: List[int] = None) -> List[Dict[str, Any]]:
    ys = years or filtration_years(g)
    out = []
    for T in ys:
        row = {"year": T}
        for L in "SMO":
            row[L] = sum(1 for n in g.nodes.values() if n.layer == L and year_of(n) <= T)
        row["V"] = row["S"] + row["M"] + row["O"]
        row["E"] = sum(1 for r in g.routes.values() if year_of(r) <= T)
        for pol in ("structural", "possibility", "no_go", "open"):
            row[pol] = sum(1 for r in g.routes.values() if r.polarity == pol and year_of(r) <= T)
        out.append(row)
    return out


def growth_decomposition(g: Graph) -> Dict[str, Any]:
    """Per-year decomposition of the growth of a dated graph into arrivals (nodes with the edges they bring)
    and closures (edges between nodes that already existed), with latencies and the identity check."""
    years = filtration_years(g)
    node_year = {n.uid: year_of(n) for n in g.nodes.values()}
    rows = []
    closures = []
    arrival_degree: Dict[str, int] = {u: 0 for u in g.nodes}
    same_year_edges = 0
    for y in years:
        arr = [n for n in g.nodes.values() if year_of(n) == y]
        edges = [r for r in g.routes.values() if year_of(r) == y]
        a_edges = []; c_edges = []
        for r in edges:
            ends = r.inputs + [r.target]
            if any(node_year[u] == y for u in ends):
                a_edges.append(r)
                if all(node_year[u] == y for u in ends):
                    same_year_edges += 1
                for u in ends:
                    if node_year[u] == y:
                        arrival_degree[u] += 1
            else:
                c_edges.append(r)
                lat = y - max(node_year[u] for u in ends)
                closures.append({"edge": r.native_id, "year": y, "latency": lat, "kind": r.kind, "polarity": r.polarity, "status": r.status,
                                 "from": r.inputs[0].split(":")[1], "to": r.target.split(":")[1]})
        row = {"year": y, "arrivals": len(arr), "arrivals_by_layer": Counter(n.layer for n in arr), "arrival_edges": len(a_edges), "closure_edges": len(c_edges),
               "polarity": Counter(r.polarity for r in edges), "phases_routes": Counter(phase_of_route(r) for r in edges),
               "phases_nodes": Counter(phase_of_node(n) for n in arr),
               "nodes": [n.native_id for n in arr], "edges": [r.native_id for r in edges]}
        rows.append(row)
    lat = [c["latency"] for c in closures]
    E = len(g.routes)
    sum_arr_deg = sum(arrival_degree.values())
    # excess: a route with a(r) arriving endpoints is counted a(r) times in the arrival degrees
    excess = 0
    for r in g.routes.values():
        a = sum(1 for u in r.inputs + [r.target] if node_year[u] == year_of(r))
        if a >= 1:
            excess += a - 1
    identity = {"E": E, "sum_arrival_degree": sum_arr_deg, "excess_multi_arrival": excess, "closures": len(closures),
                "check": sum_arr_deg - excess + len(closures), "holds": sum_arr_deg - excess + len(closures) == E}
    deg_at_arrival = Counter(arrival_degree.values())
    return {"rows": rows, "closures": closures, "n_closures": len(closures), "closure_fraction": len(closures) / E if E else None,
            "latency_mean": (sum(lat) / len(lat)) if lat else None, "latency_median": (sorted(lat)[len(lat) // 2] if lat else None),
            "latency_max": max(lat) if lat else None, "latency_hist": dict(sorted(Counter(min(l, 60) // 5 * 5 for l in lat).items())),
            "identity": identity, "degree_at_arrival": dict(sorted(deg_at_arrival.items())),
            "mean_degree_at_arrival": sum_arr_deg / len(g.nodes)}


def densification(curve: List[Dict[str, Any]], vmin: int = 10) -> Dict[str, Any]:
    pts = [(r["V"], r["E"]) for r in curve if r["V"] >= vmin and r["E"] >= 1]
    if len(pts) < 3:
        return {"alpha": None, "n": len(pts)}
    xs = [math.log(v) for v, e in pts]; ys = [math.log(e) for v, e in pts]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs); sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    a = sxy / sxx if sxx else None
    b = my - a * mx if a is not None else None
    ss_res = sum((y - (a * x + b)) ** 2 for x, y in zip(xs, ys)) if a is not None else None
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if (ss_tot and ss_res is not None) else None
    return {"alpha": a, "intercept": b, "r2": r2, "n": len(pts), "V_final": pts[-1][0], "E_final": pts[-1][1]}


def preferential_attachment(g: Graph) -> Dict[str, Any]:
    """For closure edges: mean degree (at the time) of the endpoints vs the mean degree of all nodes then present."""
    years = filtration_years(g)
    node_year = {n.uid: year_of(n) for n in g.nodes.values()}
    deg: Dict[str, int] = defaultdict(int)
    present: Set[str] = set()
    ratios = []; n_closure = 0; sum_end = 0.0; sum_all = 0.0
    for y in years:
        for n in g.nodes.values():
            if year_of(n) == y:
                present.add(n.uid)
        edges = [r for r in g.routes.values() if year_of(r) == y]
        # evaluate closure edges against the degrees before this year's edges are added
        for r in edges:
            ends = r.inputs + [r.target]
            if all(node_year[u] < y for u in ends) and present:
                mean_all = sum(deg[u] for u in present) / len(present)
                mean_end = sum(deg[u] for u in ends) / len(ends)
                n_closure += 1; sum_end += mean_end; sum_all += mean_all
        for r in edges:
            for u in r.inputs + [r.target]:
                deg[u] += 1
    return {"n_closure": n_closure, "mean_endpoint_degree": sum_end / n_closure if n_closure else None,
            "mean_present_degree": sum_all / n_closure if n_closure else None,
            "ratio": (sum_end / sum_all) if sum_all else None}


def witness_effect_timing(g: Graph) -> Dict[str, Any]:
    rows = []
    for r in g.routes.values():
        if r.kind == "pairs":
            w, e = r.inputs[0], r.target
            rows.append({"witness": w.split(":")[1], "effect": e.split(":")[1], "t_witness": year_of(g.nodes[w]), "t_effect": year_of(g.nodes[e]), "t_edge": year_of(r)})
    same = sum(1 for x in rows if x["t_witness"] == x["t_effect"]); wfirst = sum(1 for x in rows if x["t_witness"] < x["t_effect"]); efirst = sum(1 for x in rows if x["t_witness"] > x["t_effect"])
    return {"pairs": len(rows), "same_year": same, "witness_first": wfirst, "effect_first": efirst, "rows": rows}


def explanation_lag(g: Graph) -> Dict[str, Any]:
    """For each effect node: years from its appearance to the first edge from the model layer into it."""
    rows = []
    for n in g.nodes.values():
        if n.sublayer != "O.effect":
            continue
        m_edges = [r for r in g.routes.values() if r.target == n.uid and g.layer_of(r.inputs[0]) == "M"]
        s_edges = [r for r in g.routes.values() if r.target == n.uid and g.layer_of(r.inputs[0]) == "S"]
        first_m = min((year_of(r) for r in m_edges), default=None); first_s = min((year_of(r) for r in s_edges), default=None)
        rows.append({"effect": n.native_id, "t": year_of(n), "first_model_edge": first_m, "lag_model": (first_m - year_of(n)) if first_m is not None else None,
                     "first_state_edge": first_s, "lag_state": (first_s - year_of(n)) if first_s is not None else None})
    lm = [x["lag_model"] for x in rows if x["lag_model"] is not None]
    return {"effects": len(rows), "with_model_edge": len(lm), "mean_lag_model": sum(lm) / len(lm) if lm else None, "max_lag_model": max(lm) if lm else None, "rows": rows}


def first_edge_polarity(g: Graph) -> Dict[str, Any]:
    """Polarity of the first incident edge of each node, by layer."""
    out: Dict[str, Counter] = {"S": Counter(), "M": Counter(), "O": Counter()}
    for n in g.nodes.values():
        inc = [r for r in g.routes.values() if n.uid in r.inputs or n.uid == r.target]
        if not inc:
            out[n.layer]["isolated"] += 1; continue
        y0 = min(year_of(r) for r in inc)
        first = [r for r in inc if year_of(r) == y0]
        pols = sorted({r.polarity for r in first})
        out[n.layer]["+".join(pols)] += 1
    return {L: dict(c) for L, c in out.items()}


def layer_lead(curve: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Year at which each layer reaches half of its final size."""
    final = curve[-1]
    out = {}
    for L in "SMO":
        half = final[L] / 2
        out[L] = next((r["year"] for r in curve if r[L] >= half), None)
    return out


# ---------------------------------------------------------------------------
# merged four-branch evolutionary network
# ---------------------------------------------------------------------------
def concept_table(gs: Dict[str, Graph]) -> List[Dict[str, Any]]:
    rows = []
    for cid, label, members, note in CONCEPTS:
        mem = {b: ids for b, ids in members.items() if b in FOUR}
        if len(mem) < 2:
            continue
        years = {}
        for b, ids in mem.items():
            ys = [year_of(gs[b].nodes[f"{b}:{i}"]) for i in ids]
            years[b] = min(ys)
        first_b = min(years, key=years.get)
        rows.append({"id": cid, "label": label, "years": years, "first": first_b, "t_first": years[first_b], "t_last": max(years.values()),
                     "lag": max(years.values()) - min(years.values()), "branches": sorted(mem), "note": note,
                     "roles": {b: sorted({gs[b].nodes[f'{b}:{i}'].layer for i in ids}) for b, ids in mem.items()}})
    return sorted(rows, key=lambda r: r["t_first"])


def merged_curve(gs: Dict[str, Graph], concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    years = sorted(set().union(*[set(filtration_years(gs[b])) for b in FOUR]))
    member_concept = {}
    for c in concepts:
        for b in c["branches"]:
            for cid_, label, members, note in CONCEPTS:
                if cid_ == c["id"]:
                    for i in members.get(b, []):
                        member_concept[f"{b}:{i}"] = c["id"]
    out = []
    for T in years:
        row = {"year": T}
        tot = 0
        for b in FOUR:
            g = gs[b]
            row[b] = sum(1 for n in g.nodes.values() if year_of(n) <= T); tot += row[b]
            row[b + "_E"] = sum(1 for r in g.routes.values() if year_of(r) <= T)
        row["V"] = tot
        for L in "SMO":
            row[L] = sum(1 for b in FOUR for n in gs[b].nodes.values() if n.layer == L and year_of(n) <= T)
        row["E"] = sum(row[b + "_E"] for b in FOUR)
        # glue edges: a concept with k members present contributes k-1 identifications
        present_members = defaultdict(int)
        for b in FOUR:
            for n in gs[b].nodes.values():
                if year_of(n) <= T and n.uid in member_concept:
                    present_members[member_concept[n.uid]] += 1
        row["glue"] = sum(k - 1 for k in present_members.values() if k >= 2)
        row["concepts_shared_live"] = sum(1 for k in present_members.values() if k >= 2)
        row["V_collapsed"] = tot - row["glue"]
        out.append(row)
    return out


def decade_table(gs: Dict[str, Graph]) -> List[Dict[str, Any]]:
    """Per decade and branch: new nodes by layer, new routes by phase, with the rule attribution."""
    rows = []
    decades = sorted({(year_of(n) // 10) * 10 for b in FOUR for n in gs[b].nodes.values()} | {(year_of(r) // 10) * 10 for b in FOUR for r in gs[b].routes.values()})
    for d in decades:
        for b in FOUR:
            g = gs[b]
            nodes = [n for n in g.nodes.values() if (year_of(n) // 10) * 10 == d]
            routes = [r for r in g.routes.values() if (year_of(r) // 10) * 10 == d]
            if not nodes and not routes:
                continue
            rows.append({"decade": d, "branch": b, "nodes": len(nodes), "S": sum(1 for n in nodes if n.layer == "S"), "M": sum(1 for n in nodes if n.layer == "M"),
                         "O": sum(1 for n in nodes if n.layer == "O"), "routes": len(routes),
                         "phases": {p: sum(1 for r in routes if phase_of_route(r) == p) for p in PHASES},
                         "polarity": dict(Counter(r.polarity for r in routes)), "kinds": dict(Counter(r.kind for r in routes))})
    return rows


def merged_phase_table(gs: Dict[str, Graph]) -> List[Dict[str, Any]]:
    decades = sorted({(year_of(n) // 10) * 10 for b in FOUR for n in gs[b].nodes.values()} | {(year_of(r) // 10) * 10 for b in FOUR for r in gs[b].routes.values()})
    rows = []
    for d in decades:
        ph = Counter()
        for b in FOUR:
            for n in gs[b].nodes.values():
                if (year_of(n) // 10) * 10 == d:
                    ph[phase_of_node(n)] += 1
            for r in gs[b].routes.values():
                if (year_of(r) // 10) * 10 == d:
                    ph[phase_of_route(r)] += 1
        rows.append({"decade": d, **{p: ph.get(p, 0) for p in PHASES}, "total": sum(ph.values())})
    return rows


def hep_rules_by_year(hep_replay: Dict[str, Any], raw_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The automatically detected rule firings of the Standard Model replay placed on the year axis (start year of the step)."""
    import re
    out = []
    for k, rules in hep_replay["auto_matrix"].items():
        k = int(k)
        yrs = [int(y) for y in re.findall(r"(1[5-9]\d{2}|20[0-2]\d)", raw_steps[k - 1].get("years") or "")]
        # a step is placed at its start year; the final view (step 12, "1927-2012 (final view)") at the end of its range
        y = (max(yrs) if k == 12 else min(yrs)) if yrs else None
        out.append({"step": k, "id": raw_steps[k - 1]["id"], "year": y, "rules": rules})
    return sorted(out, key=lambda r: (r["year"] or 0, r["step"]))
