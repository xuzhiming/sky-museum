import bpy, os
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tex')
# name: (albedo(tex or rgb), emission(tex or rgb or None), emission strength, rough, metal, alpha, uv_scale)
# palette from the sheet's material board: M-01 dark titanium, M-02 brushed metal, M-03 smoked glass, M-04 cyan light strip, M-05 amber light
MATS = {
 'titanium':      ((0.40, 0.42, 0.46), None, 0, 0.34, 1.0, 1.0, 12.0),             # M-02 gunmetal cladding
 'frame_metal':   ((0.58, 0.60, 0.64), None, 0, 0.28, 1.0, 1.0, 4.0),
 'frame_dark':    ((0.06, 0.065, 0.08), None, 0, 0.4, 0.9, 1.0, 4.0),
 'glass_curtain': ((0.015, 0.03, 0.05), None, 0, 0.03, 0.0, 0.42, 4.0),          # M-03 low-e glass (dark, reflective, see-through)
 'ti_armor':      ((0.66, 0.68, 0.72), None, 0, 0.30, 1.0, 1.0, 4.0),            # M-01 titanium alloy, light silver-grey (exoskeleton / armor)
 'ti_armor2':     ((0.44, 0.46, 0.50), None, 0, 0.34, 1.0, 1.0, 4.0),            # M-02 gunmetal armor panels
 'ti_panel':      ((0.47, 0.49, 0.53), None, 0, 0.32, 1.0, 1.0, 4.0),             # M-02 armor panels (tone variation)
 'ti_panel2':     ((0.44, 0.46, 0.50), None, 0, 0.34, 1.0, 1.0, 4.0),
 'ti_panel3':     ((0.50, 0.52, 0.56), None, 0, 0.29, 1.0, 1.0, 4.0),
 'brushed':       ((0.72, 0.73, 0.76), None, 0, 0.24, 1.0, 1.0, 4.0),             # M-02 brushed metal trim
 'struct_dark':   ((0.12, 0.125, 0.14), None, 0, 0.40, 1.0, 1.0, 4.0),            # M-05 dark structural metal
 'room_warm':     ((1.0, 0.62, 0.3), (1.0, 0.58, 0.26), 7.0, 0.5, 0.0, 1.0, 4.0), # interior ceiling coves seen through glass
 'room_warm_hi':  ((1.0, 0.7, 0.4), (1.0, 0.66, 0.34), 12.0, 0.5, 0.0, 1.0, 4.0),
 'room_warm_lo':  ((1.0, 0.55, 0.25), (1.0, 0.5, 0.2), 3.5, 0.5, 0.0, 1.0, 4.0),
 'glass_clear':   ((0.5, 0.7, 0.85), None, 0, 0.03, 0.0, 0.22, 4.0),
 'glass_core':    ((0.3, 0.55, 0.7), (0.2, 0.6, 0.9), 0.03, 0.03, 0.0, 0.14, 4.0),
 'glass_floor':   ((0.4, 0.7, 0.95), (0.2, 0.7, 1.0), 0.4, 0.03, 0.0, 0.35, 4.0),
 'rail_glass':    ((0.25, 0.4, 0.5), (0.2, 0.7, 1.0), 0.02, 0.03, 0.0, 0.12, 4.0),
 'rail_metal':    ((0.55, 0.56, 0.6), None, 0, 0.3, 1.0, 1.0, 4.0),
 'strip_cyan':    ((0.1, 0.9, 1.0), (0.05, 0.8, 1.0), 14.0, 0.4, 0.0, 1.0, 4.0),
 'strip_cyan_soft': ((0.1, 0.8, 1.0), (0.1, 0.8, 1.0), 4.0, 0.4, 0.0, 1.0, 4.0),
 'strip_amber_soft': ((1.0, 0.6, 0.25), (1.0, 0.55, 0.2), 3.0, 0.4, 0.0, 1.0, 4.0),
 'strip_amber':   ((1.0, 0.62, 0.25), (1.0, 0.55, 0.18), 10.0, 0.4, 0.0, 1.0, 4.0),
 'light_panel':   ((1.0, 0.85, 0.62), (1.0, 0.72, 0.42), 8.0, 0.5, 0.0, 1.0, 4.0),
 'beacon':        ((1.0, 0.2, 0.3), (1.0, 0.15, 0.25), 30.0, 0.4, 0.0, 1.0, 4.0),
 'cab':           ((1.0, 0.7, 0.4), (1.0, 0.65, 0.3), 5.0, 0.4, 0.0, 1.0, 4.0),
 'door_lift':     ((0.1, 0.5, 0.6), (0.05, 0.6, 0.8), 1.5, 0.3, 0.6, 1.0, 4.0),
 'door_lift_hs':  ((0.6, 0.45, 0.2), (0.9, 0.6, 0.25), 1.2, 0.3, 0.9, 1.0, 4.0),
 'lift_shaft':    ((0.09, 0.1, 0.12), None, 0, 0.4, 0.7, 1.0, 4.0),
 'gold':          ((1.0, 0.62, 0.2), (1.0, 0.42, 0.06), 0.25, 0.18, 1.0, 1.0, 4.0),
 'bronze':        ((0.55, 0.3, 0.1), (1.0, 0.45, 0.1), 0.15, 0.3, 1.0, 1.0, 4.0),
 'holo_cyan':     ((0.2, 0.9, 1.0), (0.2, 0.9, 1.0), 6.0, 0.2, 0.0, 0.8, 4.0),
 'plaza':         ('floor_dark', None, 0, 0.35, 0.2, 1.0, 16.0),
 'floor_stone':   ('floor_stone', None, 0, 0.25, 0.3, 1.0, 8.0),
 'floor_dark':    ('floor_dark', None, 0, 0.3, 0.3, 1.0, 8.0),
 'wall_ring':     ((0.16, 0.17, 0.2), None, 0, 0.5, 0.6, 1.0, 4.0),
 'wall_core':     ((0.12, 0.13, 0.15), None, 0, 0.45, 0.8, 1.0, 4.0),
 'wall_light':    ((0.55, 0.55, 0.57), None, 0, 0.7, 0.1, 1.0, 4.0),
 'wall_dark':     ((0.2, 0.2, 0.23), None, 0, 0.6, 0.3, 1.0, 4.0),
 'stair':         ((0.3, 0.31, 0.34), None, 0, 0.5, 0.5, 1.0, 3.0),
 'esc_step':      ((0.5, 0.52, 0.56), None, 0, 0.3, 1.0, 1.0, 3.0),
 'esc_deck':      ((0.25, 0.26, 0.3), None, 0, 0.35, 0.8, 1.0, 3.0),
 'poche':         ((0.95, 0.5, 0.15), (0.95, 0.5, 0.15), 1.4, 0.8, 0.0, 1.0, 4.0),
}
for s in 'abcd':
    MATS['screen_' + s] = ('screen_' + s, 'screen_' + s, 4.5, 0.3, 0.0, 1.0, 1.0)
    MATS['art_' + s] = ('art_' + s, 'art_' + s, 1.2, 0.5, 0.0, 1.0, 1.0)
