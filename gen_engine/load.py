"""Loaders: the six released instances -> universal schema (schema.py).

Nothing is invented here.  Each loader reads the released JSON of the
instance, keeps every native field in `extra`, and fills the universal
fields (layer, sublayer, kind, polarity, time index) by the explicit rules
written in this file.  The rules are the content of Chapter 3 of the thesis
("normalisation") and are deliberately simple so that they can be checked.
"""
from __future__ import annotations
import json, os, re
from typing import Dict, List, Tuple, Any
from .schema import Node, Route, Branch, Graph, UNIVERSAL_KIND_CLASS

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sources")


def _read(name: str) -> Dict[str, Any]:
    with open(os.path.join(SRC, name), encoding="utf-8") as f:
        return json.load(f)


def _polarity(kind: str, native_polarity: str | None = None) -> str:
    if native_polarity in ("structural", "possibility", "no_go", "open"):
        return native_polarity
    return UNIVERSAL_KIND_CLASS[kind]


# ---------------------------------------------------------------------------
# Type D branches: EM reader (v3.1), University Physics reader (v2), LocGlob (v6.1)
# ---------------------------------------------------------------------------
_D_LAYER = {"observable": "O", "model": "M", "state": "S"}


def _d_sublayer(ntype: str, era: str, nid: str, label: str) -> str:
    if ntype == "observable":
        return "O.direct"
    if ntype == "model":
        return "M.law"
    # state
    if era == "quantum":
        return "S.hilbert"
    lab = label.lower()
    if any(w in lab for w in ("field", "wave", "potential", "density", "radiation", "mode", "tensor", "bundle", "current")):
        return "S.field"
    return "S.point"


def load_em() -> Graph:
    d = _read("em_v3.1.json")
    br = Branch(id="EM", title=d["title"], btype="D",
                source="tahmeedhossain/GEN_epistemic_evolution, data/v3.1_maxwell_to_qed_network.json",
                version=d["version"], time_axis="paragraph (0..77) of the 23-section reader",
                native_layers=["observable", "model", "state"], layer_map=dict(_D_LAYER),
                notes="Routes are AND/single; kind classical/quantization/quantum/classical_limit/failed.")
    g = Graph(br)
    for n in d["nodes"]:
        g.add_node(Node(uid=f"EM:{n['id']}", branch="EM", native_id=n["id"], label=n["label"],
                        layer=_D_LAYER[n["type"]], sublayer=_d_sublayer(n["type"], n["era"], n["id"], n["label"]),
                        native_layer=n["type"], era=n["era"], t=n["first_paragraph"],
                        extra={k: n[k] for k in ("symbol", "derived", "description", "math_structure", "properties", "section") if k in n}))
    for r in d["routes"]:
        ins = [f"EM:{i['node']}" for i in r["inputs"]]
        kind = "failed" if r.get("failed") else "derives"
        g.add_route(Route(uid=f"EM:{r['id']}", branch="EM", native_id=r["id"], inputs=ins, target=f"EM:{r['target']}",
                          logic=r["logic"], kind=kind, kind_native=r["kind"], status="failed" if r.get("failed") else "established",
                          polarity=_polarity(kind), t=r["appears_at_paragraph"],
                          extra={k: r[k] for k in ("title", "formula", "section", "text_marker_paragraph") if k in r}))
    g.extra = {"sections": d["sections"], "paragraphs": [{"index": p["index"], "section": p["section"]} for p in d["paragraphs"]]}
    return g


