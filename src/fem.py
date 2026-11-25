"""Structured hex8 FEM (Wilson-Taylor incompatible modes) for a concrete slab, modal frequency-domain solver.
Units: SI (m, kg, s, N, Pa). Time convention exp(+i w t). Displacement dof order: 3*node + comp (x,y,z)."""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


def hex8_matrices(dx, dy, dz, E, nu, rho):
    lam = E * nu / ((1 + nu) * (1 - 2 * nu)); mu = E / (2 * (1 + nu))
    D = np.zeros((6, 6)); D[:3, :3] = lam
    for i in range(3):
        D[i, i] += 2 * mu; D[3 + i, 3 + i] = mu
    xi = np.array([[(n & 1) * 2 - 1, ((n >> 1) & 1) * 2 - 1, ((n >> 2) & 1) * 2 - 1] for n in range(8)], float)
    g = 1 / np.sqrt(3)
    J = np.array([dx, dy, dz]) / 2.0; detJ = J.prod()

    def Bmat(G):  # G[i,j] = d u_i / d x_j  as function of column; returns 6-row builder
        pass

    def strain_rows(grad):  # grad: (3,3,ncols) du_i/dx_j
        B = np.zeros((6, grad.shape[2]))
        B[0] = grad[0, 0]; B[1] = grad[1, 1]; B[2] = grad[2, 2]
        B[3] = grad[0, 1] + grad[1, 0]; B[4] = grad[1, 2] + grad[2, 1]; B[5] = grad[2, 0] + grad[0, 2]
        return B

    Kuu = np.zeros((24, 24)); Kua = np.zeros((24, 9)); Kaa = np.zeros((9, 9))
    for c in (-g, g):
        for b in (-g, g):
            for a in (-g, g):
                gr = np.zeros((3, 3, 24))
                for n in range(8):
                    sx, sy, sz = xi[n]
                    d = np.array([sx * (1 + sy * b) * (1 + sz * c), sy * (1 + sx * a) * (1 + sz * c),
                                  sz * (1 + sx * a) * (1 + sy * b)]) / 8.0 / J
                    for comp in range(3):
                        gr[comp, :, 3 * n + comp] = d
                Bc = strain_rows(gr)
                gi = np.zeros((3, 3, 9)); pt = (a, b, c)
                for m in range(3):
                    d = -2 * pt[m] / J[m]
                    for u in range(3):
                        gi[u, m, 3 * m + u] = d
                Bi = strain_rows(gi)
                w = detJ
                Kuu += Bc.T @ D @ Bc * w; Kua += Bc.T @ D @ Bi * w; Kaa += Bi.T @ D @ Bi * w
    Ke = Kuu - Kua @ np.linalg.solve(Kaa, Kua.T)
    M1 = lambda h: h * np.array([[1 / 3, 1 / 6], [1 / 6, 1 / 3]])
    M8 = rho * np.kron(M1(dz), np.kron(M1(dy), M1(dx)))
    Me = np.kron(M8, np.eye(3))
    return 0.5 * (Ke + Ke.T), Me


