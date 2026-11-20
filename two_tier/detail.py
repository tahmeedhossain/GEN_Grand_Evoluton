"""Statement, references and check data behind every route, abstraction edge and node.

Embedded in the page and read the first time a node or an edge is selected.  An array with one record
per line; `k` is the kind of record:

  r   route             u, s (full statement), refs, src (where it comes from) and, by branch, cond, via,
                        title, tags, step
  a   abstraction edge  id, links (routes it rests on), via (closure chain), kern (cells of the
                        two-qubit table), concept, step
  n   node              u, df (full definition) and, by branch, refs, theory, family, role, status, years,
                        symbol, math, props, uir, sub, req, blind
  s   HEP step          id, n, title, years, driver, text, refs

Nothing here is computed: every field is copied from a source file, except `links`, `via` and `kern`,
which point to other records of the built network.
"""
import json
import os
import re

from .load import source

ROLE_NAME = {
    'model': 'model (the axioms that fix the free operations)', 'framework': 'framework', 'free_state': 'free states',
    'resource_state': 'resource states', 'free_ops': 'free operations', 'use_ops': 'resource-utilizing operations',
    'no_ops': 'operations impossible even with resources', 'detector': 'detection witness', 'quantifier': 'quantifier',
    'dist': 'distinguished state',
}


def _clean(d):
    return {k: v for k, v in d.items() if v not in (None, '', [], {})}


