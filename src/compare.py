"""Comparison loop.
Mode A (sheet): ref/calib.json lists, per view, the panel crop on the design sheet and its dimension-line calibration:
   {"front": {"sheet": "ref/sheet_exterior.png", "crop": [x0,y0,x1,y1], "ground_y": px, "top_y": px, "top_m": 420,
              "x_left": px, "x_right": px, "span_m": 360, "thr": 40}, ...}
   The panel is segmented (difference from paper colour, close + fill holes), mapped to metres with its own dimension lines,
   and compared with the model's orthographic mask render on a 3 px/m grid: silhouette IoU + mean top-edge error (m).
Mode B (dimension check, always run): measures the model's rendered masks and checks the dimension table
   (H, base W/D, base segment height, obs-ring heights, spire, 8 arms in the top view, atrium dia in section)."""
import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params as P
PXM = 1380 / 460.0
CAM_Z = 215.0      # ortho camera centre height
FONT = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 18) if os.path.exists('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc') else None

def model_mask(view, tag):
    im = np.asarray(Image.open(os.path.join(ROOT, 'renders/ortho/%s_mask_%s.png' % (view, tag))).convert('L')).astype(float)
    return im > 128

def m2px_elev(x, z, shape):
    H, W = shape
    return W / 2 + x * PXM, H / 2 - (z - CAM_Z) * PXM

def elev_profile(m):
    """per row: (xmin,xmax) in metres, row z"""
    H, W = m.shape
    out = []
    for r in range(H):
        xs = np.where(m[r])[0]
        z = CAM_Z + (H / 2 - r) / PXM
        if len(xs): out.append((z, (xs.min() - W / 2) / PXM, (xs.max() - W / 2) / PXM))
    return out

def dimension_check(tag):
    rows = []
    def add(name, model, target, tol):
        rows.append(dict(item=name, model=round(float(model), 2), target=target, err=round(float(model - target), 2), ok=bool(abs(model - target) <= tol)))
    for v in ('front', 'right'):
        m = model_mask(v, tag)
        pr = elev_profile(m)
        ztop = max(z for z, a, b in pr)
        add('%s: total height H' % v, ztop, P.H_TOTAL, 2.0)
        w = lambda zz: [b - a for z, a, b in pr if abs(z - zz) < 0.5 / PXM * 2]
        add('%s: base width @z=10' % v, np.mean(w(10.0)), P.W_BASE if v == 'front' else P.D_BASE, 3.0)
        add('%s: base width @z=46' % v, np.mean(w(46.0)), P.W_BASE if v == 'front' else P.D_BASE, 3.0)
        # podium step: width drop just above 48
        ws = [(z, b - a) for z, a, b in pr if 40 < z < 60]
        step_z = max([z for z, ww in ws if ww > (P.W_BASE - 6)], default=0)
        add('%s: base segment top (setback)' % v, step_z, 48.0, 1.5)
        # observation rings: local width maxima above 300 m
        ws = np.array([(z, b - a) for z, a, b in pr if 300 < z < 410])
        rings = []
        if len(ws):
            zz, ww = ws[:, 0], ws[:, 1]
            for target in (320.0, 360.0, 400.0):
                sel = (zz > target - 8) & (zz < target + 2)
                if sel.any():
                    k = np.argmax(ww[sel]); rings.append((zz[sel][k], ww[sel][k]))
                    add('%s: obs ring top z (target %d)' % (v, target), zz[sel][ww[sel] > ww[sel].max() - 1.0].max(), target, 1.5)
        # segment boundaries (dimension table stations): width = 2 x arm-tip radius on the axis views
        for zz in (120.0, 180.0, 250.0, 308.0, 340.0, 385.0):
            add('%s: width @z=%d (param Ro)' % (v, zz), np.mean(w(zz)), round(2 * P.Ro(zz), 1), 3.0)
        add('%s: spire present above 410 (top z)' % v, ztop, P.H_TOTAL, 1.0)
    # top view: count arms from polar profile
    m = model_mask('top', tag); H, W = m.shape
    ang = np.linspace(-math.pi, math.pi, 720, endpoint=False); rad = []
    for a in ang:
        rr = np.arange(0, 230, 0.5)
        xs = (W / 2 + rr * math.cos(a) * PXM).astype(int); ys = (H / 2 - rr * math.sin(a) * PXM).astype(int)
        ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
        v = m[ys[ok], xs[ok]]
        rad.append(rr[ok][v].max() if v.any() else 0)
    rad = np.array(rad)
    # arms: peaks of the footprint radius below the disc radius (discs are circles) - use the mask of the podium via the front-arm spacing
    thr = (rad.min() + rad.max()) / 2; hi = rad > thr
    runs = int(np.sum(hi & ~np.roll(hi, 1)))
    add('top: arm count (polar runs above mid radius)', runs, 8, 0)
    add('top: valley radius at podium (min r)', rad.min(), round(P.Ri(0), 1), 4.0)
    add('top: footprint max radius (W/2)', rad.max(), P.W_BASE / 2, 3.0)
    return rows