MATS['screen_sign'] = ('screen_sign', 'screen_sign', 3.0, 0.3, 0.0, 1.0, 1.0)

DETAIL = {'bronze', 'titanium', 'ti_armor', 'ti_armor2', 'ti_panel', 'ti_panel2', 'ti_panel3', 'brushed', 'struct_dark', 'frame_dark', 'frame_metal', 'gold'}

def surface_detail(nt, b, rough, brushed=False):
    """roughness variation + micro normal detail (procedural; render only - glTF keeps the base values)"""
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.0, 1.0, 40.0) if brushed else (1.0, 1.0, 1.0)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.35 if not brushed else 2.0; nz.inputs['Detail'].default_value = 6.0
    nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    rp = nt.nodes.new('ShaderNodeMapRange'); rp.inputs['To Min'].default_value = rough * 0.65; rp.inputs['To Max'].default_value = min(1.0, rough * 1.45)
    nt.links.new(nz.outputs['Fac'], rp.inputs['Value']); nt.links.new(rp.outputs['Result'], b.inputs['Roughness'])
    nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 6.0 if not brushed else 30.0; nz2.inputs['Detail'].default_value = 4.0
    nt.links.new(mp.outputs['Vector'], nz2.inputs['Vector'])
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.06 if not brushed else 0.1; bm.inputs['Distance'].default_value = 0.02
    nt.links.new(nz2.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs['Normal'], b.inputs['Normal'])

_img = {}
def img(name):
    if name in _img: return _img[name]
    im = bpy.data.images.load(os.path.join(TEX, name + '.png'), check_existing=True); im.pack(); _img[name] = im
    return im

def make_material(name):
    alb, emi, es, rough, metal, alpha, uv = MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = None
    if isinstance(alb, str):
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img(alb)
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    else:
        b.inputs['Base Color'].default_value = (*alb, 1)
    if emi is not None:
        if isinstance(emi, str):
            nt.links.new(t.outputs['Color'], b.inputs['Emission Color'])
        else:
            b.inputs['Emission Color'].default_value = (*emi, 1)
        b.inputs['Emission Strength'].default_value = es
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if name in DETAIL:
        surface_detail(nt, b, rough, brushed=(name == 'brushed'))
    if name in ('ti_armor', 'brushed', 'frame_metal'):   # brushed titanium: anisotropic highlight (render-only)
        try: b.inputs['Anisotropic'].default_value = 0.55
        except KeyError: pass
    if name == 'glass_curtain':
        b.inputs['Specular IOR Level'].default_value = 0.9
        b.inputs['Coat Weight'].default_value = 0.6; b.inputs['Coat Roughness'].default_value = 0.02
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    return m
