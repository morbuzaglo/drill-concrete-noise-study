"""Main analysis: narrowband pressure transfer functions, octave-band levels, case comparisons, CSV tables and figures.
usage: python analyze.py [bempp|own]    (default bempp = CalculiX velocities + Bempp-cl transfer vectors)"""
import sys, csv, numpy as np, pathlib
from post import *
from figstyle import *

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = sys.argv[1] if len(sys.argv) > 1 else 'bempp'
TAG = '_dx0.05'
UIND, UDIFF = 1.0, 1.4          # numerical uncertainty [dB] of a band level / of a between-case difference (rss of the convergence results)
RES = ROOT / 'results'
BANDS = EDGES[:5]; BL = LABEL[:5]
MICS = ['F', 'R', 'Rg', 'O']        # F,R,Rg: Bempp-cl; O (oblique, off-plane): in-house BEM
COL = {'t10_exp': NAVY, 't10_bur': TEAL, 't20_exp': ORANGE, 't20_bur': RED}
LSTY = {'t10_exp': '-', 't10_bur': '--', 't20_exp': '-', 't20_bur': '--'}
HLAB = {'t10_exp': 't=100 mm חשוף', 't10_bur': 't=100 mm קבור', 't20_exp': 't=200 mm חשוף', 't20_bur': 't=200 mm קבור'}


def get_p(cid, src=SRC, tag=TAG):
    if src == 'own':
        d = np.load(RES / f'ownbem_{cid}{tag}.npz'); f, p = d['f'], d['p'].copy()
    else:
        f, p, _ = pressure(cid, tag)
    fO = RES / f'ownbemO_{cid}{tag}.npz'
    if fO.exists(): p[:, 3] = np.load(fO)['p'][:, 0]          # column 3 = oblique microphone O (the original S mic is a dipole null)
    return f, p


def get_all(src=SRC, tag=TAG):
    return {cid: get_p(cid, src, tag) for cid in CASES}


def tf_db(p):
    return 20 * np.log10(np.abs(p) / PREF)


def band_tab(P):
    """octave-band mean-square pressure transfer, dB re 20 uPa per N for a flat force PSD of 1 N^2/Hz*(band width)  [= SPL for 1 N rms per Hz^0.5 ...]"""
    return {cid: tf_band_level(f, p, BANDS) for cid, (f, p) in P.items()}


def spectrum_levels(P, kind, frms=10.0):
    out = {}
    for cid, (f, p) in P.items():
        S = force_psd(f, kind, frms)
        out[cid] = band_levels(f, p, S, BANDS)
    return out


def effects(L):
    """L: dict cid -> (nband, nmic). Returns thickness effects (t20-t10) at exp/bur, burial effects (bur-exp) at t10/t20, interaction."""
    th_e = L['t20_exp'] - L['t10_exp']; th_b = L['t20_bur'] - L['t10_bur']
    bu_10 = L['t10_bur'] - L['t10_exp']; bu_20 = L['t20_bur'] - L['t20_exp']
    return dict(thick_exposed=th_e, thick_buried=th_b, burial_t100=bu_10, burial_t200=bu_20, interaction=bu_20 - bu_10)


def write_csvs(P, Lflat, Lpink, Ltf):
    d = RES / 'tables'; d.mkdir(exist_ok=True)
    for cid, (f, p) in P.items():
        with open(d / f'tf_narrowband_{cid}.csv', 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh); w.writerow(['f_Hz'] + [f'{m}_dB_re20uPa_per_N' for m in MICS] + [f'{m}_phase_deg' for m in MICS] + [f'{m}_abs_Pa_per_N' for m in MICS])
            for i in range(len(f)):
                w.writerow([f'{f[i]:.4f}'] + [f'{tf_db(p[i, j]):.3f}' for j in range(4)] + [f'{np.degrees(np.angle(p[i, j])):.2f}' for j in range(4)] + [f'{np.abs(p[i, j]):.6e}' for j in range(4)])
    def dump(name, L):
        with open(d / name, 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh); w.writerow(['case', 'mic'] + [f'{b}Hz' for b in BL])
            for cid in CASES:
                for j, m in enumerate(MICS): w.writerow([cid, m] + [f'{L[cid][i, j]:.2f}' for i in range(len(BL))])
    dump('band_meansq_transfer_dB_re20uPa_per_N.csv', Ltf); dump('band_SPL_assumed_flat_10Nrms.csv', Lflat); dump('band_SPL_assumed_pink_10Nrms.csv', Lpink)
    for nm, L in (('flat', Lflat), ('tf', Ltf)):
        E = effects(L)
        with open(d / f'band_effects_{nm}.csv', 'w', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh); w.writerow(['effect', 'mic'] + [f'{b}Hz' for b in BL])
            for k, v in E.items():
                for j, m in enumerate(MICS): w.writerow([k, m] + [f'{v[i, j]:+.2f}' for i in range(len(BL))])


