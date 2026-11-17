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
        # sheet: W/D 360 envelope; the drawn base tapers continuously (no setback at 48 - base 0-48 is the titanium podium band)
        add('%s: base width @z=4 (340..362, within 360 envelope)' % v, np.mean(w(4.0)), 351.0, 11.0)
        wt = 2 * P.Ro(46.0) * max(1.0, P.FAN['r_scale'] * math.cos(math.radians(45 - P.FAN['half_deg'])))   # fans project beyond the arm tips
        add('%s: base width @z=46 (taper + fans)' % v, np.mean(w(46.0)), round(wt, 1), 12.0)   # side view also carries the 3 m portal frame
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
        for zz in (120.0, 150.0, 220.0, 308.0, 340.0, 385.0):   # stations clear of the saucer pods
            add('%s: width @z=%d (param Ro)' % (v, zz), np.mean(w(zz)), round(2 * P.Ro(zz), 1), 5.0)   # layered ribs / joints / cyan strips stand ~2 m proud per side
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
    # lobes = 4 pointed cardinal arms + 4 diagonal fans: local maxima of r(theta) with >= 4 m prominence
    from scipy.signal import find_peaks
    sm = np.convolve(np.concatenate([rad[-15:], rad, rad[:15]]), np.ones(15) / 15, 'same')[15:-15]
    ext = np.concatenate([sm, sm[:100]])
    # lobes = circular runs of the smoothed footprint radius standing >= 5 m above the valley minimum
    # (flat-topped fans carry facade-detail ripples, so peak picking over-/under-counts them)
    hi = sm > sm.min() + 5.0
    lobes = int(np.sum(hi & ~np.roll(hi, 1))) if not hi.all() else 1
    add('top: arm/lobe count (r(theta) peaks)', lobes, 8, 0)
    add('top: valley radius at podium (min r)', rad.min(), round(P.Ri(0), 1), 4.0)
    xs_ = np.where(m.any(0))[0]; ys_ = np.where(m.any(1))[0]
    add('top: plan extent W (x)', (xs_.max() - xs_.min()) / PXM, P.W_BASE, 6.0)
    add('top: plan extent D (y)', (ys_.max() - ys_.min()) / PXM, P.D_BASE, 6.0)
    return rows

def sheet_compare(tag):
    """reference masks ref/refmask_<view>.png (made by refmask.py from the design sheet panels, already in the model's
    3 px/m ortho frame) vs model mask renders. metrics: IoU, mean top-edge error (m), mean width-profile error (m, per 5 m row).
    elevations compared for z >= 4 m (sheet ground lines / labels removed)."""
    out = []
    for v in ['front', 'back', 'left', 'right', 'top', 'section']:
        rp = os.path.join(ROOT, 'ref/refmask_%s.png' % v)
        mp = os.path.join(ROOT, 'renders/ortho/%s_mask_%s.png' % (v, tag))
        if not (os.path.exists(rp) and os.path.exists(mp)): continue
        R = np.asarray(Image.open(rp).convert('L')) > 128
        mm = np.asarray(Image.open(mp).convert('L')) > 30
        H, W = mm.shape
        if v != 'top':
            Z = CAM_Z + (H / 2 - np.arange(H)) / PXM
            keep = (Z >= 4.0)[:, None]; R = R & keep; mm = mm & keep
        iou = (R & mm).sum() / max((R | mm).sum(), 1)
        cols = np.where(R.any(0) | mm.any(0))[0]
        def top(M, c_): return np.argmax(M[:, c_]) if M[:, c_].any() else H
        te = np.mean([abs(top(R, c_) - top(mm, c_)) for c_ in cols]) / PXM if len(cols) else float('nan')
        rows = range(0, H, 15)
        wr = [abs(R[r].sum() - mm[r].sum()) / PXM for r in rows if R[r].any() or mm[r].any()]
        we = float(np.mean(wr)) if wr else float('nan')
        ov = np.zeros((H, W, 3), np.uint8); ov[R & mm] = (230, 230, 230); ov[R & ~mm] = (255, 80, 60); ov[mm & ~R] = (40, 200, 255)
        pan = Image.open(os.path.join(ROOT, 'ref/panelm_%s.png' % v)).convert('RGB') if os.path.exists(os.path.join(ROOT, 'ref/panelm_%s.png' % v)) else Image.new('RGB', (W, H))
        sbs = Image.new('RGB', (W * 2, H), (0, 0, 0)); sbs.paste(pan.resize((W, H)), (0, 0)); sbs.paste(Image.fromarray(ov), (W, 0))
        sbs.resize((W, H // 2)).save(os.path.join(ROOT, 'compare/compare_%s_%s.png' % (v, tag)))
        out.append(dict(view=v, iou=round(float(iou), 4), top_err_m=round(float(te), 2), width_err_m=round(we, 2)))
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
    for r in sc or []: print('SHEET %-8s IoU %.4f  top-edge %6.2f m  width %6.2f m' % (r['view'], r['iou'], r['top_err_m'], r['width_err_m']))
    if sc: print('SHEET mean IoU %.4f' % np.mean([r['iou'] for r in sc]))

if __name__ == '__main__':
    run(sys.argv[1])
