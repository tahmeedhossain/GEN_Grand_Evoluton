"""Membership certificates for explicit two-qubit objects, and the inclusions they induce.

The cluster nodes of the resource-theory network are sets of states.  Here the claim "the abstract
network is a clustering of concrete states" is tested on objects small enough to compute with:
explicit two-qubit density matrices, each with a Hamiltonian, against executable definitions of
ten free sets.  Three things are produced:

  1. an incidence table  object x free set  with a grade on every cell
       computed   the predicate was evaluated on the density matrix
       derived    follows from a computed cell by a released inclusion edge (SS16, SS17)
       import     taken from the literature (thresholds of the Werner family)
       unknown    not decided here
  2. every single-premise implication  "free in a  =>  free in b"  that no object refutes, sorted into
       recorded      a released inclusion edge
       transitive    follows from released inclusion edges
       candidate     holds on all objects and is not derivable from the released edges
     and every released inclusion that an object would contradict (expected: none);
  3. for each released strictness claim, whether some object witnesses it.

Frame of the objects (fixed here, stated with every result):
  H = (wA/2) Z x 1 + (wB/2) 1 x Z with wA = 1, wB = 3/2 (nondegenerate, noninteracting), beta = 2;
  coherence, imaginarity, asymmetry and athermality are evaluated in the eigenbasis of the object's
  own Hamiltonian; the stabilizer polytope is the one of the Pauli frame X, Y, Z of each qubit.
"""
import itertools

import numpy as np
from scipy.optimize import linprog, minimize

TOL = 1e-9
I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
PAULI = [I2, X, Y, Z]
kron = np.kron
WA, WB, BETA = 1.0, 1.5, 2.0


def ket(*c):
    v = np.array(c, dtype=complex)
    return v / np.linalg.norm(v)


def proj(v):
    return np.outer(v, v.conj())


def gibbs(H, beta=BETA):
    w, V = np.linalg.eigh(H)
    p = np.exp(-beta * (w - w.min()))
    p /= p.sum()
    return (V * p) @ V.conj().T


K0, K1 = ket(1, 0), ket(0, 1)
KP, KPI = ket(1, 1), ket(1, 1j)
KH = ket(np.cos(np.pi / 8), np.sin(np.pi / 8))                 # real, non-stabilizer
_b = 0.5 * np.arccos(1 / np.sqrt(3))
KT = ket(np.cos(_b), np.exp(1j * np.pi / 4) * np.sin(_b))      # Bloch vector (1,1,1)/sqrt(3)
PHI = ket(1, 0, 0, 1)
PSIM = ket(0, 1, -1, 0)
H_DEF = 0.5 * WA * kron(Z, I2) + 0.5 * WB * kron(I2, Z)
_n = np.array([1, 1, 1]) / np.sqrt(3)
H_TILT = kron(-0.5 * WA * (_n[0] * X + _n[1] * Y + _n[2] * Z), I2) + 0.5 * WB * kron(I2, Z)


def werner(p):
    return p * proj(PSIM) + (1 - p) * np.eye(4) / 4


