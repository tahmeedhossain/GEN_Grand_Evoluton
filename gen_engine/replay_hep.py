"""Replay of the Standard Model graph as graph operations, and automatic rule detection.

For each pair of consecutive graph steps the engine computes the set
differences of nodes and routes, decomposes them into primitive operations,
and evaluates the graph predicates of the ten rules of evolution.  The
result is a rule matrix computed from the data alone, which is compared with
the hand-assigned matrix of the GEN_HEP repository (tools/rules_steps.py).

Predicates use only: layers, node kinds (hilbert/uir/sector; frame/fund/eff/
cand/cluster), the UIR label of a sector, the A/P/F badge of an observable,
route kinds and AND-route leg sets.  No step text is read.
"""
from __future__ import annotations
import re
from typing import Dict, List, Set, Tuple, Any, FrozenSet
from .schema import Graph
from .load import load_hep_steps

HAND_MATRIX = {1: {}, 2: {1: '●', 8: '●'}, 3: {2: '○'}, 4: {2: '●', 3: '●'}, 5: {2: '●', 4: '●', 9: '●'},
               6: {2: '●', 4: '●', 5: '●', 9: '●'}, 7: {4: '●', 5: '●', 6: '○', 8: '●', 9: '●'},
               8: {2: '●', 4: '●', 6: '●', 9: '●'}, 9: {2: '●', 4: '●', 7: '●', 8: '●', 9: '●'},
               10: {2: '●', 4: '●', 9: '●'}, 11: {2: '○', 4: '●', 8: '○'}, 12: {4: '●', 9: '●', 10: '●'}}

# The paper's own table of where each rule fires (GEN_HEP paper, Table "Where each rule fires", sec_laws.tex)
PAPER_TABLE = {1: [2], 2: [4, 5, 6, 7, 8, 11, 9, 10], 3: [4], 4: [5, 6, 7, 8, 9, 10, 11, 12], 5: [6, 7, 8],
               6: [8, 7], 7: [9], 8: [7, 9, 11], 9: [5, 6, 7, 9, 10], 10: [12]}


def unexplained(g: Graph) -> Set[str]:
    """O nodes with no incoming single route of kind predicts/calibrates/frames from the model layer (weak and candidate excluded)."""
    explained: Set[str] = set()
    for r in g.routes.values():
        if r.logic == "single" and r.kind in ("predicts", "calibrates", "frames") and not r.extra.get("weak") and g.layer_of(r.inputs[0]) == "M":
            explained.add(r.target)
    return {n.uid for n in g.nodes_in("O")} - explained


def calibration_sources(g: Graph) -> Dict[str, Set[str]]:
    by_o: Dict[str, Set[str]] = {}
    for r in g.routes.values():
        if r.kind == "calibrates":
            by_o.setdefault(r.target, set()).add(r.inputs[0])
    return by_o


def shared_calibrations(g: Graph) -> List[Tuple[str, str, str]]:
    out = []
    for o, ms in calibration_sources(g).items():
        ms = sorted(ms)
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                out.append((ms[i], ms[j], o))
    return out


def and_routes(g: Graph) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for r in g.routes.values():
        if r.logic == "AND":
            out.setdefault(r.target, []).append({"legs": r.extra.get("legs"), "inputs": r.inputs, "label": r.extra.get("label"), "kind": r.kind})
    return out


def kind_of(g: Graph, uid: str) -> str:
    return g.nodes[uid].extra.get("kind") or ""


def canon_uir(g: Graph, uid: str) -> str:
    u = g.nodes[uid].extra.get("uir") or ""
    return re.sub(r"[\s±∓+−-]", "", u)


def badge(g: Graph, uid: str) -> str:
    return g.nodes[uid].extra.get("driver") or ""


