"""Case builder: slab (concrete) + soil impedance + drill loads + BEM radiation to microphones.
Global coordinates (m): x = drilling axis (drill-side face at x=0, rear face at x=t), y = width, z = height above the soil line.
Slab local z = global z - zb  (zb = 0 exposed, -0.4 half... partially buried)."""
import numpy as np, scipy.sparse as sp, time
from fem import Slab, ModalModel, soil_props
from bem import Panels, BEM, PREF

W_SLAB, H_SLAB = 1.0, 1.0
DRILL = dict(yc=0.5, zl=0.7, depth=0.05, ri=0.020, ro=0.025)     # drill axis position (specimen coords), blind hole depth, annulus
MIC_H = 1.0
OCT_FC = np.array([62.5, 125, 250, 500, 1000, 2000, 4000, 8000])
OCT_LABEL = ['63', '125', '250', '500', '1000', '2000', '4000', '8000']
FMIN, FMAX = 62.5 / np.sqrt(2), 1000 * np.sqrt(2)


def freq_grid(ratio=1.015, fmin=FMIN, fmax=FMAX):
    n = int(np.ceil(np.log(fmax / fmin) / np.log(ratio)))
    return fmin * ratio ** np.arange(n + 1)


def mic_positions(t):
    return {'F': (-1.0, 0.5, MIC_H), 'R': (t + 1.0, 0.5, MIC_H), 'Rg': (1.3, 0.5, MIC_H), 'S': (t / 2, 2.0, MIC_H)}


def exposed_panels(slab, dp):
    """Quad panels of the slab faces above the soil line, global coords, outward normals."""
    t, W, H, zb = slab.t, slab.W, slab.H, slab.zb
    L = np.array([t, W, H]); off = np.array([0.0, 0.0, zb])
    z0 = max(0.0, -zb)                       # local z where the soil line is
    faces = []
    for ax in range(3):
        for side in (0, 1):
            if ax == 2 and side == 0: continue                    # bottom face never radiates
            b, c = [a for a in range(3) if a != ax]
            rb = (0.0, L[b]); rc = (0.0, L[c])
            if b == 2: rb = (z0, L[b])
            if c == 2: rc = (z0, L[c])
            nb = int(round((rb[1] - rb[0]) / dp)); nc = int(round((rc[1] - rc[0]) / dp))
            assert abs(nb * dp - (rb[1] - rb[0])) < 1e-9 and abs(nc * dp - (rc[1] - rc[0])) < 1e-9
            want = np.zeros(3); want[ax] = 1 if side else -1
            for i in range(nb):
                for j in range(nc):
                    q = np.zeros((4, 3))
                    for k, (du, dv) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
                        q[k, ax] = L[ax] * side; q[k, b] = rb[0] + (i + du) * dp; q[k, c] = rc[0] + (j + dv) * dp
                    n = np.cross(q[2] - q[0], q[3] - q[1])
                    if n @ want < 0: q = q[::-1].copy()
                    faces.append((q, ax, side))
    corners_local = np.array([f[0] for f in faces])
    tags = np.array([[f[1], f[2]] for f in faces])
    return corners_local + off, corners_local, tags


def velocity_operator(slab, corners_local, nrm, dp):
    """Sparse (npan, ndof): panel-mean normal displacement from nodal dofs, sampled at 2x2 points per panel."""
    cen = corners_local.mean(1)
    pts = [corners_local[:, i] for i in range(4)]            # panel-mean velocity = mean of the 4 corner-node values
    S = sum(slab.interp(p) for p in pts) / 4.0               # (npan, nn)
    P = sp.csr_matrix((len(cen), slab.ndof))
    for comp in range(3):
        E = sp.csr_matrix((np.ones(slab.nn), (np.arange(slab.nn), 3 * np.arange(slab.nn) + comp)), shape=(slab.nn, slab.ndof))
        P = P + sp.diags(nrm[:, comp]) @ S @ E
    return P


def node_dof_op(slab, pt, comp):
    S = slab.interp(np.array([pt]))
    E = sp.csr_matrix((np.ones(slab.nn), (np.arange(slab.nn), 3 * np.arange(slab.nn) + comp)), shape=(slab.nn, slab.ndof))
    return (S @ E)


# ----------------------------------------------------------------- drill loads
def annulus_points(yc, zl, x, ri, ro, nr=4, nth=96, seg=None):
    """Quadrature points over the annulus. seg=(nseg, arc_deg, offset_deg) keeps only the cutting segments.
    Returns pts (n,3) local, area weights (n,), polar angles (n,), radii (n,)."""
    rg = ri + (np.arange(nr) + 0.5) * (ro - ri) / nr
    th = (np.arange(nth) + 0.5) * 2 * np.pi / nth
    R, T = np.meshgrid(rg, th, indexing='ij'); R, T = R.ravel(), T.ravel()
    A = R * (ro - ri) / nr * 2 * np.pi / nth
    if seg is not None:
        nseg, arc, off = seg
        ang = (np.degrees(T) - off) % (360.0 / nseg)
        keep = ang < arc
        R, T, A = R[keep], T[keep], A[keep]
    pts = np.stack([np.full_like(R, x), yc + R * np.cos(T), zl + R * np.sin(T)], 1)
    return pts, A, T, R


