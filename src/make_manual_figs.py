"""SVG figures (plus PNG fallbacks) for the Hebrew LS-DYNA theory + practice manual. Output: figures/manual/*.svg
Schematic figures are drawn with matplotlib patches; data figures use the real project files (mesh.k, loads.k, eigout, Press_dB, CalculiX results)."""
import re, pathlib, numpy as np
from figstyle import *
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle, Circle, FancyArrowPatch, Polygon

ROOT = pathlib.Path(__file__).resolve().parents[1]
EV = ROOT / 'lsdyna' / 'run_evidence_t10_bur'
SUB = 'manual'
BLUE2 = '#3C6FB0'; GREEN = '#2E8B57'; YEL = '#FFF4D6'; PINK = '#FBE3E1'; MINT = '#E3F4EE'


def canvas(w, h, scale=0.8):
    fig, ax = plt.subplots(figsize=(w * scale, h * scale)); ax.set_xlim(0, w); ax.set_ylim(0, h); ax.set_aspect('equal'); ax.axis('off')
    return fig, ax


def label(ax, x, y, s, fs=10, ha='center', color=NAVY, bold=False, va='center'):
    ax.text(x, y, H(s), ha=ha, va=va, fontsize=fs, color=color, fontweight='bold' if bold else 'normal')


def spring(ax, p, q, n=6, w=0.14, color=NAVY, lw=1.3):
    p = np.array(p, float); q = np.array(q, float); d = q - p; L = np.linalg.norm(d); u = d / L; nrm = np.array([-u[1], u[0]])
    a = 0.18; pts = [p, p + u * L * a]
    for i in range(n):
        pts.append(p + u * L * (a + (1 - 2 * a) * (i + 0.5) / n) + nrm * w * (1 if i % 2 == 0 else -1))
    pts += [p + u * L * (1 - a), q]
    ax.plot(*np.array(pts).T, color=color, lw=lw)


def dashpot(ax, p, q, w=0.12, color=TEAL, lw=1.3):
    p = np.array(p, float); q = np.array(q, float); d = q - p; L = np.linalg.norm(d); u = d / L; nrm = np.array([-u[1], u[0]])
    m1 = p + u * L * 0.35; m2 = p + u * L * 0.62
    ax.plot(*np.array([p, m1]).T, color=color, lw=lw); ax.plot(*np.array([m2 + u * L * 0.0, q]).T, color=color, lw=lw)
    ax.plot(*np.array([m1 + nrm * w, m1 - nrm * w]).T, color=color, lw=lw)
    box_pts = np.array([m1 + nrm * w * 1.5 + u * L * 0.28, m1 + nrm * w * 1.5, m1 - nrm * w * 1.5, m1 - nrm * w * 1.5 + u * L * 0.28])
    ax.plot(*box_pts.T, color=color, lw=lw)


def hatch(ax, x0, x1, y, n=14, d=0.12, color=GRAY):
    xs = np.linspace(x0, x1, n)
    ax.plot([x0, x1], [y, y], color=color, lw=1.6)
    for x in xs: ax.plot([x, x - d], [y, y - d], color=color, lw=0.9)


# ---------------------------------------------------------------- F1 chain
def f01_chain():
    fig, ax = canvas(13, 3.6, 0.85)
    xs = [0.2, 3.5, 6.8, 10.1]; names = ['מקור\nכוח קידוח F(f)', 'מבנה\nלוח בטון + אדמה', 'קרינה\nמהירות משטח v → לחץ', 'מקלט\nלחץ p(f) במיקרופון']
    cols = [YEL, LIGHT, MINT, PINK]
    for x, n, c in zip(xs, names, cols): box(ax, x, 1.2, 2.7, 1.5, n, fc=c, fs=11, bold=False)
    for x in xs[:-1]: arrow(ax, (x + 2.8, 1.95), (x + 3.4, 1.95))
    for x, t in zip(xs[:3], ['H_{v,F}=v/F', 'H_{p,v}=p/v', '']):
        pass
    label(ax, 3.35 + 0.05, 2.45, 'v/F', 10, color=TEAL); label(ax, 6.65, 2.45, 'p/v', 10, color=TEAL)
    label(ax, 6.5, 0.85, 'פונקציית התמסורת הכוללת, ביחידות Pa/N:', 11, bold=True)
    label(ax, 6.5, 0.3, 'H_pF = p/F = (v/F) · (p/v)      [ SSD  ×  BEM ]', 11, color=TEAL)
    label(ax, 6.5, 3.4, 'שרשרת הרעש המבני', 13, bold=True)
    save(fig, SUB, 'f01_chain')


