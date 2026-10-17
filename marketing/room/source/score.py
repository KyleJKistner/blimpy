"""Original score, sound design and dialogue mix for FLOAT / Room.

Deterministic synthesis in NumPy/SciPy: band-limited supersaw pads, filtered
plucks, Karplus-Strong strings, FM bells, synthesized drums, convolution
reverb and kick-driven ducking. No samples, loops or recordings are used.
Dialogue comes from voice.py (synthetic stock voices).

Writes 48 kHz float WAV stems to ../assets/audio and a pre-master mix.
Final loudness (-14 LUFS integrated, -1 dBTP) is set by master.py.
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, lfilter, resample_poly, sosfilt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import timeline as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'audio'
SR = 48000
DUR = T.FRAMES / T.FPS
N = int(DUR * SR) + SR          # one second of tail room, trimmed at the end
B = 60 / T.BPM                  # 0.5 s
rng = np.random.default_rng(20261017)
BUSES = ['pad', 'keys', 'arp', 'bass', 'drums', 'fx', 'ui', 'dialogue']
bus = {k: np.zeros((N, 2)) for k in BUSES}
send = {k: np.zeros((N, 2)) for k in BUSES}     # reverb sends


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(name, sig, start, amp=1.0, pan=0.0, verb=0.0):
    sig = np.asarray(sig, np.float64)
    i = int(round(start * SR))
    if sig.ndim == 1:
        p = np.clip(pan, -1, 1)
        sig = np.column_stack((sig * np.sqrt((1 - p) / 2), sig * np.sqrt((1 + p) / 2))) * np.sqrt(2)
    j0 = max(0, -i)
    i = max(0, i)
    j = min(N, i + len(sig) - j0)
    if j <= i:
        return
    seg = sig[j0:j0 + j - i] * amp
    bus[name][i:j] += seg
    if verb:
        send[name][i:j] += seg * verb


def lp(x, fc, order=2):
    return sosfilt(butter(order, min(fc, SR * .45), fs=SR, output='sos'), x, axis=0)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, btype='highpass', fs=SR, output='sos'), x, axis=0)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, min(hi, SR * .45)], btype='bandpass', fs=SR, output='sos'), x, axis=0)


def sweep_filter(x, f0, f1, kind='bandpass', q=1.2, block=256):
    """Time-varying biquad (RBJ cookbook) with exponential cutoff sweep."""
    y = np.zeros_like(x)
    z = np.zeros(2)
    nb = int(np.ceil(len(x) / block))
    for k in range(nb):
        fc = f0 * (f1 / f0) ** (k / max(1, nb - 1))
        w0 = 2 * np.pi * min(fc, SR * .45) / SR
        al = np.sin(w0) / (2 * q)
        cw = np.cos(w0)
        if kind == 'bandpass':
            b = np.array([al, 0, -al])
        else:
            b = np.array([(1 - cw) / 2, 1 - cw, (1 - cw) / 2])
        a = np.array([1 + al, -2 * cw, 1 - al])
        seg = x[k * block:(k + 1) * block]
        y[k * block:k * block + len(seg)], z = lfilter(b / a[0], a / a[0], seg, zi=z)
    return y


def saw(f, n, phase=0.0):
    """PolyBLEP band-limited sawtooth; f may be scalar or per-sample array."""
    dt = np.broadcast_to(np.asarray(f, np.float64) / SR, (n,))
    ph = (phase + np.cumsum(dt)) % 1.0
    y = 2 * ph - 1
    m = ph < dt
    x = ph[m] / dt[m]
    y[m] -= x + x - x * x - 1
    m = ph > 1 - dt
    x = (ph[m] - 1) / dt[m]
    y[m] -= x * x + x + x + 1
    return y


def env_adsr(n, a, d, s, r, dur):
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rel = np.clip((dur - t) / max(r, 1e-4), 0, 1)
    return e * np.minimum(1, rel + (t < dur - r))


# ----------------------------------------------------------------------------
# Instruments
# ----------------------------------------------------------------------------

def pad(start, dur, notes, amp=.05, cutoff=1800, verb=.45):
    n = int((dur + 1.2) * SR)
    t = np.arange(n) / SR
    e = np.clip(t / .55, 0, 1) ** 1.5 * np.clip((dur + 1.2 - t) / 1.2, 0, 1)
    for k, m in enumerate(notes):
        left = np.zeros(n)
        right = np.zeros(n)
        for j, det in enumerate([-.11, -.05, 0, .05, .11]):
            v = saw(hz(m) * 2 ** (det / 12), n, rng.uniform())
            p = (j - 2) / 2.5
            left += v * np.sqrt((1 - p) / 2)
            right += v * np.sqrt((1 + p) / 2)
        st = lp(np.column_stack((left, right)), cutoff * (1 + .1 * k), 2) / 5
        place('pad', st * e[:, None], start, amp, verb=verb)


def felt(start, m, amp=.12, pan=0.0, dur=2.5, verb=.4):
    """Soft felt-piano-like tone: slightly inharmonic partials, hammer thump."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    x = np.zeros(n)
    for k in range(1, 9):
        fk = f * k * np.sqrt(1 + .00035 * k * k)
        if fk > 16000:
            break
        x += np.sin(2 * np.pi * fk * t) * np.exp(-t * (1.1 + .9 * k)) / k ** 1.3
    thump = lp(rng.standard_normal(n), 900) * np.exp(-t * 90) * .25
    x = (x + thump) * np.clip(t / .006, 0, 1) * np.clip((dur - t) / .3, 0, 1)
    place('keys', lp(x, 5200), start, amp, pan, verb)


