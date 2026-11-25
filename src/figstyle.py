"""Shared figure style: Hebrew bidi labels, navy/teal palette, SVG output (text outlined to paths)."""
import pathlib, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import patches

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIG = ROOT / 'figures'
pass

NAVY, TEAL, GRAY, ORANGE, RED, LIGHT = '#12264A', '#0F8B8D', '#6B7280', '#D9822B', '#B8312F', '#E6EEF5'
CYCLE = [NAVY, TEAL, ORANGE, RED, GRAY, '#7A5AA6']
LS = ['-', '--', '-.', ':', (0, (5, 1)), (0, (3, 1, 1, 1))]   # distinguishable in grayscale

plt.rcParams.update({
    'svg.fonttype': 'path', 'mathtext.fontset': 'dejavusans', 'axes.unicode_minus': False,
    'font.family': ['David', 'Arial', 'DejaVu Sans'], 'font.size': 13,
    'axes.titlesize': 14, 'axes.labelsize': 13, 'legend.fontsize': 11.5,
    'axes.edgecolor': GRAY, 'axes.labelcolor': NAVY, 'axes.titlecolor': NAVY,
    'xtick.color': NAVY, 'ytick.color': NAVY, 'text.color': NAVY,
    'axes.grid': True, 'grid.color': '#D5DBE3', 'grid.linewidth': 0.6,
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.dpi': 100, 'savefig.dpi': 200,
    'axes.prop_cycle': matplotlib.cycler(color=CYCLE),
})


import re as _re
_HEB = _re.compile('[֐-׿]')
_RLM = '‏'


_LRI, _PDI = '⁦', '⁩'
_ALNUM = _re.compile('[A-Za-z0-9Ͱ-Ͽ]')
_NONHEB = _re.compile('[^֐-׿\n]+')


def _wrap_seg(m):
    seg = m.group(0)
    core = seg.strip(' :,;.!?-–—־')
    if not _ALNUM.search(core): return seg
    i = seg.index(core); pre, post = seg[:i], seg[i + len(core):]
    for o, c in (('(', ')'), ('[', ']')):
        while core.startswith(o) and core.count(o) > core.count(c): pre += o; core = core[1:]
        while core.endswith(c) and core.count(c) > core.count(o): post = c + post; core = core[:-1]
        while core.endswith(o) and core.count(o) > core.count(c): post = o + post; core = core[:-1]
        while core.startswith(c) and core.count(c) > core.count(o): pre += c; core = core[1:]
    if not _ALNUM.search(core): return seg
    return pre + _LRI + core + _PDI + post


def H(s):
    """Right-to-left text for matplotlib (>= 3.11 runs the Unicode bidi algorithm itself). A string that contains Hebrew
    gets an RTL base direction (RLM marks) and every Latin/number/formula run is isolated (LRI..PDI), so that, for example,
    '20 lg d + 11 (ISO 9613-2)' stays one left-to-right unit inside a right-to-left sentence. Applied to every Text through
    set_text, so titles, labels, ticks, legends and annotations are all handled."""
    if isinstance(s, str):
        s = s.replace(_RLM, '').replace(_LRI, '').replace(_PDI, '')
        if _HEB.search(s) and '$' not in s:
            return _RLM + _NONHEB.sub(_wrap_seg, s) + _RLM
    return s


from matplotlib import text as _mtext
_orig_set_text = _mtext.Text.set_text


def _set_text(self, s):
    _orig_set_text(self, H(s) if isinstance(s, str) else s)


_mtext.Text.set_text = _set_text


AUDIT = []
import numpy as np
from matplotlib import ticker as _ticker
from matplotlib.legend import Legend as _Legend

_LOCS = ['upper right', 'upper left', 'lower left', 'lower right', 'center right', 'center left', 'lower center', 'upper center', 'center']


def _log_fmt(v, _):
    if v <= 0: return ''
    e = np.log10(v)
    if abs(e - round(e)) < 1e-9:
        n = int(round(e))
        return f'$10^{{{n}}}$' if n not in (0, 1) else ('1' if n == 0 else '10')
    return f'{v:g}'


def _fix_axes(fig):
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            if axis.get_scale() == 'log':
                axis.set_major_formatter(_ticker.FuncFormatter(_log_fmt))
                axis.set_minor_formatter(_ticker.NullFormatter())


def _data_points(ax, r):
    """Display-space sample points of every line and the rectangles (bars, patches) of an axes."""
    pts = []
    for ln in ax.get_lines():
        if not ln.get_visible(): continue
        xy = ln.get_xydata()
        if len(xy) < 2: continue
        xy = np.asarray(xy, float); xy = xy[np.isfinite(xy).all(axis=1)]
        if ax.get_xscale() == 'log': xy = xy[xy[:, 0] > 0]
        if ax.get_yscale() == 'log': xy = xy[xy[:, 1] > 0]
        # densify
        if len(xy) > 1:
            t = np.linspace(0, 1, 6 * len(xy)); idx = np.linspace(0, len(xy) - 1, len(t))
            xy = np.column_stack([np.interp(idx, np.arange(len(xy)), xy[:, 0]), np.interp(idx, np.arange(len(xy)), xy[:, 1])])
        pts.append(ax.transData.transform(xy))
    return np.vstack(pts) if pts else np.zeros((0, 2))


def _rects(ax):
    out = []
    for p in ax.patches:
        try:
            if p.get_visible() and p.__class__.__name__ == 'Rectangle' and p.get_alpha() in (None, 1) and p.get_height() != 0:
                out.append(p.get_window_extent())
        except Exception: pass
    return out