# ---------------------------------------------------------------- F2 octave bands
def f02_octave():
    fig, ax = plt.subplots(figsize=(9.5, 3.6))
    fc = np.array([31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000]); lo = fc / np.sqrt(2); hi = fc * np.sqrt(2)
    for i, (a, b, c) in enumerate(zip(lo, hi, fc)):
        ok = 63 <= c <= 1000
        ax.add_patch(Rectangle((a, 0), b - a, 1, fc=(TEAL if ok else '#D5DBE3'), ec='white', alpha=0.9 if ok else 0.7))
        ax.text(c, 0.5, f'{c:g}', ha='center', va='center', fontsize=11, color='white' if ok else NAVY, fontweight='bold')
    ax.plot([44.19, 1414.3], [1.12, 1.12], color=ORANGE, lw=5, solid_capstyle='butt', clip_on=False)
    ax.text(250, 1.2, H('תחום החישוב: 44.2–1414 Hz'), ha='center', fontsize=11, color=ORANGE)
    ax.set_xscale('log'); ax.set_xlim(20, 12000); ax.set_ylim(0, 1.35); ax.set_yticks([]); ax.grid(False)
    ax.set_xlabel(H('תדר [Hz]; גבולות הפס fc/√2 ... fc·√2'))
    ax.spines['left'].set_visible(False)
    save(fig, SUB, 'f02_octave')


# ---------------------------------------------------------------- F3 SDOF
def f03_sdof():
    fig, axs = plt.subplots(2, 1, figsize=(8, 6.2), sharex=True)
    r = np.logspace(-1, 1, 1200)
    for z, c, ls in ((0.01, NAVY, '-'), (0.05, TEAL, '--'), (0.2, ORANGE, '-.')):
        h = 1 / (1 - r ** 2 + 2j * z * r)
        axs[0].loglog(r, np.abs(h), color=c, ls=ls, lw=1.8, label=H(f'ζ = {z}'))
        axs[1].semilogx(r, np.degrees(np.angle(h)), color=c, ls=ls, lw=1.8)
    axs[0].set_ylabel(H('|H| = |x| · k / F')); axs[0].legend(); axs[0].set_ylim(0.01, 80)
    axs[0].set_title(H('מערכת דרגת חופש אחת: משרעת ופאזה כפונקציה של ω/ωₙ'))
    axs[0].annotate(H('שיא ≈ 1/(2ζ)'), (1, 50), (2.2, 40), arrowprops=dict(arrowstyle='->', color=GRAY), fontsize=11)
    axs[1].set_ylabel(H('פאזה [°]')); axs[1].set_xlabel(H('יחס תדרים  ω / ωₙ')); axs[1].set_yticks([0, -45, -90, -135, -180])
    axs[1].axvline(1, color=GRAY, lw=0.8, ls=':'); axs[0].axvline(1, color=GRAY, lw=0.8, ls=':')
    save(fig, SUB, 'f03_sdof')


# ---------------------------------------------------------------- F4 plate modes
def f04_modes():
    fig, axs = plt.subplots(2, 3, figsize=(9.5, 6.2))
    x = np.linspace(0, 1, 120); X, Y = np.meshgrid(x, x)
    D = 30e9 * 0.1 ** 3 / (12 * (1 - 0.2 ** 2)); rh = 2400 * 0.1
    for ax, (m, n) in zip(axs.ravel(), ((1, 1), (2, 1), (1, 2), (2, 2), (3, 1), (3, 2))):
        Z = np.sin(m * np.pi * X) * np.sin(n * np.pi * Y)
        ax.contourf(X, Y, Z, levels=np.linspace(-1, 1, 21), cmap='RdBu_r'); ax.contour(X, Y, Z, levels=[0], colors='k', linewidths=1.2)
        f = np.pi / 2 * (m * m + n * n) * np.sqrt(D / rh); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        ax.set_title(H(f'(m,n) = ({m},{n})   f ≈ {f:.0f} Hz'), fontsize=11)
    fig.suptitle(H('צורות מודים של לוח מרובע נשען חופשית (100 mm בטון, 1×1 m): קווים שחורים הם קווי צומת'), fontsize=12)
    save(fig, SUB, 'f04_modes')


