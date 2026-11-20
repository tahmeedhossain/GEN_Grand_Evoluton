"""Build the evolutionary analyses: dated branches, growth decompositions, rules on the year axis,
the merged four-branch evolutionary network, and the numbers for the thesis (Part II).

    python3 build_evolution.py   # writes out/evolution.json, data/gen_evolution_network.json, thesis/numbers_evo.tex
"""
from __future__ import annotations
import json, os, sys, datetime, re
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from gen_engine.chrono import dated_graphs_union, provenance_summary, hep_raw, PROJECT_YEAR
from gen_engine.evolution import (FOUR, PHASES, cumulative_curve, growth_decomposition, densification, preferential_attachment,
                                  witness_effect_timing, explanation_lag, first_edge_polarity, layer_lead, concept_table, merged_curve,
                                  decade_table, merged_phase_table, hep_rules_by_year, phase_of_route, phase_of_node, year_of)
from gen_engine.schema import dump
from gen_engine.glue import CONCEPTS

OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)

# rule attribution of a route by branch and kind (for the rules x decade table)
def rule_of_route(b: str, r) -> str:
    if b == "EM":
        return "R12 fail" if r.kind == "failed" else "R11 derive"
    if b == "HEP":
        if r.kind_native in ("cluster_member", "cluster_lineage", "m2m"):
            return "R7/R10 absorb-cluster"
        return {"enters": "R4 route", "predicts": "R2 drive/predict", "calibrates": "R9 calibrate", "frames": "R2 frame", "candidate": "R2 announce",
                "backedge": "R1/R3 partition-extend", "lineage": "R7/R10 absorb-cluster", "subset": "O-cluster (family)"}.get(r.kind, r.kind)
    # type E
    return {"structural": "R14 close (structural)", "possibility": "R14 close (possibility)", "no_go": "R14 close (no-go)", "open": "R13 open cell"}[r.polarity]


def designated_pairs(g):
    pairs = set()
    for r in g.routes.values():
        a = g.nodes[r.inputs[0]].native_layer.split("/")[0]; b = g.nodes[r.target].native_layer.split("/")[0]
        pairs.add(tuple(sorted((a, b))))
    return pairs


def census_trajectory(g, years):
    """Pair census among present nodes restricted to the designated native-layer pairs: open cells over time."""
    des = designated_pairs(g)
    out = []
    nodes = list(g.nodes.values())
    for T in years:
        present = [n for n in nodes if year_of(n) <= T]
        by_layer = Counter(n.native_layer.split("/")[0] for n in present)
        cells = 0
        for (a, b) in des:
            if a == b:
                cells += by_layer[a] * (by_layer[a] - 1) // 2
            else:
                cells += by_layer[a] * by_layer[b]
        connected = set()
        for r in g.routes.values():
            if year_of(r) <= T:
                connected.add(frozenset((r.inputs[0], r.target)))
        out.append({"year": T, "cells": cells, "connected": len(connected), "open": cells - len(connected)})
    return out


