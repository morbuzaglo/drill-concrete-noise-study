"""Additional SVG figures for the manual: drilling physics, modelling map, experiment roadmap, load paths. Run after make_manual_figs.py."""
import sys, pathlib, numpy as np
from make_manual_figs import *
from matplotlib.patches import Wedge, Arc

SUB = 'manual'


# ---------------------------------------------------------------- F18 drill kinematics + force signal
def f18_drill():
    fig = plt.figure(figsize=(12.5, 5.2))
    ax = fig.add_axes([0.0, 0.0, 0.34, 1.0]); ax.set_xlim(-1.6, 1.6); ax.set_ylim(-1.6, 1.7); ax.set_aspect('equal'); ax.axis('off')
    N = 6; ri, ro = 0.8, 1.0
    for k in range(N):
        a0 = 360 / N * k + 4; ax.add_patch(Wedge((0, 0), ro, a0, a0 + 360 / N - 20, width=ro - ri, fc=NAVY, ec='white', lw=1))
    ax.plot(0, 0, 'o', color=ORANGE, ms=8); ax.plot(0, 0, 'o', color='white', ms=3)
    ax.add_patch(Arc((0, 0), 1.45, 1.45, theta1=20, theta2=150, color=RED, lw=2.2)); ax.annotate('', xy=(-0.63, 0.37), xytext=(-0.55, 0.45), arrowprops=dict(arrowstyle='-|>', color=RED, lw=2.2))
    ax.text(0, 0.95 * 0.0 + 0.0, '', fontsize=1)
    ax.text(0, 0.0, H('Ω'), ha='center', va='center', fontsize=1)
    ax.text(-0.15, 0.55, H('Ω'), color=RED, fontsize=15, fontweight='bold', ha='center')
    for k in (0, 2):
        a = np.radians(360 / N * k + 24); p = np.array([0.9 * np.cos(a), 0.9 * np.sin(a)]); t = np.array([-np.sin(a), np.cos(a)])
        ax.annotate('', xy=p - 0.55 * t, xytext=p, arrowprops=dict(arrowstyle='-|>', color=TEAL, lw=2))
    ax.text(0.65, -1.25, H('כוח משיק על מקטע: F_t'), color=TEAL, fontsize=11, ha='center')
    ax.text(0, 1.45, H('מבט לאורך ציר הקידוח: N = 6 מקטעי יהלום'), ha='center', fontsize=12, color=NAVY, fontweight='bold')
    ax.text(0, -1.5, H('הדחיפה F_a בניצב לדף, אל תוך הבטון'), ha='center', fontsize=11, color=ORANGE)
    ax.add_patch(Circle((1.28, 1.15), 0.1, fc='none', ec=ORANGE, lw=2)); ax.plot(1.28, 1.15, '.', color=ORANGE, ms=6)
    ax2 = fig.add_axes([0.40, 0.58, 0.58, 0.34]); ax3 = fig.add_axes([0.40, 0.10, 0.58, 0.32])
    n = 1500.0; fr = n / 60; fs = N * fr; t = np.linspace(0, 0.16, 2000)
    rng = np.random.default_rng(3)
    F = 1 + 0.35 * np.cos(2 * np.pi * fs * t) + 0.18 * np.cos(2 * np.pi * 2 * fs * t + 0.7) + 0.07 * rng.standard_normal(t.size)
    ax2.plot(t * 1000, F, color=NAVY, lw=1.6); ax2.axhline(1, color=GRAY, lw=0.8, ls=':'); ax2.set_ylim(0.2, 1.9)
    ax2.set_xlabel(H('זמן [ms]')); ax2.set_ylabel(H('כוח צירי, יחסי')); ax2.set_title(H('אות כוח סכמטי: ממוצע + פעימות במעבר המקטעים'), fontsize=11.5)
    ax2.annotate('', xy=(1000 / fs * 1.0 + 6, 1.7), xytext=(6, 1.7), arrowprops=dict(arrowstyle='<->', color=ORANGE)); ax2.text(10, 1.78, H(f'מחזור {1000 / fs:.1f} ms'), color=ORANGE, fontsize=10)
    spec = np.abs(np.fft.rfft((F - F.mean()) * np.hanning(F.size))) / F.size * 4; fq = np.fft.rfftfreq(F.size, t[1] - t[0])
    ax3.plot(fq, spec, color=TEAL, lw=1.5); ax3.set_xlim(0, 700); ax3.set_xlabel(H('תדר [Hz]')); ax3.set_ylabel(H('משרעת, יחסית'))
    ax3.set_title(H('הספקטרום: קווים בכפולות של N · n/60'), fontsize=11.5)
    for j in (1, 2, 3): ax3.axvline(j * fs, color=GRAY, lw=0.6, ls=':'); ax3.text(j * fs + 5, spec.max() * 0.9, f'{j}·{fs:.0f}', fontsize=9, color=GRAY)
    save(fig, SUB, 'f18_drill')


