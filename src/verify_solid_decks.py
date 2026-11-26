"""Static (no solver) check of the solid-soil LS-DYNA decks: node references, element counts, load resultant, widths."""
import numpy as np, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parents[1]; D = ROOT / 'lsdyna_solid'; rows = []
for case in ['t10_exp', 't10_bur', 't20_exp', 't20_bur']:
    sec = None; nodes = {}; solids = []; shells = []; disc = []
    for ln in (D / case / 'mesh.k').read_text().splitlines():
        if ln.startswith('*'): sec = ln.strip(); continue
        if ln.startswith('$') or not ln.strip(): continue
        if sec == '*NODE': nodes[int(ln[:8])] = (float(ln[8:24]), float(ln[24:40]), float(ln[40:56]))
        elif sec == '*ELEMENT_SOLID': solids.append([int(ln[i:i + 8]) for i in range(0, 80, 8)])
        elif sec == '*ELEMENT_SHELL': shells.append([int(ln[i:i + 8]) for i in range(0, 48, 8)])
        elif sec == '*ELEMENT_DISCRETE': disc.append([int(ln[i:i + 8]) for i in range(0, 32, 8)])
    miss = sum(n not in nodes for e in solids for n in e[2:]) + sum(n not in nodes for e in shells for n in e[2:]) + sum(n not in nodes for e in disc for n in e[2:4])
    # signed volumes of the first solids (ordering check)
    neg = 0
    for e in solids[::50]:
        p = np.array([nodes[n] for n in e[2:]]); v = np.dot(np.cross(p[1] - p[0], p[3] - p[0]), p[4] - p[0])
        neg += v <= 0
    lines = (D / case / 'loads.k').read_text().splitlines(); cur = {}
    for i, l in enumerate(lines):
        if l.startswith('*DEFINE_CURVE'): cur[int(lines[i + 2][:10])] = float(lines[i + 4][20:40])
    Fx = 0.0; ssd = False
    for ln in (D / case / 'main.k').read_text().splitlines():
        if ln.startswith('*'): ssd = ln.startswith('*FREQUENCY_DOMAIN_SSD'); continue
        if ssd and len(ln) >= 80 and not ln.startswith('$') and ln[40:50].strip() and int(ln[40:50]) in cur and int(ln[20:30]) == 1: Fx += cur[int(ln[40:50])]
    wide = sum(len(l) > 80 for f in ('main.k', 'mesh.k', 'loads.k') for l in (D / case / f).read_text().splitlines() if not l.startswith('$'))
    rows.append((case, len(nodes), len(solids), len(shells), len(disc), miss, int(neg), Fx, wide))
    print(f'{case}: nodes {len(nodes)} solids {len(solids)} shells {len(shells)} dampers {len(disc)} missing-refs {miss} negative-volume(sampled) {int(neg)} Fx={Fx:.6f} N  over-wide lines {wide}')
(D / 'static_check.txt').write_text('\n'.join('%s nodes=%d solids=%d shells=%d dampers=%d missing=%d negvol=%d Fx=%.6f wide=%d' % r for r in rows) + '\n')
