"""Abstraction edges: the relation that ties a cluster node to what it clusters.

An abstraction edge is NOT a route.  A route says "from these inputs the target follows".
An abstraction edge says how the extensions of two nodes of the same kind are related:

  member     ext(src) is contained in ext(dst)          src is an instance or sub-family of the cluster dst
  subset     ext(src) is contained in ext(dst)          both are clusters
  equal      ext(src) = ext(dst)                        two names of one cluster (glue) or two clusters that coincide
  cut        ext(dst) meets ext(src) in a proper part   the cluster dst divides the carrier src
  excluded   ext(src) and ext(dst) are disjoint
  complement dst is the complement of src inside the common carrier (free set / resource set)
  disjoint   two clusters with empty intersection
  aggregate  dst is built from its sources by a sum, a direct sum or a functional (global = sum of local)
  criterion  src (model layer) supplies the predicate that defines the cluster dst
  test       src (observable layer) is a membership test of the cluster dst (witness, monotone)
  lineage    src (model) was absorbed into the model cluster dst
  hosts      the model src contains members of the cluster dst
  reify      an observable-layer cluster re-appears as a state-layer object of a resource theory
  refines    Part I cross-edge kept as recorded (no extension semantics assigned)

Criterion types (field crit), i.e. what licenses the cluster:
  sym  invariance under a group action      sub  membership in a subtheory
  par  factorisation over a partition       con  a constraint or an axiom list
  def  deficit against a reference model, decided by a witness
  fam  same process family or same physical system
  agg  aggregation (sum, direct sum, moment) lin  model lineage
  str  substitution in routes (members are interchangeable as legs of one route)
"""
import json
import os
from collections import defaultdict

from .load import source

FAMILY_CRIT = {'pur': 'con', 'ath': 'con+sym', 'asy': 'sym', 'coh': 'sym', 'ima': 'sym', 'mag': 'sub',
               'nga': 'sub', 'ent': 'par', 'ste': 'par', 'nlo': 'par', 'ctx': 'par', 'inc': 'par', 'dis': 'none'}

