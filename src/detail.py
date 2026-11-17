"""facade detail modules (sheet_exterior 'Facade Modules' + 'Detail Nodes'):
M1 main frame / layered structural ribs, M2 display curtain wall, M3 platform ring module, M4 angled-cut armor panels,
M5 vertical light-strip module, M6 entrance portal frame; node A rib joint, node B cantilever / bracket / light band, node C mullions."""
import math, numpy as np

def _h(*a):
    """deterministic hash -> [0,1)"""
    x = 0
    for v in a: x = (x * 1000003 + int(round(v * 10))) & 0xFFFFFFFF
    x ^= x >> 13; x = (x * 0x5bd1e995) & 0xFFFFFFFF; x ^= x >> 15
    return (x & 0xFFFF) / 65536.0

def bil(P00, P10, P01, P11, u, v):
    return (P00 * (1 - u) + P10 * u) * (1 - v) + (P01 * (1 - u) + P11 * u) * v

def quad_normal(P00, P10, P01, outward_xy):
    n = np.cross(P10 - P00, P01 - P00); n /= max(np.linalg.norm(n), 1e-9)
    if np.dot(n[:2], outward_xy) < 0: n = -n
    return n

def panels(acc, g, mats, P00, P10, P01, P11, outward_xy, cw=4.5, ch=4.0, gap=0.14, depth=0.32, bev=0.22, u0=0.0, u1=1.0, v0=0.0, v1=1.0,
           angled=False, seed=0.0):
    """panelised cladding on the quad (u: P00->P10, v: P00->P01): chamfered panels (bevelled edge + seam gap).
    angled=True (M4 armor): alternate panels are tilted (one edge proud) for the angled-cut look."""
    P00, P10, P01, P11 = map(lambda p: np.array(p, float), (P00, P10, P01, P11))
    W = np.linalg.norm(P10 - P00) * (u1 - u0); H = np.linalg.norm(P01 - P00) * (v1 - v0)
    nu = max(1, int(round(W / cw))); nv = max(1, int(round(H / ch)))
    n = quad_normal(P00, P10, P01, outward_xy)
    du = (u1 - u0) / nu; dv = (v1 - v0) / nv
    Lu = np.linalg.norm(P10 - P00) + 1e-9; Lv = np.linalg.norm(P01 - P00) + 1e-9
    gu, gv = gap / Lu, gap / Lv; bu, bv = bev / Lu, bev / Lv
    for i in range(nu):
        for j in range(nv):
            ua, ub = u0 + i * du + gu, u0 + (i + 1) * du - gu
            va, vb = v0 + j * dv + gv, v0 + (j + 1) * dv - gv
            if ub <= ua or vb <= va: continue
            base = [bil(P00, P10, P01, P11, a, b) for a, b in ((ua, va), (ub, va), (ub, vb), (ua, vb))]
            r = _h(seed, i, j)
            d0 = depth * (0.85 + 0.3 * r)
            if angled == 'blade':   # M4 stepped blades: every column tilts the same way (one vertical edge proud) -> sawtooth plates
                r = _h(seed, i); d0 = depth * (0.85 + 0.3 * r)
                dd = [d0 * 0.25, d0 * 1.7, d0 * 1.7, d0 * 0.25]
            elif angled:
                k = (i + j) % 3
                dd = [d0, d0, d0, d0]
                if k == 1: dd = [d0 * 0.4, d0 * 2.2, d0 * 2.2, d0 * 0.4]
                elif k == 2: dd = [d0 * 0.4, d0 * 0.4, d0 * 2.0, d0 * 2.0]
            else:
                dd = [d0] * 4
            ins = [(ua + bu, va + bv), (ub - bu, va + bv), (ub - bu, vb - bv), (ua + bu, vb - bv)]
            top = [bil(P00, P10, P01, P11, a, b) + n * dd[q] for q, (a, b) in enumerate(ins)]
            m = mats[int(r * len(mats)) % len(mats)]
            faces = [[tuple(t) for t in top]] + [[tuple(base[q]), tuple(base[(q + 1) % 4]), tuple(top[(q + 1) % 4]), tuple(top[q])] for q in range(4)]
            ctr = np.mean(base, 0) - n * 1.0
            acc.add_faces_oriented(g, m, faces, ctr)

