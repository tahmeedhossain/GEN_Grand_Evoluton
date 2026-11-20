"""Build everything: normalised branches, atlas, replay, filtration, census, numbers, figures, tables, pages (Part I), then Part II via build_evolution.py.

    python3 build.py            # writes out/*.json, data/gen_grand_network.json, thesis/numbers.tex, figures/*.pdf
"""
from __future__ import annotations
import json, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_engine.load import load_all, load_hep_steps
from gen_engine.atlas import build_atlas
from gen_engine.schema import dump
from gen_engine.replay_hep import replay, cumulative, final_predictive_content
from gen_engine.filtration import filtration_check, growth_curve, failed_route_resolution, depth_statistics, chapter_carry_in, order_comparison
from gen_engine.census import gpt_witness_census, gpt_pair_census, qrt_conversion_census, hep_sector_term_census, agenda_type_D, agenda_type_E
from gen_engine.ops import OPS, RULES

OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)


def main():
    graphs = load_all()
    atlas = build_atlas(graphs)
    dump(atlas, os.path.join(HERE, "data", "gen_grand_network.json"))
    for b, g in graphs.items():
        dump(g.to_json(), os.path.join(OUT, f"branch_{b}.json"))

    results = {"generated": datetime.datetime.now().isoformat(timespec="seconds"), "counts": atlas["counts"]}

    # --- signatures (layer-pair matrices) per branch, expanded and record-level
    sig = {}
    for b, g in graphs.items():
        pm = g.pair_matrix()
        sig[b] = {"pair_matrix": {f"{k[0]}->{k[1]}": v for k, v in sorted(pm.items())},
                  "signature": [{"inputs": dict(k[0]), "target": k[1], "n": v} for k, v in sorted(g.signature().items(), key=lambda kv: -kv[1])]}
    # HEP record-level pair matrix at the final step (generic edges counted once)
    raw = json.load(open(os.path.join(HERE, "data", "sources", "hep_v1.2.json")))
    final_raw = raw["steps"][11]
    rec = {}
    for e in final_raw["edges"]:
        k = {"s2m": "S->M", "m2o": "M->O", "m2s": "M->S", "m2m": "M->M"}[e["k"]]
        rec[k] = rec.get(k, 0) + 1
    rec["S->M (AND routes)"] = len(final_raw.get("ands", []))
    sig["HEP"]["record_level_final_step"] = rec
    results["signatures"] = sig

    # --- HEP replay
    rep = replay()
    br, steps, _ = load_hep_steps()
    rep["cumulative"] = cumulative(steps)
    rep["predictive_content"] = final_predictive_content(steps)["per_node"]
    rep["sector_term_census"] = hep_sector_term_census(steps[-1])
    results["hep"] = rep
    dump(rep, os.path.join(OUT, "hep_replay.json"))

    # --- type D analyses
    typeD = {}
    for b in ("EM", "UP", "LG"):
        g = graphs[b]
        typeD[b] = {"filtration": filtration_check(g), "growth": growth_curve(g), "failed": failed_route_resolution(g),
                    "depth": depth_statistics(g), "agenda": agenda_type_D(g)}
    typeD["UP"]["chapters"] = chapter_carry_in(graphs["UP"])
    typeD["order_EM_vs_UP"] = order_comparison(graphs, atlas["concepts"], "EM", "UP")
    results["typeD"] = typeD
    dump(typeD, os.path.join(OUT, "typeD.json"))

    # --- type E analyses
    typeE = {"GPT": {"witness_census": gpt_witness_census(graphs["GPT"]), "pair_census": gpt_pair_census(graphs["GPT"]), "agenda": agenda_type_E(graphs["GPT"])},
             "QRT": {"conversion_census": qrt_conversion_census(graphs["QRT"]), "pair_census": gpt_pair_census(graphs["QRT"]), "agenda": agenda_type_E(graphs["QRT"])}}
    results["typeE"] = typeE
    dump(typeE, os.path.join(OUT, "typeE.json"))

    # --- concepts and flips
    results["concepts"] = atlas["concepts"]
    results["cross_edges"] = atlas["cross_edges"]
    results["ops"] = OPS; results["rules"] = RULES
    dump(results, os.path.join(OUT, "results.json"))
    write_numbers(results, graphs)
    print("done:", atlas["counts"])


def tex_escape(s: str) -> str:
    return str(s).replace("_", "\\_").replace("%", "\\%").replace("&", "\\&").replace("#", "\\#")


