"""Excitation tests: uniform annular axial load vs 6 discrete segments (0 deg and 30 deg offset); torque transfer in Pa/(N m).
In-house modal FEM + BEM (dx=0.05) on t=100 mm exposed and t=200 mm buried, 70 log-spaced frequencies 44-1414 Hz."""
import numpy as np, csv, pathlib
from model import Case, freq_grid, PREF
from fem import soil_props
from dsp import *
ROOT = pathlib.Path(__file__).resolve().parents[1]
fr = freq_grid(1.0075 ** 2.5 * 1.0 + 0.0, 44.19, 1414.3)
fr = np.geomspace(44.19, 1414.3, 90)
import sys
DX = float(sys.argv[1]) if len(sys.argv) > 1 else 0.05
rows = []; summ = {}
for cid, (t, bur) in ((('t10_exp', (0.1, False)),) if DX < 0.04 else (('t10_exp', (0.1, False)), ('t20_bur', (0.2, True)))):
    c = Case(t, bur, dx=DX, dp=0.05, soil=soil_props(eta=0.0), nmodes=60, modal=True, bem=True)
    r = c.sweep(fr, keep_v=False); p = r['p']             # (nf, nmic, 4)
    L = [tf_band_level(fr, p[:, :3, k], EDGES[:5]) for k in range(4)]     # axial uniform, torque, seg0, seg30 ; (5 bands, 3 mics)
    d0 = L[2] - L[0]; d30 = L[3] - L[0]
    nar = 20 * np.log10(np.abs(p[:, :3, 2]) / np.abs(p[:, :3, 0]))
    for bi, lab in enumerate(LABEL[:5]):
        rows.append([cid, lab, f'{d0[bi].max():+.2f}', f'{d30[bi].max():+.2f}', f'{L[1][bi, 0]:.1f}', f'{L[0][bi, 0]:.1f}'])
    summ[cid] = (np.abs(d0).max(), np.abs(d30).max(), np.abs(nar).max())
    print(cid, 'max |band-level change| 6-seg(0deg) %.2f dB, 6-seg(30deg) %.2f dB; max narrowband change %.2f dB' % summ[cid])
with open(ROOT / 'results' / f'verify_segments_dx{DX:g}.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh); w.writerow(['case', 'band_Hz', 'seg6_0deg_minus_uniform_max_dB', 'seg6_30deg_minus_uniform_max_dB', 'torque_band_dB_re20uPa_per_Nm_micF', 'axial_band_dB_re20uPa_per_N_micF']); w.writerows(rows)
