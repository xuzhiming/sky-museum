"""Interior: floor slabs with the Ø80 atrium void, ring corridors, radial arm galleries, valley cores (stairs + lifts),
atrium glass lifts L1<->L11, leaning central glass core L11-L30 (high-speed lifts), atrium escalators L1-L5, golden ring, tower floors.
Also records a circulation spec (spaces / links / probes / stair flights) -> SPEC."""
import math, numpy as np
import params as P
from shapes import arc_ribbon, slab, wall, wall_open, arc_wall, arc_band, arc_pts, torus, circle, local_rect, Polygon
from shapely.geometry import box as sbox
from shapely.ops import unary_union

SPEC = dict(spaces={}, links=[], flights=[], stairs=[], lifts=[], escalators=[])
FL = P.floors()
FLD = {n: (z, h, p) for n, z, h, p in FL}
GAL = [f for f in FL if f[1] < P.ATRIUM_TOP]   # L1..L10 (atrium floors with valley cores)
UPF = [f for f in FL if f[1] >= P.ATRIUM_TOP]  # L11..L30 (tower floors around the central core)
STAIR_ARMS = (2, 6)                             # upper stairs run along the E / W arms
HS_ARMS = (0, 4)                                # central-core lift doors S / N
ATR_LIFT_ARMS = (1, 3, 5, 7)                    # atrium glass lifts L1 <-> L11 on the diagonals
def cc(z): return (0.0, P.yc(z))                # tower / core centre at height z (lean)
RW = P.RING_WALL_R

def frame(ang, r0=0.0):
    c, s = math.cos(ang), math.sin(ang)
    O = (r0 * c, r0 * s)
    return lambda u, v: (O[0] + u * c - v * s, O[1] + u * s + v * c)

def lbox(acc, g, m, F, u0, u1, v0, v1, z0, z1):
    q = [F(u0, v0), F(u1, v0), F(u0, v1), F(u1, v1)]
    c = [(*q[0], z0), (*q[1], z0), (*q[2], z0), (*q[3], z0), (*q[0], z1), (*q[1], z1), (*q[2], z1), (*q[3], z1)]
    acc.hexa(g, m, c)

def lpoly(F, u0, u1, v0, v1):
    return Polygon([F(u0, v0), F(u1, v0), F(u1, v1), F(u0, v1)])

def space(sid, kind, floor, pt, **kw):
    SPEC['spaces'][sid] = dict(id=sid, kind=kind, floor=floor, pt=[round(float(c), 3) for c in pt], **kw)

def link(a, b, kind, probes=None, **kw):
    SPEC['links'].append(dict(a=a, b=b, kind=kind, probes=probes or [], **kw))

# ---------------------------------------------------------------- stairs
def stair_plan(h, rmax=0.18, mmax=18):
    F = 2
    while math.ceil(h / (F * rmax) - 1e-9) > mmax: F += 2
    m = int(math.ceil(h / (F * rmax) - 1e-9))
    return F, m, h / (F * m)