# ---------------------------------------------------------------- F5 mesh rule
def f05_meshrule():
    fig, ax = plt.subplots(figsize=(8.5, 5))
    f = np.logspace(np.log10(40), np.log10(2000), 300); w = 2 * np.pi * f
    for t, c, ls in ((0.1, NAVY, '-'), (0.2, TEAL, '--')):
        D = 30e9 * t ** 3 / (12 * (1 - 0.2 ** 2)); k = (w ** 2 * 2400 * t / D) ** 0.25
        ax.loglog(f, 2 * np.pi / k / 6, color=c, ls=ls, lw=2, label=H(f'מבנה, גל כפיפה, t = {t * 1000:.0f} mm: λ_b/6'))
    ax.loglog(f, 343 / f / 6, color=ORANGE, lw=2, ls='-.', label=H('אוויר: λ/6 = c/(6f)'))
    ax.axhline(0.05, color=GRAY, lw=1.2); ax.text(2000, 0.0435, H('אלמנט מבנה בפועל: 0.05 m'), ha='right', fontsize=10, color=GRAY)
    ax.axhline(0.10, color=GRAY, lw=1.0, ls=':'); ax.text(2000, 0.112, H('פאנל BEM בפס נמוך: 0.10 m'), ha='right', fontsize=10, color=GRAY)
    ax.axvspan(44.19, 1414.3, color=LIGHT, alpha=0.6, zorder=0)
    ax.set_xlabel(H('תדר [Hz]')); ax.set_ylabel(H('גודל אלמנט מרבי [m]')); ax.legend(loc='upper right', fontsize=10); ax.set_ylim(0.01, 1.5)
    ax.set_title(H('כלל אצבע: 6 אלמנטים לאורך גל'))
    save(fig, SUB, 'f05_meshrule')


# ---------------------------------------------------------------- F6 soil model
def f06_soil():
    fig, ax = canvas(11.5, 5.2, 0.85)
    # left: concrete slab side view, partially buried
    ax.add_patch(Rectangle((2.0, 1.2), 0.9, 3.0, fc=LIGHT, ec=NAVY, lw=1.8)); label(ax, 2.45, 3.4, 'בטון', 10)
    ax.plot([0.3, 4.7], [2.2, 2.2], color=ORANGE, lw=2); label(ax, 4.1, 2.45, 'קו הקרקע', 9, color=ORANGE)
    hatch(ax, 0.3, 4.7, 0.5, 18)
    for y in (1.4, 1.8):   # side springs/dashpots (normal)
        spring(ax, (1.0, y + 0.0), (2.0, y), n=5); dashpot(ax, (3.9, y + 0.0), (2.9, y), color=TEAL)
    spring(ax, (2.25, 0.5), (2.25, 1.2), n=4); dashpot(ax, (2.65, 0.5), (2.65, 1.2))
    ax.plot([1.0, 1.0], [1.3, 1.9], color=GRAY, lw=3); ax.plot([3.9, 3.9], [1.3, 1.9], color=GRAY, lw=3)
    label(ax, 0.75, 1.6, 'קצה קבוע', 8.5, color=GRAY); label(ax, 4.5, 1.1, 'k, c', 12, color=NAVY)
    label(ax, 2.5, 4.75, 'מודל קפיצים ובולמים (Winkler)', 11, bold=True)
    # right: half space alternative
    ax.add_patch(Rectangle((7.2, 1.2), 0.9, 3.0, fc=LIGHT, ec=NAVY, lw=1.8)); label(ax, 7.65, 3.4, 'בטון', 10)
    ax.add_patch(Rectangle((5.6, 0.3), 5.6, 1.9, fc='#EADFC8', ec=GRAY, lw=1.2, ls='--'))
    ax.add_patch(Rectangle((7.2, 0.3), 0.9, 1.9, fc='#EADFC8', ec=NAVY, lw=0))
    ax.plot([7.2, 8.1], [2.2, 2.2], color='#EADFC8', lw=0)
    ax.add_patch(Rectangle((7.2, 1.2), 0.9, 1.0, fc=LIGHT, ec=NAVY, lw=1.8))
    label(ax, 8.4, 0.75, 'אדמה כגוף אלסטי (אלמנטים מוצקים)', 9, color=GRAY)
    for xx in (5.6, 11.2): ax.add_patch(Rectangle((xx - 0.05, 0.3), 0.1, 1.9, fc=RED, ec=RED, alpha=0.5))
    label(ax, 5.6, 0.1, 'גבול בולע', 8.5, color=RED); label(ax, 11.2, 0.1, 'גבול בולע', 8.5, color=RED)
    label(ax, 8.4, 4.75, 'חלופה: תחום אדמה + גבולות לא מחזירים', 11, bold=True)
    ax.plot([5.6, 11.2], [2.2, 2.2], color=ORANGE, lw=2)
    save(fig, SUB, 'f06_soil')


