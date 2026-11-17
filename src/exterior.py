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
    zs = shell_stations()
    n = 3 * P.N_ARMS
    for a, b in zip(zs, zs[1:]):
        if b - a < 0.05:      # podium setback at 48: horizontal roof ring
            ring = Polygon(P.star(a)).difference(Polygon(P.star(b)))
            slab(acc, 'Podium', 'titanium', ring, a - 0.8, a, edge_mat='strip_cyan')
            continue
        A, B = star_at(a), star_at(b)
        podium = b <= 48.0 + 1e-6
        for i in range(n):
            j = (i + 1) % n
            pa0, pa1, pb0, pb1 = A[i], A[j], B[i], B[j]
            kind = i % 3          # 0 tip face, 1 tip->valley, 2 valley->tip
            if podium:
                if i == 0:        # front arm tip: entrance portal (full 48 m opening)
                    L = math.dist(pa0, pa1); f0 = (L - P.ENTRANCE_W) / 2 / L
                    for (s0, s1) in ((0, f0), (1 - f0, 1)):
                        acc.add_face('Podium', 'titanium', [(*lerp(pa0, pa1, s0), a), (*lerp(pa0, pa1, s1), a), (*lerp(pb0, pb1, s1), b), (*lerp(pb0, pb1, s0), b)])
                    continue
                acc.add_face('Podium', 'titanium', [(*pa0, a), (*pa1, a), (*pb1, b), (*pb0, b)])
            else:
                acc.add_face('Shell_Glass', 'glass_curtain', [(*pa0, a), (*pa1, a), (*pb1, b), (*pb0, b)])
                # vertical mullions
                L = math.dist(pa0, pa1); nm = max(1, int(L / 7.0))
                for m in range(1, nm):
                    t = m / nm
                    p0, p1 = lerp(pa0, pa1, t), lerp(pb0, pb1, t)
                    acc.bar('Shell_Frame', 'frame_metal', (*p0, a), (*p1, b), 0.35, 0.5)
            # horizontal floor band (every station) + warm floor-edge line seen through the glass
            acc.bar('Shell_Frame', 'frame_metal', (*pa0, a), (*pa1, a), 0.9 if not podium else 0.5, 0.6)
            if not podium:
                s0 = np.array(pa0) * (1 - 0.8 / np.linalg.norm(pa0)); s1 = np.array(pa1) * (1 - 0.8 / np.linalg.norm(pa1))
                acc.add_face('Lights_Amber', 'strip_amber_soft', [(*s0, a + 0.05), (*s1, a + 0.05), (*s1, a + 0.45), (*s0, a + 0.45)])
        # vertex ribs: arm tips (cyan strip) and valleys
        for i in range(n):
            kind = i % 3
            p0, p1 = A[i], B[i]
            if kind in (0, 1):
                acc.bar('Shell_Frame', 'frame_dark', (*p0, a), (*p1, b), 1.6, 1.6)
                if not podium:
                    # cyan light strip slightly outward of the rib
                    c0 = np.array(p0) * (1 + 0.9 / max(np.linalg.norm(p0), 1)); c1 = np.array(p1) * (1 + 0.9 / max(np.linalg.norm(p1), 1))
                    acc.bar('Lights_Cyan', 'strip_cyan', (*c0, a), (*c1, b), 0.45, 0.45)
            else:
                acc.bar('Shell_Frame', 'frame_dark', (*p0, a), (*p1, b), 1.0, 1.0)
                if not podium and P.VALLEY_STRIPS:
                    c0 = np.array(p0) * (1 + 0.6 / max(np.linalg.norm(p0), 1)); c1 = np.array(p1) * (1 + 0.6 / max(np.linalg.norm(p1), 1))
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
    """large media screens on podium side faces (sheet: big LED screens on the base)"""
    S = P.star(0); S48 = P.star(47.0)
    n = 3 * P.N_ARMS
    picks = [(1, 'screen_a'), (n - 1, 'screen_b'), (4, 'screen_c'), (n - 4, 'screen_d'), (7, 'screen_b'), (n - 7, 'screen_a'), (10, 'screen_c'), (n - 10, 'screen_d')]
    for i, mat in picks:
        j = (i + 1) % n
        z0, z1 = P.SCREEN_Z
        def pt(t, z):
            f = z / 47.0
            a = lerp(S[i], S48[i], f); b = lerp(S[j], S48[j], f)
            p = np.array(lerp(a, b, t))
            nrm = np.array([b[1] - a[1], -(b[0] - a[0])]); nrm /= np.linalg.norm(nrm)
            return (*(p + nrm * 0.5), z)
        t0, t1 = 0.12, 0.88
        acc.add_face('Screens', mat, [pt(t0, z0), pt(t1, z0), pt(t1, z1), pt(t0, z1)])
        # frame
        for (ta, za, tb, zb) in ((t0, z0, t1, z0), (t0, z1, t1, z1), (t0, z0, t0, z1), (t1, z0, t1, z1)):
            acc.bar('Shell_Frame', 'frame_dark', pt(ta, za), pt(tb, zb), 0.8, 0.8)

