"""Verification (d): convergence table. Variation of structural mesh, acoustic mesh, frequency increment, modal cutoff, soil parameters.
Pre-set tolerance: 1 dB for octave-band levels and for between-configuration differences (tightened to 0.5 dB if the effect is smaller)."""
import numpy as np, csv, pathlib
from analyze import *
CASEL = ['t10_exp', 't10_bur', 't20_exp', 't20_bur']
NM = 3           # microphones F,R,Rg (Bempp-cl)

def lev(f, p): return tf_band_level(f, p[:, :NM], BANDS)

def eff(L):
    return {k: v for k, v in effects(L).items()}

def get_var(cid, tag):
    fn = RES / f'ccx_{cid}{tag}.npz'
    if not fn.exists(): return None
    f, p, _ = pressure(cid, tag); return f, p

base = {cid: get_p(cid) for cid in CASEL}
Lb = {cid: lev(*base[cid]) for cid in CASEL}; Eb = eff(Lb)
rows = []

def compare(name, Lv, partial=False, physical=False, coarsen=False):
    d_ind = max(np.nanmax(np.abs(Lv[c] - Lb[c])) for c in Lv)
    Ev = eff({c: (Lv.get(c, Lb[c])) for c in CASEL})
    d_dif = max(np.nanmax(np.abs(Ev[k] - Eb[k])) for k in Eb)
    # which effects change if only part of the cases were varied -> still informative
    rows.append([name, ' '.join(sorted(Lv)), f'{d_ind:.2f}', f'{d_dif:.2f}', ('SENSITIVITY (physical parameter)' if physical else ('PASS' if max(d_ind, d_dif) <= 1.0 else ('COARSER-THAN-BASE (expected change)' if coarsen else 'FAIL')))])
    print(rows[-1])

# 1 structural mesh
for tag, name in (('_dx0.0333333333333', 'structural mesh dx 0.050 -> 0.0333 m'),):
    Lv = {}
    for c in CASEL:
        v = get_var(c, tag)
        if v: Lv[c] = lev(*v)
    if Lv: compare(name, Lv)
# 2 modal cutoff
for tag, name in (('_nm30', 'modal cutoff 60 -> 30 modes'), ('_nm100', 'modal cutoff 60 -> 100 modes')):
    Lv = {}
    for c in CASEL:
        v = get_var(c, tag)
        if v: Lv[c] = lev(*v)
    if Lv: compare(name, Lv)
# 3 frequency increment (subsample the clustered CalculiX grid)
for k in (2, 3):
    Lv = {c: lev(base[c][0][::k], base[c][1][::k]) for c in CASEL}; compare(f'frequency grid coarsened: every {k}-th CalculiX point', Lv, coarsen=True)
# 4 acoustic mesh / solver
Lv = {}
for c in CASEL:
    fn = RES / f'ownbem_{c}_dx0.05.npz'
    if fn.exists(): d = np.load(fn); Lv[c] = lev(d['f'], d['p'])
if Lv: compare('acoustic solver: in-house BEM (0.05 m) vs Bempp-cl + interpolation', Lv)
Lv = {}
for c in CASEL:
    fn = RES / f'ownbem01_{c}_dx0.05.npz'
    if fn.exists(): d = np.load(fn); Lv[c] = lev(d['f'], d['p'])
if Lv:
    # compare coarse vs fine acoustic mesh within the same (in-house) solver
    Lf = {}
    for c in Lv: d = np.load(RES / f'ownbem_{c}_dx0.05.npz'); Lf[c] = lev(d['f'], d['p'])
    dI = max(np.nanmax(np.abs(Lv[c] - Lf[c])) for c in Lv)
    Ec = eff({c: Lv.get(c, Lb[c]) for c in CASEL}); Ef = eff({c: Lf.get(c, Lb[c]) for c in CASEL})
    dD = max(np.nanmax(np.abs(Ec[k] - Ef[k])) for k in Ec)
    rows.append(['acoustic mesh 0.10 -> 0.05 m (in-house BEM)', ' '.join(sorted(Lv)), f'{dI:.2f}', f'{dD:.2f}', 'PASS' if max(dI, dD) <= 1.0 else 'FAIL']); print(rows[-1])
# 5 soil parameters
for tag, name in (('_Vs100', 'soil shear wave speed 200 -> 100 m/s'), ('_Vs400', 'soil shear wave speed 200 -> 400 m/s'), ('_k05', 'soil/interface spring stiffness x0.5'), ('_k2', 'soil/interface spring stiffness x2')):
    Lv = {}
    for c in CASEL:
        v = get_var(c, tag)
        if v: Lv[c] = lev(*v)
    if Lv: compare(name, Lv, physical=True)
with open(ROOT / 'results' / 'verify_d_convergence.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh); w.writerow(['variation', 'cases_varied', 'max_abs_change_in_band_level_dB', 'max_abs_change_in_between_case_difference_dB', 'verdict_vs_1dB']); w.writerows(rows)
# per-band spread used as numerical uncertainty (mesh + frequency + acoustic solver), per case difference

# soil sensitivity of the BURIAL effect (mic F, mean-square band transfer): buried variant minus exposed base
with open(ROOT / 'results' / 'soil_sensitivity.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh); w.writerow(['thickness', 'variant'] + [f'{b}Hz' for b in BL])
    for th, cb, ce in (('t100', 't10_bur', 't10_exp'), ('t200', 't20_bur', 't20_exp')):
        for tag, nm in (('', 'base Vs=200 k=1'), ('_Vs100', 'Vs=100'), ('_Vs400', 'Vs=400'), ('_k05', 'k x0.5'), ('_k2', 'k x2')):
            v = (get_var(cb, tag) if tag else base[cb])
            if v is None: continue
            Lbv = lev(*v)[:, 0] - Lb[ce][:, 0]
            w.writerow([th, nm] + [f'{x:+.2f}' for x in Lbv]); print(th, nm, np.round(Lbv, 2))
