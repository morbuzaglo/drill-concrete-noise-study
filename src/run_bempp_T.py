"""Bempp-cl acoustic transfer vectors for the four cases.  Low band (44-500 Hz): 0.10 m panels, step 20 Hz;
high band (540-1420 Hz): 0.05 m panels, step 80 Hz.  Results are expressed on the fine (0.05 m) structural panels.
usage: python run_bempp_T.py [workers]   -> results/bempp_T_<case>.npz"""
import sys, time, pathlib, numpy as np
from concurrent.futures import ProcessPoolExecutor
ROOT = pathlib.Path(__file__).resolve().parents[1]
_ctx = {}


def work(a):
    key, corners, f, mics = a
    from bempp_T import Ctx, T_at
    if key not in _ctx: _ctx[key] = Ctx(corners)
    t = time.time(); T = T_at(_ctx[key], f, mics)
    return key, f, T, time.time() - t


def fold_matrix(cf, tf, cc, tc):
    """average fine-panel values onto coarse panels (nq_c x nq_f); panels matched by face tag and containment."""
    cen_f = cf.mean(1); M = np.zeros((len(cc), len(cf)))
    lo = cc.min(1) - 1e-9; hi = cc.max(1) + 1e-9
    for j in range(len(cf)):
        m = np.all(tc == tf[j], axis=1) & np.all(cen_f[j] >= lo, axis=1) & np.all(cen_f[j] <= hi, axis=1)
        idx = np.nonzero(m)[0]; assert len(idx) == 1, (j, idx)
        M[idx[0], j] = 1
    return M / M.sum(1, keepdims=True)


def main(workers=3):
    from model import Case, mic_positions
    cases = {'t10_exp': (0.10, False), 't10_bur': (0.10, True), 't20_exp': (0.20, False), 't20_bur': (0.20, True)}
    f_low = np.arange(44.0, 500.1, 20.0); f_high = np.arange(540.0, 1421.0, 80.0)
    tasks = []; geo = {}
    for cid, (t, bur) in cases.items():
        cf = Case(t, bur, dp=0.05, modal=False, bem=False); cc = Case(t, bur, dp=0.1, modal=False, bem=False)
        mics = np.array(list(mic_positions(t).values()))
        geo[cid] = dict(cf=cf.panels.corners, tf=cf.tags, cc=cc.panels.corners, tc=cc.tags, mics=mics, M=fold_matrix(cf.panels.corners, cf.tags, cc.panels.corners, cc.tags))
        for f in f_high: tasks.append(((cid, 'f'), geo[cid]['cf'], f, mics))
    for cid in cases:
        for f in f_low: tasks.append(((cid, 'c'), geo[cid]['cc'], f, geo[cid]['mics']))
    print('tasks', len(tasks), flush=True)
    res = {}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for n, (key, f, T, dt) in enumerate(ex.map(work, tasks, chunksize=1)):
            res.setdefault(key, []).append((f, T)); print(f'{n + 1}/{len(tasks)} {key} f={f:.0f} {dt:.0f}s  elapsed {time.time() - t0:.0f}s', flush=True)
    for cid in cases:
        low = sorted(res[(cid, 'c')], key=lambda x: x[0]); high = sorted(res[(cid, 'f')], key=lambda x: x[0])
        M = geo[cid]['M']
        Tlow = np.array([T @ M for f, T in low])            # (nf, nmic, nq_fine)
        Thigh = np.array([T for f, T in high])
        np.savez_compressed(ROOT / 'results' / f'bempp_T_{cid}.npz', f_low=np.array([f for f, _ in low]), T_low=Tlow,
                            f_high=np.array([f for f, _ in high]), T_high=Thigh, mics=geo[cid]['mics'], corners=geo[cid]['cf'], tags=geo[cid]['tf'])
    print('done', time.time() - t0)


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
