import bpy, os
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tex')
# name: (albedo(tex or rgb), emission(tex or rgb or None), emission strength, rough, metal, alpha, uv_scale)
# palette from the sheet's material board: M-01 dark titanium, M-02 brushed metal, M-03 smoked glass, M-04 cyan light strip, M-05 amber light
MATS = {
 'titanium':      ('titanium', None, 0, 0.45, 0.85, 1.0, 12.0),
 'frame_metal':   ((0.42, 0.44, 0.48), None, 0, 0.3, 1.0, 1.0, 4.0),
 'frame_dark':    ((0.06, 0.065, 0.08), None, 0, 0.4, 0.9, 1.0, 4.0),
 'glass_curtain': ((0.02, 0.05, 0.09), (0.25, 0.45, 0.9), 0.06, 0.04, 0.5, 0.62, 4.0),
 'glass_clear':   ((0.5, 0.7, 0.85), None, 0, 0.03, 0.0, 0.22, 4.0),
 'glass_core':    ((0.45, 0.75, 0.95), (0.2, 0.6, 0.9), 0.15, 0.03, 0.0, 0.25, 4.0),
 'glass_floor':   ((0.4, 0.7, 0.95), (0.2, 0.7, 1.0), 0.4, 0.03, 0.0, 0.35, 4.0),
 'rail_glass':    ((0.6, 0.85, 1.0), (0.2, 0.7, 1.0), 0.05, 0.03, 0.0, 0.2, 4.0),
 'rail_metal':    ((0.55, 0.56, 0.6), None, 0, 0.3, 1.0, 1.0, 4.0),
 'strip_cyan':    ((0.1, 0.9, 1.0), (0.05, 0.8, 1.0), 9.0, 0.4, 0.0, 1.0, 4.0),
 'strip_cyan_soft': ((0.1, 0.8, 1.0), (0.1, 0.8, 1.0), 4.0, 0.4, 0.0, 1.0, 4.0),
 'strip_amber_soft': ((1.0, 0.6, 0.25), (1.0, 0.55, 0.2), 3.0, 0.4, 0.0, 1.0, 4.0),
 'strip_amber':   ((1.0, 0.62, 0.25), (1.0, 0.55, 0.18), 10.0, 0.4, 0.0, 1.0, 4.0),
 'light_panel':   ((1.0, 0.85, 0.62), (1.0, 0.72, 0.42), 8.0, 0.5, 0.0, 1.0, 4.0),
 'beacon':        ((1.0, 0.2, 0.3), (1.0, 0.15, 0.25), 30.0, 0.4, 0.0, 1.0, 4.0),
 'cab':           ((1.0, 0.7, 0.4), (1.0, 0.65, 0.3), 5.0, 0.4, 0.0, 1.0, 4.0),
 'door_lift':     ((0.1, 0.5, 0.6), (0.05, 0.6, 0.8), 1.5, 0.3, 0.6, 1.0, 4.0),
 'door_lift_hs':  ((0.6, 0.45, 0.2), (0.9, 0.6, 0.25), 1.2, 0.3, 0.9, 1.0, 4.0),
 'lift_shaft':    ((0.09, 0.1, 0.12), None, 0, 0.4, 0.7, 1.0, 4.0),
 'gold':          ((1.0, 0.55, 0.12), (1.0, 0.42, 0.06), 1.6, 0.22, 1.0, 1.0, 4.0),
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
    MATS['screen_' + s] = ('screen_' + s, 'screen_' + s, 3.0, 0.3, 0.0, 1.0, 1.0)
    MATS['art_' + s] = ('art_' + s, 'art_' + s, 1.2, 0.5, 0.0, 1.0, 1.0)
MATS['screen_sign'] = ('screen_sign', 'screen_sign', 3.0, 0.3, 0.0, 1.0, 1.0)

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
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
    return m
