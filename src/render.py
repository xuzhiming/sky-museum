import sys, os, math, argparse, time
import bpy
from mathutils import Vector
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
# orthographic elevation cameras. Scene: front = -Y side. ortho_scale covers 460 m.
ORTHO = {   # name: (location, rotation_deg, ortho_scale, res)
    'front': ((0, -1000, 215), (90, 0, 0), 460, (1380, 1380)),
    'back':  ((0, 1000, 215), (90, 0, 180), 460, (1380, 1380)),
    'left':  ((-1000, 0, 215), (90, 0, -90), 460, (1380, 1380)),
    'right': ((1000, 0, 215), (90, 0, 90), 460, (1380, 1380)),
    'top':   ((0, 0, 1000), (0, 0, 0), 460, (1380, 1380)),
    'section': ((0, -1000, 215), (90, 0, 0), 460, (1380, 1380)),
}
PXM = 1380 / 460.0      # 3 px / m
MASK_HIDE = ['Ground', 'Lights_Amber']

def setup(samples=32, res=(1600, 900), transparent=False):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True
    try:
        sc.cycles.device = 'CPU'
    except Exception: pass
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy' if False else 'None'
    sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 64
    return sc

def world(sc, col=(0.006, 0.008, 0.02), strength=1.0):
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    sky = w.node_tree.nodes.new('ShaderNodeTexGradient'); mp = w.node_tree.nodes.new('ShaderNodeMapping'); tc = w.node_tree.nodes.new('ShaderNodeTexCoord')
    ramp = w.node_tree.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.03, 0.02, 0.06, 1); ramp.color_ramp.elements[1].color = (0.002, 0.004, 0.012, 1)
    w.node_tree.links.new(tc.outputs['Window'], mp.inputs['Vector']); mp.inputs['Rotation'].default_value = (0, 0, math.radians(90))
    w.node_tree.links.new(mp.outputs['Vector'], sky.inputs['Vector']); w.node_tree.links.new(sky.outputs['Fac'], ramp.inputs['Fac'])
    w.node_tree.links.new(ramp.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = strength

def camera(loc, rot=None, target=None, lens=35, ortho=None):
    cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.lens = lens
    cd.clip_end = 5000; cd.clip_start = 0.05
    if rot: cam.rotation_euler = [math.radians(a) for a in rot]
    if target:
        d = Vector(target) - Vector(loc); cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    return cam

def light(kind, loc, energy, col=(1, 1, 1), size=1.0, rot=None):
    ld = bpy.data.lights.new('L', kind); ld.energy = energy; ld.color = col
    if hasattr(ld, 'shadow_soft_size'): ld.shadow_soft_size = size
    ob = bpy.data.objects.new('L', ld); bpy.context.scene.collection.objects.link(ob); ob.location = loc
    if rot: ob.rotation_euler = [math.radians(a) for a in rot]

def mask_override():
    m = bpy.data.materials.new('mask'); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (1, 1, 1, 1); e.inputs['Strength'].default_value = 1
    o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0], o.inputs[0])
    for ob in bpy.data.objects:
        if ob.type != 'MESH': continue
        if ob.name in MASK_HIDE: ob.hide_render = True; continue
        ob.data.materials.clear(); ob.data.materials.append(m)

