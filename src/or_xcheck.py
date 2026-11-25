"""Second structural cross-check: free-free t=100 mm slab, unit force at the drill point, accelerations at the virtual sensors.
OpenRadioss (explicit, time-domain impulse -> FFT) vs CalculiX (SSD) vs in-house modal solver. Damping: constant 1% modal
(CalculiX, in-house) vs Rayleigh alpha/beta tuned to 1% at 231 and 940 Hz (OpenRadioss)."""
import numpy as np, pathlib, subprocess, os, sys, csv, re
from fem import Slab
from model import DRILL, H_SLAB, W_SLAB
ROOT = pathlib.Path(__file__).resolve().parents[1]
OR = pathlib.Path(r'C:\OpenRadioss\OpenRadioss\exec')
job = ROOT / 'openradioss' / 'free_slab'; job.mkdir(parents=True, exist_ok=True)
dx = float(sys.argv[1]) if len(sys.argv) > 1 else 0.025
t = 0.10; slab = Slab(t, W_SLAB, H_SLAB, dx, zb=0.0)
xyz = slab.node_xyz()
nid_pt = lambda p: int(np.argmin(np.linalg.norm(xyz - np.array(p), axis=1)))
drill_node = nid_pt((DRILL['depth'], DRILL['yc'], DRILL['zl']))
sensors = [(0.0, DRILL['yc'] + 0.15, DRILL['zl']), (t, DRILL['yc'], DRILL['zl']), (t / 2, 0.85, H_SLAB)]
sens_nodes = [nid_pt(p) for p in sensors]
print('drill node', xyz[drill_node], 'sensor nodes', [xyz[n] for n in sens_nodes])

def build_radioss(Tend=0.4):
    L = ['#RADIOSS STARTER', '/BEGIN', 'FREESLAB', '      2022         0',
         '                  kg                  m                  s', '                  kg                  m                  s', '/NODE']
    L += ['%10d%20.10e%20.10e%20.10e' % (i + 1, *xyz[i]) for i in range(slab.nn)]
    L.append('/BRICK/1')
    L += ['%10d' % (e + 1) + ''.join('%10d' % (slab.conn[e, o] + 1) for o in (0, 1, 3, 2, 4, 5, 7, 6)) for e in range(len(slab.conn))]
    L += ['/PART/1', 'concrete', '         1         1         0',
          '/PROP/SOLID/1', 'solid', '#   Isolid    Ismstr               Icpre     Inpts', '        14         0                   0         0',
          '#                 qa                  qb                  dn                   h', '                 1.1                0.05                 0.1                 0.0',
          '/MAT/LAW1/1', 'concrete', '#              RHO_I', '%20.10e' % slab.rho, '#                  E                  Nu', '%20.10e%20.10e' % (slab.E, slab.nu),
          '/FUNCT/1', 'pulse', '%20.10e%20.10e' % (0.0, 0.0), '%20.10e%20.10e' % (1.0e-4, 1.0), '%20.10e%20.10e' % (2.0e-4, 0.0), '%20.10e%20.10e' % (1.0, 0.0),
          '/CLOAD/1', 'force_x', '#  funct_IDT       Dir   skew_ID   sens_ID   node_ID            Fscale_Y            Ascale_X',
          '         1         X         0         0         1%20.10e' % 1.0,
          '/GRNOD/NODE/1', 'drillnode', '%10d' % (drill_node + 1),
          '/TH/NODE/1', 'sensors', 'AX'.ljust(10) + 'AY'.ljust(10) + 'AZ'.ljust(10)] + ['%10d%10d' % (n + 1, 0) for n in sens_nodes] + [
          '/TH/NODE/2', 'drill', 'DX'.ljust(10) + 'DY'.ljust(10) + 'DZ'.ljust(10), '%10d%10d' % (drill_node + 1, 0),
          '/GRNOD/PART/2', 'allnodes', '         1',
          '/DAMP/1', 'rayleigh', '#  grnod_ID                           Alpha                Beta', '%10d%10s%20.10e%20.10e' % (2, '', 23.3, 2.72e-6),
          '/END']
    (job / 'FREESLAB_0000.rad').write_text('\n'.join(L) + '\n', encoding='ascii')
    a, b = 23.3, 2.72e-6
    E = ['#RADIOSS ENGINE', '/RUN/FREESLAB/1/', '%20.10e' % Tend, '/PRINT/-500', '/TFILE/0', '%20.10e' % 2.0e-4, '/ANIM/DT', '0 1.0e-1', '/END']
    (job / 'FREESLAB_0001.rad').write_text('\n'.join(E) + '\n', encoding='ascii')

if __name__ == '__main__':
    build_radioss()
    env = dict(os.environ, RAD_CFG_PATH=r'C:\OpenRadioss\OpenRadioss\hm_cfg_files', RAD_H3D_PATH=r'C:\OpenRadioss\OpenRadioss\extlib\h3d\lib\win64',
               PATH=r'C:\OpenRadioss\OpenRadioss\extlib\intelOneAPI_runtime\win64;C:\OpenRadioss\OpenRadioss\extlib\hm_reader\win64;C:\OpenRadioss\OpenRadioss\extlib\h3d\lib\win64;' + os.environ['PATH'], OMP_NUM_THREADS='2', KMP_STACKSIZE='400m')
    r = subprocess.run([str(OR / 'starter_win64.exe'), '-i', 'FREESLAB_0000.rad', '-np', '1'], cwd=job, env=env, capture_output=True, text=True)
    (job / 'starter.log').write_text(r.stdout + r.stderr); print('starter rc', r.returncode)
    r2 = subprocess.run([str(OR / 'engine_win64.exe'), '-i', 'FREESLAB_0001.rad'], cwd=job, env=env, capture_output=True, text=True)
    (job / 'engine.log').write_text(r2.stdout + r2.stderr); print('engine rc', r2.returncode); print(r2.stdout[-800:])
    pass