def main():
    gs, logs = dated_graphs_union()
    R = {"generated": datetime.datetime.now().isoformat(timespec="seconds"), "provenance": provenance_summary(gs), "logs": {b: {k: v for k, v in logs[b].items() if k not in ("edges", "nodes", "paragraphs", "routes")} for b in gs}}
    per = {}
    for b in FOUR:
        g = gs[b]
        cur = cumulative_curve(g)
        dec = growth_decomposition(g)
        rec = {"years": [cur[0]["year"], cur[-1]["year"]], "curve": cur, "decomposition": {k: v for k, v in dec.items() if k != "rows"},
               "rows": [{**r, "arrivals_by_layer": dict(r["arrivals_by_layer"]), "polarity": dict(r["polarity"]), "phases_routes": dict(r["phases_routes"]), "phases_nodes": dict(r["phases_nodes"])} for r in dec["rows"]],
               "densification": densification(cur), "preferential": preferential_attachment(g), "layer_half": layer_lead(cur), "first_edge_polarity": first_edge_polarity(g)}
        if b in ("GPT", "QRT"):
            rec["witness_effect"] = witness_effect_timing(g); rec["explanation_lag"] = explanation_lag(g)
            rec["census"] = census_trajectory(g, [c["year"] for c in cur])
            rec["designated_pairs"] = sorted("|".join(p) for p in designated_pairs(g))
        if b == "HEP":
            rec["removed_nodes"] = logs["HEP"]["removed_nodes"]; rec["removed_routes"] = logs["HEP"]["removed_routes"]
            from gen_engine.chrono import _first_year
            raw_steps = hep_raw()["steps"]
            rec["removal_years"] = None  # filled below from the network file (same placement rule)
            rec["route_removal_years"] = None
            rec["removals_by_step"] = sorted(Counter(n.extra["step_last"] + 1 for n in g.nodes.values() if n.extra["removed"]).items())
        # rules x decade
        rd = defaultdict(Counter)
        for r in g.routes.values():
            rd[(year_of(r) // 10) * 10][rule_of_route(b, r)] += 1
        rec["rules_by_decade"] = {str(d): dict(c) for d, c in sorted(rd.items())}
        per[b] = rec
    R["branches"] = per
    # robustness: the effect networks dated by the LATEST cited source of each edge (upper bound) instead of the earliest
    from gen_engine.chrono import load_gpt, load_qrt, date_type_E
    rob = {}
    for b, loader in (("GPT", load_gpt), ("QRT", load_qrt)):
        g2 = loader(); date_type_E(g2, "max")
        cur2 = cumulative_curve(g2); dec2 = growth_decomposition(g2)
        rob[b] = {"years": [cur2[0]["year"], cur2[-1]["year"]], "V": cur2[-1]["V"], "E": cur2[-1]["E"], "n_closures": dec2["n_closures"], "closure_fraction": dec2["closure_fraction"],
                  "latency_mean": dec2["latency_mean"], "latency_median": dec2["latency_median"], "latency_max": dec2["latency_max"], "identity_holds": dec2["identity"]["holds"],
                  "mean_degree_at_arrival": dec2["mean_degree_at_arrival"], "densification": densification(cur2), "preferential": preferential_attachment(g2),
                  "layer_half": layer_lead(cur2), "witness_effect": {k: v for k, v in witness_effect_timing(g2).items() if k != "rows"},
                  "explanation_lag": {k: v for k, v in explanation_lag(g2).items() if k != "rows"}, "provenance": provenance_summary({b: g2})[b]}
        # node-year differences between the two conventions
        g1 = gs[b]
        diffs = [year_of(g2.nodes[u]) - year_of(g1.nodes[u]) for u in g1.nodes]
        rob[b]["node_shift_mean"] = sum(diffs) / len(diffs); rob[b]["node_shift_max"] = max(diffs); rob[b]["node_shift_zero"] = sum(1 for d in diffs if d == 0)
    R["robustness_max_dating"] = rob
    # HEP rule firings on the year axis
    hep_rep = json.load(open(os.path.join(OUT, "hep_replay.json")))
    R["hep_rules_by_year"] = hep_rules_by_year(hep_rep, hep_raw()["steps"])
    # merged
    ct = concept_table(gs)
    # flag project/review-dated members
    for c in ct:
        flags = {}; dated = {}
        for b in c["branches"]:
            for cid_, label, members, note in CONCEPTS:
                if cid_ == c["id"]:
                    provs = [(gs[b].nodes[f"{b}:{i}"].extra.get("year_prov", ""), year_of(gs[b].nodes[f"{b}:{i}"])) for i in members.get(b, [])]
                    flags[b] = sorted(set(p.split(":")[0] for p, y in provs))
                    ys = [y for p, y in provs if p.split(":")[0] != "project"]
                    if ys:
                        dated[b] = min(ys)
        c["prov"] = flags
        c["years_dated"] = dated
        c["lag_dated"] = (max(dated.values()) - min(dated.values())) if len(dated) >= 2 else None
        c["first_dated"] = min(dated, key=dated.get) if dated else None
    R["concepts"] = ct
    R["merged_curve"] = merged_curve(gs, ct)
    R["decade_table"] = decade_table(gs)
    R["merged_phases"] = merged_phase_table(gs)
    # merged identity: V = sum of branch V; glue; collapsed
    last = R["merged_curve"][-1]
    R["merged_final"] = last
    dump(R, os.path.join(OUT, "evolution.json"))
    # the evolutionary network data file
    net = {"schema": "gen-evolution/1", "title": "Four-branch evolutionary network on the calendar axis (EM, HEP, GPT, QRT)",
           "generated": datetime.date.today().isoformat(),
           "dating_rules": __import__("gen_engine.chrono", fromlist=["__doc__"]).__doc__,
           "branches": [gs[b].branch.__dict__ for b in FOUR],
           "nodes": [{"uid": n.uid, "branch": n.branch, "native_id": n.native_id, "label": n.label, "layer": n.layer, "sublayer": n.sublayer, "native_layer": n.native_layer,
                      "year": year_of(n), "year_prov": n.extra.get("year_prov"), "concept": n.concept, "removed": n.extra.get("removed", False),
                      "step_first": n.extra.get("step_first"), "step_last": n.extra.get("step_last"), "desc": (n.extra.get("description") or n.extra.get("def") or n.extra.get("statement") or n.extra.get("desc") or "")[:400]}
                     for b in FOUR for n in gs[b].nodes.values()],
           "routes": [{"uid": r.uid, "branch": r.branch, "native_id": r.native_id, "inputs": r.inputs, "target": r.target, "logic": r.logic, "kind": r.kind, "kind_native": r.kind_native,
                       "status": r.status, "polarity": r.polarity, "year": year_of(r), "year_prov": r.extra.get("year_prov"), "phase": phase_of_route(r), "rule": rule_of_route(r.branch, r),
                       "removed": r.extra.get("removed", False), "step_first": r.extra.get("step_first"), "step_last": r.extra.get("step_last"),
                       "text": (r.extra.get("rel") or r.extra.get("statement") or r.extra.get("formula") or r.extra.get("title") or r.extra.get("label") or "")[:300]}
                      for b in FOUR for r in gs[b].routes.values()],
           "concepts": ct}
    # removal years of the HEP union (start year of the step after the last step in which the item is present)
    from gen_engine.chrono import _first_year
    raw_steps = hep_raw()["steps"]
    def step_removal_year(k: int) -> int:
        """Year at which step k's removals are placed: its start year; for the final view (step 12) the end of its range."""
        ys = raw_steps[k - 1].get("years") or ""
        yrs = [int(y) for y in re.findall(r"(1[5-9]\d{2}|20[0-2]\d)", ys)]
        return max(yrs) if k == 12 and yrs else (min(yrs) if yrs else PROJECT_YEAR)
    for coll in (net["nodes"], net["routes"]):
        for x in coll:
            if x["branch"] == "HEP" and x["removed"]:
                x["removal_step"] = x["step_last"] + 1
                x["removal_year"] = max(x["year"], step_removal_year(x["removal_step"]))  # a removal cannot precede the arrival
    # attach concept ids to nodes
    member_concept = {}
    for cid, label, members, note in CONCEPTS:
        for b, ids in members.items():
            for i in ids:
                member_concept[f"{b}:{i}"] = cid
    shared_ids = {c["id"] for c in ct}
    for n in net["nodes"]:
        n["concept_any"] = member_concept.get(n["uid"])  # membership in the full gluing catalogue (Part I)
        n["concept"] = member_concept.get(n["uid"]) if member_concept.get(n["uid"]) in shared_ids else None  # shared among the four branches
    R["branches"]["HEP"]["removal_years"] = sorted(Counter(n["removal_year"] for n in net["nodes"] if n.get("removal_year")).items())
    R["branches"]["HEP"]["route_removal_years"] = sorted(Counter(r["removal_year"] for r in net["routes"] if r.get("removal_year")).items())
    dump(R, os.path.join(OUT, "evolution.json"))
    net["counts"] = {"nodes": len(net["nodes"]), "routes": len(net["routes"]), "concepts_shared": len(ct), "V_collapsed_final": last["V_collapsed"], "glue_final": last["glue"]}
    dump(net, os.path.join(HERE, "data", "gen_evolution_network.json"))
    write_numbers(R, gs, net)
    print("done:", net["counts"], {b: (per[b]["years"], per[b]["curve"][-1]["V"], per[b]["curve"][-1]["E"]) for b in FOUR})


def tex_escape(s):
    return str(s).replace("_", "\\_").replace("%", "\\%").replace("&", "\\&").replace("#", "\\#")


def write_numbers(R, gs, net):
    N = {}
    # structural counts used in the philosophy mapping (computed from the network file)
    nodes = {n["uid"]: n for n in net["nodes"]}
    em_der = [r for r in net["routes"] if r["branch"] == "EM" and r["kind"] == "derives"]; em_fail = [r for r in net["routes"] if r["branch"] == "EM" and r["kind"] == "failed"]
    N["emDeriveTotal"] = len(em_der); N["emDeriveAND"] = sum(1 for r in em_der if len(r["inputs"]) >= 2)
    N["emFailedTotal"] = len(em_fail); N["emFailedAND"] = sum(1 for r in em_fail if len(r["inputs"]) >= 2)
    hep_ent = [r for r in net["routes"] if r["branch"] == "HEP" and r["kind"] == "enters"]; N["hepEntersTotal"] = len(hep_ent); N["hepEntersAND"] = sum(1 for r in hep_ent if r["logic"] == "AND")
    hep_pred = [r for r in net["routes"] if r["branch"] == "HEP" and r["kind"] == "predicts"]; N["hepPredictsTotal"] = len(hep_pred)
    N["hepPredictsMO"] = sum(1 for r in hep_pred if all(nodes[u]["layer"] == "M" for u in r["inputs"]) and nodes[r["target"]]["layer"] == "O")
    def sub_counts(b, sub):
        allc = sum(1 for n in net["nodes"] if n["branch"] == b and n["sublayer"] == sub); rem = sum(1 for n in net["nodes"] if n["branch"] == b and n["sublayer"] == sub and n.get("removed"))
        return allc, rem
    for sub, key in (("O.direct", "Odirect"), ("S.uir", "Suir"), ("M.fund", "Mfund"), ("M.frame", "Mframe"), ("M.cluster", "Mcluster"), ("M.eff", "Meff"), ("M.cand", "Mcand"), ("S.sector", "Ssector")):
        a, r_ = sub_counts("HEP", sub); N[f"hep{key}All"] = a; N[f"hep{key}Removed"] = r_
    # every removed model node of the history is the source of a reduce route (lineage or cluster membership)?
    rem_m = [n for n in net["nodes"] if n["branch"] == "HEP" and n["layer"] == "M" and n.get("removed")]
    reduce_src = {u for r in net["routes"] if r["branch"] == "HEP" and r["kind"] in ("lineage", "subset") and r["kind_native"] in ("cluster_lineage", "cluster_member", "m2m") for u in r["inputs"]}
    N["hepRemovedModel"] = len(rem_m); N["hepRemovedModelWithReduce"] = sum(1 for n in rem_m if n["uid"] in reduce_src)
    N["hepReduceRoutes"] = sum(1 for r in net["routes"] if r["branch"] == "HEP" and r["kind"] in ("lineage", "subset") and r["kind_native"] != "observable_family")
    N["gptAxioms"] = sum(1 for n in net["nodes"] if n["branch"] == "GPT" and n["sublayer"] == "M.axiom"); N["qrtAxioms"] = sum(1 for n in net["nodes"] if n["branch"] == "QRT" and n["sublayer"] == "M.axiom")
    fp = R["branches"]["GPT"]["first_edge_polarity"]["M"]; N["gptMnoGoFirst"] = fp.get("no_go", 0); N["gptMtotal"] = sum(fp.values())
    N["gptMnoGoAny"] = sum(v for k, v in fp.items() if "no_go" in k)
    lagrows = {x["effect"]: x["lag_model"] for x in R["branches"]["GPT"]["explanation_lag"]["rows"]}
    N["gptLagBell"] = lagrows.get("e-bell", "--"); N["gptLagKD"] = lagrows.get("e-kd", "--")
    N["gptLagZero"] = sum(1 for x in R["branches"]["GPT"]["explanation_lag"]["rows"] if x["lag_model"] == 0)
    digits = {"0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four", "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"}
    def mname(k): return "".join(digits.get(ch, ch) for ch in k if ch.isalnum())
    for b in FOUR:
        p = R["branches"][b]; d = p["decomposition"]; cur = p["curve"][-1]
        N[f"{b}Y0"] = p["years"][0]; N[f"{b}Y1"] = p["years"][1]; N[f"{b}Vfin"] = cur["V"]; N[f"{b}Efin"] = cur["E"]
        N[f"{b}Closures"] = d["n_closures"]; N[f"{b}ClosureFrac"] = f"{100*d['closure_fraction']:.0f}"; N[f"{b}LatMean"] = f"{d['latency_mean']:.1f}" if d["latency_mean"] is not None else "--"
        N[f"{b}LatMedian"] = d["latency_median"] if d["latency_median"] is not None else "--"; N[f"{b}LatMax"] = d["latency_max"] if d["latency_max"] is not None else "--"
        N[f"{b}SumArrDeg"] = d["identity"]["sum_arrival_degree"]; N[f"{b}Excess"] = d["identity"]["excess_multi_arrival"]; N[f"{b}IdentityHolds"] = "yes" if d["identity"]["holds"] else "no"
        N[f"{b}MeanArrDeg"] = f"{d['mean_degree_at_arrival']:.2f}"; N[f"{b}ArrDegZero"] = d["degree_at_arrival"].get(0, 0)
        N[f"{b}Alpha"] = f"{p['densification']['alpha']:.2f}" if p["densification"]["alpha"] else "--"; N[f"{b}AlphaR"] = f"{p['densification']['r2']:.2f}" if p["densification"]["r2"] else "--"
        N[f"{b}PAratio"] = f"{p['preferential']['ratio']:.2f}" if p["preferential"]["ratio"] else "--"; N[f"{b}PAn"] = p["preferential"]["n_closure"]
        for L in "SMO":
            N[f"{b}Half{L}"] = p["layer_half"][L]
        for prov, n in R["provenance"][b].items():
            N[f"{b}Prov{prov}"] = n
    g = R["branches"]["GPT"]; N["gptPairs"] = g["witness_effect"]["pairs"]; N["gptPairsSame"] = g["witness_effect"]["same_year"]; N["gptPairsWfirst"] = g["witness_effect"]["witness_first"]; N["gptPairsEfirst"] = g["witness_effect"]["effect_first"]
    N["gptEffects"] = g["explanation_lag"]["effects"]; N["gptEffectsWithM"] = g["explanation_lag"]["with_model_edge"]; N["gptLagMean"] = f"{g['explanation_lag']['mean_lag_model']:.1f}"; N["gptLagMax"] = g["explanation_lag"]["max_lag_model"]
    N["gptCensusOpenFinal"] = g["census"][-1]["open"]; N["gptCensusCellsFinal"] = g["census"][-1]["cells"]; N["gptDesignated"] = len(g["designated_pairs"])
    q = R["branches"]["QRT"]; N["qrtCensusOpenFinal"] = q["census"][-1]["open"]; N["qrtCensusCellsFinal"] = q["census"][-1]["cells"]; N["qrtDesignated"] = len(q["designated_pairs"])
    h = R["branches"]["HEP"]; N["hepRemovedNodes"] = h["removed_nodes"]; N["hepRemovedRoutes"] = h["removed_routes"]; N["hepUnionRoutes"] = h["curve"][-1]["E"]; N["hepAdjusted"] = R["logs"]["HEP"]["adjusted_routes"]
    N["emAdjusted"] = R["logs"]["EM"]["adjusted_routes"]; N["GPTForward"] = R["logs"]["GPT"]["forward_violations"]; N["QRTForward"] = R["logs"]["QRT"]["forward_violations"]
    N["gptReviewDated"] = R["provenance"]["GPT"].get("route:review-dated", 0); N["gptProjectNodes"] = R["provenance"]["GPT"].get("node:project", 0); N["qrtProjectNodes"] = R["provenance"]["QRT"].get("node:project", 0)
    N["qrtNodeRef"] = R["provenance"]["QRT"].get("node:node-ref", 0)
    for b in ("GPT", "QRT"):
        r = R["robustness_max_dating"][b]
        N[f"{b}MaxY0"] = r["years"][0]; N[f"{b}MaxY1"] = r["years"][1]; N[f"{b}MaxClosureFrac"] = f"{100*r['closure_fraction']:.0f}"; N[f"{b}MaxLatMedian"] = r["latency_median"]; N[f"{b}MaxLatMean"] = f"{r['latency_mean']:.1f}"
        N[f"{b}MaxAlpha"] = f"{r['densification']['alpha']:.2f}" if r["densification"]["alpha"] else "--"; N[f"{b}MaxPAratio"] = f"{r['preferential']['ratio']:.2f}" if r["preferential"]["ratio"] else "--"
        N[f"{b}MaxShiftMean"] = f"{r['node_shift_mean']:.1f}"; N[f"{b}MaxShiftMax"] = r["node_shift_max"]; N[f"{b}MaxShiftZero"] = r["node_shift_zero"]; N[f"{b}MaxMeanArrDeg"] = f"{r['mean_degree_at_arrival']:.2f}"
        for L in "SMO": N[f"{b}MaxHalf{L}"] = r["layer_half"][L]
    we = R["robustness_max_dating"]["GPT"]["witness_effect"]; N["gptMaxPairsSame"] = we["same_year"]; N["gptMaxPairsWfirst"] = we["witness_first"]; N["gptMaxPairsEfirst"] = we["effect_first"]
    N["gptMaxLagMean"] = f"{R['robustness_max_dating']['GPT']['explanation_lag']['mean_lag_model']:.1f}"
    # milestones on the curves (value at the last filtration year <= Y)
    def at(curve, Y, key):
        rows = [c for c in curve if c["year"] <= Y]
        return rows[-1][key] if rows else 0
    for b, years in (("GPT", (1950, 1970, 1980, 1990, 2000, 2010, 2020)), ("QRT", (2005, 2010, 2015, 2020)), ("EM", (1800, 1850, 1900, 1930)), ("HEP", (1930, 1940, 1960, 1980, 2000))):
        for Y in years:
            N[f"{b}VAt{Y}"] = at(R["branches"][b]["curve"], Y, "V"); N[f"{b}EAt{Y}"] = at(R["branches"][b]["curve"], Y, "E")
    for Y in (1900, 1950, 2000):
        N[f"mergedVAt{Y}"] = at(R["merged_curve"], Y, "V"); N[f"mergedEAt{Y}"] = at(R["merged_curve"], Y, "E"); N[f"mergedGlueAt{Y}"] = at(R["merged_curve"], Y, "glue")
    # decade with the most restructure events and the most falsify events (merged)
    mp = [r for r in R["merged_phases"] if r["total"]]
    for p in ("restructure", "falsify", "predict", "observe"):
        best = max(mp, key=lambda r: r[p]); N[f"decadeMax{p}"] = best["decade"]; N[f"decadeMax{p}N"] = best[p]
    # concurrency of phases: decades (from 1820) with >= 10 events, minimum number of active phases; decades with all eight
    big = [r for r in mp if r["decade"] >= 1820 and r["total"] >= 10]
    N["minActivePhases"] = min(sum(1 for p in PHASES if r[p]) for r in big); N["nBigDecades"] = len(big)
    N["decadesAllPhases"] = ", ".join(f"{r['decade']}s" for r in mp if all(r[p] for p in PHASES)) or "none"
    N["hepMframeKept"] = N["hepMframeAll"] - N["hepMframeRemoved"]; N["gptEffectsNoM"] = N["gptEffects"] - N["gptEffectsWithM"]
    # first year of a falsify route in each branch
    for b in FOUR:
        ys = [row["year"] for row in R["branches"][b]["rows"] if row["phases_routes"].get("falsify")]
        N[f"{b}FirstFalsify"] = min(ys) if ys else "--"
    # further quoted facts, computed
    em_lat = sorted(c["latency"] for c in R["branches"]["EM"]["decomposition"]["closures"]); N["EMLatSecond"] = em_lat[-2] if len(em_lat) >= 2 else "--"
    lagrows = {x["effect"]: x for x in R["branches"]["GPT"]["explanation_lag"]["rows"]}
    N["gptBellFirstM"] = lagrows["e-bell"]["first_model_edge"]; N["gptKDFirstM"] = lagrows["e-kd"]["first_model_edge"]; N["gptKDYear"] = lagrows["e-kd"]["t"]; N["gptBellYear"] = lagrows["e-bell"]["t"]
    for b in FOUR:
        cur = R["branches"][b]["curve"]; over = next((c["year"] for c in cur if c["E"] > c["V"]), None); N[f"{b}EoverV"] = over if over else "never"
        ng = [r["year"] for r in net["routes"] if r["branch"] == b and r["polarity"] == "no_go"]; N[f"{b}FirstNoGo"] = min(ng) if ng else "--"
    for b, Y in (("GPT", 1990), ("QRT", 2005)):
        cs = [c for c in R["branches"][b]["census"] if c["cells"]]
        cY = [c for c in cs if c["year"] <= Y][-1]
        N[f"{b}FilledRefYear"] = Y; N[f"{b}FilledRef"] = f"{100*cY['connected']/cY['cells']:.0f}"; N[f"{b}FilledLast"] = f"{100*cs[-1]['connected']/cs[-1]['cells']:.0f}"
        N[f"{b}CellsRef"] = cY["cells"]; N[f"{b}CellsGrowth"] = f"{cs[-1]['cells']/cY['cells']:.1f}"
    ct = R["concepts"]; N["nSharedFour"] = len(ct)
    dated_ct = [c for c in ct if c["lag_dated"] is not None]
    cmax = max(dated_ct, key=lambda c: c["lag_dated"]); N["lagMaxLabel"] = cmax["label"]; N["lagMaxYears"] = ", ".join(f"{b} {y}" for b, y in sorted(cmax["years_dated"].items(), key=lambda kv: kv[1]))
    lags = [c["lag_dated"] for c in ct if c["lag_dated"] is not None]
    N["nSharedDated"] = len(lags); N["lagMean"] = f"{sum(lags)/len(lags):.1f}"; N["lagMedian"] = sorted(lags)[len(lags)//2]; N["lagMax"] = max(lags); N["lagZero"] = sum(1 for l in lags if l == 0)
    firsts = Counter(c["first_dated"] for c in ct if c["lag_dated"] is not None)
    for b in FOUR: N[f"first{b}"] = firsts.get(b, 0)
    gq = [c for c in ct if set(c["branches"]) == {"GPT", "QRT"} and c["lag_dated"] is not None]
    N["nSharedGPTQRT"] = len(gq); N["firstGPTamongGQ"] = sum(1 for c in gq if c["first_dated"] == "GPT" and c["lag_dated"] > 0)
    N["firstQRTamongGQ"] = sum(1 for c in gq if c["first_dated"] == "QRT" and c["lag_dated"] > 0); N["tieGQ"] = sum(1 for c in gq if c["lag_dated"] == 0)
    gql = [c["lag_dated"] for c in gq if c["first_dated"] == "GPT" and c["lag_dated"] > 0]; N["lagGPTfirstMean"] = f"{sum(gql)/len(gql):.1f}" if gql else "--"
    qgl = [c["lag_dated"] for c in gq if c["first_dated"] == "QRT" and c["lag_dated"] > 0]; N["lagQRTfirstMean"] = f"{sum(qgl)/len(qgl):.1f}" if qgl else "--"
    eh = [c for c in ct if set(c["branches"]) == {"EM", "HEP"} and c["lag_dated"] is not None]
    N["nSharedEMHEP"] = len(eh); N["firstEMamongEH"] = sum(1 for c in eh if c["first_dated"] == "EM" and c["lag_dated"] > 0); N["firstHEPamongEH"] = sum(1 for c in eh if c["first_dated"] == "HEP" and c["lag_dated"] > 0); N["tieEH"] = sum(1 for c in eh if c["lag_dated"] == 0)
    N["nSharedUndated"] = sum(1 for c in ct if c["lag_dated"] is None)
    eg = [c for c in ct if set(c["branches"]) == {"EM", "GPT"}]; N["nSharedEMGPT"] = len(eg)
    last = R["merged_final"]; N["mergedV"] = last["V"]; N["mergedE"] = last["E"]; N["mergedGlue"] = last["glue"]; N["mergedVcollapsed"] = last["V_collapsed"]; N["mergedS"] = last["S"]; N["mergedM"] = last["M"]; N["mergedO"] = last["O"]
    N["mergedY0"] = R["merged_curve"][0]["year"]
    # year at which the merged network reaches half its final size
    half = next(r["year"] for r in R["merged_curve"] if r["V"] >= last["V"] / 2); N["mergedHalfYear"] = half
    halfE = next(r["year"] for r in R["merged_curve"] if r["E"] >= last["E"] / 2); N["mergedHalfYearE"] = halfE
    # merged phases totals
    tot = Counter()
    for row in R["merged_phases"]:
        for p in PHASES: tot[p] += row[p]
    for p in PHASES: N["phase" + p] = tot[p]
    N["phaseTotal"] = sum(tot.values())
    lines = [f"\\newcommand{{\\E{mname(k)}}}{{{tex_escape(v)}}}" for k, v in N.items()]
    with open(os.path.join(HERE, "thesis", "numbers_evo.tex"), "w") as f:
        f.write("% generated by build_evolution.py on " + datetime.date.today().isoformat() + "\n" + "\n".join(lines) + "\n")
    dump(N, os.path.join(OUT, "numbers_evo.json"))


if __name__ == "__main__":
    main()