# ---------------------------------------------------------------- F7 coincidence
def f07_coincidence():
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    f = np.logspace(np.log10(20), np.log10(2000), 300); w = 2 * np.pi * f
    for t, c, ls in ((0.1, NAVY, '-'), (0.2, TEAL, '--')):
        D = 30e9 * t ** 3 / (12 * (1 - 0.2 ** 2)); cb = (w ** 2 * D / (2400 * t)) ** 0.25
        fc = 343 ** 2 / (2 * np.pi) * np.sqrt(2400 * t / D)
        ax.loglog(f, cb, color=c, ls=ls, lw=2, label=H(f't = {t * 1000:.0f} mm:  fc ≈ {fc:.0f} Hz'))
        ax.plot([fc], [343], 'o', color=c, ms=8)
    ax.axhline(343, color=ORANGE, lw=2, ls='-.'); ax.text(22, 360, H('מהירות הקול באוויר 343 m/s'), color=ORANGE, fontsize=11)
    ax.axvspan(44.19, 1414.3, color=LIGHT, alpha=0.6, zorder=0)
    ax.text(30, 60, H('מתחת ל-fc: גל הכפיפה איטי מהקול,\nקרינה יעילה רק מהקצוות והפינות'), fontsize=10, color=GRAY)
    ax.text(300, 700, H('מעל fc: גל כפיפה מהיר מהקול,\nהלוח קורן ביעילות'), fontsize=10, color=GRAY)
    ax.set_xlabel(H('תדר [Hz]')); ax.set_ylabel(H('מהירות גל כפיפה c_b [m/s]')); ax.legend(loc='lower right'); ax.set_ylim(40, 2500)
    ax.set_title(H('תדר ההתלכדות (coincidence) של לוח בטון'))
    save(fig, SUB, 'f07_coincidence')


# ---------------------------------------------------------------- F8 BEM + image method
def f08_bem():
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax in axs: ax.set_xlim(0, 6); ax.set_ylim(0, 5); ax.set_aspect('equal'); ax.axis('off')
    ax = axs[0]
    th = np.linspace(0, 2 * np.pi, 200); r = 1.0 + 0.25 * np.cos(3 * th) ; X = 3 + 1.2 * r * np.cos(th); Y = 2.6 + 0.9 * r * np.sin(th)
    ax.fill(X, Y, fc=LIGHT, ec=NAVY, lw=2); label(ax, 3, 2.6, 'גוף רוטט\nΓ: משטח BEM', 11)
    for a in np.linspace(0.3, 2 * np.pi, 9):
        i = int(a / (2 * np.pi) * 199); n = np.array([X[i] - 3, Y[i] - 2.6]); n /= np.linalg.norm(n)
        ax.annotate('', xy=(X[i] + 0.45 * n[0], Y[i] + 0.45 * n[1]), xytext=(X[i], Y[i]), arrowprops=dict(arrowstyle='-|>', color=ORANGE, lw=1.4))
    label(ax, 5.2, 4.6, 'n: נורמל החוצה', 10, color=ORANGE)
    for p in ((0.7, 4.3), (5.3, 1.0), (0.8, 0.8)): ax.plot(*p, 's', color=RED, ms=9)
    label(ax, 1.15, 4.0, 'נקודת שדה', 9.5, color=RED); label(ax, 0.8, 0.45, 'נקודת שדה', 9.5, color=RED)
    label(ax, 3, 0.45, 'בתחום החיצוני:  ∇²p + k²p = 0', 10.5); label(ax, 3, 0.05, 'על המשטח Γ:  ∂p/∂n = −iωρ₀vₙ', 10.5)
    label(ax, 3, 4.85, 'קרינה בחצי-מרחב חופשי', 12, bold=True)
    ax = axs[1]
    ax.plot([0, 6], [2.5, 2.5], color=GRAY, lw=2.2); hatch(ax, 0, 6, 2.5, 24, 0.14)
    ax.add_patch(Rectangle((2.2, 2.5), 1.0, 1.6, fc=LIGHT, ec=NAVY, lw=2)); label(ax, 2.7, 3.3, 'מקור', 10)
    ax.add_patch(Rectangle((2.2, 0.9), 1.0, 1.6, fc='white', ec=NAVY, lw=1.6, ls='--')); label(ax, 2.7, 1.7, 'דמות', 10, color=GRAY)
    ax.plot(0.7, 3.6, 's', color=RED, ms=9); ax.plot(0.7, 1.4, 's', color=RED, alpha=0.35, ms=9)
    ax.plot([0.7, 2.2], [3.6, 3.4], color=RED, lw=1, ls=':'); ax.plot([0.7, 2.2], [3.6, 1.9], color=RED, lw=1, ls=':')
    label(ax, 1.3, 4.3, 'מיקרופון', 9.5, color=RED); label(ax, 4.9, 3.4, 'קרקע קשיחה:\n∂p/∂n = 0', 10, color=GRAY)
    label(ax, 3, 4.85, 'שיטת הדמות: משטח + תמונת ראי = גוף סגור', 12, bold=True)
    save(fig, SUB, 'f08_bem')


