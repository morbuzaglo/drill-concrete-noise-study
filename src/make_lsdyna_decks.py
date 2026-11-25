"""Generate LS-DYNA input decks for the four cases (PREPARED ONLY - not run: no usable license on this machine).
Same model as the open-source study: concrete hex mesh (dx=0.05 m, ELFORM 18 = incompatible-mode 8-node solid), soil as
discrete spring + damper elements to fixed ground nodes (same per-node values as CalculiX SPRINGA/DASHPOTA), unit axial
force (and unit torque) on the annular drill face, *FREQUENCY_DOMAIN_SSD for the structure and
*FREQUENCY_DOMAIN_ACOUSTIC_BEM for radiation.  Units: m, kg, s, N, Pa."""
import numpy as np, pathlib, json
from model import Case, mic_positions, DRILL
from fem import soil_props
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'lsdyna'
CASES = {'t10_exp': (0.10, False), 't10_bur': (0.10, True), 't20_exp': (0.20, False), 't20_bur': (0.20, True)}
FMIN, FMAX, NFREQ = 44.19, 1414.3, 1000          # study band (full octaves 63 ... 1000 Hz), ~1.4 Hz linear step
NMODES = 60; ZETA = 0.01


def fx(v):
    return '%.9E' % v


def write_case(cid, t, bur):
    d = OUT / cid; d.mkdir(parents=True, exist_ok=True)
    c = Case(t, bur, dx=0.05, dp=0.05, soil=soil_props(eta=0.0), modal=False, bem=False)
    slab = c.slab; xyz = slab.node_xyz()
    # ---------------- mesh.k : nodes, solids, discrete soil, BEM shells, field points
    L = ['*KEYWORD', '*TITLE', f'Drill structure-borne noise, concrete t={t*1000:.0f} mm, {"partially buried" if bur else "exposed"} (mesh)', '$ Units: m kg s N Pa. Global x = drilling axis, z = height above soil line.',
         f'$ Slab local z = global z + {-0.4 if bur else 0.0:.1f}. Node ids 1..{slab.nn} = concrete; ground nodes 100000+; field points 900001+.',
         '*NODE', '$#   nid               x               y               z']
    zb = c.slab.zb
    L += ['%8d%16.8E%16.8E%16.8E' % (i + 1, xyz[i, 0], xyz[i, 1], xyz[i, 2] + zb) for i in range(slab.nn)]
    L += ['*ELEMENT_SOLID', '$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8']
    order = [0, 1, 3, 2, 4, 5, 7, 6]
    L += ['%8d%8d' % (e + 1, 1) + ''.join('%8d' % (slab.conn[e, o] + 1) for o in order) for e in range(len(slab.conn))]
    # soil: spring/damper elements from the same diagonal matrices as the CalculiX model
    Ak, Ac = slab.soil_matrices(c.soil, c.faces); ak = Ak.diagonal(); ac = Ac.diagonal()
    gid = 100000; eid = 1_000_000; pid = 10; mid = 10
    parts, mats, elems, gn = [], [], [], []
    for kind in ('k', 'c'):
        arr = ak if kind == 'k' else ac
        groups = {}
        for dof in np.nonzero(arr)[0]:
            node, comp = divmod(int(dof), 3); groups.setdefault('%.6E' % arr[dof], []).append((node, comp))
        for val, items in groups.items():
            pid += 1; mid += 1
            if kind == 'k':
                mats.append(['*MAT_SPRING_ELASTIC', '$#     mid       k   (comma-separated)', '%d,%s' % (mid, val)])
            else:
                mats.append(['*MAT_DAMPER_VISCOUS', '$#     mid      dc   (comma-separated)', '%d,%s' % (mid, val)])
            parts.append(['*SECTION_DISCRETE', '$#   secid     dro      kd', '%10d%10d' % (pid, 0), '*PART', f'soil_{kind}_{pid}', '%10d%10d%10d' % (pid, pid, mid)])
            elems.append(f'$ discrete elements, part {pid}')
            for node, comp in items:
                gid += 1; eid += 1; p = xyz[node].copy(); p[2] += zb; p[comp] -= 1.0
                gn.append((gid, p)); elems.append('%8d%8d%8d%8d' % (eid, pid, gid, node + 1))
    # *SECTION_DISCRETE and *MAT already sequenced inside parts/mats lists
    L += ['*ELEMENT_DISCRETE', '$#   eid     pid      n1      n2   vid       s      pf  offset'] + [e for e in elems]
    L += ['*NODE'] + ['%8d%16.8E%16.8E%16.8E' % (g, *p) for g, p in gn]
    L += ['*SET_NODE_LIST', '1', '$ ground nodes (fixed)'] + [''.join('%10d' % g for g, _ in gn[i:i + 8]) for i in range(0, len(gn), 8)]
    L += ['*BOUNDARY_SPC_SET', '$#    nsid     cid   dofx   dofy   dofz  dofrx  dofry  dofrz', '         1         0         1         1         1         1         1         1']
    # concrete
    L += ['*MAT_ELASTIC', '$#     mid        ro         e        pr', '%10d%10.1f%10.3E%10.3f' % (1, slab.rho, slab.E, slab.nu),
          '*SECTION_SOLID', '$#   secid  elform', '%10d%10d' % (1, 18), '*PART', 'concrete', '%10d%10d%10d' % (1, 1, 1)]
    for m in mats: L += m
    for p in parts: L += p
    # BEM shells on the exposed faces (corner nodes of the 0.05 m panels are structural nodes)
    cl = c.panels.corners.copy(); cl[..., 2] -= zb
    nid = lambda q: int(slab.nid(*np.rint(q / slab.dx).astype(int))) + 1
    L += ['*MAT_ELASTIC', '$ dummy material for the acoustic surface (no stiffness contribution intended)', '%10d%10.1f%10.3E%10.3f' % (2, 1.0, 1.0, 0.0),
          '*SECTION_SHELL', '$#   secid  elform    shrf     nip   propt', '%10d%10d' % (2, 2), '%10.4f%10.4f%10.4f%10.4f' % (0.001, 0.001, 0.001, 0.001),
          '*PART', 'BEM_exposed_surface', '%10d%10d%10d' % (2, 2, 2), '*ELEMENT_SHELL', '$#   eid     pid      n1      n2      n3      n4']
    L += ['%8d%8d' % (5_000_000 + i, 2) + ''.join('%8d' % nid(cl[i, k]) for k in range(4)) for i in range(len(cl))]
    mics = mic_positions(t); mn = {}
    L += ['*NODE']
    for k, (nm, p) in enumerate(mics.items()):
        mn[nm] = 900001 + k; L.append('%8d%16.8E%16.8E%16.8E' % (900001 + k, *p))
    L += ['*SET_NODE_LIST', '2', '$ microphones: ' + ', '.join(f'{k}={v}' for k, v in mn.items()), ''.join('%10d' % v for v in mn.values())]
    L += ['*END']
    (d / 'mesh.k').write_text('\n'.join(L) + '\n', encoding='ascii')
    # ---------------- loads.k : unit loads from the same nodal vectors as the open-source model
    F = c.F; names = ['axial_uniform_1N', 'torque_uniform_1Nm', 'axial_seg6_0deg_1N', 'axial_seg6_30deg_1N']
    LD = ['*KEYWORD', '*TITLE', 'unit drill loads (axial 1 N distributed on the annulus; torque 1 N m)', '*DEFINE_CURVE', '$#    lcid', '         1', '$                 a1                  o1',
          '                 0.0                 1.0', '           1.0E+06                 1.0']
    for k, nm in enumerate(names):
        LD.append(f'$ ---- load case {k + 1}: {nm}  (switch on by including this block in main.k via the *INCLUDE lines)')
        LD.append('*LOAD_NODE_POINT' if k == 0 else '$*LOAD_NODE_POINT')
        LD.append('$#     nid     dof    lcid      sf')
        for dof in np.nonzero(F[:, k])[0]:
            LD.append(('' if k == 0 else '$') + '%10d%8d%8d%16.9E' % (dof // 3 + 1, dof % 3 + 1, 1, F[dof, k]))
    LD.append('*END')
    (d / 'loads.k').write_text('\n'.join(LD) + '\n', encoding='ascii')
    # ---------------- main.k
    M = ['*KEYWORD MEMORY=400m', '*TITLE', f'LS-DYNA SSD + acoustic BEM: drill on concrete t={t*1000:.0f} mm, {"partially buried" if bur else "exposed"}  [PREPARED, NOT RUN]',
         '$ ==================================================================================',
         '$ STATUS: not executed in this project (no usable LS-DYNA license). The mesh/material/discrete/load cards follow standard',
         '$ keyword syntax. The *FREQUENCY_DOMAIN cards below follow the R13/R14 manual layout as documented in the comments; verify',
         '$ the field positions against the manual of YOUR release (Example 8.4: SSD coupled to acoustic BEM) with a 5-frequency test run first.',
         '$ ==================================================================================',
         '*CONTROL_TERMINATION', '$#  endtim', '       1.0',
         '*CONTROL_IMPLICIT_GENERAL', '$#  imflag     dt0', '         1       1.0',
         '*CONTROL_IMPLICIT_EIGENVALUE', f'$#    neig  center   lflag  lfdtend   hflag  hfend  eigmth  shfscl', f'{NMODES:10d}       0.0         0       0.0         0       0.0         2       0.0',
         '*DATABASE_BINARY_D3PLOT', '$#      dt', '       1.0',
         '*INCLUDE', 'mesh.k', '*INCLUDE', 'loads.k',
         '$ ---- steady-state dynamics ----------------------------------------------------',
         '*FREQUENCY_DOMAIN_SSD', '$#   mdmin   mdmax   fnmin   fnmax  restmd  restdp  lcflag  relatv',
         f'         1{NMODES:10d}       0.0   {2.0*FMAX:8.1f}         0         0         0         0',
         '$#   dampf   lcdam   lctyp  dmpmas  dmpstf  dmpflg', f'{ZETA:10.4f}         0         0       0.0       0.0         0',
         '$#   nfreq  fstart   fstop  fspace   lcfreq', f'{NFREQ:10d}{FMIN:10.2f}{FMAX:10.2f}         0         0',
         '$ excitation: nodal loads defined by *LOAD_NODE_POINT with curve 1 (unit amplitude at all frequencies)',
         '$ ---- acoustic BEM (rigid ground by image method: see README, section "ground plane") -----------',
         '*FREQUENCY_DOMAIN_ACOUSTIC_BEM', '$#  method   maxit  tollin    tolr',
         '         3         0       0.0       0.0', '$#      ro       c    fmin    fmax   nfreq   dtout  tstart    pref',
         f'       1.2     343.0{FMIN:8.2f}{FMAX:8.2f}{NFREQ:8d}       0.0       0.0   2.0E-05',
         '$#  nsidext typext nsidint typint  (field points = node set 2; surface = part 2)', '         2         0         0         0',
         '*END']
    (d / 'main.k').write_text('\n'.join(M) + '\n', encoding='ascii')
    (d / 'run.bat').write_text('@echo off\r\nrem usage: run.bat   (set LSDYNA_EXE to your solver, e.g. lsdyna_dp.exe of your installation)\r\nif "%LSDYNA_EXE%"=="" (echo set LSDYNA_EXE first & exit /b 1)\r\n"%LSDYNA_EXE%" i=main.k ncpu=4 memory=400m > solver.log 2>&1\r\n', encoding='ascii')
    return dict(case=cid, t_m=t, buried=bur, nodes=slab.nn, solids=len(slab.conn), discrete=len(gn), bem_shells=len(cl), mics=mn, dx=slab.dx)


if __name__ == '__main__':
    man = [write_case(cid, t, bur) for cid, (t, bur) in CASES.items()]
    (OUT / 'manifest.json').write_text(json.dumps(man, indent=2))
    print(json.dumps(man, indent=1))
