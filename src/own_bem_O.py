"""Oblique microphone O=(-0.7, 1.7, 1.0) m from the in-house BEM on the CalculiX velocities (mic S lies in the slab mid-plane = dipole null)."""
import sys, numpy as np, pathlib, time
from model import Case
from bem import BEM
from post import *
ROOT = pathlib.Path(__file__).resolve().parents[1]
tag = sys.argv[1] if len(sys.argv) > 1 else '_dx0.05'
MO = np.array([[-0.7, 1.7, 1.0]])
for cid in CASES:
    out = ROOT / 'results' / f'ownbemO_{cid}{tag}.npz'
    if out.exists(): continue
    r = load_ccx(cid, tag); t0 = time.time()
    c = Case(r['t'], r['buried'], dx=0.05, dp=0.05, modal=False, bem=False)
    bem = BEM(c.panels, ground=True, chief=c.chief, mics=MO)
    p = np.array([bem.solve(2 * np.pi * f, r['v'][i, :, :1])['p_mic'][:, 0] for i, f in enumerate(r['freq'])])
    np.savez(out, f=r['freq'], p=p); print(cid, '%.0fs' % (time.time() - t0), flush=True)