def pluck(start, m, amp=.06, pan=0.0, dur=.45, bright=7000, verb=.25, name='arp'):
    """Two detuned saws through a fast-closing lowpass: a crisp synth pluck."""
    n = int((dur + .25) * SR)
    t = np.arange(n) / SR
    x = saw(hz(m) * 1.003, n, rng.uniform()) + saw(hz(m) * .997, n, rng.uniform())
    e1 = np.exp(-t / .05)
    y = lp(x, bright) * e1 + lp(x, 1100) * (1 - e1)
    e = np.clip(t / .002, 0, 1) * np.exp(-t * 6) * np.clip((dur + .25 - t) / .25, 0, 1)
    place(name, y * e * .5, start, amp, pan, verb)


def string(start, m, amp=.08, pan=0.0, dur=2.0, verb=.35):
    """Karplus-Strong plucked string."""
    f = hz(m)
    L = int(SR / f)
    n = int(dur * SR)
    burst = np.zeros(n)
    burst[:L] = lp(rng.uniform(-1, 1, L), 6000)
    a = np.zeros(L + 2)
    a[0] = 1
    a[L] = a[L + 1] = -.4985
    y = lfilter([1], a, burst)
    y *= np.clip((dur - np.arange(n) / SR) / .2, 0, 1)
    place('keys', y, start, amp, pan, verb)


def bell(start, m, amp=.08, pan=0.0, dur=2.2, ratio=3.5, index=2.2, verb=.5, name='ui'):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    mod = index * np.exp(-t * 3) * np.sin(2 * np.pi * f * ratio * t)
    x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 2.4) * np.clip(t / .003, 0, 1)
    x += .25 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 5)
    place(name, x * np.clip((dur - t) / .2, 0, 1), start, amp, pan, verb)


def bass(start, dur, m, amp=.22):
    n = int((dur + .05) * SR)
    t = np.arange(n) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + .22 * np.sin(4 * np.pi * f * t) + .06 * saw(f, n)
    x = np.tanh(1.3 * x)
    e = np.clip(t / .006, 0, 1) * np.clip((dur + .05 - t) / .05, 0, 1)
    place('bass', lp(x * e, 900), start, amp)