# Memberships stated inside the statement text of a released QRT edge but not drawn as an edge of
# their own.  Each entry was read from the statement of the edge named in 'prov'.
QRT_STATED = [
    # (src, dst, rel, edge id, note)
    ('d-maxmix', 'sF-ent', 'member', 'SS2', 'listed: SEP'),
    ('d-maxmix', 'sF-coh', 'member', 'SS2', 'listed: incoherent'),
    ('d-maxmix', 'sF-asy', 'member', 'SS2', 'listed: symmetric'),
    ('d-maxmix', 'sF-ima', 'member', 'SS2', 'listed: real'),
    ('d-maxmix', 'sF-mag', 'member', 'SS2', 'listed: STAB'),
    ('d-maxmix', 'sF-nga', 'member', 'SS2', 'listed: Wigner-positive'),
    ('d-maxmix', 'sF-ath', 'cut', 'SS2', 'free only for a trivial Hamiltonian'),
    ('d-gibbs', 'sF-coh', 'member', 'SS3b', 'energy basis'),
    ('d-gibbs', 'sF-asy', 'member', 'SS3b', 'U(1) time translations'),
    ('d-gibbs', 'sF-ima', 'member', 'SS3b', 'energy basis'),
    ('d-plus', 'sF-ima', 'member', 'SS4', 'real'),
    ('d-plus', 'sR-pur', 'member', 'SS4b', 'a maximal purity resource'),
    ('d-plus', 'sR-asy', 'member', 'SS4b', 'U(1) asymmetry resource for H proportional to Z'),
    ('d-bell', 'sF-ima', 'member', 'SS5', 'real'),
    ('d-bell', 'sR-ste', 'member', 'SS5b', 'maximally steering-capable'),
    ('d-bell', 'sR-nlo', 'member', 'SS5b', 'Bell-violating with incompatible measurements'),
    ('d-werner', 'sR-ent', 'member', 'SS6', 'the node denotes entangled Werner states'),
    ('d-werner', 'sF-ste', 'cut', 'SS6', 'unsteerable ranges exist (not every entangled Werner state)'),
    ('d-tstate', 'sR-coh', 'member', 'SS9', 'resource of coherence'),
    ('d-tstate', 'sR-pur', 'member', 'SS9', 'resource of purity'),
    ('d-tstate', 'sR-ima', 'member', 'SS9', 'resource of imaginarity'),
    ('d-ccdis', 'sF-ent', 'member', 'SS19', 'inside the SEP free set'),
]
# Released member edges whose statement carries the quantifier "some" / "generic": recorded as cut.
QRT_QUANTIFIED = {
    'SS3': 'generic interacting Hamiltonian; not for a Hamiltonian with a stabilizer eigenbasis (GPT edge U4)',
    'SS7': 'statement: "Some PPT bound entangled states violate a Bell inequality"',
}
# State-level inclusions of the released networks that the closure uses, with the domain on which
# the target set is defined and the frame under which the statement is made.
INCLUSIONS = [
    # (sub, sup, source, frame tag required of the atom, frame in words)
    #   'E'  the atom's coherence basis is the eigenbasis of a nondegenerate Hamiltonian
    #   'P'  the atom is bipartite and its coherence basis is a local product basis
    ('QRT:sF-coh', 'QRT:sF-ent', 'QRT:SS1', 'P', 'incoherent basis = a local product basis'),
    ('QRT:sF-ath', 'QRT:sF-coh', 'QRT:SS12', 'E', 'energy eigenbasis, nondegenerate H'),
    ('QRT:sF-coh', 'QRT:sF-ima', 'QRT:SS14', None, 'same basis'),
    ('QRT:sF-ent', 'QRT:sF-ste', 'QRT:SS16', None, ''),
    ('QRT:sF-ste', 'QRT:sF-nlo', 'QRT:SS17', None, ''),
    ('QRT:sF-nlo', 'QRT:sF-ctx', 'QRT:SS15', None, 'scenario by scenario (behaviours)'),
    ('QRT:sF-asy', 'QRT:sF-coh', 'QRT:SS18', 'E', 'U(1), nondegenerate energy eigenbasis'),
    ('QRT:sF-coh', 'QRT:sF-asy', 'QRT:SS18', 'E', 'U(1), nondegenerate energy eigenbasis'),
    ('GPT:s-thermal', 'GPT:s-tts', 'GPT:S3', None, ''),
    ('GPT:s-cohE', 'GPT:s-coh', 'GPT:S4', 'E', 'coherence basis = energy eigenbasis'),
    ('GPT:s-zerodisc', 'GPT:s-sep', 'GPT:S7', None, ''),
    ('GPT:s-bound', 'GPT:s-ent', 'GPT:S10', None, ''),
    ('GPT:s-ent', 'GPT:s-coh', 'GPT:S1', 'P', 'coherent in every product basis'),
    ('GPT:s-ent', 'GPT:s-discord', 'GPT:S2', None, ''),
    ('GPT:s-gauss', 'QRT:sF-nga', 'Part I cross-edge', None, ''),
]
DISJOINT = [
    ('GPT:s-gauss', 'GPT:s-wneg', 'GPT:S6', 'Gaussian states have a Gaussian, hence nonnegative, Wigner function'),
    ('GPT:s-thermal', 'GPT:s-cohE', 'GPT:S8', '[gamma, H] = 0'),
]
GPT_COMPLEMENT = [('GPT:s-sep', 'GPT:s-ent'), ('GPT:s-tts', 'GPT:s-cohE'), ('GPT:s-thermal', 'GPT:s-athermal'),
                  ('GPT:s-zerodisc', 'GPT:s-discord'), ('GPT:s-stab', 'GPT:s-magic')]
# Glue concepts of Part I that identify a GPT state cluster with a QRT state set.
GLUE_EQUAL = ['separable_states', 'entangled_states', 'bound_entangled', 'coherent_states', 'asymmetric_states',
              'symmetric_states', 'gibbs_state', 'athermal_states', 'wigner_negative', 'stabilizer_states',
              'magic_states', 'discordant_states', 'zero_discord']
# Domain on which each cluster is defined (which kind of object can be a member).
CLASS_DOMAIN = {
    'pur': 'any', 'ath': 'any', 'asy': 'any', 'coh': 'any', 'ima': 'any', 'mag': 'qud', 'nga': 'cv',
    'ent': 'bip', 'ste': 'bip', 'nlo': 'bip', 'ctx': 'beh', 'inc': 'dev', 'dis': 'bip'}
GPT_DOMAIN = {'s-sep': 'bip', 's-ent': 'bip', 's-bound': 'bip', 's-discord': 'bip', 's-zerodisc': 'bip',
              's-coh': 'any', 's-cohE': 'any', 's-tts': 'any', 's-thermal': 'any', 's-athermal': 'any',
              's-gauss': 'cv', 's-wneg': 'cv', 's-stab': 'qud', 's-magic': 'qud'}
