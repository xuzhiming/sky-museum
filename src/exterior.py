"""Exterior: faceted tapering 8-arm star shell, ribs, cyan strips, podium + media screens, entrance portal,
observation ring discs, crown + spire, plaza."""
import math, numpy as np
import params as P
from shapes import slab, wall, circle, arc_band, Polygon
from shapely.geometry import box as sbox

def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

def shell_stations():
    zs = [z for z in P.STATIONS if z <= 400.0 + 1e-6]
    return zs + [P.CROWN_Z]

def star_at(z):
    if z > 400.0:   # crown 400 -> CROWN_Z: same star scaled to CROWN_R about the tower axis
        s = P.CROWN_R / P.Ro(400.0); c = P.yc(400.0)
        return [(x * s, c + (y - c) * s) for x, y in P.star(400.0)]
    return P.star(z)

def build_exterior(acc):
    import detail as D
    zs = shell_stations()
    n = 3 * P.N_ARMS
    TI = ['ti_panel', 'ti_panel2', 'ti_panel3']; ARM = ['ti_armor', 'ti_armor2']
    for a, b in zip(zs, zs[1:]):
        A, B = star_at(a), star_at(b)
        podium = b <= 48.0 + 1e-6
        ca, cb = P.yc(a), P.yc(b)
        hb = b - a
        for i in range(n):
            j = (i + 1) % n
            pa0, pa1, pb1, pb0 = A[i], A[j], B[j], B[i]
            Q = [np.array((*pa0, a)), np.array((*pa1, a)), np.array((*pb0, b)), np.array((*pb1, b))]   # P00 P10 P01 P11
            mid = ((pa0[0] + pa1[0]) / 2, (pa0[1] + pa1[1]) / 2 - ca)
            kind = i % 3          # 0 tip face, 1 tip->valley, 2 valley->tip
            if podium:
                if i == 0:        # front arm tip: entrance portal (full 48 m opening)
                    L = math.dist(pa0, pa1); f0 = (L - P.ENTRANCE_W) / 2 / L
                    for (s0, s1) in ((0, f0), (1 - f0, 1)):
                        acc.add_face('Podium', 'titanium', [(*lerp(pa0, pa1, s0), a), (*lerp(pa0, pa1, s1), a), (*lerp(pb0, pb1, s1), b), (*lerp(pb0, pb1, s0), b)])
                        D.panels(acc, 'D_Panels', TI, *Q, mid, u0=s0, u1=s1, seed=i * 7 + a)
                    continue
                SCR = (1, n - 1, 4, n - 4, 7, n - 7, 10, n - 10)   # faces carrying M2 media screens (see media_screens)
                acc.add_face('Podium', 'titanium' if (kind == 0 or i in SCR) else 'glass_curtain', [(*pa0, a), (*pa1, a), (*pb1, b), (*pb0, b)])
                nrm = D.quad_normal(*Q[:3], mid)
                if kind == 0:     # podium arm tip: M4 angled armor + M5 cyan channel (as on the tower)
                    D.panels(acc, 'D_Panels', ARM, *Q, mid, cw=7.0, ch=8.0, u0=0.0, u1=0.40, angled=True, seed=i * 7 + a)
                    D.panels(acc, 'D_Panels', ARM, *Q, mid, cw=7.0, ch=8.0, u0=0.60, u1=1.0, angled=True, seed=i * 5 + a)
                    for (u0, u1, off, mat, g) in ((0.44, 0.56, 0.12, 'strip_cyan', 'Lights_Cyan'), (0.40, 0.44, 1.1, 'ti_armor', 'Shell_Frame'), (0.56, 0.60, 1.1, 'ti_armor', 'Shell_Frame')):
                        c4 = [D.bil(*Q, u, v) + nrm * off for u, v in ((u0, 0), (u1, 0), (u1, 1), (u0, 1))]
                        acc.add_face(g, mat, [tuple(p) for p in c4])
                elif i in SCR:    # screen-backed bay: dark armor behind the LED screen
                    D.panels(acc, 'D_Panels', ARM, *Q, mid, cw=7.0, ch=8.0, angled=False, seed=i * 3 + a)   # flat: stays behind the screen
                else:             # podium flanks: M4 armor fringe + M3 curtain-wall mullions + warm lobby glow floor by floor
                    ua, ub = (0.30, 1.0) if kind == 1 else (0.0, 0.70)
                    fa, fb = (0.0, 0.30) if kind == 1 else (0.70, 1.0)
                    D.panels(acc, 'D_Panels', ARM, *Q, mid, cw=6.0, ch=8.0, u0=fa, u1=fb, angled=True, seed=i * 7 + a)
                    D.mullion_grid(acc, *Q, mid, du=3.0, transoms=tuple(k / max(1, round(hb / 4.0)) for k in range(1, max(1, round(hb / 4.0)))), u0=ua, u1=ub, g='D_Mullions')
                    zz = a + 3.6
                    while zz < b - 0.5:   # mezzanine / exhibition-floor slab hints every ~4 m
                        v1 = (zz - a) / hb; v0 = max(0.0, v1 - 1.0 / hb * (1.2 if D._h(i, zz) > 0.5 else 0.7))
                        mat = 'room_warm_hi' if D._h(zz, i) > 0.7 else ('room_warm' if D._h(zz, i) > 0.3 else 'room_warm_lo')
                        c4 = [D.bil(*Q, u, v) - nrm * 1.4 for u, v in ((ua, v0), (ub, v0), (ub, v1), (ua, v1))]
                        acc.add_face('Lights_Amber', mat, [tuple(p) for p in c4][::-1])
                        zz += 4.0
            elif kind == 0:
                # arm tip: M4 angled-cut armor either side of the M5 vertical light-strip channel
                acc.add_face('Shell_Glass', 'ti_armor', [(*pa0, a), (*pa1, a), (*pb1, b), (*pb0, b)])
                D.panels(acc, 'D_Panels', ARM, *Q, mid, cw=6.5, ch=9.0, u0=0.0, u1=0.40, angled=True, seed=i * 11 + a)
                D.panels(acc, 'D_Panels', ARM, *Q, mid, cw=6.5, ch=9.0, u0=0.60, u1=1.0, angled=True, seed=i * 13 + a)
                nrm = D.quad_normal(*Q[:3], mid)
                for (u0, u1, off, mat, g) in ((0.43, 0.57, 0.12, 'strip_cyan', 'Lights_Cyan'), (0.40, 0.43, 1.1, 'ti_armor', 'Shell_Frame'), (0.57, 0.60, 1.1, 'ti_armor', 'Shell_Frame')):
                    c4 = [D.bil(*Q, u, v) + nrm * off for u, v in ((u0, 0), (u1, 0), (u1, 1), (u0, 1))]
                    acc.add_face(g, mat, [tuple(p) for p in c4])
            else:
                acc.add_face('Shell_Glass', 'glass_curtain', [(*pa0, a), (*pa1, a), (*pb1, b), (*pb0, b)])
                # M4 armor covers the ridge half of each flank; glass only in the slot between armor and the valley frame (as on the sheet)
                cov = 0.46 if a < 300 else 0.34
                ua, ub = (cov, 0.90) if kind == 1 else (0.10, 1.0 - cov)
                fa, fb = (0.0, cov) if kind == 1 else (1.0 - cov, 1.0)
                va, vb = (0.90, 1.0) if kind == 1 else (0.0, 0.10)
                nrm = D.quad_normal(*Q[:3], mid)
                D.panels(acc, 'D_Panels', ['ti_panel', 'ti_panel2', 'ti_panel3', 'ti_armor2'], *Q, mid, cw=6.5, ch=min(hb, 7.0), gap=0.16, depth=0.9, bev=0.45, u0=fa, u1=fb, angled='blade', seed=i * 17 + a)
                c4 = [D.bil(*Q, u, v) + nrm * 0.5 for u, v in ((va, 0), (vb, 0), (vb, 1), (va, 1))]       # valley-side gunmetal frame
                acc.add_face('Shell_Frame', 'ti_armor2', [tuple(p) for p in c4])
                D.mullion_grid(acc, *Q, mid, du=3.6, transoms=(0.5,) if hb > 7 else (), u0=ua, u1=ub, g='D_Mullions')
                if b > 50 and hb >= 8 and a < 330:     # diagonal bracing outside the glass (alternating per band -> X pattern)
                    flip = (zs.index(a) + kind) % 2
                    D.brace(acc, D.bil(*Q, ua if flip else ub, 0.02), D.bil(*Q, ub if flip else ua, 0.98), nrm)
                # floor-by-floor interior hint: warm ceiling cove just inside the glass (varying intensity per bay)
                r = D._h(i, a)
                if b > 50 and r > 0.12:
                    mat = 'room_warm_hi' if r > 0.75 else ('room_warm' if r > 0.35 else 'room_warm_lo')
                    zc0 = max(0.0, (b - a - 2.6) / (b - a)); zc1 = (b - a - 0.9) / (b - a)
                    c4 = [D.bil(*Q, u, v) - nrm * 1.4 for u, v in ((ua, zc0), (ub, zc0), (ub, zc1), (ua, zc1))]
                    acc.add_face('Lights_Amber', mat, [tuple(p) for p in c4][::-1])
            # horizontal floor band (every station)
            acc.bar('Shell_Frame', 'ti_armor2', (*pa0, a), (*pa1, a), 0.9 if not podium else 0.5, 0.7)
            if not podium and kind != 0:
                s0 = np.array(pa0) - np.array([0, ca]); s1 = np.array(pa1) - np.array([0, ca])
                s0 = s0 * (1 - 0.8 / np.linalg.norm(s0)) + np.array([0, ca]); s1 = s1 * (1 - 0.8 / np.linalg.norm(s1)) + np.array([0, ca])
                acc.add_face('Lights_Amber', 'strip_amber_soft', [(*s0, a + 0.05), (*s1, a + 0.05), (*s1, a + 0.45), (*s0, a + 0.45)])
        # vertex ribs: arm tips = layered M1 ribs with cyan M5 strip, valleys = slim dark rib with amber line
        for i in range(n):
            kind = i % 3
            p0, p1 = A[i], B[i]
            o = (p0[0], p0[1] - ca)
            if kind in (0, 1):
                dd = 1.9 if a < 300 else 1.2
                D.exo_frame(acc, (*p0, a), (*p1, b), o, w=3.4 if a < 300 else 2.4, d=dd)
                D.joint_plate(acc, (*p0, a), o, s=1.0 if a < 300 else 0.6, d=dd)
                if a == 0 and not (kind == 0 and i == 0) and not (kind == 1 and i == 1):   # base-corner buttress (not inside the portal)
                    Bz = P.star(40.0)[i]
                    D.buttress(acc, (*p0, 0.0), (*Bz, 40.0), o)
            else:
                acc.bar('Shell_Frame', 'ti_armor2', (*p0, a), (*p1, b), 1.0, 1.0)
                if not podium and P.VALLEY_STRIPS:
                    c0 = np.array(p0) - np.array([0, ca]); c1 = np.array(p1) - np.array([0, cb])
                    c0 = c0 * (1 + 0.6 / max(np.linalg.norm(c0), 1)) + np.array([0, ca]); c1 = c1 * (1 + 0.6 / max(np.linalg.norm(c1), 1)) + np.array([0, cb])
                    acc.bar('Lights_Amber', 'strip_amber', (*c0, a), (*c1, b), 0.3, 0.3)
    # amber horizontal light bands on the podium
    A = P.star(0)
    for zb in (16.0, 26.0, 36.0, 46.0):
        for i in range(1, 3 * P.N_ARMS):
            a, b = P.star(zb)[i], P.star(zb)[(i + 1) % (3 * P.N_ARMS)]
            acc.bar('Lights_Amber', 'strip_amber', (*np.array(a) * 1.002, zb - 0.6), (*np.array(b) * 1.002, zb - 0.6), 0.25, 0.35)
    media_screens(acc)
    portal(acc)
    fans(acc)
    pods(acc)
    obs_rings(acc)
    portal_frame(acc)
    crown_spire(acc)
    plaza(acc)

