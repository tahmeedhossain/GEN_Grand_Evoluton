"""Assemble the self-contained page gen_two_tier_explorer.html from two_tier/template.html and the built network."""
import json
import os
from collections import Counter, defaultdict

from .detail import build_detail

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # repository root
TEMPLATE = os.path.join(HERE, 'two_tier', 'template.html')
PAGE_FILE = 'gen_two_tier_explorer.html'

STOP_TITLES = {
    1687: 'The reader starts',
    1900: 'First failed route',
    1927: 'First family of observables',
    1933: 'First witness–effect pair of the generic tier',
    1939: 'Symmetry partition of the one-particle space',
    1969: 'Bell functional and Bell violation',
    1989: 'Entangled states enter as a cluster',
    2007: 'Steering: one cluster in two roles',
    2012: 'Higgs sector and the resource-theory axioms',
    2015: 'The year with the most cluster events in the generic tier',
    2026: 'Project year: distinguished states, curated memberships and their closure',
}

REFERENCES = [
    ['Formal concept analysis', 'B. Ganter, R. Wille, Formal Concept Analysis: Mathematical Foundations (Springer, 1999), doi:10.1007/978-3-642-59830-2', 'objects, attributes, incidence; implications between attributes'],
    ['Attribute exploration', 'B. Ganter, S. Obiedkov, Conceptual Exploration (Springer, 2016), doi:10.1007/978-3-662-49291-8', 'propose an implication, prove it or add a counterexample; only the single-premise fragment is run here'],
    ['Structural equivalence', 'F. Lorrain, H. C. White, J. Math. Sociol. 1, 49 (1971), doi:10.1080/0022250X.1971.9989788', 'nodes with the same ties are substitutable; the substitution criterion of rule R17'],
    ['Levels of abstraction', 'L. Floridi, Minds and Machines 18, 303 (2008), doi:10.1007/s11023-008-9113-7', 'a level of abstraction is fixed by a set of observables'],
    ['Wigner classes', 'E. Wigner, Ann. Math. 40, 149 (1939)', 'as cited in GEN_HEP Step 2'],
    ['Separability of two qubits', 'M. Horodecki, P. Horodecki, R. Horodecki, Phys. Lett. A 223, 1 (1996)', 'as cited in GEN_GPT_Level; PPT is necessary and sufficient for two qubits'],
    ['CHSH for two qubits', 'R. Horodecki, P. Horodecki, M. Horodecki, Phys. Lett. A 200, 340 (1995), doi:10.1016/0375-9601(95)00214-N', 'violation iff the two largest eigenvalues of TᵀT sum to more than 1'],
    ['Werner states', 'R. F. Werner, Phys. Rev. A 40, 4277 (1989); J. Barrett, Phys. Rev. A 65, 042302 (2002); H. M. Wiseman, S. J. Jones, A. C. Doherty, Phys. Rev. Lett. 98, 140402 (2007); A. Acín, N. Gisin, B. Toner, arXiv:quant-ph/0606138', 'imported thresholds for the steering and Bell-locality cells of the two entangled Werner states that do not violate CHSH'],
    ['Hudson theorem', 'R. L. Hudson, Rep. Math. Phys. 6, 249 (1974)', 'as cited in GEN_GPT_Level edge S6'],
]