# ---------------------------------------------------------------- F9 workflow
def f09_workflow():
    fig, ax = canvas(13, 6.2, 0.85)
    box(ax, 0.2, 5.0, 12.6, 0.8, 'lsdyna_dp.exe  i=main.k  ncpu=4  memory=400m  bem=1', fc=YEL, fs=11)
    ys = [3.5, 3.5, 3.5]; xs = [0.2, 4.5, 8.8]; w = 4.0
    titles = ['שלב 1: ערכים עצמיים', 'שלב 2: תגובה בתחום התדר', 'שלב 3: קרינה אקוסטית']
    kws = ['*CONTROL_IMPLICIT_GENERAL\n*CONTROL_IMPLICIT_EIGENVALUE', '*FREQUENCY_DOMAIN_SSD\n*DATABASE_FREQUENCY_BINARY_D3SSD', '*FREQUENCY_DOMAIN_ACOUSTIC_BEM\n*SET_SEGMENT  *SET_NODE_LIST']
    outs = ['eigout   d3eigv', 'd3ssd   bin_velfreq', 'Press_Pa   Press_dB   bepres']
    for x, t, k, o, c in zip(xs, titles, kws, outs, (LIGHT, MINT, PINK)):
        box(ax, x, 3.5, w, 1.1, t, fc=c, fs=11.5, bold=True)
        label(ax, x + w / 2, 2.75, k, 9, color=TEAL)
        box(ax, x, 1.2, w, 0.9, o, fc='white', fs=10)
        arrow(ax, (x + w / 2, 3.45), (x + w / 2, 2.15), color=GRAY)
        arrow(ax, (x + w / 2, 5.0), (x + w / 2, 4.65), color=GRAY)
    arrow(ax, (xs[0] + w + 0.05, 4.05), (xs[1] - 0.05, 4.05), lw=2); arrow(ax, (xs[1] + w + 0.05, 4.05), (xs[2] - 0.05, 4.05), lw=2)
    label(ax, 4.35, 4.3, 'מודים', 9, color=TEAL); label(ax, 8.65, 4.3, 'מהירות משטח', 9, color=TEAL)
    box(ax, 0.2, 0.05, 12.6, 0.8, 'פוסט-פרוססינג: LS-PrePost ו-Python (פסי אוקטבה, השוואה למודלים)', fc=YEL, fs=10.5)
    arrow(ax, (6.5, 1.15), (6.5, 0.9), color=GRAY)
    save(fig, SUB, 'f09_workflow')


# ---------------------------------------------------------------- F10 deck anatomy
def f10_anatomy():
    fig, ax = canvas(12.5, 9.6, 0.8)
    rows = [
        (7.7, 'main.k', ['*KEYWORD MEMORY=400m', '*TITLE', '*INCLUDE mesh.k  /  *INCLUDE loads.k'], YEL),
        (5.1, 'mesh.k  (גיאומטריה ומודל פיזי)', ['*NODE  *ELEMENT_SOLID  *PART  *SECTION_SOLID  *MAT_ELASTIC', '*MAT_SPRING_ELASTIC  *MAT_DAMPER_VISCOUS  *SECTION_DISCRETE  *ELEMENT_DISCRETE', '*SET_NODE_LIST  *SET_SEGMENT  *ELEMENT_SHELL  *BOUNDARY_SPC_SET'], LIGHT),
        (3.4, 'loads.k  (עומס)', ['*DEFINE_CURVE   (משרעת לכל צומת + עקום פאזה)'], MINT),
        (0.2, 'main.k  (בקרה ופתרנים)', ['*CONTROL_IMPLICIT_EIGENVALUE  *CONTROL_IMPLICIT_GENERAL  *CONTROL_IMPLICIT_SOLUTION', '*FREQUENCY_DOMAIN_SSD   (כרטיסים 1, 2, 3 ועומסים)', '*DATABASE_FREQUENCY_BINARY_D3SSD', '*FREQUENCY_DOMAIN_ACOUSTIC_BEM   (כרטיסים 1 עד 5)   |   *END'], PINK),
    ]
    for y, t, lines, c in rows:
        h = 0.5 + 0.42 * len(lines) + 0.25
        ax.add_patch(patches.FancyBboxPatch((0.2, y), 12.0, h, boxstyle='round,pad=0.02,rounding_size=0.1', fc=c, ec=NAVY, lw=1.3))
        label(ax, 6.2, y + h - 0.3, t, 11.5, bold=True)
        for i, l in enumerate(lines): label(ax, 6.2, y + h - 0.75 - 0.42 * i, l, 9.5, color=TEAL)
    save(fig, SUB, 'f10_anatomy')


