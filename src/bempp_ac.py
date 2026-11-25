"""Exterior Helmholtz radiation with Bempp-cl (Burton-Miller, P1 pressure / DP0 velocity).
Bempp-cl uses exp(-i w t), G = exp(+ikr)/(4 pi r).  This wrapper takes velocities and returns pressures in the project
convention exp(+i w t) by conjugating on the way in and out.  Verified against the exact pulsating-sphere solution
(bench_bempp_sphere.py).  Rigid ground = image method: pass the exposed body PLUS its mirror image (closed surface),
mirrored panels carry the same outward normal velocity."""
import numpy as np
import bempp_cl.api as bempp
from bempp_cl.api.operators.boundary import helmholtz as hb, sparse
from bempp_cl.api.operators.potential import helmholtz as hp

bempp.DEFAULT_DEVICE_INTERFACE = 'numba'
bempp.DEFAULT_PRECISION = 'double'
RHO0, C0 = 1.2, 343.0


def merge_vertices(corners):
    """corners (n,4,3) -> (verts (nv,3), quads (n,4)) with coincident vertices merged."""
    v = np.asarray(corners).reshape(-1, 3)
    key = np.round(v / 1e-7).astype(np.int64)
    _, uniq, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    return v[uniq], inv.reshape(-1, 4)


def make_grid(corners):
    verts, q = merge_vertices(corners)
    tris = np.concatenate([q[:, [0, 1, 2]], q[:, [0, 2, 3]]], 0)       # first n tris = (0,1,2), next n = (0,2,3)
    return bempp.Grid(verts.T.copy(), tris.T.astype(np.uint32).copy()), len(q)


def mirror_closed(corners, v_pan):
    """Exposed panels (z>=0) + mirror image about z=0: returns corners_all (2n,4,3), v_all (2n,ncol)."""
    cm = corners.copy(); cm[..., 2] *= -1; cm = cm[:, ::-1]               # keep outward orientation after mirroring
    return np.concatenate([corners, cm], 0), np.concatenate([v_pan, v_pan], 0)


class Radiator:
    def __init__(self, corners):
        self.grid, self.nq = make_grid(corners)
        self.p1 = bempp.function_space(self.grid, 'P', 1)
        self.dp0 = bempp.function_space(self.grid, 'DP', 0)
        self.ntri = self.grid.number_of_elements

    def tri_values(self, v_quad):
        """per-quad values (nq,ncol) -> per-triangle (2nq,ncol) in the grid's element order."""
        v = np.asarray(v_quad)
        order = self._element_order()
        return np.concatenate([v, v], 0)[order]

    def _element_order(self):
        # Grid keeps element order of the input array (first nq tris then next nq tris)
        return np.arange(self.ntri)

    def solve(self, f, v_quad, pts, want_surface=False):
        """v_quad: (nq,ncol) normal velocity per quad panel (project convention). pts: (npts,3). Returns p (npts,ncol)."""
        w = 2 * np.pi * f; k = w / C0
        p1, dp0 = self.p1, self.dp0
        v = np.conj(self.tri_values(v_quad))
        ident = sparse.identity(p1, p1, p1); mass = sparse.identity(dp0, p1, p1)
        K = hb.double_layer(p1, p1, p1, k); Wop = hb.hypersingular(p1, p1, p1, k)
        Kp = hb.adjoint_double_layer(dp0, p1, p1, k); S = hb.single_layer(dp0, p1, p1, k)
        alpha = 1j / k
        lhs = 0.5 * ident - K - alpha * Wop
        slp = hp.single_layer(dp0, np.asarray(pts, float).T.copy(), k)
        dlp = hp.double_layer(p1, np.asarray(pts, float).T.copy(), k)
        out = np.zeros((len(pts), v.shape[1]), complex); surf = []
        for c in range(v.shape[1]):
            un = bempp.GridFunction(dp0, coefficients=(1j * w * RHO0 * v[:, c]).astype(complex))
            rhs = -(S * un) + alpha * (0.5 * (mass * un) + Kp * un)
            sol = bempp.linalg.lu(lhs, rhs)
            out[:, c] = -(slp * un).ravel() + (dlp * sol).ravel()
            if want_surface: surf.append(sol.coefficients)
        res = np.conj(out)
        return (res, np.conj(np.array(surf).T)) if want_surface else res
