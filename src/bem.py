"""Collocation BEM (constant quad panels, 3x3 Gauss, analytic singular part) for the exterior Helmholtz problem.
Convention exp(+i w t); G = exp(-ikr)/(4 pi r); p_n = -i w rho0 v_n (n points into the fluid).
BIE:  1/2 p(x) - int p dG/dn dS = i w rho0 int G v dS.   Field point: p(x) = i w rho0 int G v dS + int p dG/dn dS.
Optional rigid ground plane z=0 through the image method (Green's function G(x,y)+G(x,y*)).  CHIEF rows suppress
fictitious eigenfrequencies of the interior problem."""
import numpy as np
import scipy.linalg as sla

RHO0, C0 = 1.2, 343.0
PREF = 20e-6
_g = np.array([-np.sqrt(0.6), 0.0, np.sqrt(0.6)]); _wg = np.array([5 / 9, 8 / 9, 5 / 9])


class Panels:
    def __init__(self, corners, colloc=None, normals=None, project_radius=None):
        c = np.asarray(corners, float)             # (n,4,3) ccw seen from outside
        self.n = len(c)
        xi, eta = np.meshgrid(_g, _g, indexing='ij'); wq = np.outer(_wg, _wg).ravel()
        xi, eta = xi.ravel(), eta.ravel()
        N = np.stack([(1 - xi) * (1 - eta), (1 + xi) * (1 - eta), (1 + xi) * (1 + eta), (1 - xi) * (1 + eta)], 1) / 4.0
        dNx = np.stack([-(1 - eta), (1 - eta), (1 + eta), -(1 + eta)], 1) / 4.0
        dNe = np.stack([-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)], 1) / 4.0
        gp = np.einsum('gk,nkd->ngd', N, c)
        tx = np.einsum('gk,nkd->ngd', dNx, c); te = np.einsum('gk,nkd->ngd', dNe, c)
        jac = np.linalg.norm(np.cross(tx, te), axis=2)
        w = jac * wq[None, :]
        cen = c.mean(1)
        nrm = np.cross(c[:, 2] - c[:, 0], c[:, 3] - c[:, 1]); nrm /= np.linalg.norm(nrm, axis=1)[:, None]
        if project_radius is not None:             # sphere benchmark: put points on the exact sphere
            r = np.linalg.norm(gp, axis=2)
            gp = gp * (project_radius / r)[:, :, None]; w = w * (project_radius / r) ** 2
            cen = cen * (project_radius / np.linalg.norm(cen, axis=1))[:, None]
            nrm = cen / np.linalg.norm(cen, axis=1)[:, None]
        self.corners = c
        self.gp, self.w, self.cen, self.nrm = gp, w, cen, nrm
        self.area = w.sum(1)
        a = (np.linalg.norm(c[:, 1] - c[:, 0], axis=1) + np.linalg.norm(c[:, 2] - c[:, 3], axis=1)) / 4
        b = (np.linalg.norm(c[:, 2] - c[:, 1], axis=1) + np.linalg.norm(c[:, 3] - c[:, 0], axis=1)) / 4
        d = np.sqrt(a * a + b * b)
        self.S1 = 4 * (a * np.log((b + d) / a) + b * np.log((a + d) / b))   # int 1/r dS at the centre of a rectangle


def _mirror(x):
    y = x.copy(); y[..., 2] *= -1; return y


