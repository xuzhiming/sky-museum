"""云巅博物馆 / Cyberpunk Sky Museum - parameter table.
All geometry is generated from these numbers. Units: metres, Z up, origin = plan centre at ground.
Front elevation faces -Y (main entrance at the south arm tip).
Source: design sheets (exterior: elevations / top view / section / program; interior: section A-A, plans L1, L3-L5, L11-L20, L28-L30)
as transcribed in the brief (dimension lines: H 420, W 360, D 360, entrance 48, atrium dia 80, floors 9-12 m, obs. decks 320/360/400)."""
import math

H_TOTAL = 420.0           # top of spire
W_BASE = 360.0            # base width (arm tip to arm tip, E-W)
D_BASE = 360.0            # base depth (N-S)
ENTRANCE_H = 48.0         # main entrance portal height
ENTRANCE_W = 30.0         # portal clear width (sheet: arm-tip portal, ~0.6 x height)
ATRIUM_R = 40.0           # core atrium dia 80
CORE_R = 7.0              # central glass core L11-L30 (high-speed lifts), above the atrium
ART_RING_R = 18.0         # golden ring installation dia ~36
ART_RING_Z = 21.0         # interior sheet: vertical thick ring (Ø≈36) standing on the atrium floor
N_ARMS = 8                # radial 8-arm star plan

# vertical segments (exterior sheet floor table: base 0-48, lower 48-180, mid 180-320, upper 320-400, crown/spire 400-420)
SEGMENTS = [('base', 0, 48), ('lower', 48, 180), ('mid', 180, 320), ('upper', 320, 400), ('spire', 400, 420)]
# arm-tip radius profile Ro(z): fitted to the four elevation panels of the exterior sheet (refmask.py + compare loop)
RO_PROFILE = [(0, 174.0), (20, 172.0), (40, 163.0), (60, 155.0), (80, 143.0), (100, 127.0), (120, 119.0), (140, 112.0),
              (160, 106.0), (180, 99.0), (200, 90.0), (220, 83.0), (240, 76.0), (260, 70.0), (280, 64.0), (300, 57.0),
              (320, 49.0), (340, 43.0), (360, 35.0), (380, 29.0), (400, 23.0)]
VALLEY_RATIO = [[0, 0.94], [80, 0.84], [180, 0.80], [320, 0.80], [400, 0.80]]   # valley radius / tip radius (top view ~ round)
VALLEY_MIN = 0.0
TIP_HALF_W_RATIO = 0.11   # flat arm-tip half width / Ro
# side elevations: the upper tower leans to the rear (+Y): plan centre offset yc(z)
LEAN = [[0, 0.0], [100, 0.0], [400, 22.0], [420, 23.0]]
def yc(z): return _interp(LEAN, z)

# diagonal fan wings at the base (top view: fan-shaped quadrant wings between the 4 pointed cardinal arms)
FAN = dict(z1=76.0, half_deg=24.0, r_in_ratio=0.80, top_drop=0.0, r_scale=1.10)   # r_scale capped so the fans stay inside the 360 m elevation width

# saucer pods (exterior sheet: 3 cantilevered disc platforms; drawn positions, see compare_log for the label conflict)
PODS = [dict(name='P1', z=292.0, x=-71.0, y=70.0, R=36.0, t=6.5),
        dict(name='P2', z=182.0, x=-98.0, y=35.0, R=48.0, t=8.0),
        dict(name='P3', z=266.0, x=84.0, y=20.0, R=38.0, t=6.5)]
# observation ring decks at the labelled +320 / +360 / +400 levels (L21 / L28 / L30), slim cantilevers around the tower
OBS = [dict(name='L21', z=320.0, cant=8.0, t=2.0), dict(name='L28', z=360.0, cant=7.0, t=2.0), dict(name='L30', z=400.0, cant=6.0, t=1.6)]
# twin needle spires (front elevation: two blades at x = +-16 reaching 420)
SPIRE = dict(z0=410.0, z1=H_TOTAL, x=12.0, w0=3.0, d0=10.0)

# floor program. exterior sheet table: L1 0-24, L2 24-48, L3-L10 48-180, L11-L20 180-320, L21-L27 320-360,
# L28-L29 360-400, L30 400-420 (interior sheet labels +60/+120/... conflict; logged in compare_log.md)
FLOOR_H = [('L1', 24.0, 'lobby'), ('L2', 24.0, 'services')] + \
          [('L%d' % i, 16.5, 'atrium_gallery' if i <= 5 else 'themed_hall') for i in range(3, 11)] + \
          [('L%d' % i, 14.0, 'core_gallery') for i in range(11, 21)] + \
          [('L%d' % i, 40.0 / 7, 'sky_gallery') for i in range(21, 28)] + \
          [('L28', 20.0, 'cloud_observation'), ('L29', 20.0, 'cloud_observation')]