class StairShaft:
    """enclosed switch-back stair in a local frame. lanes A/B (v ranges), near landing [u0, un], flights run +u (A) / -u (B)."""
    def __init__(self, sid, F, u0, laneA, laneB, bands, wall_v=None):
        self.sid, self.F, self.u0, self.A, self.B, self.bands = sid, F, u0, laneA, laneB, bands
        self.T = P.STAIR['tread']; self.un = u0 + P.STAIR['landing'] + 0.2
        self.plans = [stair_plan(h) for (z, h) in bands]
        self.uf_max = max(self.un + (m - 1) * self.T for (_, m, _) in self.plans)
        self.ue = self.uf_max + P.STAIR['landing'] + 0.2
        self.vlo = min(laneA[0], laneB[0]) - 0.15; self.vhi = max(laneA[1], laneB[1]) + 0.15
        self.wall_v = wall_v
    def hole(self):
        return lpoly(self.F, self.un, self.ue, self.vlo, self.vhi)
    def build(self, acc):
        F, T = self.F, self.T
        rec = dict(id=self.sid, flights=[], landings=[])
        for bi, ((z0, h), (nf, m, r)) in enumerate(zip(self.bands, self.plans)):
            uf = self.un + (m - 1) * T
            z = z0
            for f in range(nf):
                lane = self.A if f % 2 == 0 else self.B
                fwd = f % 2 == 0
                steps = []
                for i in range(1, m):
                    ua = self.un + (i - 1) * T if fwd else uf - i * T
                    ub = ua + T
                    zt = z + i * r
                    lbox(acc, 'Stairs', 'stair', F, ua, ub, lane[0], lane[1], zt - 0.45, zt)
                    acc.add_face('Lights_Amber', 'strip_amber', [(*F(ua + 0.02, lane[0] + 0.05), zt - r * 0.5), (*F(ua + 0.02, lane[1] - 0.05), zt - r * 0.5), (*F(ua + 0.02, lane[1] - 0.05), zt - r * 0.5 + 0.03), (*F(ua + 0.02, lane[0] + 0.05), zt - r * 0.5 + 0.03)]) if (i % 6 == 0) else None
                    steps.append([[round(c, 3) for c in F(ua, lane[0])], [round(c, 3) for c in F(ub, lane[0])], [round(c, 3) for c in F(ub, lane[1])], [round(c, 3) for c in F(ua, lane[1])], round(zt, 4)])
                rec['flights'].append(dict(band=bi, f=f, z0=round(z, 4), n=m, riser=r, tread=T, width=lane[1] - lane[0], steps=steps,
                                           start=[*F(self.un - 0.5 if fwd else uf + 0.5, (lane[0] + lane[1]) / 2), z],
                                           end=[*F(uf + 0.6 if fwd else self.un - 0.6, (lane[0] + lane[1]) / 2), z + m * r]))
                z += m * r
                # landing after flight
                last = (bi == len(self.bands) - 1 and f == nf - 1)
                if fwd:   # far landing
                    lbox(acc, 'Stairs', 'stair', F, uf, self.ue, self.vlo + 0.15, self.vhi - 0.15, z - 0.3, z)
                    rec['landings'].append(dict(z=round(z, 4), kind='far', rect=[uf, self.ue]))
                elif f != nf - 1:   # intermediate near landing (floor-level ones are the slab)
                    lbox(acc, 'Stairs', 'stair', F, self.u0, self.un, self.vlo + 0.15, self.vhi - 0.15, z - 0.3, z)
                    rec['landings'].append(dict(z=round(z, 4), kind='near_mid', rect=[self.u0, self.un]))
                else:
                    rec['landings'].append(dict(z=round(z, 4), kind='floor', rect=[self.u0, self.un]))
            # enclosure walls for this band
            zt = z0 + h - P.SLAB_T
            vm = (self.A[1] + self.B[0]) / 2 if self.A[1] < self.B[0] else (self.B[1] + self.A[0]) / 2
            wall(acc, 'Walls', 'wall_dark', F(self.un, vm), F(uf, vm), z0, zt + P.SLAB_T, 0.2)        # centre divider
            # front wall with floor-level door
            dv0, dv1 = self.vlo + 0.4, self.vhi - 0.4
            wall_open(acc, 'Walls', 'wall_dark', F(self.u0, self.vlo), F(self.u0, self.vhi), z0, zt, [(dv0 - self.vlo, dv1 - self.vlo, 3.0)], 0.3)
            wall(acc, 'Walls', 'wall_dark', F(self.ue + 0.15, self.vlo), F(self.ue + 0.15, self.vhi), z0, zt + P.SLAB_T, 0.3)
            for vv in (self.vlo, self.vhi):
                if self.wall_v is not None and abs(vv - self.wall_v) < 0.5: continue
                wall(acc, 'Walls', 'wall_dark', F(self.u0, vv), F(self.ue + 0.15, vv), z0, zt + P.SLAB_T, 0.3)
            # shaft light
            for zz in np.arange(z0 + 2.9, z0 + h, 5.0):
                lbox(acc, 'Lights_Amber', 'light_panel', F, self.un + 0.5, self.un + 2.5, self.vhi - 0.12, self.vhi - 0.05, zz, zz + 0.25)
        SPEC['stairs'].append(rec)
        return rec
    def top_rails(self, acc, ztop):
        F = self.F
        for (a, b) in (((self.un, self.vlo), (self.ue, self.vlo)), ((self.un, self.vhi), (self.ue, self.vhi)), ((self.ue, self.vlo), (self.ue, self.vhi))):
            wall(acc, 'Rails', 'rail_metal', F(*a), F(*b), ztop, ztop + 1.1, 0.12)
        # lane-A end at the near side (lane B is where the last flight arrives)
        wall(acc, 'Rails', 'rail_metal', F(self.un, self.A[0] - 0.15), F(self.un, self.A[1] + 0.05), ztop, ztop + 1.1, 0.12)

# ---------------------------------------------------------------- valley cores
CORE_U1, CORE_W = 19.0, 7.0
def core_frame(k): return frame(P.valley_angle(k), RW)
STAIR_CORES = [0, 2, 4, 6]
def core_lifts(k): return [(12.0, 16.0)] if k in STAIR_CORES else [(5.0, 9.0), (12.0, 16.0)]

def valley_stairs():
    out = {}
    bands = [(z, h) for n, z, h, p in GAL]
    for k in STAIR_CORES:
        out[k] = StairShaft('S%d' % k, core_frame(k), 2.5, (-6.7, -5.1), (-4.9, -3.3), bands, wall_v=-6.85)
    return out

def upper_stairs():
    """L11 -> L30: one shaft per floor band, frame origin on the (leaning) tower axis, running out along the E/W arms"""
    out = {k: [] for k in STAIR_ARMS}
    for i, (n, z, h, p) in enumerate(UPF[:-1]):
        c = (0.0, UP_STACK_Y[0] if z < 320.0 else UP_STACK_Y[1])   # two vertical stacks (L11-L20, L21-L29) following the lean
        for k in STAIR_ARMS:
            a = P.arm_angle(k); ca, sa = math.cos(a), math.sin(a)
            F = lambda u, v, c=c, ca=ca, sa=sa: (c[0] + u * ca - v * sa, c[1] + u * sa + v * ca)
            out[k].append(StairShaft('SU%d_%s' % (k, n), F, UP_U0, (-1.7, -0.1), (0.1, 1.7), [(z, h)]))
    return out
UP_U0 = P.CORE_R + 2.5
UP_STACK_Y = (round(P.yc(250.0), 1), round(P.yc(370.0), 1))

