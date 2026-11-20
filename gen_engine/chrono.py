"""Chronology: a calendar-year time index for every node and route of the EM, HEP, GPT and QRT branches,
derived from the data (reference years, step years, paragraph texts) by explicit rules.

Rules (stated in the thesis, Chapter "Evolution of the effect and resource networks"):
  GPT   edge year  = earliest year among its references (journal year in parentheses, arXiv YYMM id);
                     refs that cite a review for a standard result are flagged 'review-dated';
                     definitional / derived / elementary edges with no dated source get
                     year = max(year of endpoints) once the endpoints are dated, else the project year 2026.
        node year  = earliest year among its dated incident edges.
  QRT   edge year  as GPT; node year = min(earliest node-reference year, earliest incident dated edge year).
  HEP   node year  = first year in the node's 'years' field; fallback: start year of the first step it is drawn in.
        route year = max(start year of its step, years of its endpoints).
  EM    paragraph year = first year mentioned in the paragraph text, carried forward inside a section,
                         fallback: start year of the section; node year = year of its first paragraph;
                         route year = max(year of its paragraph, years of its inputs and target).
Every assignment records its provenance ('cited', 'review-dated', 'node-ref', 'step', 'paragraph', 'section', 'project', 'propagated').
"""
from __future__ import annotations
import json, os, re
from typing import Dict, List, Tuple, Any, Optional
from .schema import Graph
from .load import _read, load_em, load_hep, load_gpt, load_qrt, hep_raw

PROJECT_YEAR = 2026
YR_PAREN = re.compile(r"\((1[5-9]\d{2}|20[0-2]\d)[a-z]?\)")
YR_LOOSE = re.compile(r"(?<![,\d])\s(1[5-9]\d{2}|20[0-2]\d)\b(?!\s*[,(]\s*\d)")
ARX = re.compile(r"\b(\d{2})(\d{2})\.\d{4,5}\b")
OLDARX = re.compile(r"(?:quant-ph|hep-th|hep-ph|cond-mat|math-ph|physics|gr-qc)/(\d{2})\d{5}")
REVIEW_WORDS = ("standard", "classic", "textbook", "folklore", "see ", "review", "e.g.")
UNDATED_WORDS = ("definitional", "elementary", "derived", "this work", "proof sketch", "combined paper")


def years_in(text: str) -> List[int]:
    """Years of a reference string: arXiv identifiers (YYMM.NNNNN, old-style archive/YYMMNNN), years in
    parentheses '(YYYY)', and, failing both, a bare year not placed like a page number (not after a comma)."""
    ys = [2000 + int(m[0]) for m in ARX.findall(text) if 0 <= int(m[0]) <= 26 and 1 <= int(m[1]) <= 12]
    ys += [(1900 + int(m)) if int(m) > 50 else (2000 + int(m)) for m in OLDARX.findall(text)]
    t2 = ARX.sub(" ", OLDARX.sub(" ", text))
    paren = [int(x) for x in YR_PAREN.findall(t2)]
    if paren:
        return ys + paren
    loose = [int(x) for x in YR_LOOSE.findall(" " + t2)]
    return ys + loose


def ref_year(refs: List[str], mode: str = "min") -> Tuple[Optional[int], str]:
    """(year, provenance) for a list of reference strings.  mode 'min': the earliest cited source (ingredient date,
    the convention of the thesis); mode 'max': the latest cited source (an upper bound, used as a robustness check)."""
    if not refs:
        return None, "none"
    ys = []
    review = False
    for r in refs:
        y = years_in(r)
        if y:
            ys.append(min(y) if mode == "min" else max(y))
        if any(w in r.lower() for w in REVIEW_WORDS):
            review = True
    if not ys:
        return None, "undated"
    return (min(ys) if mode == "min" else max(ys)), ("review-dated" if review else "cited")


YR_ANY = re.compile(r"\b(1[5-9]\d{2}|20[0-2]\d)\b")


def _first_year(s: str) -> Optional[int]:
    """First four-digit year in a free text (paragraph, step range, node year field)."""
    ys = YR_ANY.findall(s or "")
    return int(ys[0]) if ys else None


