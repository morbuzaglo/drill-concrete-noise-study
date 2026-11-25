"""Free-free t=100 mm slab, single-node unit force at the drill point: CalculiX SSD vs in-house modal vs OpenRadioss explicit FFT."""
import numpy as np, pathlib, struct, sys, csv
from model import Case
from fem import soil_props, ModalModel
from ccx_runner import *
ROOT = pathlib.Path(__file__).resolve().parents[1]
job = ROOT / 'results' / 'ccx' / 'free_slab'; job.mkdir(parents=True, exist_ok=True)
c = Case(0.1, False, dx=0.05, dp=0.05, soil=soil_props(eta=0.0), modal=False, bem=False); c.faces = []
xyz = c.slab.node_xyz(); drill_node = int(np.argmin(np.linalg.norm(xyz - np.array([0.05, 0.5, 0.7]), axis=1)))
F = np.zeros((c.slab.ndof, 1)); F[3 * drill_node, 0] = 1.0
bands = default_bands()
if '--skip-ccx' not in sys.argv:
    sn = write_inp(c, job / 'job.inp', bands, nmodes=60, loads=F)
    rc, dt, out = run_ccx(str(job), 'job', log=job / 'job.log', threads=1); print('ccx rc', rc, '%.0fs' % dt)
    fr, ids, U, eig = collect(job / 'job.dat', len(sn), 1, bands)
    w = 2 * np.pi * fr; acc = np.zeros((len(fr), 3), complex)
    for i in range(len(fr)):
        u = np.zeros(c.slab.ndof, complex); u[(3 * (ids[:, None] - 1) + np.arange(3)[None, :])] = U[0, i]
        acc[i] = -w[i] ** 2 * (c.Asens @ u)
    np.savez(ROOT / 'results' / 'xcheck_free_ccx.npz', f=fr, acc=acc, eig=eig)
d = np.load(ROOT / 'results' / 'xcheck_free_ccx.npz'); fr, acc_ccx, eig = d['f'], d['acc'], d['eig']
# own modal (free-free: no soil)
mm = ModalModel(c.slab, [], soil_props(eta=0.0), nmodes=60)
AsPhi = c.Asens @ mm.Phi
acc_own = np.array([-(2 * np.pi * f) ** 2 * (AsPhi @ mm.solve(2 * np.pi * f, F))[:, 0] for f in fr])
np.savez(ROOT / 'results' / 'xcheck_free_own.npz', f=fr, acc=acc_own, f_modes=mm.f)
print('own modes', np.round(mm.f[:14], 1)); print('ccx modes', np.round(eig[:14], 1))
dB = 20 * np.log10(np.abs(acc_own) / np.abs(acc_ccx)); print('own/ccx sensor |a| dB: mean abs %.3f max %.3f' % (np.abs(dB).mean(), np.abs(dB).max()))
