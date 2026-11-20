"""Census of uncharted cells and the research agenda (Rules 13-14 and the agenda theorem).

Every number here is recomputed from the released data; where the
repositories publish a count, the engine reproduces it with the repository's
own rule and reports a structural count next to it.
"""
from __future__ import annotations
from typing import Dict, List, Any, Set, Tuple
from itertools import combinations
from .schema import Graph


# ---------------------------------------------------------------------------
# GPT: witness x state x process matrix (the page's rule, v26.html verdictFor)
# ---------------------------------------------------------------------------
def gpt_witness_census(g: Graph) -> Dict[str, Any]:
    W = g.extra["witnesses"]; combos = g.extra["combos"]
    states = [n.native_id for n in g.nodes.values() if n.native_layer == "state"]
    procs = [n.native_id for n in g.nodes.values() if n.native_layer == "process"]
    per_w = {}
    total_settled = 0
    verdict_counts = {"fires": 0, "hidden": 0, "blind": 0, "uncharted": 0}
    for w, wd in W.items():
        known = 0; vc = {"fires": 0, "hidden": 0, "blind": 0, "uncharted": 0}
        for s in states:
            for p in procs:
                c = next((c for c in combos if c["state"] == s and c["process"] == p), None)
                if c and c["verdict"].get(w):
                    v = c["verdict"][w]
                else:
                    v = "uncharted"
                    for bid, _ in wd["blind"]:
                        if bid == s or bid == p:
                            v = "blind"; break
                vc[v] = vc.get(v, 0) + 1
                if v != "uncharted":
                    known += 1
        per_w[w] = {"settled": known, "cells": len(states) * len(procs), **vc}
        total_settled += known
        for k in verdict_counts: verdict_counts[k] += vc.get(k, 0)
    cells = len(W) * len(states) * len(procs)
    return {"witnesses": len(W), "states": len(states), "processes": len(procs), "cells": cells,
            "settled": total_settled, "uncharted": cells - total_settled, "verdicts": verdict_counts, "per_witness": per_w}


def gpt_pair_census(g: Graph) -> Dict[str, Any]:
    """Unordered node pairs with at least one edge (either direction), as the repository counts them."""
    n = len(g.nodes)
    connected: Set[frozenset] = set()
    for r in g.routes.values():
        if r.inputs[0] != r.target:
            connected.add(frozenset((r.inputs[0], r.target)))
    pairs = n * (n - 1) // 2
    # by layer pair
    by_layer: Dict[Tuple[str, str], Dict[str, int]] = {}
    nodes = list(g.nodes.values())
    for a, b in combinations(nodes, 2):
        key = tuple(sorted((a.native_layer, b.native_layer)))
        rec = by_layer.setdefault(key, {"pairs": 0, "connected": 0})
        rec["pairs"] += 1
        if frozenset((a.uid, b.uid)) in connected:
            rec["connected"] += 1
    polarity = {"no_go": 0, "possibility": 0, "open": 0, "structural": 0}
    for r in g.routes.values():
        polarity[r.polarity] += 1
    return {"nodes": n, "pairs": pairs, "connected_pairs": len(connected), "unconnected_pairs": pairs - len(connected),
            "edges": len(g.routes), "polarity": polarity, "by_native_layer_pair": {"|".join(k): v for k, v in sorted(by_layer.items())}}


# ---------------------------------------------------------------------------
# QRT: 13 x 13 conversion matrix
# ---------------------------------------------------------------------------
def qrt_conversion_census(g: Graph) -> Dict[str, Any]:
    theories = [t["id"] for t in g.extra["theories"]]
    T = len(theories)
    theory_of = {n.uid: n.extra.get("theory") for n in g.nodes.values()}
    cells = T * (T - 1)
    charted_repo: Set[Tuple[str, str]] = set()     # the repository's conversion group (edge ids C*)
    charted_struct: Set[Tuple[str, str]] = set()   # any cross-theory edge between state-layer nodes
    cross_any: Set[Tuple[str, str]] = set()        # any cross-theory edge between non-framework nodes
    via = {}
    for r in g.routes.values():
        a, b = theory_of[r.inputs[0]], theory_of[r.target]
        if a in theories and b in theories and a != b:
            cross_any.add((a, b))
            if r.native_id.startswith("C"):
                charted_repo.add((a, b)); via[(a, b)] = r.extra.get("via")
            if g.nodes[r.inputs[0]].layer == "S" and g.nodes[r.target].layer == "S":
                charted_struct.add((a, b))
    matrix = {a: {b: ("C" if (a, b) in charted_repo else ("s" if (a, b) in charted_struct else ("x" if (a, b) in cross_any else ""))) for b in theories} for a in theories}
    return {"theories": theories, "cells": cells, "charted_conversion_group": len(charted_repo), "charted_state_to_state": len(charted_struct),
            "cross_theory_any": len(cross_any), "uncharted_conversion": cells - len(charted_repo), "matrix": matrix,
            "charted_cells": sorted(charted_repo), "via": {f"{a}->{b}": v for (a, b), v in via.items()}}


# ---------------------------------------------------------------------------
# Historical branch: sector x term census and the agenda
# ---------------------------------------------------------------------------
def hep_sector_term_census(g_final: Graph) -> Dict[str, Any]:
    sectors = [n.uid for n in g_final.nodes_in("S")]
    terms = [n.uid for n in g_final.nodes_in("M") if n.extra.get("kind") == "cluster"]
    entered: Set[Tuple[str, str]] = set()
    for r in g_final.routes.values():
        if r.logic == "AND":
            for u in r.inputs:
                entered.add((u, r.target))
    cells = len(sectors) * len(terms)
    matrix = {s.split(":")[1]: {t.split(":")[1]: ((s, t) in entered) for t in terms} for s in sectors}
    return {"sectors": len(sectors), "terms": len(terms), "cells": cells, "entered": len(entered), "empty": cells - len(entered), "matrix": matrix}


def agenda_type_E(g: Graph) -> Dict[str, Any]:
    open_edges = [r.native_id for r in g.routes.values() if r.kind == "open" or r.status == "open"]
    partial = [r.native_id for r in g.routes.values() if str(r.status).startswith("partial")]
    gaps = g.extra.get("gaps", [])
    return {"open_edges": open_edges, "partial_edges": partial, "recorded_gaps": len(gaps)}


def agenda_type_D(g: Graph) -> Dict[str, Any]:
    targets = {r.target for r in g.routes.values()}
    primitives = {L: sorted(n.uid.split(":")[1] for n in g.nodes_in(L) if n.uid not in targets) for L in "SMO"}
    failed = [r.native_id for r in g.routes.values() if r.kind == "failed"]
    single_route_models = []
    return {"primitive_nodes": primitives, "n_primitive": {L: len(v) for L, v in primitives.items()}, "failed_routes": failed,
            "or_targets": sorted(u.split(":")[1] for u in g.or_targets())}
