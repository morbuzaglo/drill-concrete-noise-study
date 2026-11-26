"""Cross-check of the solid-soil discretisation against CalculiX (C3D8I): same graded mesh, same materials, outer block faces fixed,
symmetry plane y = 0.5 (u_y = 0). Compares (1) static displacement under the unit axial load, (2) the lowest eigenfrequencies.
usage: python check_ccx_solid.py <case>"""
import sys, os, subprocess, re, pathlib, numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla
from coupled import SolidCase
from soil_solid import assemble
ROOT = pathlib.Path(__file__).resolve().parents[1]
CCX = os.path.join(os.environ['LOCALAPPDATA'], 'CalculiX', 'ccx_static.exe')
cid = sys.argv[1]; t = 0.1 if 't10' in cid else 0.2; bur = 'bur' in cid
sc = SolidCase(t, bur, nmodes=40, verbose=False); m = sc.mesh; so = sc.soil; sl = sc.slab
n = len(m['xyz']); xyz = m['xyz']; tol = 1e-8
# fixed set: plane u_y, outer faces (all comps)
outer = np.zeros(n, bool)
for ax, val in ((0, m['xs'][0]), (0, m['xs'][-1]), (1, m['ys'][-1]), (2, m['zs'][0])): outer |= np.abs(xyz[:, ax] - val) < tol
plane = np.abs(xyz[:, 1] - 0.5) < tol
# load vector (as in SolidCase.direct)
d = sl.dx; b = np.zeros(3 * n)
for node in range(n):
    x, y, z = xyz[node]
    if x < -1e-9 or x > t + 1e-9 or y < 0.5 - 1e-9 or y > 1 + 1e-9 or z < sl.zb - 1e-9 or z > sl.zb + 1 + 1e-9: continue
    i, j, k = int(round(x / d)), int(round(y / d)), int(round((z - sl.zb) / d))
    if abs(i * d - x) > 1e-7 or abs(j * d - y) > 1e-7 or abs(k * d + sl.zb - z) > 1e-7: continue
    b[3 * node] = sl.nid and sc.F[3 * sl.nid(i, j, k)] * (0.5 if abs(y - 0.5) < 1e-9 else 1.0)
Es = 2 * so.rho * so.Vs ** 2 * (1 + so.nu)
Ks, Ms = assemble(m, Es, so.nu, so.rho, 0); Kc, Mc = assemble(m, sl.E, sl.nu, sl.rho, 1)
K = (Ks + Kc).tocsr(); M = (Ms + Mc).tocsr()
used = np.zeros(n, bool); used[m['cells'].ravel()] = True
free = np.zeros(3 * n, bool)
for comp in range(3): free[comp::3] = used & ~outer
free[1::3] &= ~plane
fr = np.nonzero(free)[0]
Kf = K[fr][:, fr].tocsc(); Mf = M[fr][:, fr].tocsc()
u = spla.spsolve(Kf, b[fr]); uf = np.zeros(3 * n); uf[fr] = u
loaded = np.nonzero(b)[0] // 3; ref_node = int(loaded[np.argmax(np.abs(b[3 * loaded]))])
w2 = spla.eigsh(Kf, k=12, M=Mf, sigma=0.0, which='LM', return_eigenvectors=False); fe = np.sort(np.sqrt(np.abs(w2))) / 2 / np.pi
print('own: static u_x at node', ref_node, uf[3 * ref_node], ' lowest freq', np.round(fe[:8], 2))
# --- CalculiX input
job = ROOT / 'results' / 'ccx_solidcheck'; job.mkdir(parents=True, exist_ok=True)
L = ['*NODE'] + ['%d,%.8f,%.8f,%.8f' % (i + 1, *xyz[i]) for i in range(n) if used[i]]
order = [0, 1, 3, 2, 4, 5, 7, 6]
for kind, name in ((0, 'SOIL'), (1, 'CONC')):
    L.append('*ELEMENT, TYPE=C3D8I, ELSET=%s' % name)
    for ci in np.nonzero(m['kind'] == kind)[0]:
        L.append('%d,' % (ci + 1) + ','.join(str(m['cells'][ci][o] + 1) for o in order))