# ---------------------------------------------------------------------------
def date_type_E(g: Graph, mode: str = "min") -> Dict[str, Any]:
    """Assign years to a GPT/QRT graph in place (node.t_year, route.t_year) and return the provenance log."""
    log = {"edges": {}, "nodes": {}}
    # 1. dated edges
    for r in g.routes.values():
        y, prov = ref_year(r.extra.get("refs") or [], mode)
        r.extra["t_year"] = y; r.extra["year_prov"] = prov
        log["edges"][r.uid] = (y, prov)
    # 2. node years: node refs (QRT) and incident dated edges
    for n in g.nodes.values():
        cands = []
        y, prov = ref_year(n.extra.get("refs") or [], mode)
        if y is not None:
            cands.append((y, "node-ref"))
        for r in g.routes.values():
            if n.uid in r.inputs or n.uid == r.target:
                if r.extra.get("t_year") is not None:
                    cands.append((r.extra["t_year"], "edge:" + r.native_id))
        if cands:
            y0, p0 = min(cands, key=lambda c: c[0])
            n.extra["t_year"] = y0; n.extra["year_prov"] = p0
        else:
            n.extra["t_year"] = None; n.extra["year_prov"] = "undated"
        log["nodes"][n.uid] = (n.extra["t_year"], n.extra["year_prov"])
    # 3. undated edges: max of endpoint years; undated nodes: project year
    for n in g.nodes.values():
        if n.extra["t_year"] is None:
            n.extra["t_year"] = PROJECT_YEAR; n.extra["year_prov"] = "project"
    for r in g.routes.values():
        if r.extra.get("t_year") is None:
            ends = [g.nodes[u].extra["t_year"] for u in r.inputs + [r.target]]
            r.extra["t_year"] = max(ends); r.extra["year_prov"] = "propagated"
    # 4. filtration: an edge cannot precede its endpoints (true by construction for dated nodes; assert)
    viol = 0
    for r in g.routes.values():
        for u in r.inputs + [r.target]:
            if g.nodes[u].extra["t_year"] > r.extra["t_year"]:
                viol += 1
    log["forward_violations"] = viol
    return log


def date_hep(g: Graph) -> Dict[str, Any]:
    raw = hep_raw()
    step_start = {}
    for i, s in enumerate(raw["steps"], start=1):
        y = _first_year(s.get("years") or "")
        step_start[i] = y
    log = {"nodes": {}, "routes": {}, "adjusted_routes": 0}
    for n in g.nodes.values():
        y = _first_year(n.extra.get("years") or "")
        if y is None:
            steps = n.extra.get("steps_present") or []
            y = step_start.get(steps[0], 1925) if steps else 1925
            prov = "step"
        else:
            prov = "node-years"
        n.extra["t_year"] = y; n.extra["year_prov"] = prov
        log["nodes"][n.uid] = (y, prov)
    for r in g.routes.values():
        st = r.extra.get("step")
        sidx = next((i for i, s in enumerate(raw["steps"], start=1) if s["id"] == st), None)
        base = step_start.get(sidx) if sidx else None
        ends = [g.nodes[u].extra["t_year"] for u in r.inputs + [r.target]]
        y = max([e for e in ends] + ([base] if base else []))
        if base and y > base:
            log["adjusted_routes"] += 1
        r.extra["t_year"] = y; r.extra["year_prov"] = "step+endpoints"
        log["routes"][r.uid] = (y, "step+endpoints")
    return log


def date_em(g: Graph) -> Dict[str, Any]:
    d = _read("em_v3.1.json")
    sec_start = {s["index"]: _first_year(s["years"]) or 1600 for s in d["sections"]}
    para_year: Dict[int, Tuple[int, str]] = {}
    last_in_sec: Dict[int, int] = {}
    for p in d["paragraphs"]:
        y = _first_year(p["text"])
        if y is not None:
            para_year[p["index"]] = (y, "paragraph"); last_in_sec[p["section"]] = y
        elif p["section"] in last_in_sec:
            para_year[p["index"]] = (last_in_sec[p["section"]], "carried")
        else:
            para_year[p["index"]] = (sec_start[p["section"]], "section")
    log = {"paragraphs": para_year, "adjusted_routes": 0}
    for n in g.nodes.values():
        y, prov = para_year[int(n.t)]
        n.extra["t_year"] = y; n.extra["year_prov"] = prov
    for r in g.routes.values():
        y, prov = para_year[int(r.t)]
        ends = [g.nodes[u].extra["t_year"] for u in r.inputs + [r.target]]
        y2 = max([y] + ends)
        if y2 > y:
            log["adjusted_routes"] += 1
        r.extra["t_year"] = y2; r.extra["year_prov"] = prov if y2 == y else "propagated"
    return log


def dated_graphs(mode: str = "min") -> Tuple[Dict[str, Graph], Dict[str, Any]]:
    gs = {"EM": load_em(), "HEP": load_hep(), "GPT": load_gpt(), "QRT": load_qrt()}
    logs = {"EM": date_em(gs["EM"]), "HEP": date_hep(gs["HEP"]), "GPT": date_type_E(gs["GPT"], mode), "QRT": date_type_E(gs["QRT"], mode)}
    return gs, logs


