import sys, os, math, argparse, time
import bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params as P
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

def light(kind, loc, energy, col=(1, 1, 1), size=1.0, rot=None, target=None, glossy=False):
    ld = bpy.data.lights.new('L', kind); ld.energy = energy; ld.color = col
    if kind == 'AREA': ld.size = size
    elif hasattr(ld, 'shadow_soft_size'): ld.shadow_soft_size = size
    ob = bpy.data.objects.new('L', ld); bpy.context.scene.collection.objects.link(ob); ob.location = loc
    if rot: ob.rotation_euler = [math.radians(a) for a in rot]
    if target: ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    ob.visible_camera = False; ob.visible_glossy = glossy if kind == 'AREA' else True
    return ob

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

def ground(sc, r=1600.0):   # disc fades to transparent 450-1400 m: the far field shows the dark sky gradient (no grey grazing band)
    """clean studio ground: one dark glossy disc under the museum (no context buildings)"""
    n = 96
    vs = [(0, 0, -0.7)] + [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), -0.7) for i in range(n)]
    fs = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    g = bpy.data.meshes.new('gnd'); g.from_pydata(vs, [], fs)
    go = bpy.data.objects.new('GroundStudio', g); sc.collection.objects.link(go)
    gm = bpy.data.materials.new('gstudio'); gm.use_nodes = True; bs = gm.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (0.006, 0.007, 0.012, 1); bs.inputs['Roughness'].default_value = 0.35; bs.inputs['Metallic'].default_value = 0.0; bs.inputs['Specular IOR Level'].default_value = 0.12
    nt = gm.node_tree; outn = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord'); ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 450.0; mr.inputs['From Max'].default_value = 1400.0
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(tc.outputs['Object'], ln.inputs[0]); nt.links.new(ln.outputs['Value'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], mx.inputs[0])
    nt.links.new(bs.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], outn.inputs['Surface'])
    g.materials.append(gm)

def bloom(sc, strength=0.55, threshold=1.2, size=0.62):
    """compositor: bloom / glare for the neon strips"""
    ng = bpy.data.node_groups.new('Comp', 'CompositorNodeTree'); sc.compositing_node_group = ng
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = ng.nodes.new('CompositorNodeRLayers'); gl = ng.nodes.new('CompositorNodeGlare'); out = ng.nodes.new('NodeGroupOutput')
    gl.inputs['Type'].default_value = 'Bloom'; gl.inputs['Quality'].default_value = 'High'
    gl.inputs['Threshold'].default_value = threshold; gl.inputs['Strength'].default_value = strength; gl.inputs['Size'].default_value = size
    ng.links.new(rl.outputs['Image'], gl.inputs['Image']); ng.links.new(gl.outputs['Image'], out.inputs[0])

def night_world(sc, strength=1.0):
    """sheet-style night backdrop for camera rays (screen-space gradient: violet horizon glow -> deep navy), dim navy for lighting"""
    w = bpy.data.worlds.new('Night'); sc.world = w; w.use_nodes = True; nt = w.node_tree
    bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); ramp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(tc.outputs['Window'], sep.inputs['Vector']); nt.links.new(sep.outputs['Y'], ramp.inputs['Fac'])
    el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (0.06, 0.032, 0.10, 1)
    el[1].position = 1.0; el[1].color = (0.004, 0.006, 0.022, 1)
    e = el.new(0.35); e.color = (0.022, 0.024, 0.075, 1)
    lp = nt.nodes.new('ShaderNodeLightPath'); mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['B'].default_value = (0.0, 0.0, 0.0, 1)
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Factor'])
    # lighting / reflection rays: HDRI-ish night dome so the titanium reads silver (bright cool horizon band, warm city glow below, navy zenith)
    tg = nt.nodes.new('ShaderNodeTexCoord'); sg = nt.nodes.new('ShaderNodeSeparateXYZ'); rg = nt.nodes.new('ShaderNodeValToRGB')
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -1.0; mr.inputs['From Max'].default_value = 1.0
    nt.links.new(tg.outputs['Generated'], sg.inputs['Vector']); nt.links.new(sg.outputs['Z'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], rg.inputs['Fac'])
    E = rg.color_ramp.elements
    E[0].position = 0.0; E[0].color = (0.09, 0.05, 0.03, 1)
    E[1].position = 1.0; E[1].color = (0.02, 0.02, 0.05, 1)
    e2 = E.new(0.47); e2.color = (0.30, 0.17, 0.08, 1)
    e3 = E.new(0.52); e3.color = (0.42, 0.34, 0.27, 1)
    e4 = E.new(0.62); e4.color = (0.08, 0.065, 0.11, 1)
    nt.links.new(rg.outputs['Color'], mix.inputs['A'])
    nt.links.new(ramp.outputs['Color'], mix.inputs['B'])
    nt.links.new(mix.outputs['Result'], bg.inputs['Color']); bg.inputs['Strength'].default_value = strength

