"""Solid-soil model vs the spring/dashpot model: pressure transfer functions, octave-band levels, case effects, comparison tables and figures.
usage: python analyze_solid.py [tag=_solid]     (needs results/ccx_<case><tag>.npz from run_solid_cases.py)
Mics: F, R, Rg (Bempp-cl transfer vectors, same acoustic model for both soil models)."""
import sys, csv, numpy as np, pathlib
import analyze as A
from post import *
from figstyle import *

ROOT = pathlib.Path(__file__).resolve().parents[1]; RES = ROOT / 'results'
TAG = sys.argv[1] if len(sys.argv) > 1 else '_solid'
CASES = ['t10_exp', 't10_bur', 't20_exp', 't20_bur']; MICS = ['F', 'R', 'Rg']; B = A.BANDS; BL = A.BL
COL = A.COL; HLAB = A.HLAB


def get_solid(tag=TAG):
    out = {}
    for cid in CASES:
        if (RES / f'ccx_{cid}{tag}.npz').exists():
            f, p, _ = pressure(cid, tag); out[cid] = (f, p[:, :3])
    return out


def get_spring():
    out = {}
    for cid in CASES:
        f, p, _ = pressure(cid, '_dx0.05'); out[cid] = (f, p[:, :3])
    return out


def bands(P): return {cid: tf_band_level(f, p, B) for cid, (f, p) in P.items()}


def effects(L):
    E = {}
    if all(c in L for c in CASES):
        E['thick_exposed'] = L['t20_exp'] - L['t10_exp']; E['thick_buried'] = L['t20_bur'] - L['t10_bur']
        E['burial_t100'] = L['t10_bur'] - L['t10_exp']; E['burial_t200'] = L['t20_bur'] - L['t20_exp']
    return E


