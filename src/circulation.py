"""Circulation check: spaces/doors/stairs/lifts graph reachable from the plaza, physical probes against the built mesh (BVH),
and a stair / escalator geometry audit. Writes circulation_report.{json,md}."""
import sys, os, json, math
from collections import defaultdict, deque
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
COLL = ['Podium', 'Portal', 'Hood', 'Entrance_Glass', 'Shell_Glass', 'Slabs', 'Slabs_Glass', 'Walls', 'Cores', 'Stairs', 'Escalators', 'Rails',
        'Bridges', 'Obs_Decks', 'Pods', 'Fans', 'Atrium_Roof', 'Ground', 'Core_Glass', 'Exhibits', 'Spire']
RULES = dict(stair=dict(rmin=0.15, rmax=0.18, tmin=0.28, wmin=1.4, nmax=18, head=2.1), escalator=dict(rmin=0.15, rmax=0.21, tmin=0.30, wmin=1.0, nmax=200, head=2.3))

def bvh():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'model.blend'))
    bm = bmesh.new()
    for n in COLL:
        ob = bpy.data.objects.get(n)
        if ob: bm.from_mesh(ob.data)
    return BVHTree.FromBMesh(bm)

def main():
    S = json.load(open(os.path.join(ROOT, 'circulation_spec.json')))
    T = bvh()
    def ray(o, d, dist):
        loc, nrm, idx, dd = T.ray_cast(Vector(o), Vector(d).normalized(), dist)
        return dd
    def floor_at(p, tol=0.2):
        d = ray((p[0], p[1], p[2] + 1.0), (0, 0, -1), 1.6)
        return d is not None and abs((p[2] + 1.0 - d) - p[2]) <= tol
    def clear(a, b, z):
        L = math.dist(a, b)
        for h in (0.4, 1.2, 2.0):
            o = (a[0], a[1], z + h); dv = (b[0] - a[0], b[1] - a[1], 0)
            if ray(o, dv, L) is not None: return False
        return True
    res_probe = []
    def check(pr):
        if pr['t'] == 'floor': return floor_at(pr['p'])
        return clear(pr['a'], pr['b'], pr['z'])
    # ---- stair / escalator audit
    audit = []
    flight_ok = {}
    for kind, recs in (('stair', S['stairs']), ('escalator', S['escalators'])):
        R = RULES[kind]
        for rec in recs:
            fls = rec['flights'] if kind == 'stair' else [dict(band=0, f=0, n=rec['n'], riser=rec['riser'], tread=rec['tread'], width=rec['width'], steps=rec['steps'], z0=rec['steps'][0][4] - rec['riser'])]
            for f in fls:
                issues = []
                if not (R['rmin'] - 1e-6 <= f['riser'] <= R['rmax'] + 1e-6): issues.append('riser %.3f' % f['riser'])
                if f['tread'] < R['tmin'] - 1e-6: issues.append('tread %.3f' % f['tread'])
                if f['width'] < R['wmin'] - 1e-6: issues.append('width %.2f' % f['width'])
                if f['n'] > R['nmax']: issues.append('risers/flight %d' % f['n'])
                if kind == 'stair' and not (0.55 <= 2 * f['riser'] + f['tread'] <= 0.70): issues.append('2R+T %.3f' % (2 * f['riser'] + f['tread']))
                minhead, bad_surf = 99.0, 0
                for st in f['steps']:
                    cx = sum(p[0] for p in st[:4]) / 4; cy = sum(p[1] for p in st[:4]) / 4; zt = st[4]
                    d = ray((cx, cy, zt + 0.02), (0, 0, 1), 10.0)
                    minhead = min(minhead, d if d is not None else 99.0)
                    dd = ray((cx, cy, zt + 0.3), (0, 0, -1), 0.5)
                    if dd is None or abs(dd - 0.3) > 0.03: bad_surf += 1
                if minhead < R['head']: issues.append('headroom %.2f' % minhead)
                if bad_surf: issues.append('%d steps without tread surface' % bad_surf)
                key = (rec['id'], f['band'])
                flight_ok[key] = flight_ok.get(key, True) and not issues
                audit.append(dict(id=rec['id'], kind=kind, band=f['band'], flight=f['f'], n=f['n'], riser=round(f['riser'], 4), tread=f['tread'], width=f['width'], headroom=round(minhead, 2), issues=issues))
    # ---- graph
    adj = defaultdict(list); link_res = []
    for L in S['links']:
        ok = all(check(p) for p in L['probes'])
        if L['kind'] == 'stair': ok = ok and flight_ok.get((L['ref'], L['band']), False)
        if L['kind'] == 'escalator': ok = ok and flight_ok.get((L['ref'], 0), False)
        link_res.append(dict(a=L['a'], b=L['b'], kind=L['kind'], ok=ok, failed=[p for p in L['probes'] if not check(p)]))
        if ok: adj[L['a']].append(L['b']); adj[L['b']].append(L['a'])
    for lf in S['lifts']:
        st = [s for s in lf['stops'] if s in S['spaces']]
        for a, b in zip(st, st[1:]): adj[a].append(b); adj[b].append(a)
    # bridge HS doors are lift stops of the central core too
    hs_doors = [s for s in S['spaces'] if s.startswith('HS_door_')]
    for s in hs_doors: adj[s].append('L1_lobby'); adj['L1_lobby'].append(s)
    space_floor_ok = {sid: floor_at(sp['pt']) for sid, sp in S['spaces'].items()}
    seen = {'plaza'}; q = deque(['plaza'])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in seen: seen.add(v); q.append(v)
    unreachable = sorted(set(S['spaces']) - seen)
    by_floor = defaultdict(lambda: [0, 0])
    for sid, sp in S['spaces'].items():
        by_floor[sp['floor']][1] += 1
        if sid in seen: by_floor[sp['floor']][0] += 1
    # walking-only reachability (no lifts): stairs + escalators + doors
    adj2 = defaultdict(list)
    for L in link_res:
        if L['ok']: adj2[L['a']].append(L['b']); adj2[L['b']].append(L['a'])
    seen2 = {'plaza'}; q = deque(['plaza'])
    while q:
        u = q.popleft()
        for v in adj2[u]:
            if v not in seen2: seen2.add(v); q.append(v)
    # negative probes: facade / walls must block
    neg = []
    for name, a, b, z in [('L8 arm0 -> outside through glass', (0, -100), (0, -130), 130.5), ('L1 lobby -> outside through podium (arm2 side)', (120, 10), (200, 10), 0.0),
                          ('L5 corridor -> arm hall through ring wall', (math.cos(0.3) * 44, math.sin(0.3) * 44), (math.cos(0.3) * 52, math.sin(0.3) * 52), 81.0),
                          ('L3 corridor -> atrium void (balustrade)', (0, 43), (0, 36), 48.0), ('L20 hall -> outside through glass', (0, 0), (0, -70), 306.0)]:
        neg.append(dict(name=name, blocked=not clear(a, b, z)))
    rep = dict(spaces=len(S['spaces']), reachable=len(seen), reachable_walking=len(seen2), unreachable=unreachable,
               unreachable_walking=sorted(set(S['spaces']) - seen2)[:60], n_unreachable_walking=len(set(S['spaces']) - seen2),
               links=len(link_res), links_ok=sum(l['ok'] for l in link_res), failed_links=[l for l in link_res if not l['ok']][:40],
               spaces_without_floor=[s for s, ok in space_floor_ok.items() if not ok],
               by_floor={k: v for k, v in sorted(by_floor.items(), key=lambda kv: int(kv[0][1:]))},
               lifts=[dict(id=l['id'], kind=l['kind'], stops=len(l['stops'])) for l in S['lifts']],
               flights=len(audit), flights_ok=sum(not a['issues'] for a in audit), flight_issues=[a for a in audit if a['issues']][:40],
               min_headroom_stairs=min(a['headroom'] for a in audit if a['kind'] == 'stair'), min_headroom_esc=min(a['headroom'] for a in audit if a['kind'] == 'escalator'),
               negative_probes=neg)
    json.dump(rep, open(os.path.join(ROOT, 'circulation_report.json'), 'w'), indent=1)
    md = ['# Circulation report', '',
          f"* spaces {rep['spaces']}, reachable from plaza {rep['reachable']} (walking only, no lifts: {rep['reachable_walking']})",
          f"* links {rep['links']}, physically open (all probes pass) {rep['links_ok']}",
          f"* stair/escalator flights audited {rep['flights']}, passing {rep['flights_ok']}; min headroom stairs {rep['min_headroom_stairs']} m, escalators {rep['min_headroom_esc']} m",
          f"* lifts: " + ', '.join('%s(%s, %d stops)' % (l['id'], l['kind'], l['stops']) for l in rep['lifts']),
          f"* negative probes (must be blocked): " + ', '.join('%s=%s' % (n['name'], 'blocked' if n['blocked'] else 'OPEN!') for n in neg),
          f"* spaces without floor under their reference point: {rep['spaces_without_floor'] or 'none'}",
          f"* unreachable: {unreachable or 'none'}", '', '| floor | reachable / spaces |', '|---|---|'] + \
         ['| %s | %d / %d |' % (k, v[0], v[1]) for k, v in rep['by_floor'].items()]
    if rep['failed_links']: md += ['', '## failed links'] + ['* %s -> %s (%s): %s' % (l['a'], l['b'], l['kind'], l['failed']) for l in rep['failed_links']]
    if rep['flight_issues']: md += ['', '## flight issues'] + ['* %s band %d flight %d: %s' % (a['id'], a['band'], a['flight'], a['issues']) for a in rep['flight_issues']]
    open(os.path.join(ROOT, 'circulation_report.md'), 'w').write('\n'.join(md) + '\n')
    print('\n'.join(md[:12]))
    if rep['failed_links']: print('failed', [(l['a'], l['b']) for l in rep['failed_links']][:20])
    if rep['flight_issues']: print('issues', rep['flight_issues'][:5])

if __name__ == '__main__':
    main()