# ---------------------------------------------------------------- escalators
ESC_SPEC = [('L1', 'L2', 0.0, 30.0), ('L2', 'L3', 90.0, 30.0), ('L3', 'L4', 180.0, 34.0), ('L4', 'L5', 270.0, 34.0)]
def esc_geom(lo, hi, phi, d):
    z0 = FLD[lo][0]; z1 = FLD[hi][0]
    n = np.array([math.cos(math.radians(phi)), math.sin(math.radians(phi))]); tau = np.array([-n[1], n[0]])
    rise = z1 - z0; N = int(round(rise / P.ESC['riser'])); r = rise / N; T = P.ESC['tread']; run = (N - 1) * T
    te = math.sqrt(P.ATRIUM_R ** 2 - d ** 2)
    if lo == 'L1': t1 = te; t0 = te - run
    else: t0 = -run / 2; t1 = run / 2
    return dict(z0=z0, z1=z1, n=n, tau=tau, d=d, N=N, r=r, T=T, t0=t0, t1=t1, te=te, first=lo == 'L1')

def build_escalators(acc):
    gaps = {}
    for lo, hi, phi, d in ESC_SPEC:
        E = esc_geom(lo, hi, phi, d)
        n, tau = E['n'], E['tau']; w = P.ESC['width'] / 2
        Fp = lambda t, s: tuple(n * d + tau * t + n * s)
        steps = []
        for i in range(1, E['N']):
            ta = E['t0'] + (i - 1) * E['T']; tb = ta + E['T']; zt = E['z0'] + i * E['r']
            q = [Fp(ta, -w), Fp(tb, -w), Fp(ta, w), Fp(tb, w)]
            acc.hexa('Escalators', 'esc_step', [(*q[0], zt - 0.5), (*q[1], zt - 0.5), (*q[2], zt - 0.5), (*q[3], zt - 0.5), (*q[0], zt), (*q[1], zt), (*q[2], zt), (*q[3], zt)])
            steps.append([[round(c, 3) for c in q[0]], [round(c, 3) for c in q[1]], [round(c, 3) for c in q[3]], [round(c, 3) for c in q[2]], round(zt, 4)])
        tf = E['t0'] + (E['N'] - 1) * E['T']
        # top landing (to slab edge + 1 m), bottom landing (upper escalators only)
        def deck(ta, tb, z):
            q = [Fp(ta, -w - 0.2), Fp(tb, -w - 0.2), Fp(ta, w + 0.2), Fp(tb, w + 0.2)]
            acc.hexa('Escalators', 'esc_deck', [(*q[0], z - 0.4), (*q[1], z - 0.4), (*q[2], z - 0.4), (*q[3], z - 0.4), (*q[0], z), (*q[1], z), (*q[2], z), (*q[3], z)])
        deck(tf, E['te'] + 1.0, E['z1'])
        if not E['first']: deck(-E['te'] - 1.0, E['t0'], E['z0'])
        # balustrades (glass + cyan handrail strip) along flight + landings
        tlo = E['t0'] if E['first'] else -E['te'] - 0.2
        for s in (-w - 0.15, w + 0.15):
            if not E['first']: wall(acc, 'Rails', 'rail_glass', Fp(-E['te'] + 0.6, s), Fp(E['t0'], s), E['z0'], E['z0'] + 1.1, 0.06)
            wall(acc, 'Rails', 'rail_glass', Fp(tf, s), Fp(E['te'] - 0.6, s), E['z1'], E['z1'] + 1.1, 0.06)
            for i in range(0, E['N'] - 1, 4):
                ta = E['t0'] + i * E['T']; tb = min(ta + 4 * E['T'], tf); za = E['z0'] + (i + 1) * E['r']; zb = E['z0'] + min(i + 4, E['N'] - 1) * E['r']
                pa, pb = Fp(ta, s), Fp(tb, s)
                acc.hexa('Rails', 'rail_glass', [(*pa, za - 0.4), (*pb, zb - 0.4), (*np.add(pa, n * 0.06 * np.sign(s)), za - 0.4), (*np.add(pb, n * 0.06 * np.sign(s)), zb - 0.4),
                                                 (*pa, za + 1.0), (*pb, zb + 1.0), (*np.add(pa, n * 0.06 * np.sign(s)), za + 1.0), (*np.add(pb, n * 0.06 * np.sign(s)), zb + 1.0)])
                acc.bar('Lights_Cyan', 'strip_cyan', (*pa, za + 1.05), (*pb, zb + 1.05), 0.12, 0.08)
        # stringer underside glow
        acc.bar('Lights_Amber', 'strip_amber', (*Fp(E['t0'], 0), E['z0'] - 0.55), (*Fp(tf, 0), E['z1'] - 0.55), 0.5, 0.1)
        # rail gaps (angles) at slab edge
        top_pt = Fp(E['te'], 0); gaps.setdefault(hi, []).append(math.atan2(top_pt[1], top_pt[0]))
        if not E['first']:
            bp = Fp(-E['te'], 0); gaps.setdefault(lo, []).append(math.atan2(bp[1], bp[0]))
        start = Fp(E['t0'] - 1.0 if E['first'] else -E['te'] + 1.5, 0); end = Fp(E['te'] + 1.5, 0)
        rec = dict(id='E_%s_%s' % (lo, hi), lo=lo, hi=hi, n=E['N'], riser=E['r'], tread=E['T'], width=P.ESC['width'], steps=steps,
                   start=[*start, E['z0']], end=[*end, E['z1']], path=[[*Fp(t, 0), E['z0'] + max(0, min(E['N'], (t - E['t0']) / E['T'] + 1)) * E['r']] for t in np.linspace(E['t0'] - 0.5, tf + 0.5, 12)])
        SPEC['escalators'].append(rec)
        ring_lo = '%s_lobby' % lo if lo == 'L1' else '%s_ring' % lo
        link(ring_lo, '%s_ring' % hi, 'escalator', probes=[dict(t='floor', p=rec['start']), dict(t='floor', p=rec['end'])], ref=rec['id'])
    return gaps