def uplights(scale=1.0):
    """facade grazing: warm + cyan area uplights at the podium edge and a cool moon key"""
    light('SUN', (0, 0, 500), 0.22, (0.55, 0.65, 1.0), rot=(62, 0, -35))
    for k in range(8):
        a = -math.pi / 2 + k * math.pi / 4 + math.pi / 8
        r = 215.0
        light('AREA', (r * math.cos(a), r * math.sin(a), 2.0), 2.5e5 * scale, (0.45, 0.8, 1.0) if k in (0, 4) else (1.0, 0.66, 0.36), size=60,
              target=(0.5 * r * math.cos(a), 0.5 * r * math.sin(a), 160.0))

def metal_lights(scale=1.0, focus=(0, 0, 150)):
    """rim + key lights so the exoskeleton catches light: two cool rims from behind, one warm key front-left, one top fill"""
    fx, fy, fz = focus
    light('AREA', (fx + 420, fy + 380, fz + 260), 4.5e6 * scale, (1.0, 0.78, 0.56), size=120, target=focus, glossy=True)
    light('AREA', (fx - 420, fy + 380, fz + 200), 2.6e6 * scale, (0.72, 0.84, 1.0), size=120, target=focus, glossy=True)
    light('AREA', (fx - 360, fy - 420, fz + 80), 1.6e6 * scale, (1.0, 0.72, 0.48), size=160, target=focus, glossy=True)
    light('AREA', (fx, fy - 100, fz + 650), 0.15e6 * scale, (0.8, 0.85, 1.0), size=200, target=focus, glossy=False)

def hood_glow(scale=1.0):
    """warm hall light behind the hood glass + key lights on the entrance-hall gold ring + spot on the atrium ring"""
    y0 = -P.Ro(0); E = P.ENTRY_HALL; rc = (0, E['ring_y'], E['ring_z'])
    for sx in (-1, 1): light('AREA', (sx * 22, y0 + 6, 4.0), 4.5e5 * scale, (1.0, 0.7, 0.4), size=10, target=rc)
    light('AREA', (0, E['ring_y'] - 12, 75.0), 4.0e5 * scale, (1.0, 0.75, 0.45), size=24, target=rc)
    light('AREA', (0, E['ring_y'] + 20, 30.0), 1.2e5 * scale, (1.0, 0.6, 0.3), size=20, target=rc)   # back light: gold rim
    for x in (-24, 0, 24): light('POINT', (x, y0 + 14, 28), 7e4 * scale, (1.0, 0.7, 0.4), size=8)
    light('POINT', (0, y0 + 30, 10), 1.2e5 * scale, (1.0, 0.72, 0.42), size=6)
    light('AREA', (0, -30, 6), 2.5e5 * scale, (1.0, 0.75, 0.45), size=20, target=(0, 0, P.ART_RING_Z))

def dof(cam_ob, dist, fstop):
    c = cam_ob.data; c.dof.use_dof = True; c.dof.focus_distance = dist; c.dof.aperture_fstop = fstop

HD = (1920, 1080)
def screen_backs():
    """render-only: exterior LED media screens show a dark back panel when seen from inside (no mirrored art)"""
    for m in bpy.data.materials:
        if m.name not in ('screen_a', 'screen_b', 'screen_c', 'screen_d') or m.get('backs'): continue
        nt = m.node_tree; out = nt.nodes['Material Output']; src = out.inputs['Surface'].links[0].from_socket
        geo = nt.nodes.new('ShaderNodeNewGeometry'); dk = nt.nodes.new('ShaderNodeBsdfDiffuse')
        dk.inputs['Color'].default_value = (0.01, 0.011, 0.013, 1)
        mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(geo.outputs['Backfacing'], mix.inputs[0]); nt.links.new(src, mix.inputs[1]); nt.links.new(dk.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs['Surface']); m['backs'] = 1