def media_screens(acc):
    """M2 display curtain wall: large LED media screens on the lower faces, deep bezel + cyan edge light + louvre fins"""
    ZS0, ZS1 = 24.0, 46.0    # screen band kept inside one near-planar facade segment (the 0-24 m podium bulges ~4 m beyond a 0-47 chord)
    S = P.star(ZS0); S48 = P.star(ZS1)
    n = 3 * P.N_ARMS
    picks = [(1, 'screen_a'), (n - 1, 'screen_b'), (4, 'screen_c'), (n - 4, 'screen_d'), (7, 'screen_b'), (n - 7, 'screen_a'), (10, 'screen_c'), (n - 10, 'screen_d')]
    for i, mat in picks:
        j = (i + 1) % n
        z0, z1 = ZS0 + 1.0, P.SCREEN_Z[1]
        def pt(t, z, off=0.5):
            f = (min(z, ZS1) - ZS0) / (ZS1 - ZS0)
            a = lerp(S[i], S48[i], f); b = lerp(S[j], S48[j], f)
            p = np.array(lerp(a, b, t))
            nrm = np.array([b[1] - a[1], -(b[0] - a[0])]); nrm /= np.linalg.norm(nrm)
            return (*(p + nrm * off), z)
        z1 = min(z1, 46.0)
        t0, t1 = 0.12, 0.88
        acc.add_face('Screens', mat, [pt(t0, z0, 1.2), pt(t1, z0, 1.2), pt(t1, z1, 1.2), pt(t0, z1, 1.2)])
        for (ta, za, tb, zb) in ((t0, z0, t1, z0), (t0, z1, t1, z1), (t0, z0, t0, z1), (t1, z0, t1, z1)):
            acc.bar('Shell_Frame', 'struct_dark', pt(ta, za, 1.4), pt(tb, zb, 1.4), 1.2, 1.6)
            acc.bar('Lights_Cyan', 'strip_cyan', pt(ta, za, 2.25), pt(tb, zb, 2.25), 0.25, 0.1)
        for k in range(1, 6):   # vertical LED module seams
            t = t0 + (t1 - t0) * k / 6
            acc.bar('Shell_Frame', 'struct_dark', pt(t, z0, 1.25), pt(t, z1, 1.25), 0.12, 0.1)