# ---------------------------------------------------------------- per-floor build
def floor_slab_geom(name, z, stairs, up):
    g = Polygon(P.star(z, inset=0.35))
    if z < P.ATRIUM_TOP:
        if name != 'L1':
            g = g.difference(circle(P.ATRIUM_R, 96))
            for k, S in stairs.items(): g = g.difference(S.hole())
        if name in ('L2', 'L3', 'L4', 'L5'):
            g = g.difference(sbox(-P.ENTRANCE_W / 2 - 6, -400, P.ENTRANCE_W / 2 + 6, -P.Ro(0) + P.ENTRANCE_RECESS + 0.5))
        return g
    if name == 'L11':
        for k, S in stairs.items(): g = g.difference(S.hole())
    g = g.difference(circle(P.CORE_R + 0.2, 40, *cc(z)))
    for k, lst in up.items():
        for S in lst:
            if abs(S.bands[0][0] + S.bands[0][1] - z) < 1e-3: g = g.difference(S.hole())
    return g

def build_interior(acc):
    stairs = valley_stairs(); up = upper_stairs()
    esc_gaps = build_escalators(acc)
    space('plaza', 'outdoor', 'L0', (0, -205, 0))
    link('plaza', 'L1_arm0', 'door', probes=[dict(t='clear', a=(0, -P.Ro(0) + P.ENTRANCE_RECESS - 2.0), b=(0, -P.Ro(0) + P.ENTRANCE_RECESS + 2.0), z=0.0),
                                              dict(t='floor', p=(0, -P.Ro(0) - 4, 0)), dict(t='floor', p=(0, -P.Ro(0) + P.ENTRANCE_RECESS + 4, 0))])
    for idx, (name, z, h, prog) in enumerate(FL):
        zc = z + h - P.SLAB_T
        # ---- slab
        g = floor_slab_geom(name, z, stairs, up)
        slab(acc, 'Slabs', 'floor_stone' if name == 'L1' else 'floor_dark', g, z - P.SLAB_T, z, edge_mat='titanium')
        if z >= P.ATRIUM_TOP: upper_floor(acc, name, z, h, prog, up); continue
        # ---- atrium edge
        if name != 'L1':
            gaps = [(a, 1.6) for a in esc_gaps.get(name, [])]
            ivs = rail_intervals(P.ATRIUM_R + 0.1, gaps)
            for a0, a1 in ivs:
                arc_wall(acc, 'Rails', 'rail_glass', P.ATRIUM_R + 0.15, a0, a1, z, z + 1.1, t=0.06, seg_len=3.0)
                arc_ribbon(acc, 'Lights_Cyan', 'strip_cyan', P.ATRIUM_R + 0.08, a0, a1, z + 1.04, z + 1.12, seg_len=3.0)
            arc_ribbon(acc, 'Lights_Cyan', 'strip_cyan', P.ATRIUM_R - 0.03, 0, 2 * math.pi, z - 0.45, z - 0.2, seg_len=3.0)
        # ---- ring corridor wall + arm doors
        core_half = math.atan2(CORE_W, RW)
        if name != 'L1':
            cuts = []
            for k in range(P.N_ARMS):
                cuts.append((P.arm_angle(k), (P.HALL_DOOR_W / 2) / RW))
                cuts.append((P.valley_angle(k), core_half))
            for a0, a1 in intervals_from_cuts(cuts):
                arc_wall(acc, 'Walls', 'wall_ring', RW, a0, a1, z, zc, t=0.3)
            # door lintels above arm doors
            for k in range(P.N_ARMS):
                a = P.arm_angle(k); hw = (P.HALL_DOOR_W / 2) / RW
                dh = min(6.0, h - 2.0)
                arc_wall(acc, 'Walls', 'wall_ring', RW, a - hw, a + hw, z + dh, zc, t=0.3, seg_len=2.0)
                arc_ribbon(acc, 'Lights_Cyan', 'strip_cyan', RW - 0.18, a - hw, a + hw, z + dh - 0.15, z + dh, seg_len=2.0)
        # ---- spaces + links
        ring = '%s_lobby' % name if name == 'L1' else '%s_ring' % name
        space(ring, 'lobby' if name == 'L1' else 'corridor', name, (0, -20, z) if name == 'L1' else (0, -(P.ATRIUM_R + 3.5), z))
        for k in range(P.N_ARMS):
            a = P.arm_angle(k); rm = (P.Ri(z) + P.Ro(z)) / 2
            sid = '%s_arm%d' % (name, k)
            space(sid, 'entrance_hall' if (name == 'L1' and k == 0) else ('hall' if name in ('L1', 'L2') else 'gallery'), name, (rm * math.cos(a) - 4.0 * math.sin(a), rm * math.sin(a) + 4.0 * math.cos(a), z), program=prog)
            ca, sa = math.cos(a), math.sin(a)
            link(ring, sid, 'open' if name == 'L1' else 'door',
                 probes=[dict(t='clear', a=((RW - 2) * ca, (RW - 2) * sa), b=((RW + 2) * ca, (RW + 2) * sa), z=z),
                         dict(t='floor', p=((RW + 4) * ca, (RW + 4) * sa, z)), dict(t='floor', p=((RW - 3) * ca, (RW - 3) * sa, z))])
        # ---- radial partitions between arms (valley lines)
        for k in range(P.N_ARMS):
            F = core_frame(k)
            r_end0 = P.Ri(z) - 0.4 - RW; r_end1 = P.Ri(zc) - 0.4 - RW
            p0, p1 = F(CORE_U1, 0), F(r_end0, 0); q1 = F(r_end1, 0)
            acc.hexa('Walls', 'wall_light', [(*F(CORE_U1, -0.15), z), (*F(r_end0, -0.15), z), (*F(CORE_U1, 0.15), z), (*F(r_end0, 0.15), z),
                                             (*F(CORE_U1, -0.15), zc), (*F(r_end1, -0.15), zc), (*F(CORE_U1, 0.15), zc), (*F(r_end1, 0.15), zc)])
        # ---- cores
        for k in range(P.N_ARMS):
            F = core_frame(k)
            cid = '%s_core%d' % (name, k)
            space(cid, 'core', name, (*F(8.0, 0.0), z))
            wall_open(acc, 'Walls', 'wall_core', F(0, -CORE_W), F(0, CORE_W), z, zc, [(CORE_W - 1.6, CORE_W + 1.6, 3.6)], 0.3)
            for vv in (-CORE_W, CORE_W):
                wall(acc, 'Walls', 'wall_core', F(-0.6, vv), F(CORE_U1, vv), z, zc + P.SLAB_T, 0.3)
            wall(acc, 'Walls', 'wall_core', F(CORE_U1, -CORE_W), F(CORE_U1, CORE_W), z, zc + P.SLAB_T, 0.3)
            lbox(acc, 'Lights_Amber', 'strip_cyan', F, -0.25, -0.15, -1.6, 1.6, z + 3.6, z + 3.8)
            lbox(acc, 'Lights_Amber', 'light_panel', F, 3.0, 17.0, -0.3, 0.3, zc - 0.08, zc - 0.02)
            link(ring, cid, 'door', probes=[dict(t='clear', a=F(-1.5, 0), b=F(1.5, 0), z=z), dict(t='floor', p=(*F(1.5, 0), z)), dict(t='floor', p=(*F(-1.5, 0), z))])
            # passenger lifts: closed shafts with door panels on the v=+3 face
            for (ua, ub) in core_lifts(k):
                lbox(acc, 'Cores', 'lift_shaft', F, ua, ub, 3.0, 6.7, z, z + h)
                lbox(acc, 'Lights_Cyan', 'door_lift', F, ua + 0.9, ub - 0.9, 2.95, 3.0, z + 0.05, z + 2.6)
            if k in STAIR_CORES:
                S = stairs[k]
                link(cid, '%s_stair%d' % (name, k), 'door', probes=[dict(t='clear', a=F(1.2, -5.0), b=F(3.8, -5.0), z=z), dict(t='floor', p=(*F(3.6, -5.0), z))])
                space('%s_stair%d' % (name, k), 'stair_landing', name, (*F(3.6, -5.0), z))
        # ---- ceiling lights + gallery fit-out
        arc_band(acc, 'Lights_Amber', 'light_panel', RW - 4.0, RW - 3.4, 0, 2 * math.pi, zc - 0.02, down=True)
        for k in range(P.N_ARMS):
            arm_fitout(acc, name, z, h, k)
    # valley stairs L1 -> L11 (geometry + vertical links)
    for k, S in stairs.items():
        S.build(acc); S.top_rails(acc, P.ATRIUM_TOP)
        for i, (n, z, h, p) in enumerate(GAL):
            nxt = FL[i + 1][0]
            dst = '%s_stair%d' % (nxt, k) if nxt in [g[0] for g in GAL] else '%s_hall' % nxt
            link('%s_stair%d' % (n, k), dst, 'stair', ref=S.sid, band=i)
    # upper stairs L11 -> L30 (one shaft per band)
    for k, lst in up.items():
        for i, S in enumerate(lst):
            S.build(acc)
            n0 = UPF[i][0]; n1 = UPF[i + 1][0]; z0 = UPF[i][1]; z1 = UPF[i + 1][1]
            u0 = S.u0
            lid = '%s_su%d' % (n0, k)
            link('%s_hall' % n0, lid, 'door', probes=[dict(t='clear', a=S.F(u0 - 1.5, -0.9), b=S.F(u0 + 1.5, -0.9), z=z0), dict(t='floor', p=(*S.F(u0 + 1.2, -0.9), z0))])
            space(lid, 'stair_landing', n0, (*S.F(u0 + 1.2, -0.9), z0))
            link(lid, '%s_hall' % n1, 'stair', ref=S.sid, band=0)
        lst[-1].top_rails(acc, UPF[-1][1])
    # passenger lifts (valley cores): serve L1..L10 + L11 sky lobby
    for k in range(P.N_ARMS):
        stops = ['%s_core%d' % (n, k) for n, z, h, p in GAL] + ['L11_hall']
        for li, _ in enumerate(core_lifts(k)):
            SPEC['lifts'].append(dict(id='P%d_%d' % (k, li), kind='passenger', stops=stops))
    atrium_lifts(acc)
    central_core(acc)
    atrium_roof(acc)
    art_ring(acc)
    lobby_fitout(acc)
    return SPEC

