"""compare/drawing_vs_model_final.png: per view  [design-sheet panel (calibrated into the model frame) | model ortho render | mask overlay]
overlay colours: white = both, red = drawing only, cyan = model only. usage: final_sheet.py TAG [FIRST_TAG]"""
import sys, os, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
from compare import sheet_compare
tag = sys.argv[1]; first = sys.argv[2] if len(sys.argv) > 2 else None
FP = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
F1 = ImageFont.truetype(FP, 30); F2 = ImageFont.truetype(FP, 20)
T = 440; views = ['front', 'back', 'left', 'right', 'top', 'section']
sc = {r['view']: r for r in sheet_compare(tag)}
s0 = {}
if first and os.path.exists(os.path.join(ROOT, 'compare/scores_%s.json' % first)):
    s0 = {r['view']: r for r in json.load(open(os.path.join(ROOT, 'compare/scores_%s.json' % first)))['sheet']}
W = Image.new('RGB', (T * 3 + 150, 90 + T * len(views)), (8, 10, 18)); d = ImageDraw.Draw(W)
d.text((16, 14), '云巅博物馆 · drawing vs model (%s)   列: 设计图面板 | 模型正交渲染 | 轮廓叠加 (白=重合 红=仅图纸 青=仅模型)' % tag, fill=(255, 200, 120), font=F2)
d.text((16, 48), 'IoU per view' + ('  (first %s → final %s)' % (first, tag) if s0 else ''), fill=(0, 230, 255), font=F2)
for i, v in enumerate(views):
    y = 90 + i * T
    pan = Image.open(os.path.join(ROOT, 'ref/panelm_%s.png' % v)).convert('RGB')
    rp = os.path.join(ROOT, 'renders/ortho/%s_%s.png' % (v, tag))
    ren = Image.open(rp).convert('RGB') if os.path.exists(rp) else Image.new('RGB', (690, 690))
    R = np.asarray(Image.open(os.path.join(ROOT, 'ref/refmask_%s.png' % v)).convert('L')) > 128
    M = np.asarray(Image.open(os.path.join(ROOT, 'renders/ortho/%s_mask_%s.png' % (v, tag))).convert('L')) > 30
    ov = np.zeros(R.shape + (3,), np.uint8); ov[R & M] = (225, 225, 225); ov[R & ~M] = (255, 70, 50); ov[M & ~R] = (30, 200, 255)
    for j, im in enumerate((pan, ren, Image.fromarray(ov))):
        W.paste(im.resize((T, T)), (150 + j * T, y))
    d.text((10, y + 10), v.upper(), fill=(0, 240, 255), font=F1)
    r = sc.get(v)
    if r:
        txt = 'IoU\n%.3f' % r['iou'] + ('\n(was\n%.3f)' % s0[v]['iou'] if v in s0 else '') + '\n\ntop-edge\n%.1f m\nwidth\n%.1f m' % (r['top_err_m'], r['width_err_m'])
        d.multiline_text((10, y + 60), txt, fill=(220, 240, 255), font=F2, spacing=4)
W.save(os.path.join(ROOT, 'compare/drawing_vs_model_%s.png' % tag))
print('wrote', 'compare/drawing_vs_model_%s.png' % tag)
