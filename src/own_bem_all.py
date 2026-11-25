"""In-house BEM applied to the CalculiX panel velocities at every CalculiX frequency (dense-grid acoustic cross-check)."""
import sys, numpy as np, pathlib, time
from model import Case, mic_positions
from post import *
ROOT = pathlib.Path(__file__).resolve().parents[1]
tag = sys.argv[1] if len(sys.argv) > 1 else '_dx0.05'
for cid in CASES:
    out = ROOT / 'results' / f'ownbem_{cid}{tag}.npz'
    if out.exists(): continue
    r = load_ccx(cid, tag); t0 = time.time()
    c = Case(r['t'], r['buried'], dx=0.05, dp=0.05, modal=False, bem=True)
    p = np.array([c.bem.solve(2 * np.pi * f, r['v'][i, :, :1])['p_mic'][:, 0] for i, f in enumerate(r['freq'])])
    np.savez(out, f=r['freq'], p=p); print(cid, '%.0fs' % (time.time() - t0), flush=True)