# ---------------------------------------------------------------- F19 spectral ladder vs modes
def f19_ladder():
    from post import load_ccx
    eig = load_ccx('t10_exp', '_dx0.05')['eig']
    n, N = 1500.0, 6; fr = n / 60
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    ax.set_xscale('log'); ax.set_xlim(20, 1600); ax.set_ylim(0, 1.95)
    for e in eig[eig < 1600]: ax.axvline(e, color='#B8C2CF', lw=1.0, zorder=0)
    ax.axvline(180, color=ORANGE, lw=1.6, ls='--'); ax.text(185, 1.1, H('fc ≈ 180 Hz (100 mm)'), color=ORANGE, fontsize=10)
    def stems(freqs, amps, c, m, lab):
        ax.vlines(freqs, 0, amps, color=c, lw=2.4); ax.plot(freqs, amps, m, color=c, ms=7, label=H(lab))
    j = np.arange(1, 10); ax_f = j * N * fr; la = np.sort(np.concatenate([j * N * fr - fr, j * N * fr + fr])); im = fr * np.arange(1, 6)
    stems(im, 0.35 / np.arange(1, 6), RED, 'v', 'בלתי-איזון וסטייה: n/60 וכפולותיה (כוח רוחבי)')
    stems(ax_f[ax_f < 1600], 1.0 / j[ax_f < 1600] ** 0.7, NAVY, 'o', 'מעבר מקטעים: j·N·n/60 (כוח צירי ומומנט פיתול)')
    stems(la[la < 1600], 0.55 / np.repeat(j, 2)[:la.size][la < 1600] ** 0.7, TEAL, 's', 'מעבר מקטעים: (j·N ± 1)·n/60 (כוח רוחבי ומומנט כפיפה)')
    ax.plot([], [], color='#B8C2CF', lw=1.5, label=H('תדרים עצמיים של הלוח (CalculiX, t=100 mm חשוף)'))
    ax.set_yticks([]); ax.set_xlabel(H('תדר [Hz]')); ax.legend(loc='upper right', fontsize=9.5)
    ax.set_title(H('סולם הקווים הספקטרליים. דוגמה: n = 1500 סל"ד, N = 6 מקטעים. המשרעות סכמטיות'), fontsize=12)
    ax.set_xticks([25, 50, 100, 200, 400, 800, 1600]); ax.set_xticklabels(['25', '50', '100', '200', '400', '800', '1600'])
    save(fig, SUB, 'f19_ladder')