def intervals_from_cuts(cuts):
    """full circle minus angular cuts (centre, half-width) -> [(a0, a1)]"""
    cs = sorted(((c - w) % (2 * math.pi), (c - w) % (2 * math.pi) + 2 * w) for c, w in cuts)
    out = []
    for i, (s, e) in enumerate(cs):
        ns = cs[(i + 1) % len(cs)][0] + (2 * math.pi if i + 1 == len(cs) else 0)
        if ns > e + 1e-4: out.append((e, ns))
    return out

def rail_intervals(r, gaps):
    if not gaps: return [(0, 2 * math.pi)]
    return intervals_from_cuts([(a, (w / 2 + 0.3) / r) for a, w in gaps])

def arm_fitout(acc, name, z, h, k):
    a = P.arm_angle(k); F = frame(a, 0.0)
    zc = z + h - P.SLAB_T
    ri = P.Ri(z)
    # ceiling light lines along the arm
    for v in (-6.0, 6.0):
        lbox(acc, 'Lights_Amber', 'light_panel', F, RW + 3, P.Ro(zc) - 14, v - 0.25, v + 0.25, zc - 0.1, zc - 0.02)
    if name == 'L1' and k == 0: return
    if name in ('L1', 'L2'):
        # service / shop counters
        lbox(acc, 'Exhibits', 'titanium', F, ri - 4, ri + 8, -9, -7.5, z, z + 1.1)
        lbox(acc, 'Lights_Amber', 'strip_amber', F, ri - 4, ri + 8, -7.55, -7.45, z + 0.9, z + 1.05)
        return
    dh = min(5.5, h - 3.0)
    arts = ['art_a', 'art_b', 'art_c', 'art_d']
    # typical gallery: free-standing display walls with framed art + picture lights, plinths with lit sculptures
    for q, uu in enumerate(np.arange(RW + 10.0, ri - 12.0, 12.0)):
        sgn = 1 if q % 2 else -1; v = sgn * 9.0
        lbox(acc, 'Exhibits', 'wall_light', F, uu, uu + 7.0, v - 0.2, v + 0.2, z, z + dh)
        vv = v - sgn * 0.21
        qd = [(*F(uu + 0.8, vv), z + 1.3), (*F(uu + 6.2, vv), z + 1.3), (*F(uu + 6.2, vv), z + dh - 1.0), (*F(uu + 0.8, vv), z + dh - 1.0)]
        acc.add_face('Art', arts[(k + q) % 4], qd if sgn < 0 else qd[::-1])
        lbox(acc, 'Exhibits', 'frame_dark', F, uu + 0.6, uu + 6.4, vv - sgn * 0.08 - 0.04, vv - sgn * 0.08 + 0.04, z + 1.1, z + 1.3)
        lbox(acc, 'Lights_Amber', 'light_panel', F, uu + 0.5, uu + 6.5, vv - sgn * 0.6 - 0.15, vv - sgn * 0.6 + 0.15, z + dh + 0.3, z + dh + 0.4)
        lbox(acc, 'Exhibits', 'struct_dark', F, uu + 2.5, uu + 4.5, -1.0, 1.0, z, z + 1.0)
        lbox(acc, 'Lights_Cyan', 'strip_cyan', F, uu + 2.45, uu + 4.55, -1.05, 1.05, z + 0.95, z + 1.0)
        acc.cyl('Art', 'gold' if q % 2 else 'holo_cyan', *F(uu + 3.5, 0), z + 1.0, z + 2.8, 0.7, n=10, r1=0.1)
    for j, v in enumerate((-8.0, 8.0)):
        lbox(acc, 'Exhibits', 'wall_light', F, ri - 8, ri + 6, v - 0.2, v + 0.2, z, z + dh)
        m = arts[(k + j + int(z)) % 4]
        for s in (-1, 1):
            vv = v + s * 0.21
            q = [(*F(ri - 6, vv), z + 1.2), (*F(ri + 4, vv), z + 1.2), (*F(ri + 4, vv), z + dh - 0.8), (*F(ri - 6, vv), z + dh - 0.8)]
            acc.add_face('Art', m, q if s > 0 else q[::-1])
        lbox(acc, 'Lights_Amber', 'strip_amber', F, ri - 8, ri + 6, v - 0.25, v + 0.25, z + dh, z + dh + 0.08)
    # plinth + glowing sculpture
    lbox(acc, 'Exhibits', 'titanium', F, ri + 12, ri + 15, -1.5, 1.5, z, z + 1.0)
    acc.cyl('Art', 'holo_cyan' if k % 2 else 'gold', *F(ri + 13.5, 0), z + 1.0, z + 3.4, 0.9, n=8, r1=0.2)

