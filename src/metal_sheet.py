"""compare/metal_vs_sheet.png: sheet front view (left) vs model front elevation render (right), plus hero"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
tag = sys.argv[1] if len(sys.argv) > 1 else 'final'
sh = Image.open(os.path.join(R, 'ref/sheet_exterior.png')).convert('RGB').crop((285, 0, 615, 395))
H = 1100
a = sh.resize((int(sh.width * H / sh.height), H), Image.LANCZOS)
b = Image.open(os.path.join(R, 'renders/elevation_front_%s.png' % tag)).convert('RGB')
b = b.resize((int(b.width * H / b.height), H), Image.LANCZOS)
ims = [a, b]
hp = os.path.join(R, 'renders/hero_night_%s.png' % tag)
if os.path.exists(hp):
    c = Image.open(hp).convert('RGB'); c = c.resize((int(c.width * H / c.height), H), Image.LANCZOS); ims.append(c)
W = sum(i.width for i in ims) + 20 * (len(ims) + 1)
out = Image.new('RGB', (W, H + 90), (12, 14, 22)); d = ImageDraw.Draw(out)
try: f = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 34)
except Exception: f = ImageFont.load_default()
x = 20
for im, lab in zip(ims, ['sheet: front view (正面图)', 'model: front elevation render', 'model: hero night']):
    out.paste(im, (x, 70)); d.text((x, 18), lab, fill=(220, 230, 240), font=f); x += im.width + 20
os.makedirs(os.path.join(R, 'compare'), exist_ok=True)
out.save(os.path.join(R, 'compare/metal_vs_sheet.png')); print('wrote compare/metal_vs_sheet.png', out.size)
