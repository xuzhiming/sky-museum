"""coordinate-descent tuning of exterior parameters against the sheet reference masks (mean IoU over 6 views).
each evaluation: exterior-only build -> /tmp/tune.blend -> 6 mask renders -> compare. results appended to compare/tune/tune_log.jsonl"""
import subprocess, json, os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
from compare import sheet_compare
ENV = dict(os.environ, SKY_EXT_ONLY='1', SKY_BLEND='/tmp/tune.blend')
def evaluate(ovr):
    env = dict(ENV, SKY_OVR=json.dumps(ovr))
    subprocess.run(['python3', 'build.py'], cwd=HERE, env=env, capture_output=True, check=True)
    subprocess.run(['python3', 'render.py', '--views', 'front_mask,right_mask,top_mask,back_mask,left_mask,section_mask', '--tag', 'tune'], cwd=HERE, env=env, capture_output=True, check=True)
    sc = sheet_compare('tune'); W = dict(section=float(os.environ.get('SEC_W', 0.5))); m = float(sum(r['iou'] * W.get(r['view'], 1.0) for r in sc) / sum(W.get(r['view'], 1.0) for r in sc))
    with open(os.path.join(ROOT, 'compare/tune/tune_log.jsonl'), 'a') as f: f.write(json.dumps(dict(ovr=ovr, mean=m, views={r['view']: r['iou'] for r in sc})) + '\n')
    return m, sc
if __name__ == '__main__':
    spec = json.load(open(sys.argv[1]))          # {"start": {...}, "steps": {"key": step, ...}, "passes": 2}
    cur = dict(spec.get('start', {})); best, _ = evaluate(cur); print('start', round(best, 4), flush=True)
    for p in range(spec.get('passes', 1)):
        for k, st in spec['steps'].items():
            base = cur.get(k, spec['base'][k])
            improved = True
            while improved:
                improved = False
                for d in (+st, -st):
                    cand = dict(cur); cand[k] = round(base + d, 4)
                    m, _ = evaluate(cand)
                    if m > best + 1e-4:
                        best, cur, base, improved = m, cand, cand[k], True
                        print('pass', p, k, cand[k], round(best, 4), flush=True); break
        st_ = {k: v / 2 for k, v in spec['steps'].items()}; spec['steps'] = st_
    print('BEST', round(best, 4), json.dumps(cur))
    json.dump(dict(best=best, ovr=cur), open(os.path.join(ROOT, 'compare/tune/tune_best.json'), 'w'), indent=1)