def objects():
    """name -> dict(rho, H, label, node, round, note)."""
    O = {}

    def add(name, rho, label, node=None, rnd=0, H=H_DEF, note=''):
        O[name] = dict(rho=np.array(rho, dtype=complex), H=H, label=label, node=node, round=rnd, note=note)

    add('I4', np.eye(4) / 4, 'I/4', 'QRT:d-maxmix')
    add('00', proj(kron(K0, K0)), '|00>')
    add('p0', proj(kron(KP, K0)), '|+>|0>', 'QRT:d-plus', note='|+> of the network, with |0> on the second qubit')
    add('T0', proj(kron(KT, K0)), '|T>|0>', 'QRT:d-tstate', note='named in QRT:SS13 and GPT:R4a')
    add('gibbs', gibbs(H_DEF), 'Gibbs state of H', None, note='H diagonal in the Pauli-Z product basis')
    add('gibbsT', gibbs(H_TILT), 'Gibbs state of a tilted H', 'QRT:d-gibbs', H=H_TILT,
        note='first qubit: H along (1,1,1)/sqrt(3); the generic case of QRT:SS3')
    add('bell', proj(PHI), '|Phi+>', 'QRT:d-bell')
    add('w20', werner(0.2), 'Werner p = 0.2')
    add('w40', werner(0.4), 'Werner p = 0.4', 'QRT:d-werner')
    add('w60', werner(0.6), 'Werner p = 0.6', 'QRT:d-werner')
    add('w90', werner(0.9), 'Werner p = 0.9')
    add('cc', 0.5 * proj(kron(K0, K0)) + 0.5 * proj(kron(K1, K1)), '(|00><00| + |11><11|)/2')
    add('ccdis', 0.5 * proj(kron(K0, K0)) + 0.5 * proj(kron(KP, KP)), '(|00><00| + |++><++|)/2', 'QRT:d-ccdis',
        note='example of GPT:R4b')
    # round 1: objects added in answer to implications that round 0 could not refute
    add('pi0', proj(kron(KPI, K0)), '|+i>|0>', None, 1, note='stabilizer state with an imaginary density matrix')
    add('H0', proj(kron(KH, K0)), '|H>|0>', None, 1, note='real state outside the stabilizer polytope')
    return O


# ---------------------------------------------------------------------------------------------
# stabilizer polytope of two qubits
# ---------------------------------------------------------------------------------------------
def stabilizer_states():
    Hd = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    S = np.array([[1, 0], [0, 1j]], dtype=complex)
    CN = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex)
    gens = [kron(Hd, I2), kron(I2, Hd), kron(S, I2), kron(I2, S), CN]

    def canon(v):
        k = np.argmax(np.abs(v) > 1e-9)
        v = v * np.exp(-1j * np.angle(v[k]))
        return tuple(np.round(v, 9).real.tolist() + np.round(v, 9).imag.tolist())

    start = kron(K0, K0)
    seen = {canon(start): start}
    frontier = [start]
    while frontier:
        nxt = []
        for v in frontier:
            for g in gens:
                w = g @ v
                c = canon(w)
                if c not in seen:
                    seen[c] = w
                    nxt.append(w)
        frontier = nxt
    return list(seen.values())


def pauli_vector(rho):
    return np.array([np.trace(rho @ kron(a, b)).real for a in PAULI for b in PAULI])


_STAB = None


def robustness_of_magic(rho):
    """min ||x||_1 with rho = sum_k x_k |s_k><s_k|; equals 1 iff rho is in the stabilizer polytope."""
    global _STAB
    if _STAB is None:
        _STAB = np.array([pauli_vector(proj(v)) for v in stabilizer_states()]).T      # 16 x 60
    A = np.hstack([_STAB, -_STAB])
    res = linprog(np.ones(A.shape[1]), A_eq=A, b_eq=pauli_vector(rho), bounds=(0, None), method='highs')
    assert res.status == 0, res.message
    return float(res.fun)


# ---------------------------------------------------------------------------------------------
# predicates
# ---------------------------------------------------------------------------------------------
def partial_transpose(rho):
    return rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)


def chsh_M(rho):
    T = np.array([[np.trace(rho @ kron(a, b)).real for b in (X, Y, Z)] for a in (X, Y, Z)])
    ev = np.sort(np.linalg.eigvalsh(T.T @ T))
    return float(ev[-1] + ev[-2])