def central_core(acc):
    """glass core L11 -> crown, centred on the leaning tower axis (stepped per floor), 4 high-speed lifts"""
    R = P.CORE_R
    stops = {}
    door_ang = [P.arm_angle(k) for k in HS_ARMS]
    for nm, z, h, p in UPF:
        z1 = min(z + h, P.CROWN_Z); c = cc(z)
        if nm in P.HS_STOPS:
            for a0, a1 in intervals_from_cuts([(a, 1.6 / R) for a in door_ang]):
                arc_wall(acc, 'Core_Glass', 'glass_core', R, a0, a1, z, z1, t=0.12, seg_len=2.4, c=c)
            for a in door_ang:
                arc_wall(acc, 'Core_Glass', 'glass_core', R, a - 1.6 / R, a + 1.6 / R, z + 3.2, z1, t=0.12, seg_len=1.6, c=c)
                F = cframe(a, c)
                lbox(acc, 'Cores', 'door_lift_hs', F, R - 1.0, R - 0.85, -1.4, 1.4, z, z + 3.2)
                lbox(acc, 'Lights_Cyan', 'strip_cyan', F, R - 0.85, R - 0.8, -1.55, 1.55, z + 3.15, z + 3.3)
            stops[nm] = '%s_hall' % nm
        else:
            arc_wall(acc, 'Core_Glass', 'glass_core', R, 0, 2 * math.pi, z, z1, t=0.12, seg_len=2.4, c=c)
        for k in range(8):
            a = 2 * math.pi * k / 8
            acc.bar('Shell_Frame', 'frame_metal', (c[0] + R * math.cos(a), c[1] + R * math.sin(a), z), (c[0] + R * math.cos(a), c[1] + R * math.sin(a), z1), 0.3, 0.3)
        acc.cyl('Shell_Frame', 'frame_metal', c[0], c[1], z1 - 0.3, z1, R + 0.15, n=24, r1=R + 0.15, caps=False)
        for k in range(4):     # lift shafts (stepped with the core)
            F = cframe(P.valley_angle(2 * k), c)
            lbox(acc, 'Cores', 'lift_shaft', F, 2.2, 5.6, -1.7, 1.7, z, z1)
    # glowing oculus: core underside seen from the atrium
    acc.cyl('Lights_Cyan', 'holo_cyan', *cc(P.ATRIUM_TOP), P.ATRIUM_TOP - 0.7, P.ATRIUM_TOP - 0.6, R + 0.3, n=32, r1=R + 0.3)
    SPEC['lifts'].append(dict(id='HS', kind='high_speed', count=P.N_HS_LIFTS, stops=[stops[n] for n in P.HS_STOPS]))

