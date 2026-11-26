"""Run the solid-soil model for one case: soil impedance on a coarse frequency grid (spline), modal coupling on a 1 Hz grid.
usage: python run_solid_cases.py <case> [tag=_solid] [Vs=200] [eta_s=0.05] [Lx=1.5] [D=2.0] [g=1.2] [hmax=0.2] [coarse]
Output: results/ccx_<case><tag>.npz (same layout as the CalculiX results, so post.py / analyze.py can read it with tag=<tag>)."""
import sys, time, numpy as np, pathlib
from coupled import SolidCase
ROOT = pathlib.Path(__file__).resolve().parents[1]
cid = sys.argv[1]; tag = sys.argv[2] if len(sys.argv) > 2 else '_solid'
Vs = float(sys.argv[3]) if len(sys.argv) > 3 else 200.0; eta_s = float(sys.argv[4]) if len(sys.argv) > 4 else 0.05
Lx = float(sys.argv[5]) if len(sys.argv) > 5 else 1.5; D = float(sys.argv[6]) if len(sys.argv) > 6 else 2.0
g = float(sys.argv[7]) if len(sys.argv) > 7 else 1.2; hmax = float(sys.argv[8]) if len(sys.argv) > 8 else 0.20
t = 0.1 if 't10' in cid else 0.2; bur = 'bur' in cid
t0 = time.time()
sc = SolidCase(t, bur, Vs=Vs, eta_s=eta_s, Lx=Lx, Ly=Lx, D=D, g=g, hmax=hmax)
coarse = len(sys.argv) > 9 and sys.argv[9] == 'coarse'
fg = np.concatenate([np.arange(40, 400, 24.0), np.arange(400, 1460, 50.0)]) if coarse else np.concatenate([np.arange(40, 400, 12.0), np.arange(400, 1460, 25.0)])
sc.prepare(fg, verbose=True)
# interpolation check at points between the grid nodes
chk = []
for f in (455.0, 705.0, 1005.0, 1305.0):
    Zs, Ze = sc.spl(f), sc.Zsoil(f); chk.append((f, np.linalg.norm(Zs - Ze) / np.linalg.norm(Ze)))
print('spline check', [(f, round(e, 4)) for f, e in chk], flush=True)
freqs = np.arange(44.0, 1415.0, 1.0)
res = sc.solve(freqs)
c = sc.case
np.savez(ROOT / 'results' / f'ccx_{cid}{tag}.npz', freq=res['freq'], v=res['v'], acc=res['acc'], eig=sc.fn[:60], corners=c.panels.corners, tags=c.tags, t=t, buried=bur,
         dx=0.05, nmodes=sc.nm, Vs=Vs, eta_s=eta_s, Lx=Lx, D=D, g=g, hmax=hmax, runtime=time.time() - t0, spline_check=np.array(chk))
print(f'{cid}{tag}: done {time.time() - t0:.0f} s', flush=True)