# Kind of object each atom is (the domains it belongs to).  'any' is implied.
ATOM_DOMAINS = {
    'QRT:d-maxmix': {'bip', 'qud'}, 'QRT:d-gibbs': {'bip', 'qud'}, 'QRT:d-plus': {'qud'},
    'QRT:d-tstate': {'qud'}, 'QRT:d-wpos': {'qud'}, 'QRT:d-bell': {'bip', 'qud'},
    'QRT:d-werner': {'bip', 'qud'}, 'QRT:d-bound': {'bip', 'qud'}, 'QRT:d-ccdis': {'bip', 'qud'},
    'UP:stat': {'cv'}, 'UP:pib': {'cv'}, 'UP:hatom': {'cv'}, 'UP:wpack': {'cv'}, 'UP:qho': {'cv'},
    'UP:mbd': set(), 'UP:theq': set(), 'UP:bbrad': {'cv'}, 'HEP:s_g': {'cv'},
}

# Frame of each atom (see INCLUSIONS).  'E' is given only where a nondegenerate Hamiltonian is named:
# |+> is stated for basis Z and H proportional to Z (QRT:SS4b); the Gibbs state is stated in the
# energy basis of a generic Hamiltonian (QRT:SS3b), possibly interacting, so it has no 'P'; the box
# and the oscillator have nondegenerate bound-state spectra.  The hydrogen atom, the free particle
# behind the wave packet, the ideal gas and the radiation field have degenerate spectra, and the
# generic stationary state names no Hamiltonian: no 'E'.  The bipartite distinguished states are
# stated in a local product basis and no Hamiltonian is named: 'P' only.
ATOM_FRAMES = {
    'QRT:d-maxmix': {'E', 'P'}, 'QRT:d-gibbs': {'E'}, 'QRT:d-plus': {'E'}, 'QRT:d-tstate': set(),
    'QRT:d-wpos': set(), 'QRT:d-bell': {'P'}, 'QRT:d-werner': {'P'}, 'QRT:d-bound': {'P'},
    'QRT:d-ccdis': {'P'}, 'UP:stat': set(), 'UP:pib': {'E'}, 'UP:hatom': set(), 'UP:wpack': set(),
    'UP:qho': {'E'}, 'UP:mbd': set(), 'UP:theq': set(), 'UP:bbrad': set(),
}

# Sector -> Wigner class.  Particle content of each Fock sector of the Standard Model graph;
# neutrinos are massless in the graph until Step 11 (stated simplification of GEN_HEP).
HEP_SECTOR_CLASS = {
    's_e': 'u_mh', 's_p': 'u_mh', 's_n': 'u_mh', 's_mu': 'u_mh', 's_u': 'u_mh', 's_d': 'u_mh',
    's_nu': 'u_0h', 's_nue': 'u_0h', 's_num': 'u_0h', 's_g': 'u_01', 's_W': 'u_m1', 's_Z': 'u_m1',
    's_H': 'u_m0'}
HEP_GROUP_LABEL = {'fer': 'Fermion sectors f', 'chg': 'Charged fermion sectors, Q ≠ 0', 'nus': 'Neutrino sectors ν'}


def _yr(nodes, *uids):
    ys = [nodes[u]['year'] for u in uids if u in nodes]
    if not ys or any(y is None for y in ys):
        return None
    return max(ys)


