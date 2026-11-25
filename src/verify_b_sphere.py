"""Verification (b): pulsating sphere with prescribed uniform surface velocity vs the analytical solution.
Bempp-cl (free field, direct Burton-Miller), Bempp-cl hemisphere over a rigid ground (image method, transfer-vector path used by the study),
in-house BEM (free field and ground). a = 0.25 m, v0 = 1 m/s. Tolerance 0.5 dB, 5 degrees."""
import numpy as np, csv, pathlib
from bem import sphere_panels, pulsating_sphere_exact, C0, Panels, BEM
from bempp_ac import Radiator
from bempp_T import Ctx, T_at
ROOT = pathlib.Path(__file__).resolve().parents[1]
a = 0.25; v0 = 1.0
KA = [0.5, 1.0, 2.0, 3.0, np.pi, 4.0]
pts_free = np.array([[0.5, 0, 0], [1.0, 0, 0.3], [2.0, 0, 0]])
pts_gnd = np.array([[0.5, 0, 0.01], [1.0, 0, 0.3], [2.0, 0, 0.5]])
rows = []
def rec(method, ka, pts, p):
    rr = np.linalg.norm(pts, axis=1); pe = pulsating_sphere_exact(ka * C0 / a, a, v0, rr)
    for k in range(len(rr)):
        rows.append([method, f'{ka:.3f}', f'{rr[k]:.2f}', f'{20 * np.log10(abs(p[k]) / abs(pe[k])):+.3f}', f'{np.degrees(np.angle(p[k] / pe[k])):+.2f}'])
rng = np.random.default_rng(2)
# Bempp free field, N=10 (1200 triangles)
R = Radiator(sphere_panels(a, 10))
for ka in KA:
    f = ka * C0 / a / (2 * np.pi); p = R.solve(f, np.full((R.nq, 1), v0, complex), pts_free)[:, 0]; rec('Bempp-cl free field (N=10)', ka, pts_free, p)
# Bempp hemisphere on rigid ground via transfer vectors (as used in the study), N=8
ctx = Ctx(sphere_panels(a, 8, half=True))
for ka in KA:
    f = ka * C0 / a / (2 * np.pi); p = T_at(ctx, f, pts_gnd) @ np.full(ctx.nq_exp, v0); rec('Bempp-cl hemisphere + rigid ground (N=8)', ka, pts_gnd, p)
# in-house BEM
c = sphere_panels(a, 12); P = Panels(c, project_radius=a)
ch = rng.normal(size=(12, 3)); ch = ch / np.linalg.norm(ch, axis=1)[:, None] * a * rng.uniform(0.1, 0.7, 12)[:, None]
B = BEM(P, ground=False, chief=ch, mics=pts_free)
for ka in KA: rec('in-house BEM free field (N=12)', ka, pts_free, B.solve(ka * C0 / a, np.full((P.n, 1), v0, complex))['p_mic'][:, 0])
c = sphere_panels(a, 12, half=True); P = Panels(c, project_radius=a); ch[:, 2] = np.abs(ch[:, 2]) + 0.01
B = BEM(P, ground=True, chief=ch, mics=pts_gnd)
for ka in KA: rec('in-house BEM hemisphere + ground (N=12)', ka, pts_gnd, B.solve(ka * C0 / a, np.full((P.n, 1), v0, complex))['p_mic'][:, 0])
with open(ROOT / 'results' / 'verify_b_sphere.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh); w.writerow(['method', 'ka', 'r_m', 'level_error_dB', 'phase_error_deg']); w.writerows(rows)
for m in dict.fromkeys(r[0] for r in rows):
    e = [abs(float(r[3])) for r in rows if r[0] == m]; ph = [abs(float(r[4])) for r in rows if r[0] == m]
    print(f'{m}: max |level error| {max(e):.3f} dB, max |phase error| {max(ph):.2f} deg')