def fig_tf(P):
    fig, axs = plt.subplots(3, 1, figsize=(9.5, 10), sharex=True)
    for a, (j, m, ttl) in zip(axs, ((0, 'F', 'מיקרופון F – חזית, 1.0 m מהפנים'), (1, 'R', 'מיקרופון R – גב, 1.0 m מהפנים האחוריים'), (3, 'O', 'מיקרופון O – אלכסוני, מחוץ למישור הלוח'))):
        for cid, (f, p) in P.items():
            a.plot(f, tf_db(p[:, j]), color=COL[cid], ls=LSTY[cid], lw=1.5, label=H(HLAB[cid]))
        a.set_ylabel(H('dB יחסית ל-20 µPa ל-N')); a.set_title(H(ttl)); a.set_xscale('log'); a.set_ylim(-5, 65); a.set_xticks([50, 63, 100, 125, 250, 500, 1000]); a.set_xticklabels(['50', '63', '100', '125', '250', '500', '1000'])
        for fe in (44.2, 88.4, 176.8, 353.6, 707.1, 1414.2): a.axvline(fe, color='#B8C2CF', lw=0.7, ls=':')
    axs[0].legend(ncol=2, fontsize=9.5); axs[-1].set_xlabel(H('תדר [Hz]'))
    axs[-1].set_xlim(44, 1420)
    fig.suptitle(H('פונקציות תמסורת לחץ-כוח, עומס צירי יחידה 1 N, ' + 'f = 44–1414 Hz'), fontsize=13)
    save(fig, 'main', 'tf_narrowband')


def fig_bands(Ltf):
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.4), sharey=True)
    for a, (j, m) in zip(axs, ((0, 'F'), (1, 'R'), (3, 'O'))):
        x = np.arange(len(BL)); w = 0.2
        for k, cid in enumerate(CASES):
            a.bar(x + (k - 1.5) * w, Ltf[cid][:, j], w, color=COL[cid], label=H(HLAB[cid]))
        a.set_xticks(x); a.set_xticklabels(BL); a.set_xlabel(H('פס אוקטבה, מרכז [Hz]')); a.set_title(H(f'מיקרופון {m}'))
    axs[0].set_ylabel(H('dB יחסית ל-20 µPa ל-N, ספקטרום כוח שטוח')); axs[0].legend(fontsize=9, ncol=1)
    fig.suptitle(H('רמת לחץ ממוצעת בפס אוקטבה לכוח יחידה, ספקטרום עירור שטוח'), fontsize=13)
    save(fig, 'main', 'band_levels')


def fig_effects(Ltf, U=None):
    E = effects(Ltf)
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.4), sharey=True)
    for a, (j, m) in zip(axs, ((0, 'F'), (1, 'R'), (3, 'O'))):
        x = np.arange(len(BL)); w = 0.2
        for k, (key, lab, c) in enumerate((('thick_exposed', 'עובי 200 לעומת 100 mm, חשוף', NAVY), ('thick_buried', 'עובי 200 לעומת 100 mm, קבור', TEAL), ('burial_t100', 'קבורה לעומת חשוף, t=100 mm', ORANGE), ('burial_t200', 'קבורה לעומת חשוף, t=200 mm', RED))):
            a.bar(x + (k - 1.5) * w, E[key][:, j], w, color=c, label=H(lab), yerr=(None if U is None else U[:, j]), capsize=2, ecolor='k')
        a.axhspan(-UDIFF, UDIFF, color='#E6EEF5', zorder=0, label=H('אי-ודאות מספרית של הפרש')); a.axhline(0, color='k', lw=0.8); a.set_xticks(x); a.set_xticklabels(BL); a.set_xlabel(H('פס אוקטבה, מרכז [Hz]')); a.set_title(H(f'מיקרופון {m}'))
    axs[0].set_ylabel(H('הפרש רמה [dB]')); axs[0].legend(fontsize=8.5, loc='best')
    fig.suptitle(H('הפרשי רמה בין המקרים לפי פס אוקטבה, עומס יחידה וספקטרום שטוח'), fontsize=13)
    save(fig, 'main', 'band_effects')


def fig_acc(P=None):
    fig, axs = plt.subplots(1, 3, figsize=(13, 3.9), sharey=True)
    for cid in CASES:
        r = load_ccx(cid, TAG); f = r['freq']
        for a, s, nm in zip(axs, range(3), ('A1 – חזית ליד החור', 'A2 – גב מול החור', 'A3 – פינה עליונה')):
            a.plot(f, 20 * np.log10(np.abs(r['acc'][:, s, 0]) / 1e-6), color=COL[cid], ls=LSTY[cid], lw=1.3, label=H(HLAB[cid])); a.set_title(H(nm)); a.set_xscale('log'); a.set_xlabel(H('תדר [Hz]'))
    axs[0].set_ylabel(H('תאוצה, dB יחסית ל-1 µm/s² ל-N')); axs[0].legend(fontsize=8.5)
    save(fig, 'main', 'acc_sensors')


if __name__ == '__main__':
    P = get_all()
    Ltf = band_tab(P); Lflat = spectrum_levels(P, 'flat'); Lpink = spectrum_levels(P, 'pink')
    write_csvs(P, Lflat, Lpink, Ltf)
    fig_tf(P); fig_bands(Ltf); fig_effects(Ltf); fig_acc()
    E = effects(Ltf)
    np.set_printoptions(precision=2, suppress=True, linewidth=150)
    for cid in CASES: print(cid, 'band transfer dB re20uPa/N (rows=bands, cols=F,R,Rg,S)\n', Ltf[cid])
    for k, v in E.items(): print(k, '\n', v)