SLAB_T = 0.6
ATRIUM_TOP = 180.0        # Ø80 atrium void L1-L10, roofed at L11 (section A-A)

def floors():
    """[(name, z_floor, h, program)] L1..L30"""
    out, z = [], 0.0
    for n, h, p in FLOOR_H:
        out.append((n, round(z, 4), h, p)); z += h
    assert abs(z - 400.0) < 1e-6, z
    out.append(('L30', 400.0, H_TOTAL - 400.0, 'cloud_observation'))
    return out

# interior layout (per typical floor)
CORRIDOR_W = 7.0          # ring corridor 6-8 m around the atrium
RING_WALL_R = ATRIUM_R + CORRIDOR_W
HALL_DOOR_W = 10.0        # opening from ring corridor into each arm hall
ARM_HALL_W = 26.0         # gallery hall width (18-30)
CORE_BOX = dict(r0=RING_WALL_R + 0.5, r1=RING_WALL_R + 19.0, w=14.0)   # valley cores (stairs / lifts)
STAIR = dict(riser=0.1667, tread=0.30, width=1.6, landing=2.0, max_run=18)
ESC = dict(riser=0.20, tread=0.35, width=1.6)      # escalators L1-L5 (walkable step flights)
N_HS_LIFTS = 4            # high-speed in central core
N_PASS_LIFTS = 8          # passenger lifts in valley cores
HS_STOPS = ['L11', 'L21', 'L28', 'L29', 'L30']   # central core (sky lobby L11); atrium lifts L1 <-> L11
BRIDGE_LEVELS = []
BRIDGE_W = 4.0

# angles
def arm_angle(k): return -math.pi / 2 + k * 2 * math.pi / N_ARMS          # k=0 -> south (front)
def valley_angle(k): return arm_angle(k) + math.pi / N_ARMS

def _interp(tab, z):
    if z <= tab[0][0]: return tab[0][1]
    for (z0, a), (z1, b) in zip(tab, tab[1:]):
        if z <= z1: return a + (b - a) * (z - z0) / max(z1 - z0, 1e-9)
    return tab[-1][1]

RO_SCALE = 1.0
def Ro(z): return _interp(RO_PROFILE, z) * RO_SCALE
def Ri(z): return Ro(z) * _interp(VALLEY_RATIO, z)

def star(z, inset=0.0):
    """plan polygon at height z: 8 flat-tipped arms. returns [(x,y)] CCW, 24 vertices."""
    ro, ri = Ro(z) - inset, Ri(z) - inset
    hw = TIP_HALF_W_RATIO * Ro(z)
    pts = []; c = yc(z)
    for k in range(N_ARMS):
        a = arm_angle(k)
        ca, sa = math.cos(a), math.sin(a)
        # tip corners (perpendicular offset), then valley
        for s in (-1, 1):
            pts.append((ro * ca - s * hw * sa, ro * sa + s * hw * ca + c))
        v = valley_angle(k)
        pts.append((ri * math.cos(v), ri * math.sin(v) + c))
    return pts

STATIONS = sorted(set([round(z, 3) for z, _ in RO_PROFILE] + [round(f[1], 3) for f in floors()] + [400]))

if __name__ == '__main__':
    for n, z, h, p in floors(): print(n, z, h, p, 'Ro %.1f Ri %.1f' % (Ro(z), Ri(z)))

# --- exterior details
CROWN_Z = 410.0; CROWN_R = 18.0     # L30 glass crown 400 -> 410
ENTRANCE_RECESS = 6.0
HOOD = dict(half_w=60.0, top_z=112.0, proud=2.5, open_w=34.0, open_h=14.0, n_diag=10, glaze_z=24.0, sign_z=30.0)   # sheet front view: pyramid glass hood over the central third
DOOR_W, DOOR_H = 12.0, 6.0
SCREEN_Z = (12.0, 78.0)             # front elevation: media screens ~z 15-85 on the lower faces
PORTAL_FRAME = dict(leg_x=82.0, eave_z=100.0, eave_x=128.0, peak_z=190.0)   # pentagon frame on the main facade
VALLEY_STRIPS = True
PLAZA_R = 250.0

# --- comparison-loop overrides: SKY_OVR='{"FAN.half_deg": 22, "PODS.0.z": 290}' (used by tune.py only)
import os as _os, json as _json
for _k, _v in _json.loads(_os.environ.get('SKY_OVR', '{}')).items():
    _p = _k.split('.'); _o = globals()
    if len(_p) == 1: _o[_p[0]] = _v; continue
    _o = _o[_p[0]]
    for _q in _p[1:-1]: _o = _o[int(_q)] if isinstance(_o, list) else _o[_q]
    _l = _p[-1]
    if isinstance(_o, list): _o[int(_l)] = _v
    else: _o[_l] = _v
