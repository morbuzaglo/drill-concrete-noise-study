"""Independent cross-check of CalculiX + Bempp-cl results with the in-house modal FEM + collocation BEM (same geometry, loads, soil)."""
import sys, numpy as np, csv, pathlib, time
from model import Case, PREF
from fem import soil_props
from post import *
ROOT = pathlib.Path(__file__).resolve().parents[1]

def run(cid, tag='_dx0.05', dx=0.05, nsel=36, do_acoustic=True):
    t, bur = {'t10_exp': (0.1, False), 't10_bur': (0.1, True), 't20_exp': (0.2, False), 't20_bur': (0.2, True)}[cid]
    r = load_ccx(cid, tag)
    f = r['freq']; sel = np.unique(np.linspace(0, len(f) - 1, nsel).astype(int)); fs = f[sel]
    c = Case(t, bur, dx=dx, dp=0.05, nmodes=60, soil=soil_props(eta=0.0), eta=0.02, modal=True, bem=do_acoustic)
    out = c.sweep(fs, loads=c.F[:, :1], keep_v=True)
    # structural: sensor accelerations and rms normal velocity
    a_own = np.abs(out['acc'][:, :, 0]); a_ccx = np.abs(r['acc'][sel, :, 0])
    d_acc = 20 * np.log10(a_own / a_ccx)
    v_own = np.sqrt(np.mean(np.abs(out['v'][:, :, 0]) ** 2, axis=1)); v_ccx = np.sqrt(np.mean(np.abs(r['v'][sel, :, 0]) ** 2, axis=1))
    d_v = 20 * np.log10(v_own / v_ccx)
    # acoustic with identical velocities: own BEM on ccx velocities vs own BEM on own velocities
    res = dict(f=fs, d_acc=d_acc, d_v=d_v)
    if do_acoustic:
        p_own = out['p'][:, :, 0]
        p_mix = np.array([c.bem.solve(2 * np.pi * fq, r['v'][i, :, :1])['p_mic'][:, 0] for fq, i in zip(fs, sel)])
        res['p_own'] = p_own; res['p_mix'] = p_mix
    return res, sel

if __name__ == '__main__':
    cid = sys.argv[1]; tag = sys.argv[2] if len(sys.argv) > 2 else '_dx0.05'
    t0 = time.time(); res, sel = run(cid, tag)
    np.savez(ROOT / 'results' / f'crosscheck_own_{cid}.npz', sel=sel, **res)
    print(cid, 'time %.0fs' % (time.time() - t0))
    print(' sensor |a| own/ccx dB: mean abs %.3f max abs %.3f' % (np.mean(np.abs(res['d_acc'])), np.max(np.abs(res['d_acc']))))
    print(' rms normal velocity own/ccx dB: mean abs %.3f max abs %.3f' % (np.mean(np.abs(res['d_v'])), np.max(np.abs(res['d_v']))))
