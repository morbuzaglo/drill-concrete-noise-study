"""Verification (a): simply supported square plate, CalculiX natural frequencies and mode shapes vs analytical."""
import numpy as np, pathlib, re, subprocess, os, csv
from ccx_runner import CCX
ROOT = pathlib.Path(__file__).resolve().parents[1]
job = ROOT / 'results' / 'verify' / 'plate'; job.mkdir(parents=True, exist_ok=True)
a = b = 1.0; h = 0.05; E, nu, rho = 30e9, 0.2, 2400.0
nx = ny = 20; nz = 2
dx, dy, dz = a / nx, b / ny, h / nz
nid = lambda i, j, k: 1 + i + (nx + 1) * (j + (ny + 1) * k)
L = ['*NODE']
for k in range(nz + 1):
    for j in range(ny + 1):
        for i in range(nx + 1):
            L.append('%d,%.8f,%.8f,%.8f' % (nid(i, j, k), i * dx, j * dy, k * dz))
L.append('*ELEMENT, TYPE=C3D8I, ELSET=EALL'); e = 0
for k in range(nz):
    for j in range(ny):
        for i in range(nx):
            e += 1; n = [nid(i, j, k), nid(i + 1, j, k), nid(i + 1, j + 1, k), nid(i, j + 1, k), nid(i, j, k + 1), nid(i + 1, j, k + 1), nid(i + 1, j + 1, k + 1), nid(i, j + 1, k + 1)]
            L.append('%d,' % e + ','.join(map(str, n)))
L += ['*MATERIAL, NAME=C', '*ELASTIC', '%.6e,%.3f' % (E, nu), '*DENSITY', '%.3f' % rho, '*SOLID SECTION, ELSET=EALL, MATERIAL=C']
edge = sorted({nid(i, j, k) for k in range(nz + 1) for j in range(ny + 1) for i in range(nx + 1) if i in (0, nx) or j in (0, ny)})
L.append('*NSET, NSET=EDGE'); L += [','.join(map(str, edge[q:q + 12])) for q in range(0, len(edge), 12)]
top = [nid(i, j, nz) for j in range(ny + 1) for i in range(nx + 1)]
L.append('*NSET, NSET=TOP'); L += [','.join(map(str, top[q:q + 12])) for q in range(0, len(top), 12)]
L += ['*BOUNDARY', 'EDGE,3,3', '%d,1,2' % nid(0, 0, 1), '%d,2,2' % nid(nx, 0, 1)]
L += ['*STEP', '*FREQUENCY', '14', '*NODE PRINT, NSET=TOP, FREQUENCY=1', 'U', '*END STEP']
(job / 'plate.inp').write_text('\n'.join(L) + '\n')
r = subprocess.run([CCX, '-i', 'plate'], cwd=job, capture_output=True, text=True); (job / 'plate.log').write_text(r.stdout)
txt = (job / 'plate.dat').read_text()
eig = [float(m.group(1)) for m in re.finditer(r'^\s+(\d+)\s+[-+0-9.E]+\s+[-+0-9.E]+\s+([-+0-9.E]+)\s+[-+0-9.E]+\s*$', txt, re.M) for m in [re.match(r'.*', m.group(0))] ] if False else None
rows = re.findall(r'^\s+(\d+)\s+([-+0-9.E]+)\s+([-+0-9.E]+)\s+([-+0-9.E]+)\s+([-+0-9.E]+)\s*$', txt, re.M)
f_ccx = np.array([float(r_[3]) for r_ in rows][:14])
D = E * h ** 3 / (12 * (1 - nu ** 2)); c0 = np.sqrt(D / (rho * h))
an = sorted([((m, n_), np.pi / 2 * c0 * (m ** 2 / a ** 2 + n_ ** 2 / b ** 2) / (2 * np.pi) * 2 / 1.0) for m in range(1, 6) for n_ in range(1, 6)], key=lambda t: t[1])
# f_mn = (pi/2) sqrt(D/rho h) (m^2/a^2+n^2/b^2)  [Hz]
an = sorted([((m, n_), (np.pi / 2) * c0 * (m ** 2 / a ** 2 + n_ ** 2 / b ** 2)) for m in range(1, 6) for n_ in range(1, 6)], key=lambda t: t[1])
kappa = 5 / 6
def mindlin(m, n_):
    fk = (np.pi / 2) * c0 * (m ** 2 / a ** 2 + n_ ** 2 / b ** 2)
    return fk / np.sqrt(1 + (np.pi ** 2 * h ** 2 / 12) * (m ** 2 / a ** 2 + n_ ** 2 / b ** 2) * (1 + 2 / (kappa * (1 - nu))))
# mode shapes at top nodes
blocks = re.findall(r' displacements \(vx,vy,vz\) for set TOP and time\s+([0-9.Ee+-]+)\s*\n\n((?:[ \t]*\d+(?:\s+[-+0-9.Ee]+){3}\s*\n)+)', txt)
xy = lambda n_: ((n_ - 1) % (nx + 1) * dx, ((n_ - 1) // (nx + 1)) % (ny + 1) * dy)
rowsout = []; modes = []
# bending modes: those with dominant z displacement; take eigen list excluding in-plane by matching analytic order
bend = [(f, int(i)) for i, (f) in enumerate(f_ccx)]
used = set(); res = []
for (mn, fa) in an[:8]:
    j = int(np.argmin([abs(f - fa) if idx not in used else 1e9 for idx, f in enumerate(f_ccx)])); used.add(j)
    res.append((mn, fa, mindlin(*mn), f_ccx[j], j))
res.sort(key=lambda t: t[1])
with open(ROOT / 'results' / 'verify_a_plate.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh); w.writerow(['mode_mn', 'f_thin_plate_Hz', 'f_mindlin_Hz', 'f_CalculiX_Hz', 'err_vs_thin_pct', 'err_vs_mindlin_pct', 'MAC_vs_sinsin'])
    for (mn, fa, fm, fc, j) in res:
        # MAC of ccx mode j (z displacement of top nodes) vs sin(m pi x/a) sin(n pi y/b); degenerate pairs -> best over (m,n),(n,m) combination
        blk = np.array([[float(x) for x in ln.split()] for ln in blocks[j][1].strip().split('\n')])
        X = np.array([xy(int(n_)) for n_ in blk[:, 0]]); uz = blk[:, 3]
        s1 = np.sin(mn[0] * np.pi * X[:, 0] / a) * np.sin(mn[1] * np.pi * X[:, 1] / b)
        s2 = np.sin(mn[1] * np.pi * X[:, 0] / a) * np.sin(mn[0] * np.pi * X[:, 1] / b)
        if mn[0] != mn[1]:   # degenerate: project onto span
            Q, _ = np.linalg.qr(np.stack([s1, s2], 1)); pr = Q @ (Q.T @ uz); mac = (pr @ uz) ** 2 / ((pr @ pr) * (uz @ uz))
        else:
            mac = (s1 @ uz) ** 2 / ((s1 @ s1) * (uz @ uz))
        w.writerow([f'{mn[0]}{mn[1]}', f'{fa:.2f}', f'{fm:.2f}', f'{fc:.2f}', f'{100 * (fc / fa - 1):.2f}', f'{100 * (fc / fm - 1):.2f}', f'{mac:.4f}'])
        print(mn, f'thin {fa:.1f}  mindlin {fm:.1f}  ccx {fc:.1f}  err_thin {100 * (fc / fa - 1):+.2f}%  err_mindlin {100 * (fc / fm - 1):+.2f}%  MAC {mac:.4f}')
