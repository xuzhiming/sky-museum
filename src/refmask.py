"""segment the sheet panels -> metric masks in the model's ortho frame (3 px/m, 1380x1380, centre x=0, z=215)"""
import json, os, sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PXM = 1380 / 460.0; CAM_Z = 215.0; N = 1380

def panel_mask(c, sheet):
    x0, y0, x1, y1 = c['crop']
    pan = sheet[y0:y1, x0:x1].astype(float)
    # background: per-row median of the panel's outer columns (navy gradient)
    if 'bg' in c:
        # background = per-channel linear fit in y through the bg patches (vertical navy gradient)
        ys = np.array([(b[1] + b[3]) / 2 for b in c['bg']]); cols = np.array([np.median(sheet[b[1]:b[3], b[0]:b[2]].reshape(-1, 3), 0) for b in c['bg']]).astype(float)
        if np.ptp(ys) > 50:
            A = np.stack([ys, np.ones_like(ys)], 1); coef = np.linalg.lstsq(A, cols, rcond=None)[0]
            yy = np.arange(y0, y1)[:, None]; bg = (yy * coef[0] + coef[1])[:, None, :]
        else:
            bg = cols.mean(0)[None, None, :] * np.ones((pan.shape[0], 1, 1))
    else:
        edge = np.concatenate([pan[:, :6], pan[:, -6:]], 1)
        bg = np.median(edge, 1)[:, None, :]
    d = np.abs(pan - bg).sum(2)
    lum = pan.mean(2); bgl = bg.mean(2)
    m = (d > c.get('thr', 34)) | (lum > bgl + 22)
    for e in c.get('excl', []):
        m[max(0, e[1] - y0):e[3] - y0, max(0, e[0] - x0):e[2] - x0] = False
    gy = c['ground_y'] - y0
    if c.get('top_m') == 420: m[gy - 3:, :] = False     # drop the plaza / ground glow strip (compare from z >= 4 m)
    m = ndi.binary_closing(m, np.ones((3, 3)), iterations=c.get('close', 4))
    m = ndi.binary_fill_holes(m)
    m = ndi.binary_opening(m, np.ones((3, 3)), iterations=2)
    if 'mirror_below_y' in c:
        r0 = c['mirror_below_y'] - y0; xc = int(round((c['x_left'] + c['x_right']) / 2 - x0))
        w = min(xc, m.shape[1] - xc)
        m[r0:, xc - w:xc] = m[r0:, xc:xc + w][:, ::-1]
    lab, n = ndi.label(m)
    if n > 1:
        sz = ndi.sum(m, lab, range(1, n + 1)); keep = [i + 1 for i, s in enumerate(sz) if s > 0.01 * sz.max()]
        m = np.isin(lab, keep)
    return m

def to_metric(view, c, m):
    x0, y0, x1, y1 = c['crop']
    sx = (c['x_right'] - c['x_left']) / c['span_m']
    sz = (c['ground_y'] - c['top_y']) / c['top_m']
    xc = (c['x_left'] + c['x_right']) / 2
    yy, xx = np.mgrid[0:N, 0:N]
    X = (xx - N / 2) / PXM
    if view == 'top':
        Y = (N / 2 - yy) / PXM            # blender +y up in the top render
        yc = (c['ground_y'] + c['top_y']) / 2
        px = xc + X * sx - x0; py = yc - Y * sz - y0
    else:
        Z = CAM_Z + (N / 2 - yy) / PXM
        px = xc + X * sx - x0; py = c['ground_y'] - Z * sz - y0
    ok = (px >= 0) & (px < m.shape[1] - 1) & (py >= 0) & (py < m.shape[0] - 1)
    R = np.zeros((N, N) + m.shape[2:], m.dtype); R[ok] = m[py[ok].astype(int), px[ok].astype(int)]
    return R

def build():
    C = json.load(open(os.path.join(ROOT, 'ref/calib.json')))
    out = {}
    for v, c in C.items():
        if v.startswith('_'): continue
        sheet = np.asarray(Image.open(os.path.join(ROOT, c['sheet'])).convert('RGB'))
        m = panel_mask(c, sheet)
        Image.fromarray((m * 255).astype(np.uint8)).save(os.path.join(ROOT, 'ref/panelmask_%s.png' % v))
        R = to_metric(v, c, m)
        Image.fromarray((R * 255).astype(np.uint8)).save(os.path.join(ROOT, 'ref/refmask_%s.png' % v))
        x0, y0, x1, y1 = c['crop']
        Image.fromarray(sheet[y0:y1, x0:x1]).save(os.path.join(ROOT, 'ref/panel_%s.png' % v))
        Image.fromarray(to_metric(v, c, np.ascontiguousarray(sheet[y0:y1, x0:x1]))).save(os.path.join(ROOT, 'ref/panelm_%s.png' % v))   # panel in the model frame
        out[v] = R
    return out

if __name__ == '__main__':
    R = build()
    for v, m in R.items(): print(v, m.sum())