def mullion_grid(acc, P00, P10, P01, P11, outward_xy, du=3.6, transoms=(0.5,), u0=0.0, u1=1.0, w=0.22, d=0.55, g='Shell_Frame', mat='frame_metal'):
    """node C: curtain-wall mullions (vertical) + transoms on the glass quad, projecting outward"""
    P00, P10, P01, P11 = map(lambda p: np.array(p, float), (P00, P10, P01, P11))
    n = quad_normal(P00, P10, P01, outward_xy) * (d / 2)
    L = np.linalg.norm(P10 - P00) * (u1 - u0); k = max(1, int(L / du))
    for m in range(1, k):
        u = u0 + (u1 - u0) * m / k
        acc.bar(g, mat, bil(P00, P10, P01, P11, u, 0) + n, bil(P00, P10, P01, P11, u, 1) + n, w, d)
    for v in transoms:
        acc.bar(g, mat, bil(P00, P10, P01, P11, u0, v) + n, bil(P00, P10, P01, P11, u1, v) + n, w * 0.8, d * 0.7)

def rib(acc, p0, p1, outward_xy, depth=2.6, cyan=True, g='Shell_Frame'):
    """M1 / node A: layered structural rib on an arm-tip edge: dark core + titanium fin + cyan strip on the fin edge"""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    o = np.array([outward_xy[0], outward_xy[1], 0.0]); o /= max(np.linalg.norm(o), 1e-9)
    acc.bar(g, 'struct_dark', p0, p1, 1.8, 1.8)
    acc.bar(g, 'ti_armor', p0 + o * depth * 0.5, p1 + o * depth * 0.5, 0.9, depth)
    if cyan:
        acc.bar('Lights_Cyan', 'strip_cyan', p0 + o * (depth + 0.05), p1 + o * (depth + 0.05), 0.55, 0.3)

def rib_joint(acc, p, outward_xy, s=1.0):
    """node A: rib / bracing joint plate at a floor station"""
    p = np.array(p, float); o = np.array([outward_xy[0], outward_xy[1], 0.0]); o /= max(np.linalg.norm(o), 1e-9)
    acc.bar('Shell_Frame', 'struct_dark', p - np.array([0, 0, 0.9 * s]) + o * 0.3, p + np.array([0, 0, 0.9 * s]) + o * 0.3, 3.2 * s, 2.0 * s)
    acc.bar('Shell_Frame', 'brushed', p - np.array([0, 0, 0.35 * s]) + o * 1.4, p + np.array([0, 0, 0.35 * s]) + o * 1.4, 2.2 * s, 0.25)

def ring_module(acc, c, R, z, t, posts=3.0, brackets=10.0, r_in=None, g='Obs_Decks', bracket_depth=None):
    """M3 / node B: platform ring fascia + cyan light band, glass balustrade with posts and top rail, under-deck radial brackets,
    concentric underside light rings"""
    from shapes import arc_wall, arc_band
    cx, cy = c
    n = int(2 * math.pi * R / posts)
    for i in range(n):
        a = 2 * math.pi * i / n
        p = (cx + (R - 0.5) * math.cos(a), cy + (R - 0.5) * math.sin(a))
        acc.bar('Rails', 'brushed', (*p, z), (*p, z + 1.25), 0.12, 0.12)
    arc_wall(acc, 'Rails', 'rail_glass', R - 0.5, 0, 2 * math.pi, z + 0.1, z + 1.15, t=0.04, seg_len=4.0, c=c)
    arc_wall(acc, 'Rails', 'brushed', R - 0.5, 0, 2 * math.pi, z + 1.2, z + 1.32, t=0.12, seg_len=4.0, c=c)
    arc_wall(acc, 'Lights_Cyan', 'strip_cyan', R - 0.45, 0, 2 * math.pi, z + 0.02, z + 0.1, t=0.05, seg_len=4.0, c=c)   # deck-edge LED
    arc_wall(acc, 'Lights_Cyan', 'strip_cyan', R + 0.06, 0, 2 * math.pi, z - t * 0.55, z - t * 0.35, t=0.05, seg_len=4.0, c=c)   # fascia band
    ri = r_in if r_in is not None else R * 0.5
    nb = int(360 / brackets); bd = bracket_depth or min(8.0, (R - ri) * 0.6)
    for i in range(nb):
        a = 2 * math.pi * i / nb; ca, sa = math.cos(a), math.sin(a)
        p_in = (cx + ri * ca, cy + ri * sa); p_out = (cx + (R - 1.2) * ca, cy + (R - 1.2) * sa)
        # triangular bracket: top chord under the deck, diagonal strut back to the wall
        acc.bar(g, 'struct_dark', (*p_in, z - t - 0.3), (*p_out, z - t - 0.3), 0.7, 0.6)
        acc.bar(g, 'struct_dark', (*p_in, z - t - bd), (*p_out, z - t - 0.6), 0.6, 0.6)
        acc.bar(g, 'brushed', (*p_in, z - t - bd - 0.6), (*p_in, z - t), 0.9, 0.9)
    for rr, mat in ((R - 2.5, 'strip_cyan'), (R * 0.78, 'strip_amber'), (R * 0.62, 'strip_cyan_soft')):
        if rr > ri + 1: _arc_band_c(acc, mat, c, rr - 0.35, rr + 0.35, z - t - 0.08)