def step_counts(g: Graph) -> Dict[str, Any]:
    M = g.nodes_in("M")
    return {
        "S": len(g.nodes_in("S")), "M": len(M), "O": len(g.nodes_in("O")),
        "routes_expanded": len(g.routes),
        "AND": sum(1 for r in g.routes.values() if r.logic == "AND"),
        "unexplained": sorted(x.split(":")[1] for x in unexplained(g)),
        "eff": sum(1 for n in M if n.extra.get("kind") == "eff"),
        "fund": sum(1 for n in M if n.extra.get("kind") == "fund"),
        "cand": sum(1 for n in M if n.extra.get("kind") == "cand"),
        "cluster": sum(1 for n in M if n.extra.get("kind") == "cluster"),
        "calibrations": sum(1 for r in g.routes.values() if r.kind == "calibrates"),
        "predictions": sum(1 for r in g.routes.values() if r.kind == "predicts"),
        "badges": {b: sum(1 for n in g.nodes_in("O") if badge(g, n.uid) == b) for b in "APF"},
        "shared_calibrations": [(a.split(":")[1], b.split(":")[1], o.split(":")[1]) for a, b, o in shared_calibrations(g)],
    }


def diff_steps(g0: Graph, g1: Graph) -> Dict[str, Any]:
    d: Dict[str, Any] = {"ops": [], "rules": {}}
    short = lambda u: u.split(":")[1]
    fmt = lambda us: ", ".join(short(u) for u in us)
    for L in "SMO":
        a = {n.uid for n in g0.nodes_in(L)}; b = {n.uid for n in g1.nodes_in(L)}
        d[f"added_{L}"] = sorted(b - a); d[f"removed_{L}"] = sorted(a - b)
    key = lambda r: (r.kind, tuple(r.inputs), r.target)
    k0 = {key(r) for r in g0.routes.values()}; k1 = {key(r) for r in g1.routes.values()}
    d["added_routes"] = sorted(k1 - k0); d["removed_routes"] = sorted(k0 - k1)
    unexp0 = unexplained(g0); unexp1 = unexplained(g1)
    d["unexplained_before"] = sorted(map(short, unexp0)); d["unexplained_after"] = sorted(map(short, unexp1))
    d["newly_unexplained"] = sorted(map(short, unexp1 - unexp0))
    added_M, removed_M, added_S, removed_S = d["added_M"], d["removed_M"], d["added_S"], d["removed_S"]
    rules = d["rules"]; ops = d["ops"]

    # ---------------------------------------------------------------- state layer: R1, R3, R8
    back_targets = {r.target for r in g1.routes.values() if r.kind == "backedge"}
    new_back = {r.target for r in g1.routes.values() if r.kind == "backedge" and r.inputs[0] in added_M}
    if removed_S and len(added_S) >= 2 and all(kind_of(g1, s) == "uir" for s in added_S) and set(added_S) <= back_targets:
        rules[1] = "●"; ops.append(("PARTITION", "S", f"{fmt(removed_S)} -> {len(added_S)} irreducible classes (back-edge of a rewritten model node)"))
    if added_S and all(kind_of(g1, s) == "sector" for s in added_S) and any(kind_of(g0, s) == "uir" for s in removed_S) and new_back >= set(added_S):
        rules[3] = "●"; ops.append(("EXTEND", "S", f"{len(removed_S)} classes -> {len(added_S)} sectors with ladders, by the back-edge of {fmt(added_M)}"))
    # sector refinement: split (1 -> >=2 with the same irreducible block) / replace (k -> k with the same blocks); other added sectors are new (mediators etc.)
    sector_map: Dict[str, Set[str]] = {}   # removed sector -> set of successor sectors (same irreducible block)
    replace_classes: List[Tuple[Set[str], Set[str]]] = []   # (removed set, added set) with the same irreducible block, k -> k
    sec_removed = [s for s in removed_S if kind_of(g0, s) == "sector"]
    sec_added = [s for s in added_S if kind_of(g1, s) == "sector" and s not in new_back]
    by_uir_removed: Dict[str, List[str]] = {}
    by_uir_added: Dict[str, List[str]] = {}
    for s in sec_removed: by_uir_removed.setdefault(canon_uir(g0, s), []).append(s)
    for t in sec_added: by_uir_added.setdefault(canon_uir(g1, t), []).append(t)
    succ_used: Set[str] = set()
    splits: Dict[str, Set[str]] = {}
    for u, rem in by_uir_removed.items():
        add = by_uir_added.get(u, [])
        if not add:
            continue
        if len(rem) == 1 and len(add) >= 2:
            splits[rem[0]] = set(add); sector_map[rem[0]] = set(add); succ_used |= set(add)
        elif len(rem) == len(add):
            replace_classes.append((set(rem), set(add)))
            for r_ in rem: sector_map[r_] = set(add)
            succ_used |= set(add)
    new_sectors = [t for t in sec_added if t not in succ_used]
    d["sector_map"] = {short(k): sorted(map(short, v)) for k, v in sector_map.items()}
    d["new_sectors"] = sorted(map(short, new_sectors))
    if splits:
        rules[8] = "●"
        for k, v in splits.items():
            ops.append(("SPLIT", "S", f"{short(k)} -> {fmt(sorted(v))} (same irreducible block, distinguished by an observable)"))
    if replace_classes:
        rules[8] = "●"
        for rem, add in replace_classes:
            ops.append(("REPLACE", "S", f"{fmt(sorted(rem))} -> {fmt(sorted(add))} (same irreducible blocks: compositeness)"))
    if rules.get(1) == "●":
        rules[8] = "●"
    if new_sectors:
        ops.append(("ADD", "S", f"new sector(s) {', '.join(d['new_sectors'])}"))

    # ---------------------------------------------------------------- model layer: R2, R5, R6, R7, R10
    real_added_M = [m for m in added_M if kind_of(g1, m) not in ("cand", "cluster")]
    cand_added_M = [m for m in added_M if kind_of(g1, m) == "cand"]
    cl_added = [m for m in added_M if kind_of(g1, m) == "cluster"]
    reach = lambda ms, o: any(r.target == o and r.inputs[0] in ms and r.kind in ("predicts", "calibrates") and r.logic == "single" for r in g1.routes.values())
    if real_added_M:
        reached_old = [short(o) for o in unexp0 if o in g1.nodes and reach(real_added_M, o)]
        replaced_deficit = [short(o) for o in unexp0 if o not in g1.nodes]
        same_step_A = [short(n.uid) for n in g1.nodes_in("O") if n.uid in d["added_O"] and badge(g1, n.uid) == "A" and reach(real_added_M, n.uid)]
        if unexp0 or same_step_A:
            rules[2] = "●"; d["r2_form"] = "anomaly"
            msg = f"{fmt(real_added_M)}"
            if reached_old: msg += f"; reaches the open deficit {', '.join(reached_old)}"
            if replaced_deficit: msg += f"; deficit {', '.join(replaced_deficit)} rewritten into finer observables"
            if same_step_A: msg += f"; explains the observed-before-explained {', '.join(same_step_A)}"
            ops.append(("ADD", "M", msg))
        else:
            rules[2] = "●"; d["r2_form"] = "theory-internal"
            ops.append(("ADD", "M", f"{fmt(real_added_M)} with no unexplained observable before the step: theory-internal form; new P-badged observables " + ", ".join(short(n.uid) for n in g1.nodes_in('O') if n.uid in d['added_O'] and badge(g1, n.uid) == 'P')))
    elif cand_added_M:
        rules[2] = "○"; d["r2_form"] = "announced"
        ops.append(("ADD", "M(cand)", f"candidate node {fmt(cand_added_M)}: hypothesis announced, not established"))
    elif d["newly_unexplained"]:
        rules[2] = "○"; d["r2_form"] = "flagged"
        ops.append(("FLAG", "O", f"new unexplained observable {', '.join(d['newly_unexplained'])}: precondition of R2"))

    eff_added = [m for m in added_M if kind_of(g1, m) == "eff"]
    if eff_added:
        rules[5] = "●"; ops.append(("ADD", "M(eff)", f"effective node(s) {fmt(eff_added)}: dimensionful coupling, temporary by construction"))

    # leg-set comparison modulo the sector map (successors stand for their predecessor)
    def legclass(uid: str, gref: Graph) -> str:
        for rem, add in replace_classes:
            if uid in rem or uid in add:
                return "cls:" + "+".join(sorted(map(short, rem)))
        for k, v in splits.items():
            if uid == k or uid in v:
                return "cls:" + short(k)
        return uid
    ar0 = and_routes(g0); ar1 = and_routes(g1)
    def sets_of(ar, g):
        return {(t, frozenset(legclass(u, g) for u in r["inputs"])) for t, rs in ar.items() for r in rs}
    s0 = sets_of(ar0, g0); s1 = sets_of(ar1, g1)

    # R6 merge: >= 2 model nodes removed, one added, union of their routes (modulo sector map) inside the new node's routes
    eff_removed = [m for m in removed_M if kind_of(g0, m) == "eff"]
    if len(removed_M) >= 2 and len(real_added_M) == 1:
        m_new = real_added_M[0]
        union = {legs for t, legs in s0 if t in removed_M}
        new_sets = {legs for t, legs in s1 if t == m_new}
        if union and union <= new_sets:
            rules[6] = "●"; ops.append(("MERGE", "M", f"{fmt(removed_M)} -> {short(m_new)}: {len(union)} routes (union) contained in the {len(new_sets)} routes of the merged node"))
    # R6 prepared: two coexisting model nodes share a calibration edge, or the calibration of one observable is transferred to a second node while the first persists
    cs0 = calibration_sources(g0); cs1 = calibration_sources(g1)
    transfer = []
    for o, ms1 in cs1.items():
        ms0 = cs0.get(o, set())
        moved_from = [m for m in ms0 if m not in ms1 and m in g1.nodes and kind_of(g1, m) in ("eff", "fund")]
        moved_to = [m for m in ms1 if m not in ms0 and m in added_M]
        if moved_from and moved_to:
            transfer.append((sorted(map(short, moved_from)), sorted(map(short, moved_to)), short(o)))
    if 6 not in rules and (shared_calibrations(g1) or transfer):
        rules[6] = "○"
        tdesc = "; ".join(f"{o}: {', '.join(a)} -> {', '.join(b)}" for a, b, o in transfer) if transfer else str(step_counts(g1)["shared_calibrations"])
        ops.append(("SIGNAL", "M", f"calibration edge transferred between coexisting nodes ({tdesc}): a merge is due"))

    # R7 absorption: an effective node removed, fundamental node(s) added together with new sector(s); every old route is covered by the
    # union of new routes with the new-sector (mediator) legs removed
    fund_added = [m for m in added_M if kind_of(g1, m) == "fund"]
    if eff_removed and fund_added and new_sectors and 6 not in rules:
        old_sets = {legs for t, legs in s0 if t in eff_removed}
        new_sets_by_fund = {m: [legs for t, legs in s1 if t == m] for m in fund_added}
        mediators: Set[str] = set(); covered = 0
        for os_ in old_sets:
            best = None
            for m, legsets in new_sets_by_fund.items():
                stripped = [legs - set(new_sectors) for legs in legsets]
                cover = frozenset().union(*stripped) if stripped else frozenset()
                if os_ <= cover:
                    best = m; mediators |= {u for legs in legsets for u in legs if u in new_sectors}
            if best: covered += 1
        if covered == len(old_sets) and old_sets:
            rules[7] = "●"
            ops.append(("ABSORB", "M", f"{fmt(eff_removed)} absorbed into {fmt(fund_added)}: each of the {len(old_sets)} old routes is covered by new routes once the mediator leg(s) {fmt(sorted(mediators))} are removed"))

    # R4 route composition (genuinely new routes, re-attachments listed separately)
    members: Dict[str, str] = {}
    for c in (g1.clusters or []):
        for m in c.get("members", []):
            members[f"HEP:{m}"] = f"HEP:{c['id']}"
    truly_new = []; reattached = []
    for t, legs in s1 - s0:
        prev = [(t0, l0) for (t0, l0) in s0 if l0 == legs]
        if any(members.get(t0) == t for t0, _ in prev):
            reattached.append((t, legs))
        else:
            truly_new.append((t, legs))
    d["new_and_routes"] = len(truly_new); d["reattached_and_routes"] = len(reattached)
    if truly_new or reattached:
        rules[4] = "●"
        if truly_new:
            raw_legs = {(t, frozenset(legclass(u, g1) for u in r["inputs"])): len(r["inputs"]) for t, rs in ar1.items() for r in rs}
            ops.append(("ROUTE", "S->M", f"{len(truly_new)} new AND route(s): " + "; ".join(sorted(f"{short(t)} <- {raw_legs.get((t, legs), len(legs))} leg(s)" for t, legs in truly_new))))
        if reattached:
            ops.append(("ROUTE", "S->M", f"{len(reattached)} route(s) re-attached to clusters"))

    # R9 calibration
    new_cal = sorted({k[2] for k in d["added_routes"] if k[0] == "calibrates"})
    new_cal_obs = [short(o) for o in new_cal if o not in cs0]
    if new_cal:
        rules[9] = "●"
        ops.append(("CALIBRATE", "O->M", f"calibration edge(s) added for {fmt(new_cal)}" + (f"; new parameter(s): {', '.join(new_cal_obs)}" if new_cal_obs else "; re-attached only")))
    # R10 clustering
    if cl_added:
        rules[10] = "●"; ops.append(("CLUSTER", "M", f"{len(cl_added)} clusters: {fmt(cl_added)}; absorbed members: " + ", ".join(m for c in (g1.clusters or []) for m in c.get('members', []) if f'HEP:{m}' not in g1.nodes)))
    return d


