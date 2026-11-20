"""Universal schema of the Grand Epistemic Network (GEN-Grand).

A concept graph is G = (V, R, lambda, kappa, sigma):
  V      nodes (concepts)
  R      routes = directed hyperedges (inputs, target, logic)
  lambda layer map V -> {S, M, O}   (with a finer sub-layer)
  kappa  kind of a route (native vocabulary of the branch + a universal class)
  sigma  status of a route (epistemic footing)

Every instance of the project is normalised into this schema without
changing its content: native ids, labels, kinds and statuses are kept in
the record, and the universal fields are added next to them.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
import json

LAYERS = ("S", "M", "O")

# Sub-layers used across branches.  The first letter is the layer.
SUBLAYERS = {
    # state layer
    "S.point": "point/vector/distribution state of a dynamical system",
    "S.field": "field configuration",
    "S.hilbert": "Hilbert-space state / ray",
    "S.uir": "irreducible representation (building block)",
    "S.sector": "Fock sector with occupation ladder",
    "S.cluster": "cluster of state operators (a subset of the state space)",
    "S.free": "free set of a resource theory",
    "S.resource": "resource states of a resource theory",
    "S.dist": "distinguished shared state",
    # model layer
    "M.law": "law / equation / construction (dynamic branches)",
    "M.frame": "framework node (postulate, evolution, field construction)",
    "M.axiom": "axiom of a theory space (GPT) or of a resource framework",
    "M.model": "a concrete theory / GPT / resource theory",
    "M.fund": "fundamental interaction node (dimensionless coupling)",
    "M.eff": "effective interaction node (dimensionful coupling)",
    "M.cand": "candidate model node (not established)",
    "M.cluster": "cluster of model nodes (Lagrangian term)",
    "M.process": "process / operation class (channels, free operations)",
    # observable layer
    "O.direct": "directly measured quantity",
    "O.effect": "effect: a cluster of observable outcomes that a witness detects",
    "O.witness": "witness: operator-valued test paired with an effect",
    "O.task": "operational task powered by an effect/resource",
}

UNIVERSAL_KIND_CLASS = {
    # dynamic branches
    "derives": "structural",           # AND route: inputs jointly produce the target
    "failed": "no_go",                 # route whose prediction failed
    # historical branch
    "enters": "structural",            # state (sector, n) legs enter a model node
    "predicts": "possibility",         # model -> observable, status pred
    "calibrates": "structural",        # model -> observable, status fit (parameter fixed)
    "frames": "structural",            # model -> observable, framework assignment
    "candidate": "open",               # model -> observable, candidate
    "backedge": "structural",          # model -> state (partition / ladder)
    "lineage": "structural",           # model -> model absorption trace
    # effect / resource branches (native kinds kept)
    "implies": "possibility", "equiv": "structural", "necessary": "possibility",
    "not_implies": "no_go", "enables": "possibility", "forbids": "no_go",
    "witness": "possibility", "hides": "no_go", "generates": "structural",
    "subset": "structural", "pairs": "structural", "excludes": "no_go",
    "hosts": "structural", "open": "open",
    "specializes": "structural", "distinct": "no_go", "contains": "structural",
    "converts_to": "possibility", "activates": "possibility", "bounds": "structural",
    "member_free": "structural", "member_resource": "structural",
    "violates": "no_go", "satisfies": "structural", "irreversible": "no_go",
    "reversible": "possibility",
    # LocGlob flows
    "transport": "structural", "conversion": "structural",
}


@dataclass
class Node:
    uid: str                 # "<branch>:<native id>"
    branch: str
    native_id: str
    label: str
    layer: str               # S | M | O
    sublayer: str            # one of SUBLAYERS
    native_layer: str        # the branch's own layer word
    era: Optional[str] = None
    t: Optional[float] = None   # time index on the branch's own axis (paragraph / step / version)
    concept: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Route:
    uid: str
    branch: str
    native_id: str
    inputs: List[str]        # node uids
    target: str              # node uid
    logic: str               # AND | single
    kind: str                # universal kind
    kind_native: str
    status: str
    polarity: str            # structural | possibility | no_go | open
    t: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Branch:
    id: str
    title: str
    btype: str               # D (dynamic/pedagogical) | H (historical theory-building) | E (effect/resource)
    source: str
    version: str
    time_axis: str
    native_layers: List[str]
    layer_map: Dict[str, str]
    notes: str = ""


class Graph:
    """A concept graph with layer map and hyperedge routes."""

    def __init__(self, branch: Branch):
        self.branch = branch
        self.nodes: Dict[str, Node] = {}
        self.routes: Dict[str, Route] = {}

    # --- construction -----------------------------------------------------
    def add_node(self, n: Node):
        assert n.layer in LAYERS, n
        assert n.sublayer in SUBLAYERS, n.sublayer
        self.nodes[n.uid] = n

    def add_route(self, r: Route):
        for u in r.inputs + [r.target]:
            assert u in self.nodes, (r.uid, u)
        assert r.kind in UNIVERSAL_KIND_CLASS, r.kind
        self.routes[r.uid] = r

    # --- queries ------------------------------------------------------------
    def layer_of(self, uid: str) -> str:
        return self.nodes[uid].layer

    def nodes_in(self, layer: str) -> List[Node]:
        return [n for n in self.nodes.values() if n.layer == layer]

    def signature(self) -> Dict[Tuple[Tuple[Tuple[str, int], ...], str], int]:
        """Layer-pair signature: counts of routes by (multiset of input layers, target layer)."""
        sig: Dict = {}
        for r in self.routes.values():
            ins = {}
            for u in r.inputs:
                L = self.layer_of(u)
                ins[L] = ins.get(L, 0) + 1
            key = (tuple(sorted(ins.items())), self.layer_of(r.target))
            sig[key] = sig.get(key, 0) + 1
        return sig

    def pair_matrix(self) -> Dict[Tuple[str, str], int]:
        """Flattened signature: every (input layer, target layer) pair of every route counted once per leg."""
        m: Dict[Tuple[str, str], int] = {}
        for r in self.routes.values():
            for u in r.inputs:
                k = (self.layer_of(u), self.layer_of(r.target))
                m[k] = m.get(k, 0) + 1
        return m

    def in_routes(self, uid: str) -> List[Route]:
        return [r for r in self.routes.values() if r.target == uid]

    def out_routes(self, uid: str) -> List[Route]:
        return [r for r in self.routes.values() if uid in r.inputs]

    def or_targets(self) -> List[str]:
        """Targets with two or more routes (OR logic between alternative routes)."""
        c: Dict[str, int] = {}
        for r in self.routes.values():
            c[r.target] = c.get(r.target, 0) + 1
        return [t for t, k in c.items() if k >= 2]

    def to_json(self) -> Dict[str, Any]:
        return {
            "branch": asdict(self.branch),
            "nodes": [asdict(n) for n in self.nodes.values()],
            "routes": [asdict(r) for r in self.routes.values()],
        }


def dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
