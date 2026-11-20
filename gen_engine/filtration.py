"""Reading-indexed (type D) graphs: filtration checks, growth curves, failed-route resolution,
chapter carry-in, prerequisite depth, and the historical-vs-pedagogical order comparison."""
from __future__ import annotations
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import networkx as nx
from .schema import Graph


def filtration_check(g: Graph) -> Dict[str, Any]:
    """Rule 11: every route appears no earlier than its inputs and its target (no forward links)."""
    viol = []
    for r in g.routes.values():
        if r.t is None:
            continue
        for u in r.inputs + [r.target]:
            tu = g.nodes[u].t
            if tu is not None and tu > r.t:
                viol.append({"route": r.native_id, "node": u, "node_t": tu, "route_t": r.t})
    times = sorted({n.t for n in g.nodes.values() if n.t is not None} | {r.t for r in g.routes.values() if r.t is not None})
    return {"routes": len(g.routes), "forward_links": len(viol), "violations": viol[:20], "time_points": len(times),
            "t_min": times[0] if times else None, "t_max": times[-1] if times else None}


def growth_curve(g: Graph) -> List[Dict[str, Any]]:
    """Cumulative node counts per layer and route counts as functions of the time index."""
    ts = sorted({n.t for n in g.nodes.values() if n.t is not None} | {r.t for r in g.routes.values() if r.t is not None})
    out = []
    for t in ts:
        row = {"t": t}
        for L in "SMO":
            row[L] = sum(1 for n in g.nodes.values() if n.layer == L and n.t is not None and n.t <= t)
        row["routes"] = sum(1 for r in g.routes.values() if r.t is not None and r.t <= t)
        row["AND"] = sum(1 for r in g.routes.values() if r.t is not None and r.t <= t and r.logic == "AND")
        row["failed"] = sum(1 for r in g.routes.values() if r.t is not None and r.t <= t and r.kind == "failed")
        for era in ("classical", "relativistic", "quantum"):
            row[era] = sum(1 for n in g.nodes.values() if n.era == era and n.t is not None and n.t <= t)
        out.append(row)
    return out


def failed_route_resolution(g: Graph) -> Dict[str, Any]:
    """Rule 12: for each failed route into a target o, the first non-failed route into o at or after the failed route
    (forward resolution).  The nearest non-failed route before it (usually the measurement that the failed
    prediction is compared with) is recorded as well."""
    rows = []
    for r in g.routes.values():
        if r.kind != "failed":
            continue
        others = [s for s in g.routes.values() if s.target == r.target and s.kind != "failed" and s.t is not None and r.t is not None]
        later = [s for s in others if s.t >= r.t]; earlier = [s for s in others if s.t < r.t]
        row = {"failed": r.native_id, "target": r.target.split(":")[1], "t_failed": r.t, "title_failed": r.extra.get("title"),
               "resolved_by": None, "t_resolved": None, "distance": None, "resolver_kind": None, "earlier": None, "t_earlier": None, "earlier_kind": None}
        if later:
            s = min(later, key=lambda x: x.t)
            row.update({"resolved_by": s.native_id, "t_resolved": s.t, "distance": s.t - r.t, "resolver_kind": s.kind_native, "title_resolver": s.extra.get("title")})
        if earlier:
            e = max(earlier, key=lambda x: x.t)
            row.update({"earlier": e.native_id, "t_earlier": e.t, "earlier_kind": e.kind_native})
        rows.append(row)
    dist = [x["distance"] for x in rows if x["distance"] is not None]
    return {"n_failed": len(rows), "n_resolved": len(dist), "max_distance": max(dist) if dist else None,
            "mean_distance": (sum(dist) / len(dist)) if dist else None, "rows": rows}


def two_section(g: Graph) -> nx.DiGraph:
    """The 2-section digraph of the hypergraph: input -> target for every leg."""
    G = nx.DiGraph()
    G.add_nodes_from(g.nodes)
    for r in g.routes.values():
        for u in r.inputs:
            if u != r.target:
                G.add_edge(u, r.target, route=r.uid)
    return G