# ---------------------------------------------------------------- F20 rotating force
def f20_rotating():
    fig = plt.figure(figsize=(11.5, 4.2))
    ax = fig.add_axes([0.0, 0.0, 0.32, 1.0]); ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.5, 1.5); ax.set_aspect('equal'); ax.axis('off')
    th = np.linspace(0, 2 * np.pi, 200); ax.plot(np.cos(th), np.sin(th), color='#B8C2CF', lw=1.5, ls='--')
    ax.annotate('', xy=(0, 1.3), xytext=(0, -1.3), arrowprops=dict(arrowstyle='-|>', color=GRAY, lw=1)); ax.annotate('', xy=(1.3, 0), xytext=(-1.3, 0), arrowprops=dict(arrowstyle='-|>', color=GRAY, lw=1))
    a = np.radians(40); ax.annotate('', xy=(np.cos(a), np.sin(a)), xytext=(0, 0), arrowprops=dict(arrowstyle='-|>', color=RED, lw=2.6))
    ax.plot([np.cos(a), np.cos(a)], [0, np.sin(a)], color=TEAL, lw=1.6, ls=':'); ax.plot([0, np.cos(a)], [np.sin(a), np.sin(a)], color=NAVY, lw=1.6, ls=':')
    ax.text(1.35, -0.12, 'y', fontsize=12); ax.text(0.08, 1.35, 'z', fontsize=12)
    ax.text(0.5, 0.15, H('F'), color=RED, fontsize=14, fontweight='bold'); ax.text(1.02, 0.35, H('F_z'), color=TEAL, fontsize=11); ax.text(0.2, 0.9, H('F_y'), color=NAVY, fontsize=11)
    ax.text(0, -1.45, H('וקטור כוח מסתובב בקצב Ω = 2π·n/60'), ha='center', fontsize=11)
    ax2 = fig.add_axes([0.42, 0.18, 0.56, 0.68]); t = np.linspace(0, 2, 400)
    ax2.plot(t, np.cos(2 * np.pi * t), color=NAVY, lw=2, label=H('F_y = F·cos(Ωt)    LC1 = F ,  LC2 = 0°'))
    ax2.plot(t, np.cos(2 * np.pi * t - np.pi / 2), color=TEAL, lw=2, ls='--', label=H('F_z = F·sin(Ωt)    LC1 = F ,  LC2 = 90°'))
    ax2.set_xlabel(H('זמן, ביחידות של מחזור סיבוב')); ax2.set_ylim(-1.5, 1.9); ax2.legend(loc='upper right', fontsize=10); ax2.set_yticks([-1, 0, 1])
    ax2.set_title(H('שני כוחות הרמוניים בהפרש פאזה 90° מייצרים כוח מסתובב'), fontsize=12)
    save(fig, SUB, 'f20_rotating')


# ---------------------------------------------------------------- F21 load paths
def f21_loadpath():
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.6))
    ax = axs[0]; ax.set_xlim(-1.2, 1.4); ax.set_ylim(-0.1, 1.2); ax.set_aspect('equal'); ax.axis('off')
    z = np.linspace(0, 1, 100); w = 0.28 * np.sin(np.pi * z) ** 2
    ax.add_patch(Rectangle((0, 0), 0.12, 1, fc='none', ec=GRAY, lw=1.5, ls='--'))
    ax.fill_betweenx(z, w, w + 0.12, color=LIGHT, ec=NAVY, lw=2)
    ax.annotate('', xy=(0.05 + 0.3, 0.55), xytext=(-0.9, 0.55), arrowprops=dict(arrowstyle='-|>', color=ORANGE, lw=3))
    ax.text(-0.95, 0.65, H('דחיפה צירית F_a'), color=ORANGE, fontsize=12)
    ax.text(0.55, 0.15, H('הלוח מתכופף:\nתנועה בניצב למישור,\nקורן ביעילות'), color=NAVY, fontsize=11, ha='left')
    ax.text(0.0, 1.12, H('כוח צירי  ⟶  כפיפה'), fontsize=12.5, fontweight='bold', ha='center', color=NAVY)
    ax = axs[1]; ax.set_xlim(-1.3, 1.3); ax.set_ylim(-1.3, 1.45); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Rectangle((-1, -1), 2, 2, fc='none', ec=GRAY, lw=1.5, ls='--'))
    ang = np.radians(7); R = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]]); sq = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]) @ R.T
    ax.plot(*sq.T, color=NAVY, lw=2); ax.fill(*sq[:4].T, color=LIGHT, alpha=0.8)
    ax.add_patch(Arc((0, 0), 0.8, 0.8, theta1=20, theta2=300, color=RED, lw=3)); ax.annotate('', xy=(0.38, 0.12), xytext=(0.38, 0.0), arrowprops=dict(arrowstyle='-|>', color=RED, lw=3))
    ax.text(0, -1.22, H('מומנט פיתול T: הלוח מסתובב במישורו.\nכמעט אין תנועה בניצב למישור, ולכן קרינה חלשה'), ha='center', fontsize=10.5, color=NAVY)
    ax.text(0, 1.2, H('מומנט פיתול  ⟶  גזירה במישור'), fontsize=12.5, fontweight='bold', ha='center', color=NAVY)
    save(fig, SUB, 'f21_loadpath')