class Assembler:
    """Geometry cache for one collocation set: far pairs by centroid rule, near pairs by 3x3 Gauss."""
    NEAR = 3.5

    def __init__(self, x, P, ground, self_idx=False):
        self.x, self.P, self.ground, self.self_idx = np.asarray(x, float), P, ground, self_idx
        c = P.corners
        diag = np.maximum(np.linalg.norm(c[:, 2] - c[:, 0], axis=1), np.linalg.norm(c[:, 3] - c[:, 1], axis=1))
        self.imgs = []
        for img in range(2 if ground else 1):
            cen = _mirror(P.cen) if img else P.cen; nr = _mirror(P.nrm) if img else P.nrm
            gp = _mirror(P.gp) if img else P.gp
            d = cen[None] - self.x[:, None]
            rc = np.linalg.norm(d, axis=2); rcs = np.where(rc < 1e-12, 1.0, rc)
            dr = np.einsum('mnd,nd->mn', d, nr) / rcs
            near = rc < self.NEAR * diag[None, :]
            mi, ni = np.nonzero(near)
            df = gp[ni] - self.x[mi][:, None, :]
            r = np.linalg.norm(df, axis=2); r = np.where(r < 1e-12, 1.0, r)
            drg = np.einsum('kgd,kd->kg', df, nr[ni]) / r
            self.imgs.append(dict(rc=rcs, dr=dr, far=~near, mi=mi, ni=ni, r=r, drg=drg, area=P.area, w=P.w[ni]))

    def GH(self, k):
        P = self.P; m = len(self.x)
        G = np.zeros((m, P.n), complex); H = np.zeros((m, P.n), complex)
        for im in self.imgs:
            e = np.exp(-1j * k * im['rc'])
            g = e / (4 * np.pi * im['rc']) * im['area'][None]
            h = -e * (1 + 1j * k * im['rc']) / (4 * np.pi * im['rc'] ** 2) * im['dr'] * im['area'][None]
            G += np.where(im['far'], g, 0); H += np.where(im['far'], h, 0)
            r = im['r']; e = np.exp(-1j * k * r)
            gg = np.sum(e / (4 * np.pi * r) * im['w'], axis=1)
            hh = np.sum(-e * (1 + 1j * k * r) / (4 * np.pi * r ** 2) * im['drg'] * im['w'], axis=1)
            np.add.at(G, (im['mi'], im['ni']), gg); np.add.at(H, (im['mi'], im['ni']), hh)
        if self.self_idx:
            ii = np.arange(P.n)
            rr = np.linalg.norm(P.gp - P.cen[:, None, :], axis=2); rr = np.where(rr < 1e-12, 1.0, rr)
            gself = P.S1 / (4 * np.pi) + np.sum((np.exp(-1j * k * rr) - 1) / (4 * np.pi * rr) * P.w, axis=1)
            hself = np.zeros(P.n, complex)
            if self.ground:
                mg = _mirror(P.gp) - P.cen[:, None, :]; d2 = np.linalg.norm(mg, axis=2)
                gself = gself + np.sum(np.exp(-1j * k * d2) / (4 * np.pi * d2) * P.w, axis=1)
                dgi = -np.exp(-1j * k * d2) * (1 + 1j * k * d2) / (4 * np.pi * d2 ** 2) * (np.einsum('ngd,nd->ng', mg, _mirror(P.nrm)) / d2)
                hself = np.sum(dgi * P.w, axis=1)
            G[ii, ii] = gself; H[ii, ii] = hself
        return G, H


class BEM:
    def __init__(self, P, ground=False, chief=None, mics=None, field=None):
        self.P, self.ground = P, ground
        self.asm_s = Assembler(P.cen, P, ground, self_idx=True)
        self.asm_c = None if chief is None else Assembler(np.asarray(chief, float), P, ground)
        self.asm_m = None if mics is None else Assembler(np.asarray(mics, float), P, ground)
        self.asm_f = None if field is None else Assembler(np.asarray(field, float), P, ground)

    def solve(self, w, v, want_field=False):
        """v: (n,ncol) panel normal velocities. Returns dict p_surf, p_mic, (p_field)."""
        k = w / C0; P = self.P
        G, H = self.asm_s.GH(k)
        A = 0.5 * np.eye(P.n) - H; B = 1j * w * RHO0 * (G @ v)
        if self.asm_c is not None:
            Gc, Hc = self.asm_c.GH(k)
            A = np.vstack([A, -Hc]); B = np.vstack([B, 1j * w * RHO0 * (Gc @ v)])
            Ah = A.conj().T; p = np.linalg.solve(Ah @ A, Ah @ B)
        else:
            p = np.linalg.solve(A, B)
        out = {'p_surf': p}
        for name, asm in (('p_mic', self.asm_m), ('p_field', self.asm_f if want_field else None)):
            if asm is not None:
                Gm, Hm = asm.GH(k)
                out[name] = 1j * w * RHO0 * (Gm @ v) + Hm @ p
        return out


# ------------------------- benchmark mesh: cube-sphere ---------------------------------
def sphere_panels(a, N, half=False):
    """Cube-sphere with N x N quads per cube face. half=True keeps z>=0 (needs N even)."""
    s = np.linspace(-1, 1, N + 1)
    faces = []
    for ax in range(3):
        for sign in (-1, 1):
            u, vv = np.meshgrid(np.arange(N), np.arange(N), indexing='ij')
            for i, j in zip(u.ravel(), vv.ravel()):
                cs = []
                for (du, dv) in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    q = np.zeros(3); q[ax] = sign; q[(ax + 1) % 3] = s[i + du]; q[(ax + 2) % 3] = s[j + dv]
                    cs.append(q)
                cs = np.array(cs)
                n = np.cross(cs[2] - cs[0], cs[3] - cs[1])
                if n @ cs.mean(0) < 0: cs = cs[::-1]
                faces.append(cs)
    faces = np.array(faces)
    cen = faces.mean(1)
    if half:
        faces = faces[cen[:, 2] > 1e-9 * 0 + 1e-12]
    faces = faces / np.linalg.norm(faces, axis=2)[:, :, None] * a
    return faces


def pulsating_sphere_exact(w, a, v0, r):
    k = w / C0
    return 1j * w * RHO0 * v0 * a ** 2 * np.exp(-1j * k * (r - a)) / (r * (1 + 1j * k * a))
