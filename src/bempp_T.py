"""Acoustic transfer vectors T(f) (nmic x npanel) from Bempp-cl boundary operators (Burton-Miller, P1/DP0), rigid ground by the
image method (exposed body + mirror image = closed mesh).  p_mic = T(f) @ v_panel  with project convention exp(+i w t).
Dense solve is done once per frequency for all microphones (adjoint trick), so any number of velocity fields can be applied.
Field-point potentials are evaluated with a centroid rule (microphones are >= 0.5 m from the surface)."""
import numpy as np, time
import bempp_cl.api as bempp
from bempp_cl.api.operators.boundary import helmholtz as hb, sparse
from bempp_ac import merge_vertices, RHO0, C0
from scipy.interpolate import CubicSpline

bempp.DEFAULT_DEVICE_INTERFACE = 'numba'
bempp.DEFAULT_PRECISION = 'double'


def mirror_all(corners):
    cm = corners.copy(); cm[..., 2] *= -1; cm = cm[:, ::-1]
    return np.concatenate([corners, cm], 0)


class Ctx:
    def __init__(self, corners_exposed):
        self.nq_exp = len(corners_exposed)
        call = mirror_all(corners_exposed)
        verts, q = merge_vertices(call)
        self.nq_all = len(q)
        tris = np.concatenate([q[:, [0, 1, 2]], q[:, [0, 2, 3]]], 0)
        self.verts, self.tris = verts, tris
        self.grid = bempp.Grid(verts.T.copy(), tris.T.astype(np.uint32).copy())
        self.p1 = bempp.function_space(self.grid, 'P', 1); self.dp0 = bempp.function_space(self.grid, 'DP', 0)
        # triangle geometry for potentials
        P0, P1_, P2 = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
        cr = np.cross(P1_ - P0, P2 - P0); self.area = 0.5 * np.linalg.norm(cr, axis=1)
        self.nrm = cr / np.linalg.norm(cr, axis=1)[:, None]; self.cen = (P0 + P1_ + P2) / 3
        # fold matrix: quad velocity (exposed) -> triangle velocity coefficients (exposed tris, their mirrors)
        n = self.nq_all; ntri = 2 * n
        rows = np.concatenate([np.arange(n), n + np.arange(n)])           # tri index of quad i: i and n+i
        fold = np.zeros((ntri, self.nq_exp))
        for i in range(n):
            src = i if i < self.nq_exp else i - self.nq_exp
            fold[i, src] = 1; fold[n + i, src] = 1
        self.fold = fold


def T_at(ctx, f, mics, ground_ok=True):
    w = 2 * np.pi * f; k = w / C0; p1, dp0 = ctx.p1, ctx.dp0
    ident = sparse.identity(p1, p1, p1); mass = sparse.identity(dp0, p1, p1)
    K = hb.double_layer(p1, p1, p1, k); Wop = hb.hypersingular(p1, p1, p1, k)
    Kp = hb.adjoint_double_layer(dp0, p1, p1, k); S = hb.single_layer(dp0, p1, p1, k)
    alpha = 1j / k
    A = np.asarray((0.5 * ident - K - alpha * Wop).weak_form().A)
    Sw = np.asarray(S.weak_form().A); Kpw = np.asarray(Kp.weak_form().A)
    mw = mass.weak_form(); Mw = (mw.sparse_operator if hasattr(mw, 'sparse_operator') else mw.A).toarray()
    R = -Sw + alpha * (0.5 * Mw + Kpw)                     # (np1, ndp0): solution coefficients per unit DP0 datum u
    # potentials by centroid rule
    x = np.asarray(mics, float)
    d = ctx.cen[None] - x[:, None]; r = np.linalg.norm(d, axis=2)
    e = np.exp(1j * k * r) / (4 * np.pi * r)
    Spot = e * ctx.area[None]                              # (nmic, ntri)
    # d/dn_y [e^{ikr}/(4 pi r)] = e (ik - 1/r) * dr/dn_y, dr/dn_y = (y-x).n / r
    dGdn = e * (1j * k - 1.0 / r) * (np.einsum('mnd,nd->mn', d, ctx.nrm) / r)
    Dpot = np.zeros((len(x), ctx.p1.global_dof_count), complex)
    l2g = np.asarray(ctx.p1.local2global)                    # (ntri, 3) global dof of each local vertex function
    for a in range(3):
        np.add.at(Dpot.T, l2g[:, a], (dGdn * ctx.area[None] / 3).T)
    X = np.linalg.solve(A.T, Dpot.T)                       # (np1, nmic)  adjoint solve
    # p = -Spot u + Dpot A^{-1} R u , with u = i w rho v (bempp-convention, v conj later)
    Tb = (-Spot + X.T @ R) * (1j * w * RHO0)               # (nmic, ntri)
    Tq = Tb @ ctx.fold                                     # (nmic, nq_exp)
    return np.conj(Tq)                                      # to exp(+i w t) convention


def interp_T(fT, Tlist, fq, mics, ref):
    """Interpolate de-phased transfer vectors. Tlist (nfT, nmic, nq). ref: reference distance per mic (m)."""
    k = 2 * np.pi * fT / C0
    ph = np.exp(1j * k[:, None] * ref[None, :])[:, :, None]       # convention exp(+iwt): outgoing exp(-ikr) -> multiply exp(+ikr)
    Td = Tlist * ph
    cs = CubicSpline(fT, Td, axis=0)
    kq = 2 * np.pi * fq / C0
    return cs(fq) * np.exp(-1j * kq[:, None] * ref[None, :])[:, :, None]