def beauty(v, tag, samples, scale):
    """presentation renders: clean night backdrop + studio ground (no context city), AgX, denoise, bloom"""
    R = lambda wh: (int(wh[0] * scale), int(wh[1] * scale))
    sc = setup(samples=samples, res=R(HD))
    sc.view_settings.exposure = 0.0
    try: sc.view_settings.look = 'AgX - Punchy'   # warmer, more saturated grade (sheet look)
    except TypeError: pass
    screen_backs()
    out = None
    if v == 'hero':
        night_world(sc); ground(sc); uplights(0.45); metal_lights(); hood_glow(); bloom(sc, 0.25, size=0.5)
        camera((-95, -305, 1.6), target=(0, 0, 178), lens=15)   # low + close: tower fills the frame
        sc.view_settings.exposure = -0.25
        out = 'hero_night'
    elif v == 'entrance':
        night_world(sc); ground(sc); uplights(0.35); hood_glow(); bloom(sc, 0.4)
        y0 = -P.Ro(0); metal_lights(0.22, focus=(0, y0, 30)); sc.view_settings.exposure = -0.45
        light('AREA', (0, y0 - 40, 1.0), 4e4, (1.0, 0.75, 0.5), size=30, target=(0, y0, 25))
        cam = camera((34, y0 - 70, 2.2), target=(-2, y0, 26), lens=24); dof(cam, 75, 8.0)
        out = 'entrance_closeup'
    elif v == 'platform':
        night_world(sc); ground(sc); uplights(0.15); bloom(sc, 0.45)
        o = P.PODS[1]; z = o['z']; metal_lights(0.25, focus=(o['x'], o['y'], z)); sc.view_settings.exposure = -0.35
        light('AREA', (o['x'] - 60, o['y'] - 80, z - 30), 2e5, (0.6, 0.8, 1.0), size=40, target=(o['x'], o['y'], z))
        cam = camera((o['x'] - 105, o['y'] - 120, z - 16), target=(o['x'] + 8, o['y'], z - 4), lens=30); dof(cam, 150, 11.0)
        out = 'platform_closeup'
    elif v == 'atrium':
        night_world(sc, 0.4); bloom(sc, 0.5)
        for z in (90, 140): light('POINT', (0, 0, z), 3e4, (1.0, 0.75, 0.45), size=3)
        for x in (-22, 22): light('POINT', (x, -14, 30), 2.5e4, (1.0, 0.6, 0.2), size=4)
        light('POINT', (0, -30, 8), 6e4, (0.4, 0.8, 1.0), size=2)
        light('AREA', (0, -20, 3), 3e4, (1.0, 0.8, 0.55), size=8, target=(0, 0, 20))
        cam = camera((5, -50, 1.7), target=(0, 0, 24), lens=16); dof(cam, 50, 5.6)
        out = 'atrium_interior'
    elif v == 'gallery':
        night_world(sc, 0.4); bloom(sc, 0.4); sc.view_settings.exposure = -1.6
        z = 130.5
        for rr in (60, 80, 100): light('POINT', (rr, 0, z + 8), 6e3, (1.0, 0.8, 0.55), size=2)
        cam = camera((49, -3, z + 1.7), target=(110, 4, z + 3.5), lens=18); dof(cam, 25, 5.6)
        out = 'gallery_typical'
    elif v in ('elev_front', 'elev_side'):
        sc.render.resolution_x, sc.render.resolution_y = R((1600, 1800))
        night_world(sc); ground(sc); uplights(0.4); metal_lights(0.8); hood_glow(); bloom(sc, 0.4)
        if v == 'elev_front': camera((0, -1500, 212), rot=(90, 0, 0), ortho=470)
        else: camera((1500, 0, 212), rot=(90, 0, 90), ortho=470)
        out = 'elevation_front' if v == 'elev_front' else 'elevation_side'
    elif v == 'cutaway':
        night_world(sc); clip_y(0.0); bloom(sc, 0.4)
        light('SUN', (0, 0, 500), 2.2, (0.85, 0.88, 1.0), rot=(55, 0, 20))
        for z in (12, 60, 160, 260): light('POINT', (0, 10, z), 6e4, (1.0, 0.8, 0.6), size=3)
        camera((-420, -620, 260), target=(0, 0, 190), lens=38)
        out = 'section_cutaway'
    render_to(os.path.join(OUT, 'renders/%s_%s.png' % (out, tag)))

def run(views, tag, samples, scale):
    for v in views:
        bpy.ops.wm.open_mainfile(filepath=os.environ.get('SKY_BLEND', os.path.join(OUT, 'model.blend')))
        t0 = time.time()
        if v.endswith('_mask'):
            b = v[:-5]; loc, rot, osc, res = ORTHO[b]
            sc = setup(samples=1, res=res); sc.cycles.use_denoising = False
            sc.view_settings.view_transform = 'Standard'
            world(sc, strength=0.0); mask_override()
            if b == 'section': clip_y(0.0)
            camera(loc, rot=rot, ortho=osc)
            render_to(os.path.join(OUT, 'renders/ortho/%s_%s.png' % (v, tag)))
        elif v in ORTHO:
            loc, rot, osc, res = ORTHO[v]
            sc = setup(samples=samples, res=(int(res[0] * scale), int(res[1] * scale)))
            night_world(sc); uplights(0.8); bloom(sc, 0.45)
            if v == 'section': clip_y(0.0)
            camera(loc, rot=rot, ortho=osc)
            render_to(os.path.join(OUT, 'renders/ortho/%s_%s.png' % (v, tag)))
        else:
            beauty(v, tag, samples, scale)
        print(v, 'done', round(time.time() - t0, 1), 's', flush=True)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--views', required=True); ap.add_argument('--tag', default='r1')
    ap.add_argument('--samples', type=int, default=32); ap.add_argument('--scale', type=float, default=1.0)
    a = ap.parse_args()
    run(a.views.split(','), a.tag, a.samples, a.scale)
