"""The combined pipeline: operations, rules, stages, and the attribution of every event to a stage.

Part II of the grand network gave each node and route one of eight phases through a lookup table
(node: O -> observe, M -> hypothesize, S -> restructure; route: by kind).  The combined pipeline keeps
that table and adds two cross-tier phases:

  abstract     a cluster is formed or extended: a cluster node enters, or an abstraction edge
               (criterion, test, member, subset, cut, aggregate, complement) is added
  instantiate  an inclusion between clusters is carried down to a member (closure, rule R20), or a
               membership is established by a measurement through a witness

The table below is the whole of the hand-made part of the attribution.
"""
from collections import Counter, defaultdict

PHASES8 = ['observe', 'deficit', 'hypothesize', 'restructure', 'predict', 'falsify', 'calibrate', 'reduce']
PHASES = PHASES8 + ['abstract', 'instantiate']
CLUSTER_SUB = {'S.cluster', 'S.free', 'S.resource', 'S.uir', 'S.group', 'S.family', 'M.cluster', 'O.effect', 'O.witness'}
CLUSTER_REL = {'member', 'subset', 'equal', 'test', 'hosts', 'cut', 'excluded', 'aggregate', 'complement',
               'criterion', 'lineage', 'reify', 'disjoint'}
# abstraction edges that restate a released route move that route to the phase 'abstract'
RESTATE_REL = {'member', 'subset', 'equal', 'test', 'hosts', 'cut'}
OPERATIONS = [
    # id, signature, effect on counts (dV, dR, dA), meaning
    ('CLUSTER', 'f ; U -> c', '+1 node (+2 with the complement), +1 criterion edge, +|U| member edges',
     'Add a cluster node c for the set U of nodes of one layer that satisfy a predicate supplied by the model-layer node f.'),
    ('TEST', 'w -> c', '+1 witness node, +1 test edge',
     'Attach an observable-layer functional w that decides, completely or in part, whether an object is in c.'),
    ('AGGREGATE', 'U -> c', '+1 node, +|U| aggregate edges',
     'Add a node that is a sum, a direct sum or a moment of its members (total energy, Fock ladder, first moment of a distribution).'),
    ('LIFT', 'r -> (a, b)', '+1 abstract edge, status open',
     'From routes between members of a and members of b, or from an implication of the incidence table, propose an edge between the clusters.'),
    ('DESCEND', '(a subset b), u in a -> u in b', '+1 member edge, status derived',
     'Carry an inclusion between clusters down to a member; with a witness and data, the membership has status observed.'),
    ('REFINE', 'c -> c1, c2 ; or + atom', '+1 or +2 nodes',
     'Split a cluster, add a counterexample atom, or restrict an inclusion to a frame, when a derived fact contradicts a stated one or an implication is refuted.'),
    ('REIFY', 'e (O) -> s (S)', '+1 glue with a role flip',
     'An observable-layer cluster (a table of outcome statistics, a set of measurements) is taken as the object of a resource theory and placed in its state layer.'),
]