def _arc_band_c(acc, mat, c, r0, r1, z, seg=2.5):
    n = max(12, int(2 * math.pi * r1 / seg)); cx, cy = c
    g = 'Lights_Cyan' if 'cyan' in mat else 'Lights_Amber'
    for i in range(n):
        A, B = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        q = [(cx + r0 * math.cos(A), cy + r0 * math.sin(A), z), (cx + r1 * math.cos(A), cy + r1 * math.sin(A), z),
             (cx + r1 * math.cos(B), cy + r1 * math.sin(B), z), (cx + r0 * math.cos(B), cy + r0 * math.sin(B), z)]
        acc.add_face(g, mat, q[::-1])

def exo_frame(acc, p0, p1, outward_xy, w=3.4, d=1.9, g='Shell_Frame'):
    """M1 exoskeleton: heavy brushed-titanium box frame on an arm ridge (real depth), gunmetal back plate,
    cyan M5 strip recessed in a channel between two silver lips"""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    o = np.array([outward_xy[0], outward_xy[1], 0.0]); o /= max(np.linalg.norm(o), 1e-9)
    dv = p1 - p0; L = np.linalg.norm(dv)
    if L < 1e-6: return
    s = np.cross(dv / L, o); s /= max(np.linalg.norm(s), 1e-9)
    acc.bar(g, 'ti_armor2', p0 + o * 0.3, p1 + o * 0.3, w + 1.6, 0.6, up=o)                 # back plate
    for sg in (-1, 1):                                                                        # twin silver flanges = channel lips
        acc.bar(g, 'ti_armor', p0 + o * d * 0.5 + s * sg * (w * 0.5 - 0.6), p1 + o * d * 0.5 + s * sg * (w * 0.5 - 0.6), 1.2, d, up=o)
    acc.bar(g, 'struct_dark', p0 + o * d * 0.35, p1 + o * d * 0.35, w - 2.4, d * 0.7, up=o)  # channel floor
    acc.bar('Lights_Cyan', 'strip_cyan', p0 + o * (d * 0.7 + 0.08), p1 + o * (d * 0.7 + 0.08), 0.5, 0.16, up=o)

def joint_plate(acc, p, outward_xy, s=1.0, d=1.9):
    """node A: bolted titanium joint plate clamping the exoskeleton at a floor station (4 bolts)"""
    p = np.array(p, float); o = np.array([outward_xy[0], outward_xy[1], 0.0]); o /= max(np.linalg.norm(o), 1e-9)
    z = np.array([0, 0, 1.0]); sd = np.cross(z, o)
    acc.bar('Shell_Frame', 'ti_armor2', p - z * 1.4 * s + o * (d + 0.15), p + z * 1.4 * s + o * (d + 0.15), 4.6 * s, 0.4, up=o)
    for a in (-1, 1):
        for b in (-1, 1):
            c = p + z * b * 0.95 * s + sd * a * 1.75 * s + o * (d + 0.4)
            acc.bar('Shell_Frame', 'brushed', c - o * 0.1, c + o * 0.15, 0.35 * s, 0.35 * s)

def brace(acc, pa, pb, nrm, off=1.1, w=0.7):
    """diagonal bracing member outside the glass"""
    pa, pb = np.array(pa, float) + nrm * off, np.array(pb, float) + nrm * off
    acc.bar('Shell_Frame', 'brushed', pa, pb, w, w, up=nrm)

def buttress(acc, p0, p1, outward_xy, out=2.4, t=2.2, g='Shell_Frame'):
    """thick triangular metal fin at a base corner: out m proud at z=0, tapering to the facade at z1"""
    p0 = np.array(p0, float); p1 = np.array(p1, float); o = np.array([outward_xy[0], outward_xy[1], 0.0]); o /= max(np.linalg.norm(o), 1e-9)
    sd = np.cross(np.array([0, 0, 1.0]), o) * t * 0.5
    zt = p1 - p0
    # hexa corners c[ix + 2*iy + 4*iz]: ix = inner/outer, iy = side, iz = bottom/top
    c = [p0 - sd, p0 + o * out - sd, p0 + sd, p0 + o * out + sd,
         p0 - sd + zt, p0 + o * 0.25 - sd + zt, p0 + sd + zt, p0 + o * 0.25 + sd + zt]
    acc.hexa(g, 'ti_armor', c)
    acc.bar('Lights_Cyan', 'strip_cyan', p0 + o * (out + 0.05) + np.array([0, 0, 0.5]), p0 + o * 0.3 + zt - np.array([0, 0, 0.5]), 0.3, 0.12)
