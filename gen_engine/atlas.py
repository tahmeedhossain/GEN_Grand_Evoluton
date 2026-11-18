"""Atlas builder: the six normalised branch graphs glued into the Grand Epistemic Network."""
from __future__ import annotations
from dataclasses import asdict
from typing import Dict, List, Any
import datetime
from .schema import Graph
from .glue import CONCEPTS, CROSS_EDGES


def build_atlas(graphs: Dict[str, Graph]) -> Dict[str, Any]:
    uid_concept: Dict[str, str] = {}
    concepts: List[Dict[str, Any]] = []
    errors = []
    for cid, label, members, note in CONCEPTS:
        rec = {"id": cid, "label": label, "members": [], "roles": {}, "sublayers": {}, "note": note}
        for b, ids in members.items():
            for nid in ids:
                uid = f"{b}:{nid}"
                if uid not in graphs[b].nodes:
                    errors.append(f"concept {cid}: unknown node {uid}")
                    continue
                if uid in uid_concept:
                    errors.append(f"node {uid} in two concepts: {uid_concept[uid]} and {cid}")
                uid_concept[uid] = cid
                n = graphs[b].nodes[uid]
                rec["members"].append(uid)
                rec["roles"].setdefault(b, set()).add(n.layer)
                rec["sublayers"].setdefault(b, set()).add(n.sublayer)
        rec["roles"] = {b: sorted(v) for b, v in rec["roles"].items()}
        rec["sublayers"] = {b: sorted(v) for b, v in rec["sublayers"].items()}
        allroles = sorted({r for v in rec["roles"].values() for r in v})
        rec["role_set"] = allroles
        rec["flip"] = len(allroles) > 1
        rec["n_branches"] = len(rec["roles"])
        concepts.append(rec)
    if errors:
        raise ValueError("\n".join(errors))
    for g in graphs.values():
        for n in g.nodes.values():
            n.concept = uid_concept.get(n.uid)
    cross = []
    for f, t, rel, note in CROSS_EDGES:
        fb = f.split(":")[0]
        if f not in graphs[fb].nodes:
            raise ValueError(f"cross edge: unknown node {f}")
        if t.startswith("c:"):
            if t[2:] not in {c["id"] for c in concepts}:
                raise ValueError(f"cross edge: unknown concept {t}")
        else:
            tb = t.split(":")[0]
            if t not in graphs[tb].nodes:
                raise ValueError(f"cross edge: unknown node {t}")
        cross.append({"from": f, "to": t, "relation": rel, "note": note})

    atlas = {
        "schema": "gen-grand/1",
        "title": "The Grand Epistemic Network of physics: six concept graphs glued on shared concepts",
        "generated": datetime.date.today().isoformat(),
        "layers": {"S": "state", "M": "model", "O": "observable"},
        "branch_types": {"D": "dynamic / pedagogical reader: observables primitive, AND routes M∧S→S/O",
                         "H": "historical theory-building: S→M routes with occupation numbers, M→O predictions, M→S back-edges",
                         "E": "effect / resource network: model fixed (quantum theory and its GPT neighbours), state clusters, witness-effect pairs, direct S→effect edges"},
        "branches": [asdict(g.branch) for g in graphs.values()],
        "nodes": [asdict(n) for g in graphs.values() for n in g.nodes.values()],
        "routes": [asdict(r) for g in graphs.values() for r in g.routes.values()],
        "concepts": concepts,
        "cross_edges": cross,
        "hep_clusters": graphs["HEP"].clusters,
    }
    # counts
    atlas["counts"] = {
        "branches": len(graphs),
        "nodes": len(atlas["nodes"]),
        "routes": len(atlas["routes"]),
        "concepts": len(concepts),
        "glued_nodes": len(uid_concept),
        "role_flips": sum(1 for c in concepts if c["flip"]),
        "cross_edges": len(cross),
        "per_branch": {b: {"nodes": len(g.nodes), "routes": len(g.routes),
                           "S": len(g.nodes_in("S")), "M": len(g.nodes_in("M")), "O": len(g.nodes_in("O")),
                           "AND": sum(1 for r in g.routes.values() if r.logic == "AND"),
                           "or_targets": len(g.or_targets())}
                       for b, g in graphs.items()},
    }
    return atlas
