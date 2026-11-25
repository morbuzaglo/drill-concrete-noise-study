"""Acoustic-mesh convergence: in-house BEM with 0.10 m panels (CalculiX velocities averaged onto coarse panels) at every frequency."""
import sys, numpy as np, pathlib, time
from model import Case, mic_positions
from bem import BEM
from post import *
from run_bempp_T import fold_matrix
ROOT = pathlib.Path(__file__).resolve().parents[1]
for cid in CASES:
    out = ROOT / 'results' / f'ownbem01_{cid}_dx0.05.npz'
    if out.exists(): continue
    r = load_ccx(cid, '_dx0.05'); t0 = time.time()
    cf = Case(r['t'], r['buried'], dx=0.05, dp=0.05, modal=False, bem=False); cc = Case(r['t'], r['buried'], dx=0.05, dp=0.1, modal=False, bem=True)
    M = fold_matrix(cf.panels.corners, cf.tags, cc.panels.corners, cc.tags)
    p = np.array([cc.bem.solve(2 * np.pi * f, (M @ r['v'][i, :, :1]))['p_mic'][:, 0] for i, f in enumerate(r['freq'])])
    np.savez(out, f=r['freq'], p=p); print(cid, '%.0fs' % (time.time() - t0), flush=True)