def load_up() -> Graph:
    d = _read("up_v2.json")
    br = Branch(id="UP", title=d["title"], btype="D",
                source="tahmeedhossain/GEN_Learning, data/v2/university_physics_network_v2.json",
                version="v2", time_axis="paragraph (0..619) of the 44-chapter reading text",
                native_layers=["observable", "model", "state"], layer_map=dict(_D_LAYER),
                notes="Routes are AND/single; kind classical/relativistic/quantum/to_*/failed; model nodes flagged postulate.")
    g = Graph(br)
    for n in d["nodes"]:
        g.add_node(Node(uid=f"UP:{n['id']}", branch="UP", native_id=n["id"], label=n["label"],
                        layer=_D_LAYER[n["type"]], sublayer=_d_sublayer(n["type"], n["era"], n["id"], n["label"]),
                        native_layer=n["type"], era=n["era"], t=n["paragraph"],
                        extra={k: n[k] for k in ("symbol", "primitive", "postulate", "description", "vol", "section", "chapter", "order") if k in n}))
    for r in d["routes"]:
        ins = [f"UP:{i['node']}" for i in r["inputs"]]
        kind = "failed" if r["kind"] == "failed" else "derives"
        g.add_route(Route(uid=f"UP:{r['id']}", branch="UP", native_id=r["id"], inputs=ins, target=f"UP:{r['target']}",
                          logic=r["logic"], kind=kind, kind_native=r["kind"], status="failed" if kind == "failed" else "established",
                          polarity=_polarity(kind), t=r["paragraph"],
                          extra={k: r[k] for k in ("title", "formula", "tags", "vol", "section", "chapter") if k in r}))
    g.extra = {"chapters": [{k: c[k] for k in ("vol", "ch", "unit", "title", "p0", "p1")} for c in d["chapters"]],
               "stats": d["stats"]}
    return g


def load_locglob() -> Graph:
    d = _read("locglob_v6.1.json")
    br = Branch(id="LG", title="Local cycles and global conservation (" + d["name"] + ")", btype="D",
                source="tahmeedhossain/GEN_LocGlob_Flow, data/v6.1_local-global.json",
                version=d["version"], time_axis="version (1.0 .. 6.1); v6.1 loaded",
                native_layers=["observable", "model", "state"], layer_map=dict(_D_LAYER),
                notes="Routes may have several targets (expanded one per target); energy flows are observable->observable routes of kind transport/conversion. Page 'result' and 'flow rule' entries are not concept nodes.")
    g = Graph(br)
    flow_label = {fl["id"]: f"{fl['label']}: {fl['kind']} {fl['from']} -> {fl['to']}" for fl in d["flows"]}
    for n in d["nodes"]:
        if n["type"] == "flow rule":
            # a derived conversion/transport law: a model-layer node (its inputs are the field laws and the curl parts)
            g.add_node(Node(uid=f"LG:{n['id']}", branch="LG", native_id=n["id"], label=flow_label.get(n["id"], n["id"]), layer="M",
                            sublayer="M.law", native_layer="flow rule", era="classical", t=6.1, extra={}))
            continue
        if n["type"] == "result":
            # a derived claim about the observables (cycling / conservation): an effect-type observable
            g.add_node(Node(uid=f"LG:{n['id']}", branch="LG", native_id=n["id"], label=n["title"], layer="O",
                            sublayer="O.effect", native_layer="result", era="classical", t=6.1, extra={}))
            continue
        lab = n["label"] or n.get("symbol") or n["id"]
        sub = "O.direct" if n["type"] == "observable" else ("M.law" if n["type"] == "model" else "S.field")
        g.add_node(Node(uid=f"LG:{n['id']}", branch="LG", native_id=n["id"], label=lab, layer=_D_LAYER[n["type"]], sublayer=sub,
                        native_layer=n["type"], era="classical", t=6.1,
                        extra={k: n[k] for k in ("symbol", "title", "property", "switch") if k in n and n[k] is not None}))
    for r in d["routes"]:
        for j, tgt in enumerate(r["targets"]):
            ins = [f"LG:{i}" for i in r["inputs"]]
            g.add_route(Route(uid=f"LG:{r['id']}" + (f"#{j}" if len(r["targets"]) > 1 else ""), branch="LG", native_id=r["id"],
                              inputs=ins, target=f"LG:{tgt}", logic="AND" if len(ins) > 1 else "single", kind="derives",
                              kind_native="route", status="established", polarity="structural", t=6.1, extra={}))
    for fl in d["flows"]:
        g.add_route(Route(uid=f"LG:{fl['id']}", branch="LG", native_id=fl["id"], inputs=[f"LG:{fl['from']}"], target=f"LG:{fl['to']}",
                          logic="single", kind=fl["kind"], kind_native="flow:" + fl["kind"], status="established",
                          polarity="structural", t=6.1, extra={"label": fl["label"]}))
    g.extra = {"properties": d["properties"], "results": d["results"], "regions": d["regions"]}
    return g


