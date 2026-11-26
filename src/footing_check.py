"""Soil block check: vertical dynamic stiffness of a rigid 1 x 1 m surface footing vs the Gazetas/Lysmer closed forms.
K_static = 4.54 G L / (1 - nu) (L = half side), c ~ rho V_La A with V_La = 3.4 Vs / (pi (1 - nu)). Uses the same Soil class and graded mesh generator."""
import numpy as np, sys, csv, pathlib
import solidmesh as sm
from soil_solid import Soil
ROOT = pathlib.Path(__file__).resolve().parents[1]
Vs, rho, nu = 200.0, 1800.0, 0.3; G = rho * Vs ** 2; L = 0.5; A = 1.0
Ks = 4.54 * G * L / (1 - nu); Vla = 3.4 * Vs / (np.pi * (1 - nu)); c = rho * Vla * A
rows = [['Lx_m', 'D_m', 'f_Hz', 'a0', 'K_model_re', 'K_model_im', 'K_ref_re', 'K_ref_im', 'ratio_re', 'ratio_im']]
for (Lx, D) in ((1.5, 2.0), (2.0, 2.5)):
    m = sm.build(1.0, False, Lx=Lx, Ly=Lx, D=D); s = Soil(m, eta=0.05)
    zi = [k for k, g in enumerate(s.idof) if g % 3 == 2]
    for f in (30, 100, 300):
        w = 2 * np.pi * f; Dc = s.D_cond(w)
        K = 2 * Dc[np.ix_(zi, zi)].sum()                 # full footing = 2 x half; u_z = 1 on all footing nodes, other dofs rigid
        a0 = w * L / Vs; Kref = Ks * (1 - 0.15 * a0 ** 2 * 0) + 1j * w * c       # static real part + radiation dashpot (high-frequency form)
        rows.append([Lx, D, f, f'{a0:.2f}', f'{K.real:.3e}', f'{K.imag:.3e}', f'{Kref.real:.3e}', f'{Kref.imag:.3e}', f'{K.real / Kref.real:.2f}', f'{K.imag / Kref.imag:.2f}'])
        print(rows[-1], flush=True)
with open(ROOT / 'results' / 'verify_footing.csv', 'w', newline='') as fh: csv.writer(fh).writerows(rows)
