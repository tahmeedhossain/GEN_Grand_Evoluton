"""Write TWO_TIER.md (Part III) from the built network.  Every number in the text is computed here from
the data; each breakdown asserts the composition it describes, so a rebuild that changes the data
fails here instead of leaving a wrong sentence."""
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # repository root
NOTES = os.path.join(HERE, 'TWO_TIER.md')
MEMBER_REL = ('member', 'cut', 'aggregate', 'excluded')


def _prefix(e):
    a, b = e['id'].split('.', 1)
    return a + '.' + ''.join(ch for ch in b if not ch.isdigit())


def write_notes(full):
    N = full['numbers']
    nodes = {n['uid']: n for n in full['nodes']}
    abst = full['abst']
    st = [e for e in abst if e['origin'] != 'closure']
    cl = [e for e in abst if e['origin'] == 'closure']
    K = N['kernel']

    def L(u):
        return nodes[u]['label']

    def tier(u):
        return nodes[u]['tier']

    def ids(xs):
        return ', '.join(x.split(':', 1)[1] for x in xs)

    tiers = Counter(n['tier'] for n in nodes.values())
    flow = N['flow']

    def f(k):
        return flow.get(k, 0)

    # ---- section 1: direction of the abstraction edges
    a2c = [e for e in st if all(tier(s) == 'A' for s in e['src']) and tier(e['dst']) == 'C']
    a2c_rel = Counter(e['rel'] for e in a2c)
    assert set(a2c_rel) <= {'subset', 'refines'}, a2c_rel
    assert {e['dst'] for e in a2c if e['rel'] == 'subset'} == {'EM:hilb'}
    ref = [e for e in a2c if e['rel'] == 'refines']
    assert {e['src'][0] for e in ref} == {'GPT:m-quantum'}
    assert a2c_rel['subset'] == N['carrier_inclusions']
    assert not any(k.startswith('A→C') for k in flow)

    cc = [e for e in st if e['rel'] in MEMBER_REL and all(tier(s) == 'C' for s in e['src']) and tier(e['dst']) == 'C']
    aa = [e for e in st if e['rel'] in MEMBER_REL and all(tier(s) == 'A' for s in e['src']) and tier(e['dst']) == 'A']
    ca = [e for e in st if e['rel'] in MEMBER_REL and any(tier(s) == 'C' for s in e['src']) and tier(e['dst']) == 'A']
    assert all(all(tier(s) == 'C' for s in e['src']) for e in ca)
    total_mem = len(cc) + len(aa) + len(ca)
    assert total_mem == sum(flow.values())
    crit_cc = Counter(e['crit'] for e in cc)
    assert set(crit_cc) == {'sym', 'str', 'lin', 'fam', 'agg'}, crit_cc
    pre = defaultdict(Counter)
    for e in cc:
        pre[e['crit']][_prefix(e)] += 1
    assert pre['sym'] == Counter({'h.ext': pre['sym']['h.ext'], 'h.part': pre['sym']['h.part'], 'x.fam': pre['sym']['x.fam']})
    assert pre['lin'] == Counter({'h.mcl': crit_cc['lin']}) and pre['str'] == Counter({'h.grp': crit_cc['str']})
    assert set(pre['fam']) == {'x.fam', 'h.fam'} and set(pre['agg']) == {'l.agg', 'x.agg', 'x.fam'}
    assert all(nodes[e['src'][0]]['sub'] == 'S.dist' and nodes[e['src'][0]]['branch'] == 'QRT' for e in aa)
    ca_native = [e for e in ca if e['origin'] == 'native']
    ca_cur = [e for e in ca if e['origin'].startswith('curated')]
    assert len(ca_native) + len(ca_cur) == len(ca)
    assert sorted(e['id'] for e in ca_native) == ['x.fam017', 'x.gm001', 'x.gm002'], [e['id'] for e in ca_native]
    ca_dated = [e for e in ca if e['year'] is not None]
    no_member = N['classes_no_member']

    # ---- section 2: totals
    by_origin = N['abst_by_origin']
    stm_ids = sorted({e['prov'].split()[0].split(':')[1] for e in st if e['id'].startswith('q.stm')},
                     key=lambda x: (int(''.join(c for c in x if c.isdigit())), x))
    cur = [e for e in st if e['origin'].startswith('curated')]
    cur_sector = [e for e in cur if _prefix(e) == 'h.ext']
    cur_ca = [e for e in cur if e in ca]
    assert len(cur_sector) + len(cur_ca) == len(cur), (len(cur_sector), len(cur_ca), len(cur))
    crit_types = N['crit_types']
    crit_line = ', '.join('%s %d' % (k, v) for k, v in sorted(crit_types.items(), key=lambda kv: (-kv[1], kv[0])))

    # ---- section 4: events
    ev = N['events']
    ph = ['observe', 'deficit', 'hypothesize', 'restructure', 'predict', 'falsify', 'calibrate', 'reduce',
          'abstract', 'instantiate']

    def row(T, name):
        cells = [str(ev.get(T + '.' + p, 0)) if T != 'X' or p in ('abstract', 'instantiate') else '' for p in ph]
        return '| %s | %s |' % (name, ' | '.join(cells))

    und = Counter(e['stage'] for e in abst if e['year'] is None)
    assert sum(und.values()) == N['abst_undated']
    materialized = [u for u, n in nodes.items() if n.get('materialized')]
    fi = N['firsts']

    abst_by_id = {e['id']: e for e in abst}
    CONNECT = {'member': 'in', 'aggregate': 'in', 'cut': 'cut by', 'lineage': '→', 'reify': 'reified as'}

    def first(k):
        x = fi[k]
        rel = abst_by_id[x['edge']]['rel']
        return '%d (%s %s %s)' % (x['year'], ' + '.join(L(s) for s in x['src']), CONNECT[rel], L(x['dst']))

    # ---- section 6: closure
    cls_of = {m: c['id'] for c in full['classes'] for m in c['nodes']}
    assert all(e['dst'] in cls_of for e in cl)
    cl_C = [e for e in cl if tier(e['src'][0]) == 'C']
    examples = []
    for u in ('UP:bbrad', 'UP:pib', 'UP:qho', 'UP:wpack'):
        ins = sorted({L(e['dst']) for e in cl_C if e['src'][0] == u and e['rel'] == 'member'})
        examples.append('%s: %s' % (L(u).lower() if u != 'UP:wpack' else 'a wave packet', ', '.join(ins)))
    C = N['census']
    repeats = N['closure']['derived'] - C['derived']

    # ---- section 7: kernel
    kr = K['rounds']

    def krow(r, j, label):
        lv = kr[r]['levels'][j]
        c = lv['counts']
        cand = lv['candidates']
        cand_s = '%d%s' % (len(cand), (': ' + ', '.join(cand)) if 0 < len(cand) <= 8 else '')
        return '| %d | %s | %d | %d | %d | %s |' % (kr[r]['n_objects'], label, c.get('recorded', 0), c.get('transitive', 0),
                                                   c.get('refuted', 0), cand_s)
    lv_label = ['QRT', 'QRT + GPT:S7', 'QRT + GPT:S7 + GPT:R1']
    assert [l['level'] for l in kr[0]['levels']] == ['QRT', 'QRT+GPT', 'QRT+GPT+R1']
    for r in kr:
        for l in r['levels']:
            assert l['contradictions'] == 0
    s0 = kr[1]
    dc = full['detail_counts']
    x_dated = [e for e in st if e['year'] is not None and len({tier(s) for s in e['src']} | {tier(e['dst'])}) > 1]
    x_routes = [r for r in full['routes'] if len({tier(u) for u in r['inputs']} | {tier(r['target'])}) > 1]
    props = '\n'.join('- %s (%s; %s). %s Evidence: %s' % (p['id'], p['net'], p['kind'], p['text'], p['evidence'])
                      for p in full['proposals'])

    text = f"""# Two-tier network: clustering of states and observables as an epistemic operation (Part III)

Main network of this repository since 20 November 2026. Built by Claude (Anthropic) for Tahmeed Hossain, without independent review. This file is generated by `two_tier/notes.py` from the build of {N['generated']}; rebuild with `python3 build_two_tier.py`.

- Page: `gen_two_tier_explorer.html` (also opened by `index.html`). Views: Evolution, Combined pipeline, Clusters, Checks, Method. Every node and line opens its statement, its references and, where they exist, the cells of the two-qubit kernel.
- Tierless version (Parts I and II): `gen_evolution_explorer.html` and `gen_grand_explorer.html`, with the thesis `GEN_grand_thesis.pdf`. Their content is unchanged; they gained the Version button that sits at the bottom left of every page and switches between the three pages.
- Data: `data/gen_two_tier_network.json` (nodes, routes, abstraction edges, classes, effects, incidence table, kernel table, timeline, numbers), `out/two_tier_numbers.json` (every number quoted here), `out/two_tier_context.json` (kernel table).

Part I of this repository merged six concept graphs; Part II dated the four with a history (EM, HEP, GPT, QRT) and attributed every event to one of eight method phases. Part III reads the merged network at two levels of abstraction and adds the clustering of states and observables as an operation of the method.

## 1. The claim and what the data says

Claim. A state or observable node of the generic networks (GEN_GPT_Level, GEN_QRT_Level) is a cluster of state or observable nodes of the system-specific networks (GEN_epistemic_evolution, GEN_HEP, GEN_Learning, GEN_LocGlob_Flow).

To test it, every node gets a tier. Tier C (system-specific, {tiers['C']} nodes): EM, HEP, UP, LG. Tier A (generic, {tiers['A']} nodes): GPT, QRT. The relation "is a member of" is recorded as an abstraction edge (section 2). One count per edge, stated edges only:

| members → cluster | member | cut | aggregate | excluded |
|---|---|---|---|---|
| C → C | {f('C→C member')} | {f('C→C cut') or ''} | {f('C→C aggregate') or ''} | {f('C→C excluded') or ''} |
| A → A | {f('A→A member')} | {f('A→A cut') or ''} | {f('A→A aggregate') or ''} | {f('A→A excluded') or ''} |
| C → A | {f('C→A member')} | {f('C→A cut') or ''} | {f('C→A aggregate') or ''} | {f('C→A excluded') or ''} |
| A → C | 0 | 0 | 0 | 0 |

Reading.

1. The direction of the claim holds: no generic node is a member of a system-specific cluster. {len(a2c)} abstraction edges run from A to C and none is a membership: {a2c_rel['subset']} are inclusions of a generic cluster in the quantum state space of the electromagnetism reader (EM:hilb), the carrier that the cluster divides; {a2c_rel['refines']} are Part I cross-edges from the model node of quantum theory (GPT:m-quantum) to its realisations in the readers ({', '.join(sorted(e['dst'] for e in ref))}).
2. Clustering is not confined to the passage between the tiers. {len(cc)} of the {total_mem} stated membership edges lie inside tier C: {crit_cc['sym']} by symmetry ({pre['sym']['h.part']} Wigner classes as parts of the one-particle space, rule R1; {pre['sym']['h.ext']} Fock sectors as members of their Wigner class; {pre['sym']['x.fam']} Part I cross-edge), {crit_cc['str']} sectors as members of the groups that stand as one leg of a route, {crit_cc['lin']} model nodes as members of a term of the Standard Model Lagrangian or of the candidate cluster beyond it (Step 12), {crit_cc['fam']} members of families of observables or systems ({pre['fam']['h.fam']} observable families of the Standard Model graph, {pre['fam']['x.fam']} Part I cross-edges), {crit_cc['agg']} aggregates (local energies summed to a region total, parts of a field energy, sectors of a Fock space). {len(aa)} lie inside tier A, and all their members are distinguished states of the resource-theory network.
3. The released data realise the claim for few nodes. Of the {len(ca)} C → A edges, {len(ca_native)} come from Part I (one cross-edge, the heat engine of the textbook reader as a member of work extraction and conversion, a resource-utilizing operation of the athermality theory; two glue concepts read as memberships: the Maxwell–Boltzmann distribution in the thermal states, double-slit interference in second-order interference) and {len(ca_cur)} were curated on 18 November 2026. {len(ca) - len(ca_dated)} of the {len(ca)} have an end in the textbook reader and no year. After the closure (section 6), {N['classes_with_C_member']} of the {N['classes']} state classes and {sum(1 for x in full['effects'] if x['members_C'])} of the {N['effects']} effects have a member from tier C. The other classes have only distinguished states of the resource-theory network as members, or no member ({ids(no_member)}).

So the claim describes the intended relation between the two kinds of network, and the missing C → A memberships are a list of edges to add (proposals P9, P10).

## 2. Abstraction edges

A route (Part I) says that a target follows from its inputs. An abstraction edge relates the extensions of two nodes. Kinds:

- member, excluded: every state (datum) denoted by the source is in the cluster, or none is.
- cut: only part of the source is in the cluster. Cuts are recorded and not used in the closure.
- subset, equal, complement, disjoint: between clusters.
- aggregate: the target is a sum, a direct sum or a moment of its sources.
- criterion: a model-layer node supplies the predicate of the cluster. test: an observable-layer functional decides membership. lineage: a model was absorbed.
- hosts, reify, refines: a model hosts a cluster; an observable-layer cluster is taken as an object of the state layer of a resource theory; an inclusion of process classes or of models (Part I cross-edge kept as recorded).

Criterion types. Four are the typology of free-operation justifications of the resource-theory network (node F-TYPE, the family attribute of each theory, proposition QP1): invariance under a group (sym), membership in a subtheory (sub), factorisation over a partition (par), a constraint (con). The released data use five more: deficit against a reference model with a witness (def), same process type or system (fam), aggregation (agg), substitution in a route (str), model lineage (lin). Counts over stated criterion, member, cut and aggregate edges: {crit_line}.

Well-formedness (three legs, one per layer). A cluster node is well formed when it has a criterion edge from the model layer, a test edge from the observable layer and at least one member. For an effect the criterion is a no-go edge from a model or an axiom.

Total: {N['abst']} abstraction edges, {N['abst_stated']} stated and {N['closure']['derived']} derived by closure. Origin of the stated ones: {by_origin.get('native', 0)} taken from the released graphs (edges, partitions, clusters, families) and from the cross-edges and glue concepts of Part I, {by_origin.get('native (theory band)', 0)} from the theory band of the resource-theory network (model, free set, resource set of one theory), {by_origin.get('native (read from a released statement)', 0)} read from released statements ({', '.join(stm_ids)}), {len(cur)} curated on 18 November 2026 ({len(cur_sector)} assign a sector of the Standard Model graph to its Wigner class; {len(cur_ca)} are memberships or cuts of system-specific nodes in generic clusters). {N['abst_restating_route']} of the stated edges restate a released route.

## 3. Operations and rules

Operations added: CLUSTER (f ; U → c), TEST (w → c), AGGREGATE (U → c), LIFT, DESCEND, REFINE, REIFY (an observable-layer cluster placed in the state layer of a resource theory, a glue with a role flip).

Rules added (R1 to R16 are in Part II).

- R17, state clustering. Guard: a model-layer node f supplies a predicate that separates state nodes, or routes into one target differ only by one leg. Action: add the cluster node, its complement where a carrier is fixed, the criterion edge from f and the member edges. R1 (symmetry partition, GEN_HEP) is the case of an invariance inside one system.
- R18, observable clustering, three forms. Family: observables of one process type are members of a family node. Aggregate: a node is a sum or a moment of its members. Effect: given a reference model m0 and a functional w that m0 bounds, the effect is the set of observable data outside the bound, with a no-go edge from m0, the test edge from w and the member edges.
- R19, lift. Guard: two clusters with members and no edge between them, and either a member-level route from one into the other or an implication of the incidence table. Action: add the edge with status open; rule R14 closes it.
- R20, descent. Guard: an inclusion a ⊆ b with status theorem or definition, a member u of a, u an object of the kind on which b is defined, and the frame of the inclusion holds for u. Action: add u ∈ b with status derived, and the excluded edge for the complement. With a witness of b and measured data of u the status is observed; no membership in the released data has that status, so R20 fires here only through the closure.
- R21, refinement. Guard: a derived fact contradicts a stated one, or an implication of the incidence table is refuted by an object. Action: split the cluster, add the counterexample as an atom, or restrict the inclusion to a frame.

Relation to the history graphs. In GEN_HEP an observable with no route from the current model (rule R2) drives a change of the model and is resolved within a few steps. An effect of the generic tier is the same deficit with the reference model kept fixed: the set of data that the reference model cannot produce becomes a node, and the witness is its test. In the released data {N['effects_with_reference']} of the {N['effects']} effects carry such a no-go edge from a model or axiom node; the other {N['effects'] - N['effects_with_reference']} are flagged (P6).

## 4. The combined pipeline

A stage is a phase in a tier. Phases: the eight of Part II (observe, deficit, hypothesize, restructure, predict, falsify, calibrate, reduce) followed by cluster and descend. Tier of an event: the tier of the node, of the target of the route, or of the two ends of the abstraction edge; an abstraction edge with one end in each tier counts as crossing (row "across"). The attribution is a lookup table (`two_tier/pipeline.py`): a node of a cluster sublayer, or a route that an abstraction edge restates, moves to the phase cluster; an edge derived by closure is in the phase descend.

Dated events ({N['nodes_dated']} nodes, {N['routes_dated']} routes, {N['events_extra_abst']} abstraction edges that restate no route; {N['events_total']} in all):

| tier | {' | '.join(p if p not in ('abstract', 'instantiate') else {'abstract': 'cluster', 'instantiate': 'descend'}[p] for p in ph)} |
|{'---|' * (len(ph) + 1)}
{row('A', 'A (generic)')}
{row('X', 'across')}
{row('C', 'C (system-specific)')}

In the generic tier the phases carry other content: observe is a witness tied to what it detects, deficit is the census of unconnected pairs (R13), hypothesize is a conjectured edge or an axiom, falsify is a no-go edge, reduce is an equivalence.

{N['abst_undated']} abstraction edges have an end in UP or LG and no year ({und.get('C.abstract', 0)} inside C, {und.get('X.abstract', 0)} cluster edges across, {und.get('X.instantiate', 0)} descend edges across). Applied to the dated nodes and routes, the eight-phase table of Part II gives {N['events8_total']} events; the dated nodes include the {len(materialized)} group nodes of the Standard Model graph ({ids(sorted(materialized))}) that this network makes explicit. No route of the released graphs has ends in both tiers; the lines between the tiers on the map are the {len(x_dated)} dated stated abstraction edges with one end in each tier.

First occurrences in the chronology of Part II (year of the earliest cited source): model lineage R10 {first('R10')}, family of observables R18 {first('R18')}, first membership R17 {first('R17')}, Wigner partition R1 {first('R1')}, first reification {first('REIFY')}, first dated C → A membership or cut {first('first C→A membership')}, first derived membership R20 {first('R20')}.

## 5. Sources

{N['nodes']} nodes and {N['routes']} routes: {', '.join('%s %d' % (b, N['nodes_by_branch'][b]) for b in ('EM', 'HEP', 'UP', 'LG', 'GPT', 'QRT'))} nodes (Part I and Part II data of this repository; commits GEN_epistemic_evolution 17bde64, GEN_LocGlob_Flow 42751ee, GEN_Learning c6e2fa4, GEN_HEP 4258f6e, GEN_GPT_Level e18fa8c, GEN_QRT_Level 198ca02). HEP counts the {len(materialized)} group nodes added here. UP and LG have no years and are absent from the time axis.

## 6. Closure of the memberships (rule R20)

Facts are signed pairs (u, c). u ∈ c means that every state denoted by the node u lies in c; u ∉ c means that none does. Rules:

1. u ∈ a and a ⊆ b give u ∈ b.
2. u ∉ b and a ⊆ b give u ∉ a.
3. u ∈ a and a, b disjoint give u ∉ b.
4. u ∉ a and b the complement of a give u ∈ b.

Rules 1 to 3 hold for arbitrary sets. Rule 4 needs u inside the carrier of the pair, so a conclusion about c is drawn only when u is an object of the kind on which c is defined (domain tags: any, bipartite, qudit, continuous variable, behaviour, device). An inclusion stated under a frame is used only for atoms that carry the frame: E, the coherence basis is the eigenbasis of a nondegenerate Hamiltonian; P, the atom is bipartite with a local product coherence basis. The fixed point is the least one; each derived fact keeps the edges it comes from. The tags were assigned by hand (`two_tier/abstraction.py`, tables INCLUSIONS, ATOM_DOMAINS, ATOM_FRAMES).

Result: {N['closure']['stated']} stated facts on {N['closure']['atoms']} atoms, {N['closure']['inclusions']} inclusions, {N['closure']['disjoint']} disjointness edges, the complement pairs and the glue give {N['closure']['derived']} derived facts at node level ({N['closure']['derived_in']} memberships, {N['closure']['derived_out']} exclusions) and {N['closure']['conflicts']} conflicts. {len(cl_C)} of them concern tier-C atoms. Derived memberships of four of them: {'; '.join(examples)}.

Incidence table of {C['atoms']} atoms and the {C['classes']} state classes that remain after glue: {C['applicable']} applicable cells, {C['known']} settled ({C['stated']} stated, {C['derived']} derived only, {C['cut']} cuts). The other {repeats} derived facts repeat a settled cell on the second node of a glue class. The {C['applicable'] - C['known']} empty cells are open items in the sense of R13.

Refinements made while building (rule R21). A first closure run derived that the Gibbs state is separable through QRT:SS1 and that a single-particle stationary state is "not entangled". Both are wrong readings: the energy eigenbasis of an interacting Hamiltonian is not a product basis (QRT:SS3 records the Gibbs state of a generic interacting H as magic), and entanglement is not defined for a single system. The inclusions were restricted to frames and every conclusion to the domain of its cluster.

## 7. Kernel: ten free sets on explicit two-qubit states

Purpose: check that the inclusion structure of the generic tier is recoverable from concrete members. Objects: {kr[0]['n_objects']} two-qubit density matrices, of which 8 realise 7 of the 9 distinguished states of the resource-theory network (the bound entangled state and the Wigner-positive magic state have no two-qubit realisation) and 5 are reference states; {kr[1]['n_objects'] - kr[0]['n_objects']} more were added in a second round. Frame: H = (ωA/2) Z⊗1 + (ωB/2) 1⊗Z, ωA = 1, ωB = 1.5, β = 2 (nondegenerate total spectrum). Attributes: membership in the free sets of purity, athermality, asymmetry, coherence, imaginarity, magic (linear program over the {K['stabilizer_states']} two-qubit stabilizer states), discord (numerical minimisation over local bases), entanglement (PPT, exact for two qubits), steering and Bell nonlocality (CHSH by the Horodecki criterion; separable ⇒ unsteerable ⇒ local). Four cells are imported thresholds for the Werner states at p = 0.4 and p = 0.6.

Implications "free in a ⇒ free in b" of the table (single-premise fragment of attribute exploration), compared with the released inclusions:

| objects | edges used | recorded | transitive | refuted | candidates |
|---|---|---|---|---|---|
{krow(0, 0, lv_label[0])}
{krow(0, 1, lv_label[1])}
{krow(0, 2, lv_label[2])}
{krow(1, 0, lv_label[0])}
{krow(1, 1, lv_label[1])}
{krow(1, 2, lv_label[2])}

No released inclusion is refuted. With the resource-theory edges alone the discord column is unconnected. GPT:S7 (zero-discord states are separable) and GPT:R1 (proposition of the nonclassicality network: for a noninteracting H with nondegenerate total spectrum, symmetric states are classical-classical) account for all candidates except mag⇒ima, which is false and survives only because no named state is a stabilizer state with an imaginary density matrix; the added state |+i⟩|0⟩ refutes it. All {s0['strict']} released strictness claims have a witness among the objects, {s0['strict_import_only']} of them only through the imported Werner thresholds. Cross-check: {K['crosscheck']['facts']} membership facts of the closure, stated or derived, concern a state realised in the table; each is compared with every object that realises it ({K['crosscheck']['compared']} comparisons, the Werner states being realised by two objects), and {K['crosscheck']['agree']} of the {K['crosscheck']['compared']} agree with the computed cell.

## 8. Proposals for the released graphs (not applied)

{props}

## 9. Limits

- Years are the ingredient chronology of Part II, not historical dates. Curated edges are dated 2026.
- The {len(cur)} curated edges rest on the node definitions as written in the released data. Those with status standard are textbook identifications that were not derived here.
- The frame and domain tags of the closure were assigned by hand.
- Kernel: tolerance 1e-9; the discord test is a numerical minimisation; the cell "Bell-local" of the Werner state at p = 0.6 holds for projective measurements only (Acín, Gisin, Toner, arXiv:quant-ph/0606138); locality under general measurements is not established at this p.
- Only the single-premise implications of the incidence table were computed, not a full attribute exploration.

## 10. What the page shows for a selected node or line

The statements are embedded in the page ({sum(dc.values())} records: {dc.get('r', 0)} routes, {dc.get('n', 0)} nodes, {dc.get('a', 0)} of the {N['abst']} abstraction edges, {dc.get('s', 0)} steps of the Standard Model graph; an abstraction edge without a record rests on the definitions of its two nodes) and read when something is first selected. Every field is copied from a source file; only the links between records are computed (`two_tier/detail.py`).

- A route: the full statement and the references of the edge in its source graph (GEN_GPT_Level v2.6, GEN_QRT_Level v1.2); for GEN_HEP the step with its text and references; for the EM and textbook readers the section; the rule that fixed its year.
- An abstraction edge: the routes it rests on, with the same content; the chain of edges for one derived by rule R20; the cells of the two-qubit table when the member is one of its states; the shared concept of Part I when the edge comes from glue.

## 11. References

- B. Ganter, R. Wille, Formal Concept Analysis: Mathematical Foundations (Springer, 1999), doi:10.1007/978-3-642-59830-2.
- B. Ganter, S. Obiedkov, Conceptual Exploration (Springer, 2016), doi:10.1007/978-3-662-49291-8.
- F. Lorrain, H. C. White, J. Math. Sociol. 1, 49 (1971), doi:10.1080/0022250X.1971.9989788 (structural equivalence; the substitution criterion).
- L. Floridi, Minds and Machines 18, 303 (2008), doi:10.1007/s11023-008-9113-7 (levels of abstraction).
- R. Horodecki, P. Horodecki, M. Horodecki, Phys. Lett. A 200, 340 (1995), doi:10.1016/0375-9601(95)00214-N (CHSH criterion for two qubits).
- R. F. Werner, Phys. Rev. A 40, 4277 (1989); J. Barrett, Phys. Rev. A 65, 042302 (2002); H. M. Wiseman, S. J. Jones, A. C. Doherty, Phys. Rev. Lett. 98, 140402 (2007); A. Acín, N. Gisin, B. Toner, arXiv:quant-ph/0606138 (Werner-state thresholds).
- Released statements are cited by edge id of the graph they belong to (QRT:SSn, GPT:Sn, GPT:R1).
"""
    open(NOTES, 'w', encoding='utf-8').write(text)
    return dict(file='TWO_TIER.md', bytes=os.path.getsize(NOTES))
