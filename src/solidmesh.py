"""Structured graded hex mesh of the concrete slab AND a solid soil block (half model, symmetry plane y = 0.5).
Global coordinates: x = drill axis (slab 0..t), y = width (slab 0..1, half model y >= 0.5), z = height above the soil line (soil z < 0).
Nodes are shared between concrete and soil cells, so the interface is conforming. Units SI."""
import numpy as np

YC = 0.5                      # symmetry plane (drill axis y)


def grade_out(x0, L, h0=0.05, g=1.25, hmax=0.30):
    """Increasing coordinates after x0 up to x0+L with cell size h0*g^k (capped at hmax); the last cell is adjusted to hit L exactly."""
    xs = [0.0]; h = h0
    while xs[-1] + h < L - 1e-9:
        xs.append(xs[-1] + h); h = min(h * g, hmax)
    if L - xs[-1] < 0.5 * h and len(xs) > 1: xs[-1] = L
    else: xs.append(L)
    return x0 + np.array(xs[1:])


def axis_lines(lo, hi, dx, out_lo, out_hi, **kw):
    """uniform lines lo..hi (step dx) with graded lines outside; out_* are the outer extents (>= 0)."""
    core = lo + dx * np.arange(int(round((hi - lo) / dx)) + 1)
    left = (lo - grade_out(0.0, out_lo, **kw))[::-1] if out_lo > 0 else np.array([])
    right = grade_out(hi, out_hi, **kw) if out_hi > 0 else np.array([])
    return np.concatenate([left, core, right])


def build(t, buried, Lx=1.5, Ly=1.5, D=2.0, dx=0.05, h0=0.05, g=1.2, hmax=0.20, W=1.0, H=1.0, half=True):
    zb = -0.4 if buried else 0.0
    xs = axis_lines(0.0, t, dx, Lx, Lx, h0=h0, g=g, hmax=hmax)
    y0 = YC if half else 0.0
    ys = axis_lines(y0, W, dx, 0.0 if half else Ly, Ly, h0=h0, g=g, hmax=hmax)      # half model: from the symmetry plane
    # z lines: slab-region uniform from zb up to the soil line (buried) or just the soil line (exposed); graded downwards
    ztop = 0.0
    zlow = zb if buried else 0.0
    zs_core = zlow + dx * np.arange(int(round((ztop - zlow) / dx)) + 1) if buried else np.array([0.0])
    zs = np.concatenate([(zlow - grade_out(0.0, D, h0=h0, g=g, hmax=hmax))[::-1], zs_core])
    nx, ny, nz = len(xs) - 1, len(ys) - 1, len(zs) - 1
    cx = 0.5 * (xs[1:] + xs[:-1]); cy = 0.5 * (ys[1:] + ys[:-1]); cz = 0.5 * (zs[1:] + zs[:-1])
    # soil cells: all cells below the soil line except those inside the slab box (buried)
    ex, ey, ez = np.meshgrid(np.arange(nx), np.arange(ny), np.arange(nz), indexing='ij')
    ex, ey, ez = ex.ravel(), ey.ravel(), ez.ravel()
    inslab = (cx[ex] > 0) & (cx[ex] < t) & (cy[ey] > y0) & (cy[ey] < W) & (cz[ez] > zb) & (cz[ez] < zb + H)
    soil = ~inslab & (cz[ez] < 0)
    sc = np.stack([ex[soil], ey[soil], ez[soil]], 1)
    # concrete cells (own uniform grid, dx), global z = zb + k dx
    nxs, nys, nzs = int(round(t / dx)), int(round((W - y0) / dx)), int(round(H / dx))
    cex, cey, cez = np.meshgrid(np.arange(nxs), np.arange(nys), np.arange(nzs), indexing='ij')
    conc = np.stack([cex.ravel(), cey.ravel(), cez.ravel()], 1)
    # node table keyed by rounded coordinates
    key = lambda p: tuple(np.round(np.asarray(p) / 1e-7).astype(np.int64))
    table = {}; xyz = []

    def nid(p):
        k = key(p)
        i = table.get(k)
        if i is None: i = len(xyz); table[k] = i; xyz.append(p)
        return i
    cells = []; kind = []; size = []
    for (a, b, c) in sc:
        nodes = [nid((xs[a + (n & 1)], ys[b + ((n >> 1) & 1)], zs[c + ((n >> 2) & 1)])) for n in range(8)]
        cells.append(nodes); kind.append(0); size.append((xs[a + 1] - xs[a], ys[b + 1] - ys[b], zs[c + 1] - zs[c]))
    for (a, b, c) in conc:
        nodes = [nid((a * dx + (n & 1) * dx, y0 + b * dx + ((n >> 1) & 1) * dx, zb + c * dx + ((n >> 2) & 1) * dx)) for n in range(8)]
        cells.append(nodes); kind.append(1); size.append((dx, dx, dx))
    xyz = np.array(xyz); cells = np.array(cells); kind = np.array(kind); size = np.array(size)
    # interface nodes: nodes used by both a soil and a concrete cell
    used_s = np.zeros(len(xyz), bool); used_c = np.zeros(len(xyz), bool)
    used_s[cells[kind == 0].ravel()] = True; used_c[cells[kind == 1].ravel()] = True
    iface = np.nonzero(used_s & used_c)[0]
    # outer (absorbing) faces of the soil block: (node, axis, area share). planes: x=xs[0], x=xs[-1], y=ys[-1], z=zs[0]
    ab = []
    tol = 1e-9
    sc_nodes = cells[kind == 0]; ssz = size[kind == 0]
    for ci in range(len(sc_nodes)):
        nd = sc_nodes[ci]; sz = ssz[ci]; P = xyz[nd]
        for ax, val in ((0, xs[0]), (0, xs[-1]), (1, ys[-1]), (2, zs[0])) + (() if half else ((1, ys[0]),)):
            sel = [n for n in range(8) if abs(P[n, ax] - val) < tol]
            if len(sel) == 4:
                o = [a for a in range(3) if a != ax]; area = sz[o[0]] * sz[o[1]]
                for n in sel: ab.append((nd[n], ax, area / 4.0))
    ab = np.array(ab) if ab else np.zeros((0, 3))
    plane = np.nonzero(np.abs(xyz[:, 1] - YC) < tol)[0] if half else np.zeros(0, int)
    return dict(half=half, xyz=xyz, cells=cells, kind=kind, size=size, iface=iface, absorb=ab, plane=plane, xs=xs, ys=ys, zs=zs, t=t, zb=zb, buried=buried, dx=dx)


if __name__ == '__main__':
    for t, bur in ((0.1, False), (0.1, True), (0.2, True)):
        m = build(t, bur)
        print(t, bur, 'nodes', len(m['xyz']), 'soil cells', int((m['kind'] == 0).sum()), 'concrete cells', int((m['kind'] == 1).sum()), 'iface nodes', len(m['iface']),
              'grid', len(m['xs']), len(m['ys']), len(m['zs']), 'dof', 3 * len(m['xyz']))
