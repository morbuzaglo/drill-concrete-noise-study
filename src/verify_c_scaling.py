"""Verification (c): doubling the excitation doubles complex velocity and pressure (+6.02 dB). CalculiX SSD with loads F and 2F,
pressure from the in-house BEM on the CalculiX velocities (linear operator) and the Bempp transfer vectors when available."""
import numpy as np, pathlib, csv
from model import Case
from fem import soil_props
from ccx_runner import *
ROOT = pathlib.Path(__file__).resolve().parents[1]
job = ROOT / 'results' / 'verify' / 'scaling'; job.mkdir(parents=True, exist_ok=True)
c = Case(0.1, False, dx=0.05, dp=0.05, soil=soil_props(eta=0.0), modal=False, bem=True)
F = np.stack([c.F[:, 0], 2.0 * c.F[:, 0]], 1)
bands = [(100.0, 700.0, 4)]
sn = write_inp(c, job / 'job.inp', bands, nmodes=40, loads=F)
rc, dt, out = run_ccx(str(job), 'job', log=job / 'job.log', threads=1); print('ccx rc', rc, '%.0fs' % dt)
fr, ids, U, eig = collect(job / 'job.dat', len(sn), 2, bands)
w = 2 * np.pi * fr; rows = []; devp = []; devv = []; devdB = []
for i, f in enumerate(fr):
    v = []
    for k in range(2):
        u = np.zeros(c.slab.ndof, complex); u[(3 * (ids[:, None] - 1) + np.arange(3)[None, :])] = U[k, i]; v.append(1j * w[i] * (c.Pvel @ u))
    v = np.array(v).T
    p = c.bem.solve(w[i], v)['p_mic']
    rv = np.linalg.norm(v[:, 1]) / np.linalg.norm(v[:, 0]); rp = np.abs(p[:, 1] / p[:, 0])
    ph = np.abs(np.angle(p[:, 1] / p[:, 0]))
    dB = 20 * np.log10(np.abs(p[:, 1]) / np.abs(p[:, 0]))
    rows.append([f'{f:.1f}', f'{rv:.8f}', f'{rp.min():.8f}', f'{rp.max():.8f}', f'{dB.min():.4f}', f'{dB.max():.4f}', f'{ph.max():.2e}'])
    devp.append(np.max(np.abs(rp - 2))); devv.append(abs(rv - 2)); devdB.append(np.max(np.abs(dB - 6.0206)))
with open(ROOT / 'results' / 'verify_c_scaling.csv', 'w', newline='', encoding='utf-8') as fh:
    wr = csv.writer(fh); wr.writerow(['f_Hz', 'velocity_ratio', 'p_ratio_min', 'p_ratio_max', 'dSPL_min_dB', 'dSPL_max_dB', 'max_phase_dev_rad']); wr.writerows(rows)
print('frequencies', len(fr)); print('max |v ratio - 2| = %.2e' % max(devv)); print('max |p ratio - 2| = %.2e' % max(devp)); print('max |dSPL - 6.0206| = %.2e dB' % max(devdB))
