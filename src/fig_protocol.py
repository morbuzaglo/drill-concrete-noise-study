"""Sensor-placement diagram for the physical validation protocol (front view of the slab and plan view)."""
from figstyle import *
from matplotlib.patches import Rectangle, Circle
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 5.2), gridspec_kw=dict(width_ratios=[1, 1.25]))
# front view (y-z), specimen 1.0 x 1.0 m
a1.add_patch(Rectangle((0, 0), 1, 1, fc='#E4E8ED', ec=NAVY, lw=1.6))
a1.add_patch(Rectangle((-0.15, -0.4), 1.3, 0.4, fc='#E9DCC3', ec='none', hatch='..'))
a1.axhline(0, color='#7A5A2A', lw=1.5)
a1.plot(0.5, 0.7, marker='o', ms=16, mfc='none', mec=RED, mew=2.2); a1.text(0.56, 0.78, H('חור קידוח'), color=RED, ha='left', fontsize=10)
for nm, (y, z) in {'A1': (0.65, 0.7), 'A3': (0.85, 1.0), 'A4': (0.2, 0.3), 'A5': (0.8, 0.3)}.items():
    a1.plot(y, z, 's', color=TEAL, ms=9); a1.text(y + 0.025, z - 0.075, nm, color=TEAL, fontsize=10, fontweight='bold')
for nm, (y, z) in {'H1': (0.5, 0.7), 'H2': (0.25, 0.7), 'H3': (0.5, 0.35)}.items():
    a1.plot(y, z, 'x', color=ORANGE, ms=11, mew=2.4); a1.text(y - 0.045, z - 0.1, nm, color=ORANGE, fontsize=10, fontweight='bold')
a1.set_xlim(-0.15, 1.15); a1.set_ylim(-0.4, 1.12); a1.set_aspect('equal'); a1.grid(False)
a1.set_title(H('מבט מהחזית: מדי תאוצה A ונקודות פטיש H')); a1.set_xlabel('y [m]'); a1.set_ylabel('z [m]')
a1.text(0.5, -0.2, H('קרקע; במקרה הקבור הבטון מוטמן מתחת לקו z = 0'), ha='center', fontsize=9, color='#5A3E10', bbox=dict(fc='white', ec='none', alpha=0.9))
# plan view (x-y)
t = 0.15
a2.add_patch(Rectangle((0, 0), t, 1.0, fc='#BFC5CC', ec=NAVY, lw=1.6))
a2.plot([0.05], [0.5], 'o', color=RED, ms=9); a2.annotate('', xy=(0.0, 0.5), xytext=(-0.5, 0.5), arrowprops=dict(arrowstyle='-|>', color=RED, lw=2))
a2.text(-0.5, 0.54, H('כיוון קידוח'), color=RED, fontsize=10)
for nm, (x, y) in {'F': (-1.0, 0.5), 'R': (t + 1.0, 0.5), 'S': (t / 2, 2.0)}.items():
    a2.plot(x, y, 'o', color=NAVY, ms=10); a2.text(x, y + 0.09, nm, ha='center', color=NAVY, fontsize=11, fontweight='bold')
a2.plot([1.3], [0.5], 'o', mfc='none', mec=GRAY, ms=10); a2.text(1.3, 0.62, 'Rg', ha='center', color=GRAY, fontsize=10)
a2.annotate('', xy=(0, 0.35), xytext=(-1.0, 0.35), arrowprops=dict(arrowstyle='<->', color=GRAY)); a2.text(-0.5, 0.28, '1.0 m', ha='center', fontsize=9, color=GRAY)
a2.annotate('', xy=(t, 0.35), xytext=(t + 1.0, 0.35), arrowprops=dict(arrowstyle='<->', color=GRAY)); a2.text(t + 0.5, 0.28, '1.0 m', ha='center', fontsize=9, color=GRAY)
a2.set_xlim(-1.3, 1.6); a2.set_ylim(-0.3, 2.3); a2.set_aspect('equal'); a2.grid(False)
a2.set_title(H('מבט מלמעלה: מיקרופונים בגובה 1.0 m מעל קו הקרקע')); a2.set_xlabel('x [m]'); a2.set_ylabel('y [m]')
fig.suptitle(H('מערך מדידה מוצע לתיקוף: אותה גיאומטריה, אותם מיקומי חיישנים בארבעת המקרים'), fontsize=13)
save(fig, 'main', 'protocol_layout')
