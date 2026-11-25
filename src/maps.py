"""Vibration maps (CalculiX panel velocities) and pressure maps on the plane y=0.5 m (BEM on the CalculiX velocities)."""
import numpy as np, pathlib
from matplotlib.collections import PolyCollection
from figstyle import *
from model import Case
from fem import soil_props
from post import *
ROOT = pathlib.Path(__file__).resolve().parents[1]
FREQS = [125.0, 340.0, 560.0, 940.0]
VREF = 1e-9      # m/s per N reference for velocity level

def v_at(r, f):
    """complex panel velocity at exactly f (linear interpolation of re/im between the two neighbouring CalculiX frequencies)"""
    fr = r['freq']; i = int(np.clip(np.searchsorted(fr, f) - 1, 0, len(fr) - 2)); a = (f - fr[i]) / (fr[i + 1] - fr[i])
    return (1 - a) * r['v'][i, :, 0] + a * r['v'][i + 1, :, 0]

def face_polys(r, ax, side):
    c = r['corners']; tg = r['tags']; m = (tg[:, 0] == ax) & (tg[:, 1] == side)
    idx = np.nonzero(m)[0]; q = c[idx]                  # (n,4,3) global
    polys = q[:, :, [1, 2]]                             # (y,z)
    return idx, polys

def vib_maps(tag='_dx0.05', freqs=FREQS):
    data = {cid: load_ccx(cid, tag) for cid in CASES}
    for fq in freqs:
        fig, axs = plt.subplots(2, 4, figsize=(13, 6.6), sharex=True, sharey=True)
        vmin, vmax = None, None; allL = []
        for j, cid in enumerate(CASES):
            r = data[cid]; vv = v_at(r, fq)
            for k, side in enumerate((0, 1)):
                idx, polys = face_polys(r, 0, side)
                L = 20 * np.log10(np.abs(vv[idx]) / VREF); allL.append(L)
        lo, hi = np.percentile(np.concatenate(allL), [2, 99.5]); lo = max(lo, hi - 40)
        for j, cid in enumerate(CASES):
            r = data[cid]; vv = v_at(r, fq)
            for k, side in enumerate((0, 1)):
                a = axs[k, j]; idx, polys = face_polys(r, 0, side)
                L = 20 * np.log10(np.abs(vv[idx]) / VREF)
                pc = PolyCollection(polys, array=L, cmap='magma', clim=(lo, hi), edgecolors='none'); a.add_collection(pc)
                a.axhline(0, color='#7A5A2A', lw=1.5); a.set_xlim(0, 1); a.set_ylim(-0.4, 1.0); a.set_aspect('equal'); a.grid(False)
                if k == 0: a.plot([0.5], [0.7 + (-0.4 if r['buried'] else 0)], 'c+', ms=10, mew=2)
                a.set_title(H(CASE_LABEL[cid].replace('exposed', 'חשוף').replace('buried', 'קבור') + (' – חזית' if side == 0 else ' – גב')), fontsize=9)
        for a in axs[1]: a.set_xlabel('y [m]')
        for a in axs[:, 0]: a.set_ylabel('z [m]')
        cb = fig.colorbar(pc, ax=axs, shrink=0.8, pad=0.02); cb.set_label(H('מהירות נורמלית, dB יחסית ל-1 nm/s ל-N'))
        fig.suptitle(H(f'מפת רעידות על פני הבטון, f = {fq:.0f} Hz, עומס יחידה 1 N, סקאלת צבע זהה'), fontsize=12)
        save(fig, 'maps', f'vib_{int(fq)}Hz')

def pressure_maps(tag='_dx0.05', freqs=FREQS):
    xs = np.linspace(-1.6, 1.7, 56); zs = np.linspace(0.03, 1.55, 40)
    X, Z = np.meshgrid(xs, zs); pts = np.stack([X.ravel(), np.full(X.size, 0.5), Z.ravel()], 1)
    store = {}
    for cid in CASES:
        r = load_ccx(cid, tag); t, bur = r['t'], r['buried']
        c = Case(t, bur, dx=0.05, dp=0.05, modal=False, bem=False)
        from bem import BEM
        mics = np.array(list(__import__('model').mic_positions(t).values()))
        zb = -0.4 if bur else 0.0
        mask = (pts[:, 0] > -0.02) & (pts[:, 0] < t + 0.02) & (pts[:, 2] < 1.0 + zb + 0.02)
        keep = ~mask
        bem = BEM(c.panels, ground=True, chief=np.stack([np.random.default_rng(3).uniform(0.15 * t, 0.85 * t, 24), np.random.default_rng(4).uniform(0.1, 0.9, 24), np.random.default_rng(5).uniform(0.05 * (1 + zb), 0.95 * (1 + zb), 24)], 1), mics=mics, field=pts[keep])
        for fq in freqs:
            o = bem.solve(2 * np.pi * fq, v_at(r, fq)[:, None], want_field=True)
            P = np.full(X.size, np.nan, complex); P[keep] = o['p_field'][:, 0]
            store[(cid, fq)] = (20 * np.log10(np.abs(P).reshape(X.shape) / PREF), fq, mics, t, zb)
    for fq in freqs:
        allv = np.concatenate([store[(cid, fq)][0][np.isfinite(store[(cid, fq)][0])] for cid in CASES])
        hi = np.percentile(allv, 99.5); lo = hi - 40
        fig, axs = plt.subplots(1, 4, figsize=(14, 3.9), sharex=True, sharey=True)
        for a, cid in zip(axs, CASES):
            L, ff, mics, t, zb = store[(cid, fq)]
            im = a.pcolormesh(X, Z, L, cmap='viridis', vmin=lo, vmax=hi, shading='auto')
            a.add_patch(__import__('matplotlib').patches.Rectangle((0, zb), t, 1.0, fc='#BFC5CC', ec=NAVY, zorder=3))
            a.axhline(0, color='#7A5A2A', lw=1.5)
            a.plot(mics[:3, 0], mics[:3, 2], 'o', color='w', mec='k', ms=6, zorder=5)
            a.set_aspect('equal'); a.grid(False); a.set_title(H(CASE_LABEL[cid].replace('exposed', 'חשוף').replace('buried', 'קבור')), fontsize=10); a.set_xlabel('x [m]')
        axs[0].set_ylabel('z [m]')
        cb = fig.colorbar(im, ax=axs, shrink=0.9, pad=0.01); cb.set_label(H('SPL, dB יחסית ל-20 µPa ל-N'))
        fig.suptitle(H(f'מפת לחץ אקוסטי במישור y = 0.5 m, f = {ff:.0f} Hz, עומס יחידה 1 N, סקאלת צבע זהה'), fontsize=12)
        save(fig, 'maps', f'pressure_{int(fq)}Hz')

if __name__ == '__main__':
    import sys
    if 'vib' in sys.argv: vib_maps()
    if 'pres' in sys.argv: pressure_maps()