def portal(acc):
    """48 m main entrance portal at the south arm tip + recessed glass curtain with doors"""
    y0 = -P.Ro(0.0); W = P.ENTRANCE_W; H = P.ENTRANCE_H; rec = P.ENTRANCE_RECESS
    # jambs / returns
    for sx in (-1, 1):
        x = sx * W / 2
        acc.box('Portal', 'titanium', (x - 0.6) if sx < 0 else x, y0, 0, x if sx < 0 else (x + 0.6), y0 + rec, H)
        # projecting frame fins with cyan inner strip
        acc.box('Portal', 'frame_dark', x - 1.5 + sx * 1.5, y0 + 0.05, 0, x + 1.5 + sx * 1.5, y0 + 1.5, H)
        acc.box('Lights_Cyan', 'strip_cyan', x - 0.25, y0 + 0.0, 0.2, x + 0.25, y0 + 0.1, H - 0.5)
    acc.box('Portal', 'frame_dark', -W / 2 - 3.0, y0 + 0.05, H - 3.0, W / 2 + 3.0, y0 + 1.5, H)   # lintel fascia (flush, inside the 360 m envelope)
    acc.box('Lights_Cyan', 'strip_cyan', -W / 2, y0 + 0.0, H - 3.4, W / 2, y0 + 0.1, H - 3.0)
    acc.box('Lights_Amber', 'strip_amber', -W / 2, y0 + 1.5, H - 3.2, W / 2, y0 + rec - 0.3, H - 3.0)          # soffit glow
    # recessed curtain wall with door opening
    yc = y0 + rec
    dw, dh = P.DOOR_W, P.DOOR_H
    for (x0, x1, z0, z1) in ((-W / 2, -dw / 2, 0, H), (dw / 2, W / 2, 0, H), (-dw / 2, dw / 2, dh, H)):
        acc.box('Entrance_Glass', 'glass_clear', x0, yc - 0.1, z0, x1, yc + 0.1, z1)
    for x in np.linspace(-W / 2, W / 2, 7):
        acc.box('Shell_Frame', 'frame_metal', x - 0.2, yc - 0.4, 0, x + 0.2, yc + 0.2, H)
    for z in (dh, 16.0, 26.0, 36.0, 46.0):
        acc.box('Shell_Frame', 'frame_metal', -W / 2, yc - 0.4, z - 0.2, W / 2, yc + 0.2, z + 0.2)
    # canopy + sign screen
    acc.box('Portal', 'frame_dark', -W / 2, y0 + 1.5, 10.0, W / 2, y0 + rec - 0.3, 10.8)        # inner canopy (inside the recess)
    acc.box('Lights_Cyan', 'strip_cyan', -W / 2, y0 + 1.45, 10.0, W / 2, y0 + 1.55, 10.8)
    acc.add_face('Screens', 'screen_sign', [(-12, yc - 0.35, 30), (12, yc - 0.35, 30), (12, yc - 0.35, 40), (-12, yc - 0.35, 40)])