# ---------------------------------------------------------------- F22 modelling map
def f22_modelmap():
    fig, ax = canvas(13, 7.2, 0.8)
    box(ax, 4.3, 6.2, 4.4, 0.8, 'סוג העירור שרוצים למדל', fc=YEL, fs=12, bold=True)
    rows = [
        ('קווים הרמוניים\n(מעבר מקטעים, סיבוב, מנוע)', 'תגובה הרמונית. עומס יחידה\nועקומי משרעת ופאזה', '*FREQUENCY_DOMAIN_SSD', LIGHT),
        ('רחב-סרט אקראי\n(חיתוך גרגרים, חיכוך)', 'צפיפות ספקטרלית של הכוח\nPSD, הרמות מ-H · S', '*FREQUENCY_DOMAIN_' + chr(10) + 'RANDOM_VIBRATION', MINT),
        ('פגיעות\n(פטיש, פגיעה בזיון)', 'תגובה בזמן ו-FFT, או\nתמסורת SSD כפול ספקטרום הפגיעה', 'ניתוח implicit או explicit בזמן', PINK),
        ('אי-יציבות עצמית\n(chatter, stick-slip)', 'לא לינארי ותלוי תנאי חיתוך.\nלא נכנס ל-SSD', 'מגע ותנועה בזמן, מחוץ למחקר', '#EEE'),
    ]
    xs = [0.2, 3.5, 6.8, 10.1]
    for x, (a, b, c, col) in zip(xs, rows):
        arrow(ax, (6.5, 6.15), (x + 1.4, 5.35), color=GRAY)
        box(ax, x, 4.4, 2.8, 0.95, a, fc=col, fs=9.5, bold=True)
        arrow(ax, (x + 1.4, 4.35), (x + 1.4, 3.65), color=GRAY)
        box(ax, x, 2.45, 2.8, 1.2, b, fc='white', fs=9)
        arrow(ax, (x + 1.4, 2.4), (x + 1.4, 1.75), color=GRAY)
        box(ax, x, 0.9, 2.8, 0.85, c, fc='white', ec=TEAL, fs=8.3, tc=TEAL)
    label(ax, 6.5, 0.3, 'במחקר השתמשנו בענף הראשון. שלושת האחרים נשארים להרחבה.', 11, color=GRAY)
    save(fig, SUB, 'f22_modelmap')


# ---------------------------------------------------------------- F23 experiments roadmap
def f23_experiments():
    fig, ax = canvas(13, 9.0, 0.8)
    items = [
        ('E0', 'הגדרת הבעיה', 'מקדחה, כתר, סל"ד,\nבטון, גיאומטריה', YEL, 0.2, 6.3),
        ('E1', 'אפיון העירור', 'כוחות ומומנט,\nקווים ספקטרליים', YEL, 3.5, 6.3),
        ('E2', 'חומר הבטון', 'E, ρ, בלימה', LIGHT, 6.8, 6.3),
        ('E3', 'מבחן מודאלי', 'תדרים, צורות,\nבלימה מול eigout', LIGHT, 10.1, 6.3),
        ('E4', 'אדמה וקבורה', 'Vs, k, c\nמול עומק קבורה', LIGHT, 0.2, 3.5),
        ('E5', 'שרשרת כוח–לחץ', 'שייקר + מיקרופון:\nמדידת H_pF ישירה', MINT, 3.5, 3.5),
        ('E6', 'קרינה', 'סריקת רטט ועוצמה,\nיעילות קרינה', MINT, 6.8, 3.5),
        ('E7', 'קידוח מלא', 'מטריצת 2×2:\nחיזוי מול מדידה', PINK, 10.1, 3.5),
    ]
    for tag, t, sub, col, x, y in items:
        ax.add_patch(patches.FancyBboxPatch((x, y), 2.8, 1.9, boxstyle='round,pad=0.02,rounding_size=0.1', fc=col, ec=NAVY, lw=1.3))
        label(ax, x + 0.45, y + 1.5, tag, 13, bold=True, color=TEAL); label(ax, x + 1.75, y + 1.5, t, 10.5, bold=True)
        label(ax, x + 1.4, y + 0.65, sub, 9.5)
    for x in (3.0, 6.3, 9.6): arrow(ax, (x + 0.0, 7.25), (x + 0.5, 7.25), lw=1.8)
    arrow(ax, (11.5, 6.25), (1.6, 5.45), lw=1.4, color=GRAY)
    for x in (3.0, 6.3, 9.6): arrow(ax, (x, 4.45), (x + 0.5, 4.45), lw=1.8)
    box(ax, 0.2, 1.3, 12.7, 1.3, 'עדכון המודל לפי E2, E3, E4  ←  השוואת חיזוי ל-E5 ו-E6  ←  סבילות עוברת?  ←  חיזוי E7 לפני המדידה', fc='white', fs=10.5)
    arrow(ax, (1.6, 3.45), (1.6, 2.65), color=GRAY); arrow(ax, (4.9, 3.45), (4.9, 2.65), color=GRAY); arrow(ax, (8.2, 3.45), (8.2, 2.65), color=GRAY); arrow(ax, (11.5, 3.45), (11.5, 2.65), color=GRAY)
    label(ax, 6.5, 0.7, 'מ-E0 עד E4 זולים וקצרים. E5 הוא מבחן האמת של השרשרת. E7 נעשה אחרון.', 11, color=GRAY)
    label(ax, 6.5, 8.75, 'מסלול הניסויים', 13, bold=True)
    save(fig, SUB, 'f23_experiments')