def clip_y(value):
    """section: hide everything in front of y=value (keep y > value), cut faces shown as poche"""
    for m in bpy.data.materials:
        if not m.use_nodes: continue
        nt = m.node_tree
        bsdf = nt.nodes.get('Principled BSDF')
        is_clear = m.name.startswith(('glass', 'rail_glass', 'strip', 'light', 'screen'))
        out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
        link = out.inputs['Surface'].links[0]; srcsock = link.from_socket
        geo = nt.nodes.new('ShaderNodeNewGeometry'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        cmp_ = nt.nodes.new('ShaderNodeMath'); cmp_.operation = 'LESS_THAN'; cmp_.inputs[1].default_value = value
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        pm = nt.nodes.new('ShaderNodeEmission'); pm.inputs['Color'].default_value = (0.95, 0.45, 0.12, 1); pm.inputs['Strength'].default_value = 0.9; pm.inputs['Color'].default_value = (0.9, 0.42, 0.1, 1)
        mixb = nt.nodes.new('ShaderNodeMixShader'); mixc = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(geo.outputs['Position'], sep.inputs['Vector']); nt.links.new(sep.outputs['Y'], cmp_.inputs[0])
        nt.links.new(geo.outputs['Backfacing'], mixb.inputs['Fac']) if not is_clear else setattr(mixb.inputs['Fac'], 'default_value', 0.0)
        nt.links.new(srcsock, mixb.inputs[1]); nt.links.new(pm.outputs['Emission'], mixb.inputs[2])
        nt.links.new(cmp_.outputs[0], mixc.inputs['Fac']); nt.links.new(mixb.outputs[0], mixc.inputs[1]); nt.links.new(tr.outputs[0], mixc.inputs[2])
        nt.links.new(mixc.outputs[0], out.inputs['Surface'])

def render_to(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.context.scene.render.filepath = path; bpy.ops.render.render(write_still=True)

def city(sc):
    """low context blocks (render only, never exported)"""
    import random; random.seed(3)
    me = bpy.data.meshes.new('ctx'); verts = []; faces = []
    for i in range(260):
        a = random.uniform(0, 2 * math.pi); r = random.uniform(330, 1400)
        da = (a - math.radians(-124) + math.pi) % (2 * math.pi) - math.pi
        if abs(da) < math.radians(28) and r < 1100: continue
        da2 = (a - math.radians(-80) + math.pi) % (2 * math.pi) - math.pi
        if abs(da2) < math.radians(20) and r < 700: continue
        x, y = r * math.cos(a), r * math.sin(a); w = random.uniform(20, 60); d = random.uniform(20, 60); h = random.uniform(20, 160) * (1.4 if r > 700 else 0.8)
        o = len(verts)
        verts += [(x, y, 0), (x + w, y, 0), (x + w, y + d, 0), (x, y + d, 0), (x, y, h), (x + w, y, h), (x + w, y + d, h), (x, y + d, h)]
        faces += [(o, o + 1, o + 5, o + 4), (o + 1, o + 2, o + 6, o + 5), (o + 2, o + 3, o + 7, o + 6), (o + 3, o, o + 4, o + 7), (o + 4, o + 5, o + 6, o + 7)]
    me.from_pydata(verts, [], faces); ob = bpy.data.objects.new('Context', me); sc.collection.objects.link(ob)
    m = bpy.data.materials.new('ctx'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.02, 0.025, 0.04, 1); b.inputs['Emission Color'].default_value = (0.3, 0.5, 1.0, 1); b.inputs['Emission Strength'].default_value = 0.02
    me.materials.append(m)
    g = bpy.data.meshes.new('gnd'); g.from_pydata([(-3000, -3000, -0.7), (3000, -3000, -0.7), (3000, 3000, -0.7), (-3000, 3000, -0.7)], [], [(0, 1, 2, 3)])
    go = bpy.data.objects.new('GroundCtx', g); sc.collection.objects.link(go)
    gm = bpy.data.materials.new('gctx'); gm.use_nodes = True; gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.01, 0.012, 0.02, 1)
    gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.3
    g.materials.append(gm)

def run(views, tag, samples, scale):
    for v in views:
        bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, 'model.blend'))
        t0 = time.time()
        if v.endswith('_mask'):
            b = v[:-5]; loc, rot, osc, res = ORTHO[b]
            sc = setup(samples=1, res=res); sc.cycles.use_denoising = False
            sc.view_settings.view_transform = 'Standard'
            world(sc, strength=0.0); mask_override()
            camera(loc, rot=rot, ortho=osc)
            render_to(os.path.join(OUT, 'renders/ortho/%s_%s.png' % (v, tag)))
        elif v in ORTHO:
            loc, rot, osc, res = ORTHO[v]
            sc = setup(samples=samples, res=(int(res[0] * scale), int(res[1] * scale)))
            world(sc, strength=1.0)
            if v == 'section': clip_y(0.0)
            light('SUN', (0, 0, 500), 0.6, (0.6, 0.7, 1.0), rot=(50, 0, 30))
            camera(loc, rot=rot, ortho=osc)
            render_to(os.path.join(OUT, 'renders/ortho/%s_%s.png' % (v, tag)))
        elif v == 'hero':
            sc = setup(samples=samples, res=(int(1920 * scale), int(1080 * scale)))
            world(sc, strength=1.0); city(sc)
            light('SUN', (0, 0, 500), 0.25, (0.5, 0.6, 1.0), rot=(60, 0, -40))
            light('AREA', (0, -300, 5), 4e6, (0.3, 0.8, 1.0), size=200, rot=(70, 0, 0))
            camera((-520, -760, 120), target=(0, 0, 175), lens=34)
            render_to(os.path.join(OUT, 'renders/hero_night_%s.png' % tag))
        elif v == 'hero2':
            sc = setup(samples=samples, res=(int(1920 * scale), int(1080 * scale)))
            world(sc, strength=1.0); city(sc)
            light('SUN', (0, 0, 500), 0.25, (0.5, 0.6, 1.0), rot=(60, 0, -40))
            camera((60, -330, 6), target=(0, -150, 60), lens=22)
            render_to(os.path.join(OUT, 'renders/entrance_night_%s.png' % tag))
        elif v == 'atrium':
            sc = setup(samples=samples, res=(int(1920 * scale), int(1080 * scale)))
            world(sc, strength=0.5)
            for z in (12, 40, 90, 160): light('POINT', (0, 0, z), 3e4, (1.0, 0.75, 0.45), size=3)
            light('POINT', (0, 0, 34), 1.5e4, (1.0, 0.6, 0.2), size=6)
            light('POINT', (0, -30, 8), 6e4, (0.4, 0.8, 1.0), size=2)
            camera((6, -42, 1.7), target=(0, 0, 60), lens=14)
            render_to(os.path.join(OUT, 'renders/atrium_interior_%s.png' % tag))
        elif v == 'gallery':
            sc = setup(samples=samples, res=(int(1920 * scale), int(1080 * scale)))
            world(sc, strength=0.5)
            z = 128.0
            for r in (60, 80, 100): light('POINT', (r, 0, z + 8), 2e4, (1.0, 0.8, 0.55), size=2)
            camera((49, -3, z + 1.7), target=(110, 4, z + 3.5), lens=16)
            render_to(os.path.join(OUT, 'renders/gallery_L12_%s.png' % tag))
        elif v == 'obs':
            sc = setup(samples=samples, res=(int(1920 * scale), int(1080 * scale)))
            world(sc, strength=1.0); city(sc)
            light('POINT', (0, -40, 330), 1e5, (1.0, 0.75, 0.5), size=3)
            camera((-30, -60, 321.7), target=(40, -120, 315), lens=16)
            render_to(os.path.join(OUT, 'renders/obs_L28_%s.png' % tag))
        elif v == 'cutaway':
            sc = setup(samples=samples, res=(int(1920 * scale), int(1080 * scale)))
            world(sc, strength=1.0); clip_y(0.0)
            light('SUN', (0, 0, 500), 2.2, (0.85, 0.88, 1.0), rot=(55, 0, 20))
            for z in (12, 60, 160, 260): light('POINT', (0, 10, z), 6e4, (1.0, 0.8, 0.6), size=3)
            camera((-420, -620, 260), target=(0, 0, 190), lens=38)
            render_to(os.path.join(OUT, 'renders/section_cutaway_%s.png' % tag))
        print(v, 'done', round(time.time() - t0, 1), 's', flush=True)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--views', required=True); ap.add_argument('--tag', default='r1')
    ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0)
    a = ap.parse_args()
    run(a.views.split(','), a.tag, a.samples, a.scale)
