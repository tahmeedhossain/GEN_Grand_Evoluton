#!/usr/bin/env python3
"""Build the two-tier network (main network of this repository): python3 build_two_tier.py

Reads data/gen_grand_network.json, data/gen_evolution_network.json and data/sources/{gpt_v2.6,qrt_v1.2,hep_v1.2}.json.
Writes data/gen_two_tier_network.json (everything), out/two_tier_numbers.json (every number quoted in the
page and in TWO_TIER.md), out/two_tier_context.json (the two-qubit kernel table), gen_two_tier_explorer.html
(self-contained page) and TWO_TIER.md.
"""
import datetime
import json
import os
from collections import Counter, defaultdict

from two_tier import kernel
from two_tier.export import export
from two_tier.notes import write_notes
from two_tier.abstraction import (ATOM_DOMAINS, ATOM_FRAMES, CLASS_DOMAIN, DISJOINT, FAMILY_CRIT, GPT_DOMAIN,
                                INCLUSIONS, Builder, class_domain, closure)
from two_tier.load import BRANCH_TITLE, HIGH, LOW, load_all
from two_tier.pipeline import (OPERATIONS, PHASES, PHASES8, RULES, STAGES, attribute, timeline)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
DATA = os.path.join(HERE, 'data')
os.makedirs(OUT, exist_ok=True)

MEMBER_REL = ('member', 'cut', 'excluded', 'aggregate')