# ---------------------------------------------------------------- F11 SSD cards
def f11_cards():
    fig, ax = canvas(12.6, 8.6, 0.8)
    cards = [
        ('כרטיס 1', ['MDMIN', 'MDMAX', 'FNMIN', 'FNMAX', 'RESTMD', 'RESTDP', 'LCFLAG', 'RELATV'], ['1', '60', '0.0', '0.0', '0', '0', '', '']),
        ('כרטיס 2', ['DAMPF', 'LCDAM', 'LCTYP', 'DMPMAS', 'DMPSTF', 'DMPFLG', '', ''], ['0.01', '0', '0', '0.0', '0.0', '', '', '']),
        ('כרטיס 3', ['', '', '', '', '', 'NOUT', 'NOTYP', 'NOVA'], ['', '', '', '', '', '1', '2', '0']),
        ('כרטיס 7 (לכל עומס)', ['NID', 'NTYP', 'DOF', 'VAD', 'LC1', 'LC2', 'LC3', 'VID'], ['848', '0', '1', '0', '1000', '200', '0', '0']),
    ]
    notes = ['מודים 1..60 (או תחום תדרים FNMIN/FNMAX)', 'ζ = 0.01 קבוע לכל המודים', 'צמתי פלט לצימוד אקוסטי', 'LC1 = עקום משרעת, LC2 = עקום פאזה [°]']
    y = 7.3
    for (nm, names, vals), note in zip(cards, notes):
        label(ax, 12.4, y + 0.85, nm, 11, ha='right', bold=True); label(ax, 0.2, y + 0.85, note, 9.5, ha='left', color=GRAY)
        for i in range(8):
            x = 0.2 + i * 1.55
            ax.add_patch(Rectangle((x, y + 0.35), 1.5, 0.35, fc=NAVY, ec='white')); ax.text(x + 0.75, y + 0.525, names[i], ha='center', va='center', color='white', fontsize=9.5, fontweight='bold')
            ax.add_patch(Rectangle((x, y), 1.5, 0.35, fc=YEL if vals[i] else 'white', ec=GRAY)); ax.text(x + 0.75, y + 0.175, vals[i], ha='center', va='center', color=NAVY, fontsize=10)
        y -= 1.75
    label(ax, 6.3, 0.15, 'כל שדה ברוחב 10 תווים (פורמט קבוע). ערך מיושר לימין בתוך השדה.', 10.5, color=TEAL)
    save(fig, SUB, 'f11_cards')


# ---------------------------------------------------------------- parse helpers
def read_nodes(mesh):
    nodes = {}; sec = None; shells = []; seg = False
    for ln in mesh.read_text().split('\n'):
        if ln.startswith('*'): sec = ln.strip(); continue
        if ln.startswith('$') or not ln.strip(): continue
        if sec == '*NODE': nodes[int(ln[:8])] = (float(ln[8:24]), float(ln[24:40]), float(ln[40:56]))
        elif sec == '*ELEMENT_SHELL': shells.append([int(ln[i:i + 8]) for i in range(0, 48, 8)])
    return nodes, shells


# ---------------------------------------------------------------- F12 loads on annulus
def f12_loads():
    D = ROOT / 'lsdyna' / 't10_bur'
    nodes, _ = read_nodes(D / 'mesh.k')
    lines = (D / 'loads.k').read_text().split('\n'); cur = {}
    for i, l in enumerate(lines):
        if l.startswith('*DEFINE_CURVE'): cur[int(lines[i + 2][:10])] = float(lines[i + 4][20:40])
    main = (D / 'main.k').read_text().split('\n'); L = []
    for ln in main:
        if re.match(r'^(\s*\d+){8}\s*$', ln) and len(ln) == 80 and 1000 <= int(ln[40:50]) < 2000:
            L.append((int(ln[:10]), cur[int(ln[40:50])]))
    P = np.array([nodes[n][1:] for n, _ in L]); Fv = np.array([v for _, v in L])
    fig, ax = plt.subplots(figsize=(5.8, 5.4))
    th = np.linspace(0, 2 * np.pi, 200)
    for r in (0.020, 0.025): ax.plot(0.5 + r * np.cos(th), 0.3 + r * np.sin(th), color=ORANGE, lw=1.8)
    s = ax.scatter(P[:, 0], P[:, 1], s=60 + 900 * Fv / Fv.max(), c=Fv, cmap='viridis', ec='k', lw=0.6, zorder=3)
    ax.set_aspect('equal'); ax.set_xlim(0.43, 0.57); ax.set_ylim(0.23, 0.37); ax.grid(True)
    ax.set_xlabel(H('y [m]')); ax.set_ylabel(H('z [m] (מקומי)')); cb = fig.colorbar(s, ax=ax, shrink=0.8); cb.set_label(H('כוח צירי בצומת [N]'))
    ax.set_title(H(f'חלוקת 1 N על {len(L)} צמתים; סכום = {Fv.sum():.6f} N'), fontsize=12)
    ax.text(0.57, 0.235, H('טבעת הקידוח: ri=20, ro=25 mm'), ha='right', fontsize=10, color=ORANGE)
    save(fig, SUB, 'f12_loads')