def build_loads(slab, drill=DRILL, nth=96):
    """Columns: 0 axial uniform (1 N), 1 torque uniform (1 N m), 2 axial 6 segments (40 deg arcs), 3 axial 6 segments rotated 30 deg.
    Returns F (ndof, 4) and a checks dict (resultant force/moment recomputed from the NODAL loads)."""
    cols, info = [], {}
    xyz = slab.node_xyz(); yc, zc = drill['yc'], drill['zl']
    for name, kind, seg in (('axial_uniform', 'ax', None), ('torque_uniform', 'tq', None),
                            ('axial_seg6_0deg', 'ax', (6, 40.0, 0.0)), ('axial_seg6_30deg', 'ax', (6, 40.0, 30.0))):
        pts, A, T, R = annulus_points(yc, zc, drill['depth'], drill['ri'], drill['ro'], nth=nth, seg=seg)
        S = slab.interp(pts)                                    # (np, nn)
        f = np.zeros(slab.ndof)
        if kind == 'ax':
            wgt = A / A.sum()                                   # total 1 N along +x (into the concrete)
            nod = np.asarray(S.T @ wgt).ravel(); f[0::3] = nod
        else:
            tau = 1.0 / np.sum(A * R)                           # uniform tangential traction -> 1 N m about +x
            ty = -np.sin(T) * tau * A; tz = np.cos(T) * tau * A
            f[1::3] = np.asarray(S.T @ ty).ravel(); f[2::3] = np.asarray(S.T @ tz).ravel()
        Fx, Fy, Fz = f[0::3].sum(), f[1::3].sum(), f[2::3].sum()
        Mx = np.sum((xyz[:, 1] - yc) * f[2::3] - (xyz[:, 2] - zc) * f[1::3])
        info[name] = dict(Fx=Fx, Fy=Fy, Fz=Fz, Mx=Mx, npts=len(A), nnodes=int(np.count_nonzero(f)))
        cols.append(f)
    return np.array(cols).T, info


# ----------------------------------------------------------------- case
class Case:
    def __init__(self, t, buried, dx=0.025, dp=0.05, nmodes=80, soil=None, eta=0.02, nchief=24, seed=7, modal=True, bem=True):
        self.t, self.buried, self.dx, self.dp = t, buried, dx, dp
        zb = -0.4 if buried else 0.0
        self.slab = Slab(t, W_SLAB, H_SLAB, dx, zb=zb, eta=eta)
        self.soil = soil or soil_props(eta=0.0)
        faces = ['bottom', 'front', 'back', 'left', 'right'] if buried else ['bottom']
        self.t0 = time.time()
        self.faces = faces
        self.modal = ModalModel(self.slab, faces, self.soil, nmodes=nmodes) if modal else None
        self.F, self.load_checks = build_loads(self.slab)
        cg, cl, tags = exposed_panels(self.slab, dp)
        self.panels = Panels(cg); self.tags = tags
        self.Pvel = velocity_operator(self.slab, cl, self.panels.nrm, dp)
        self.PvelPhi = self.Pvel @ self.modal.Phi if modal else None
        # virtual accelerometers (specimen coords): A1 drill-side face near hole, A2 rear face opposite hole, A3 top-corner region
        zl = DRILL['zl']
        self.sensor_names = ['A1_front', 'A2_rear', 'A3_top']
        self.sensors = [(0.0, DRILL['yc'] + 0.15, zl), (t, DRILL['yc'], zl), (t / 2, 0.85, H_SLAB)]
        self.Asens = sp.vstack([node_dof_op(self.slab, p, 0) for p in self.sensors]).tocsr()
        self.AsPhi = self.Asens @ self.modal.Phi if modal else None
        self.mic_names = list(mic_positions(t).keys())
        self.mics = np.array(list(mic_positions(t).values()))
        rng = np.random.default_rng(seed)
        zt = max(0.0, 0.0) + 0.0
        ztop = H_SLAB + zb
        ch = np.stack([rng.uniform(0.15 * t, 0.85 * t, nchief), rng.uniform(0.1, 0.9, nchief), rng.uniform(0.05 * ztop, 0.95 * ztop, nchief)], 1)
        self.chief = ch
        self.bem = BEM(self.panels, ground=True, chief=ch, mics=self.mics) if bem else None
        self.build_time = time.time() - self.t0

    def sweep(self, freqs, nm=None, loads=None, keep_v=True, verbose=False):
        nm = nm or self.modal.nm
        F = self.F if loads is None else loads
        nf, nc = len(freqs), F.shape[1]
        pm = np.zeros((nf, len(self.mics), nc), complex)
        acc = np.zeros((nf, len(self.sensors), nc), complex)
        vp = np.zeros((nf, self.panels.n, nc), complex) if keep_v else None
        Fm = self.modal.Phi[:, :nm].T @ F
        for i, f in enumerate(freqs):
            w = 2 * np.pi * f
            q = self.modal.solve(w, F, nm=nm)
            v = 1j * w * (self.PvelPhi[:, :nm] @ q)             # normal velocity (outward positive)
            acc[i] = -w ** 2 * (self.AsPhi[:, :nm] @ q)
            out = self.bem.solve(w, v)
            pm[i] = out['p_mic']
            if keep_v: vp[i] = v
            if verbose and i % 40 == 0: print(f'  f={f:.1f} ({i}/{nf}) {time.time() - self.t0:.0f}s', flush=True)
        return dict(freq=np.asarray(freqs), p=pm, acc=acc, v=vp)
