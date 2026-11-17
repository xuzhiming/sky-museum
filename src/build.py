import sys, os, math, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from geom import Acc
import exterior, interior, mats, params as P

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

def make_acc():
    acc = Acc()
    exterior.build_exterior(acc)
    spec = {} if os.environ.get('SKY_EXT_ONLY') else interior.build_interior(acc)
    return acc, spec

def to_blender(acc):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cache = {}
    def getmat(n):
        if n not in cache: cache[n] = mats.make_material(n)
        return cache[n]
    for gname, gm in acc.g.items():
        verts, faces, midx, mlist = [], [], [], list(gm.keys())
        for mi, mname in enumerate(mlist):
            v, f = gm[mname]; o = len(verts); verts.extend(v)
            faces.extend([tuple(i + o for i in q) for q in f]); midx.extend([mi] * len(f))
        mesh = bpy.data.meshes.new(gname); mesh.from_pydata(verts, [], faces); mesh.update()
        for mn in mlist: mesh.materials.append(getmat(mn))
        mesh.polygons.foreach_set('material_index', midx)
        V = np.array(verts, dtype=np.float32)
        uvl = mesh.uv_layers.new(name='UVMap'); uvs = np.zeros((len(mesh.loops), 2), dtype=np.float32)
        for p in mesh.polygons:
            pts = V[list(p.vertices)]; mn = mlist[midx[p.index]]
            n = np.array(p.normal); ax = int(np.argmax(np.abs(n)))
            if mn.startswith(('screen', 'art_')):
                # oriented quad mapping: u along first edge, v up
                e = pts[1] - pts[0]; e /= max(np.linalg.norm(e), 1e-9)
                up = np.cross(n, e); u = (pts - pts[0]) @ e; w = (pts - pts[0]) @ up
                uv = np.stack([(u - u.min()) / max(np.ptp(u), 1e-6), (w - w.min()) / max(np.ptp(w), 1e-6)], 1)
                uvs[p.loop_start:p.loop_start + p.loop_total] = uv; continue
            sc = mats.MATS[mn][6]
            uv = pts[:, [1, 2]] if ax == 0 else (pts[:, [0, 2]] if ax == 1 else pts[:, [0, 1]])
            uvs[p.loop_start:p.loop_start + p.loop_total] = uv / sc
        uvl.data.foreach_set('uv', uvs.ravel())
        ob = bpy.data.objects.new(gname, mesh); bpy.context.scene.collection.objects.link(ob)

if __name__ == '__main__':
    t0 = time.time()
    acc, spec = make_acc()
    print('tris', acc.stats(), acc.tri_by_group())
    to_blender(acc)
    if os.environ.get('SKY_BLEND'):
        bpy.ops.wm.save_as_mainfile(filepath=os.environ['SKY_BLEND']); sys.exit(0)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'model.blend'))
    json.dump(dict(tris=acc.stats(), by_group=acc.tri_by_group()), open(os.path.join(OUT, 'tri_stats.json'), 'w'), indent=1)
    json.dump(spec, open(os.path.join(OUT, 'circulation_spec.json'), 'w'))
    print('built in', round(time.time() - t0, 1))
