"""procedural textures (PIL): media screens, sign, artworks, titanium panels, floors"""
import os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tex'); os.makedirs(TEX, exist_ok=True)
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
if not os.path.exists(FONT): FONT = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
def font(s): return ImageFont.truetype(FONT, s)

def grad(w, h, c0, c1, vertical=True):
    t = np.linspace(0, 1, h if vertical else w)
    a = np.array(c0, float)[None, :] * (1 - t[:, None]) + np.array(c1, float)[None, :] * t[:, None]
    if vertical: im = np.repeat(a[:, None, :], w, 1)
    else: im = np.repeat(a[None, :, :], h, 0)
    return Image.fromarray(im.astype(np.uint8))

def screen(name, c0, c1, title, sub, seed):
    random.seed(seed)
    W, H = 1024, 512
    im = grad(W, H, c0, c1, vertical=False); d = ImageDraw.Draw(im)
    for i in range(40):
        x = random.randint(0, W); y = random.randint(0, H); r = random.randint(10, 120)
        col = random.choice([(0, 240, 255), (255, 60, 200), (255, 190, 80), (140, 80, 255)])
        d.ellipse([x - r, y - r, x + r, y + r], outline=col + (255,), width=random.randint(1, 4))
    for y in range(0, H, 6): d.line([(0, y), (W, y)], fill=(0, 0, 0), width=1)
    im = im.filter(ImageFilter.GaussianBlur(0.8)); d = ImageDraw.Draw(im)
    d.text((60, 120), title, font=font(150), fill=(255, 255, 255))
    d.text((66, 330), sub, font=font(56), fill=(0, 245, 255))
    im.save(os.path.join(TEX, name + '.png'))

def sign():
    W, H = 1024, 432
    im = Image.new('RGB', (W, H), (5, 8, 20)); d = ImageDraw.Draw(im)
    d.rectangle([8, 8, W - 8, H - 8], outline=(0, 240, 255), width=6)
    d.text((W / 2, 170), '云巅博物馆', font=font(170), fill=(255, 205, 120), anchor='mm')
    d.text((W / 2, 345), 'CYBERPUNK SKY MUSEUM', font=font(64), fill=(0, 240, 255), anchor='mm')
    im.save(os.path.join(TEX, 'screen_sign.png'))

def art(name, seed):
    random.seed(seed); W, H = 512, 512
    pal = random.choice([[(10, 10, 30), (0, 220, 255), (255, 170, 60)], [(20, 5, 30), (255, 60, 190), (90, 200, 255)], [(5, 15, 20), (255, 200, 90), (255, 90, 40)], [(8, 8, 18), (120, 90, 255), (0, 255, 200)]])
    im = Image.new('RGB', (W, H), pal[0]); d = ImageDraw.Draw(im)
    for i in range(18):
        c = pal[1 + i % 2]
        if i % 3 == 0:
            r = random.randint(30, 220); x, y = random.randint(0, W), random.randint(0, H)
            d.ellipse([x - r, y - r, x + r, y + r], outline=c, width=random.randint(2, 10))
        else:
            x0, y0 = random.randint(0, W), random.randint(0, H)
            d.line([(x0, y0), (x0 + random.randint(-300, 300), y0 + random.randint(-300, 300))], fill=c, width=random.randint(2, 14))
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    d = ImageDraw.Draw(im); d.rectangle([0, 0, W - 1, H - 1], outline=(200, 160, 90), width=10)
    im.save(os.path.join(TEX, name + '.png'))

def panels(name, base, line, cell=64, size=512, noise=8, seed=1):
    rng = np.random.default_rng(seed)
    a = np.ones((size, size, 3)) * np.array(base, float)
    a += rng.normal(0, noise, (size, size, 1))
    for i in range(0, size, cell):
        a[i:i + 2, :, :] = line; a[:, i:i + 2, :] = line
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(TEX, name + '.png'))

if __name__ == '__main__':
    screen('screen_a', (10, 0, 60), (0, 120, 200), '云巅', 'SKY MUSEUM · 420M', 1)
    screen('screen_b', (80, 0, 70), (255, 80, 40), '未来艺术', 'FUTURE ART EXPO 2077', 2)
    screen('screen_c', (0, 40, 60), (0, 200, 160), '观云台', 'CLOUD DECK  L28-L30', 3)
    screen('screen_d', (40, 10, 0), (220, 140, 20), '光之环', 'GOLDEN RING · ATRIUM', 4)
    sign()
    for i, n in enumerate('abcd'): art('art_' + n, 10 + i)
    panels('titanium', (52, 56, 66), (28, 30, 36), cell=128, noise=6)
    panels('floor_stone', (70, 72, 80), (40, 42, 48), cell=128, noise=5, seed=2)
    panels('floor_dark', (38, 40, 46), (24, 26, 30), cell=128, noise=4, seed=3)
    print('ok')
