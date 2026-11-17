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
CORE_R = 9.0              # central glass elevator core inside the atrium (4 high-speed lifts)
ART_RING_R = 18.0         # golden ring installation dia ~36
ART_RING_Z = 34.0         # hangs in the L3-L5 atrium-gallery band
N_ARMS = 8                # radial 8-arm star plan

# vertical segments (sheet: base 0-48, lower 48-180, mid 180-320, upper taper 320-400, spire 400-420)
SEGMENTS = [('base', 0, 48), ('lower', 48, 180), ('mid', 180, 320), ('upper', 320, 400), ('spire', 400, 420)]
# arm-tip radius profile Ro(z) (half of the elevation width at that height) - piecewise linear stations
RO_PROFILE = [(0, 180.0), (48, 180.0), (48.01, 168.0), (180, 136.0), (320, 96.0), (400, 44.0)]
SPIRE = dict(z0=400.0, z1=H_TOTAL, r0=10.0, mast_r=1.2)
VALLEY_RATIO = [(0, 0.60), (180, 0.64), (320, 0.76), (400, 0.80)]   # valley radius / tip radius
VALLEY_MIN = 74.0         # valleys must clear the atrium + core ring up to L27
TIP_HALF_W_RATIO = 0.11   # flat arm-tip half width / Ro

# observation ring cantilever discs
OBS = [dict(name='L28', z=320.0, cant=16.0, t=3.0), dict(name='L29', z=360.0, cant=14.0, t=2.6), dict(name='L30', z=400.0, cant=12.0, t=2.4)]

# floor program (interior sheet): name, floor-to-floor height, program
FLOOR_H = [('L1', 16.0, 'lobby'), ('L2', 10.0, 'services')] + \
          [('L%d' % i, 10.0, 'atrium_gallery') for i in (3, 4, 5)] + \
          [('L%d' % i, 12.0, 'themed_hall') for i in range(6, 11)] + \
          [('L%d' % i, 12.0, 'core_gallery') for i in range(11, 21)] + \
          [('L%d' % i, 12.0, 'sky_gallery') for i in range(21, 28)]
OBS_FLOORS = [('L28', 320.0, 'cloud_observation'), ('L29', 360.0, 'cloud_observation'), ('L30', 400.0, 'cloud_observation')]
SLAB_T = 0.6

def floors():
    """[(name, z_floor, h, program)] L1..L30"""
    out, z = [], 0.0
    for n, h, p in FLOOR_H:
        out.append((n, z, h, p)); z += h
    assert abs(z - 320.0) < 1e-6, z
    for i, (n, zf, p) in enumerate(OBS_FLOORS):
        h = (OBS_FLOORS[i + 1][1] if i + 1 < len(OBS_FLOORS) else H_TOTAL) - zf
        out.append((n, zf, h, p))
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
HS_STOPS = ['L1', 'L11', 'L21', 'L28', 'L29', 'L30']
BRIDGE_LEVELS = ['L11', 'L21']
BRIDGE_W = 4.0

# angles
def arm_angle(k): return -math.pi / 2 + k * 2 * math.pi / N_ARMS          # k=0 -> south (front)
def valley_angle(k): return arm_angle(k) + math.pi / N_ARMS

def _interp(tab, z):
    if z <= tab[0][0]: return tab[0][1]
    for (z0, a), (z1, b) in zip(tab, tab[1:]):
        if z <= z1: return a + (b - a) * (z - z0) / max(z1 - z0, 1e-9)
    return tab[-1][1]

def Ro(z): return _interp(RO_PROFILE, z)
def Ri(z):
    r = Ro(z) * _interp(VALLEY_RATIO, z)
    return max(r, VALLEY_MIN) if z <= 320 else r

def star(z, inset=0.0):
    """plan polygon at height z: 8 flat-tipped arms. returns [(x,y)] CCW, 24 vertices."""
    ro, ri = Ro(z) - inset, Ri(z) - inset
    hw = TIP_HALF_W_RATIO * Ro(z)
    pts = []
    for k in range(N_ARMS):
        a = arm_angle(k)
        ca, sa = math.cos(a), math.sin(a)
        # tip corners (perpendicular offset), then valley
        for s in (-1, 1):
            pts.append((ro * ca - s * hw * sa, ro * sa + s * hw * ca))
        v = valley_angle(k)
        pts.append((ri * math.cos(v), ri * math.sin(v)))
    return pts

STATIONS = sorted(set([0, 8, 16, 26, 36, 48, 48.01] + [f[1] for f in floors()] + [360, 400]))

if __name__ == '__main__':
    for n, z, h, p in floors(): print(n, z, h, p, 'Ro %.1f Ri %.1f' % (Ro(z), Ri(z)))

# --- exterior details
CROWN_Z = 410.0; CROWN_R = 30.0     # L30 glass crown 400 -> 410, spire 410 -> 420
SPIRE['z0'] = CROWN_Z
ENTRANCE_RECESS = 6.0
DOOR_W, DOOR_H = 12.0, 6.0
SCREEN_Z = (6.0, 42.0)
VALLEY_STRIPS = True
PLAZA_R = 250.0
