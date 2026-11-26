"""Validation of the solid-soil substructure model: (1) modal coupling vs direct coupled solve, (2) impedance interpolation error.
usage: python validate_solid.py <case>   -> results/verify_solid_<case>.csv"""
import sys, numpy as np, time, csv, pathlib
from coupled import SolidCase
ROOT = pathlib.Path(__file__).resolve().parents[1]
cid = sys.argv[1]; t = 0.1 if 't10' in cid else 0.2; bur = 'bur' in cid
sc = SolidCase(t, bur)
fg = np.geomspace(40, 1450, 40); sc.prepare(fg, verbose=False)
rows = [['f_Hz', 'rel_err_velocity_modal_vs_direct', 'rel_err_impedance_spline']]
for f in (63.0, 125.0, 250.0, 500.0, 900.0):
    r = sc.solve([f])['v'][0, :, 0]
    U = sc.direct(f); w = 2 * np.pi * f
    vd = 1j * w * (sc.case.Pvel @ U)
    e1 = np.linalg.norm(r - vd) / np.linalg.norm(vd)
    Zs, Ze = sc.spl(f), sc.Zsoil(f); e2 = np.linalg.norm(Zs - Ze) / np.linalg.norm(Ze)
    rows.append([f, f'{e1:.4f}', f'{e2:.5f}']); print(f, rows[-1], flush=True)
with open(ROOT / 'results' / f'verify_solid_{cid}.csv', 'w', newline='') as fh: csv.writer(fh).writerows(rows)