def cframe(ang, c):
    ca, sa = math.cos(ang), math.sin(ang)
    return lambda u, v: (c[0] + u * ca - v * sa, c[1] + u * sa + v * ca)

ATR_LIFT_R = 37.0
def atrium_lifts(acc):
    """4 glass lift shafts in the atrium on the diagonals, L1 lobby <-> L11 sky lobby (doors face the atrium centre)"""
    zt = P.ATRIUM_TOP + 3.6
    for k in ATR_LIFT_ARMS:
        F = frame(P.arm_angle(k), 0.0)
        u0, u1 = ATR_LIFT_R - 1.75, ATR_LIFT_R + 1.75
        for (ua, ub, va, vb) in ((u0, u1, -1.75, -1.6), (u0, u1, 1.6, 1.75), (u1 - 0.15, u1, -1.75, 1.75)):
            lbox(acc, 'Core_Glass', 'glass_core', F, ua, ub, va, vb, 0.0, zt)
        for zz, z1 in ((3.2, P.ATRIUM_TOP), (P.ATRIUM_TOP + 3.2, zt)):
            lbox(acc, 'Core_Glass', 'glass_core', F, u0, u0 + 0.15, -1.75, 1.75, zz, z1)
        lbox(acc, 'Shell_Frame', 'frame_metal', F, u0 - 0.1, u1 + 0.1, -1.85, 1.85, zt, zt + 0.4)
        for zz in (0.0, P.ATRIUM_TOP):
            lbox(acc, 'Cores', 'door_lift_hs', F, u0 + 0.15, u0 + 0.3, -1.3, 1.3, zz, zz + 3.0)
            lbox(acc, 'Lights_Cyan', 'strip_cyan', F, u0 - 0.05, u0, -1.45, 1.45, zz + 3.0, zz + 3.15)
        lbox(acc, 'Lights_Cyan', 'strip_cyan', F, u1 + 0.02, u1 + 0.1, -0.15, 0.15, 3.0, P.ATRIUM_TOP)
        lbox(acc, 'Lights_Amber', 'cab', F, u0 + 0.3, u1 - 0.3, -1.4, 1.4, 60.0 + 30 * k, 63.0 + 30 * k)
    SPEC['lifts'].append(dict(id='HA', kind='atrium_glass', count=len(ATR_LIFT_ARMS), stops=['L1_lobby', 'L11_hall']))

def atrium_roof(acc):
    """section A-A: the Ø80 atrium is closed at L11 by a faceted conical soffit rising to the core oculus"""
    z0, z1 = P.ATRIUM_TOP - 9.0, P.ATRIUM_TOP - 0.7
    r0, r1 = P.ATRIUM_R - 0.2, P.CORE_R + 0.4
    c1 = cc(P.ATRIUM_TOP); n = 32
    for i in range(n):
        A, B = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        q = [(r0 * math.cos(A), r0 * math.sin(A), z0), (r0 * math.cos(B), r0 * math.sin(B), z0),
             (c1[0] + r1 * math.cos(B), c1[1] + r1 * math.sin(B), z1), (c1[0] + r1 * math.cos(A), c1[1] + r1 * math.sin(A), z1)]
        acc.add_face('Atrium_Roof', 'titanium', q[::-1])
        if i % 2 == 0:
            acc.bar('Lights_Cyan', 'strip_cyan', (r0 * math.cos(A) * 0.995, r0 * math.sin(A) * 0.995, z0 - 0.05), (c1[0] + r1 * math.cos(A), c1[1] + r1 * math.sin(A), z1 - 0.05), 0.25, 0.08)
    arc_band(acc, 'Lights_Amber', 'strip_amber', r0 - 0.6, r0, 0, 2 * math.pi, z0 - 0.05, down=True)