def provenance_summary(gs: Dict[str, Graph]) -> Dict[str, Dict[str, int]]:
    out = {}
    for b, g in gs.items():
        c: Dict[str, int] = {}
        for n in g.nodes.values():
            p = n.extra.get("year_prov", "?").split(":")[0]
            c["node:" + p] = c.get("node:" + p, 0) + 1
        for r in g.routes.values():
            p = r.extra.get("year_prov", "?")
            c["route:" + p] = c.get("route:" + p, 0) + 1
        out[b] = c
    return out


# ---------------------------------------------------------------------------
# HEP union graph: every node and route that ever existed, with first/last step and year
# ---------------------------------------------------------------------------
def load_hep_union() -> Tuple[Graph, Dict[str, Any]]:
    """Union over the twelve step graphs: a route is keyed by (kind, inputs, target) and dated at its first step;
    nodes carry steps_present; the removal step of nodes and routes is recorded in extra['t_removed_step']."""
    from .load import load_hep_steps
    from .schema import Route
    br, steps, raw = load_hep_steps()
    step_start = {i: _first_year(s.get("years") or "") for i, s in enumerate(raw["steps"], start=1)}
    g = Graph(br)
    first_step: Dict[str, int] = {}; last_step: Dict[str, int] = {}
    for gs in steps:
        for n in gs.nodes.values():
            first_step.setdefault(n.uid, gs.step["index"]); last_step[n.uid] = gs.step["index"]
    atlas = load_hep()  # for node year fields
    for uid in first_step:
        n = atlas.nodes[uid]
        y = _first_year(n.extra.get("years") or "")
        prov = "node-years"
        if y is None:
            y = step_start[first_step[uid]]; prov = "step"
        n.extra["t_year"] = y; n.extra["year_prov"] = prov
        n.extra["step_first"] = first_step[uid]; n.extra["step_last"] = last_step[uid]
        n.extra["removed"] = last_step[uid] < 12
        g.add_node(n)
    seen: Dict[Tuple, Route] = {}
    for gs in steps:
        for r in gs.routes.values():
            key = (r.kind, tuple(r.inputs), r.target)
            if key not in seen:
                r2 = Route(uid=r.uid, branch="HEP", native_id=r.native_id, inputs=list(r.inputs), target=r.target, logic=r.logic, kind=r.kind,
                           kind_native=r.kind_native, status=r.status, polarity=r.polarity, t=r.t, extra=dict(r.extra))
                r2.extra["step_first"] = gs.step["index"]; r2.extra["step_last"] = gs.step["index"]
                seen[key] = r2
            else:
                seen[key].extra["step_last"] = gs.step["index"]
    adjusted = 0
    for r in seen.values():
        base = step_start[r.extra["step_first"]]
        ends = [g.nodes[u].extra["t_year"] for u in r.inputs + [r.target]]
        y = max(ends + [base])
        if y > base:
            adjusted += 1
        r.extra["t_year"] = y; r.extra["year_prov"] = "step+endpoints"; r.extra["removed"] = r.extra["step_last"] < 12
        g.add_route(r)
    # routes of the atlas view that are not step routes: observable families (dated at the member's year),
    # cluster lineage and cluster membership (the reduce operations of the final view, dated at the successor's year)
    for r in atlas.routes.values():
        if r.kind_native in ("observable_family", "cluster_lineage", "cluster_member"):
            r2 = Route(uid=r.uid, branch="HEP", native_id=r.native_id, inputs=list(r.inputs), target=r.target, logic=r.logic, kind=r.kind,
                       kind_native=r.kind_native, status=r.status, polarity=r.polarity, t=r.t, extra=dict(r.extra))
            ends = [g.nodes[u].extra["t_year"] for u in r.inputs + [r.target]]
            r2.extra["t_year"] = max(ends); r2.extra["year_prov"] = "endpoints"
            r2.extra["step_first"] = 4 if r.kind_native == "observable_family" else 12; r2.extra["step_last"] = 12; r2.extra["removed"] = False
            g.add_route(r2)
    g.clusters = atlas.clusters
    g.extra = atlas.extra
    return g, {"adjusted_routes": adjusted, "routes": len(g.routes), "nodes": len(g.nodes),
               "removed_nodes": sum(1 for n in g.nodes.values() if n.extra["removed"]), "removed_routes": sum(1 for r in g.routes.values() if r.extra["removed"])}


def dated_graphs_union() -> Tuple[Dict[str, Graph], Dict[str, Any]]:
    """Like dated_graphs but with the HEP union graph (all routes ever present) in place of the atlas view."""
    gs, logs = dated_graphs()
    hu, hlog = load_hep_union()
    gs["HEP"] = hu; logs["HEP"] = hlog
    return gs, logs
