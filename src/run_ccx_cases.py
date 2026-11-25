"""Run CalculiX modal + steady-state-dynamics for the 2x2 cases (or a subset) and store panel normal velocities.
usage: python run_ccx_cases.py <case_id> [dx] [nmodes] [tag]     case_id like t10_exp, t10_bur, t20_exp, t20_bur"""
import sys, time, pathlib, numpy as np
from model import Case
from fem import soil_props
from ccx_runner import *

ROOT = pathlib.Path(__file__).resolve().parents[1]
CASES = {'t10_exp': (0.10, False), 't10_bur': (0.10, True), 't20_exp': (0.20, False), 't20_bur': (0.20, True)}


def run(cid, dx=0.025, nmodes=60, tag='', soil=None, zeta=None, bands=None, ncols=1, dp=0.05, threads=1):
    t, bur = CASES[cid]
    name = f'{cid}{tag}'
    job = ROOT / 'results' / 'ccx' / name; job.mkdir(parents=True, exist_ok=True)
    c = Case(t, bur, dx=dx, dp=dp, soil=soil or soil_props(eta=0.0), modal=False, bem=False)
    bands = bands or default_bands()
    F = c.F[:, :ncols]
    sn = write_inp(c, job / 'job.inp', bands, nmodes=nmodes, zeta=zeta, loads=F)
    rc, dt, out = run_ccx(str(job), 'job', log=job / 'job.log', threads=threads)
    if rc != 0:
        raise RuntimeError(f'ccx failed rc={rc}: {out[-800:]}')
    fr, ids, U, eig = collect(job / 'job.dat', len(sn), ncols, bands)
    w = 2 * np.pi * fr
    nf = len(fr)
    v = np.zeros((nf, c.panels.n, ncols), complex); acc = np.zeros((nf, 3, ncols), complex)
    for k in range(ncols):
        for i in range(nf):
            u = np.zeros(c.slab.ndof, complex)
            idx = (3 * (ids[:, None] - 1) + np.arange(3)[None, :])
            u[idx] = U[k, i]
            v[i, :, k] = 1j * w[i] * (c.Pvel @ u)
            acc[i, :, k] = -w[i] ** 2 * (c.Asens @ u)
    np.savez_compressed(ROOT / 'results' / f'ccx_{name}.npz', freq=fr, v=v, acc=acc, eig=np.array(eig), runtime=dt,
                        corners=c.panels.corners, tags=c.tags, t=t, buried=bur, dx=dx, nmodes=nmodes)
    (job / 'job.dat').unlink(missing_ok=True)                    # large text output; keep the .inp and the log only
    return dt, len(fr)


if __name__ == '__main__':
    cid = sys.argv[1]
    dx = float(sys.argv[2]) if len(sys.argv) > 2 else 0.025
    nm = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    tag = sys.argv[4] if len(sys.argv) > 4 else ''
    Vs = float(sys.argv[5]) if len(sys.argv) > 5 else 200.0
    ks = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
    ncols = int(sys.argv[7]) if len(sys.argv) > 7 else 1
    t0 = time.time(); dt, nf = run(cid, dx, nm, tag, soil=soil_props(Vs=Vs, eta=0.0, kscale=ks), ncols=ncols)
    print(f'{cid}{tag}: ccx {dt:.0f} s, {nf} frequencies, total {time.time() - t0:.0f} s', flush=True)