def portal(acc):
    """M6 entrance portal: stepped multi-layer frame with cyan reveals, gable crown, canopy with light grid, glazing grid, doors, sign"""
    y0 = -P.Ro(0.0); W = P.ENTRANCE_W; H = P.ENTRANCE_H; rec = P.ENTRANCE_RECESS
    for sx in (-1, 1):
        x = sx * W / 2
        acc.box('Portal', 'titanium', (x - 0.6) if sx < 0 else x, y0, 0, x if sx < 0 else (x + 0.6), y0 + rec, H)
        for k in range(3):      # stepped jambs (outer layers stand proud of the facade)
            xa = x + sx * (0.6 + 2.2 * k); xb = xa + sx * 2.0
            yb = y0 + 1.5 - 0.9 * k
            acc.box('Portal', 'ti_armor' if k != 1 else 'ti_armor2', min(xa, xb), yb - 1.6, 0, max(xa, xb), yb, H + 2.0 * k)
            acc.box('Lights_Cyan', 'strip_cyan', min(xa, xb) + (0.0 if sx > 0 else 1.7), yb - 1.7, 0.3, max(xa, xb) - (1.7 if sx > 0 else 0.0), yb - 1.6, H + 2.0 * k - 0.3)
        for k in range(4):      # vertical fins beside the portal
            xf = sx * (W / 2 + 9.0 + 3.2 * k)
            acc.box('Portal', 'ti_armor2', xf - 0.35, y0 - 1.8, 0, xf + 0.35, y0 + 0.1, H - 6 - 4 * k)
            acc.box('Lights_Amber', 'strip_amber', xf - 0.1, y0 - 1.85, 0.5, xf + 0.1, y0 - 1.8, H - 6.5 - 4 * k)
    acc.box('Portal', 'ti_armor', -W / 2 - 6.6, y0 - 0.3, H - 3.0, W / 2 + 6.6, y0 + 1.5, H + 4.0)   # lintel
    acc.box('Lights_Cyan', 'strip_cyan', -W / 2 - 6.0, y0 - 0.4, H - 2.2, W / 2 + 6.0, y0 - 0.3, H - 1.8)
    # gable crown over the portal (pentagon frame, M6)
    gx, gz0, gz1 = W / 2 + 7.0, H + 4.0, H + 22.0
    for (pa, pb) in (((-gx, gz0), (0, gz1)), ((0, gz1), (gx, gz0))):
        acc.bar('Portal', 'ti_armor', (pa[0], y0 - 1.0, pa[1]), (pb[0], y0 - 1.0, pb[1]), 2.6, 2.4)
        acc.bar('Lights_Cyan', 'strip_cyan', (pa[0], y0 - 2.25, pa[1] - 0.8), (pb[0], y0 - 2.25, pb[1] - 0.8), 0.6, 0.1)
    acc.add_face('Portal', 'ti_armor2', [(-gx + 3, y0 + 0.2, gz0 + 0.6), (gx - 3, y0 + 0.2, gz0 + 0.6), (0, y0 + 0.2, gz1 - 2.0)])
    acc.add_face('Screens', 'screen_sign', [(-9, y0 - 0.1, gz0 + 1.6), (9, y0 - 0.1, gz0 + 1.6), (9, y0 - 0.1, gz0 + 6.6), (-9, y0 - 0.1, gz0 + 6.6)])
    # recessed glazing: mullion grid + transoms, doors
    yc = y0 + rec
    dw, dh = P.DOOR_W, P.DOOR_H
    for (x0, x1, z0, z1) in ((-W / 2, -dw / 2, 0, H), (dw / 2, W / 2, 0, H), (-dw / 2, dw / 2, dh, H)):
        acc.box('Entrance_Glass', 'glass_clear', x0, yc - 0.1, z0, x1, yc + 0.1, z1)
    for x in np.linspace(-W / 2, W / 2, 13):
        acc.box('Shell_Frame', 'brushed', x - 0.15, yc - 0.5, 0 if abs(x) >= dw / 2 - 0.1 else dh, x + 0.15, yc + 0.2, H)
    for z in [dh] + list(np.arange(10.0, H, 4.0)):
        acc.box('Shell_Frame', 'brushed', -W / 2, yc - 0.45, z - 0.12, W / 2, yc + 0.2, z + 0.12)
    for x in (-dw / 2 + 0.3, -0.15, dw / 2 - 0.3):  # door leaves frames
        acc.box('Shell_Frame', 'struct_dark', x - 0.15, yc - 0.3, 0, x + 0.15, yc + 0.1, dh)
    # canopy with underside light grid
    acc.box('Portal', 'ti_armor2', -W / 2 - 1.0, y0 - 4.0, 11.0, W / 2 + 1.0, y0 + rec - 0.3, 12.0)
    acc.box('Lights_Cyan', 'strip_cyan', -W / 2 - 1.0, y0 - 4.1, 11.2, W / 2 + 1.0, y0 - 4.0, 11.8)
    for x in np.linspace(-W / 2 + 2, W / 2 - 2, 6):
        acc.box('Lights_Amber', 'light_panel', x - 0.8, y0 - 3.5, 10.95, x + 0.8, y0 + rec - 1.0, 11.0)
    acc.add_face('Screens', 'screen_sign', [(-12, yc - 0.55, 30), (12, yc - 0.55, 30), (12, yc - 0.55, 40), (-12, yc - 0.55, 40)])
    # entry plinth steps + lit bollards
    for k in range(3):
        acc.box('Ground', 'ti_panel', -W / 2 - 4 + k, y0 - 9 + 2 * k, 0.0, W / 2 + 4 - k, y0 + 0.2, 0.05 + 0.0 * k)
    for sx in (-1, 1):
        for k in range(5):
            acc.cyl('Ground', 'strip_cyan', sx * (W / 2 + 3), y0 - 12 - 7 * k, 0, 1.1, 0.25, n=8)