RULES = [
    # id, name, tier, layer, origin, statement
    ('R1', 'Symmetry partition', 'C', 'S', 'GEN_HEP', 'A symmetry represented on the state layer partitions it; the labels of the pieces become observables.'),
    ('R2', 'In-degree-zero drive', 'C', 'M', 'GEN_HEP', 'An observable with no route from the model layer drives a change of the model layer.'),
    ('R3', 'Fock extension', 'C', 'S', 'GEN_HEP', 'A field node extends each realized class to a sector with an occupation ladder.'),
    ('R4', 'Route composition', 'C', 'S→M', 'GEN_HEP', 'An interaction term is entered by an AND route with one leg per field of the term.'),
    ('R5', 'Effective status', 'C', 'M', 'GEN_HEP', 'A term whose coupling has negative mass dimension is marked effective from the moment it is added.'),
    ('R6', 'Universality merge', 'C', 'M', 'GEN_HEP', 'Model nodes that share one calibration are merged.'),
    ('R7', 'Absorption', 'C', 'M', 'GEN_HEP', 'An effective node is absorbed into a fundamental one; the mediator sector enters every former route.'),
    ('R8', 'Sector refinement', 'C', 'S', 'GEN_HEP', 'A state node is split or replaced only through an observable or a model back-edge.'),
    ('R9', 'Calibration', 'C', 'O→M', 'GEN_HEP', 'One parameter is fixed by one observable; the remaining edges of the node are predictions.'),
    ('R10', 'Clustering of models', 'C', 'M', 'GEN_HEP', 'Model nodes are grouped inside the term they belong to, with lineage edges.'),
    ('R11', 'Derivation', 'C', 'M∧S→S/O', 'readers', 'A node is derived by an AND route from nodes already present (no forward links).'),
    ('R12', 'Failed route', 'C', 'M∧S→O', 'readers', 'A derivation that contradicts the observable is kept as a failed route and resolved by a later node.'),
    ('R13', 'Census', 'A', 'all', 'GPT / QRT', 'Every unconnected pair or uncharted cell is listed as an open item.'),
    ('R14', 'Closure', 'A', 'all', 'GPT / QRT', 'An open item is closed by composition, by an elementary computation, by a counterexample or from the literature.'),
    ('R15', 'Composition', 'C', 'S', 'world-model engine', 'Independent new observables are composed as tensor-product sectors.'),
    ('R16', 'Reduction', 'C/A', 'M', 'world-model engine', 'A model is reduced to its simplest representation (parameter ties, commutant decomposition, equivalences).'),
    ('R17', 'State clustering', 'C, A, C→A', 'S', 'this work', 'Guard: a model-layer node f supplies a predicate that separates state nodes (an invariance, a subtheory, a partition, a constraint), or routes into one target differ only by one leg. Action: add the cluster node, its complement where a carrier is fixed, the criterion edge from f and the member edges. R1 is the case of an invariance inside one system.'),
    ('R18', 'Observable clustering', 'C, A, C→A', 'O', 'this work', 'Three forms. Family: observables of one process type are members of a family node. Aggregate: a node is a sum or a moment of its members. Effect: given a reference model m0 and a functional w that m0 bounds, the effect is the set of observable data outside the bound, with a no-go edge from m0, the test edge from w and the member edges. The effect is the deficit of rule R2 against a model that is kept fixed.'),
    ('R19', 'Lift', 'A', 'S, O', 'this work', 'Guard: two clusters with members and no edge between them, and either a member-level route from one into the other or an implication of the incidence table. Action: add the edge with status open; it is closed by R14.'),
    ('R20', 'Descent', 'A, A→C', 'S, O', 'this work', 'Guard: an inclusion a ⊆ b with status theorem or definition, a member u of a, u an object of the kind on which b is defined, and the frame of the inclusion holds for u. Action: add the member edge u ∈ b with status derived and the excluded edge for the complement. With a witness of b and measured data of u the status is observed.'),
    ('R21', 'Refinement', 'A', 'S, O', 'this work', 'Guard: a derived fact contradicts a stated one, or an implication of the incidence table is refuted by an object. Action: split the cluster, add the counterexample as an atom, or restrict the inclusion to a frame.'),
]

STAGES = [
    # id, tier, phase, title, what happens, rules.  Tier X: an abstraction edge whose ends lie in different tiers.
    ('A.observe', 'A', 'observe', 'Witness', 'A witness is tied to what it detects; a task enters.', ['R14']),
    ('A.deficit', 'A', 'deficit', 'Census', 'Unconnected pairs and uncharted cells are listed.', ['R13']),
    ('A.hypothesize', 'A', 'hypothesize', 'Conjecture', 'An axiom, a model or an open edge is proposed.', ['R19']),
    ('A.restructure', 'A', 'restructure', 'Refine', 'A distinguished state, a counterexample or a split enters.', ['R21']),
    ('A.predict', 'A', 'predict', 'Possibility', 'Implication, enabling and conversion edges between clusters.', ['R14']),
    ('A.falsify', 'A', 'falsify', 'No-go', 'Forbidding and separation edges between clusters.', ['R14']),
    ('A.calibrate', 'A', 'calibrate', 'Calibrate', 'A measured or simulated value enters as an import.', ['R9']),
    ('A.reduce', 'A', 'reduce', 'Equivalence', 'Equivalences, specializations and inclusions between clusters.', ['R14', 'R16']),
    ('A.abstract', 'A', 'abstract', 'Cluster', 'A generic cluster node enters, or a criterion, test, member or complement edge between generic nodes is added.', ['R17', 'R18']),
    ('A.instantiate', 'A', 'instantiate', 'Descend', 'An inclusion between generic clusters is carried down to a generic distinguished state.', ['R20']),
    ('X.abstract', 'X', 'abstract', 'Cluster ↑', 'An abstraction edge joins a node of a named system and a generic node: the system node is a member of a generic cluster or is cut by it, a system observable is a test of a generic cluster, or a generic cluster is a subset of a state space of the readers (its carrier).', ['R17', 'R18']),
    ('X.instantiate', 'X', 'instantiate', 'Descend ↓', 'The membership of a node of a named system in a generic cluster is derived from an inclusion between clusters, or is observed through a witness.', ['R20']),
    ('C.observe', 'C', 'observe', 'Observe', 'A direct observable of a named system enters.', ['R11']),
    ('C.deficit', 'C', 'deficit', 'Deficit', 'An observable has no route from the model layer.', ['R2']),
    ('C.hypothesize', 'C', 'hypothesize', 'Hypothesize', 'A law, a term or a frame is added or rewritten.', ['R2', 'R5']),
    ('C.restructure', 'C', 'restructure', 'Restructure', 'State nodes are added, extended, split, composed; routes enter model nodes.', ['R3', 'R4', 'R8', 'R15']),
    ('C.predict', 'C', 'predict', 'Predict', 'A route from model and state to an observable or a state.', ['R2', 'R11']),
    ('C.falsify', 'C', 'falsify', 'Falsify', 'A derivation fails against the observable.', ['R12']),
    ('C.calibrate', 'C', 'calibrate', 'Calibrate', 'An observable fixes a parameter.', ['R9']),
    ('C.reduce', 'C', 'reduce', 'Reduce', 'Models are merged, absorbed or reduced.', ['R6', 'R7', 'R16']),
    ('C.abstract', 'C', 'abstract', 'Cluster', 'Nodes of a named system are clustered inside the system: symmetry classes, sectors and groups of sectors, families of observables, clusters of terms.', ['R1', 'R10', 'R17', 'R18']),
    ('C.instantiate', 'C', 'instantiate', 'Descend', 'An inclusion between clusters of a named system is carried down to a member.', ['R20']),
]