class Builder:
    def __init__(self, d):
        self.d = d
        self.nodes = d['nodes']
        self.routes = d['routes']
        self.edges = []
        self.count = defaultdict(int)

    def add(self, pre, src, dst, rel, crit=None, frame=None, status='definition', prov='', note='', year='auto',
            origin='native'):
        src = [src] if isinstance(src, str) else list(src)
        for u in src + [dst] + list(frame or []):
            assert u in self.nodes, (pre, u)
        self.count[pre] += 1
        if year == 'auto':
            year = _yr(self.nodes, *(src + [dst]))
            if year is not None and origin.startswith('curated'):
                year = 2026          # curated for this network (2026-11-18); Part II convention for project items
        e = dict(id='%s%03d' % (pre, self.count[pre]), src=src, dst=dst, rel=rel, crit=crit,
                 frame=list(frame or []), status=status, prov=prov, note=note, year=year, origin=origin)
        self.edges.append(e)
        return e

    # ------------------------------------------------------------------ QRT
    def qrt(self):
        q = source('qrt')
        N = {n['id']: n for n in q['nodes']}
        fam = {t['id']: t['family'] for t in q['theories']}
        self.qrt_theories = [t['id'] for t in q['theories']]
        self.qrt_family = fam
        byrole = defaultdict(dict)
        for n in q['nodes']:
            byrole[n['theory']][n['role']] = n['id']
        for t in self.qrt_theories:
            m, f, r = byrole[t]['model'], byrole[t]['free_state'], byrole[t]['resource_state']
            for c in (f, r):
                self.add('q.crit', 'QRT:' + m, 'QRT:' + c, 'criterion', FAMILY_CRIT[t], status='definition',
                         prov='QRT theory band "%s": model, free set and resource set of one theory' % t,
                         note='family: ' + fam[t], origin='native (theory band)')
            self.add('q.comp', 'QRT:' + f, 'QRT:' + r, 'complement', FAMILY_CRIT[t], status='definition',
                     prov='QRT theory band "%s"' % t, origin='native (theory band)')
        for e in q['edges']:
            a, b, k = 'QRT:' + e['from'], 'QRT:' + e['to'], e['kind']
            la, lb = N[e['from']]['layer'], N[e['to']]['layer']
            prov = 'QRT:' + e['id']
            if k in ('member_free', 'member_resource'):
                if e['id'] in QRT_QUANTIFIED:
                    self.add('q.mem', a, b, 'cut', status=e['status'], prov=prov,
                             note='released kind %s; %s' % (k, QRT_QUANTIFIED[e['id']]))
                else:
                    self.add('q.mem', a, b, 'member', status=e['status'], prov=prov)
            elif k == 'subset' and la == lb == 'state':
                self.add('q.sub', a, b, 'subset', status=e['status'], prov=prov)
            elif k == 'equiv' and la == lb == 'state' and e['id'] == 'SS18':
                self.add('q.sub', a, b, 'equal', status=e['status'], prov=prov,
                         note='U(1), nondegenerate energy eigenbasis')
            elif k == 'witness' and la == 'witness' and lb == 'state':
                self.add('q.test', a, b, 'test', 'def', status=e['status'], prov=prov)
            elif k in ('subset', 'contains') and la == lb == 'process_cptp':
                self.add('q.proc', a, b, 'refines', status=e['status'], prov=prov,
                         note='operation-class inclusion (kind %s); not used in the state closure' % k)
        for s, dst, rel, eid, note in QRT_STATED:
            st = next(e['status'] for e in q['edges'] if e['id'] == eid)
            self.add('q.stm', 'QRT:' + s, 'QRT:' + dst, rel, status=st, prov='QRT:%s (statement text)' % eid,
                     note=note, origin='native (read from a released statement)')

    # ------------------------------------------------------------------ GPT
    def gpt(self):
        g = source('gpt')
        ty = {n['id']: n['type'] for n in g['nodes']}
        self.gpt_types = ty
        for e in g['edges']:
            a, b, k = 'GPT:' + e['source'], 'GPT:' + e['target'], e['kind']
            ta, tb = ty[e['source']], ty[e['target']]
            prov = 'GPT:' + e['id']
            if k == 'pairs':
                self.add('g.test', a, b, 'test', 'def', status=e['status'], prov=prov)
            elif k == 'subset' and ta == tb == 'state':
                self.add('g.sub', a, b, 'subset', status=e['status'], prov=prov)
            elif k == 'implies' and ta == tb == 'state' and e['id'] in ('S1', 'S2'):
                self.add('g.sub', a, b, 'subset', status=e['status'], prov=prov,
                         note='released kind implies; a set inclusion by its statement')
            elif k == 'forbids' and ta == tb == 'state' and e['id'] in ('S6', 'S8'):
                self.add('g.dis', a, b, 'disjoint', status=e['status'], prov=prov)
            elif k == 'hosts':
                self.add('g.host', a, b, 'hosts', status=e['status'], prov=prov)
            elif k == 'subset' and ta == tb == 'process':
                self.add('g.proc', a, b, 'refines', status=e['status'], prov=prov,
                         note='process-cluster inclusion; not used in the state closure')
        for a, b in GPT_COMPLEMENT:
            self.add('g.comp', a, b, 'complement', status='definition',
                     prov='node definitions of ' + a.split(':')[1] + ' and ' + b.split(':')[1])
        # reference model of an effect: a no-go edge between a model or axiom node and the effect
        self.effect_reference = defaultdict(list)
        for e in g['edges']:
            if e['kind'] in ('forbids', 'excludes'):
                for x, y in ((e['source'], e['target']), (e['target'], e['source'])):
                    if ty[x] in ('model', 'axiom') and ty[y] == 'effect':
                        self.effect_reference[y].append((e['id'], x, e['kind']))
                        self.add('g.ref', 'GPT:' + x, 'GPT:' + y, 'criterion', 'def', status=e['status'],
                                 prov='GPT:' + e['id'], note='reference model of the effect (kind %s)' % e['kind'])
        self.gpt_effects = [n['id'] for n in g['nodes'] if n['type'] == 'effect']

    # ------------------------------------------------------------------ HEP
    def hep(self):
        h = source('hep')
        nodes = self.nodes
        for u in ['u_vac', 'u_m0', 'u_mh', 'u_m1', 'u_0h', 'u_01', 'u_02', 'u_cs', 'u_tach']:
            self.add('h.part', 'HEP:' + u, 'HEP:H1', 'member', 'sym', frame=['HEP:m_U'],
                     status='theorem', prov='HEP Step 2 PARTITION (back-edges wigner/e3)',
                     note='H1 decomposes into irreducible representations of the Poincaré group (Wigner 1939)')
        for s, u in HEP_SECTOR_CLASS.items():
            note = 'one-particle space of the sector carries this Wigner class'
            if u == 'u_0h':
                note += '; neutrinos are massless in the graph until Step 11'
            self.add('h.ext', 'HEP:' + s, 'HEP:' + u, 'member', 'sym', frame=['HEP:m_U', 'HEP:m_field'],
                     status='standard', prov='HEP Step 4 EXTEND (one field per UIR); particle content of the sector',
                     note=note, origin='curated 2026-11-18')
        # groups of sectors used as one leg of an AND route
        groups, first_step, targets = {}, {}, defaultdict(set)
        for i, s in enumerate(h['steps'], 1):
            for gdef in s.get('groups', []):
                groups[gdef['id']] = gdef['members']
            for a in s.get('ands', []):
                for leg in a['legs']:
                    if 'g' in leg:
                        first_step.setdefault(leg['g'], i)
                        targets[leg['g']].add(a['t'])
        step_year = {i: int(s['years'][:4]) for i, s in enumerate(h['steps'], 1) if s['years'][:4].isdigit()}
        for gid, members in groups.items():
            uid = 'HEP:g_' + gid
            yr = max([step_year[first_step[gid]]] + [nodes['HEP:' + m]['year'] for m in members])
            nodes[uid] = dict(uid=uid, branch='HEP', nid='g_' + gid, label=HEP_GROUP_LABEL[gid], layer='S',
                              sub='S.group', tier='C', year=yr, year_prov='first route with this group leg',
                              desc='Group of Fock sectors used as one leg of an AND route (step.groups of the released data).',
                              concept=None, removed=False, removal_year=None, step_first=first_step[gid],
                              step_last=12, status='released', materialized=True)
            fr = sorted('HEP:' + t for t in targets[gid] if 'HEP:' + t in nodes)
            for m in members:
                self.add('h.grp', 'HEP:' + m, uid, 'member', 'str', frame=fr, status='definition',
                         prov='HEP step.groups "%s" (Steps %d-12)' % (gid, first_step[gid]),
                         note='any member can stand as the leg of the routes into ' + ', '.join(t.split(':')[1] for t in fr))
        self.hep_groups = groups
        # observable families and model clusters are routes of the Part II network
        for r in self.routes:
            if r['branch'] != 'HEP':
                continue
            if r['rule'] == 'O-cluster (family)':
                rel = 'subset' if r['inputs'][0] in ('HEP:o_sig', 'HEP:o_G') else 'member'
                self.add('h.fam', r['inputs'][0], r['target'], rel, 'fam', frame=['HEP:m_A'], status='definition',
                         prov='Part II route ' + r['rid'], note='process family of the observable', year=r['year'])
            elif r['rule'] == 'R7/R10 absorb-cluster' and r['kind'] == 'subset':
                self.add('h.mcl', r['inputs'][0], r['target'], 'member', 'lin', status='definition',
                         prov='HEP Step 12 CLUSTER (' + r['rid'] + ')', year=r['year'])
            elif r['rule'] == 'R7/R10 absorb-cluster' and r['kind'] == 'lineage':
                self.add('h.lin', r['inputs'][0], r['target'], 'lineage', 'lin', status='established',
                         prov='HEP lineage (' + r['rid'] + ')', note=r['text'], year=r['year'])

    # ------------------------------------------------------------------ LG
    def lg(self):
        for u in ('LG:uE', 'LG:uB', 'LG:uM'):
            self.add('l.agg', u, 'LG:uR', 'aggregate', 'agg', frame=['LG:Ef'], status='definition',
                     prov='LG route r_uR', note='region total = sum of the local energies')
        self.add('l.agg', 'LG:uR', 'LG:U', 'aggregate', 'agg', frame=['LG:Ef'], status='definition',
                 prov='LG route r_U1', note='U = sum over regions of u_R')
        for u in ('LG:sR', 'LG:sN'):
            self.add('l.agg', u, 'LG:x', 'aggregate', 'agg', frame=['LG:Pr'], status='definition',
                     prov='LG routes r_sR, r_sN', note='local state = restriction P_R x of the global state')

    # ------------------------------------------------------------------ Part I cross-edges and glue
    def part1(self):
        G = self.d['G']
        concept = {c['id']: c for c in G['concepts']}
        self.concept = concept
        rep = {'hilbert_state': 'EM:hilb', 'maxwell_equations': 'EM:maxwell', 'poynting_vector': 'EM:S',
               'poisson_structure': 'EM:pb', 'photon': 'EM:photon', 'momentum': 'HEP:o_p',
               'qed_interaction': 'EM:qedL', 'observable_postulate': 'HEP:m_A',
               'schrodinger_evolution': 'EM:schro', 'measurement_incompatibility': 'GPT:e-incomp',
               'electric_energy_density': 'LG:uE', 'magnetic_energy_density': 'LG:uB'}

        def tgt(x):
            return rep[x[2:]] if x.startswith('c:') else x

        for e in G['cross_edges']:
            a, b, rel, note = e['from'], tgt(e['to']), e['relation'], e.get('note') or ''
            prov = 'Part I cross-edge (%s)' % rel
            if a.startswith('GPT:s-') and e['to'] == 'c:hilbert_state':
                self.add('x.car', a, b, 'subset', status='definition', prov=prov,
                         note='the cluster is a subset of the quantum state space (concept hilbert_state)')
            elif a == 'UP:particles':
                self.add('x.fam', b, a, 'member', 'fam', status='definition', prov=prov,
                         note='the textbook node is refined by the Fock sectors')
            elif a == 'EM:fock':
                self.add('x.fam', b, a, 'member', 'agg', status='definition', prov=prov, note=note)
            elif a == 'EM:spinor':
                self.add('x.fam', a, b, 'member', 'sym', frame=['HEP:m_U'], status='definition', prov=prov, note=note)
            elif a == 'EM:positron':
                self.add('x.fam', a, b, 'member', 'fam', status='definition', prov=prov, note=note)
            elif a == 'GPT:s-gauss':
                self.add('x.sub', a, b, 'subset', status='theorem', prov=prov, note=note)
            elif rel == 'part_of' and a.startswith('LG:'):
                self.add('x.agg', a, b, 'aggregate', 'agg', status='definition', prov=prov, note=note)
            elif rel == 'part_of' and a == 'EM:u':
                self.add('x.agg', b, a, 'aggregate', 'agg', status='definition', prov=prov, note=note)
            elif a in ('LG:Sin', 'LG:Sout', 'LG:U'):
                self.add('x.fam', a, b, 'member', 'fam', status='definition', prov=prov, note=note)
            elif a == 'UP:engine':
                self.add('x.fam', a, b, 'member', 'fam', status='definition', prov=prov, note=note)
            else:
                self.add('x.ref', a, b, 'refines', status='definition', prov=prov, note=note)
        # glue: GPT state cluster = QRT state set
        for cid in GLUE_EQUAL:
            ms = concept[cid]['members']
            gp = [m for m in ms if m.startswith('GPT:')]
            qr = [m for m in ms if m.startswith('QRT:') and not m.startswith('QRT:d-gibbs')]
            for a in gp:
                for b in qr:
                    self.add('x.eq', a, b, 'equal', status='definition', prov='Part I glue concept ' + cid,
                             note=concept[cid]['note'])
        # glue concepts that are memberships when read by extension
        self.add('x.gm', 'UP:mbd', 'GPT:s-thermal', 'member', 'con', status='standard',
                 prov='Part I glue concept gibbs_state, read as membership',
                 note='one-particle marginal of the classical canonical (Gibbs) state of an ideal gas')
        self.add('x.gm', 'UP:dslit', 'GPT:e-interf2', 'member', 'def', status='standard',
                 prov='Part I glue concept interference (role flip), read as membership',
                 note='double-slit fringes are an instance of two-path interference')
        # role flips that are reifications of an observable-layer cluster
        for cid in ('bell_nonlocality', 'epr_steering', 'ks_contextuality', 'measurement_incompatibility'):
            ms = concept[cid]['members']
            for a in [m for m in ms if m.startswith('GPT:')]:
                for b in [m for m in ms if m.startswith('QRT:')]:
                    self.add('x.rei', a, b, 'reify', status='definition', prov='Part I glue concept %s (role flip)' % cid,
                             note=concept[cid]['note'])

    # ------------------------------------------------------------------ curated for this network (2026-11-18)
    def curated(self):
        A = self.add
        O = 'curated 2026-11-18'
        for u, why in (('UP:stat', 'a solution with one definite energy: |psi_n><psi_n| commutes with H'),
                       ('UP:pib', 'the node lists the energy eigenfunctions psi_n of the infinite well'),
                       ('UP:qho', 'the node lists the energy eigenfunctions psi_n of the oscillator'),
                       ('UP:hatom', 'the node lists the energy eigenfunctions psi_nlm of the Coulomb problem')):
            A('c.mem', u, 'GPT:s-tts', 'member', 'sym', frame=['UP:tise'], status='definition', prov=O, note=why, origin=O)
        A('c.mem', 'UP:wpack', 'GPT:s-cohE', 'member', 'sym', frame=['UP:tdse'], status='elementary', prov=O,
          note='a superposition of plane waves of different |k| superposes different energies hbar^2 k^2 / 2m, so [rho, H] is not 0',
          origin=O)
        A('c.mem', 'UP:bbrad', 'GPT:s-thermal', 'member', 'con', frame=['UP:planck'], status='standard', prov=O,
          note='radiation in equilibrium at temperature T: the Gibbs state of the field modes', origin=O)
        A('c.mem', 'UP:theq', 'GPT:s-thermal', 'member', 'con', status='standard', prov=O,
          note='standard identification: the equilibrium state at temperature T is the Gibbs state (canonical ensemble)',
          origin=O)
        A('c.mem', 'UP:bbrad', 'GPT:s-gauss', 'member', 'sub', status='definition', prov=O,
          note='thermal state of a quadratic (free-field) Hamiltonian; listed in the definition of s-gauss', origin=O)
        A('c.cut', 'UP:qho', 'GPT:s-gauss', 'cut', 'sub', status='definition', prov=O,
          note='only the ground state psi_0, a Gaussian, is a member', origin=O)
        A('c.cut', 'UP:qho', 'GPT:s-wneg', 'cut', 'sub', status='theorem', prov=O + '; GPT:S6 (Hudson)',
          note='the eigenstates n >= 1 are pure and not Gaussian, hence Wigner-negative', origin=O)
        A('c.cut', 'HEP:s_g', 'GPT:s-gauss', 'cut', 'sub', frame=['HEP:m_field'], status='definition', prov=O,
          note='per field mode: only the rung |0> of the ladder is Gaussian', origin=O)
        A('c.cut', 'HEP:s_g', 'GPT:s-wneg', 'cut', 'sub', frame=['HEP:m_field'], status='theorem',
          prov=O + '; GPT:S6 (Hudson)',
          note='per field mode: the number states |N>, N >= 1, are pure and not Gaussian, hence Wigner-negative', origin=O)
        A('c.mem', ['HEP:o_x', 'HEP:o_p'], 'GPT:e-incomp', 'member', 'def', frame=['HEP:m_A', 'EM:comm'],
          status='theorem', prov=O,
          note='two sharp observables are jointly measurable only if they commute; [x, p] = i hbar', origin=O)
        A('c.mem', 'UP:DG', 'GPT:e-interf2', 'member', 'def', frame=['UP:debrog'], status='standard', prov=O,
          note='diffraction of single electrons by a crystal: multi-path interference, of second order in quantum theory',
          origin=O)
        A('c.mem', 'EM:abphase', 'GPT:e-interf2', 'member', 'def', frame=['EM:conn'], status='standard', prov=O,
          note='a shift of two-path electron interference fringes', origin=O)

    def build(self):
        self.qrt()
        self.gpt()
        self.hep()
        self.lg()
        self.part1()
        self.curated()
        return self.edges


