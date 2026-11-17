import base64, json, os, sys, math
r = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..') + '/'
sys.path.insert(0, r + 'src')
import params as P
t = open(r + 'src/web_template.html').read()
g = base64.b64encode(open(r + 'web/model_web.glb', 'rb').read()).decode()
fl = [[n, z] for n, z, h, p in P.floors()]
F = {n: z for n, z in fl}
a0 = P.arm_angle(0)
# spawn: blender x, y, z, three-yaw (yaw 0 looks toward blender +y)
def up(n, yaw=math.pi):
    z = F[n]; return [0, P.yc(z) - (P.CORE_R + 3.5), z, yaw]
spawn = {'plaza': [0, -P.Ro(0) - 41, 0, 0], 'lobby': [0, -P.Ro(0) + 25, 0, 0], 'atrium': [14, -30, 0, 0.3], 'esc': [30, -18, 0, 0],
         'L3': [0, -(P.ATRIUM_R + 3.5), F['L3'], 0], 'L11': up('L11'), 'L12': up('L12'), 'L21': up('L21'),
         'L28': up('L28'), 'L30': up('L30')}
label = {'plaza': '广场', 'lobby': 'L1 门厅', 'atrium': 'L1 中庭', 'esc': '扶梯 L1→L2', 'L3': 'L3 环廊', 'L11': 'L11 空中大堂', 'L12': 'L12 核心展廊',
         'L21': 'L21 天空展廊', 'L28': 'L28 观云台', 'L30': 'L30 观云台'}
TP = dict(spawn=spawn, label=label, order=list(spawn), floors=fl)
COLL = ['Podium', 'Portal', 'Entrance_Glass', 'Shell_Glass', 'Slabs', 'Slabs_Glass', 'Walls', 'Cores', 'Stairs', 'Escalators', 'Rails', 'Bridges', 'Obs_Decks', 'Pods', 'Fans', 'Atrium_Roof', 'Ground', 'Core_Glass', 'Exhibits', 'Spire']
js = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
out = t.replace('__TP_JSON__', js(TP)).replace('__COLL_JSON__', js(COLL)).replace('__GLB_BASE64__', g)
open(r + 'web/preview.html', 'w').write(out)
json.dump(TP, open(r + 'web/teleports.json', 'w'), ensure_ascii=False, indent=1)
print('preview.html', len(out))
