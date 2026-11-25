"""Figure: four geometries in the common coordinate system (side view x-z)."""
import numpy as np
from figstyle import *
from matplotlib.patches import Rectangle, FancyArrowPatch
cases = [(0.1, False, 'חשוף, t = 100 mm'), (0.1, True, 'קבור חלקית, t = 100 mm'), (0.2, False, 'חשוף, t = 200 mm'), (0.2, True, 'קבור חלקית, t = 200 mm')]
fig, axs = plt.subplots(2, 2, figsize=(11, 8.2), sharex=True, sharey=True)
for ax, (t, bur, ttl) in zip(axs.ravel(), cases):
    zb = -0.4 if bur else 0.0
    ax.add_patch(Rectangle((-1.5, -0.7), 3.4, 0.7, fc='#E9DCC3', ec='none', hatch='..', alpha=0.9, zorder=0))
    ax.axhline(0, color='#7A5A2A', lw=1.6, zorder=1)
    ax.add_patch(Rectangle((0, zb), t, 1.0, fc='#BFC5CC', ec=NAVY, lw=1.5, zorder=3))
    zd = 0.7 + zb
    ax.add_patch(FancyArrowPatch((-0.45, zd), (0.0, zd), arrowstyle='-|>', mutation_scale=16, color=RED, lw=2.4, zorder=5))
    ax.plot([0, 0.05], [zd, zd], color=RED, lw=5, zorder=6, solid_capstyle='butt')
    ax.plot([-0.6, t + 0.6], [zd, zd], color=RED, lw=0.8, ls='-.', zorder=2)
    ax.text(-1.45, zd + 0.05, H('ציר קידוח'), color=RED, fontsize=10, ha='left')
    mics = {'F': (-1.0, 1.0), 'R': (t + 1.0, 1.0), 'Rg': (1.3, 1.0)}
    for nm, (x, z) in mics.items():
        ax.plot(x, z, 'o', color=TEAL, ms=8, zorder=6); ax.text(x, z + (0.07 if nm != 'Rg' else -0.17), nm, color=TEAL, ha='center', fontsize=11, fontweight='bold')
    ax.annotate('', xy=(t, 1.0 - 0.05 + 0.0), xytext=(t + 1.0, 1.0 - 0.05), arrowprops=dict(arrowstyle='<->', color=GRAY, lw=1.0))
    ax.text(t + 0.5, 0.88, '1.0 m', ha='center', fontsize=9, color=GRAY)
    # supports
    for xs in np.linspace(0.0, t, 4):
        ax.plot([xs, xs], [zb - 0.0, zb - 0.07], color=ORANGE, lw=2)
    ax.text(-1.45, zb - 0.12, H('תמיכה: קפיץ + בולם'), fontsize=9, color=ORANGE, ha='left')
    ax.text(1.85, -0.62, H('קרקע'), fontsize=11, color='#7A5A2A', ha='right')
    ax.text(1.85, 0.03, H('קו הקרקע z = 0'), fontsize=9, color='#7A5A2A', ha='right', va='bottom')
    ax.set_title(H(ttl)); ax.set_xlim(-1.5, 1.9); ax.set_ylim(-0.7, 1.35); ax.set_aspect('equal'); ax.grid(False)
for ax in axs[1]: ax.set_xlabel('x [m]')
for ax in axs[:, 0]: ax.set_ylabel(H('z [m] מעל קו הקרקע'))
fig.suptitle(H('ארבע הגיאומטריות במערכת צירים משותפת (מבט צד, y = 0.5 m)'), color=NAVY, fontsize=14)
save(fig, 'main', 'geometry_2x2')
