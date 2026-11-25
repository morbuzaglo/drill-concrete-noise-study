"""Compare LS-DYNA (SSD + acoustic BEM) pressure at the field points with CalculiX + Bempp-cl for one case.
usage: python compare_lsdyna.py [case=t10_bur] [folder=<ROOT>/lsdyna/<case>]
Reads Press_Pa and eigout written by the LS-DYNA run. Mics: 900001=F, 900002=R, 900003=Rg, 900004=S.
F and R are equal for this symmetric geometry (mics at x=-1 and x=t+1, slab symmetric about its mid-plane) - not a mapping error."""
import sys, re, pathlib, numpy as np
from post import *

case = sys.argv[1] if len(sys.argv) > 1 else 't10_bur'
D = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'lsdyna' / case
cur = {}; pt = None
for l in (D / 'Press_Pa').read_text().split('\n'):
    m = re.match(r'\s*pt\s+(\d+)', l)
    if m: pt = int(m.group(1)); cur[pt] = []; continue
    v = l.split()
    if pt and len(v) == 2: cur[pt].append((float(v[0]), float(v[1])))
A = {k: np.array(v) for k, v in cur.items()}
fl = A[900001][:, 0]
f, p, r = pressure(case, '_dx0.05')
edges = [(44.2, 88.4, '63'), (88.4, 176.8, '125'), (176.8, 353.6, '250'), (353.6, 707.1, '500'), (707.1, 1414.3, '1000')]
for j, (k, nm) in enumerate(zip(sorted(A), ['F', 'R', 'Rg'])):
    L = A[k][:, 1]; O = np.interp(fl, f, np.abs(p[:, j]))
    print(f'mic {nm}: band mean-square difference LS-DYNA - (CalculiX+Bempp), dB')
    for a, b, n in edges:
        m = (fl >= a) & (fl < b)
        print('   %5s Hz: %+5.1f   (per-frequency 10-90%%: %+.1f .. %+.1f)' % (n, 10 * np.log10(np.mean(L[m] ** 2) / np.mean(O[m] ** 2)), *np.percentile(20 * np.log10(L[m] / O[m]), [10, 90])))
eg = [float(l.split()[3]) for l in (D / 'eigout').read_text().split('\n') if re.match(r'\s+\d+\s+[-+0-9.E]+\s+[-+0-9.E]+\s+[-+0-9.E]+\s+[-+0-9.E]+\s*$', l)]
print('LS-DYNA eigenfrequencies (first 20):', np.round(eg[:20], 1), ' last of %d: %.0f' % (len(eg), eg[-1]))
print('CalculiX eigenfrequencies (first 20):', np.round(r['eig'][:20], 1), ' last of %d: %.0f' % (len(r['eig']), r['eig'][-1]))