def build_detail(full):
    G, E = source('grand'), source('evolution')
    GPT, QRT, HEP = source('gpt'), source('qrt'), source('hep')

    nodes = {n['uid']: n for n in full['nodes']}
    routes = full['routes']
    abst = full['abst']
    route_uid = {r['uid'] for r in routes}
    abst_id = {e['id'] for e in abst}

    groute = {r['uid']: r for r in G['routes']}
    gnode = {n['uid']: n for n in G['nodes']}
    eroute = {r['uid']: r for r in E['routes']}
    enode = {n['uid']: n for n in E['nodes']}
    gpt_e = {e['id']: e for e in GPT['edges']}
    gpt_n = {n['id']: n for n in GPT['nodes']}
    qrt_e = {e['id']: e for e in QRT['edges']}
    qrt_n = {n['id']: n for n in QRT['nodes']}
    qrt_t = {t['id']: t for t in QRT['theories']}
    hep_step = {s['id']: (i + 1, s) for i, s in enumerate(HEP['steps'])}
    hep_ref = HEP['references']
    concept = {c['id']: c for c in G['concepts']}

    recs = []

    # ---- steps of the Standard Model history ----------------------------------------------------
    for sid, (i, s) in hep_step.items():
        recs.append(_clean(dict(k='s', id=sid, n=i, title=s['title'], years=s['years'], driver=s.get('driverLabel'),
                                text=s.get('text'), refs=[hep_ref.get(x, x) for x in s.get('refs', [])])))
    # ---- routes -------------------------------------------------------------------------------
    for r in routes:
        b, uid, rid = r['branch'], r['uid'], r['rid']
        rec = dict(k='r', u=uid)
        if b == 'GPT':
            e = gpt_e[rid]
            rec.update(s=e['statement'], refs=e['refs'], cond=e.get('condition'),
                       src='GEN_GPT_Level v2.6, edge ' + rid)
        elif b == 'QRT':
            e = qrt_e[rid]
            rec.update(s=e['statement'], refs=e['refs'], via=e.get('via'), src='GEN_QRT_Level v1.2, edge ' + rid)
        elif b == 'EM':
            ex = groute[uid]['extra']
            par = ex.get('text_marker_paragraph')
            rec.update(s=ex.get('formula'), title=ex.get('title'),
                       src='GEN_epistemic_evolution v3.1, reader section %s%s' % (
                           ex.get('section'), '' if par is None else ', paragraph %s' % par),
                       yp=eroute[uid]['year_prov'])
        elif b == 'HEP':
            sid = rid.split('/')[0]
            rec.update(s=eroute[uid]['text'], yp=eroute[uid]['year_prov'])
            if sid in hep_step:
                i, s = hep_step[sid]
                rec.update(step=sid, src='GEN_HEP v1.2, step %d: %s (%s)' % (i, s['title'], s['years']))
            else:
                rec.update(src='GEN_HEP v1.2, family of observables')
        elif b in ('UP', 'LG'):
            ex = groute[uid.split('>')[0]]['extra']
            if b == 'UP':
                rec.update(s=ex.get('formula'), title=ex.get('title'), tags=ex.get('tags'),
                           src='University Physics reader (GEN_Learning v2), volume %s, section %s' % (
                               ex.get('vol'), ex.get('section')))
            else:
                rec.update(s=ex.get('label'), src='GEN_LocGlob_Flow v6.1, route ' + rid)
        if rec.get('s') == r['text'] and len(r['text'] or '') <= 170:
            del rec['s']                      # the page already holds the full statement
        recs.append(_clean(rec))

    # ---- kernel cells per (atom node, class node) ---------------------------------------------
    ctx = full['context']
    cls_of = {m: c['id'] for c in full['classes'] for m in c['nodes']}
    comp = {}
    for e in abst:
        if e['rel'] == 'complement':
            a, b2 = e['src'][0], e['dst']
            if a in cls_of and b2 in cls_of:
                comp[cls_of[a]], comp[cls_of[b2]] = cls_of[b2], cls_of[a]
    attr_free = {cls_of[a['node']]: a for a in ctx['attrs'] if a['node'] in cls_of}
    attr_res = {comp[c]: a for c, a in attr_free.items() if c in comp}
    obj_of = {}
    for o in ctx['objects']:
        if o.get('node'):
            obj_of.setdefault(o['node'], []).append(o)

    def kern(u, c):
        cls = cls_of.get(c)
        a = attr_free.get(cls) or attr_res.get(cls)
        if a is None or u not in obj_of:
            return None
        out = []
        for o in obj_of[u]:
            cell = o['cells'][a['id']]
            out.append(dict(obj=o['label'], attr=a['label'], set=nodes[a['node']]['label'], free=cell['val'],
                            grade=cell['grade'], detail=cell['detail']))
        return out

    # ---- abstraction edges --------------------------------------------------------------------
    for e in abst:
        rec = dict(k='a', id=e['id'])
        links = []

        def link(u):
            if u in route_uid and u not in links:
                links.append(u)

        if e.get('route'):
            link(e['route'])
        prov = e['prov'] or ''
        if e['origin'] == 'closure':
            rec['via'] = [x.strip() for x in prov.split(':', 1)[1].split(';') if x.strip()]
        else:
            for m in re.finditer(r'\b(QRT|GPT):([A-Za-z0-9]+)', prov):
                link(m.group(1) + ':' + m.group(2))
            m = re.search(r'LG routes? ([\w, ]+)', prov)
            if m:
                for tok in re.findall(r'r_\w+', m.group(1)):
                    for u in route_uid:
                        if u.startswith('LG:' + tok + '>'):
                            link(u)
            m = re.search(r'HEP [Ss]tep (\d+)', prov)
            if m:
                for sid, (i, s) in hep_step.items():
                    if i == int(m.group(1)):
                        rec['step'] = sid
            m = re.search(r'glue concept (\w+)', prov)
            if m and m.group(1) in concept:
                c = concept[m.group(1)]
                rec['concept'] = _clean(dict(id=c['id'], label=c['label'], note=c.get('note'),
                                             members=[x for x in c['members'] if x in nodes]))
        if links:
            rec['links'] = links
        if len(e['src']) == 1 and e['rel'] in ('member', 'excluded', 'cut'):
            kc = kern(e['src'][0], e['dst'])
            if kc:
                rec['kern'] = kc
        if len(rec) > 2:
            recs.append(rec)

    # ---- nodes --------------------------------------------------------------------------------
    for uid, n in nodes.items():
        b, nid = n['branch'], n['nid']
        rec = dict(k='n', u=uid)
        if b == 'GPT':
            g = gpt_n[nid]
            rec.update(df=g['def'], kind=g['type'], src='GEN_GPT_Level v2.6, node ' + nid)
            w = GPT['witnesses'].get(nid)
            if w:
                req = [['GPT:' + x[0], x[1]] for grp in w.get('requires', {}).values() for x in grp
                       if 'GPT:' + x[0] in nodes]
                blind = [['GPT:' + x[0], x[1]] for x in w.get('blind', []) if 'GPT:' + x[0] in nodes]
                rec.update(req=req, blind=blind)
        elif b == 'QRT':
            q = qrt_n[nid]
            t = qrt_t.get(q['theory'])
            rec.update(df=q['statement'], refs=q['refs'], theory=t['name'] if t else q['theory'],
                       family=t['family'] if t else None, role=ROLE_NAME.get(q['role'], q['role']),
                       status=q['status'], src='GEN_QRT_Level v1.2, node ' + nid)
        elif b == 'HEP':
            h = HEP['nodes'].get(nid, {})
            rec.update(df=h.get('desc'), years=h.get('years'), refs=[hep_ref.get(x, x) for x in h.get('refs', [])],
                       uir=h.get('uir'), sub=h.get('sub'), src='GEN_HEP v1.2, node ' + nid)
        elif b == 'EM':
            ex = gnode[uid]['extra']
            rec.update(df=ex.get('description'), symbol=ex.get('symbol'), math=ex.get('math_structure'),
                       props=ex.get('properties'), yp=enode[uid]['year_prov'],
                       src='GEN_epistemic_evolution v3.1, reader section %s' % ex.get('section'))
        elif b == 'UP':
            ex = gnode[uid]['extra']
            rec.update(df=ex.get('description'), symbol=ex.get('symbol'),
                       src='University Physics reader (GEN_Learning v2), volume %s, section %s' % (
                           ex.get('vol'), ex.get('section')))
        elif b == 'LG':
            ex = gnode[uid]['extra']
            rec.update(symbol=ex.get('symbol'), df=ex.get('property'), src='GEN_LocGlob_Flow v6.1, node ' + nid)
        if rec.get('df') == n['desc'] and len(n['desc'] or '') <= 240:
            del rec['df']                     # the page already holds the full definition
        if isinstance(rec.get('props'), (list, dict)):
            rec['props'] = json.dumps(rec['props'], ensure_ascii=False)
        recs.append(_clean(rec))
    return recs


def write_detail(full, path):
    recs = build_detail(full)
    with open(path, 'w') as f:
        f.write('[\n' + ',\n'.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) for r in recs) + '\n]\n')
    return recs