# ---------------------------------------------------------------------------
# Type H branch: Standard Model epistemic graph (v1.2), per step
# ---------------------------------------------------------------------------
_HEP_SUB = {("S", "hilbert"): "S.hilbert", ("S", "uir"): "S.uir", ("S", "sector"): "S.sector",
            ("M", "frame"): "M.frame", ("M", "fund"): "M.fund", ("M", "eff"): "M.eff", ("M", "cand"): "M.cand",
            ("M", "cluster"): "M.cluster", ("O", None): "O.direct"}
_HEP_M2O = {"pred": "predicts", "fit": "calibrates", "frame": "frames", "cand": "candidate", "weak": "frames"}
# Sector groups used by group legs (the page draws a bracket over these sectors).
HEP_GROUPS = {"chg": ["s_e", "s_mu", "s_u", "s_d"],           # charged fermion sectors present from Step 9 on
              "fer": ["s_nue", "s_e", "s_num", "s_mu", "s_u", "s_d"],
              "nus": ["s_nue", "s_num"]}


def hep_raw() -> Dict[str, Any]:
    return _read("hep_v1.2.json")


def _hep_node(k: str, v: Dict[str, Any], step_index: int) -> Node:
    sub = _HEP_SUB[(v["layer"], v.get("kind"))]
    return Node(uid=f"HEP:{k}", branch="HEP", native_id=k, label=v["label"], layer=v["layer"], sublayer=sub,
                native_layer={"S": "state", "M": "model", "O": "observable"}[v["layer"]], era="quantum", t=step_index,
                extra={kk: vv for kk, vv in v.items() if kk not in ("layer", "label")})


