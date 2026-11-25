"""Verification (e): synthetic signals with known RMS / PSD pass through the same processing chain as solver output."""
import numpy as np, csv, pathlib
from dsp import *
ROOT = pathlib.Path(__file__).resolve().parents[1]
rows = []
def add(name, expected, measured, unit, tol):
    err = measured - expected
    rows.append([name, f'{expected:.4f}', f'{measured:.4f}', unit, f'{err:+.4f}', tol, 'PASS' if abs(err) <= tol else 'FAIL'])
rng = np.random.default_rng(11)
fs = 8192.0; T = 400.0; n = int(fs * T); t = np.arange(n) / fs
# 1) sine, 1 Pa peak  -> rms 0.7071 Pa -> 90.97 dB
A = 1.0; x = A * np.sin(2 * np.pi * 250.0 * t)
add('sine rms (time domain)', A / np.sqrt(2), np.sqrt(np.mean(x ** 2)), 'Pa', 1e-3)
f, S = psd_welch(x, fs, 16384); df = f[1] - f[0]
add('sine rms from Welch PSD integral', A / np.sqrt(2), np.sqrt(np.sum(S) * df), 'Pa', 5e-3)
add('sine SPL', spl(A / np.sqrt(2)), spl(np.sqrt(np.sum(S) * df)), 'dB', 0.05)
add('sine SPL (analytic 20log10(0.7071/20e-6))', 20 * np.log10(A / np.sqrt(2) / 20e-6), spl(A / np.sqrt(2)), 'dB', 1e-9)
# 2) white noise with known one-sided PSD S0, octave-band energy integration
S0 = 4e-2; sig = np.sqrt(S0 * fs / 2); w = rng.normal(0, sig, n)
f, S = psd_welch(w, fs, 16384)
for (f1, f2), lab in zip(EDGES[:5], LABEL[:5]):
    exp = spl(np.sqrt(S0 * (f2 - f1)))
    meas = spl(np.sqrt(trapz_band(f, S, f1, f2)))
    add(f'white-noise octave {lab} Hz band level', exp, meas, 'dB', 0.2)
# 3) noise filtered by a known transfer function: band level from time-domain RMS vs |H|^2 S integral
F = np.fft.rfft(w); fr = np.fft.rfftfreq(n, 1 / fs)
H = (1.0 + 4.0 / (1 + ((fr - 500) / 60.0) ** 2)) * np.exp(-1j * fr / 300.0)       # resonance-like H(f)
y = np.fft.irfft(F * H, n)
fm, Sy = psd_welch(y, fs, 16384)
Hm = np.interp(fm, fr, np.abs(H))
for (f1, f2), lab in zip(EDGES[1:5], LABEL[1:5]):
    # time-domain band RMS via ideal FFT mask
    mask = (fr >= f1) & (fr < f2); yb = np.fft.irfft(np.fft.rfft(y) * mask, n)
    meas_td = spl(np.sqrt(np.mean(yb ** 2)))
    pred = band_levels(fm, Hm, np.full_like(fm, S0), bands=np.array([[f1, f2]]))[0, 0]
    add(f'filtered noise {lab} Hz: |H|^2 S0 integral vs time-domain RMS', meas_td, pred, 'dB', 0.3)
# 4) assumed force spectra: total RMS and band-level code path
ff = np.linspace(EDGES[0, 0], EDGES[4, 1], 200001)
for kind in ('flat', 'pink'):
    S = force_psd(ff, kind, 10.0)
    add(f'assumed force PSD ({kind}) total RMS', 10.0, np.sqrt(np.trapezoid(S, ff)), 'N', 0.01)
    H1 = np.ones_like(ff)
    L = band_levels(ff, H1, S)
    # unit transfer 1 Pa/N : sum of band powers must equal total
    ptot = sum(10 ** (L[i, 0] / 10) * PREF ** 2 for i in range(5))
    add(f'band-sum of {kind} spectrum = total power', 10.0 ** 2, ptot, 'N^2', 0.05)
with open(ROOT / 'results' / 'verify_e_dsp.csv', 'w', newline='', encoding='utf-8') as fh:
    wr = csv.writer(fh); wr.writerow(['check', 'expected', 'measured', 'unit', 'error', 'tolerance', 'verdict']); wr.writerows(rows)
for r in rows: print(r)
print('FAILS:', sum(r[-1] == 'FAIL' for r in rows))
