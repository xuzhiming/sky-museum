"""Headless Chrome smoke + walk test of web/preview.html: loads, no console errors, BVH collision, L1 walk plaza->entrance->lobby->atrium
-> escalator to L2, stair climb L3->L4 in valley core S0, negative test (atrium balustrade blocks), teleports."""
import json, math, time, sys, os
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
SH = ROOT + 'renders/walk/'; os.makedirs(SH, exist_ok=True)
S = json.load(open(ROOT + 'circulation_spec.json'))
log, errors = [], []
def L(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); log.append(s)
res = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', headless=True,
                          args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_page(viewport={'width': 960, 'height': 540})
    pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    pg.on('pageerror', lambda e: errors.append('PAGEERROR ' + str(e)))
    t0 = time.time()
    pg.goto('file://' + ROOT + 'web/preview.html')
    pg.wait_for_function('window.__ready === true && window.__collisionReady === true', timeout=240000)
    st = lambda: pg.evaluate('window.__walk.state()')
    L('loaded in', round(time.time() - t0, 1), 's; bvh', st()['bvh'], 'collision tris', st()['tris'])
    time.sleep(2); pg.screenshot(path=SH + '00_orbit_hero.png')
    pg.keyboard.press('KeyF'); time.sleep(1.0)
    assert st()['on']
    def steer(target, tol=0.5, run=False, timeout=60):
        t1 = time.time(); last = None; lastmove = time.time(); ok = False
        pg.keyboard.down('KeyW')
        if run: pg.keyboard.down('ShiftLeft')
        while time.time() - t1 < timeout:
            s = st(); dx, dy = target[0] - s['x'], target[1] - s['y']
            if math.hypot(dx, dy) < tol: ok = True; break
            pg.evaluate(f'window.__walk.setLook({math.atan2(-dx, dy)}, 0)')
            if last is None or math.hypot(s['x'] - last[0], s['y'] - last[1]) > 0.15: last = (s['x'], s['y']); lastmove = time.time()
            elif time.time() - lastmove > 5: break
            time.sleep(0.04)
        pg.keyboard.up('KeyW')
        if run: pg.keyboard.up('ShiftLeft')
        return ok, st()
    def route(name, pts, shots=()):
        for i, q in enumerate(pts):
            ok, s = steer(q[:2], q[2] if len(q) > 2 else 0.6, run=(len(q) > 3 and q[3]))
            if not ok:
                L(name, 'STUCK at wp', i, q, '->', round(s['x'], 2), round(s['y'], 2), round(s['z'], 2)); pg.screenshot(path=SH + name + '_stuck.png'); return False, s
            if i in shots: pg.screenshot(path=SH + '%s_wp%02d.png' % (name, i))
        return True, st()
    # ---- 1. L1: plaza -> entrance door -> lobby -> atrium -> escalator -> L2
    pg.evaluate('window.__walk.teleport("plaza")'); time.sleep(0.8)
    pg.screenshot(path=SH + '01_plaza.png')
    ok, s = route('L1', [(0, -186, 0.8, True), (0, -170, 0.6), (0, -120, 0.8, True), (0, -50, 0.8, True), (0, -25, 0.8), (25, -12, 0.7), (32, -5.4, 0.4), (32, 23.4, 0.4), (32, 27.5, 0.6), (30, 32, 0.6)], shots=(1, 2, 4, 6, 7))
    L('L1 route ok', ok, 'final', round(s['x'], 2), round(s['y'], 2), 'z', round(s['z'], 2), s['floor'])
    res['L1_to_L2'] = dict(ok=ok and abs(s['z'] - 16.0) < 0.3, z=s['z'])
    pg.evaluate('window.__walk.setLook(2.4, -0.25)'); time.sleep(0.5); pg.screenshot(path=SH + '02_L2_atrium_view.png')
    # ---- 2. negative: L3 corridor -> walk into the atrium balustrade
    pg.evaluate('window.__walk.setPos(0, 44, 26)'); time.sleep(0.6)
    ok, s = steer((0, 30), 0.5, timeout=8)
    res['balustrade_blocks'] = dict(ok=(not ok) and s['y'] > 39.5 and abs(s['z'] - 26) < 0.3, y=s['y'], z=s['z'])
    L('NEG balustrade: stopped at y', round(s['y'], 2), 'z', round(s['z'], 2), '->', res['balustrade_blocks']['ok'])
    pg.screenshot(path=SH + '03_L3_balustrade_block.png')
    # ---- 3. stair climb L3 -> L4 in valley core S0
    rec = [r for r in S['stairs'] if r['id'] == 'S0'][0]
    fl = [f for f in rec['flights'] if f['band'] == 2]
    c = math.cos(-math.pi / 2 + math.pi / 8); sn = math.sin(-math.pi / 2 + math.pi / 8)
    F = lambda u, v: (47 * c + u * c - v * sn, 47 * sn + u * sn + v * c)
    z3 = fl[0]['z0']
    pg.evaluate('window.__walk.setPos(%f, %f, %f)' % (*F(-3.0, 0), z3)); time.sleep(0.6)
    pts = [(*F(1.5, 0), 0.4), (*F(1.5, -5.0), 0.35), (*F(3.4, -5.85), 0.35)]
    for f in fl: pts += [(f['start'][0], f['start'][1], 0.3), (f['end'][0], f['end'][1], 0.3)]
    pts += [(*F(3.4, -4.1), 0.35), (*F(1.2, -4.6), 0.4), (*F(1.5, 0), 0.4), (*F(-2.5, 0), 0.5)]
    ok, s = route('S0', pts, shots=(4, 8))
    res['stair_L3_L4'] = dict(ok=ok and abs(s['z'] - fl[-1]['z0'] - fl[-1]['n'] * fl[-1]['riser']) < 0.3, z=s['z'], expect=fl[-1]['z0'] + fl[-1]['n'] * fl[-1]['riser'])
    L('stair route ok', ok, 'z', round(s['z'], 2), 'expect', round(res['stair_L3_L4']['expect'], 2), s['floor'])
    pg.screenshot(path=SH + '04_L4_after_stairs.png')
    # ---- 4. teleports
    for i, n in enumerate(['lobby', 'atrium', 'L12', 'L21', 'L28', 'L30']):
        pg.evaluate('window.__walk.teleport("%s")' % n); t1 = time.time()
        while time.time() - t1 < 8 and not st()['grounded']: time.sleep(0.2)
        time.sleep(0.5); s = st()
        res['tp_' + n] = dict(ok=s['grounded'], z=round(s['z'], 2), floor=s['floor'])
        L('teleport', n, round(s['x'], 1), round(s['y'], 1), round(s['z'], 2), s['floor'], 'grounded', s['grounded'])
        pg.screenshot(path=SH + '05_tp_%s.png' % n)
    pg.keyboard.press('KeyF'); time.sleep(0.5)
    pg.evaluate('window.__setCut("sec")'); pg.evaluate('window.__goTo("hero")'); time.sleep(2.0); pg.screenshot(path=SH + '06_orbit_section.png')
    res['console_errors'] = errors
    L('console errors:', errors)
    json.dump(dict(results=res, log=log), open(SH + 'walk_test.json', 'w'), indent=1)
    b.close()
allok = all(v['ok'] for k, v in res.items() if isinstance(v, dict)) and not errors
L('ALL PASS' if allok else 'SOME FAILED', {k: v['ok'] for k, v in res.items() if isinstance(v, dict)})