# ---------------------------------------------------------------- F24 axial vs torque (real data, needs ccx *_c3)
def f24_axial_torque():
    from post import pressure
    from dsp import tf_band_level, EDGES
    import analyze as A
    f, p, r = pressure('t10_exp', '_c3', col=0); _, p1, _ = pressure('t10_exp', '_c3', col=1); _, p2, _ = pressure('t10_exp', '_c3', col=2)
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6))
    db = lambda x: 20 * np.log10(np.abs(x) / 20e-6)
    axs[0].plot(f, db(p[:, 0]), color=NAVY, lw=1.6, label=H('כוח צירי 1 N'))
    axs[0].plot(f, db(p1[:, 0]), color=RED, lw=1.6, ls='--', label=H('מומנט פיתול 1 N·m'))
    axs[0].set_xscale('log'); axs[0].set_xlabel(H('תדר [Hz]')); axs[0].set_ylabel(H('dB יחסית ל-20 µPa, מיקרופון F')); axs[0].legend()
    axs[0].set_title(H('לחץ ליחידת עומס, t=100 mm חשוף'), fontsize=12)
    B = A.BANDS; L0 = tf_band_level(f, p, B)[:, 0]; L1 = tf_band_level(f, p1, B)[:, 0]; L2 = tf_band_level(f, p2, B)[:, 0]
    x = np.arange(len(A.BL)); w = 0.27
    axs[1].bar(x - w, L0, w, color=NAVY, label=H('צירי, טבעת אחידה')); axs[1].bar(x, L2, w, color=TEAL, label=H('צירי, 6 מקטעים')); axs[1].bar(x + w, L1, w, color=RED, label=H('פיתול'))
    axs[1].set_xticks(x); axs[1].set_xticklabels(A.BL); axs[1].set_xlabel(H('פס אוקטבה, מרכז [Hz]')); axs[1].set_ylabel(H('dB יחסית ל-20 µPa')); axs[1].legend(fontsize=9.5)
    axs[1].set_title(H('רמות פס: ממוצע ריבועי'), fontsize=12)
    save(fig, SUB, 'f24_axial_torque')
    print('bands axial', np.round(L0, 1), 'torque', np.round(L1, 1), 'seg6', np.round(L2, 1))


if __name__ == '__main__':
    todo = [f18_drill, f19_ladder, f20_rotating, f21_loadpath, f22_modelmap, f23_experiments]
    if (ROOT / 'results' / 'ccx_t10_exp_c3.npz').exists(): todo.append(f24_axial_torque)
    for fn in todo:
        try: fn()
        except Exception as e:
            import traceback; print('FAILED', fn.__name__, e); traceback.print_exc()