def _legend_cost(ax, bb, pts, rects, texts=()):
    n = 0
    for tb in texts:
        ox = min(bb.x1, tb.x1) - max(bb.x0, tb.x0); oy = min(bb.y1, tb.y1) - max(bb.y0, tb.y0)
        if ox > 0 and oy > 0: n += 30
    n += int(((pts[:, 0] > bb.x0) & (pts[:, 0] < bb.x1) & (pts[:, 1] > bb.y0) & (pts[:, 1] < bb.y1)).sum()) if len(pts) else 0
    for rb in rects:
        ox = min(bb.x1, rb.x1) - max(bb.x0, rb.x0); oy = min(bb.y1, rb.y1) - max(bb.y0, rb.y0)
        if ox > 0 and oy > 0: n += 20
    return n


def place_legends(fig):
    """Move every legend to the corner where it covers no data; if no corner is free put it outside the axes."""
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    for ax in fig.axes:
        lg = ax.get_legend()
        if lg is None or getattr(lg, '_pinned', False): continue
        pts = _data_points(ax, r); rects = _rects(ax)
        best = None
        for loc in _LOCS:
            lg._loc = _Legend.codes[loc] if hasattr(_Legend, 'codes') else lg._loc
            lg.set_loc(loc) if hasattr(lg, 'set_loc') else None
            fig.canvas.draw()
            c = _legend_cost(ax, lg.get_window_extent(r), pts, rects, [t.get_window_extent(r) for t in ax.texts if t.get_text().strip()])
            if best is None or c < best[0]: best = (c, loc)
            if c == 0: break
        lg.set_loc(best[1])
        if best[0] > 0:
            fig.canvas.draw()
            ab = ax.get_window_extent(r)
            low = min([ab.y0] + [t.get_window_extent(r).y0 for t in ax.xaxis.get_ticklabels() if t.get_visible() and t.get_text()]
                      + ([ax.xaxis.label.get_window_extent(r).y0] if ax.xaxis.label.get_text() else []))
            y_axes = (low - ab.y0) / ab.height - 0.04
            lg.set_loc('upper center'); lg.set_bbox_to_anchor((0.5, y_axes), transform=ax.transAxes)


def audit(fig, name):
    """Report overlaps: text over text, text over a data line/bar. Tick labels that lie outside the view are ignored."""
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    items = []
    skip = set()
    for ax in fig.axes:
        for axis, lim in ((ax.xaxis, ax.get_xlim()), (ax.yaxis, ax.get_ylim())):
            lo, hi = min(lim), max(lim)
            for t, loc in zip(axis.get_majorticklabels(), axis.get_majorticklocs()):
                if not (lo - 1e-9 <= loc <= hi + 1e-9): skip.add(id(t))
            for t, loc in zip(axis.get_minorticklabels(), axis.get_minorticklocs()):
                skip.add(id(t))
    for t in fig.findobj(_mtext.Text):
        if id(t) in skip or not t.get_visible() or not t.get_text().strip(): continue
        try: bb = t.get_window_extent(r)
        except Exception: continue
        if bb.width < 1 or bb.height < 1: continue
        items.append((t, t.get_text().replace(chr(8207), '')[:26], bb))
    out = []
    for i in range(len(items)):
        a = items[i][2]
        for j in range(i + 1, len(items)):
            b = items[j][2]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0); oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ox > 2 and oy > 2 and ox * oy > 0.10 * min(a.width * a.height, b.width * b.height):
                out.append(f'text/text: {items[i][1]!r} x {items[j][1]!r}')
    # text over data (annotations and legends) per axes
    for ax in fig.axes:
        if ax.name == 'polar' or hasattr(ax, 'zaxis'): continue
        pts = _data_points(ax, r); rects = _rects(ax)
        cands = list(ax.texts) + ([ax.get_legend()] if ax.get_legend() else [])
        for t in cands:
            if not t.get_visible(): continue
            if hasattr(t, 'get_text') and not t.get_text().strip(): continue
            bb = t.get_window_extent(r)
            n = int(((pts[:, 0] > bb.x0) & (pts[:, 0] < bb.x1) & (pts[:, 1] > bb.y0) & (pts[:, 1] < bb.y1)).sum()) if len(pts) else 0
            hit = any(min(bb.x1, rb.x1) - max(bb.x0, rb.x0) > 2 and min(bb.y1, rb.y1) - max(bb.y0, rb.y0) > 2 for rb in rects)
            if n > 2 or hit:
                label = 'legend' if isinstance(t, _Legend) else t.get_text().replace(chr(8207), '')[:24]
                out.append(f'over data: {label!r} (points {n}, bar {hit})')
    for o in out: print('   AUDIT', name, o)
    AUDIT.extend((name, o) for o in out)


def save(fig, sub, name):
    _fix_axes(fig)
    place_legends(fig)
    audit(fig, name)
    d = FIG / sub
    d.mkdir(parents=True, exist_ok=True)
    fig.savefig(d / f'{name}.svg', format='svg', bbox_inches='tight', facecolor='white')
    # PNG fallback is required by the OOXML SVG-embedding scheme (a:blip + asvg:svgBlip);
    # Word shows the SVG, the PNG is used only by consumers that do not support SVG.
    fig.savefig(d / f'{name}.fallback.png', format='png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('saved', sub, name)


def box(ax, x, y, w, h, text, fc=LIGHT, ec=NAVY, fs=10, bold=False, tc=None):
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.08',
                                        fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2, H(text), ha='center', va='center', fontsize=fs,
            color=tc or NAVY, fontweight='bold' if bold else 'normal', linespacing=1.3)


def arrow(ax, p, q, color=NAVY, lw=1.4, style='-|>', ls='-'):
    ax.annotate('', xy=q, xytext=p, arrowprops=dict(arrowstyle=style, color=color, lw=lw, ls=ls,
                                                   shrinkA=0, shrinkB=0, mutation_scale=12))