def load_hep_steps() -> Tuple[Branch, List[Graph], Dict[str, Any]]:
    """One graph per graph step (12 graphs; the synthesis step 13 has no graph)."""
    d = hep_raw()
    br = Branch(id="HEP", title=d["title"], btype="H",
                source="tahmeedhossain/GEN_HEP, data/v1.2_sm_epistemic_graph.json", version=d["version"],
                time_axis="step (1..12) of the historical sequence",
                native_layers=["S", "M", "O"], layer_map={"S": "S", "M": "M", "O": "O"},
                notes="Edges: s2m, m2o (pred/fit/frame/cand), m2s back-edge, m2m lineage; AND routes with (sector, n) and (group, n) legs. "
                      "Generic layer edges (from/to the whole state layer) are expanded to one route per state node and flagged generic.")
    graphs: List[Graph] = []
    first_seen: Dict[str, int] = {}
    for si, step in enumerate(d["steps"], start=1):
        if not (step["S"] or step["M"] or step["O"]):
            continue
        g = Graph(br)
        for layer_key in ("S", "M", "O"):
            for k in step[layer_key]:
                first_seen.setdefault(k, si)
                n = _hep_node(k, d["nodes"][k], first_seen[k])
                g.add_node(n)
        state_uids = [f"HEP:{k}" for k in step["S"]]
        ei = 0
        for e in step["edges"]:
            ei += 1
            f, t, k = e["f"], e["t"], e["k"]
            if k == "s2m":
                srcs = state_uids if f == "S" else [f"HEP:{f}"]
                for s_uid in srcs:
                    g.add_route(Route(uid=f"HEP:{step['id']}:e{ei}:{s_uid.split(':')[1]}", branch="HEP", native_id=f"{step['id']}/e{ei}",
                                      inputs=[s_uid], target=f"HEP:{t}", logic="single", kind="enters", kind_native="s2m",
                                      status="established", polarity="structural", t=si,
                                      extra={"rel": e.get("rel"), "generic": f == "S", "step": step["id"]}))
            elif k == "m2o":
                kind = _HEP_M2O[e.get("st", "pred")]
                g.add_route(Route(uid=f"HEP:{step['id']}:e{ei}", branch="HEP", native_id=f"{step['id']}/e{ei}",
                                  inputs=[f"HEP:{f}"], target=f"HEP:{t}", logic="single", kind=kind, kind_native="m2o/" + e.get("st", "pred"),
                                  status=e.get("st", "pred"), polarity=_polarity(kind), t=si,
                                  extra={"rel": e.get("rel"), "step": step["id"], "weak": e.get("weak", False)}))
            elif k == "m2s":
                tgts = state_uids if t == "S" else [f"HEP:{t}"]
                for t_uid in tgts:
                    g.add_route(Route(uid=f"HEP:{step['id']}:e{ei}:{t_uid.split(':')[1]}", branch="HEP", native_id=f"{step['id']}/e{ei}",
                                      inputs=[f"HEP:{f}"], target=t_uid, logic="single", kind="backedge", kind_native="m2s",
                                      status="established", polarity="structural", t=si,
                                      extra={"rel": e.get("rel"), "generic": t == "S", "step": step["id"]}))
            elif k == "m2m":
                g.add_route(Route(uid=f"HEP:{step['id']}:e{ei}", branch="HEP", native_id=f"{step['id']}/e{ei}",
                                  inputs=[f"HEP:{f}"], target=f"HEP:{t}", logic="single", kind="lineage", kind_native="m2m",
                                  status="established", polarity="structural", t=si, extra={"rel": e.get("rel"), "step": step["id"]}))
            else:
                raise ValueError(k)
        for ai, a in enumerate(step.get("ands", []), start=1):
            legs: List[str] = []
            leg_desc = []
            for l in a["legs"]:
                if "s" in l:
                    legs.append(f"HEP:{l['s']}")
                    leg_desc.append({"sector": l["s"], "n": l["n"]})
                else:
                    members = [m for m in HEP_GROUPS[l["g"]] if m in step["S"]]
                    legs.extend(f"HEP:{m}" for m in members)
                    leg_desc.append({"group": l["g"], "members": members, "n": l["n"], "label": l.get("label")})
            g.add_route(Route(uid=f"HEP:{step['id']}:and{ai}", branch="HEP", native_id=f"{step['id']}/and{ai}", inputs=legs,
                              target=f"HEP:{a['t']}", logic="AND", kind="candidate" if a.get("cand") else "enters",
                              kind_native="and_route", status="candidate" if a.get("cand") else "established",
                              polarity="open" if a.get("cand") else "structural", t=si,
                              extra={"label": a.get("label"), "rel": a.get("rel"), "legs": leg_desc, "step": step["id"]}))
        # clusters (step 12)
        g.clusters = step.get("clusters")
        g.step = {k: step[k] for k in ("id", "title", "years", "driver", "phases", "ops") if k in step}
        g.step["index"] = si
        graphs.append(g)
    return br, graphs, d


