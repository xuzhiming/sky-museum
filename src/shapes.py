"""Extra primitives on top of geom.Acc (polygon slabs with holes, walls with openings, torus, arcs)."""
import math, numpy as np
import mapbox_earcut as earcut
from shapely.geometry import Polygon, Point, box as sbox
from shapely.ops import unary_union
from shapely import affinity

def circle(r, n=64, cx=0.0, cy=0.0):
    return Polygon([(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)])

def local_rect(O, ang, u0, u1, v0, v1):
    """rectangle in a local frame (origin O, u along angle ang, v = +90deg)"""
    c, s = math.cos(ang), math.sin(ang)
    P = lambda u, v: (O[0] + u * c - v * s, O[1] + u * s + v * c)
    return Polygon([P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)])

def _polys(geom):
    if geom.is_empty: return []
    if geom.geom_type == 'Polygon': return [geom]
    return [g for g in getattr(geom, 'geoms', []) if g.geom_type == 'Polygon']

def slab(acc, group, mat, geom, z0, z1, edge_mat=None, bottom=True, top_mat=None):
    """extrude a shapely (multi)polygon with holes between z0 and z1"""
    for P in _polys(geom):
        P = P.buffer(0)
        if P.is_empty or P.area < 1e-4: continue
        for P in _polys(P):
            rings = [np.array(P.exterior.coords[:-1])] + [np.array(i.coords[:-1]) for i in P.interiors]
            # orientation: exterior CCW, holes CW
            fixed = []
            for k, r in enumerate(rings):
                a = 0.5 * np.sum(r[:, 0] * np.roll(r[:, 1], -1) - np.roll(r[:, 0], -1) * r[:, 1])
                if (k == 0 and a < 0) or (k > 0 and a > 0): r = r[::-1]
                fixed.append(r)
            V = np.vstack(fixed)
            ends = np.cumsum([len(r) for r in fixed]).astype(np.uint32)
            tri = earcut.triangulate_float64(V.astype(np.float64), ends).reshape(-1, 3)
            for t in tri:
                a, b, c = V[t[0]], V[t[1]], V[t[2]]
                # earcut returns CW or CCW? enforce: top normal +z
                cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
                if cr < 0: b, c = c, b
                acc.add_face(group, top_mat or mat, [(a[0], a[1], z1), (b[0], b[1], z1), (c[0], c[1], z1)])
                if bottom: acc.add_face(group, mat, [(a[0], a[1], z0), (c[0], c[1], z0), (b[0], b[1], z0)])
            em = edge_mat or mat
            for k, r in enumerate(fixed):
                n = len(r)
                for i in range(n):
                    a, b = r[i], r[(i + 1) % n]
                    # exterior CCW -> outward normal is right of edge; holes CW -> also outward of solid
                    acc.add_face(group, em, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)])

def wall(acc, group, mat, p0, p1, z0, z1, t=0.3):
    if z1 - z0 < 1e-3: return
    zm = (z0 + z1) / 2
    acc.bar(group, mat, (p0[0], p0[1], zm), (p1[0], p1[1], zm), t, z1 - z0)

def wall_open(acc, group, mat, p0, p1, z0, z1, openings, t=0.3):
    """wall p0->p1 with openings [(s0, s1, h)] measured along the wall from p0 (s in metres)."""
    p0 = np.array(p0, float); p1 = np.array(p1, float)
    L = np.linalg.norm(p1 - p0); d = (p1 - p0) / max(L, 1e-9)
    P = lambda s: p0 + d * s
    cur = 0.0
    for s0, s1, h in sorted(openings):
        s0 = max(s0, 0); s1 = min(s1, L)
        if s1 <= s0: continue
        if s0 > cur + 1e-3: wall(acc, group, mat, P(cur), P(s0), z0, z1, t)
        if z0 + h < z1 - 1e-3: wall(acc, group, mat, P(s0), P(s1), z0 + h, z1, t)
        cur = max(cur, s1)
    if cur < L - 1e-3: wall(acc, group, mat, P(cur), P(L), z0, z1, t)

def arc_pts(r, a0, a1, seg_len=3.0, c=(0.0, 0.0)):
    n = max(1, int(math.ceil(abs(a1 - a0) * r / seg_len)))
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]

def arc_wall(acc, group, mat, r, a0, a1, z0, z1, t=0.3, seg_len=3.0, c=(0.0, 0.0)):
    pts = arc_pts(r, a0, a1, seg_len, c)
    for a, b in zip(pts, pts[1:]): wall(acc, group, mat, a, b, z0, z1, t)

def arc_band(acc, group, mat, r0, r1, a0, a1, z, seg_len=2.0, down=False):
    """flat annular band (lights) at height z"""
    n = max(1, int(math.ceil(abs(a1 - a0) * r1 / seg_len)))
    for i in range(n):
        A, B = a0 + (a1 - a0) * i / n, a0 + (a1 - a0) * (i + 1) / n
        q = [(r0 * math.cos(A), r0 * math.sin(A), z), (r1 * math.cos(A), r1 * math.sin(A), z), (r1 * math.cos(B), r1 * math.sin(B), z), (r0 * math.cos(B), r0 * math.sin(B), z)]
        acc.add_face(group, mat, q[::-1] if down else q)

def torus(acc, group, mat, R, r, center, tilt=(0.0, 0.0), n=72, m=10):
    cx, cy, cz = center
    tx, ty = tilt
    def rot(p):
        x, y, z = p
        # tilt about x then y
        y, z = y * math.cos(tx) - z * math.sin(tx), y * math.sin(tx) + z * math.cos(tx)
        x, z = x * math.cos(ty) + z * math.sin(ty), -x * math.sin(ty) + z * math.cos(ty)
        return (cx + x, cy + y, cz + z)
    P = [[rot(((R + r * math.cos(2 * math.pi * j / m)) * math.cos(2 * math.pi * i / n),
               (R + r * math.cos(2 * math.pi * j / m)) * math.sin(2 * math.pi * i / n), r * math.sin(2 * math.pi * j / m))) for j in range(m)] for i in range(n)]
    for i in range(n):
        for j in range(m):
            a, b, c, d = P[i][j], P[(i + 1) % n][j], P[(i + 1) % n][(j + 1) % m], P[i][(j + 1) % m]
            acc.add_face(group, mat, [a, b, c, d])

def arc_ribbon(acc, group, mat, r, a0, a1, z0, z1, seg_len=3.0):
    """vertical single-sided ribbon (light strips) - 2 tris per segment"""
    pts = arc_pts(r, a0, a1, seg_len)
    for a, b in zip(pts, pts[1:]):
        acc.add_face(group, mat, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)])