def sheet_compare(tag):
    cf = os.path.join(ROOT, 'ref/calib.json')
    if not os.path.exists(cf): return None
    C = json.load(open(cf)); out = []
    for v, c in C.items():
        if v.startswith('_'): continue
        sheet = Image.open(os.path.join(ROOT, c['sheet'])).convert('RGB')
        x0, y0, x1, y1 = c['crop']; pan = np.asarray(sheet.crop((x0, y0, x1, y1))).astype(float)
        bg = np.median(np.concatenate([pan[:4].reshape(-1, 3), pan[-4:].reshape(-1, 3)]), 0)
        ref = np.abs(pan - bg).sum(2) > c.get('thr', 40)
        ref = ndi.binary_closing(ref, np.ones((3, 3)), iterations=3); ref = ndi.binary_fill_holes(ref)
        ref = ndi.binary_opening(ref, np.ones((3, 3)))
        lab, n = ndi.label(ref)
        if n > 1:
            sz = ndi.sum(ref, lab, range(1, n + 1)); ref = np.isin(lab, [i + 1 for i, s in enumerate(sz) if s > 0.02 * sz.max()])
        # sheet px -> metres (own dimension lines)
        sx = c['span_m'] / (c['x_right'] - c['x_left']); sz_ = c['top_m'] / (c['ground_y'] - c['top_y'])
        mm = model_mask(v if v != 'section' else 'front', tag); H, W = mm.shape
        # resample sheet mask into model grid
        yy, xx = np.mgrid[0:H, 0:W]
        X = (xx - W / 2) / PXM; Z = CAM_Z + (H / 2 - yy) / PXM
        if v == 'top': Y = Z - CAM_Z
        px = (c['x_left'] - x0) + (X + c['span_m'] / 2) / sx
        py = (c['ground_y'] - y0) - (Z / sz_ if v != 'top' else (Y + c['top_m'] / 2) / sz_ - (c['ground_y'] - c['top_y']))
        ok = (px >= 0) & (px < ref.shape[1] - 1) & (py >= 0) & (py < ref.shape[0] - 1)
        R = np.zeros_like(mm); R[ok] = ref[py[ok].astype(int), px[ok].astype(int)]
        if v != 'top': R &= Z >= 0; mm = mm & (Z >= 0)
        iou = (R & mm).sum() / max((R | mm).sum(), 1)
        cols = np.where(R.any(0) & mm.any(0))[0]
        te = np.mean([abs(np.argmax(R[:, c_]) - np.argmax(mm[:, c_])) for c_ in cols]) / PXM if len(cols) else float('nan')
        ov = np.zeros((H, W, 3), np.uint8); ov[R & mm] = (230, 230, 230); ov[R & ~mm] = (255, 80, 60); ov[mm & ~R] = (40, 200, 255)
        sbs = Image.new('RGB', (W * 2, H), (0, 0, 0)); sbs.paste(Image.fromarray(pan.astype(np.uint8)).resize((W, H)), (0, 0)); sbs.paste(Image.fromarray(ov), (W, 0))
        sbs.save(os.path.join(ROOT, 'compare/compare_%s_%s.png' % (v, tag)))
        out.append(dict(view=v, iou=round(float(iou), 4), top_err_m=round(float(te), 2)))
    return out

def sheet_image(tag, rows):
    """comparison sheet: model ortho beauty renders (front/right/top/section) + masks + dimension table"""
    views = ['front', 'right', 'top', 'section']
    tiles = []
    for v in views:
        p = os.path.join(ROOT, 'renders/ortho/%s_%s.png' % (v, tag))
        if not os.path.exists(p): p = os.path.join(ROOT, 'renders/ortho/%s_final.png' % v)
        im = Image.open(p).convert('RGB').resize((520, 520)) if os.path.exists(p) else Image.new('RGB', (520, 520))
        d = ImageDraw.Draw(im)
        if v != 'top':
            for z, lab in ((0, '±0'), (48, '48'), (180, '180'), (320, '320'), (360, '360'), (400, '400'), (420, '420')):
                yy = 260 - (z - CAM_Z) * PXM * 520 / 1380
                d.line([(0, yy), (40, yy)], fill=(255, 190, 90), width=1); d.text((2, yy - 16), lab, fill=(255, 190, 90), font=FONT)
        d.text((10, 490), v.upper(), fill=(0, 240, 255), font=FONT)
        tiles.append(im)
    W = Image.new('RGB', (520 * 4, 520 + 40 + 26 * (len(rows) + 1)), (8, 10, 18)); d = ImageDraw.Draw(W)
    for i, t in enumerate(tiles): W.paste(t, (520 * i, 0))
    y = 530
    d.text((10, y), '云巅博物馆 · dimension check (%s): item / model / target / err / ok' % tag, fill=(255, 200, 120), font=FONT); y += 30
    for r in rows:
        d.text((10, y), '%-40s %8.2f  %8s  %7.2f  %s' % (r['item'], r['model'], r['target'], r['err'], 'OK' if r['ok'] else 'X'), fill=(200, 240, 255) if r['ok'] else (255, 90, 80), font=FONT); y += 26
    W.save(os.path.join(ROOT, 'compare/comparison_sheet_%s.png' % tag))

def run(tag):
    rows = dimension_check(tag)
    sc = sheet_compare(tag)
    sheet_image(tag, rows)
    json.dump(dict(dimension_check=rows, sheet=sc), open(os.path.join(ROOT, 'compare/scores_%s.json' % tag), 'w'), indent=1)
    for r in rows: print(('OK ' if r['ok'] else 'XX ') + '%-42s model %8.2f target %s err %6.2f' % (r['item'], r['model'], r['target'], r['err']))
    print('sheet IoU:', sc if sc is not None else 'n/a (ref/calib.json + sheet image missing)')

if __name__ == '__main__':
    run(sys.argv[1])