def load_hep() -> Graph:
    """The atlas view of the SM graph: every node that ever existed, with first/last step and final status,
    and the routes of the final graph step (Step 12)."""
    br, graphs, d = load_hep_steps()
    final = graphs[-1]
    g = Graph(br)
    present: Dict[str, List[int]] = {}
    for gs in graphs:
        for uid in gs.nodes:
            present.setdefault(uid, []).append(gs.step["index"])
    for k, v in d["nodes"].items():
        uid = f"HEP:{k}"
        steps = present.get(uid, [])
        n = _hep_node(k, v, steps[0] if steps else None)
        n.extra["steps_present"] = steps
        n.extra["in_final"] = uid in final.nodes
        n.extra["absorbed"] = any(k in c.get("members", []) and k != c["id"] for c in (final.clusters or [])) and uid not in final.nodes
        g.add_node(n)
    for r in final.routes.values():
        g.add_route(r)
    # lineage edges recorded inside clusters at the final step
    for c in final.clusters or []:
        for li, l in enumerate(c.get("lineage", []), start=1):
            g.add_route(Route(uid=f"HEP:sm:lineage:{c['id']}:{li}", branch="HEP", native_id=f"sm/lineage/{c['id']}/{li}",
                              inputs=[f"HEP:{l['f']}"], target=f"HEP:{l['t']}", logic="single", kind="lineage", kind_native="cluster_lineage",
                              status="established", polarity="structural", t=12, extra={"rel": l.get("rel"), "cluster": c["id"]}))
        for m in c.get("members", []):
            if m != c["id"]:
                g.add_route(Route(uid=f"HEP:sm:member:{c['id']}:{m}", branch="HEP", native_id=f"sm/member/{c['id']}/{m}",
                                  inputs=[f"HEP:{m}"], target=f"HEP:{c['id']}", logic="single", kind="subset", kind_native="cluster_member",
                                  status="established", polarity="structural", t=12, extra={"cluster": c["id"]}))
    # observable families (effect clusters inside the historical graph): members refine the family head,
    # and the generic production/decay observable is refined by the two family heads (Step-4 rewrite)
    for fam_head, tag in (("o_sig", "σ-type"), ("o_G", "Γ-type")):
        for k, v in d["nodes"].items():
            if v["layer"] == "O" and k != fam_head and tag in (v.get("sub") or ""):
                g.add_route(Route(uid=f"HEP:fam:{k}:{fam_head}", branch="HEP", native_id=f"fam/{k}/{fam_head}", inputs=[f"HEP:{k}"], target=f"HEP:{fam_head}",
                                  logic="single", kind="subset", kind_native="observable_family", status="established", polarity="structural",
                                  t=g.nodes[f"HEP:{k}"].t, extra={"family": tag}))
    for fam_head in ("o_sig", "o_G"):
        g.add_route(Route(uid=f"HEP:fam:{fam_head}:o_prod", branch="HEP", native_id=f"fam/{fam_head}/o_prod", inputs=[f"HEP:{fam_head}"], target="HEP:o_prod",
                          logic="single", kind="subset", kind_native="observable_family", status="established", polarity="structural", t=4,
                          extra={"family": "rewrite of particle production (Step 4)"}))
    g.clusters = final.clusters
    g.extra = {"steps": [gs.step for gs in graphs], "references": d["references"]}
    return g


# ---------------------------------------------------------------------------
# Type E branches: nonclassicality network (v2.6) and QRT network (v1.2)
# ---------------------------------------------------------------------------
_GPT_MAP = {"axiom": ("M", "M.axiom"), "model": ("M", "M.model"), "state": ("S", "S.cluster"), "process": ("M", "M.process"),
            "witness": ("O", "O.witness"), "effect": ("O", "O.effect"), "task": ("O", "O.task")}


def _gpt_version_of_edge(eid: str, in_v2: set, in_v1: set) -> float:
    """The data files are v1 (1.0), network_v2.json (the v2.4 release, which contains the round-3 R edges and the
    v2.3 MH edges) and v2.6.  Version of first appearance by file membership and, inside the v2.4 file, by id group."""
    if eid in in_v1:
        return 1.0
    if eid in in_v2:
        if eid.startswith("MH"):
            return 2.3
        if re.match(r"^R\d", eid):
            return 2.4
        return 2.0
    if eid.startswith("U"):
        return 2.6
    return 2.6