def offdiag_min(rho, seed=7, starts=80):
    """Smallest off-diagonal weight of rho over all local orthonormal product bases (0 iff classical-classical)."""
    def U(t, f):
        return np.array([[np.cos(t / 2), -np.exp(-1j * f) * np.sin(t / 2)],
                         [np.exp(1j * f) * np.sin(t / 2), np.cos(t / 2)]])

    def f(x):
        W = kron(U(x[0], x[1]), U(x[2], x[3]))
        r = W.conj().T @ rho @ W
        return float(np.sum(np.abs(r - np.diag(np.diag(r))) ** 2))

    rng = np.random.default_rng(seed)
    best = f(np.zeros(4))
    for _ in range(starts):
        x0 = rng.uniform(0, 2 * np.pi, 4)
        r = minimize(f, x0, method='BFGS', options=dict(gtol=1e-12))
        best = min(best, float(r.fun))
        if best < 1e-13:
            break
    return best


ATTRS = ['pur', 'ath', 'asy', 'coh', 'ima', 'mag', 'dis', 'ent', 'ste', 'nlo']
ATTR_LABEL = {
    'pur': 'maximally mixed', 'ath': 'Gibbs state', 'asy': 'time-translation symmetric',
    'coh': 'incoherent (energy basis)', 'ima': 'real (energy basis)', 'mag': 'stabilizer polytope',
    'dis': 'classical-classical', 'ent': 'separable', 'ste': 'unsteerable', 'nlo': 'Bell-local'}
ATTR_NODE = {a: 'QRT:sF-' + a for a in ATTRS}
WERNER_IMPORT = {
    # p: (unsteerable?, local?, source)
    0.4: (True, True, 'unsteerable for p <= 1/2 (Wiseman, Jones, Doherty, Phys. Rev. Lett. 98, 140402 (2007)); '
                      'local model for all measurements for p <= 5/12 (Barrett, Phys. Rev. A 65, 042302 (2002))'),
    0.6: (False, True, 'steerable for p > 1/2 (Wiseman, Jones, Doherty 2007); local model for projective '
                       'measurements iff p <= 1/K_G(3) (Acin, Gisin, Toner, arXiv:quant-ph/0606138), a range that '
                       'contains p = 0.6 (local for p <= 0.6875 as quoted in arXiv:2309.09960); '
                       'locality under general measurements is not established at this p'),
}


def evaluate(name, o):
    rho, H = o['rho'], o['H']
    cell = {}

    def put(a, val, grade, detail):
        cell[a] = dict(val=val, grade=grade, detail=detail)

    d = np.linalg.norm(rho - np.eye(4) / 4)
    put('pur', bool(d < TOL), 'computed', '|rho - I/4| = %.3g' % d)
    d = np.linalg.norm(rho - gibbs(H))
    put('ath', bool(d < TOL), 'computed', '|rho - gamma| = %.3g' % d)
    d = np.linalg.norm(rho @ H - H @ rho)
    put('asy', bool(d < TOL), 'computed', '|[rho, H]| = %.3g' % d)
    w, V = np.linalg.eigh(H)
    r = V.conj().T @ rho @ V
    off = np.linalg.norm(r - np.diag(np.diag(r)))
    put('coh', bool(off < TOL), 'computed', 'off-diagonal norm in the eigenbasis of H = %.3g' % off)
    if np.allclose(H, np.diag(np.diag(H))):
        im = np.abs(rho.imag).max()
        put('ima', bool(im < TOL), 'computed', 'max |Im rho| in the eigenbasis of H = %.3g' % im)
    elif off < TOL:
        put('ima', True, 'computed', 'diagonal in the eigenbasis of H, hence real there')
    else:
        put('ima', None, 'unknown', 'eigenbasis phases of a non-diagonal H were not fixed')
    R = robustness_of_magic(rho)
    put('mag', bool(R < 1 + 1e-7), 'computed', 'robustness of magic = %.6f' % R)
    m = offdiag_min(rho)
    put('dis', bool(m < 1e-10), 'computed', 'least off-diagonal weight over local product bases = %.3g (numerical minimisation)' % m)
    ev = np.linalg.eigvalsh(partial_transpose(rho)).min()
    put('ent', bool(ev > -TOL), 'computed', 'least eigenvalue of the partial transpose = %.4f (PPT is exact for two qubits)' % ev)
    M = chsh_M(rho)
    p = None
    if name.startswith('w'):
        p = int(name[1:]) / 100
    if M > 1 + 1e-9:
        put('nlo', False, 'computed', 'CHSH: M = %.4f > 1 (Horodecki criterion), maximal value %.4f' % (M, 2 * np.sqrt(M)))
        put('ste', False, 'derived', 'not Bell-local, hence steerable (QRT:SS17)')
    elif cell['ent']['val']:
        put('ste', True, 'derived', 'separable, hence unsteerable (QRT:SS16)')
        put('nlo', True, 'derived', 'unsteerable, hence Bell-local (QRT:SS17)')
    elif p in WERNER_IMPORT:
        s, l, src = WERNER_IMPORT[p]
        put('ste', s, 'import', src)
        put('nlo', l, 'import', src + '; CHSH: M = %.4f <= 1' % M)
    else:
        put('ste', None, 'unknown', 'entangled, CHSH not violated (M = %.4f)' % M)
        put('nlo', None, 'unknown', 'entangled, CHSH not violated (M = %.4f)' % M)
    return cell