METHOD = [
    ['Two tiers', [
        'Tier C holds the nodes that name a physical system: the electromagnetism reader, the Standard Model history, the textbook reader and the lattice model. Tier A holds the nodes defined for any system: the nonclassicality network and the resource-theory network. The tier is assigned by branch.',
        'A state or observable node of tier A is a cluster: a set of states, or of observable data, picked out by a predicate. Tier C has clusters of its own (Wigner classes, Fock sectors, groups of sectors, families of observables, clusters of interaction terms), and tier A has atoms of its own (the nine distinguished states of the resource-theory network).',
    ]],
    ['Abstraction edges', [
        'A route says that a target follows from its inputs. An abstraction edge says how the extensions of two nodes are related: member, subset, equal, cut (the cluster divides the carrier), excluded, complement, disjoint, aggregate (the target is a sum, a direct sum or a moment of its sources). Three further kinds tie a cluster to the other layers: criterion (a model-layer node supplies the predicate), test (an observable-layer functional decides membership), lineage (a model was absorbed).',
        'Every abstraction edge records where it comes from: a released edge, a released statement, the theory band of the resource-theory network, a cross-edge or glue concept of Part I, or the curation of 18 November 2026. Curated edges carry the criterion in words and a status (definition, theorem, elementary, standard).',
    ]],
    ['Clustering as an operation', [
        'Rule R17 clusters states. A model-layer node supplies a predicate: an invariance under a group, membership in a subtheory, factorisation over a partition, a constraint. These four are the typology of free-operation justifications recorded in the resource-theory network (node F-TYPE, the family attribute of each theory, proposition QP1). Two more criteria occur in the released data: the same physical system or process (a sector, a family), and substitution in a route (the groups of sectors that stand as one leg of an AND route). Rule R1 of the Standard Model graph is the first case inside one system.',
        'Rule R18 clusters observables in three forms: a family of one process type, an aggregate (a total, a moment), and an effect. An effect is the set of observable data that a named reference model cannot produce; a witness is the test of membership. In the history graphs the same situation is the deficit of rule R2, an observable with no route from the current model, and it is resolved within a few steps. In the generic tier the reference model is kept fixed and the deficit set becomes a node.',
        'Rule R19 lifts: member-level routes, or an implication of the incidence table, propose an edge between clusters. Rule R20 descends: an inclusion between clusters, a member, the right kind of object and the right frame give a derived membership; with a witness and data the membership is observed. Rule R21 refines: a contradiction or a refuted implication splits a cluster, adds a counterexample atom or restricts an inclusion to a frame.',
        'A cluster node is well formed when it has three legs, one per layer: a criterion edge from the model layer, a test edge from the observable layer, and at least one member.',
    ]],
    ['What is computed', [
        'The closure of the membership relation is a least fixed point of four monotone rules. A conclusion is drawn only when the atom is an object of the kind the cluster is defined on, and an inclusion stated under a frame is used only for atoms that carry the frame. Derived facts keep the list of edges they come from.',
        'The kernel evaluates ten free-set predicates on explicit two-qubit density matrices and compares the resulting incidence table with the released inclusion edges. It reports contradictions, implications that the released edges do not yield, and whether each released strictness claim has a witness among the objects.',
        'Every event (node, route, abstraction edge) gets a stage of the combined cycle from a lookup table. A stage is a phase in a tier. The phases are the eight of Part II plus cluster and descend. The tier is that of the node, of the target of the route, or of the two ends of the abstraction edge; an abstraction edge with one end in each tier is counted as crossing.',
    ]],
    ['Limits', [
        'Years are the ingredient chronology of Part II: the year of the earliest source cited by the networks, not a historical date. Curated edges are dated 2026. The textbook reader and the lattice model have no year and do not appear on the time axis.',
        'The curated memberships rest on the node definitions as written in the released data. Those with status standard are textbook identifications that were not derived here. The frame and domain tags that gate the closure were assigned by hand.',
        'The kernel uses a numerical tolerance of 1e-9; the classical-classical test is a numerical minimisation over local bases; four cells use thresholds imported from the literature.',
        'Only the six released graphs enter. The proposals are not applied to them.',
        'Built by an AI system (Claude, Anthropic) for Tahmeed Hossain, without independent review.',
    ]],
]


def _short(s, n):
    s = (s or '').strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + '…'