def main():
    d = load_all()
    nodes, routes = d['nodes'], d['routes']
    B = Builder(d)
    abst = B.build()

    # ------------------------------------------------------------------ closure (rule R20)
    facts, conflicts = closure(abst, nodes)
    n_k = 0
    for (u, c), f in sorted(facts.items()):
        if f['stated']:
            continue
        n_k += 1
        abst.append(dict(id='k.%03d' % n_k, src=[u], dst=c, rel='member' if f['val'] else 'excluded', crit=None,
                         frame=[], status='derived', prov='closure: ' + ' ; '.join(f['via']),
                         note='derived by rule R20 from the edges listed',
                         year=2026 if nodes[u]['year'] is not None else None, origin='closure'))
    by_route = attribute(nodes, routes, abst)
    T = timeline(nodes, routes, abst)

    # ------------------------------------------------------------------ glue classes of state clusters
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in abst:
        if e['rel'] == 'equal' and e['id'].startswith('x.eq') and nodes[e['dst']]['sub'] != 'S.dist':
            parent[find(e['src'][0])] = find(e['dst'])
    cls_nodes = [u for u, n in nodes.items() if n['tier'] == 'A' and n['branch'] in HIGH
                 and n['sub'] in ('S.cluster', 'S.free', 'S.resource')]
    groups = defaultdict(list)
    for u in cls_nodes:
        groups[find(u)].append(u)
    classes = []
    for root, ms in groups.items():
        ms = sorted(ms, key=lambda u: (0 if u.startswith('QRT') else 1, u))
        classes.append(dict(id=ms[0], nodes=ms, label=nodes[ms[0]]['label'],
                            domain=next((class_domain(m, nodes) for m in ms if class_domain(m, nodes)), None)))
    classes.sort(key=lambda c: c['id'])
    cls_of = {m: c['id'] for c in classes for m in c['nodes']}

    # ------------------------------------------------------------------ three-leg lint
    comp_of = {}
    for e in abst:
        if e['rel'] == 'complement':
            comp_of[e['src'][0]], comp_of[e['dst']] = e['dst'], e['src'][0]
    reified = defaultdict(list)          # state-layer node -> observable-layer clusters it reifies
    for e in abst:
        if e['rel'] == 'reify':
            reified[e['dst']].append(e['src'][0])

    def legs(c):
        ms = set(c['nodes'])
        partner = {cls_of[comp_of[m]] for m in ms if m in comp_of and comp_of[m] in cls_of}
        pm = {m for q in classes if q['id'] in partner for m in q['nodes']}
        crit = [e['id'] for e in abst if e['rel'] == 'criterion' and e['dst'] in ms]
        test = [e['id'] for e in abst if e['rel'] == 'test' and e['dst'] in ms]
        test_c = [e['id'] for e in abst if e['rel'] == 'test' and e['dst'] in pm]
        via = {x for m in ms for x in reified.get(m, [])}
        mem_s = [e for e in abst if e['dst'] in ms and e['rel'] in ('member', 'cut') and e['origin'] != 'closure']
        mem_s += [e for e in abst if e['rel'] == 'equal' and e['src'][0] in ms and nodes[e['dst']]['sub'] == 'S.dist']
        mem_r = [e for e in abst if e['dst'] in via and e['rel'] in ('member', 'cut')]
        mem_d = [e for e in abst if e['dst'] in ms and e['rel'] == 'member' and e['origin'] == 'closure']

        # count members per class, not per node: a stated membership on one node of a glue class and its
        # derived twin on the other node are one stated member
        def key(e):
            return (e['dst'],) if e['rel'] == 'equal' else tuple(e['src'])

        S = {}
        for e in mem_s:
            S.setdefault(key(e), e)
        R = {}
        for e in mem_r:
            if key(e) not in S:
                R.setdefault(key(e), e)
        D = {}
        for e in mem_d:
            if key(e) not in S and key(e) not in R:
                D.setdefault(key(e), e)
        tiers = Counter(nodes[k[0]]['tier'] for k in list(S) + list(R))
        tiers_d = Counter(nodes[k[0]]['tier'] for k in D)
        return dict(criterion=crit, test=test, test_complement=test_c, stated=len(S), via_reify=len(R),
                    derived=len(D), stated_C=tiers.get('C', 0), stated_A=tiers.get('A', 0),
                    derived_C=tiers_d.get('C', 0), derived_A=tiers_d.get('A', 0))

    for c in classes:
        c['legs'] = legs(c)
        L = c['legs']
        c['has_member'] = L['stated'] + L['via_reify'] + L['derived'] > 0
        c['has_test'] = bool(L['test'] or L['test_complement'])
        c['three_leg'] = bool(L['criterion']) and c['has_test'] and c['has_member']
    effects = []
    for u, n in nodes.items():
        if n['sub'] == 'O.effect' and n['branch'] == 'GPT':
            ref = [e['id'] for e in abst if e['rel'] == 'criterion' and e['dst'] == u]
            test = [e['id'] for e in abst if e['rel'] == 'test' and e['dst'] == u]
            mem = [e for e in abst if e['dst'] == u and e['rel'] in ('member', 'cut')]
            effects.append(dict(id=u, label=n['label'], reference=ref, test=test, members=[e['id'] for e in mem],
                                members_C=sum(1 for e in mem if all(nodes[s]['tier'] == 'C' for s in e['src'])),
                                three_leg=bool(ref) and bool(test) and bool(mem)))
    effects.sort(key=lambda x: x['id'])

    # ------------------------------------------------------------------ census: atoms x classes
    atoms = sorted({k[0] for k in facts} | {e['src'][0] for e in abst if e['rel'] == 'cut' and len(e['src']) == 1
                                             and e['dst'] in cls_of})
    cell = {}
    for (u, c), f in facts.items():
        if c in cls_of:
            k, v = (u, cls_of[c]), ('in' if f['val'] else 'out') + ('' if f['stated'] else '*')
            if k in cell and cell[k].rstrip('*') != v.rstrip('*'):
                raise SystemExit('census: contradictory facts in one glue class: %s' % (k,))
            if k not in cell or (cell[k].endswith('*') and not v.endswith('*')):
                cell[k] = v                 # a stated fact on either node of the class takes precedence
    for e in abst:
        if e['rel'] == 'cut' and len(e['src']) == 1 and e['dst'] in cls_of:
            cell.setdefault((e['src'][0], cls_of[e['dst']]), 'cut')

    def applicable(u, c):
        dom = c['domain']
        return dom in (None, 'any') or dom in ATOM_DOMAINS.get(u, set())

    census = dict(atoms=atoms, classes=[c['id'] for c in classes], cells={}, applicable=0, known=0, stated=0,
                  derived=0, cut=0)
    for u in atoms:
        for c in classes:
            v = cell.get((u, c['id']))
            if not applicable(u, c) and v is None:
                census['cells'][u + '|' + c['id']] = 'na'
                continue
            census['applicable'] += 1
            if v:
                census['known'] += 1
                census['cut' if v == 'cut' else ('derived' if v.endswith('*') else 'stated')] += 1
                census['cells'][u + '|' + c['id']] = v

    # ------------------------------------------------------------------ kernel and cross-check
    ctx = kernel.analyse()
    attr_of = {}
    for a in kernel.ATTRS:
        attr_of['QRT:sF-' + a] = (a, True)
        attr_of['QRT:sR-' + a] = (a, False)
    for g, (a, pol) in {'s-sep': ('ent', True), 's-ent': ('ent', False), 's-coh': ('coh', False),
                        's-cohE': ('asy', False), 's-tts': ('asy', True), 's-thermal': ('ath', True),
                        's-athermal': ('ath', False), 's-stab': ('mag', True), 's-magic': ('mag', False),
                        's-discord': ('dis', False), 's-zerodisc': ('dis', True)}.items():
        attr_of['GPT:' + g] = (a, pol)
    check = dict(agree=0, disagree=[], unknown=0, compared=0)
    seen = set()                       # distinct facts; an atom realised by two objects is compared twice
    for o in ctx['objects']:
        if not o['node']:
            continue
        for (u, c), f in facts.items():
            if u != o['node'] or c not in attr_of:
                continue
            a, free_side = attr_of[c]
            want_free = (f['val'] == free_side)          # the fact says: the object is in the free set of a
            got = o['cells'][a]['val']
            check['compared'] += 1
            seen.add((u, c))
            if got is None:
                check['unknown'] += 1
            elif got == want_free:
                check['agree'] += 1
            else:
                check['disagree'].append(dict(object=o['id'], node=u, cls=c, fact=f['val'], stated=f['stated'],
                                              kernel=got, detail=o['cells'][a]['detail']))
    check['facts'] = len(seen)
    ctx['crosscheck'] = check

    # ------------------------------------------------------------------ counts
    def tier(u):
        return nodes[u]['tier']

    flow = Counter()
    flow_branch = Counter()
    flow_pairs = Counter()
    for e in abst:
        if e['rel'] in MEMBER_REL and e['origin'] != 'closure':
            ts = '+'.join(sorted({tier(x) for x in e['src']}))
            flow[(ts, tier(e['dst']), e['rel'])] += 1                 # one count per edge
            flow_branch[('+'.join(sorted({nodes[x]['branch'] for x in e['src']})), nodes[e['dst']]['branch'])] += 1
            for x in e['src']:
                flow_pairs[(tier(x), tier(e['dst']), e['rel'])] += 1   # one count per (source node, cluster)
    carrier = sum(1 for e in abst if e['rel'] == 'subset' and tier(e['src'][0]) == 'A' and tier(e['dst']) == 'C')
    ev = Counter()                      # dated events by stage; the same counting as pipeline.timeline
    ev8 = Counter()                     # the eight-phase table of Part II (nodes and routes only)
    for n in nodes.values():
        if n['year'] is not None:
            ev[n['stage']] += 1
            ev8[{'O': 'observe', 'M': 'hypothesize', 'S': 'restructure'}[n['layer']]] += 1
    for r in routes:
        if r['year'] is not None:
            ev[r['stage']] += 1
            ev8[r['phase8']] += 1
    extra = [e for e in abst if e['year'] is not None and not (e.get('route') and e['rel'] in
                                                                  ('member', 'subset', 'equal', 'test', 'hosts', 'cut'))]
    for e in extra:
        ev[e['stage']] += 1
    tl = Counter()
    for y, c in T.items():
        for sg, v in c.items():
            tl[sg] += v
    assert dict(tl) == dict(ev), (dict(tl), dict(ev))
    crit_types = Counter()
    for e in abst:
        if e['crit'] and e['rel'] in ('criterion', 'member', 'aggregate', 'cut') and e['origin'] != 'closure':
            for c in e['crit'].split('+'):
                crit_types[c] += 1
    firsts = {}
    for e in sorted([e for e in abst if e['year'] is not None], key=lambda e: e['year']):
        key = e['rule'] or e['rel']
        firsts.setdefault(key, dict(year=e['year'], edge=e['id'], src=e['src'], dst=e['dst']))
        if e['rel'] in MEMBER_REL and any(tier(s) == 'C' for s in e['src']) and tier(e['dst']) == 'A':
            firsts.setdefault('first C→A membership', dict(year=e['year'], edge=e['id'], src=e['src'], dst=e['dst']))
        if e['status'] == 'observed':
            firsts.setdefault('first observed membership', dict(year=e['year'], edge=e['id'], src=e['src'], dst=e['dst']))

    dated = [n for n in nodes.values() if n['year'] is not None]
    numbers = dict(
        generated=datetime.date.today().isoformat(),
        nodes=len(nodes), routes=len(routes), abst=len(abst),
        nodes_by_branch=dict(Counter(n['branch'] for n in nodes.values())),
        routes_by_branch=dict(Counter(r['branch'] for r in routes)),
        nodes_by_tier_layer={t + '.' + l: v for (t, l), v in Counter((n['tier'], n['layer']) for n in nodes.values()).items()},
        nodes_dated=len(dated), routes_dated=sum(1 for r in routes if r['year'] is not None),
        abst_by_rel=dict(Counter(e['rel'] for e in abst)),
        abst_by_origin=dict(Counter(e['origin'] for e in abst)),
        abst_by_rule=dict(Counter(str(e['rule']) for e in abst)),
        abst_stated=sum(1 for e in abst if e['origin'] != 'closure'),
        abst_restating_route=len(by_route),
        closure=dict(stated=sum(1 for f in facts.values() if f['stated']),
                     derived=sum(1 for f in facts.values() if not f['stated']),
                     derived_in=sum(1 for f in facts.values() if not f['stated'] and f['val']),
                     derived_out=sum(1 for f in facts.values() if not f['stated'] and not f['val']),
                     conflicts=len(conflicts), atoms=len({k[0] for k in facts}),
                     inclusions=len(INCLUSIONS), disjoint=len(DISJOINT)),
        classes=len(classes), classes_three_leg=sum(1 for c in classes if c['three_leg']),
        classes_no_criterion=[c['id'] for c in classes if not c['legs']['criterion']],
        classes_no_test=[c['id'] for c in classes if not c['has_test']],
        classes_no_member=[c['id'] for c in classes if not c['has_member']],
        abst_undated=sum(1 for e in abst if e['year'] is None),
        classes_with_C_member=sum(1 for c in classes if c['legs']['stated_C'] + c['legs']['derived_C'] > 0),
        classes_with_stated_member=sum(1 for c in classes if c['legs']['stated'] + c['legs']['via_reify'] > 0),
        classes_with_stated_C_member=sum(1 for c in classes if c['legs']['stated_C'] > 0),
        effects=len(effects), effects_with_reference=sum(1 for x in effects if x['reference']),
        effects_with_test=sum(1 for x in effects if x['test']),
        effects_with_member=sum(1 for x in effects if x['members']),
        effects_three_leg=sum(1 for x in effects if x['three_leg']),
        census=dict(atoms=len(atoms), classes=len(classes), applicable=census['applicable'], known=census['known'],
                    stated=census['stated'], derived=census['derived'], cut=census['cut']),
        flow={'%s→%s %s' % k: v for k, v in sorted(flow.items())},
        flow_pairs={'%s→%s %s' % k: v for k, v in sorted(flow_pairs.items())},
        flow_branch={'%s→%s' % k: v for k, v in sorted(flow_branch.items())},
        carrier_inclusions=carrier,
        events=dict(sorted(ev.items())), events_extra_abst=len(extra),
        events_total=sum(ev.values()), events8=dict(ev8), events8_total=sum(ev8.values()),
        crit_types=dict(crit_types), firsts=firsts,
        kernel=dict(objects=len(ctx['objects']), attrs=len(ctx['attrs']),
                    stabilizer_states=ctx['n_stabilizer_states'],
                    rounds=[dict(round=r['round'], n_objects=r['n_objects'],
                                 levels=[dict(level=l['level'], counts=l['counts'],
                                              contradictions=len(l['contradictions']),
                                              candidates=[c['a'] + '⇒' + c['b'] for c in l['candidates']])
                                         for l in r['levels']],
                                 strict=len(r['strict']), strict_witnessed=sum(1 for s in r['strict'] if s['witnessed']),
                                 strict_import_only=sum(1 for s in r['strict'] if s['only_by_import']))
                            for r in ctx['rounds']],
                    crosscheck=dict(facts=check['facts'], compared=check['compared'], agree=check['agree'], unknown=check['unknown'],
                                    disagree=len(check['disagree']))),
    )

    full = dict(
        schema='gen-two-tier/1', title='Grand epistemic network across two tiers: clustering as an epistemic operation',
        generated=numbers['generated'],
        sources=dict(grand='data/gen_grand_network.json (Part I, 2026-11-13)',
                     evolution='data/gen_evolution_network.json (Part II, 2026-11-14)',
                     repos={'GEN_epistemic_evolution': '17bde64', 'GEN_LocGlob_Flow': '42751ee', 'GEN_Learning': 'c6e2fa4',
                            'GEN_HEP': '4258f6e', 'GEN_GPT_Level': 'e18fa8c', 'GEN_QRT_Level': '198ca02'}),
        branches=[dict(id=b, title=t, tier=('C' if b in LOW else 'A' if b in HIGH else 'C/A'),
                       dated=b not in ('UP', 'LG')) for b, t in BRANCH_TITLE.items()],
        phases=PHASES, stages=[dict(id=a, tier=b, phase=c, title=t, what=w, rules=r) for a, b, c, t, w, r in STAGES],
        operations=[dict(id=a, sig=b, counts=c, text=t) for a, b, c, t in OPERATIONS],
        rules=[dict(id=a, name=b, tier=c, layer=l, origin=o, text=t) for a, b, c, l, o, t in RULES],
        nodes=list(nodes.values()), routes=routes, abst=abst, classes=classes, effects=effects, census=census,
        conflicts=[dict(fact=list(k), a=a, b=b) for k, a, b in conflicts],
        inclusions=[dict(sub=a, sup=b, source=s, frame_tag=t, frame=f) for a, b, s, t, f in INCLUSIONS],
        disjoint=[dict(a=a, b=b, source=s, note=n) for a, b, s, n in DISJOINT],
        atom_domains={k: sorted(v) for k, v in ATOM_DOMAINS.items()},
        atom_frames={k: sorted(v) for k, v in ATOM_FRAMES.items()},
        timeline=T, context=ctx, numbers=numbers)
    page = export(full)                # also sets full['proposals'] and full['detail_counts']
    notes = write_notes(full)
    json.dump(full, open(os.path.join(DATA, 'gen_two_tier_network.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(numbers, open(os.path.join(OUT, 'two_tier_numbers.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(ctx, open(os.path.join(OUT, 'two_tier_context.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    full['page'], full['notes'] = page, notes
    return full


if __name__ == '__main__':
    full = main()
    N = full['numbers']
    for k in ('nodes', 'routes', 'abst', 'abst_stated', 'abst_restating_route', 'nodes_by_branch', 'abst_by_rel',
              'abst_by_origin', 'abst_by_rule', 'closure', 'classes', 'classes_three_leg', 'classes_no_criterion',
              'classes_no_test', 'classes_no_member', 'classes_with_C_member', 'classes_with_stated_C_member',
              'classes_with_stated_member', 'abst_undated',
              'effects', 'effects_with_reference', 'effects_with_member', 'effects_three_leg', 'census', 'flow',
              'flow_branch', 'carrier_inclusions', 'events', 'events_total', 'events8', 'events8_total',
              'crit_types', 'firsts'):
        print(k, '=', json.dumps(N[k], ensure_ascii=False))
    print('kernel', json.dumps(N['kernel'], ensure_ascii=False))
    for dd in full['context']['crosscheck']['disagree']:
        print('DISAGREE', dd)
    print('page', json.dumps(full['page']))
    print('notes', full['notes'])