def fans(acc):
    """diagonal fan wings L1-L5: annular sectors (outer arc follows Ro(z)); titanium panelised base, glass + mullions above 48"""
    import detail as D
    f = P.FAN; hz = math.radians(f['half_deg'])
    zs = [z for z in P.STATIONS if z < f['z1']] + [f['z1']]
    m = 10
    for k in (1, 3, 5, 7):
        a0 = P.arm_angle(k)
        def ring(z):
            ro = P.Ro(z) * f['r_scale'] - (f['top_drop'] if z >= f['z1'] else 0); ri = P.Ri(z) * f['r_in_ratio']; c = P.yc(z)
            out = [(ro * math.cos(a0 - hz + 2 * hz * i / m), c + ro * math.sin(a0 - hz + 2 * hz * i / m)) for i in range(m + 1)]
            inn = [(ri * math.cos(a0 + hz - 2 * hz * i / m), c + ri * math.sin(a0 + hz - 2 * hz * i / m)) for i in range(m + 1)]
            return out + inn
        for za, zb in zip(zs, zs[1:]):
            A, B = ring(za), ring(zb); n = len(A); c = P.yc(za)
            for i in range(m):    # outer arc faces
                Q = [np.array((*A[i], za)), np.array((*A[i + 1], za)), np.array((*B[i], zb)), np.array((*B[i + 1], zb))]
                mid = ((A[i][0] + A[i + 1][0]) / 2, (A[i][1] + A[i + 1][1]) / 2 - c)
                if zb <= 48.0 + 1e-6:
                    nrm = D.quad_normal(*Q[:3], mid)
                    if i in (0, m - 1, m // 2 - 1, m // 2):   # M4 angled armor columns (edges + centre pair)
                        acc.add_face('Fans', 'ti_armor', [(*A[i], za), (*A[i + 1], za), (*B[i + 1], zb), (*B[i], zb)])
                        D.panels(acc, 'D_Panels', ['ti_armor', 'ti_armor2'], *Q, mid, cw=3.2, ch=4.0, angled=True, seed=k * 100 + i + za)
                        if i == m // 2:   # M5 cyan channel between the centre armor columns
                            c4 = [D.bil(*Q, u, v) + nrm * 0.5 for u, v in ((0.0, 0), (0.08, 0), (0.08, 1), (0.0, 1))]
                            acc.add_face('Lights_Cyan', 'strip_cyan', [tuple(p) for p in c4])
                    else:                 # M3 curtain wall + warm exhibition glow, floor by floor
                        acc.add_face('Fans', 'glass_curtain', [(*A[i], za), (*A[i + 1], za), (*B[i + 1], zb), (*B[i], zb)])
                        hb = zb - za; nt = max(1, round(hb / 4.0))
                        D.mullion_grid(acc, *Q, mid, du=3.0, transoms=tuple(t / nt for t in range(1, nt)), g='D_Mullions')
                        zz = za + 3.6
                        while zz < zb - 0.5:
                            v1 = (zz - za) / hb; v0 = max(0.0, v1 - (1.2 if D._h(k, i, zz) > 0.5 else 0.7) / hb)
                            mat = ['room_warm', 'room_warm_hi', 'room_warm_lo'][int(D._h(i, k, zz) * 3) % 3]
                            acc.add_face('Lights_Amber', mat, [tuple(D.bil(*Q, u, v) - nrm * 1.4) for u, v in ((0, v0), (1, v0), (1, v1), (0, v1))][::-1])
                            zz += 4.0
                else:
                    acc.add_face('Fans', 'glass_curtain', [(*A[i], za), (*A[i + 1], za), (*B[i + 1], zb), (*B[i], zb)])
                    D.mullion_grid(acc, *Q, mid, du=3.6, transoms=(0.5,), g='D_Mullions')
                    nrm = D.quad_normal(*Q[:3], mid)
                    mat = ['room_warm', 'room_warm_hi', 'room_warm_lo'][int(D._h(k, i, za) * 3)]
                    acc.add_face('Lights_Amber', mat, [tuple(D.bil(*Q, u, v) - nrm * 1.4) for u, v in ((0, 0.8), (1, 0.8), (1, 0.9), (0, 0.9))][::-1])
            for (i, j) in ((m, m + 1), (2 * m + 1, 0)):   # side faces
                acc.add_face('Fans', 'titanium', [(*A[i], za), (*A[j], za), (*B[j], zb), (*B[i], zb)])
            for i in range(m):
                acc.bar('Shell_Frame', 'ti_armor2', (*A[i], za), (*A[i + 1], za), 0.8, 0.7)
                if za > 0:
                    acc.add_face('Lights_Amber', 'strip_amber_soft', [(A[i][0] * 0.997, A[i][1] * 0.997, za + 0.6), (A[i + 1][0] * 0.997, A[i + 1][1] * 0.997, za + 0.6), (A[i + 1][0] * 0.997, A[i + 1][1] * 0.997, za + 1.0), (A[i][0] * 0.997, A[i][1] * 0.997, za + 1.0)])
        for i, mat in ((2, 'screen_a' if k < 4 else 'screen_c'), (m - 3, 'screen_d' if k < 4 else 'screen_b')):   # M2 media screens on the fan flanks
            def sp(z, ii, off):
                p = ring(z)[ii]; c = P.yc(z); d = np.array((p[0], p[1] - c)); d /= np.linalg.norm(d)
                return (p[0] + d[0] * off, p[1] + d[1] * off, z)
            z0s, z1s = 14.0, 40.0
            acc.add_face('Screens', mat, [sp(z0s, i, 1.2), sp(z0s, i + 2, 1.2), sp(z1s, i + 2, 1.2), sp(z1s, i, 1.2)])
            for (ia, za_, ib, zb_) in ((i, z0s, i + 2, z0s), (i, z1s, i + 2, z1s), (i, z0s, i, z1s), (i + 2, z0s, i + 2, z1s)):
                acc.bar('Shell_Frame', 'struct_dark', sp(za_, ia, 1.4), sp(zb_, ib, 1.4), 1.0, 1.4)
                acc.bar('Lights_Cyan', 'strip_cyan', sp(za_, ia, 2.15), sp(zb_, ib, 2.15), 0.22, 0.1)
        T = ring(f['z1'])
        slab(acc, 'Fans', 'titanium', Polygon(T), f['z1'] - 0.8, f['z1'], edge_mat='strip_cyan_soft')
        R0 = ring(0)
        for i in (0, m):
            D.rib(acc, (*R0[i], 0.0), (*T[i], f['z1']), (R0[i][0], R0[i][1]), depth=1.8)

def pods(acc):
    """3 saucer pods: titanium deck + node B ring module (glass balustrade, posts, fascia band, brackets, underside light rings),
    ribbed conical underside, support struts to the tower, glass pavilion with mullions, neck bridge"""
    import detail as D
    for o in P.PODS:
        z = o['z']; R = o['R']; x, y = o['x'], o['y']; t = o['t']
        disc = circle(R, 96, x, y).difference(Polygon(P.star(z, inset=-0.3)))
        slab(acc, 'Pods', 'ti_panel', disc, z - t, z, edge_mat='ti_armor')
        n = 64; zb = z - t - R * 0.32; rb = R * 0.4
        for i in range(n):
            A, B = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            q = [(x + R * math.cos(A), y + R * math.sin(A), z - t), (x + R * math.cos(B), y + R * math.sin(B), z - t),
                 (x + rb * math.cos(B), y + rb * math.sin(B), zb), (x + rb * math.cos(A), y + rb * math.sin(A), zb)]
            acc.add_face('Pods', 'ti_armor2', q[::-1])
        for i in range(16):     # radial ribs on the cone
            A = 2 * math.pi * i / 16
            acc.bar('Pods', 'brushed', (x + (R - 0.8) * math.cos(A), y + (R - 0.8) * math.sin(A), z - t - 0.4), (x + rb * math.cos(A), y + rb * math.sin(A), zb - 0.2), 0.6, 0.6)
        for rr, zz, mat in ((R * 0.8, z - t - R * 0.32 * 0.25 - 0.3, 'strip_cyan'), (R * 0.6, z - t - R * 0.32 * 0.55 - 0.3, 'strip_amber')):
            D._arc_band_c(acc, mat, (x, y), rr - 0.3, rr + 0.3, zz)
        acc.cyl('Pods', 'ti_armor2', x, y, zb - 2.0, zb, rb, n=32, r1=rb * 0.8)
        acc.cyl('Lights_Cyan', 'strip_cyan', x, y, zb - 2.1, zb - 2.0, rb * 0.8, n=32, r1=rb * 0.8)
        D.ring_module(acc, (x, y), R, z, t, posts=2.5, brackets=12.0, r_in=R * 0.55, g='Pods', bracket_depth=2.5)
        # glass pavilion
        from shapes import arc_wall
        Rp = R * 0.45
        arc_wall(acc, 'Shell_Glass', 'glass_curtain', Rp, 0, 2 * math.pi, z, z + 6.0, t=0.1, seg_len=4.0, c=(x, y))
        for i in range(int(2 * math.pi * Rp / 3.0)):
            A = 2 * math.pi * i / int(2 * math.pi * Rp / 3.0)
            acc.bar('Shell_Frame', 'brushed', (x + Rp * math.cos(A), y + Rp * math.sin(A), z), (x + Rp * math.cos(A), y + Rp * math.sin(A), z + 6.0), 0.18, 0.3)
        D._arc_band_c(acc, 'room_warm_hi', (x, y), 1.0, Rp - 0.6, z + 5.9)
        acc.cyl('Pods', 'ti_armor', x, y, z + 6.0, z + 6.9, Rp + 1.2, n=48, r1=Rp * 0.7)
        acc.cyl('Lights_Cyan', 'strip_cyan', x, y, z + 6.0, z + 6.15, Rp + 1.25, n=48, r1=Rp + 1.25, caps=False)
        # neck bridge + support struts back to the tower
        c = (0.0, P.yc(z)); d = math.hypot(x - c[0], y - c[1]); ux, uy = (x - c[0]) / d, (y - c[1]) / d
        p0 = (c[0] + ux * P.Ri(z) * 0.6, c[1] + uy * P.Ri(z) * 0.6); p1 = (x - ux * R * 0.5, y - uy * R * 0.5)
        w = 5.0; nx, ny = -uy * w, ux * w
        acc.hexa('Pods', 'ti_armor', [(p0[0] - nx, p0[1] - ny, z - t), (p1[0] - nx, p1[1] - ny, z - t), (p0[0] + nx, p0[1] + ny, z - t), (p1[0] + nx, p1[1] + ny, z - t),
                                     (p0[0] - nx, p0[1] - ny, z), (p1[0] - nx, p1[1] - ny, z), (p0[0] + nx, p0[1] + ny, z), (p1[0] + nx, p1[1] + ny, z)])
        acc.bar('Lights_Cyan', 'strip_cyan', (p0[0], p0[1], z - t - 0.1), (p1[0], p1[1], z - t - 0.1), 0.6, 0.1)
        zs = z - t - R * 0.32 - 14.0; rs = P.Ro(zs) * 0.92
        for s in (-1, 1):
            q0 = (x - ux * rb * 0.6 + s * nx * 0.9, y - uy * rb * 0.6 + s * ny * 0.9, zb - 1.0)
            q1 = (c[0] + ux * rs + s * nx * 2.0, c[1] + uy * rs + s * ny * 2.0, zs)
            acc.bar('Pods', 'brushed', q0, q1, 1.4, 1.4)
            acc.bar('Lights_Amber', 'strip_amber', (q0[0], q0[1], q0[2] - 0.75), (q1[0], q1[1], q1[2] - 0.75), 0.25, 0.1)

def obs_rings(acc):
    """M3 observation ring decks at +320/+360/+400 (sheet labels): node B ring module"""
    import detail as D
    for o in P.OBS:
        z = o['z']; c = (0.0, P.yc(z)); R = P.Ro(z) + o['cant']
        disc = circle(R, 128, *c).difference(Polygon(P.star(z, inset=-0.2)))
        slab(acc, 'Obs_Decks', 'ti_panel', disc, z - o['t'], z, edge_mat='ti_armor')
        D.ring_module(acc, c, R, z, o['t'], posts=2.5, brackets=7.5, r_in=P.Ro(z - 6.0) * 0.95, g='Obs_Decks', bracket_depth=5.0)

def _surf_y(x, z):
    """front (-Y) shell surface y at (x, z)"""
    from shapely.geometry import LineString
    g = Polygon(P.star(z)).intersection(LineString([(x, -400), (x, 400)]))
    if g.is_empty: return None
    cs = [p for gg in g.geoms for p in gg.coords] if hasattr(g, 'geoms') else list(g.coords)
    return min(c[1] for c in cs)

def portal_frame(acc):
    """front elevation: pentagon (gable) frame on the main facade around the entrance + atrium glazing"""
    f = P.PORTAL_FRAME
    pts = [(-f['leg_x'], 0.0), (-f['leg_x'], f['eave_z']), (-f['eave_x'], f['eave_z']), (0.0, f['peak_z']), (f['eave_x'], f['eave_z']), (f['leg_x'], f['eave_z']), (f['leg_x'], 0.0)]
    for (xa, za), (xb, zb) in zip(pts, pts[1:]):
        n = max(2, int(math.hypot(xb - xa, zb - za) / 6.0))
        prev = None
        for i in range(n + 1):
            x = xa + (xb - xa) * i / n; z = za + (zb - za) * i / n
            y = _surf_y(x, z)
            if y is None: prev = None; continue
            p = (x, y - 1.2, z)
            if prev:
                acc.bar('Portal', 'frame_dark', prev, p, 2.4, 2.0)
                acc.bar('Lights_Cyan', 'strip_cyan', (prev[0], prev[1] - 1.05, prev[2]), (p[0], p[1] - 1.05, p[2]), 0.5, 0.15)
            prev = p

def crown_spire(acc):
    zc = P.CROWN_Z; c = P.yc(zc)
    slab(acc, 'Spire', 'ti_armor', Polygon(star_at(zc)), zc - 0.8, zc, edge_mat='strip_cyan_soft')
    s = P.SPIRE
    for sx in (-1, 1):     # twin needle blades: armor blade + collar rings + cyan edge + beacon
        x0 = sx * s['x']; y0 = P.yc(s['z0'])
        w, d = s['w0'] / 2, s['d0'] / 2
        q = [(x0 - w, y0 - d, s['z0']), (x0 + w, y0 - d, s['z0']), (x0 - w, y0 + d, s['z0']), (x0 + w, y0 + d, s['z0'])]
        xt, yt = x0 * 0.85, P.yc(s['z1'])
        t = [(xt - 0.3, yt - 0.4, s['z1']), (xt + 0.3, yt - 0.4, s['z1']), (xt - 0.3, yt + 0.4, s['z1']), (xt + 0.3, yt + 0.4, s['z1'])]
        acc.hexa('Spire', 'ti_armor', q + t)
        acc.bar('Lights_Cyan', 'strip_cyan', (x0 - sx * w * 1.05, y0 - d * 0.5, s['z0']), (xt - sx * 0.35, yt, s['z1'] - 1.0), 0.3, 0.3)
        acc.bar('Lights_Cyan', 'strip_cyan', (x0 + sx * w * 1.05, y0 + d * 0.5, s['z0']), (xt + sx * 0.35, yt, s['z1'] - 1.0), 0.3, 0.3)
        for zz in np.arange(s['z0'] + 1.5, s['z1'] - 2.0, 2.0):
            f = (zz - s['z0']) / (s['z1'] - s['z0'])
            cx_ = x0 + (xt - x0) * f; cy_ = y0 + (yt - y0) * f; ww = w + (0.3 - w) * f + 0.25; dd = d + (0.4 - d) * f + 0.25
            acc.box('Spire', 'brushed', cx_ - ww, cy_ - dd, zz, cx_ + ww, cy_ + dd, zz + 0.3)
        acc.cyl('Lights_Cyan', 'beacon', xt, yt, s['z1'] - 0.8, s['z1'], 0.45, n=8)
    acc.cyl('Spire', 'struct_dark', 0, c, zc, zc + 6.0, 3.0, n=16, r1=1.0)
    for zz in (zc + 1.0, zc + 3.0, zc + 5.0):
        rr = 3.0 - 2.0 * (zz - zc) / 6.0
        acc.cyl('Lights_Cyan', 'strip_cyan', 0, c, zz, zz + 0.2, rr + 0.1, n=16, r1=rr + 0.1, caps=False)
    acc.cyl('Lights_Cyan', 'holo_cyan', 0, c, zc + 6.0, 416.0, 0.8, n=8, r1=0.2)

def plaza(acc):
    g = circle(P.PLAZA_R, 96).difference(Polygon(P.star(0.0)))
    slab(acc, 'Ground', 'plaza', g, -0.6, 0.0)
    # radial light lines in the plaza
    for k in range(P.N_ARMS):
        a = P.arm_angle(k)
        r0 = P.Ro(0) + 6; r1 = P.PLAZA_R - 6
        if k == 0: continue
        acc.bar('Ground', 'strip_cyan', (r0 * math.cos(a), r0 * math.sin(a), 0.03), (r1 * math.cos(a), r1 * math.sin(a), 0.03), 0.4, 0.06)
    # entrance approach strip
    for sx in (-1, 1):
        acc.box('Ground', 'strip_cyan', sx * 9 - 0.2, -P.PLAZA_R + 6, 0.0, sx * 9 + 0.2, -P.Ro(0) - 14, 0.05)
    arc_band(acc, 'Ground', 'strip_amber', P.PLAZA_R - 3, P.PLAZA_R - 2.4, 0, 2 * math.pi, 0.03)