def fans(acc):
    """diagonal fan wings L1-L5: annular sectors (outer arc follows Ro(z)) lofted up to FAN z1, titanium + glass bands"""
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
            A, B = ring(za), ring(zb); n = len(A)
            for i in range(m):    # outer arc faces
                mat = 'titanium' if zb <= 48.0 + 1e-6 else 'glass_curtain'
                acc.add_face('Fans', mat, [(*A[i], za), (*A[i + 1], za), (*B[i + 1], zb), (*B[i], zb)])
            for (i, j) in ((m, m + 1), (2 * m + 1, 0)):   # side faces
                acc.add_face('Fans', 'titanium', [(*A[i], za), (*A[j], za), (*B[j], zb), (*B[i], zb)])
            for i in range(m):
                acc.bar('Shell_Frame', 'frame_metal', (*A[i], za), (*A[i + 1], za), 0.8, 0.6)
                acc.add_face('Lights_Amber', 'strip_amber_soft', [(A[i][0] * 0.997, A[i][1] * 0.997, za + 0.6), (A[i + 1][0] * 0.997, A[i + 1][1] * 0.997, za + 0.6), (A[i + 1][0] * 0.997, A[i + 1][1] * 0.997, za + 1.0), (A[i][0] * 0.997, A[i][1] * 0.997, za + 1.0)]) if za > 0 else None
        T = ring(f['z1'])
        slab(acc, 'Fans', 'titanium', Polygon(T), f['z1'] - 0.8, f['z1'], edge_mat='strip_cyan_soft')
        for i in range(m + 1):
            acc.bar('Shell_Frame', 'frame_dark', (*ring(0)[i], 0.0), (*T[i], f['z1']), 1.2, 1.2) if i in (0, m) else None

def pods(acc):
    """3 saucer pods (exterior sheet) docked to tower floors: deck disc + conical underside + glass rail + pavilion + neck bridge"""
    from shapes import arc_wall
    FL = {n: z for n, z, h, p in P.floors()}
    for o in P.PODS:
        z = o['z']; R = o['R']; x, y = o['x'], o['y']; t = o['t']
        disc = circle(R, 72, x, y).difference(Polygon(P.star(z, inset=-0.3)))
        slab(acc, 'Pods', 'titanium', disc, z - t, z, edge_mat='strip_cyan_soft')
        n = 48; zb = z - t - R * 0.32; rb = R * 0.4
        for i in range(n):
            A, B = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            q = [(x + R * math.cos(A), y + R * math.sin(A), z - t), (x + R * math.cos(B), y + R * math.sin(B), z - t),
                 (x + rb * math.cos(B), y + rb * math.sin(B), zb), (x + rb * math.cos(A), y + rb * math.sin(A), zb)]
            acc.add_face('Pods', 'frame_dark', q[::-1])
        acc.cyl('Pods', 'frame_dark', x, y, zb - 0.5, zb, rb, n=24, r1=rb)
        arc_band(acc, 'Lights_Cyan', 'strip_cyan', R - 1.6, R - 0.8, 0, 2 * math.pi, z - t - 0.05, down=True)
        arc_wall(acc, 'Rails', 'rail_glass', R - 0.4, 0, 2 * math.pi, z, z + 1.3, t=0.06, seg_len=4.0, c=(x, y))
        arc_wall(acc, 'Shell_Frame', 'frame_metal', R - 0.4, 0, 2 * math.pi, z + 1.25, z + 1.4, t=0.15, seg_len=4.0, c=(x, y))
        arc_wall(acc, 'Shell_Glass', 'glass_curtain', R * 0.45, 0, 2 * math.pi, z, z + 6.0, t=0.1, seg_len=4.0, c=(x, y))
        acc.cyl('Pods', 'titanium', x, y, z + 6.0, z + 6.8, R * 0.47, n=32, r1=R * 0.3)
        c = (0.0, P.yc(z)); d = math.hypot(x - c[0], y - c[1]); ux, uy = (x - c[0]) / d, (y - c[1]) / d
        p0 = (c[0] + ux * P.Ri(z) * 0.6, c[1] + uy * P.Ri(z) * 0.6); p1 = (x - ux * R * 0.5, y - uy * R * 0.5)
        w = 5.0; nx, ny = -uy * w, ux * w
        acc.hexa('Pods', 'titanium', [(p0[0] - nx, p0[1] - ny, z - t), (p1[0] - nx, p1[1] - ny, z - t), (p0[0] + nx, p0[1] + ny, z - t), (p1[0] + nx, p1[1] + ny, z - t),
                                     (p0[0] - nx, p0[1] - ny, z), (p1[0] - nx, p1[1] - ny, z), (p0[0] + nx, p0[1] + ny, z), (p1[0] + nx, p1[1] + ny, z)])
        acc.bar('Lights_Cyan', 'strip_cyan', (p0[0], p0[1], z - t - 0.1), (p1[0], p1[1], z - t - 0.1), 0.6, 0.1)

