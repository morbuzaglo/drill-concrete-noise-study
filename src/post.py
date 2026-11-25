"""Combine CalculiX panel velocities with Bempp-cl transfer vectors -> pressure transfer functions and band levels."""
import numpy as np, pathlib
from scipy.interpolate import CubicSpline
from dsp import *

ROOT = pathlib.Path(__file__).resolve().parents[1]
C0 = 343.0
CASES = ['t10_exp', 't10_bur', 't20_exp', 't20_bur']
MIC_NAMES = ['F', 'R', 'Rg', 'S']
CASE_LABEL = {'t10_exp': 't=100 mm, exposed', 't10_bur': 't=100 mm, buried', 't20_exp': 't=200 mm, exposed', 't20_bur': 't=200 mm, buried'}


def load_ccx(cid, tag=''):
    d = np.load(ROOT / 'results' / f'ccx_{cid}{tag}.npz', allow_pickle=True)
    f = d['freq']; u, idx = np.unique(f, return_index=True)           # band edges are duplicated
    return dict(freq=u, v=d['v'][idx], acc=d['acc'][idx], eig=d['eig'], corners=d['corners'], tags=d['tags'], t=float(d['t']), buried=bool(d['buried']))


def load_T(cid, tfile=None):
    d = np.load(tfile or ROOT / 'results' / f'bempp_T_{cid}.npz')
    fT = np.concatenate([d['f_low'], d['f_high']]); T = np.concatenate([d['T_low'], d['T_high']], 0)
    return fT, T, d['mics']


def interp_T(fT, T, fq, mics, center):
    ref = np.linalg.norm(mics - center[None], axis=1)
    k = 2 * np.pi * fT / C0
    Td = T * np.exp(1j * k[:, None] * ref[None, :])[:, :, None]
    cs = CubicSpline(fT, Td, axis=0)
    return cs(fq) * np.exp(-1j * 2 * np.pi * fq[:, None] / C0 * ref[None, :])[:, :, None]


def pressure(cid, tag='', tfile=None, col=0):
    r = load_ccx(cid, tag); fT, T, mics = load_T(cid, tfile)
    t = r['t']; zb = -0.4 if r['buried'] else 0.0
    center = np.array([t / 2, 0.5, 0.5 + zb])
    Ti = interp_T(fT, T, r['freq'], mics, center)
    p = np.einsum('fmq,fq->fm', Ti, r['v'][:, :, col])
    return r['freq'], p, r


def bands_mean_sq(f, p, bands=EDGES):
    return tf_band_level(f, p, bands)