# ---------------------------------------------------------------------------------------------
# closure of the membership relation (rule R20, descent)
# ---------------------------------------------------------------------------------------------
def class_domain(uid, nodes):
    br, nid = uid.split(':', 1)
    if br == 'QRT' and nid[:3] in ('sF-', 'sR-'):
        return CLASS_DOMAIN[nid[3:]]
    if br == 'GPT':
        return GPT_DOMAIN.get(nid)
    return None


def closure(edges, nodes):
    """Least fixed point of four monotone rules on signed membership facts.

      (i)   u in a,     a subset b              =>  u in b
      (ii)  u not in b, a subset b              =>  u not in a
      (iii) u in a,     a and b disjoint        =>  u not in b
      (iv)  u not in a, b complement of a       =>  u in b

    A conclusion about a cluster c is drawn only if the atom u is an object of the kind on which c
    is defined (CLASS_DOMAIN / GPT_DOMAIN against ATOM_DOMAINS), and an inclusion that is stated
    under a frame is used only for atoms that carry that frame (ATOM_FRAMES).  Each fact keeps the
    list of edges it was derived from.  A stated fact is never overwritten; a derived value that
    contradicts an existing fact is reported as a conflict.
    """
    sub = defaultdict(list)      # a -> [(b, source, frame tag)]
    for a, b, src, tag, frame in INCLUSIONS:
        sub[a].append((b, src, tag))
    for e in edges:
        if e['rel'] == 'equal' and e['id'].startswith('x.eq'):
            a, b = e['src'][0], e['dst']
            if nodes[b]['sub'] == 'S.dist':
                continue                      # s-bound = d-bound is entered as a fact below
            sub[a].append((b, e['id'], None))
            sub[b].append((a, e['id'], None))
    disj = defaultdict(list)
    comp = {}
    for e in edges:
        if e['rel'] == 'complement':
            a, b = e['src'][0], e['dst']
            comp[a], comp[b] = (b, e['id']), (a, e['id'])
            disj[a].append((b, e['id']))
            disj[b].append((a, e['id']))
    for a, b, src, note in DISJOINT:
        disj[a].append((b, src))
        disj[b].append((a, src))
    sup = defaultdict(list)
    for a, lst in sub.items():
        for b, src, tag in lst:
            sup[b].append((a, src, tag))

    def in_dom(u, c):
        dom = class_domain(c, nodes)
        if dom is None:
            return False
        if dom == 'any':
            return True
        return dom in ATOM_DOMAINS.get(u, set())

    def has(u, tag):
        return tag is None or tag in ATOM_FRAMES.get(u, set())

    facts = {}     # (u, c) -> dict(val, via, stated)
    for e in edges:
        if len(e['src']) != 1:
            continue
        u, c = e['src'][0], e['dst']
        if e['rel'] == 'member' and class_domain(c, nodes) is not None and nodes[u]['layer'] == 'S':
            facts[(u, c)] = dict(val=True, via=[e['id']], stated=True)
        elif e['rel'] == 'excluded' and class_domain(c, nodes) is not None and nodes[u]['layer'] == 'S':
            facts[(u, c)] = dict(val=False, via=[e['id']], stated=True)
        elif e['rel'] == 'equal' and e['id'].startswith('x.eq') and nodes[c]['sub'] == 'S.dist':
            facts[(c, u)] = dict(val=True, via=[e['id']], stated=True)      # d-bound is the cluster s-bound
    conflicts = []
    changed = True
    while changed:
        changed = False
        for (u, a), f in list(facts.items()):
            new = []
            if f['val']:
                for b, src, tag in sub.get(a, []):
                    if has(u, tag):
                        new.append(((u, b), True, src))
                for b, src in disj.get(a, []):
                    new.append(((u, b), False, src))
            else:
                for b, src, tag in sup.get(a, []):
                    if has(u, tag):
                        new.append(((u, b), False, src))
                if a in comp:
                    new.append(((u, comp[a][0]), True, comp[a][1]))
            for key, val, src in new:
                if not in_dom(key[0], key[1]):
                    continue
                if key not in facts:
                    facts[key] = dict(val=val, via=f['via'] + [src], stated=False)
                    changed = True
                elif facts[key]['val'] != val:
                    c = (key, facts[key]['via'], f['via'] + [src])
                    if c not in conflicts:
                        conflicts.append(c)
    return facts, conflicts