L += ['*MATERIAL, NAME=SOILM', '*ELASTIC', '%.6e,%.4f' % (Es, so.nu), '*DENSITY', '%.4f' % so.rho, '*SOLID SECTION, ELSET=SOIL, MATERIAL=SOILM',
      '*MATERIAL, NAME=CONCM', '*ELASTIC', '%.6e,%.4f' % (sl.E, sl.nu), '*DENSITY', '%.4f' % sl.rho, '*SOLID SECTION, ELSET=CONC, MATERIAL=CONCM']
fx = [i + 1 for i in range(n) if used[i] and outer[i]]; pl = [i + 1 for i in range(n) if used[i] and plane[i] and not outer[i]]
L += ['*NSET, NSET=OUT'] + [','.join(map(str, fx[i:i + 12])) for i in range(0, len(fx), 12)]
L += ['*NSET, NSET=PLN'] + [','.join(map(str, pl[i:i + 12])) for i in range(0, len(pl), 12)]
L += ['*NSET, NSET=REF', str(ref_node + 1)]
L += ['*BOUNDARY', 'OUT,1,3', 'PLN,2,2']
L += ['*STEP', '*FREQUENCY', '8', '*END STEP']
L += ['*STEP', '*STATIC', '*CLOAD'] + ['%d,1,%.9e' % (nd + 1, b[3 * nd]) for nd in loaded if used[nd]] + ['*NODE PRINT, NSET=REF', 'U', '*END STEP']
(job / 'chk.inp').write_text('\n'.join(L) + '\n', encoding='ascii')
env = dict(os.environ, OMP_NUM_THREADS='2')
r = subprocess.run([CCX, '-i', 'chk'], cwd=job, env=env, capture_output=True, text=True)
dat = (job / 'chk.dat').read_text(errors='ignore')
eig = [float(mm.group(1)) for mm in re.finditer(r'^\s+\d+\s+[-+0-9.E]+\s+[-+0-9.E]+\s+([-+0-9.E]+)\s+[-+0-9.E]+\s*$', dat.split('S T E P       2')[0], re.M)]
mm = re.search(r'displacements \(vx,vy,vz\) for set REF.*?\n\n\s+\d+\s+([-+0-9.E]+)', dat, re.S)
print('ccx: static u_x', float(mm.group(1)) if mm else None, ' lowest freq', np.round(eig[:8], 2), ' rc', r.returncode)
if mm: print('static rel diff', abs(float(mm.group(1)) - uf[3 * ref_node]) / abs(uf[3 * ref_node]))
print('freq rel diff', np.round(np.abs(np.array(eig[:8]) - fe[:8]) / fe[:8], 5))
# test: lumped (row-sum) mass
Ml = sp.diags(np.asarray(Mf.sum(axis=1)).ravel()).tocsc()
w2l = spla.eigsh(Kf, k=12, M=Ml, sigma=0.0, which='LM', return_eigenvectors=False); fl = np.sort(np.sqrt(np.abs(w2l))) / 2 / np.pi
print('own lumped-mass freq', np.round(fl[:8], 2), ' vs ccx rel diff', np.round(np.abs(np.array(eig[:8]) - fl[:8]) / fl[:8], 5))
import csv
with open(ROOT / 'results' / f'verify_ccx_solid_{cid}.csv', 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['quantity', 'own', 'calculix', 'rel_diff'])
    if mm: w.writerow(['static u_x at load node [m]', f'{uf[3 * ref_node]:.6e}', f'{float(mm.group(1)):.6e}', f'{abs(float(mm.group(1)) - uf[3 * ref_node]) / abs(uf[3 * ref_node]):.2e}'])
    for k in range(min(8, len(eig))): w.writerow([f'eigenfrequency {k + 1} [Hz]', f'{fe[k]:.3f}', f'{eig[k]:.3f}', f'{abs(eig[k] - fe[k]) / fe[k]:.4f}'])
