"""Primitive graph operations of the Grand Epistemic Network and their count deltas.

Every change of a concept graph in the six instances decomposes into these
operations (Chapter 5 of the thesis).  The table OPS gives, for each
operation, the layer it acts on, the change of the node count of that layer,
the change of the route count, and the rule(s) that fire it.  Deltas are
stated for the elementary case; the replay (replay_hep.py) measures the
actual deltas on the data.
"""

# name: (layer, delta nodes, delta routes, description)
OPS = {
    "ADD":       ("S|M|O", "+1", "+k (k = routes attached on arrival)", "a new node appears"),
    "REWRITE":   ("S|M|O", "0", "0 or re-attached", "a node keeps its identity and changes its content"),
    "PARTITION": ("S", "+(k-1)", "+k back-edges", "a state node is replaced by the k irreducible components of a symmetry representation (R1)"),
    "EXTEND":    ("S", "0 (ladders are internal)", "+1 back-edge per sector", "each irreducible block becomes a Fock ladder (R3)"),
    "SPLIT":     ("S", "+1", "routes re-attached", "a sector splits in two after an observable distinguishes them (R8)"),
    "REPLACE":   ("S", "0", "routes re-attached", "k sectors are replaced by k others after an observable shows compositeness (R8)"),
    "MERGE":     ("M", "-(k-1)", "routes = union", "k model nodes that share a calibration become one (R6)"),
    "ABSORB":    ("M", "-1 eff, +1 fund, +sectors", "+1 leg per route; +lineage", "an effective node becomes the low-energy limit of a fundamental one (R7)"),
    "CLUSTER":   ("M", "+1 cluster per term", "routes re-attached to clusters; +member/lineage edges", "fundamental nodes grouped by Lagrangian term (R10)"),
    "LINEAGE":   ("M->M", "0", "+1", "an absorption trace recorded inside a cluster"),
    "ROUTE":     ("S->M", "0", "+1 AND route", "legs = (sector, n) pairs of the fields of a term (R4)"),
    "PREDICT":   ("M->O", "0", "+1", "a model node reaches an observable (status pred)"),
    "CALIBRATE": ("M->O", "0", "+1 (status fit)", "an observable fixes a parameter (R9)"),
    "FLAG":      ("O", "0", "0", "an observable has in-degree 0 from the model layer (R2 precondition)"),
    "SIGNAL":    ("M", "0", "0", "two model nodes share a calibration edge (R6 precondition)"),
    "BACK":      ("M->S", "0", "+1", "a model node acts on the state layer"),
    "DERIVE":    ("M∧S->S|O (type D)", "0 or +1", "+1 AND route", "a reading-indexed route combines model and state nodes (readers)"),
    "FAIL":      ("route", "0", "0 (route marked failed)", "a prediction route fails; a later route to the same target resolves it"),
    "COMPOSE":   ("S", "+1 (tensor sector)", "+routes", "a new independent sector is adjoined by tensor product (Rule II of the inference engine)"),
    "REDUCE":    ("M|S", "-(k-1)", "0", "parameters tied by symmetry, representation reduced by the commutant (Rule III of the inference engine)"),
    "CONTRACT":  ("M", "-1", "S->O direct edges replace 2-paths", "a fixed model node is suppressed: an H-graph becomes an E-graph (Prop. contraction)"),
    "LIFT":      ("M", "+1", "2-paths replace S->O edges", "inverse of CONTRACT"),
    "CENSUS":    ("layer pair", "0", "0", "enumerate the cells (pairs) of a layer pair with no recorded edge"),
    "CLOSE":     ("edge", "0", "+1", "settle a cell by composition, elementary proof, counterexample or literature fill"),
}

RULES = {
    1: "symmetry partition", 2: "in-degree-zero drive", 3: "Fock extension", 4: "route composition",
    5: "effective status", 6: "universality merge", 7: "absorption", 8: "sector refinement",
    9: "calibration", 10: "clustering",
    11: "reading-order growth (readers): a node appears at the paragraph that introduces it, a route at the paragraph that explains it; no forward links",
    12: "failed-route resolution (readers): a failed route is followed by a successful route into the same target",
    13: "census (effect/resource branches): every pair of a designated layer pair without an edge is a candidate",
    14: "closure (effect/resource branches): a candidate is settled by composition, elementary proof, counterexample or literature fill",
    15: "compose (inference engine): adjoin an independent sector by tensor product when refit fails",
    16: "reduce (inference engine): tie parameters when the evidence favours it and decompose by the commutant",
}
