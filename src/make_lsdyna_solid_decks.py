"""LS-DYNA decks with the soil as a SOLID block (full model, both halves of the slab): main.k, mesh.k, loads.k, run.bat in lsdyna_solid/<case>/.
Soil: hex8 elements (same graded mesh as the open-source solid model), Lysmer viscous boundaries as discrete dampers to fixed ground nodes on the
outer faces of the block. Frequency domain: *FREQUENCY_DOMAIN_SSD_DIRECT (no modal basis: the soil block has thousands of modes and is heavily damped).
PREPARED, NOT RUN. The SSD_DIRECT card layout is assumed identical to *FREQUENCY_DOMAIN_SSD (not verified against the manual of the release)."""
import numpy as np, pathlib, json
import solidmesh as sm
from model import Case, mic_positions
ROOT = pathlib.Path(__file__).resolve().parents[1]; OUT = ROOT / 'lsdyna_solid'
CASES = {'t10_exp': (0.10, False), 't10_bur': (0.10, True), 't20_exp': (0.20, False), 't20_bur': (0.20, True)}
FMIN, FMAX, NFREQ = 44.19, 1414.3, 1000
ZETA = 0.01; RHO_S, VS, NU_S = 1800.0, 200.0, 0.3


def write_case(cid, t, bur):
    d = OUT / cid; d.mkdir(parents=True, exist_ok=True)
    m = sm.build(t, bur, half=False); xyz = m['xyz']; n = len(xyz)
    c = Case(t, bur, dx=0.05, dp=0.05, modal=False, bem=False); sl = c.slab; zb = sl.zb
    table = {tuple(np.round(q / 1e-7).astype(np.int64)): i + 1 for i, q in enumerate(xyz)}
    nodeid = lambda p: table[tuple(np.round(np.asarray(p, float) / 1e-7).astype(np.int64))]
    cp = VS * np.sqrt(2 * (1 - NU_S) / (1 - 2 * NU_S)); Es = 2 * RHO_S * VS ** 2 * (1 + NU_S)
    L = ['*KEYWORD', '*TITLE', f'Drill noise, concrete t={t*1000:.0f} mm, {"partially buried" if bur else "exposed"}, SOLID soil block (mesh)', '$ Units: m kg s N Pa. x = drilling axis, z = height above the soil line.',
         '*NODE', '$#   nid               x               y               z']
    L += ['%8d%16.8E%16.8E%16.8E' % (i + 1, *xyz[i]) for i in range(n)]
    order = [0, 1, 3, 2, 4, 5, 7, 6]
    L += ['*ELEMENT_SOLID', '$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8']
    for ci in range(len(m['cells'])):
        pid = 1 if m['kind'][ci] == 1 else 3
        L.append('%8d%8d' % (ci + 1, pid) + ''.join('%8d' % (m['cells'][ci][o] + 1) for o in order))
    # lysmer dampers on the outer faces: per node and direction, summed over the faces
    cn = {}
    for node, ax, area in m['absorb']:
        node = int(node); ax = int(ax)
        for comp in range(3): cn[(node, comp)] = cn.get((node, comp), 0.0) + (RHO_S * cp if comp == ax else RHO_S * VS) * area
    groups = {}
    for (node, comp), v in cn.items(): groups.setdefault('%.4E' % v, []).append((node, comp))
    gid = 1_000_000; eid = 5_000_000; pid = 10; mid = 10; parts, mats, elems, gn = [], [], [], []
    for val, items in groups.items():
        pid += 1; mid += 1
        mats.append(['*MAT_DAMPER_VISCOUS', '$#     mid        dc', '%10d%10.5G' % (mid, float(val))])
        parts.append(['*SECTION_DISCRETE', '$#   secid     dro      kd', '%10d%10d' % (pid, 0), '$#     cdl       tdl', '       0.0       0.0', '*PART', f'lysmer_{pid}', '%10d%10d%10d' % (pid, pid, mid)])
        elems.append(f'$ discrete dampers, part {pid}')
        for node, comp in items:
            gid += 1; eid += 1; p = xyz[node].copy(); p[comp] -= 1.0
            gn.append((gid, p)); elems.append('%8d%8d%8d%8d' % (eid, pid, gid, node + 1))
    L += ['*ELEMENT_DISCRETE', '$#   eid     pid      n1      n2   vid       s      pf  offset'] + elems
    L += ['*NODE'] + ['%8d%16.8E%16.8E%16.8E' % (g, *p) for g, p in gn]
    L += ['*SET_NODE_LIST', '1', '$ ground nodes of the absorbing boundary (fixed)'] + [''.join('%10d' % g for g, _ in gn[i:i + 8]) for i in range(0, len(gn), 8)]
    L += ['*BOUNDARY_SPC_SET', '$#    nsid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz', '         1         0         1         1         1         1         1         1']
    L += ['*MAT_ELASTIC', '$#     mid        ro         e        pr', '%10d%10.1f%10.3E%10.3f' % (1, sl.rho, sl.E, sl.nu), '%10d%10.1f%10.3E%10.3f' % (3, RHO_S, Es, NU_S),
          '*SECTION_SOLID', '$#   secid  elform', '%10d%10d' % (1, 18), '%10d%10d' % (3, 18),
          '*PART', 'concrete', '%10d%10d%10d' % (1, 1, 1), '*PART', 'soil_block', '%10d%10d%10d' % (3, 3, 3)]
    for mm in mats: L += mm
    for pp in parts: L += pp
    # BEM surface: shells on the exposed faces and the segment set; rotations of the surface nodes clamped (see the manual, chapter 18)
    cl = c.panels.corners
    L += ['*MAT_ELASTIC', '$ dummy material for the acoustic surface', '%10d%10.1f%10.3E%10.3f' % (2, 1.0, 1.0, 0.0),
          '*SECTION_SHELL', '$#   secid  elform    shrf     nip   propt', '%10d%10d' % (2, 2), '%10.4f%10.4f%10.4f%10.4f' % (0.001, 0.001, 0.001, 0.001),
          '*PART', 'BEM_exposed_surface', '%10d%10d%10d' % (2, 2, 2), '*ELEMENT_SHELL', '$#   eid     pid      n1      n2      n3      n4']
    L += ['%8d%8d' % (6_000_000 + i, 2) + ''.join('%8d' % nodeid(cl[i, k]) for k in range(4)) for i in range(len(cl))]
    L += ['*SET_SEGMENT', '$#     sid       da1       da2       da3       da4    solver', '%10d%10.3f%10.3f%10.3f%10.3f' % (1, 0, 0, 0, 0), '$#      n1        n2        n3        n4        a1        a2        a3        a4']
    L += [''.join('%10d' % nodeid(cl[i, k]) for k in range(4)) for i in range(len(cl))]
    sn = sorted({nodeid(cl[i, k]) for i in range(len(cl)) for k in range(4)})
    L += ['*SET_NODE_LIST', '$#     sid       da1       da2       da3       da4    solver', '%10d%10.3f%10.3f%10.3f%10.3f' % (3, 0, 0, 0, 0), '$#    nid1      nid2      nid3      nid4      nid5      nid6      nid7      nid8']
    L += [''.join('%10d' % v for v in sn[i:i + 8]) for i in range(0, len(sn), 8)]
    L += ['*BOUNDARY_SPC_SET', '$#    nsid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz', '%10d%10d%10d%10d%10d%10d%10d%10d' % (3, 0, 0, 0, 0, 1, 1, 1)]
    mics = mic_positions(t); mn = {}
    L += ['*NODE']
    for k, (nm, p) in enumerate(mics.items()):
        mn[nm] = 900001 + k; L.append('%8d%16.8E%16.8E%16.8E' % (900001 + k, *p))
    L += ['*SET_NODE_LIST', '2', '$ microphones: ' + ', '.join(f'{k}={v}' for k, v in mn.items()), ''.join('%10d' % v for v in mn.values()), '*END']
    (d / 'mesh.k').write_text(chr(10).join(L) + chr(10), encoding='ascii')
    # ---- loads: axial uniform annulus, one amplitude curve per loaded node
    F = c.F[:, 0]; LD = ['*KEYWORD', '*TITLE', 'unit axial drill load (1 N on the annulus): amplitude curve per loaded node']
    def curve(lcid, val):
        return ['*DEFINE_CURVE', '$#    lcid      sidr       sfa       sfo      offa      offo    dattyp', '%10d%10d%10.3f%10.3f%10.3f%10.3f%10d' % (lcid, 0, 0, 0, 0, 0, 0),
                '$#                a1                  o1', '%20.8E%20.8E' % (1.0, val), '%20.8E%20.8E' % (2000.0, val)]
    LD += curve(200, 0.0); cards = []
    ijk = lambda dof: divmod(dof // 3, 1)
    for i, dof in enumerate(np.nonzero(F)[0]):
        node = dof // 3; nx1, ny1 = sl.nx + 1, sl.ny + 1
        ii = node % nx1; jj = (node // nx1) % ny1; kk = node // (nx1 * ny1)
        p = (ii * sl.dx, jj * sl.dx, zb + kk * sl.dx)
        LD += curve(1000 + i, float(F[dof])); cards.append('%10d%10d%10d%10d%10d%10d%10d%10d' % (nodeid(p), 0, dof % 3 + 1, 0, 1000 + i, 200, 0, 0))
    LD.append('*END'); (d / 'loads.k').write_text(chr(10).join(LD) + chr(10), encoding='ascii')
    M = ['*KEYWORD MEMORY=2000m', '*TITLE', f'SSD-direct + acoustic BEM: concrete t={t*1000:.0f} mm, {"partially buried" if bur else "exposed"}, solid soil block',
         '$ PREPARED, NOT RUN. *FREQUENCY_DOMAIN_SSD_DIRECT cards are assumed to follow *FREQUENCY_DOMAIN_SSD: check against the manual of your release.',
         '$ Soil material damping (hysteretic eta = 0.05) is not reproduced; only the Lysmer dampers on the outer faces and DAMPF act.',
         '*INCLUDE', 'mesh.k', '*INCLUDE', 'loads.k',
         '*CONTROL_IMPLICIT_GENERAL', '$#  imflag       dt0    imform      nsbs       igs     cnstn      form    zero_v', '         1     0.000         0         0         0         0         0         0',
         '*CONTROL_IMPLICIT_SOLUTION', '$#  nsolvr    ilimit    maxref     dctol     ectol     rctol     lstol    abstol', '         1         0         0     0.000     0.000     0.000     0.000     0.000',
         '*FREQUENCY_DOMAIN_SSD_DIRECT', '$#   mdmin     mdmax     fnmin     fnmax    restmd    restdp    lcflag    relatv', '%10d%10d%10.3f%10.3f%10d%10d' % (1, 1, 0.0, 0.0, 0, 0),
         '$#   dampf     lcdam     lctyp    dmpmas    dmpstf    dmpflg', '%10.6f%10d%10d%10.3f%10.3f' % (ZETA, 0, 0, 0.0, 0.0),
         '$#                                                      nout     notyp      nova', '%60d%10d%10d' % (1, 2, 0),
         '$#     nid      ntyp       dof       vad       lc1       lc2       lc3       vid'] + cards + \
        ['*DATABASE_FREQUENCY_BINARY_D3SSD', '$#  binary', '         1', '$#    fmin      fmax     nfreq    fspace    lcfreq', '%10.4f%10.4f%10d%10d%10d' % (FMIN, FMAX, NFREQ, 0, 0),
         '*FREQUENCY_DOMAIN_ACOUSTIC_BEM', '$#      ro         c     fnmin     fnmax     nfreq    dt_out   t_start      pref',
         '%10.4f%10.4f%10.4f%10.4f%10d%10.6f%10.3f%10.3E' % (1.2, 343.0, FMIN, FMAX, NFREQ, 0.001, 0.0, 2.0E-5),
         '$#nsid_ext  type_ext  nsid_int  type_int   fft_win     trslt    ipfile    iunits', '         2         1         0         0         4         0         0         0',
         '$#  method     maxit  tol_iter       ndd    tol_lr  tol_fact     ibdim       npg', '         2      1000 1.0000E-6         8     0.000     0.000         0         0',
         '$#               nbc    restrt     iedge      noel     nfrup', '                   1                   1',
         '$#    ssid    sstype      norm  bem_type       lc1       lc2', '         1         2         0         0', '*END']
    (d / 'main.k').write_text(chr(10).join(M) + chr(10), encoding='ascii')
    BAT = ['@echo off', 'rem double precision, BEM enabled. The direct SSD needs the SMP solver (not MPP).',
           'if "%LSDYNA_EXE%"=="" set "LSDYNA_EXE=C:\\Program Files\\ANSYS Inc\\v252\\ansys\\bin\\winx64\\lsdyna_dp.exe"',
           '"%LSDYNA_EXE%" i=main.k ncpu=4 memory=2000m bem=1 > solver.log 2>&1']
    (d / 'run.bat').write_text('\r\n'.join(BAT) + '\r\n', encoding='ascii')
    return dict(case=cid, t_m=t, buried=bur, nodes=n, solid_cells=int(len(m['cells'])), dampers=len(gn), bem_shells=len(cl), load_nodes=len(cards), dofs=3 * n)


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    man = [write_case(cid, t, bur) for cid, (t, bur) in CASES.items()]
    (OUT / 'manifest.json').write_text(json.dumps(man, indent=2)); print(json.dumps(man, indent=1))