def replay() -> Dict[str, Any]:
    br, steps, raw = load_hep_steps()
    out: Dict[str, Any] = {"steps": [], "diffs": [], "auto_matrix": {}, "hand_matrix": HAND_MATRIX, "comparison": {}}
    for g in steps:
        c = step_counts(g)
        c["records"] = len(raw["steps"][g.step["index"] - 1]["edges"])
        c["and_records"] = len(raw["steps"][g.step["index"] - 1].get("ands", []))
        c["id"] = g.step["id"]; c["index"] = g.step["index"]; c["driver"] = g.step.get("driver"); c["title"] = g.step["title"]
        out["steps"].append(c)
    out["auto_matrix"][1] = {}
    for i in range(1, len(steps)):
        d = diff_steps(steps[i - 1], steps[i])
        d["index"] = steps[i].step["index"]; d["id"] = steps[i].step["id"]; d["driver"] = steps[i].step.get("driver")
        d["recorded_ops"] = steps[i].step.get("ops")
        out["diffs"].append(d)
        out["auto_matrix"][d["index"]] = {k: v for k, v in sorted(d["rules"].items())}
    agree = disagree = 0; details = []
    paper_agree = paper_disagree = 0; paper_details = []
    for k in range(1, 13):
        for r in range(1, 11):
            a = out["auto_matrix"].get(k, {}).get(r, ""); h = HAND_MATRIX[k].get(r, "")
            if a == h: agree += 1
            else:
                disagree += 1; details.append({"step": k, "rule": r, "auto": a, "hand": h})
            p = "●" if k in PAPER_TABLE[r] else ""
            a_fire = "●" if a == "●" else ""
            if a_fire == p: paper_agree += 1
            else:
                paper_disagree += 1; paper_details.append({"step": k, "rule": r, "auto": a, "paper_table": p})
    out["comparison"] = {"cells": 120, "agree": agree, "disagree": disagree, "details": details,
                         "paper_table_agree": paper_agree, "paper_table_disagree": paper_disagree, "paper_table_details": paper_details}
    inv = {"S_to_S_routes": 0, "O_as_input": 0, "m2o_from_nonM": 0, "and_routes_with_nonS_leg": 0, "and_routes_into_nonM": 0, "routes_checked": 0}
    for g in steps:
        for r in g.routes.values():
            inv["routes_checked"] += 1
            tl = g.layer_of(r.target); il = [g.layer_of(u) for u in r.inputs]
            if tl == "S" and any(x == "S" for x in il): inv["S_to_S_routes"] += 1
            if any(x == "O" for x in il): inv["O_as_input"] += 1
            if r.logic == "single" and r.kind in ("predicts", "calibrates", "frames", "candidate") and any(x != "M" for x in il): inv["m2o_from_nonM"] += 1
            if r.logic == "AND" and any(x != "S" for x in il): inv["and_routes_with_nonS_leg"] += 1
            if r.logic == "AND" and tl != "M": inv["and_routes_into_nonM"] += 1
    out["invariants"] = inv
    out["driver_consistency"] = [{"step": d["index"], "id": d["id"], "driver": d["driver"], "deficit_before": bool(d["unexplained_before"]), "r2_form": d.get("r2_form")} for d in out["diffs"]]
    # count trajectories across steps
    out["trajectories"] = {k: [s[k] for s in out["steps"]] for k in ("S", "M", "O", "AND", "eff", "fund", "cluster", "calibrations", "predictions")}
    out["trajectories"]["unexplained"] = [len(s["unexplained"]) for s in out["steps"]]
    out["removals"] = [{"step": d["index"], "removed_S": list(map(lambda u: u.split(":")[1], d["removed_S"])), "removed_M": list(map(lambda u: u.split(":")[1], d["removed_M"])), "removed_O": list(map(lambda u: u.split(":")[1], d["removed_O"]))}
                       for d in out["diffs"] if d["removed_S"] or d["removed_M"] or d["removed_O"]]
    return out