def obs_rings(acc):
    """slim observation ring decks at +320/+360/+400 (sheet labels), glass balustrade + under-glow"""
    from shapes import arc_wall
    for o in P.OBS:
        z = o['z']; c = (0.0, P.yc(z)); R = P.Ro(z) + o['cant']
        disc = circle(R, 96, *c).difference(Polygon(P.star(z, inset=-0.2)))
        slab(acc, 'Obs_Decks', 'titanium', disc, z - o['t'], z, edge_mat='strip_cyan_soft')
        arc_band(acc, 'Lights_Cyan', 'strip_cyan', R - 1.6, R - 0.9, 0, 2 * math.pi, z - o['t'] - 0.05, down=True) if c == (0.0, 0.0) else None
        arc_wall(acc, 'Rails', 'rail_glass', R - 0.4, 0, 2 * math.pi, z, z + 1.3, t=0.06, seg_len=4.0, c=c)
        arc_wall(acc, 'Shell_Frame', 'frame_metal', R - 0.4, 0, 2 * math.pi, z + 1.25, z + 1.35, t=0.15, seg_len=4.0, c=c)
        arc_wall(acc, 'Lights_Cyan', 'strip_cyan', R + 0.05, 0, 2 * math.pi, z - o['t'] + 0.3, z - o['t'] + 0.7, t=0.05, seg_len=4.0, c=c)

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
    slab(acc, 'Spire', 'titanium', Polygon(star_at(zc)), zc - 0.8, zc)
    s = P.SPIRE
    for sx in (-1, 1):     # twin needle blades
        x0 = sx * s['x']; y0 = P.yc(s['z0'])
        w, d = s['w0'] / 2, s['d0'] / 2
        q = [(x0 - w, y0 - d, s['z0']), (x0 + w, y0 - d, s['z0']), (x0 - w, y0 + d, s['z0']), (x0 + w, y0 + d, s['z0'])]
        xt, yt = x0 * 0.85, P.yc(s['z1'])
        t = [(xt - 0.3, yt - 0.4, s['z1']), (xt + 0.3, yt - 0.4, s['z1']), (xt - 0.3, yt + 0.4, s['z1']), (xt + 0.3, yt + 0.4, s['z1'])]
        acc.hexa('Spire', 'titanium', q + t)
        acc.bar('Lights_Cyan', 'strip_cyan', (x0 - sx * w * 1.05, y0 - d * 0.5, s['z0']), (xt - sx * 0.35, yt, s['z1'] - 1.0), 0.3, 0.3)
        acc.cyl('Lights_Cyan', 'beacon', xt, yt, s['z1'] - 0.8, s['z1'], 0.45, n=8)
    acc.cyl('Spire', 'frame_dark', 0, c, zc, zc + 6.0, 3.0, n=12, r1=1.0)
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