# released inclusions among the ten free sets (a subset of b), with their source
RECORDED_QRT = {
    ('coh', 'ent'): 'QRT:SS1', ('ath', 'coh'): 'QRT:SS12', ('coh', 'ima'): 'QRT:SS14',
    ('ent', 'ste'): 'QRT:SS16', ('ste', 'nlo'): 'QRT:SS17', ('asy', 'coh'): 'QRT:SS18',
    ('coh', 'asy'): 'QRT:SS18',
    # the free set of purity is the single state I/d: "pur => b" is the membership of I/d in b
    ('pur', 'ent'): 'QRT:SS2', ('pur', 'coh'): 'QRT:SS2', ('pur', 'asy'): 'QRT:SS2',
    ('pur', 'ima'): 'QRT:SS2', ('pur', 'mag'): 'QRT:SS2',
    # the free set of athermality is the single state gamma
    ('ath', 'asy'): 'QRT:SS3b', ('ath', 'ima'): 'QRT:SS3b',
}
# inclusions that reach the resource-theory sets through the glue with the nonclassicality network
RECORDED_GPT = {
    ('dis', 'ent'): 'GPT:S7 (zero-discord states are separable), through the glue of the two networks',
}
RECORDED_GPT_DERIVED = {
    ('asy', 'dis'): 'GPT:R1 (derived in the project: nondegenerate noninteracting H, symmetric states are classical-classical)',
}
LEVELS = [('QRT', RECORDED_QRT),
          ('QRT+GPT', {**RECORDED_QRT, **RECORDED_GPT}),
          ('QRT+GPT+R1', {**RECORDED_QRT, **RECORDED_GPT, **RECORDED_GPT_DERIVED})]
# released strictness / independence claims: the implication a => b must fail
STRICT = [
    ('ent', 'coh', 'QRT:SS1 (strict)'), ('coh', 'ath', 'QRT:SS12 (the Gibbs state is one incoherent state)'),
    ('ima', 'coh', 'QRT:SS14 (strict)'), ('ste', 'ent', 'QRT:SS16 (strict)'), ('nlo', 'ste', 'QRT:SS17 (strict)'),
    ('mag', 'ent', 'QRT:SS13'), ('ent', 'mag', 'QRT:SS13'), ('ent', 'dis', 'GPT:S7 (strict)'),
    ('coh', 'mag', 'QRT:SS3 (thermal magic: energy-incoherent yet magic)'),
]


def transitive(rec):
    cl = set(rec)
    changed = True
    while changed:
        changed = False
        for (a, b), (c, e) in itertools.product(list(cl), list(cl)):
            if b == c and a != e and (a, e) not in cl:
                cl.add((a, e))
                changed = True
    return cl