def art_ring(acc):
    """interior sheet: thick vertical golden ring Ø≈36 standing on the atrium floor (faces the entrance)"""
    z = P.ART_RING_Z; Rt = P.ART_RING_R - 5.5
    torus(acc, 'Art', 'gold', Rt, 5.5, (0, 0, z), tilt=(math.radians(90), 0), n=72, m=16)
    torus(acc, 'Art', 'strip_amber', Rt - 5.6, 0.25, (0, -0.0, z), tilt=(math.radians(90), 0), n=48, m=6)
    for s in (-1, 1):
        torus(acc, 'Art', 'strip_cyan', Rt, 0.2, (0, s * 5.55, z), tilt=(math.radians(90), 0), n=72, m=5)
    acc.box('Art', 'titanium', -6.0, -4.0, 0.0, 6.0, 4.0, z - P.ART_RING_R + 1.2)
    # ornament: radial blades (gear teeth) around the outer rim + inner filigree ring, bronze/dark inlay
    for i in range(72):
        a = 2 * math.pi * i / 72; ca, sa = math.cos(a), math.sin(a)
        for s_ in (-1, 1):
            p0 = (ca * (Rt + 3.2), s_ * 4.2, z + sa * (Rt + 3.2)); p1 = (ca * (Rt + 6.4), s_ * 2.4, z + sa * (Rt + 6.4))
            acc.bar('Art', 'bronze' if i % 2 else 'gold', p0, p1, 0.5, 0.35, up=(0, 1, 0))
        acc.bar('Art', 'struct_dark', (ca * (Rt - 5.0), -2.5, z + sa * (Rt - 5.0)), (ca * (Rt - 6.2), 2.5, z + sa * (Rt - 6.2)), 0.35, 0.35) if i % 3 == 0 else None
    torus(acc, 'Art', 'bronze', Rt + 5.6, 0.45, (0, 0, z), tilt=(math.radians(90), 0), n=96, m=6)
    arc_band(acc, 'Lights_Amber', 'strip_amber', 9.6, 10.0, 0, 2 * math.pi, 0.02)

def lobby_fitout(acc):
    # reception desk (arc) + info pylon in the L1 lobby, front side of the atrium
    for a0 in (math.radians(-130), math.radians(-60)):
        arc_wall(acc, 'Exhibits', 'titanium', 30.0, a0, a0 + math.radians(20), 0, 1.1, t=1.2, seg_len=2.0)
        arc_wall(acc, 'Lights_Amber', 'strip_amber', 29.35, a0, a0 + math.radians(20), 0.85, 1.0, t=0.05, seg_len=2.0)
    for x in (-24.0, 24.0):
        acc.box('Exhibits', 'frame_dark', x - 1.5, -150, 0, x + 1.5, -149.4, 7.0)
        acc.add_face('Screens', 'screen_sign', [(x - 1.4, -150.05, 1.0), (x + 1.4, -150.05, 1.0), (x + 1.4, -150.05, 6.8), (x - 1.4, -150.05, 6.8)])

def upper_floor(acc, name, z, h, prog, up):
    """L11-L30: open galleries around the leaning central core, display walls on the diagonal arms"""
    c = cc(z); zc = z + h - P.SLAB_T; ri = P.Ri(z)
    sid = '%s_hall' % name
    space(sid, 'sky_lobby' if name == 'L11' else ('observation' if name in ('L28', 'L29', 'L30') else 'gallery'), name, (c[0], c[1] - (P.CORE_R + 3.5), z), program=prog)
    # perimeter amber cove + ceiling ring light
    pts = P.star(z, inset=2.0)
    for a, b in zip(pts, pts[1:] + pts[:1]):
        acc.bar('Lights_Amber', 'strip_amber', (*a, z + 0.05), (*b, z + 0.05), 0.3, 0.1)
    # ceiling cove lights near the facade (visible through the glass as floor-by-floor warm bands)
    if h > 4.0:
        cp = P.star(zc, inset=3.5)
        for a, b in zip(cp, cp[1:] + cp[:1]):
            acc.bar('Lights_Amber', 'light_panel', (*a, zc - 0.12), (*b, zc - 0.12), 0.8, 0.08)
    # exhibits
    r0, r1 = P.CORE_R + 6.0, ri - 3.0
    for k in (1, 3, 5, 7):
        F = cframe(P.arm_angle(k), c)
        if r1 - r0 > 6.0 and h >= 9.0:
            dh = min(6.0, h - 3.0)
            lbox(acc, 'Exhibits', 'wall_light', F, r0, r1, -0.2, 0.2, z, z + dh)
            m = ['art_a', 'art_b', 'art_c', 'art_d'][(k + int(z)) % 4]
            for s_ in (-1, 1):
                vv = s_ * 0.21; q = [(*F(r0 + 1, vv), z + 1.2), (*F(r1 - 1, vv), z + 1.2), (*F(r1 - 1, vv), z + dh - 0.8), (*F(r0 + 1, vv), z + dh - 0.8)]
                acc.add_face('Art', m, q if s_ > 0 else q[::-1])
            lbox(acc, 'Lights_Amber', 'strip_amber', F, r0, r1, -0.25, 0.25, z + dh, z + dh + 0.08)
        elif r1 - r0 > 3.0:
            rm = (r0 + r1) / 2
            lbox(acc, 'Exhibits', 'titanium', F, rm - 1.5, rm + 1.5, -1.0, 1.0, z, z + 0.8)
            acc.cyl('Art', 'holo_cyan' if k % 4 == 1 else 'gold', *F(rm, 0), z + 0.8, z + min(2.6, h - 1.5), 0.6, n=8, r1=0.15)
    if name == 'L11':
        for k in ATR_LIFT_ARMS:   # sky-lobby side of the atrium lifts
            link(sid, 'L1_lobby', 'lift', ref='HA', probes=[dict(t='floor', p=(*frame(P.arm_angle(k), 0)(ATR_LIFT_R - 3.0, 0), z))])