def load_gpt() -> Graph:
    d = _read("gpt_v2.6.json")
    v2 = _read("gpt_v2.json"); v1 = _read("gpt_v1.json")
    in_v2 = {e["id"] for e in v2["edges"]}; in_v1 = {e["id"] for e in v1["edges"]}
    nodes_v2 = {n["id"] for n in v2["nodes"]}; nodes_v1 = {n["id"] for n in v1["nodes"]}
    br = Branch(id="GPT", title=d["meta"]["title"], btype="E",
                source="tahmeedhossain/GEN_GPT_Level, data/network_v2.6.json", version="2.6",
                time_axis="release version (1.0, 2.0, 2.3, 2.4, 2.6)",
                native_layers=d["meta"]["layers"], layer_map={k: v[0] for k, v in _GPT_MAP.items()},
                notes="Seven native layers folded into three: axiom/model/process -> M; state -> S; witness/effect/task -> O.")
    g = Graph(br)
    for n in d["nodes"]:
        L, sub = _GPT_MAP[n["type"]]
        g.add_node(Node(uid=f"GPT:{n['id']}", branch="GPT", native_id=n["id"], label=n["label"], layer=L, sublayer=sub,
                        native_layer=n["type"], era="quantum", t=1.0 if n["id"] in nodes_v1 else (2.0 if n["id"] in nodes_v2 else 2.4),
                        extra={"def": n.get("def")}))
    for e in d["edges"]:
        kind = e["kind"]
        g.add_route(Route(uid=f"GPT:{e['id']}", branch="GPT", native_id=e["id"], inputs=[f"GPT:{e['source']}"], target=f"GPT:{e['target']}",
                          logic="single", kind=kind, kind_native=kind, status=e["status"], polarity=_polarity(kind),
                          t=_gpt_version_of_edge(e["id"], in_v2, in_v1), extra={"statement": e.get("statement"), "refs": e.get("refs", [])}))
    g.extra = {"witnesses": d["witnesses"], "combos": d["combos"], "gaps": d["gaps"], "meta": d["meta"]}
    return g


_QRT_MAP = {("model", "model"): ("M", "M.model"), ("model", "framework"): ("M", "M.axiom"),
            ("state", "free_state"): ("S", "S.free"), ("state", "resource_state"): ("S", "S.resource"), ("state", "dist"): ("S", "S.dist"),
            ("process_cptp", "free_ops"): ("M", "M.process"), ("process_cptp", "use_ops"): ("M", "M.process"),
            ("process_cptp", "no_ops"): ("M", "M.process"), ("process_cptp", "framework"): ("M", "M.process"),
            ("witness", "detector"): ("O", "O.witness"), ("witness", "quantifier"): ("O", "O.witness"),
            ("witness", "framework"): ("O", "O.witness"), ("task", "framework"): ("O", "O.task"), ("task", "task"): ("O", "O.task")}


def load_qrt() -> Graph:
    d = _read("qrt_v1.2.json")
    v11 = _read("qrt_v1.1.json")
    in_v11 = {e["id"] for e in v11["edges"]}
    br = Branch(id="QRT", title=d["meta"]["title"], btype="E",
                source="tahmeedhossain/GEN_QRT_Level, data/qrt_network_v1.2.json", version="1.2",
                time_axis="release version (1.1, 1.2)", native_layers=d["meta"]["layers"],
                layer_map={"model": "M", "state": "S", "process_cptp": "M", "witness": "O", "task": "O"},
                notes="Five native layers folded into three: model/process_cptp -> M; state -> S; witness/task -> O. "
                      "Node roles kept as sub-layers (free/resource/dist; free_ops/use_ops/no_ops; detector/quantifier).")
    g = Graph(br)
    for n in d["nodes"]:
        L, sub = _QRT_MAP[(n["layer"], n["role"])]
        g.add_node(Node(uid=f"QRT:{n['id']}", branch="QRT", native_id=n["id"], label=n["label"], layer=L, sublayer=sub,
                        native_layer=n["layer"] + "/" + n["role"], era="quantum", t=1.1,
                        extra={"theory": n["theory"], "role": n["role"], "statement": n.get("statement"), "refs": n.get("refs", []), "status": n.get("status")}))
    for e in d["edges"]:
        kind = e["kind"]
        g.add_route(Route(uid=f"QRT:{e['id']}", branch="QRT", native_id=e["id"], inputs=[f"QRT:{e['from']}"], target=f"QRT:{e['to']}",
                          logic="single", kind=kind, kind_native=kind, status=e["status"], polarity=_polarity(kind, e.get("polarity")),
                          t=1.1 if e["id"] in in_v11 else 1.2, extra={"statement": e.get("statement"), "refs": e.get("refs", []), "via": e.get("via")}))
    g.extra = {"theories": d["theories"], "gaps": d["gaps"], "derived_propositions": d["derived_propositions"], "meta": d["meta"]}
    return g


def load_all() -> Dict[str, Graph]:
    return {"EM": load_em(), "UP": load_up(), "LG": load_locglob(), "HEP": load_hep(), "GPT": load_gpt(), "QRT": load_qrt()}
