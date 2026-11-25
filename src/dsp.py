"""Signal processing helpers: SPL, one-sided PSD, octave-band integration, assumed excitation spectra.
All pressures are RMS unless stated; transfer functions H = p/F are complex phasor ratios (peak/peak = RMS/RMS)."""
import numpy as np
PREF = 20e-6
FC = np.array([62.5, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
LABEL = ['63', '125', '250', '500', '1000', '2000', '4000', '8000']
EDGES = np.stack([FC / np.sqrt(2), FC * np.sqrt(2)], 1)


def spl(p_rms):
    return 20 * np.log10(np.maximum(p_rms, 1e-30) / PREF)


def trapz_band(f, y, f1, f2):
    """Trapezoid integral of y(f) over [f1,f2] with linear interpolation of y at the band edges (f sorted, unique)."""
    m = (f > f1) & (f < f2)
    ff = np.concatenate([[f1], f[m], [f2]]); yy = np.concatenate([[np.interp(f1, f, y)], y[m], [np.interp(f2, f, y)]])
    return np.trapezoid(yy, ff)


def force_psd(f, kind='flat', frms=10.0, fa=EDGES[0, 0], fb=EDGES[4, 1]):
    """Assumed (illustrative) force spectral density [N^2/Hz] with total RMS frms over [fa,fb]."""
    f = np.asarray(f, float)
    if kind == 'flat':
        S = np.where((f >= fa) & (f <= fb), frms ** 2 / (fb - fa), 0.0)
    elif kind == 'pink':
        S = np.where((f >= fa) & (f <= fb), frms ** 2 / (np.log(fb / fa) * f), 0.0)
    else:
        raise ValueError(kind)
    return S


def band_levels(f, H, S, bands=EDGES):
    """Unweighted octave-band SPL [dB re 20 uPa] of p = H*F with force PSD S. H may be (nf,) or (nf,nmic)."""
    H = np.asarray(H)
    if H.ndim == 1: H = H[:, None]
    out = np.full((len(bands), H.shape[1]), np.nan)
    for i, (f1, f2) in enumerate(bands):
        if f2 < f[0] or f1 > f[-1]: continue
        for j in range(H.shape[1]):
            out[i, j] = spl(np.sqrt(trapz_band(f, np.abs(H[:, j]) ** 2 * S, f1, f2)))
    return out


def tf_band_level(f, H, bands=EDGES):
    """Octave-band mean-square transfer |H|^2 averaged over the band, expressed as dB re 20uPa per N (unit flat force density 1 N^2/Hz*B)."""
    H = np.asarray(H)
    if H.ndim == 1: H = H[:, None]
    out = np.full((len(bands), H.shape[1]), np.nan)
    for i, (f1, f2) in enumerate(bands):
        if f2 < f[0] or f1 > f[-1]: continue
        for j in range(H.shape[1]):
            out[i, j] = spl(np.sqrt(trapz_band(f, np.abs(H[:, j]) ** 2, f1, f2) / (f2 - f1)))
    return out


def psd_welch(x, fs, nper=8192):
    """One-sided PSD [unit^2/Hz] with Hann window and power normalisation (Parseval-consistent)."""
    from scipy.signal import welch
    return welch(x, fs=fs, window='hann', nperseg=nper, noverlap=nper // 2, detrend=False, scaling='density')
