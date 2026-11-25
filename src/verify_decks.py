"""Static (no-solver) consistency check of the prepared LS-DYNA decks: node references, element counts, load resultants."""
import numpy as np, pathlib, json, re
ROOT = pathlib.Path(__file__).resolve().parents[1]; D = ROOT / 'lsdyna'
rows = []
for case in ['t10_exp', 't10_bur', 't20_exp', 't20_bur']:
    txt = (D / case / 'mesh.k').read_text().splitlines()
    sec = None; nodes = {}; solids = []; shells = []; disc = []
    for ln in txt:
        if ln.startswith('*'): sec = ln.strip(); continue
        if ln.startswith('$') or not ln.strip(): continue
        if sec == '*NODE':
            nodes[int(ln[:8])] = (float(ln[8:24]), float(ln[24:40]), float(ln[40:56]))
        elif sec == '*ELEMENT_SOLID': solids.append([int(ln[i:i + 8]) for i in range(0, 80, 8)])
        elif sec == '*ELEMENT_SHELL': shells.append([int(ln[i:i + 8]) for i in range(0, 48, 8)])
        elif sec == '*ELEMENT_DISCRETE': disc.append([int(ln[i:i + 8]) for i in range(0, 32, 8)])
    miss = sum(n not in nodes for e in solids for n in e[2:]) + sum(n not in nodes for e in shells for n in e[2:]) + sum(n not in nodes for e in disc for n in e[2:4])
    # loads
    sec = None; F = {}
    for ln in (D / case / 'loads.k').read_text().splitlines():
        if ln.startswith('*') or ln.startswith('$*'): sec = ln.lstrip('$').strip(); continue
        m = re.match(r'^(\$?)\s*(\d+)\s+(\d)\s+(\d+)\s+([-+0-9.E]+)\s*$', ln)
        if m: F.setdefault(m.group(1) == '', []).append((int(m.group(2)), int(m.group(3)), float(m.group(5))))
    axial = F.get(True, [])
    Fx = sum(f for n, d, f in axial if d == 1)
    yc, zc = 0.5, 0.7 + (-0.4 if 'bur' in case else 0.0)
    Mx = sum((nodes[n][1] - yc) * f * (d == 3) - (nodes[n][2] - zc) * f * (d == 2) for n, d, f in axial)
    # vol of solids vs expected
    t = 0.1 if 't10' in case else 0.2
    rows.append((case, len(nodes), len(solids), len(shells), len(disc), miss, Fx, Mx))
    print(f'{case}: nodes {len(nodes)}  solids {len(solids)}  shells {len(shells)}  discrete {len(disc)}  missing-node refs {miss}  axial-load Fx={Fx:.6f} N  moment={Mx:.2e}')
(D / 'static_check.txt').write_text('\n'.join('%s nodes=%d solids=%d shells=%d discrete=%d missing=%d Fx=%.6f Mx=%.2e' % r for r in rows) + '\n')