# ---------------------------------------------------------------------------
# Cumulative view: observables persist; model->observable routes persist through successor nodes
# ---------------------------------------------------------------------------
def successor_map(steps: List[Graph]) -> Dict[str, str]:
    """Removed model node -> successor model node, derived from the data:
    (i) a step that removes k model nodes and adds exactly one: the added node (merge / absorption into one);
    (ii) lineage edges recorded in the final clusters; (iii) cluster membership at the final step."""
    succ: Dict[str, str] = {}
    for i in range(1, len(steps)):
        g0, g1 = steps[i - 1], steps[i]
        rem = [n.uid for n in g0.nodes_in("M") if n.uid not in g1.nodes]
        add = [n.uid for n in g1.nodes_in("M") if n.uid not in g0.nodes and kind_of(g1, n.uid) != "cluster"]
        if rem and len(add) == 1:
            for m in rem:
                succ[m] = add[0]
    final = steps[-1]
    for c in final.clusters or []:
        for l in c.get("lineage", []):
            succ.setdefault(f"HEP:{l['f']}", f"HEP:{l['t']}")
        for m in c.get("members", []):
            if m != c["id"]:
                succ.setdefault(f"HEP:{m}", f"HEP:{c['id']}")
    return succ


def resolve(uid: str, succ: Dict[str, str], alive: Set[str]) -> str:
    seen = set()
    while uid not in alive and uid in succ and uid not in seen:
        seen.add(uid); uid = succ[uid]
    return uid