def export(full):
    nodes = {n['uid']: n for n in full['nodes']}
    routes, abst = full['routes'], full['abst']

    def lab(u):
        return nodes[u]['label']

    def describe(e):
        return '%s: %s → %s' % (e['rel'], ' + '.join(lab(s) for s in e['src']), lab(e['dst']))

    # ---- stops
    ev_n, ev_r, ev_a = defaultdict(list), defaultdict(list), defaultdict(list)
    for n in full['nodes']:
        if n['year'] is not None:
            ev_n[n['year']].append(n)
    for r in routes:
        if r['year'] is not None:
            ev_r[r['year']].append(r)
    for e in abst:
        if e['year'] is not None:
            ev_a[e['year']].append(e)
    stops = []
    for y, title in sorted(STOP_TITLES.items()):
        A = ev_a[y]
        items = []
        if y == 1687:
            items = ['%s (%s)' % (n['label'], {'O': 'observable', 'M': 'law', 'S': 'state'}[n['layer']]) for n in ev_n[y]]
        elif y == 1900:
            items = ['%s: %s' % (r['rid'], r['text']) for r in ev_r[y] if r['kind'] == 'failed']
        elif y == 2026:
            c = Counter(e['origin'] for e in A)
            items = ['%d edges with origin "%s"' % (v, k) for k, v in c.most_common()]
        else:
            pref = [e for e in A if e['rel'] in ('member', 'test', 'cut', 'reify', 'aggregate', 'excluded')]
            items = [describe(e) for e in (pref or A)[:6]]
        stops.append(dict(year=y, title=title, nodes=len(ev_n[y]), routes=len(ev_r[y]), abst=len(A), items=items))

    # ---- branch x stage
    bs = defaultdict(Counter)
    for n in full['nodes']:
        if n['year'] is not None:
            bs[n['branch']][n['stage']] += 1
    for r in routes:
        if r['year'] is not None:
            bs[r['branch']][r['stage']] += 1
    for e in abst:
        if e['year'] is not None and not (e.get('route') and e['rel'] in ('member', 'subset', 'equal', 'test', 'hosts', 'cut')):
            bs[nodes[e['dst']]['branch']][e['stage']] += 1
    branch_stage = {b: dict(c) for b, c in bs.items()}
    undated_stage = dict(Counter(e['stage'] for e in abst if e['year'] is None))

    # ---- nodes of the two generic networks without a released edge.  The routes of GPT and QRT are the
    #      released edges one to one (156 and 86), so route degree zero means: no edge in the released file.
    deg = Counter()
    for r in routes:
        for u in r['inputs'] + [r['target']]:
            deg[u] += 1
    isolated = sorted(u for u, n in nodes.items() if n['branch'] in ('GPT', 'QRT') and deg[u] == 0)
    iso_q = [u.split(':')[1] for u in isolated if u.startswith('QRT:')]
    iso_g = [u.split(':')[1] for u in isolated if u.startswith('GPT:')]
    ROLE = [('m-', 'model'), ('sF-', 'free sets'), ('pF-', 'free operations'), ('pU-', 'use protocols'),
            ('wD-', 'detectors'), ('wQ-', 'quantifiers')]
    by_role = []
    for pre, name in ROLE:
        xs = [x for x in iso_q if x.startswith(pre)]
        if xs:
            by_role.append('%s %s' % (name, ', '.join(xs)))
    assert sum(len([x for x in iso_q if x.startswith(pre)]) for pre, _ in ROLE) == len(iso_q)

    # ---- compact kernel context
    ctx = full['context']
    lv_names = [l['level'] for l in ctx['rounds'][0]['levels']]
    imps = []
    r0, r1 = ctx['rounds'][0], ctx['rounds'][1]
    for k, i0 in enumerate(r0['levels'][0]['implications']):
        imps.append(dict(a=i0['a'], b=i0['b'], support=[i0['support'], r1['levels'][0]['implications'][k]['support']],
                         by=[i0['refuted_by'], r1['levels'][0]['implications'][k]['refuted_by']],
                         kind=[[r['levels'][j]['implications'][k]['kind'] for j in range(3)] for r in (r0, r1)],
                         source=r1['levels'][2]['implications'][k]['source']))
    context = dict(frame=ctx['frame'], attrs=ctx['attrs'], objects=ctx['objects'], levels=lv_names,
                   counts=[[l['counts'] for l in r['levels']] for r in (r0, r1)],
                   candidates=[[[c['a'] + '⇒' + c['b'] for c in l['candidates']] for l in r['levels']] for r in (r0, r1)],
                   n_objects=[r0['n_objects'], r1['n_objects']], implications=imps, strict=r1['strict'],
                   strict0=r0['strict'], crosscheck=ctx['crosscheck'], n_stab=ctx['n_stabilizer_states'])

    N = full['numbers']
    n_import = sum(1 for o in ctx['objects'] for c in o['cells'].values() if c['grade'] == 'import')
    n_unknown = sum(1 for o in ctx['objects'] for c in o['cells'].values() if c['val'] is None)
    assert n_import == 4, n_import          # the Limits text of METHOD quotes this number
    context['n_import'], context['n_unknown'] = n_import, n_unknown
    proposals = [
        dict(id='P1', net='GEN_QRT_Level', kind='missing literature edge',
             text='Add the inclusion sF-dis ⊂ sF-ent (zero-discord states are separable). The nonclassicality network has it as edge S7; the resource-theory network has no edge at sF-dis.',
             evidence='Kernel: dis ⇒ ent holds on all objects and is not derivable from the released QRT edges alone.'),
        dict(id='P2', net='GEN_QRT_Level', kind='elementary edge',
             text='Add the inclusion sF-coh ⊂ sF-dis for a local product incoherent basis: a state diagonal in a product basis is classical-classical by the definition of GPT:s-zerodisc. Edge SS1 is then the composition of this edge with P1.',
             evidence='Kernel: coh ⇒ dis holds on all objects; derivable only through GPT:R1, a proposition derived in the project.'),
        dict(id='P3', net='GEN_QRT_Level', kind='statement',
             text='Edge SS2 lists the free sets that contain I/d; the classical-classical set is missing from the list.',
             evidence='Kernel: pur ⇒ dis; I/4 is diagonal in every product basis.'),
        dict(id='P4', net='GEN_QRT_Level', kind='missing atom',
             text='No distinguished state is a stabilizer state with an imaginary density matrix. With the states the network names, STAB ⊂ real cannot be refuted; |+i> refutes it.',
             evidence='Kernel round 0: mag ⇒ ima is a candidate; round 1: refuted by |+i>|0>.'),
        dict(id='P5', net='GEN_QRT_Level, GEN_GPT_Level', kind='nodes without an edge',
             text='%d of the %d nodes of the resource-theory network have no edge; each belongs to its theory only through the node attribute "theory": %s. In the nonclassicality network %d of %d nodes have no edge (%s). For the purity theory this leaves the free set and the resource set without a test edge.'
                  % (len(iso_q), N['nodes_by_branch']['QRT'], '; '.join(by_role), len(iso_g), N['nodes_by_branch']['GPT'], ', '.join(iso_g)),
             evidence='Count of released edges per node (%d edges in QRT v1.2, %d in GPT v2.6). Three-leg lint: classes without a test are %s.'
                      % (N['routes_by_branch']['QRT'], N['routes_by_branch']['GPT'], ', '.join(x.split(':')[1] for x in N['classes_no_test']))),
        dict(id='P6', net='GEN_GPT_Level', kind='missing reference models',
             text='%d of %d effects have a no-go edge from the model layer. The other effects are defined in their node text as the absence of a model of a named kind (local hidden states, noncontextual value assignments, a joint distribution), but no node stands for that model.' % (N['effects_with_reference'], N['effects']),
             evidence='Three-leg lint of the effects, Checks view.'),
        dict(id='P7', net='GEN_GPT_Level', kind='missing criterion',
             text='The clusters s-gauss and s-bound have no criterion edge and no test edge. For s-gauss the model node m-gaussian exists and no edge joins the two.',
             evidence='Three-leg lint of the state clusters.'),
        dict(id='P8', net='GEN_QRT_Level', kind='scope',
             text='Edge SS12 states that the Gibbs state is incoherent in the energy basis for a nondegenerate Hamiltonian. The Gibbs state is a function of H and is therefore diagonal in every eigenbasis of H, degenerate or not. The closure here keeps the released scope.',
             evidence='Elementary; not used in the closure.'),
        dict(id='P9', net='all', kind='cross-tier edges',
             text='%d stated membership and cut edges run from system-specific nodes into generic clusters. They are candidates for cross-network edges of the released graphs.' % (N['flow'].get('C→A member', 0) + N['flow'].get('C→A cut', 0)),
             evidence='Clusters view, filter "With a member from the other tier"; Checks view, direction of the membership edges.'),
        dict(id='P10', net='GEN_QRT_Level, GEN_GPT_Level', kind='derived memberships',
             text='The closure derives %d facts (%d memberships, %d exclusions) from %d stated ones, with %d conflicts. Each is a candidate edge with its derivation. On the %d classes that remain after glue they settle %d cells of the incidence table that had no stated fact.' % (N['closure']['derived'], N['closure']['derived_in'], N['closure']['derived_out'], N['closure']['stated'], N['closure']['conflicts'], N['classes'], N['census']['derived']),
             evidence='Kernel cross-check: %d comparisons of %d facts with the computed table; %d agree.' % (N['kernel']['crosscheck']['compared'], N['kernel']['crosscheck']['facts'], N['kernel']['crosscheck']['agree'])),
    ]

    full['proposals'] = proposals
    meta = dict(schema='gen-two-tier-page/1', title=full['title'], generated=full['generated'], sources=full['sources'],
                branches=full['branches'], phases=full['phases'], stages=full['stages'], operations=full['operations'],
                rules=full['rules'], classes=full['classes'], effects=full['effects'], census=full['census'],
                inclusions=full['inclusions'], disjoint=full['disjoint'], atom_domains=full['atom_domains'],
                atom_frames=full['atom_frames'], timeline=full['timeline'], numbers=N, stops=stops,
                branch_stage=branch_stage, undated_stage=undated_stage, isolated=isolated, context=context, proposals=proposals, method=METHOD,
                references=REFERENCES)

    pn = [dict(u=n['uid'], b=n['branch'], n=n['nid'], l=n['label'], L=n['layer'], s=n['sub'], t=n['tier'], y=n['year'],
               yp=n['year_prov'], ry=n.get('removal_year'), d=_short(n.get('desc'), 240), st=n['status'], ph=n['phase'],
               sg=n['stage'], c=n.get('concept')) for n in full['nodes']]
    pr = [dict(u=r['uid'], b=r['branch'], r=r['rid'], i=r['inputs'], o=r['target'], k=r['kind'], y=r['year'],
               ry=r.get('removal_year'), ph=r['phase'], p8=r['phase8'], sg=r['stage'], ru=r.get('rule'),
               x=_short(r.get('text'), 170), st=r.get('status'), gr=r.get('grade')) for r in routes]
    pa = [dict(id=e['id'], s=e['src'], d=e['dst'], rel=e['rel'], crit=e['crit'], fr=e['frame'], st=e['status'],
               pv=e['prov'], nt=e['note'], y=e['year'], og=e['origin'], ph=e['phase'], sg=e['stage'], ru=e['rule'],
               rt=e.get('route'))
          for e in abst]

    detail = build_detail(full)
    full['detail_counts'] = dict(Counter(r['k'] for r in detail))
    blob = json.dumps(dict(meta=meta, nodes=pn, routes=pr, abst=pa, detail=detail), ensure_ascii=False, separators=(',', ':'))
    blob = blob.replace('</', '<\\/')
    tpl = open(TEMPLATE, encoding='utf-8').read()
    assert tpl.count('/*__EMBED__*/') == 1
    out = os.path.join(HERE, PAGE_FILE)
    open(out, 'w', encoding='utf-8').write(tpl.replace('/*__EMBED__*/', 'window.__GEN__=' + blob + ';'))
    return dict(file=PAGE_FILE, bytes=os.path.getsize(out), nodes=len(pn), routes=len(pr), abst=len(pa), detail=len(detail))