def write_numbers(R, graphs):
    """Every number quoted in the thesis is a macro defined here."""
    N = {}
    c = R["counts"]
    N["nBranches"] = c["branches"]; N["nNodes"] = c["nodes"]; N["nRoutes"] = c["routes"]; N["nConcepts"] = c["concepts"]
    N["nGlued"] = c["glued_nodes"]; N["nFlips"] = c["role_flips"]; N["nCross"] = c["cross_edges"]
    for b, v in c["per_branch"].items():
        for k, x in v.items():
            N[f"{b}{k}"] = x
    hep = R["hep"]
    cmp_ = hep["comparison"]
    N["hepAgree"] = cmp_["agree"]; N["hepDisagree"] = cmp_["disagree"]; N["hepPaperAgree"] = cmp_["paper_table_agree"]; N["hepPaperDisagree"] = cmp_["paper_table_disagree"]
    N["hepRoutesChecked"] = hep["invariants"]["routes_checked"]
    for k, v in hep["invariants"].items():
        N["hepInv" + k.replace("_", "")] = v
    N["hepStepsGraph"] = len(hep["steps"])
    N["hepOCumFinal"] = hep["cumulative"][-1]["O_cumulative"]; N["hepOShownFinal"] = hep["cumulative"][-1]["O_shown"]
    N["hepUnexplainedFinal"] = len(hep["cumulative"][-1]["unexplained_cumulative"])
    N["hepUnexplainedFinalList"] = ", ".join(hep["cumulative"][-1]["unexplained_cumulative"])
    for b, n in hep["cumulative"][-1]["badges_cumulative"].items():
        N["hepBadge" + b] = n
    N["hepM2OCumFinal"] = hep["cumulative"][-1]["routes_m2o_cumulative"]
    N["hepSectorTermCells"] = hep["sector_term_census"]["cells"]; N["hepSectorTermEntered"] = hep["sector_term_census"]["entered"]; N["hepSectorTermEmpty"] = hep["sector_term_census"]["empty"]
    N["hepTrajS"] = ", ".join(map(str, hep["trajectories"]["S"])); N["hepTrajM"] = ", ".join(map(str, hep["trajectories"]["M"])); N["hepTrajO"] = ", ".join(map(str, hep["trajectories"]["O"]))
    N["hepTrajEff"] = ", ".join(map(str, hep["trajectories"]["eff"])); N["hepTrajFund"] = ", ".join(map(str, hep["trajectories"]["fund"])); N["hepTrajAND"] = ", ".join(map(str, hep["trajectories"]["AND"]))
    N["hepTrajUnexp"] = ", ".join(map(str, hep["trajectories"]["unexplained"]))
    N["hepTrajUnexpCum"] = ", ".join(str(len(x["unexplained_cumulative"])) for x in hep["cumulative"])
    N["hepTrajOCum"] = ", ".join(str(x["O_cumulative"]) for x in hep["cumulative"])
    N["hepRemovalEvents"] = sum(1 for x in hep["removals"] if x["removed_S"] or x["removed_M"])
    N["hepRemovedSNodes"] = sum(len(x["removed_S"]) for x in hep["removals"]); N["hepRemovedMNodes"] = sum(len(x["removed_M"]) for x in hep["removals"])
    pc = hep["predictive_content"]
    for k, v in pc.items():
        N[f"hepPC{k.replace('_', '')}pred"] = v["n_pred"]; N[f"hepPC{k.replace('_', '')}fit"] = v["n_fit"]
    N["hepPCtotalPred"] = sum(v["n_pred"] for v in pc.values()); N["hepPCtotalFit"] = sum(v["n_fit"] for v in pc.values())
    D = R["typeD"]
    for b in ("EM", "UP", "LG"):
        N[f"{b}ForwardLinks"] = D[b]["filtration"]["forward_links"]; N[f"{b}TimePoints"] = D[b]["filtration"]["time_points"]
        N[f"{b}Tmax"] = D[b]["filtration"]["t_max"]
        N[f"{b}Failed"] = D[b]["failed"]["n_failed"]; N[f"{b}FailedResolved"] = D[b]["failed"]["n_resolved"]
        N[f"{b}FailedMaxDist"] = D[b]["failed"]["max_distance"] if D[b]["failed"]["max_distance"] is not None else "--"
        N[f"{b}Acyclic"] = "yes" if D[b]["depth"]["acyclic"] else "no"
        N[f"{b}NodesInCycles"] = D[b]["depth"]["nodes_in_cycles"]; N[f"{b}LargestSCC"] = D[b]["depth"]["largest_scc"]
        N[f"{b}LongestChain"] = D[b]["depth"].get("longest_chain", D[b]["depth"].get("longest_chain_condensed"))
        N[f"{b}Edges2section"] = D[b]["depth"]["edges_2section"]
        for L, lst in D[b]["agenda"]["primitive_nodes"].items():
            N[f"{b}Primitive{L}"] = len(lst)
    N["EMPrimitiveOList"] = ", ".join(D["EM"]["agenda"]["primitive_nodes"]["O"])
    N["UPPrimitiveOList"] = ", ".join(D["UP"]["agenda"]["primitive_nodes"]["O"])
    oc = D["order_EM_vs_UP"]
    N["orderN"] = oc["n"]; N["orderTau"] = f"{oc['kendall_tau_b']:.3f}"; N["orderRho"] = f"{oc['spearman_rho']:.3f}"
    N["orderConc"] = oc["concordant"]; N["orderDisc"] = oc["discordant"]
    N["UPChapters"] = len(D["UP"]["chapters"]); N["UPCarriedMax"] = max(r["carried_in"] for r in D["UP"]["chapters"])
    N["UPCarriedTotal"] = sum(r["carried_in"] for r in D["UP"]["chapters"])
    E = R["typeE"]
    w = E["GPT"]["witness_census"]
    N["gptCombos"] = len(graphs["GPT"].extra["combos"]); N["gptNodes"] = len(graphs["GPT"].nodes)
    N["gptCells"] = w["cells"]; N["gptSettled"] = w["settled"]; N["gptUncharted"] = w["uncharted"]; N["gptWitnesses"] = w["witnesses"]; N["gptStates"] = w["states"]; N["gptProcesses"] = w["processes"]
    for k, v in w["verdicts"].items():
        N["gptVerdict" + k] = v
    p = E["GPT"]["pair_census"]
    N["gptPairs"] = p["pairs"]; N["gptConnectedPairs"] = p["connected_pairs"]; N["gptUnconnectedPairs"] = p["unconnected_pairs"]
    N["gptNoGo"] = p["polarity"]["no_go"]; N["gptPossibility"] = p["polarity"]["possibility"] + p["polarity"]["structural"]; N["gptOpen"] = p["polarity"]["open"]
    N["gptOpenEdges"] = len(E["GPT"]["agenda"]["open_edges"]); N["gptPartialEdges"] = len(E["GPT"]["agenda"]["partial_edges"]); N["gptGaps"] = E["GPT"]["agenda"]["recorded_gaps"]
    q = E["QRT"]["conversion_census"]
    N["qrtCells"] = q["cells"]; N["qrtCharted"] = q["charted_conversion_group"]; N["qrtChartedStateState"] = q["charted_state_to_state"]; N["qrtCrossAny"] = q["cross_theory_any"]
    N["qrtUncharted"] = q["uncharted_conversion"]; N["qrtTheories"] = len(q["theories"])
    pq = E["QRT"]["pair_census"]
    N["qrtPairs"] = pq["pairs"]; N["qrtConnectedPairs"] = pq["connected_pairs"]; N["qrtPartialEdges"] = len(E["QRT"]["agenda"]["partial_edges"]); N["qrtGaps"] = E["QRT"]["agenda"]["recorded_gaps"]
    flips = [c for c in R["concepts"] if c["flip"]]
    N["nFlipsList"] = len(flips)
    N["nConceptsThreePlus"] = sum(1 for c in R["concepts"] if c["n_branches"] >= 3)
    N["nConceptsQuantumInfo"] = sum(1 for c in R["concepts"] if set(c["roles"]) <= {"GPT", "QRT"})
    N["nConceptsReaders"] = sum(1 for c in R["concepts"] if set(c["roles"]) <= {"EM", "UP", "LG"})
    N["nConceptsBridge"] = c["concepts"] - N["nConceptsQuantumInfo"] - N["nConceptsReaders"]
    # pair-matrix zero/nonzero patterns, incidences and mean legs
    for b, s in R["signatures"].items():
        pm = s["pair_matrix"]
        N[f"{b}PairsNonzero"] = len(pm)
        inc = sum(pm.values()); N[f"{b}Incidences"] = inc
        nr = c["per_branch"][b]["routes"]; N[f"{b}MeanLegs"] = f"{inc / nr:.2f}"
        for k, v in pm.items():
            N[f"{b}Pair{k.replace('->', 'to')}"] = v
    digits = {"0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four", "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine"}
    def mname(k: str) -> str:
        return "".join(digits.get(ch, ch) for ch in k if ch.isalnum())
    lines = [f"\\newcommand{{\\N{mname(k)}}}{{{tex_escape(v)}}}" for k, v in N.items()]
    os.makedirs(os.path.join(HERE, "thesis"), exist_ok=True)
    with open(os.path.join(HERE, "thesis", "numbers.tex"), "w") as f:
        f.write("% generated by build.py on " + datetime.date.today().isoformat() + "\n" + "\n".join(lines) + "\n")
    dump(N, os.path.join(OUT, "numbers.json"))


if __name__ == "__main__":
    main()
    # Part I figures, tables and page; then Part II (evolution): analyses, figures, tables and the year-slider page
    from gen_engine import figures, tables, page
    figures.main(); tables.main(); page.main()
    import build_evolution
    build_evolution.main()
    from gen_engine import figures_evo, tables_evo, page_evo
    figures_evo.main(); tables_evo.main(); page_evo.build()