def write(Lsp, Lso):
    d = RES / 'tables'; d.mkdir(exist_ok=True)
    with open(d / f'solid_band_meansq_transfer{TAG}.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['model', 'case', 'mic'] + [f'{b}Hz' for b in BL])
        for nm, L in (('springs', Lsp), ('solid', Lso)):
            for cid in CASES:
                if cid in L:
                    for j, m in enumerate(MICS): w.writerow([nm, cid, m] + [f'{L[cid][i, j]:.2f}' for i in range(len(BL))])
    with open(d / f'solid_minus_springs{TAG}.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['case', 'mic'] + [f'{b}Hz' for b in BL])
        for cid in CASES:
            if cid in Lso:
                for j, m in enumerate(MICS): w.writerow([cid, m] + [f'{Lso[cid][i, j] - Lsp[cid][i, j]:+.2f}' for i in range(len(BL))])
    with open(d / f'solid_effects{TAG}.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh); w.writerow(['model', 'effect', 'mic'] + [f'{b}Hz' for b in BL])
        for nm, L in (('springs', Lsp), ('solid', Lso)):
            for k, v in effects(L).items():
                for j, m in enumerate(MICS): w.writerow([nm, k, m] + [f'{v[i, j]:+.2f}' for i in range(len(BL))])


def fig_tf(Psp, Pso):
    cases = [c for c in ('t10_exp', 't10_bur', 't20_exp', 't20_bur') if c in Pso]
    fig, axs = plt.subplots(2, 2, figsize=(12, 7.2), sharex=True, sharey=True)
    for a, cid in zip(axs.ravel(), cases):
        f, p = Psp[cid]; a.plot(f, A.tf_db(p[:, 0]), color=GRAY, lw=1.3, ls='-', label=H('קפיצים ובולמים'))
        f, p = Pso[cid]; a.plot(f, A.tf_db(p[:, 0]), color=COL[cid], lw=1.4, label=H('אדמה מוצקה'))
        a.set_xscale('log'); a.set_title(H(HLAB[cid])); a.set_ylim(-10, 70); a.set_xticks([50, 100, 250, 500, 1000]); a.set_xticklabels(['50', '100', '250', '500', '1000'])
        a.axvline(250, color='#B8C2CF', lw=0.8, ls=':')
    axs[0, 0].legend(fontsize=9.5)
    for a in axs[1]: a.set_xlabel(H('תדר [Hz]'))
    for a in axs[:, 0]: a.set_ylabel(H('dB יחסית ל-20 µPa ל-N'))
    fig.suptitle(H('פונקציות תמסורת לחץ-כוח, מיקרופון F: אדמה מוצקה מול קפיצים'), fontsize=13)
    save(fig, 'main', 'solid_vs_springs_tf')


def fig_bands(Lsp, Lso):
    cases = [c for c in CASES if c in Lso]
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.4), sharey=True)
    for a, (nm, L) in zip(axs, (('קפיצים ובולמים', Lsp), ('אדמה מוצקה', Lso))):
        x = np.arange(len(BL)); w = 0.2
        for k, cid in enumerate(cases): a.bar(x + (k - 1.5) * w, L[cid][:, 0], w, color=COL[cid], label=H(HLAB[cid]))
        a.set_xticks(x); a.set_xticklabels(BL); a.set_xlabel(H('פס אוקטבה, מרכז [Hz]')); a.set_title(H(nm))
    axs[0].set_ylabel(H('dB יחסית ל-20 µPa ל-N, ספקטרום כוח שטוח')); axs[0].legend(fontsize=9)
    fig.suptitle(H('רמת לחץ ממוצעת בפס אוקטבה לכוח יחידה, מיקרופון F'), fontsize=13)
    save(fig, 'main', 'solid_vs_springs_bands')


def fig_effects(Lsp, Lso):
    Esp, Eso = effects(Lsp), effects(Lso)
    if not Eso: return
    keys = (('thick_exposed', 'עובי 200 לעומת 100 mm, חשוף'), ('thick_buried', 'עובי 200 לעומת 100 mm, קבור'), ('burial_t100', 'קבורה לעומת חשוף, t=100 mm'), ('burial_t200', 'קבורה לעומת חשוף, t=200 mm'))
    fig, axs = plt.subplots(2, 2, figsize=(12, 7), sharey=True, sharex=True)
    for a, (k, lab) in zip(axs.ravel(), keys):
        x = np.arange(len(BL)); w = 0.38
        a.bar(x - w / 2, Esp[k][:, 0], w, color=GRAY, label=H('קפיצים ובולמים')); a.bar(x + w / 2, Eso[k][:, 0], w, color=TEAL, label=H('אדמה מוצקה'))
        a.axhspan(-A.UDIFF, A.UDIFF, color='#E6EEF5', zorder=0); a.axhline(0, color='k', lw=0.8); a.set_title(H(lab), fontsize=11.5)
        a.set_xticks(x); a.set_xticklabels(BL)
    axs[0, 0].legend(fontsize=9); axs[1, 0].set_xlabel(H('פס אוקטבה, מרכז [Hz]')); axs[1, 1].set_xlabel(H('פס אוקטבה, מרכז [Hz]'))
    for a in axs[:, 0]: a.set_ylabel(H('הפרש רמה [dB]'))
    fig.suptitle(H('השפעות עובי וקבורה בשני מודלי האדמה, מיקרופון F'), fontsize=13)
    save(fig, 'main', 'solid_vs_springs_effects')


if __name__ == '__main__':
    Psp = get_spring(); Pso = get_solid()
    Lsp = bands(Psp); Lso = bands(Pso)
    write(Lsp, Lso)
    np.set_printoptions(precision=1, suppress=True, linewidth=150)
    for cid in Pso:
        print(cid, 'springs F', Lsp[cid][:, 0], '\n', ' ' * len(cid), 'solid  F', Lso[cid][:, 0], ' diff', Lso[cid][:, 0] - Lsp[cid][:, 0])
    if len(Pso) == 4:
        for k, v in effects(Lso).items(): print('solid', k, v[:, 0])
        for k, v in effects(Lsp).items(): print('springs', k, v[:, 0])
        fig_tf(Psp, Pso); fig_bands(Lsp, Lso); fig_effects(Lsp, Lso)