# ---------------------------------------------------------------- F13 curves
def f13_curves():
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.9))
    f = np.array([1, 2000.0])
    axs[0].plot(f, [1, 1], color=NAVY, lw=2.2, label=H('LC1: משרעת (המחקר: קבועה = 1)'))
    axs[0].plot(f, [0, 0], color=TEAL, lw=2.2, ls='--', label=H('LC2: פאזה [°] (המחקר: 0)'))
    axs[0].set_ylim(-0.3, 1.5); axs[0].legend(loc='center right'); axs[0].set_xlabel(H('תדר [Hz]')); axs[0].set_title(H('עקומות *DEFINE_CURVE של המחקר'))
    ff = np.logspace(0, np.log10(2000), 60); amp = np.where(ff < 100, 1.0, (100 / ff))
    axs[1].loglog(ff, amp, color=NAVY, lw=2.2, marker='o', ms=3, label=H('LC1: ספקטרום כוח לדוגמה, 1/f'))
    axs[1].set_xlabel(H('תדר [Hz]')); axs[1].set_title(H('אותו כרטיס עם ספקטרום תלוי תדר (איור המחשה)')); axs[1].legend(loc='lower left'); axs[1].set_ylabel(H('משרעת [N]'))
    axs[0].set_ylabel(H('ערך עקום'))
    save(fig, SUB, 'f13_curves')


# ---------------------------------------------------------------- F14 eigenfrequencies
def f14_eigen():
    import sys; sys.path.insert(0, str(ROOT / 'src')); from post import load_ccx
    eg = [float(l.split()[3]) for l in (EV / 'eigout').read_text().split('\n') if re.match(r'\s+\d+\s+[-+0-9.E]+\s+[-+0-9.E]+\s+[-+0-9.E]+\s+[-+0-9.E]+\s*$', l)]
    cc = load_ccx('t10_bur', '_dx0.05')['eig']
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.semilogy(np.arange(1, len(eg) + 1), eg, 'o', color=RED, ms=5, label=H('LS-DYNA, הרצה ראשונה (עם מעטפת BEM חופשית בסיבוב)'))
    ax.semilogy(np.arange(1, len(cc) + 1), cc, 's', color=NAVY, ms=5, label=H('CalculiX (ללא מעטפת)'))
    for fm in (40.0, 56.1, 96.5): ax.axhline(fm, color=GRAY, lw=0.5, ls=':')
    ax.axhspan(44.19, 1414.3, color=LIGHT, alpha=0.6, zorder=0); ax.axhline(158.6, color=RED, lw=0.8, ls='--')
    ax.annotate(H('60 המודים של LS-DYNA נגמרים ב-159 Hz'), (60, 158.6), (22, 600), arrowprops=dict(arrowstyle='->', color=RED), color=RED, fontsize=10.5)
    ax.annotate(H('מודים מדומים (סיבובי צמתים)'), (6, 40), (14, 11.5), arrowprops=dict(arrowstyle='->', color=GRAY), fontsize=10.5)
    ax.set_xlabel(H('מספר מוד')); ax.set_ylabel(H('תדר עצמי [Hz]')); ax.legend(loc='upper left', fontsize=9.5)
    ax.set_title(H('בדיקת השפיות של הערכים העצמיים'))
    save(fig, SUB, 'f14_eigen')