def kick(start, amp=.55):
    n = int(.42 * SR)
    t = np.arange(n) / SR
    f = 46 + 130 * np.exp(-t * 38)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    click = hp(rng.standard_normal(n), 2500) * np.exp(-t * 420) * .35
    x = np.tanh(1.6 * (body + click)) * np.clip((.42 - t) / .04, 0, 1)
    place('drums', x, start, amp)
    KICKS.append(start)


def clap(start, amp=.20, verb=.18):
    n = int(.32 * SR)
    t = np.arange(n) / SR
    noise = bp(rng.standard_normal(n), 900, 5200)
    e = np.zeros(n)
    for k, dl in enumerate([0, .011, .022]):
        e += (t >= dl) * np.exp(-(t - dl) * 160) * (t - dl >= 0)
    e += (t >= .03) * np.exp(-(t - .03) * 17) * .55
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 40) * .25
    place('drums', noise * e + body, start, amp, verb=verb)


def hat(start, amp=.05, open_=False, pan=0.0):
    dur = .28 if open_ else .07
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for fq in [205.3, 304.4, 369.6, 522.7, 540.0, 800.0]:
        x += np.sign(np.sin(2 * np.pi * fq * 7.4 * t + rng.uniform(0, 6)))
    x = hp(x / 6 + .3 * rng.standard_normal(n), 7200)
    x *= np.exp(-t * (16 if open_ else 75)) * np.clip(t / .0008, 0, 1)
    place('drums', x, start, amp, pan)


def tom(start, m, amp=.18):
    n = int(.35 * SR)
    t = np.arange(n) / SR
    f = hz(m) * (1 + .5 * np.exp(-t * 30))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
    place('drums', x, start, amp, verb=.2)


def riser(start, dur, amp=.10, lo=350, hi=9000, pan_sweep=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    u = t / dur
    x = sweep_filter(rng.standard_normal(n), lo, hi, 'bandpass', q=1.6)
    tone = saw(220 * 2 ** (u * 1.5), n) * .12
    y = (x + lp(tone, 4000)) * u ** 2.2
    if pan_sweep:
        p = np.sin(u * np.pi * 3) * .5
        y = np.column_stack((y * np.sqrt((1 - p) / 2), y * np.sqrt((1 + p) / 2))) * np.sqrt(2)
    place('fx', y, start, amp, verb=.35)


def reverse_swell(end, dur, amp=.10):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = hp(rng.standard_normal(n), 3000) * (t / dur) ** 3
    place('fx', x, end - dur, amp, verb=.3)


def whoosh(center, dur=.45, amp=.08, direction=1, lo=500, hi=6000):
    n = int(dur * SR)
    t = np.arange(n) / SR
    u = t / dur
    x = sweep_filter(rng.standard_normal(n), lo, hi, 'bandpass', q=1.0) * np.sin(np.pi * u) ** 2
    p = direction * (u * 1.6 - .8)
    y = np.column_stack((x * np.sqrt((1 - p) / 2), x * np.sqrt((1 + p) / 2))) * np.sqrt(2)
    place('fx', y, center - dur * .6, amp, verb=.25)


def impact(start, amp=.35):
    n = int(2.2 * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t * 9)) / SR) * np.exp(-t * 2.4)
    crack = bp(rng.standard_normal(n), 300, 7000) * np.exp(-t * 26) * .45
    place('fx', np.tanh(1.4 * (boom + crack)), start, amp, verb=.45)


def subdrop(start, dur=1.4, amp=.25):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 75 * (30 / 75) ** (t / dur)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6) * np.clip(t / .01, 0, 1)
    place('fx', x, start, amp)


def blip(start, f=2400, dur=.06, amp=.05, pan=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 60) * np.clip(t / .001, 0, 1)
    place('ui', x, start, amp, pan, verb=.15)


def tick(start, amp=.06, pan=0.0):
    n = int(.03 * SR)
    t = np.arange(n) / SR
    place('ui', hp(rng.standard_normal(n), 3000) * np.exp(-t * 300), start, amp, pan)