def depth_statistics(g: Graph) -> Dict[str, Any]:
    G = two_section(g)
    acyclic = nx.is_directed_acyclic_graph(G)
    sccs = [c for c in nx.strongly_connected_components(G) if len(c) > 1]
    cyc = []
    for c in sccs[:10]:
        try:
            cyc.append([u for u, v in nx.find_cycle(G.subgraph(c))])
        except nx.NetworkXNoCycle:
            pass
    out = {"nodes": G.number_of_nodes(), "edges_2section": G.number_of_edges(), "acyclic": acyclic,
           "n_nontrivial_sccs": len(sccs), "largest_scc": max((len(c) for c in sccs), default=0),
           "nodes_in_cycles": sum(len(c) for c in sccs), "cycles_sample": [[u.split(":")[1] for u in c] for c in cyc]}
    if acyclic:
        lp = nx.dag_longest_path(G)
        out["longest_chain"] = len(lp) - 1
        out["longest_chain_nodes"] = [u.split(":")[1] for u in lp]
    else:
        C = nx.condensation(G)
        lp = nx.dag_longest_path(C)
        out["longest_chain_condensed"] = len(lp) - 1
    # in/out degree summary by layer
    deg = {}
    for L in "SMO":
        ids = [n.uid for n in g.nodes_in(L)]
        deg[L] = {"mean_in": sum(G.in_degree(u) for u in ids) / max(1, len(ids)), "mean_out": sum(G.out_degree(u) for u in ids) / max(1, len(ids))}
    out["degree_by_layer"] = deg
    hubs = sorted(G.nodes, key=lambda u: G.out_degree(u), reverse=True)[:8]
    out["top_out_hubs"] = [(u.split(":")[1], g.nodes[u].layer, G.out_degree(u)) for u in hubs]
    sinks = sorted(G.nodes, key=lambda u: G.in_degree(u), reverse=True)[:8]
    out["top_in_hubs"] = [(u.split(":")[1], g.nodes[u].layer, G.in_degree(u)) for u in sinks]
    return out


def chapter_carry_in(g: Graph) -> List[Dict[str, Any]]:
    """University Physics: for each chapter, the earlier-chapter nodes that the chapter's routes connect to."""
    chapters = g.extra.get("chapters", [])
    rows = []
    for c in chapters:
        p0, p1 = c["p0"], c["p1"]
        new_nodes = {n.uid for n in g.nodes.values() if n.t is not None and p0 <= n.t <= p1}
        routes = [r for r in g.routes.values() if r.t is not None and p0 <= r.t <= p1]
        touched = set()
        for r in routes:
            for u in r.inputs + [r.target]:
                touched.add(u)
        carried = {u for u in touched if u not in new_nodes and g.nodes[u].t is not None and g.nodes[u].t < p0}
        rows.append({"vol": c["vol"], "ch": c["ch"], "title": c["title"], "unit": c.get("unit"), "new_nodes": len(new_nodes), "routes": len(routes),
                     "carried_in": len(carried), "carried_in_by_layer": {L: sum(1 for u in carried if g.nodes[u].layer == L) for L in "SMO"}})
    return rows


def order_comparison(graphs: Dict[str, Graph], concepts: List[Dict[str, Any]], a: str = "EM", b: str = "UP") -> Dict[str, Any]:
    """Historical (EM reader) vs pedagogical (UP reader) first-appearance order on the glued concepts."""
    pairs = []
    for c in concepts:
        ta = [graphs[a].nodes[u].t for u in c["members"] if u.startswith(a + ":")]
        tb = [graphs[b].nodes[u].t for u in c["members"] if u.startswith(b + ":")]
        if ta and tb:
            pairs.append({"concept": c["id"], "label": c["label"], f"t_{a}": min(ta), f"t_{b}": min(tb)})
    n = len(pairs)
    if n < 3:
        return {"n": n, "pairs": pairs}
    xa = [p[f"t_{a}"] for p in pairs]; xb = [p[f"t_{b}"] for p in pairs]
    # Kendall tau-b and Spearman rho (ties handled)
    conc = disc = 0; tie_a = tie_b = 0
    for i in range(n):
        for j in range(i + 1, n):
            da = xa[i] - xa[j]; db = xb[i] - xb[j]
            if da == 0 and db == 0:
                continue
            if da == 0: tie_a += 1; continue
            if db == 0: tie_b += 1; continue
            if (da > 0) == (db > 0): conc += 1
            else: disc += 1
    tau_b = (conc - disc) / (((conc + disc + tie_a) * (conc + disc + tie_b)) ** 0.5) if (conc + disc + tie_a) and (conc + disc + tie_b) else None
    def ranks(x):
        order = sorted(range(len(x)), key=lambda i: x[i]); r = [0.0] * len(x); i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]: j += 1
            for k in range(i, j + 1): r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    ra, rb = ranks(xa), ranks(xb)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n)); va = sum((x - ma) ** 2 for x in ra); vb = sum((x - mb) ** 2 for x in rb)
    rho = cov / (va * vb) ** 0.5 if va and vb else None
    inversions = [(pairs[i]["concept"], pairs[j]["concept"]) for i in range(n) for j in range(i + 1, n)
                  if (xa[i] - xa[j]) * (xb[i] - xb[j]) < 0]
    return {"n": n, "kendall_tau_b": tau_b, "spearman_rho": rho, "concordant": conc, "discordant": disc, "pairs": pairs,
            "inversions_sample": inversions[:40], "n_inversions": len(inversions)}