# ---------------------------------------------------------------- F15 Press_dB
def f15_press():
    cur = {}; pt = None
    for l in (EV / 'Press_dB').read_text().split('\n'):
        m = re.match(r'\s*pt\s+(\d+)', l)
        if m: pt = int(m.group(1)); cur[pt] = []; continue
        v = l.split()
        if pt and len(v) == 2:
            try: cur[pt].append((float(v[0]), float(v[1])))
            except ValueError: pass
    fig, ax = plt.subplots(figsize=(8.8, 4.6))
    for (k, nm, c, ls) in ((900001, 'F', NAVY, '-'), (900003, 'Rg', TEAL, '--'), (900004, 'S (במישור האמצע, אפס דיפול)', GRAY, ':')):
        a = np.array(cur[k]); ax.plot(a[:, 0], a[:, 1], color=c, ls=ls, lw=1.6, label=H(f'מיקרופון {nm}'))
    ax.set_xscale('log'); ax.set_xlabel(H('תדר [Hz]')); ax.set_ylabel(H('dB יחסית ל-20 µPa, לכוח 1 N')); ax.legend(fontsize=10)
    ax.set_title(H('הקובץ Press_dB שנוצר בהרצה (t=100 mm קבור, הרצה ראשונה)'))
    save(fig, SUB, 'f15_press')


# ---------------------------------------------------------------- F16 real mesh views
def f16_mesh():
    D = ROOT / 'lsdyna' / 't10_bur'
    nodes, shells = read_nodes(D / 'mesh.k')
    segs_xz = []; segs_yz = []
    for s in shells:
        pts = [nodes[n] for n in s[2:6]]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            segs_xz.append([(a[0], a[2]), (b[0], b[2])]); segs_yz.append([(a[1], a[2]), (b[1], b[2])])
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.9))
    mics = {'F': (-1.0, 0.5, 1.0), 'R': (1.1, 0.5, 1.0), 'Rg': (1.3, 0.5, 1.0)}
    for ax, segs, ix, ttl in ((axs[0], segs_xz, 0, 'מבט צד (x–z)'), (axs[1], segs_yz, 1, 'מבט חזית (y–z)')):
        ax.add_collection(LineCollection(segs, colors=NAVY, linewidths=0.6)); ax.axhline(0.0, color=ORANGE, lw=2)
        for nm, p in mics.items():
            ax.plot(p[ix], p[2], 's', color=RED, ms=7)
            if ix == 0: ax.text(p[0], p[2] + 0.06, nm, ha='center', color=RED, fontsize=10)
        ax.set_aspect('equal'); ax.set_title(H(ttl)); ax.grid(True)
    axs[0].set_xlim(-1.3, 1.6); axs[0].set_ylim(-0.6, 1.3); axs[1].set_xlim(-0.1, 1.1); axs[1].set_ylim(-0.6, 1.3)
    axs[0].set_xlabel(H('x [m]')); axs[0].set_ylabel(H('z [m]')); axs[1].set_xlabel(H('y [m]'))
    axs[0].text(-1.25, 0.05, H('קו הקרקע'), color=ORANGE, fontsize=10)
    fig.suptitle(H(f'פאנלי BEM (מעל קו הקרקע) ומיקרופונים, t=100 mm קבור: {len(shells)} פאנלים'), fontsize=12)
    save(fig, SUB, 'f16_mesh')


# ---------------------------------------------------------------- F17 troubleshooting flow
def f17_flow():
    fig, ax = canvas(12.6, 8.0, 0.8)
    rows = [
        ('קורא המילות המפתח מדווח שגיאה (KEY+…)', 'בדקו רוחב שדות (10 תווים), כרטיס חסר, סדר כרטיסים', 7.0),
        ('"Command BEM= is missing" (21275)', 'הוסיפו bem=1 לשורת ההרצה', 5.65),
        ('"Implicit is not supported in single precision" (60022)', 'הריצו lsdyna_dp.exe', 4.3),
        ('הרצה מסתיימת, אך תדרי eigout נמוכים ודחוסים', 'מודים מדומים: נעלו דרגות סיבוב של צמתי מעטפת', 2.95),
        ('Normal termination, אך הרמות לא סבירות', 'בדיקות שפיות: ×2 בעומס = +6.02 dB, מודים, נורמלים', 1.6),
    ]
    for t, a, y in rows:
        box(ax, 0.2, y, 6.2, 0.95, t, fc=PINK, fs=10)
        box(ax, 7.2, y, 5.2, 0.95, a, fc=MINT, fs=10); arrow(ax, (6.45, y + 0.47), (7.15, y + 0.47), lw=1.8)
    label(ax, 3.3, 0.9, 'תסמין בלוג', 11, bold=True); label(ax, 9.8, 0.9, 'פעולה', 11, bold=True)
    save(fig, SUB, 'f17_flow')


if __name__ == '__main__':
    for fn in (f01_chain, f02_octave, f03_sdof, f04_modes, f05_meshrule, f06_soil, f07_coincidence, f08_bem, f09_workflow, f10_anatomy, f11_cards,
               f12_loads, f13_curves, f14_eigen, f15_press, f16_mesh, f17_flow):
        try: fn()
        except Exception as e:
            import traceback; print('FAILED', fn.__name__, e); traceback.print_exc()
