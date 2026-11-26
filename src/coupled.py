"""Slab (free-free modes, symmetric subspace) coupled to a SOLID soil block through its condensed dynamic stiffness at the interface.
Replaces the spring/dashpot support of model.Case. Load: axial uniform annulus (symmetric about y = 0.5).
Also contains a direct (non-modal) coupled solve used to validate the modal coupling."""
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla, time
from scipy.interpolate import CubicSpline
from model import Case
import solidmesh as sm
from soil_solid import Soil, CSolver, assemble


class SolidCase:
    def __init__(self, t, buried, Vs=200.0, rho=1800.0, nu=0.3, eta_s=0.05, eta_c=0.02, nmodes=160, Lx=1.5, Ly=1.5, D=2.0, h0=0.05, g=1.2, hmax=0.20, verbose=True):
        self.t, self.buried, self.eta_c = t, buried, eta_c
        self.case = Case(t, buried, dx=0.05, modal=False, bem=False, eta=eta_c)
        sl = self.case.slab; self.slab = sl
        self.mesh = sm.build(t, buried, Lx=Lx, Ly=Ly, D=D, h0=h0, g=g, hmax=hmax)
        self.soil = Soil(self.mesh, Vs=Vs, rho=rho, nu=nu, eta=eta_s)
        t0 = time.time()
        vals, vecs = spla.eigsh(sl.K.tocsc(), k=nmodes, M=sl.M.tocsc(), sigma=-1e4, which='LM')
        o = np.argsort(vals); vals, vecs = vals[o], vecs[:, o]
        # reflection about y = 0.5 on the slab dofs
        ii, jj, kk = np.meshgrid(np.arange(sl.nx + 1), np.arange(sl.ny + 1), np.arange(sl.nz + 1), indexing='ij')
        nid = sl.nid(ii, jj, kk).ravel(); mir = sl.nid(ii, sl.ny - jj, kk).ravel()
        perm = np.arange(sl.ndof)
        for comp in range(3): perm[3 * nid + comp] = 3 * mir + comp
        sgn = np.ones(sl.ndof); sgn[1::3] = -1
        Y = 0.5 * (vecs + sgn[:, None] * vecs[perm])
        G = Y.T @ (sl.M @ Y); w, V = np.linalg.eigh(G)
        keep = w > 1e-6 * w.max()
        Phi = Y @ V[:, keep] / np.sqrt(w[keep])
        Kt = Phi.T @ (sl.K @ Phi); w2, Q = np.linalg.eigh(0.5 * (Kt + Kt.T))      # rotate to the eigenbasis of the symmetric subspace
        self.Phi = Phi @ Q; self.nm = Phi.shape[1]; self.Kmod = np.diag(w2)
        self.fn = np.sqrt(np.maximum(w2, 0)) / (2 * np.pi)
        self.F = self.case.F[:, 0]; self.Fm = self.Phi.T @ self.F
        # interface map: soil interface dof -> slab dof
        xyz = self.mesh['xyz']; zb = sl.zb; d = sl.dx
        sdof = []
        for gd in self.soil.idof:
            node, comp = divmod(int(gd), 3); x, y, z = xyz[node]
            i, j, k = int(round(x / d)), int(round(y / d)), int(round((z - zb) / d))
            sdof.append(3 * sl.nid(i, j, k) + comp)
        self.sdof = np.array(sdof); self.PhiI = self.Phi[self.sdof]
        self.sl_perm = perm; self.sl_sgn = sgn
        if verbose: print(f'  slab modes: {len(vals)} -> {self.nm} symmetric, f_max {self.fn.max():.0f} Hz; soil dofs {len(self.soil.free)}, interface dofs {len(self.soil.idof)} ({time.time() - t0:.1f}s)', flush=True)

    # ---- soil impedance projected on the modal basis
    def Zsoil(self, f):
        D = self.soil.D_cond(2 * np.pi * f)
        return 2.0 * (self.PhiI.T @ D @ self.PhiI)

    def prepare(self, fgrid, verbose=True):
        self.fg = np.asarray(fgrid, float); Z = []
        t0 = time.time()
        for i, f in enumerate(self.fg):
            Z.append(self.Zsoil(f))
            if verbose and i % 5 == 0: print(f'   soil impedance {i + 1}/{len(self.fg)}  f={f:.0f} Hz  {time.time() - t0:.0f}s', flush=True)
        self.Zg = np.array(Z); self.spl = CubicSpline(self.fg, self.Zg, axis=0)

    def modal_Z(self, f, exact=False):
        w = 2 * np.pi * f
        Zs = self.Zsoil(f) if exact else self.spl(f)
        return self.Kmod * (1 + 1j * self.eta_c) - w ** 2 * np.eye(self.nm) + Zs

    def solve(self, freqs, nmodes=None):
        freqs = np.asarray(freqs, float); nm = nmodes or self.nm
        c = self.case; PvP = c.Pvel @ self.Phi[:, :nm]; AsP = c.Asens @ self.Phi[:, :nm]
        v = np.zeros((len(freqs), c.panels.n, 1), complex); acc = np.zeros((len(freqs), 3, 1), complex)
        for i, f in enumerate(freqs):
            w = 2 * np.pi * f
            Z = self.modal_Z(f)[:nm, :nm]; q = np.linalg.solve(Z, self.Fm[:nm])
            v[i, :, 0] = 1j * w * (PvP @ q); acc[i, :, 0] = -w ** 2 * (AsP @ q)
        return dict(freq=freqs, v=v, acc=acc)

    # ---- direct coupled solve (half model, all dofs), for validation
    def direct(self, f):
        m = self.mesh; n = len(m['xyz']); w = 2 * np.pi * f; so = self.soil
        G = so.rho * so.Vs ** 2; Es = 2 * G * (1 + so.nu)
        Ks, Ms = assemble(m, Es, so.nu, so.rho, 0)
        sl = self.slab
        Kc, Mc = assemble(m, sl.E, sl.nu, sl.rho, 1)
        nd = 3 * n; c = np.zeros(nd)
        for node, ax, area in m['absorb']:
            node = int(node); ax = int(ax)
            for comp in range(3): c[3 * node + comp] += (so.rho * so.cp if comp == ax else so.rho * so.Vs) * area
        used = np.zeros(n, bool); used[m['cells'].ravel()] = True
        free = np.zeros(nd, bool)
        for comp in range(3): free[comp::3] = used
        free[3 * m['plane'] + 1] = False
        fr = np.nonzero(free)[0]
        Dm = (Ks * (1 + 1j * so.eta) + Kc * (1 + 1j * self.eta_c) + 1j * w * sp.diags(c) - w ** 2 * (Ms + Mc)).tocsr()[fr][:, fr]
        # load: slab nodal axial forces (half model: nodes at y = 0.5 carry half of the full-model value)
        Fs = self.F; xyz = m['xyz']; d = sl.dx; b = np.zeros(nd, complex)
        for node in range(n):
            x, y, z = xyz[node]
            if x < -1e-9 or x > self.t + 1e-9 or y < 0.5 - 1e-9 or y > 1.0 + 1e-9 or z < sl.zb - 1e-9 or z > sl.zb + 1.0 + 1e-9: continue
            i, j, k = int(round(x / d)), int(round(y / d)), int(round((z - sl.zb) / d))
            if abs(i * d - x) > 1e-7 or abs(j * d - y) > 1e-7 or abs((k * d + sl.zb) - z) > 1e-7: continue
            fx = Fs[3 * sl.nid(i, j, k)]
            b[3 * node] = fx * (0.5 if abs(y - 0.5) < 1e-9 else 1.0)
        u = np.zeros(nd, complex); cs_ = CSolver(Dm); u[fr] = cs_.solve(b[fr]); cs_.free()
        # expand to the full slab dof vector (mirror) -> panel velocities
        U = np.zeros(sl.ndof, complex)
        for i in range(sl.nx + 1):
            for j in range(sl.ny // 2, sl.ny + 1):
                for k in range(sl.nz + 1):
                    p = (i * d, 0.5 + (j - sl.ny // 2) * d, sl.zb + k * d)
                    nd_ = m_lookup(self, p)
                    if nd_ is None: continue
                    for comp in range(3):
                        U[3 * sl.nid(i, j, k) + comp] = u[3 * nd_ + comp]
                    jm = sl.ny - j
                    if jm != j:
                        U[3 * sl.nid(i, jm, k) + 0] = u[3 * nd_ + 0]; U[3 * sl.nid(i, jm, k) + 1] = -u[3 * nd_ + 1]; U[3 * sl.nid(i, jm, k) + 2] = u[3 * nd_ + 2]
        return U


def m_lookup(sc, p):
    if not hasattr(sc, '_tab'):
        sc._tab = {tuple(np.round(q / 1e-7).astype(np.int64)): i for i, q in enumerate(sc.mesh['xyz'])}
    return sc._tab.get(tuple(np.round(np.asarray(p) / 1e-7).astype(np.int64)))


if __name__ == '__main__':
    import sys
    cid = sys.argv[1] if len(sys.argv) > 1 else 't10_bur'
    t = 0.1 if 't10' in cid else 0.2; bur = 'bur' in cid
    sc = SolidCase(t, bur)
    print('lowest symmetric frequencies', np.round(sc.fn[:10], 1))
    for f in (100.0, 250.0):
        t0 = time.time(); Zex = sc.modal_Z(f, exact=True); print(f, 'exact impedance', time.time() - t0)
