"""Solid soil block (hex8, incompatible modes) with Lysmer viscous boundaries; condensed dynamic stiffness at the slab interface.
Time convention exp(+i w t): D(w) = K (1 + i eta_s) + i w C - w^2 M.  Half model: dof u_y of the symmetry plane is removed."""
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla, time
from pypardiso import PyPardisoSolver
from fem import hex8_matrices
import solidmesh as sm


def assemble(mesh, E, nu, rho, kind_sel):
    """K, M (3n x 3n) of the cells with kind == kind_sel; element matrices cached per cell size."""
    cells = mesh['cells'][mesh['kind'] == kind_sel]; size = mesh['size'][mesh['kind'] == kind_sel]
    n = len(mesh['xyz']); nd = 3 * n
    cache = {}; rows, cols, kv, mv = [], [], [], []
    keyf = lambda s: tuple(np.round(s / 1e-9).astype(np.int64))
    ids = np.empty(len(cells), int); mats = []
    for i, s in enumerate(size):
        k = keyf(s)
        if k not in cache: cache[k] = len(mats); mats.append(hex8_matrices(*s, E, nu, rho))
        ids[i] = cache[k]
    dofs = (3 * cells[:, :, None] + np.arange(3)[None, None, :]).reshape(len(cells), 24)
    Kall = np.array([m[0] for m in mats]); Mall = np.array([m[1] for m in mats])
    rows = np.repeat(dofs, 24, axis=1).ravel(); cols = np.tile(dofs, (1, 24)).ravel()
    K = sp.csr_matrix((Kall[ids].reshape(len(cells), -1).ravel(), (rows, cols)), shape=(nd, nd))
    M = sp.csr_matrix((Mall[ids].reshape(len(cells), -1).ravel(), (rows, cols)), shape=(nd, nd))
    return K, M


class CSolver:
    """Complex sparse direct solver through MKL PARDISO on the equivalent real block system [[A,-B],[B,A]] (A + iB)."""

    def __init__(self, Ac):
        Ac = Ac.tocsr(); self.n = Ac.shape[0]
        self.A = sp.bmat([[Ac.real, -Ac.imag], [Ac.imag, Ac.real]], format='csr')
        self.ps = PyPardisoSolver(); self.ps.factorize(self.A)

    def free(self):
        self.ps.free_memory(everything=True)

    def solve(self, B):
        B = np.asarray(B); one = B.ndim == 1
        if one: B = B[:, None]
        x = self.ps.solve(self.A, np.vstack([B.real, B.imag]))
        x = x.reshape(2 * self.n, -1)
        out = x[:self.n] + 1j * x[self.n:]
        return out[:, 0] if one else out


class Soil:
    def __init__(self, mesh, Vs=200.0, rho=1800.0, nu=0.3, eta=0.05):
        self.mesh = mesh; self.Vs, self.rho, self.nu, self.eta = Vs, rho, nu, eta
        G = rho * Vs ** 2; E = 2 * G * (1 + nu); self.cp = Vs * np.sqrt(2 * (1 - nu) / (1 - 2 * nu))
        K, M = assemble(mesh, E, nu, rho, 0)
        n = len(mesh['xyz']); nd = 3 * n
        # lysmer dashpots on the outer faces of the block
        c = np.zeros(nd)
        for node, ax, area in mesh['absorb']:
            node = int(node); ax = int(ax)
            for comp in range(3): c[3 * node + comp] += (rho * self.cp if comp == ax else rho * Vs) * area
        # dof bookkeeping: soil nodes only; remove u_y at the symmetry plane
        sn = np.zeros(n, bool); sn[mesh['cells'][mesh['kind'] == 0].ravel()] = True
        free = np.zeros(nd, bool)
        for comp in range(3): free[comp::3] = sn
        free[3 * mesh['plane'] + 1] = False
        self.free = np.nonzero(free)[0]
        pos = -np.ones(nd, int); pos[self.free] = np.arange(len(self.free)); self.pos = pos
        # interface dofs (node-major)
        idof = []
        for node in mesh['iface']:
            for comp in range(3):
                if free[3 * node + comp]: idof.append(3 * node + comp)
        self.idof = np.array(idof); ii = pos[self.idof]
        mask = np.ones(len(self.free), bool); mask[ii] = False; ee = np.nonzero(mask)[0]
        self.ii, self.ee = ii, ee
        sel = lambda A: A[self.free][:, self.free].tocsr()
        self.K, self.M = sel(K), sel(M); self.C = sp.diags(c[self.free]).tocsr()
        self.Kr = (self.K * (1 + 1j * eta))

    def D_cond(self, w, chunk=200, verbose=False):
        t0 = time.time()
        D = (self.Kr + 1j * w * self.C - w ** 2 * self.M).tocsr()
        ee, ii = self.ee, self.ii
        Dee = D[ee][:, ee].tocsc(); Dei = D[ee][:, ii].toarray(); Die = D[ii][:, ee]; Dii = D[ii][:, ii].toarray()
        lu = CSolver(Dee)
        X = np.empty_like(Dei)
        for a in range(0, Dei.shape[1], chunk): X[:, a:a + chunk] = lu.solve(Dei[:, a:a + chunk])
        lu.free(); out = Dii - Die @ X
        if verbose: print(f'   D_cond f={w / 2 / np.pi:.0f} Hz  nE={len(ee)} nI={len(ii)}  {time.time() - t0:.1f}s', flush=True)
        return out


if __name__ == '__main__':
    import sys
    t, bur = (0.1, sys.argv[1] == 'bur') if len(sys.argv) > 1 else (0.1, True)
    m = sm.build(t, bur); s = Soil(m)
    print('free', len(s.free), 'iface dofs', len(s.idof))
    D = s.D_cond(2 * np.pi * 200, verbose=True)
    print('symmetry err', np.abs(D - D.T).max() / np.abs(D).max())