def observable_families(steps: List[Graph]) -> Dict[str, Set[str]]:
    """Family head -> members, read from the 'sub' typing of the observables (σ-type / Γ-type) and the Step-4 rewrite."""
    fam: Dict[str, Set[str]] = {"HEP:o_sig": set(), "HEP:o_G": set(), "HEP:o_prod": {"HEP:o_sig", "HEP:o_G"}}
    for g in steps:
        for n in g.nodes_in("O"):
            sub = n.extra.get("sub") or ""
            if n.uid != "HEP:o_sig" and "σ-type" in sub: fam["HEP:o_sig"].add(n.uid)
            if n.uid != "HEP:o_G" and "Γ-type" in sub: fam["HEP:o_G"].add(n.uid)
    return fam


def cumulative(steps: List[Graph]) -> List[Dict[str, Any]]:
    """For each step: the cumulative observable layer and the persistent model->observable routes.
    A family head (σ, Γ, production) counts as explained when at least one member is explained."""
    succ = successor_map(steps)
    fam = observable_families(steps)
    out = []
    seen_O: Dict[str, Any] = {}
    m2o: Dict[Tuple[str, str], Dict[str, Any]] = {}   # (source, target) -> record (latest kind)
    cal_history: Set[str] = set()
    for g in steps:
        for n in g.nodes_in("O"):
            seen_O[n.uid] = n
        for r in g.routes.values():
            if r.logic == "single" and r.kind in ("predicts", "calibrates", "frames", "candidate") and not r.extra.get("weak"):
                m2o[(r.inputs[0], r.target)] = {"kind": r.kind, "step": g.step["index"]}
                if r.kind == "calibrates":
                    cal_history.add(r.target)
        alive = set(g.nodes)
        explained: Set[str] = set(); explained_by: Dict[str, Set[str]] = {}
        resolved_routes = []
        for (src, tgt), rec in m2o.items():
            s2 = resolve(src, succ, alive)
            if s2 in alive and rec["kind"] in ("predicts", "calibrates", "frames"):
                explained.add(tgt); explained_by.setdefault(tgt, set()).add(s2)
                resolved_routes.append((s2, tgt, rec["kind"]))
        changed = True
        while changed:
            changed = False
            for head, members in fam.items():
                if head in seen_O and head not in explained and any(m in explained for m in members):
                    explained.add(head); explained_by[head] = {"family:" + ",".join(sorted(x.split(":")[1] for x in members if x in explained))}; changed = True
        unexp = sorted(o.split(":")[1] for o in seen_O if o not in explained)
        badges = {b: sum(1 for o in seen_O.values() if (o.extra.get("driver") or "") == b) for b in "APF"}
        out.append({"step": g.step["index"], "id": g.step["id"], "O_cumulative": len(seen_O), "O_shown": len(g.nodes_in("O")),
                    "unexplained_cumulative": unexp, "routes_m2o_cumulative": len(resolved_routes),
                    "calibrated_parameters_so_far": sorted(o.split(":")[1] for o in cal_history), "badges_cumulative": badges,
                    "explained_by": {o.split(":")[1]: sorted(x.split(":")[1] for x in ms) for o, ms in explained_by.items()}})
    return out


