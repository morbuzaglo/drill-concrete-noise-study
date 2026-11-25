"""Parse the OpenRadioss time-history (big-endian Fortran unformatted T01), build FRFs (FFT of acceleration / analytic FFT of the force pulse)
and compare with CalculiX SSD and the in-house modal solver for the free-free t=100 mm slab."""
import struct, numpy as np, pathlib, json
ROOT = pathlib.Path(__file__).resolve().parents[1]
f = ROOT / 'openradioss' / 'free_slab' / 'FREESLABT01'
b = f.read_bytes(); pos = 0; recs = []
while pos + 4 <= len(b):
    n = struct.unpack('>i', b[pos:pos + 4])[0]
    if n < 0 or pos + 8 + n > len(b): break
    recs.append((pos + 4, n)); pos += 8 + n
T = []; G = []; D = []; S = []
i = 0
while i + 3 < len(recs):
    if recs[i][1] == 4 and recs[i + 1][1] == 64 and recs[i + 2][1] == 36 and recs[i + 3][1] == 12:
        rd = lambda k, fmt: np.frombuffer(b[recs[k][0]:recs[k][0] + recs[k][1]], '>f4').astype(float)
        T.append(rd(i, "f")[0]); G.append(rd(i + 1, "f")); S.append(rd(i + 2, "f")); D.append(rd(i + 3, "f")); i += 4
    else: i += 1
T = np.array(T); S = np.array(S); D = np.array(D)
print('steps', len(T), 'T range', T[0], T[-1], 'dt', np.diff(T)[:3])
# acceleration FRF via FFT on a uniform grid
dt = np.median(np.diff(T)); n = len(T); fs = 1 / dt
res = {}
for name, cols in (('var-major', [0, 1, 2]), ('node-major', [0, 3, 6])):
    a = S[:, cols]                                           # x-acceleration at the 3 sensor nodes
    a = a - a.mean(0)
    # pulse: triangle, half-width 1e-4 s centred at 1e-4 s, unit peak -> analytic transform
    fr = np.fft.rfftfreq(n, dt); w = 2 * np.pi * fr; ah = 1e-4
    Fh = ah * np.sinc(fr * ah) ** 2 * np.exp(-1j * w * ah)
    A = np.fft.rfft(a, axis=0) * dt                           # continuous-FT approximation (t starts at T[0]~dt)
    A = A * np.exp(1j * w * T[0])[:, None] * 0 + A
    H = A / Fh[:, None]
    res[name] = (fr, H)
    lo = (fr > 20) & (fr < 150)
    print(name, 'mean |a/F| 20-150 Hz per sensor', np.abs(H[lo]).mean(0), ' (rigid body F/m = %.5f)' % (1 / 240.0))
np.savez(ROOT / 'results' / 'xcheck_or_frf.npz', fr=res['var-major'][0], Hvar=res['var-major'][1], Hnode=res['node-major'][1], t_end=T[-1])