def analyse(rounds=(0, 1)):
    O = objects()
    table = {n: evaluate(n, o) for n, o in O.items()}
    out = dict(frame=dict(wA=WA, wB=WB, beta=BETA, H='(wA/2) Z x 1 + (wB/2) 1 x Z',
                          tilted='first qubit: -(wA/2) n.sigma with n = (1,1,1)/sqrt(3)'),
               attrs=[dict(id=a, label=ATTR_LABEL[a], node=ATTR_NODE[a]) for a in ATTRS],
               objects=[dict(id=n, label=o['label'], node=o['node'], round=o['round'], note=o['note'],
                             cells=table[n]) for n, o in O.items()],
               n_stabilizer_states=len(stabilizer_states()), rounds=[])
    for rnd in rounds:
        objs = [n for n, o in O.items() if o['round'] <= rnd]
        base = []
        for a, b in itertools.permutations(ATTRS, 2):
            pos = [n for n in objs if table[n][a]['val'] is True]
            ref = [n for n in pos if table[n][b]['val'] is False]
            unk = [n for n in pos if table[n][b]['val'] is None]
            imported = [n for n in ref if 'import' in (table[n][a]['grade'], table[n][b]['grade'])]
            base.append(dict(a=a, b=b, support=len(pos), refuted_by=ref[:3], unknown=unk,
                             refuted=bool(ref), vacuous=not pos,
                             refuted_only_by_import=bool(ref) and len(imported) == len(ref)))
        levels = []
        for name, rec in LEVELS:
            cl = transitive(rec)
            imps, cnt, contra = [], {}, []
            for i in base:
                key = (i['a'], i['b'])
                if i['refuted']:
                    kind = 'refuted'
                    if key in cl:
                        contra.append(dict(a=i['a'], b=i['b'], by=i['refuted_by']))
                elif i['vacuous']:
                    kind = 'vacuous'
                elif key in rec:
                    kind = 'recorded'
                elif key in cl:
                    kind = 'transitive'
                else:
                    kind = 'candidate'
                cnt[kind] = cnt.get(kind, 0) + 1
                imps.append(dict(i, kind=kind, source=rec.get(key)))
            levels.append(dict(level=name, counts=cnt, contradictions=contra,
                               candidates=[dict(a=i['a'], b=i['b'], support=i['support']) for i in imps
                                           if i['kind'] == 'candidate'],
                               implications=imps))
        strict = []
        for a, b, src in STRICT:
            i = next(x for x in base if x['a'] == a and x['b'] == b)
            strict.append(dict(a=a, b=b, source=src, witnessed=i['refuted'], by=i['refuted_by'],
                               only_by_import=i['refuted_only_by_import']))
        out['rounds'].append(dict(round=rnd, n_objects=len(objs), levels=levels, strict=strict))
    return out


if __name__ == '__main__':
    import json
    res = analyse()
    print('stabilizer states:', res['n_stabilizer_states'])
    print('%-8s' % '' + ' '.join('%-4s' % a for a in ATTRS))
    for o in res['objects']:
        row = ' '.join('%-4s' % ({True: 'F', False: 'R', None: '?'}[o['cells'][a]['val']] +
                                 {'computed': '', 'derived': "'", 'import': '*', 'unknown': ''}[o['cells'][a]['grade']])
                       for a in ATTRS)
        print('%-8s' % o['id'] + row + '   ' + o['label'] + (' [round 1]' if o['round'] else ''))
    for r in res['rounds']:
        print('\nround', r['round'], 'objects', r['n_objects'])
        for lv in r['levels']:
            print('  ', lv['level'], lv['counts'], 'contradictions', len(lv['contradictions']),
                  'candidates', [(c['a'], c['b']) for c in lv['candidates']])
        for st in r['strict']:
            print('    strict', st['a'], '=/=>', st['b'], st['source'],
                  ('witnessed' + (' (import only)' if st['only_by_import'] else '')) if st['witnessed'] else 'NOT WITNESSED', st['by'])
    json.dump(res, open('out/context.json', 'w'), indent=1)