def final_predictive_content(steps: List[Graph]) -> Dict[str, Any]:
    """Rule 9 on the final cumulative graph: per cluster, observable edges minus calibration edges."""
    cum = cumulative(steps)
    succ = successor_map(steps); final = steps[-1]; alive = set(final.nodes)
    per: Dict[str, Dict[str, Any]] = {}
    m2o: Dict[Tuple[str, str], str] = {}
    for g in steps:
        for r in g.routes.values():
            if r.logic == "single" and r.kind in ("predicts", "calibrates", "frames") and not r.extra.get("weak"):
                m2o[(r.inputs[0], r.target)] = r.kind
    for (src, tgt), kind in m2o.items():
        s2 = resolve(src, succ, alive)
        if s2 not in alive:
            continue
        rec = per.setdefault(s2.split(":")[1], {"pred": set(), "fit": set(), "frame": set()})
        rec[{"predicts": "pred", "calibrates": "fit", "frames": "frame"}[kind]].add(tgt.split(":")[1])
    for k, rec in per.items():
        # an observable both calibrated and predicted counts as calibration (the parameter is read off it)
        rec["pred"] -= rec["fit"]
        rec["n_pred"] = len(rec["pred"]); rec["n_fit"] = len(rec["fit"]); rec["n_frame"] = len(rec["frame"])
        rec["predictive_content"] = rec["n_pred"] - 0  # predictions beyond calibration (Rule 9: edges minus parameters)
        rec["pred"] = sorted(rec["pred"]); rec["fit"] = sorted(rec["fit"]); rec["frame"] = sorted(rec["frame"])
    return {"per_node": per, "cumulative": cum}