class Slab:
    """Box slab, local coords: x thickness (0..t), y width (0..W), z height (0..H). Global z = z_local + zb."""

    def __init__(self, t, W, H, dx, zb=0.0, E=30e9, nu=0.2, rho=2400.0, eta=0.02):
        self.t, self.W, self.H, self.dx, self.zb = t, W, H, dx, zb
        self.nx, self.ny, self.nz = [int(round(v / dx)) for v in (t, W, H)]
        assert abs(self.nx * dx - t) < 1e-9 and abs(self.ny * dx - W) < 1e-9 and abs(self.nz * dx - H) < 1e-9, 'dx must divide t,W,H'
        self.E, self.nu, self.rho, self.eta = E, nu, rho, eta
        self.nn = (self.nx + 1) * (self.ny + 1) * (self.nz + 1); self.ndof = 3 * self.nn
        self._assemble()

    def nid(self, i, j, k):
        return i + (self.nx + 1) * (j + (self.ny + 1) * k)

    def node_xyz(self):
        i, j, k = np.meshgrid(np.arange(self.nx + 1), np.arange(self.ny + 1), np.arange(self.nz + 1), indexing='ij')
        P = np.zeros((self.nn, 3))
        idx = self.nid(i, j, k).ravel()
        P[idx] = np.stack([i.ravel() * self.dx, j.ravel() * self.dx, k.ravel() * self.dx], 1)
        return P

    def _assemble(self):
        Ke, Me = hex8_matrices(self.dx, self.dx, self.dx, self.E, self.nu, self.rho)
        ex, ey, ez = np.meshgrid(np.arange(self.nx), np.arange(self.ny), np.arange(self.nz), indexing='ij')
        ex, ey, ez = ex.ravel(), ey.ravel(), ez.ravel()
        conn = np.stack([self.nid(ex + (n & 1), ey + ((n >> 1) & 1), ez + ((n >> 2) & 1)) for n in range(8)], 1)
        dofs = (3 * conn[:, :, None] + np.arange(3)[None, None, :]).reshape(len(conn), 24)
        self.conn = conn
        rows = np.repeat(dofs, 24, axis=1).ravel(); cols = np.tile(dofs, (1, 24)).ravel()
        n = len(conn)
        self.K = sp.csr_matrix((np.tile(Ke.ravel(), n), (rows, cols)), shape=(self.ndof, self.ndof))
        self.M = sp.csr_matrix((np.tile(Me.ravel(), n), (rows, cols)), shape=(self.ndof, self.ndof))
        self.mass = self.M.sum() / 3.0

    # ---- interpolation of a point set -> nodal weights (trilinear)
    def interp(self, pts):
        """pts (n,3) local coords -> sparse (n, nn) of trilinear weights."""
        pts = np.asarray(pts, float); d = self.dx
        ix = np.clip(np.floor(pts[:, 0] / d + 1e-9).astype(int), 0, self.nx - 1)
        iy = np.clip(np.floor(pts[:, 1] / d + 1e-9).astype(int), 0, self.ny - 1)
        iz = np.clip(np.floor(pts[:, 2] / d + 1e-9).astype(int), 0, self.nz - 1)
        fx = pts[:, 0] / d - ix; fy = pts[:, 1] / d - iy; fz = pts[:, 2] / d - iz
        rows, cols, vals = [], [], []
        for n in range(8):
            a, b, c = n & 1, (n >> 1) & 1, (n >> 2) & 1
            w = (fx if a else 1 - fx) * (fy if b else 1 - fy) * (fz if c else 1 - fz)
            rows.append(np.arange(len(pts))); cols.append(self.nid(ix + a, iy + b, iz + c)); vals.append(w)
        return sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(len(pts), self.nn))

    # ---- soil / support impedance on faces
    def soil_matrices(self, soil, faces):
        """Diagonal spring (Ak) and dashpot (Ac) matrices from a per-area half-space impedance.
        faces: subset of {'bottom','front','back','left','right'}; side faces only below the soil line (global z<0)."""
        d = self.dx; ak = np.zeros(self.ndof); ac = np.zeros(self.ndof)
        kn, kt = soil['kn'], soil['kt']; cn, ct = soil['cn'], soil['ct']
        for f in faces:
            if f == 'bottom':
                ii, jj = np.meshgrid(np.arange(self.nx), np.arange(self.ny), indexing='ij'); kk = np.zeros_like(ii); ax = 2
                nodes = lambda a, b: self.nid(ii + a, jj + b, kk)
            else:
                nsoil = int(round(max(0.0, -self.zb) / d))
                if nsoil == 0: continue
                if f in ('front', 'back'):
                    jj, kk = np.meshgrid(np.arange(self.ny), np.arange(nsoil), indexing='ij'); ii = np.full_like(jj, 0 if f == 'front' else self.nx); ax = 0
                    nodes = lambda a, b: self.nid(ii, jj + a, kk + b)
                else:
                    ii, kk = np.meshgrid(np.arange(self.nx), np.arange(nsoil), indexing='ij'); jj = np.full_like(ii, 0 if f == 'left' else self.ny); ax = 1
                    nodes = lambda a, b: self.nid(ii + a, jj, kk + b)
            for a in (0, 1):
                for b in (0, 1):
                    nd = nodes(a, b).ravel()
                    for comp in range(3):
                        k_, c_ = (kn, cn) if comp == ax else (kt, ct)
                        np.add.at(ak, 3 * nd + comp, k_ * d * d / 4); np.add.at(ac, 3 * nd + comp, c_ * d * d / 4)
        return sp.diags(ak), sp.diags(ac)


def soil_props(Vs=200.0, rho=1800.0, nu=0.3, Lref=1.0, eta=0.1, kscale=1.0):
    G = rho * Vs ** 2; cp = Vs * np.sqrt(2 * (1 - nu) / (1 - 2 * nu))
    return dict(Vs=Vs, rho=rho, nu=nu, Lref=Lref, eta=eta, cp=cp, G=G,
                kn=kscale * rho * cp ** 2 / Lref, kt=kscale * G / Lref, cn=rho * cp, ct=rho * Vs)


class ModalModel:
    """Free (+ real soil springs) modes; complex part (hysteretic + dashpots) projected on the modal basis."""

    def __init__(self, slab, faces, soil, nmodes=80):
        self.slab, self.soil = slab, soil
        Ak, Ac = slab.soil_matrices(soil, faces)
        Kt = (slab.K + Ak).tocsc()
        vals, vecs = spla.eigsh(Kt, k=nmodes, M=slab.M.tocsc(), sigma=-1e4, which='LM')
        o = np.argsort(vals); vals, vecs = vals[o], vecs[:, o]
        self.w2 = vals; self.f = np.sqrt(np.maximum(vals, 0)) / (2 * np.pi); self.Phi = vecs
        MP = slab.M @ vecs
        # mass-normalise
        s = np.sqrt(np.einsum('ij,ij->j', vecs, MP)); self.Phi = vecs / s
        self.PhiK = self.Phi.T @ (slab.K @ self.Phi)       # structure stiffness (modal)
        self.PhiAk = self.Phi.T @ (Ak @ self.Phi); self.PhiAc = self.Phi.T @ (Ac @ self.Phi)
        self.eta = slab.eta; self.eta_s = soil['eta']
        self.nm = nmodes

    def solve(self, w, F, nm=None):
        """Complex displacement for load matrix F (ndof, ncol) at angular freq w. Returns modal coords q (nm,ncol)."""
        nm = nm or self.nm
        Z = (self.PhiK[:nm, :nm] * (1 + 1j * self.eta) + self.PhiAk[:nm, :nm] * (1 + 1j * self.eta_s)
             + 1j * w * self.PhiAc[:nm, :nm] - w ** 2 * np.eye(nm))
        # PhiK + PhiAk is diag(w2) (real eigenbasis of K+Ak) plus no coupling in the real part
        return np.linalg.solve(Z, self.Phi[:, :nm].T @ F)