def whir(start, dur, amp=.012, spin_up=0.0, pan=0.0):
    """Quiet guarded-fan air noise with a blade-pass tone; illustrative only."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    k = np.clip(t / spin_up, 0, 1) if spin_up else np.ones(n)
    f = 60 + 110 * k
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) + .4 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR)
    air = bp(rng.standard_normal(n), 250, 2400)
    x = (air * .8 + tone * .25) * k ** 1.5 * np.clip((dur - t) / .3, 0, 1) * np.clip(t / .05, 0, 1)
    place('fx', x, start, amp, pan, verb=.05)


def dock_click(start, amp=.18):
    n = int(.25 * SR)
    t = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 1500, 9000) * np.exp(-t * 180) + .5 * np.sin(2 * np.pi * 1180 * t) * np.exp(-t * 70)
    x += .8 * np.sin(2 * np.pi * np.cumsum(70 + 40 * np.exp(-t * 30)) / SR) * np.exp(-t * 22)
    place('ui', x, start, amp, verb=.2)


# ----------------------------------------------------------------------------
# Arrangement (D major, 120 BPM)
# ----------------------------------------------------------------------------
KICKS = []
D, E, Fs, G, A, Bn, Cs = 62, 64, 66, 67, 69, 71, 73       # D4..C#5
CH = {
    'Gmaj9': [43, 55, 59, 62, 66, 69], 'Dadd9/F#': [42, 54, 57, 62, 64, 66], 'Asus': [45, 57, 62, 64, 69],
    'A': [45, 57, 61, 64, 69], 'D': [38, 57, 62, 66, 69, 74], 'A/C#': [37, 57, 61, 64, 69, 73],
    'Bm7': [35, 54, 59, 62, 66, 69], 'Gmaj7': [31, 55, 59, 62, 66, 71], 'Em9': [40, 55, 59, 62, 66, 71],
    'Dmaj9': [38, 54, 57, 61, 64, 69],
}
MOTIF = [A + 0, D + 12, E + 12, Fs + 12]                  # "FLOAT": a rising fourth, then steps


def section_intro():
    # 0-5 s: air, felt piano, sustained harmony. Space for the spoken question.
    pad(0.0, 2.7, CH['Gmaj9'][1:], .045, 1300)
    pad(2.5, 2.6, CH['Dadd9/F#'][1:], .045, 1500)
    bass(0.0, 2.4, CH['Gmaj9'][0] + 12, .07)
    bass(2.5, 2.4, CH['Dadd9/F#'][0] + 12, .07)
    # Piano answers the question rather than talking over it.
    for k, (t, m) in enumerate([(.02, 74), (2.0, 71), (2.25, 69), (2.5, 69), (4.0, 74), (4.25, 76), (4.5, 78)]):
        felt(t, m, .10 if t < 2.4 else .085, -.3 + .15 * k)


def section_build():
    # 5-7 s: dominant pedal, fan spin-up, filtered arp and a fill into the drop.
    pad(5.0, 2.0, CH['Asus'][1:], .05, 2200)
    for k in range(16):
        t = 5.0 + k * B / 4
        m = CH['Asus'][1 + (k % 4)] + 12
        pluck(t, m, .035 + .03 * k / 16, (-.4, .4)[k % 2], bright=1500 + 5500 * k / 16)
    for k in range(4):
        bass(5.0 + k * B, B * .8, 33 + 12, .14)
    riser(5.0, 2.0, .11)
    reverse_swell(7.0, 1.0, .07)
    for k, t in enumerate(np.arange(6.0, 7.0, B / 4)):
        clap(t, .03 + .10 * (k / 8) ** 2, verb=.1)
    for t, m in [(6.5, 50), (6.625, 47), (6.75, 45), (6.875, 43)]:
        tom(t, m, .14)


def groove(t0, t1, chords, energy=1.0, hats=True, claps=True, arp=True, kick_on=True):
    """Four-on-the-floor house groove; `chords` is [(start, name), ...] in absolute s."""
    for k, (cs, name) in enumerate(chords):
        ce = chords[k + 1][0] if k + 1 < len(chords) else t1
        notes = CH[name]
        pad(cs, ce - cs, notes[1:], .038 * energy, 2400)
        # Syncopated root bass.
        for off in np.arange(0, ce - cs - 1e-6, B):
            bass(cs + off + B / 2, B * .42, notes[0] + 12 if notes[0] < 40 else notes[0], .20 * energy)
            if off == 0:
                bass(cs, B * .35, notes[0] + 12 if notes[0] < 40 else notes[0], .16 * energy)
        if arp:
            pat = [notes[2] + 12, notes[3] + 12, notes[4] + 12, notes[3] + 12, notes[2] + 24, notes[4] + 12, notes[3] + 12, notes[-1] + 12]
            for j, t in enumerate(np.arange(cs, ce - 1e-6, B / 2)):
                pluck(t, pat[j % len(pat)], .045 * energy, (-.45, .45)[j % 2], bright=6500)
    for t in np.arange(t0, t1 - 1e-6, B):
        beat = int(round((t - t0) / B))
        if kick_on:
            kick(t, .52 * energy)
        if claps and beat % 2 == 1:
            clap(t, .17 * energy)
        if hats:
            hat(t + B / 2, .05 * energy, open_=(beat % 4 == 3), pan=.3)
            hat(t + B / 4, .022 * energy, pan=-.35)
            hat(t + 3 * B / 4, .022 * energy, pan=-.35)


def arrange():
    section_intro()
    section_build()
    # 7-11 s: the drop under the title.
    impact(7.0, .34)
    subdrop(7.0, 1.6, .22)
    groove(7.0, 11.0, [(7.0, 'D'), (9.0, 'A/C#')], 1.0)
    for j, m in enumerate(MOTIF):
        bell(7.0 + j * B, m + 12, .05, -.3 + .2 * j, name='keys', verb=.45)
    # 11-13 s: point-of-view search; filtered, ticking, tense.
    groove(11.0, 13.0, [(11.0, 'Bm7')], .78, claps=False, arp=True)
    riser(11.6, 1.4, .06, 800, 6000)
    for t in np.arange(11.0, 12.1, B / 2):
        tick(t, .045, (-.5, .5)[int(t * 4) % 2])
    for t, f in [(11.1, 2200), (11.45, 2200), (11.8, 2600)]:
        blip(t, f, .05, .045)
    blip(12.08, 2900, .07, .07)
    blip(12.16, 3900, .09, .07)
    # 13-18 s: breakdown for "Found them", warm chime, phone ping.
    pad(13.0, 2.5, CH['Gmaj7'][1:], .05, 1700)
    pad(15.5, 2.5, CH['Em9'][1:], .05, 1700)
    bass(13.0, 2.3, 43, .12)
    bass(15.5, 2.3, 40, .12)
    for k, (t, m) in enumerate([(13.0, 71), (14.0, 74), (14.5, 78), (15.5, 76), (16.5, 74), (17.0, 71)]):
        string(t, m, .07, -.3 + .12 * k)
    for t in np.arange(13.0, 18.0, B * 2):
        kick(t, .26)
    bell(13.55, 85, .06, -.15, ratio=2.0, index=1.5)
    bell(13.66, 90, .05, .15, ratio=2.0, index=1.5)
    bell(T.NOTIFICATION['at_s'], 88, .07, .2, ratio=3.0, index=1.2, dur=1.2)
    bell(T.NOTIFICATION['at_s'] + .12, 95, .06, .25, ratio=3.0, index=1.2, dur=1.2)
    riser(16.5, 1.5, .09)
    for k, t in enumerate(np.arange(17.0, 18.0, B / 4)):
        clap(t, .025 + .08 * (k / 8) ** 2, verb=.1)
    # 18-22 s: shift change; groove returns, faster harmonic rhythm into the lift.
    impact(18.0, .22)
    groove(18.0, 22.0, [(18.0, 'D'), (19.0, 'A/C#'), (20.0, 'Bm7'), (21.0, 'Gmaj7')], 1.0)
    dock_click(19.95, .16)
    bell(20.0, 81, .035, 0, ratio=1.0, index=.4, dur=1.4)
    whir(20.35, 1.9, .010, spin_up=.6, pan=-.4)
    # 22-24 s: lift; dominant build.
    groove(22.0, 24.0, [(22.0, 'A')], 1.05, claps=True)
    riser(22.0, 2.0, .12)
    reverse_swell(24.0, 1.2, .08)
    whoosh(22.15, .7, .07, 1, 300, 5000)
    # 24-27 s: "Not on a screen. / In the room." Big resolve, then air.
    impact(24.0, .28)
    groove(24.0, 26.0, [(24.0, 'D')], 1.0, arp=True)
    pad(26.0, 1.0, CH['Gmaj7'][1:], .045, 2600)
    bass(26.0, .9, 43, .18)
    for j, m in enumerate(MOTIF):
        bell(25.0 + j * B / 2, m + 12, .045, -.3 + .2 * j, name='keys')
    # 27-30 s: logo hit and ring-out.
    impact(27.0, .30)
    kick(27.0, .5)
    pad(27.0, 2.6, CH['Dmaj9'][1:], .05, 2000)
    bass(27.0, 2.7, 38, .16)
    for j, m in enumerate(MOTIF + [A + 12]):
        bell(27.0 + j * B / 2, m + 12, .06, -.4 + .2 * j, dur=2.8, name='keys')
    felt(27.0, 62, .1, 0, dur=3.0)


def sound_design():
    # Room air under everything.
    room = lp(rng.standard_normal((N, 2)), 3500) * .0025
    bus['fx'][:] += hp(room, 60)
    bell(1.55, 93, .025, .1, ratio=1.0, index=.6, dur=1.2)     # indicator wakes
    whir(5.0, 15.0, .010, spin_up=.55, pan=.1)                   # hero fans, 5.0-20.0
    whoosh(6.0, .5, .07, -1)
    whoosh(7.0, .6, .09, 1, 400, 8000)
    whoosh(11.0, .35, .05, 1)
    whoosh(13.0, .35, .04, -1)
    whoosh(24.0, .6, .06, -1, 300, 4000)


def dialogue():
    timing = json.loads((ROOT / 'assets' / 'voice' / 'timing.json').read_text())
    for ln in timing['lines']:
        sr, x = wavfile.read(ROOT / 'assets' / 'voice' / f"{ln['id']}.wav")
        x = x.astype(np.float64) / (2 ** 31 if x.dtype == np.int32 else 1.0)
        if sr != SR:
            x = resample_poly(x, SR, sr)
        x = x / max(np.abs(x).max(), 1e-9)
        if ln['who'] == 'float':
            # FLOAT: close, intimate, a touch of small-speaker presence.
            x = hp(x, 140)
            x = x + .18 * bp(x, 2500, 5500)
            place('dialogue', x, ln['start_s'], 1.25, 0.0, verb=.10)
        else:
            # Off-screen person across the room.
            x = lp(hp(x, 90), 9000)
            place('dialogue', x, ln['start_s'], 1.15, -.08, verb=.22)
    return timing


def reverb_ir(rt60=2.1, predelay=.014, seed=7):
    r = np.random.default_rng(seed)
    n = int(rt60 * 1.1 * SR)
    t = np.arange(n) / SR
    ir = r.standard_normal((n, 2)) * np.exp(-6.9 * t / rt60)[:, None]
    dark = lp(ir, 2800)
    w = np.clip(t / (rt60 * .5), 0, 1)[:, None]
    ir = hp(ir * (1 - w) + dark * w, 150)
    for d, g in [(.007, .5), (.013, .35), (.021, .3), (.029, .22)]:
        k = int(d * SR)
        ir[k, 0] += g
        ir[k + 37, 1] += g
    ir = np.vstack((np.zeros((int(predelay * SR), 2)), ir))
    return ir / np.sqrt((ir ** 2).sum() / 2) * .5


def duck_curve(times, depth=.55, release=.16):
    d = np.ones(N)
    for st in times:
        i = int(st * SR)
        ln = min(N - i, int(.4 * SR))
        if ln > 0:
            tt = np.arange(ln) / SR
            d[i:i + ln] *= 1 - depth * np.exp(-tt / release) * np.clip(tt / .003, 0, 1)
    return d


def dialogue_duck(timing, depth_db=-10.0):
    g = np.ones(N)
    target = 10 ** (depth_db / 20)
    for ln in timing['lines']:
        a, b = ln['start_s'] - .12, ln['start_s'] + ln['duration_s'] + .15
        t = np.arange(N) / SR
        k = np.clip(np.minimum((t - a) / .12, (b - t) / .25), 0, 1)
        g = np.minimum(g, 1 - (1 - target) * k)
    return g


def limiter(x, ceiling=.89, release=.08):
    peak = np.max(np.abs(x), axis=1)
    gain = np.minimum(1, ceiling / np.maximum(peak, 1e-9))
    # Look-ahead by 2 ms and smooth recovery.
    la = int(.002 * SR)
    gain = np.minimum.accumulate(np.lib.stride_tricks.sliding_window_view(np.pad(gain, (0, la), constant_values=1), la + 1), axis=1)[:, -1]
    a = np.exp(-1 / (release * SR))
    g = lfilter([1 - a], [1, -a], gain)
    g = np.minimum(g, gain)
    return x * g[:, None]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    arrange()
    sound_design()
    timing = dialogue()
    side = duck_curve(KICKS)
    for k in ('pad', 'arp', 'keys'):
        bus[k] *= np.sqrt(side)[:, None]
    bus['bass'] *= side[:, None]
    # Shared hall reverb for everything but drums' dry hits.
    ir = reverb_ir()
    wet = np.zeros((N, 2))
    total_send = sum(send.values())
    for ch in range(2):
        wet[:, ch] = fftconvolve(total_send[:, 0] * .5 + total_send[:, 1] * .5, ir[:, ch])[:N]
    duck = dialogue_duck(timing)
    gains = dict(pad=1.0, keys=1.0, arp=1.0, bass=1.0, drums=1.0, fx=1.0, ui=1.0, dialogue=1.0)
    stems = {}
    stems['music'] = (bus['pad'] + bus['keys'] + bus['arp'] + bus['bass'] + wet * .55) * duck[:, None]
    stems['drums'] = bus['drums'] * .72 * duck[:, None] ** .8
    stems['effects'] = bus['fx'] + bus['ui']
    stems['dialogue'] = bus['dialogue']
    for k in stems:
        stems[k] = hp(stems[k], 25)
    end = int(DUR * SR)
    fade = np.ones(N)
    fade[end - int(1.6 * SR):end] = np.linspace(1, 0, int(1.6 * SR)) ** 2
    fade[end:] = 0
    mix = sum(stems.values()) * fade[:, None]
    peak = np.max(np.abs(mix))
    g = .5 / max(peak, 1e-9)
    master = limiter(mix * g * 1.6)[:end]
    for k, v in stems.items():
        wavfile.write(OUT / f'{k}.wav', SR, (v * fade[:, None] * g)[:end].astype(np.float32))
    wavfile.write(OUT / 'premaster_mix.wav', SR, master.astype(np.float32))
    meta = dict(bpm=T.BPM, key='D major', duration_s=DUR, sample_rate=SR, seed=20261017,
                original_synthesis=True, stems=list(stems), kicks=len(KICKS),
                peak_before_gain=float(peak), sections={
                    'intro': [0, 5], 'build': [5, 7], 'drop': [7, 11], 'search': [11, 13], 'found': [13, 18],
                    'shift_change': [18, 22], 'lift': [22, 24], 'thesis': [24, 27], 'end': [27, 30]})
    (OUT / 'score_metadata.json').write_text(json.dumps(meta, indent=1))
    print('score written:', {k: round(float(np.sqrt(np.mean(v ** 2))), 4) for k, v in stems.items()}, flush=True)


if __name__ == '__main__':
    main()
