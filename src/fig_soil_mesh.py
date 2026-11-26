"""Figures of the solid-soil model: graded mesh (two sections), and the soil impedance seen by the slab (solid vs springs)."""
import numpy as np, pathlib
from figstyle import *
from matplotlib.collections import LineCollection, PolyCollection
import solidmesh as sm

ROOT = pathlib.Path(__file__).resolve().parents[1]


def section(m, axis, val, ax):
    """cells whose centre lies within half a cell of the plane axis = val; draw their projected rectangles."""
    xyz = m['xyz']; cells = m['cells']; kinds = m['kind']
    a, b = [i for i in range(3) if i != axis]
    polys = []; col = []
    for ci in range(len(cells)):
        P = xyz[cells[ci]]
        lo, hi = P[:, axis].min(), P[:, axis].max()
        if not (lo - 1e-9 <= val <= hi + 1e-9): continue
        x0, x1, y0, y1 = P[:, a].min(), P[:, a].max(), P[:, b].min(), P[:, b].max()
        polys.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]); col.append('#E6EEF5' if kinds[ci] == 1 else '#F4E9D6')
    ax.add_collection(PolyCollection(polys, facecolors=col, edgecolors=NAVY, linewidths=0.35))
    return a, b


def fig_mesh():
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 5.2))
    m = sm.build(0.1, True, half=True)
    # x-z section through the drill axis plane y = 0.75 (inside the half model); y-z section through x = t/2
    section(m, 1, 0.75, axs[0]); section(m, 0, 0.05, axs[1])
    axs[0].set_xlim(-1.6, 1.7); axs[0].set_ylim(-2.1, 1.1); axs[1].set_xlim(0.45, 2.55); axs[1].set_ylim(-2.1, 1.1)
    for a, (xl, yl, tt) in zip(axs, (('x [m]', 'z [m]', 'חתך x–z דרך הלוח (y=0.75 m)'), ('y [m]', 'z [m]', 'חתך y–z (x=0.05 m) ; סימטריה ב-y=0.5 m, בקצה השמאלי'))):
        a.set_aspect('equal'); a.set_xlabel(H(xl)); a.set_ylabel(H(yl)); a.set_title(H(tt), fontsize=11.5); a.axhline(0, color=ORANGE, lw=1.8); a.grid(False)
    axs[0].text(-1.5, 0.05, H('קו הקרקע'), color=ORANGE, fontsize=10)
    axs[0].text(0.55, -1.85, H('בולמי Lysmer על הפאות החיצוניות'), color=RED, fontsize=10)
    fig.suptitle(H('רשת אדמה מוצקה ולוח בטון, מקרה t=100 mm קבור: אלמנטים קטנים ליד הלוח ומתרחבים החוצה (כחול: בטון)'), fontsize=12.5)
    save(fig, 'main', 'solid_mesh')


def fig_impedance():
    """Vertical (x, the drill axis) dynamic stiffness seen by a rigid slab motion: solid block vs springs/dashpots, t=100 mm buried."""
    from coupled import SolidCase
    from model import Case
    from fem import soil_props
    sc = SolidCase(0.1, True, verbose=False, nmodes=40)
    c = Case(0.1, True, dx=0.05, modal=False, bem=False, soil=soil_props(eta=0.0)); sl = c.slab
    Ak, Ac = sl.soil_matrices(c.soil, c.faces)
    ux = np.zeros(sl.ndof); ux[0::3] = 1.0                       # rigid translation along the drill axis
    ks = ux @ (Ak @ ux); cs = ux @ (Ac @ ux)
    # solid: u_x = 1 on the interface dofs of the half model (x-dofs), doubled for the full slab
    fr = np.arange(40, 1001, 40.0); Kre, Kim = [], []
    idx = [k for k, g in enumerate(sc.soil.idof) if g % 3 == 0]
    for f in fr:
        D = sc.soil.D_cond(2 * np.pi * f); K = 2 * D[np.ix_(idx, idx)].sum(); Kre.append(K.real); Kim.append(K.imag)
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.3))
    ax[0].plot(fr, np.array(Kre) / 1e8, color=TEAL, lw=2, label=H('אדמה מוצקה')); ax[0].axhline(ks / 1e8, color=GRAY, ls='--', lw=2, label=H('קפיצים: קבוע'))
    ax[0].set_xlabel(H('תדר [Hz]')); ax[0].set_ylabel(H('חלק ממשי, קשיחות דינמית [10⁸ N/m]')); ax[0].legend(); ax[0].set_title(H('קשיחות'), fontsize=12)
    ax[1].plot(fr, np.array(Kim) / 1e8, color=TEAL, lw=2, label=H('אדמה מוצקה')); ax[1].plot(fr, 2 * np.pi * fr * cs / 1e8, color=GRAY, ls='--', lw=2, label=H('בולמים: ω·c'))
    ax[1].set_xlabel(H('תדר [Hz]')); ax[1].set_ylabel(H('חלק מדומה [10⁸ N/m]')); ax[1].legend(); ax[1].set_title(H('בלימה (חלק מדומה)'), fontsize=12)
    fig.suptitle(H('העכבה שהאדמה מציבה לתנועת גוף קשיח של הלוח לאורך ציר הקידוח, t=100 mm קבור'), fontsize=12.5)
    save(fig, 'main', 'solid_impedance')
    np.savez(ROOT / 'results' / 'impedance_compare.npz', f=fr, Kre=Kre, Kim=Kim, ks=ks, cs=cs)


if __name__ == '__main__':
    import sys
    fig_mesh()
    if len(sys.argv) > 1 and sys.argv[1] == 'imp': fig_impedance()
