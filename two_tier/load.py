"""Load every source into one node table and one route table.

Sources (in data/ of this repository):
  gen_grand_network.json      Part I merged network (six released branches, glue concepts, cross-edges)
  gen_evolution_network.json  Part II chronology (EM, HEP, GPT, QRT: years, phases, rules; HEP union of steps)
  sources/gpt_v2.6.json, sources/qrt_v1.2.json, sources/hep_v1.2.json   released data files of
                              GEN_GPT_Level, GEN_QRT_Level and GEN_HEP (commits in sources/PROVENANCE.txt)

Conventions
  uid            'BRANCH:native_id'
  tier           'C' system-specific (EM, HEP, UP, LG)
                 'A' generic        (GPT, QRT)
  year           calendar year from the Part II chronology; None for UP and LG (book / version order)
  status         'released' for every node and route
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # repository root
DATA = os.path.join(HERE, 'data')
SOURCES = {
    'grand': 'gen_grand_network.json',
    'evolution': 'gen_evolution_network.json',
    'gpt': os.path.join('sources', 'gpt_v2.6.json'),
    'qrt': os.path.join('sources', 'qrt_v1.2.json'),
    'hep': os.path.join('sources', 'hep_v1.2.json'),
}


def source(name):
    return json.load(open(os.path.join(DATA, SOURCES[name]), encoding='utf-8'))

LOW = ('EM', 'HEP', 'UP', 'LG')
HIGH = ('GPT', 'QRT')
BRANCH_TITLE = {
    'EM': 'Electromagnetism reader (GEN_epistemic_evolution v3.1)',
    'HEP': 'Standard Model history (GEN_HEP v1.2, union of the 12 steps)',
    'UP': 'University Physics reader (GEN_Learning v2)',
    'LG': 'Local cycles, global conservation (GEN_LocGlob_Flow v6.1)',
    'GPT': 'Nonclassicality network (GEN_GPT_Level v2.6)',
    'QRT': 'Resource-theory network (GEN_QRT_Level v1.2)',
}

def _short(s, n=260):
    s = (s or '').strip().replace('\n', ' ')
    return s if len(s) <= n else s[: n - 1].rstrip() + '…'


def load_all():
    G = source('grand')
    E = source('evolution')

    gnode = {n['uid']: n for n in G['nodes']}
    nodes, routes = {}, []

    # ---- dated branches (Part II) -------------------------------------------------------------
    for n in E['nodes']:
        g = gnode.get(n['uid'], {})
        nodes[n['uid']] = dict(
            uid=n['uid'], branch=n['branch'], nid=n['native_id'], label=n['label'], layer=n['layer'],
            sub=n['sublayer'], tier='C' if n['branch'] in LOW else 'A', year=n['year'],
            year_prov=n['year_prov'], desc=_short(n.get('desc')), concept=g.get('concept'),
            removed=bool(n.get('removed')), removal_year=n.get('removal_year'),
            step_first=n.get('step_first'), step_last=n.get('step_last'), status='released')
    for r in E['routes']:
        routes.append(dict(
            uid=r['uid'], branch=r['branch'],
            rid=r['native_id'], inputs=list(r['inputs']), target=r['target'], logic=r.get('logic'),
            kind=r['kind'], status=r.get('status'), polarity=r.get('polarity'), year=r['year'],
            phase=r['phase'], rule=r['rule'], text=_short(r.get('text'), 220),
            removed=bool(r.get('removed')), removal_year=r.get('removal_year'), rstatus='released'))

    # ---- undated branches (Part I) ------------------------------------------------------------
    for n in G['nodes']:
        if n['branch'] in ('UP', 'LG'):
            ex = n.get('extra') or {}
            nodes[n['uid']] = dict(
                uid=n['uid'], branch=n['branch'], nid=n['native_id'], label=n['label'], layer=n['layer'],
                sub=n['sublayer'], tier='C', year=None, year_prov='undated (book / version order)',
                desc=_short(ex.get('description') or ex.get('property') or ex.get('symbol')),
                concept=n.get('concept'), removed=False, removal_year=None, step_first=None,
                step_last=None, status='released', t=n.get('t'))
    for r in G['routes']:
        if r['branch'] in ('UP', 'LG'):
            ex = r.get('extra') or {}
            routes.append(dict(
                uid=r['uid'] + '>' + r['target'].split(':', 1)[1], branch=r['branch'],
                rid=r['native_id'], inputs=list(r['inputs']), target=r['target'], logic=r.get('logic'),
                kind=r['kind'], status=r.get('status'), polarity=r.get('polarity'), year=None,
                phase='falsify' if r['kind'] == 'failed' else 'predict',
                rule='R12 fail' if r['kind'] == 'failed' else 'R11 derive',
                text=_short(ex.get('formula') or ex.get('title') or ex.get('label'), 220),
                removed=False, removal_year=None, rstatus='released'))

    for r in routes:
        for u in r['inputs'] + [r['target']]:
            assert u in nodes, (r['uid'], u)
    return dict(G=G, E=E, nodes=nodes, routes=routes)


if __name__ == '__main__':
    import collections
    d = load_all()
    print(len(d['nodes']), 'nodes;', len(d['routes']), 'routes')
    print(collections.Counter(n['branch'] for n in d['nodes'].values()))
    print(collections.Counter(r['branch'] for r in d['routes']))
    print(collections.Counter((n['tier'], n['layer']) for n in d['nodes'].values()))