def node_phase(n):
    if n['sub'] in CLUSTER_SUB:
        return 'abstract'
    return {'O': 'observe', 'M': 'hypothesize', 'S': 'restructure'}[n['layer']]


def attribute(nodes, routes, abst):
    """Add phase10 and stage to every node, route and abstraction edge.  Returns the route->edge map."""
    by_route = {}
    rid = {}
    for r in routes:
        rid[(r['branch'], r['rid'], r['target'])] = r
        rid.setdefault((r['branch'], r['rid']), r)
    for e in abst:
        e['route'] = None
        p = e['prov']
        r = None
        if p.startswith('QRT:') or p.startswith('GPT:'):
            br, eid = p.split(':', 1)
            eid = eid.split(' ')[0]
            if '(statement text)' not in p:
                r = rid.get((br, eid))
        elif p.startswith('Part II route '):
            r = rid.get(('HEP', p[len('Part II route '):]))
        elif p.startswith('HEP Step 12 CLUSTER (') or p.startswith('HEP lineage ('):
            r = rid.get(('HEP', p[p.index('(') + 1:-1]))
        if r is not None and e['rel'] in RESTATE_REL | {'lineage', 'criterion', 'disjoint'}:
            e['route'] = r['uid']
            if e['rel'] in RESTATE_REL:
                by_route[r['uid']] = e['id']
    def edge_tier(e):
        ts = {nodes[x]['tier'] for x in e['src']} | {nodes[e['dst']]['tier']}
        return 'X' if len(ts) > 1 else ts.pop()

    E = {e['id']: e for e in abst}
    for n in nodes.values():
        n['phase'] = node_phase(n)
        n['stage'] = n['tier'] + '.' + n['phase']
    for r in routes:
        ph = r['phase']
        r['phase8'] = ph
        tier = nodes[r['target']]['tier']
        if r['uid'] in by_route:
            ph = 'abstract'
            tier = edge_tier(E[by_route[r['uid']]])
        r['phase'] = ph
        r['stage'] = tier + '.' + ph
    for e in abst:
        if e['origin'] == 'closure' or e['status'] == 'observed':
            e['phase'] = 'instantiate'
        else:
            e['phase'] = 'abstract'
        e['stage'] = edge_tier(e) + '.' + e['phase']
        ls = nodes[e['dst']]['layer']
        if e['phase'] == 'instantiate':
            e['rule'] = 'R20'
        elif e['rel'] == 'lineage' or (ls == 'M' and e['rel'] == 'member'):
            e['rule'] = 'R10'
        elif e['rel'] == 'reify':
            e['rule'] = 'REIFY'
        elif e['rel'] == 'refines':
            e['rule'] = None
        elif ls == 'S':
            e['rule'] = 'R1' if (e['id'].startswith('h.part')) else 'R17'
        elif ls == 'O':
            e['rule'] = 'R18'
        else:
            e['rule'] = 'R17' if e['rel'] == 'criterion' else None
    return by_route


def timeline(nodes, routes, abst):
    """Events per year and stage.  An abstraction edge that restates a route is not counted twice."""
    T = defaultdict(Counter)
    for n in nodes.values():
        if n['year'] is not None:
            T[n['year']][n['stage']] += 1
    for r in routes:
        if r['year'] is not None:
            T[r['year']][r['stage']] += 1
    for e in abst:
        if e['year'] is not None and not (e.get('route') and e['rel'] in RESTATE_REL):
            T[e['year']][e['stage']] += 1
    return {y: dict(c) for y, c in sorted(T.items())}
