"""Original score for "Why Most Animals in the Open Ocean Glow", synthesised in code (no samples, no reference audio).

72 BPM, D major / D Lydian for wonder, D minor for the predators. Sections follow the scenes and land on narrated
words: the score sinks with the dive, brightens when life makes light, drops out for "Bad idea", pulses under the
burglar alarm, sneaks with the dragonfish, and resolves to D major on the title.
Writes ../assets/music_dry.wav (stereo, not ducked; mix.py does that).
"""
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

import cues
import sound_effects as fx
from cues import FILM, s, w

HERE = Path(__file__).resolve().parent
SR = fx.SR
rng = np.random.default_rng(21)
BEAT = 60 / 72
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)
N = fx.n_samples(FILM)
bus = {k: np.zeros((N, 2)) for k in ["pad", "bell", "bass", "perc"]}
a = lambda scene, word, n=1: w(word, n, s(scene))


def put(name, x, at, gain_db=0.0, pan=0.0):
    x = np.asarray(x, float)
    if x.ndim == 1:
        th = (pan + 1) * np.pi / 4
        x = np.stack([x * np.cos(th), x * np.sin(th)], 1) * np.sqrt(2)
    i = int(round(at * SR))
    if i < 0:
        x, i = x[-i:], 0
    if i >= N or not len(x):
        return
    j = min(N, i + len(x))
    bus[name][i:j] += x[: j - i] * 10 ** (gain_db / 20)


def env_ar(n, a_s, r_s):
    e = np.ones(n)
    na, nr = min(n, int(a_s * SR)), min(n, int(r_s * SR))
    if na:
        e[:na] = np.linspace(0, 1, na) ** 1.5
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e


def pad(notes, dur, cutoff=1400.0, a_s=0.8, r_s=1.0, det=0.08):
    """Detuned saws through a low-pass; `cutoff` may be a (start, end) pair for a slow filter sweep."""
    n, t = fx.n_samples(dur), fx.time_axis(dur)
    L, R = np.zeros(n), np.zeros(n)
    for m in notes:
        fr = mtof(m)
        for d in (-det, 0.0, det):
            p0 = rng.random()
            L += signal.sawtooth(2 * np.pi * (fr * 2 ** (d / 12) * t + p0))
            R += signal.sawtooth(2 * np.pi * (fr * 2 ** ((d + 0.03) / 12) * t + p0 * 0.5))
    e = env_ar(n, a_s, r_s) / (3 * len(notes))
    if isinstance(cutoff, tuple):   # filter sweep: crossfade between 5 fixed low-passes (continuous, no clicks)
        cs = np.geomspace(cutoff[0], cutoff[1], 5)
        u = np.linspace(0, 4, n)
        out = np.zeros((n, 2))
        for k in range(5):
            wk = np.clip(1 - np.abs(u - k), 0, 1)
            if wk.any():
                out += np.stack([fx.lowpass(L, cs[k], 2), fx.lowpass(R, cs[k], 2)], 1) * wk[:, None]
        return out * e[:, None]
    return np.stack([fx.lowpass(L, cutoff, 2) * e, fx.lowpass(R, cutoff, 2) * e], 1)


def bell(m, dur=1.6, bright=1.0):
    """Glassy, celesta-like tone: inharmonic partials with fast high decays (the 'bioluminescent' voice)."""
    fr, t = mtof(m), fx.time_axis(dur)
    y = sum(amp * np.sin(2 * np.pi * fr * k * t) * np.exp(-t / (dec * (1 if k == 1 else 0.5)))
            for k, amp, dec in [(1, 1.0, 0.8), (2.0, 0.3 * bright, 0.4), (3.01, 0.14 * bright, 0.25), (4.17, 0.06 * bright, 0.15)] if fr * k < 12000)
    return fx.edge_fade(y, 2)


def pluck(m, dur=0.5, decay_s=0.18):
    fr, t = mtof(m), fx.time_axis(dur)
    y = sum((0.6 ** (k - 1)) / k * np.sin(2 * np.pi * fr * k * t) * np.exp(-t / (decay_s / k ** 0.7)) for k in range(1, 6))
    return fx.edge_fade(y, 1)


def bass(m, dur=1.0, decay_s=0.6):
    fr, t = mtof(m), fx.time_axis(dur)
    y = np.tanh(1.4 * (np.sin(2 * np.pi * fr * t) + 0.25 * np.sin(4 * np.pi * fr * t)))
    return y * np.exp(-t / decay_s) * env_ar(len(t), 0.01, 0.08)


def sub(m, dur, a_s=1.0, r_s=1.0):
    t = fx.time_axis(dur)
    return np.sin(2 * np.pi * mtof(m) * t) * env_ar(len(t), a_s, r_s)


def arp(notes, t0, t1, step, gain=-14, octave=12, voice=bell, pattern=(0, 2, 1, 3, 2, 1), pan=0.35, **kw):
    t, j = t0, 0
    while t < t1 - 0.05:
        mm = notes[pattern[j % len(pattern)] % len(notes)] + octave
        put("bell", voice(mm, **kw), t, gain - (2 if j % 2 else 0), pan * (1 if j % 2 else -1))
        t += step
        j += 1


def chord_seq(seq, t0, t1, cutoff=1300, gain=-6, bass_gain=-10, sub_gain=None):
    """seq: list of (notes, bass root) spread evenly over [t0, t1], overlapping slightly."""
    d = (t1 - t0) / len(seq)
    for k, (notes, root) in enumerate(seq):
        tt = t0 + k * d
        c = cutoff
        if isinstance(cutoff, tuple):   # one continuous sweep across the whole sequence
            c0, c1 = cutoff
            c = (c0 * (c1 / c0) ** (k / len(seq)), c0 * (c1 / c0) ** ((k + 1) / len(seq)))
        put("pad", pad(notes, d + 0.8, c, a_s=0.5 if k else 0.9, r_s=0.9), tt, gain)
        if root is not None:
            put("bass", bass(root, d + 0.3, 0.9), tt, bass_gain)
        if sub_gain is not None and root is not None:
            put("bass", sub(root - 12 if root > 40 else root, d + 0.6, 0.4, 0.6), tt, sub_gain)


# chord vocabulary (MIDI): D major / Lydian colours and D minor for danger
Dmaj9 = [50, 57, 64, 66, 69]; Gmaj7 = [43, 50, 59, 62, 66]; Em9 = [40, 50, 55, 59, 66]; Asus = [45, 52, 57, 59, 64]
Bm9 = [47, 54, 61, 62, 66]; Elyd = [52, 59, 64, 68, 71]; Dm = [50, 57, 62, 65]; Bb = [46, 53, 58, 62]; Gm = [43, 50, 55, 58]
A7sus = [45, 52, 55, 59, 62]; D6 = [50, 57, 62, 66, 71]

# ===================================================================== hook: wonder
H0, H1 = s("hook"), s("descent")
chord_seq([(Dmaj9, 38), (Gmaj7, 43)], H0, H1, cutoff=1200, gain=-8)
arp([62, 66, 69, 73, 76], H0 + 0.15, H1 - 0.3, BEAT / 2, gain=-17)

# ===================================================================== descent: bright above, then sinking into the dark
D0, D1, tDive = s("descent"), s("chemistry"), a("descent", "dive")
put("pad", pad([62, 69, 74, 78, 81], tDive - D0 + 0.8, 2600, a_s=0.1, r_s=0.7), D0, -9)     # the sunlit sky
put("bell", bell(86, 2.0), D0 + 0.05, -15, 0.3)
steps = [(Dmaj9, 38), ([48, 55, 62, 64, 67], 36), ([46, 53, 57, 62, 65], 34), ([45, 52, 57, 60, 64], 33)]   # D, C, Bb, A: sinking
chord_seq(steps, tDive, D1, cutoff=(1800, 420), gain=-7, bass_gain=-9, sub_gain=-12)
for i, (tw, mm) in enumerate([(a("descent", "twilight"), 81), (a("descent", "night"), 76), (a("descent", "forever"), 74)]):
    put("bell", bell(mm, 2.4, 0.7), tw, -15, (-0.3, 0.3, 0.0)[i])

# ===================================================================== chemistry: life makes light (Lydian lift)
C0, C1 = s("chemistry"), s("angler")
tSo, tMeet = a("chemistry", "so"), a("chemistry", "enzyme") + 0.06
chord_seq([(Dmaj9, 38), (Elyd, 40)], tSo - 0.15, tMeet, cutoff=(900, 2600), gain=-7, bass_gain=-10)
arp([62, 64, 66, 68, 69, 73], tSo, tMeet, BEAT / 4, gain=-18, pattern=(0, 1, 2, 3, 4, 5, 4, 2))
riser = fx.highpass(fx.noise(tMeet - tSo + 0.1, 3), 2500) * fx.swell(fx.n_samples(tMeet - tSo + 0.1), 0.98, 2.5)
put("perc", riser, tSo, -19)
put("pad", pad([62, 69, 74, 76, 81], C1 - tMeet + 0.6, 3000, a_s=0.02, r_s=0.6), tMeet, -6)      # the light: full chord hit
put("bell", bell(86, 2.2), tMeet + 0.02, -11)
put("bell", bell(93, 2.0), tMeet + 0.06, -14, 0.4)

# ===================================================================== angler: tense, then a hit on "Bad idea"
A0, A1, tB = s("angler"), s("hatchet"), a("angler", "bad")
put("pad", pad(Dm, tB - A0 - 0.1, 700, a_s=0.6, r_s=0.25, det=0.14), A0 - 0.1, -6)
put("bass", sub(38, tB - A0, 0.8, 0.2), A0, -9)
t = A0 + 0.4
for k in range(int((tB - 0.3 - t) / BEAT) + 1):                                     # slow heartbeat, a little faster near the end
    tt = t + k * BEAT * (1 - 0.02 * k)
    if tt > tB - 0.3:
        break
    put("perc", fx.thump(52, 0.3, drop=1.0, tau=0.08, click=0.1, seed=k), tt, -14)
    put("perc", fx.thump(48, 0.3, drop=1.0, tau=0.07, click=0.05, seed=k + 50), tt + 0.22, -19)
for i, mm in enumerate([62, 65, 69, 68]):                                            # creeping low plucks
    put("bell", pluck(mm - 12, 0.7, 0.25), a("angler", "dangles") + i * BEAT, -16, -0.3)
put("perc", fx.impact(44, 1.1, seed=7), tB + 0.12, -8)                              # the hit lands with the bite
put("pad", pad([38, 45, 50, 53], A1 - tB + 0.6, 500, a_s=0.02, r_s=0.6, det=0.2), tB + 0.12, -9)

# ===================================================================== hatchet: mystery, then magic on "vanishes"
T0_, T1_, tV = s("hatchet"), s("alarm"), a("hatchet", "vanishes")
chord_seq([(Gmaj7, 43), (Em9, 40), (Asus, 45)], T0_, tV, cutoff=1300, gain=-8)
arp([66, 69, 71, 74, 78], T0_ + 0.2, a("hatchet", "seen") - 0.2, BEAT / 2, gain=-18)
put("pad", pad(Dmaj9 + [76], T1_ - tV + 0.6, (1200, 3200), a_s=0.2, r_s=0.6), tV - 0.05, -8)
for i, mm in enumerate([81, 85, 88, 93]):
    put("bell", bell(mm, 1.6), tV + i * 0.09, -15, -0.4 + i * 0.27)

# ===================================================================== alarm: ostinato, doubling on "flash", a big shadow, the hit
L0, L1 = s("alarm"), s("colours")
tF, tL, tA = a("alarm", "flash") - 0.05, a("alarm", "likely"), a("alarm", "attacker") + 0.05
put("pad", pad(Dm, L1 - L0 + 0.4, 800, a_s=0.5, r_s=0.6, det=0.12), L0, -9)
t, k = L0 + 0.2, 0
while t < tA - 0.1:
    step = BEAT / 2 if t < tF else BEAT / 4
    put("bass", bass(38 if (k // 4) % 2 == 0 else 41, step * 1.4, 0.12), t, -10)
    t += step
    k += 1
put("pad", pad([26, 33, 38, 41], tA - tL + 0.3, (200, 900), a_s=1.2, r_s=0.2, det=0.25), tL, -7)   # something bigger
put("perc", fx.impact(42, 1.2, seed=8), tA, -8)
put("pad", pad([38, 45, 50], L1 - tA + 0.5, 450, a_s=0.02, r_s=0.5), tA, -10)

# ===================================================================== colours: blue wonder, then a sneaky walk
K0, K1, tBut = s("colours"), s("finale"), a("colours", "but") - 0.05
chord_seq([(Bm9, 35), (Gmaj7, 43)], K0, tBut, cutoff=1500, gain=-8)
arp([66, 69, 71, 73, 78], K0 + 0.1, tBut - 0.2, BEAT / 2, gain=-18)
sneak = [62, 65, 69, 68, 67, 65, 64, 65]                                             # pizzicato tiptoe in D minor
t, k = tBut + 0.1, 0
while t < K1 - 0.55:
    put("bell", pluck(sneak[k % len(sneak)] - 12, 0.4, 0.09), t, -13 - (3 if k % 2 else 0), -0.2 if k % 2 else 0.2)
    if k % 2 == 0:
        put("bass", bass(38 if (k // 8) % 2 == 0 else 34, 0.5, 0.18), t, -12)
    t += BEAT / 2
    k += 1
put("pad", pad([50, 53, 57, 62], K1 - tBut, 600, a_s=0.6, r_s=0.4, det=0.1), tBut, -12)
put("perc", fx.thump(60, 0.4, drop=1.5, tau=0.1, click=0.4, seed=9), K1 - 0.33, -11)

# ===================================================================== finale: open up and resolve to D major on the title
F0, tOn, tT = s("finale"), a("finale", "so") + 0.05, a("finale", "own") + 0.4
chord_seq([(Gmaj7, 43), (A7sus, 45)], F0, tOn, cutoff=(700, 1900), gain=-7, bass_gain=-9)
arp([62, 66, 69, 71, 73, 76], tOn, tT, BEAT / 4, gain=-17, pattern=(0, 1, 2, 3, 4, 5, 4, 3, 2, 1))
put("pad", pad([47, 54, 59, 62, 66], tT - tOn + 0.6, 2200, a_s=0.3, r_s=0.6), tOn, -8)          # Bm (vi) under the lights
put("bass", bass(35, tT - tOn + 0.3, 1.2), tOn, -9)
put("pad", pad(D6 + [78], FILM - tT + 0.2, (2400, 1200), a_s=0.05, r_s=1.6), tT, -5)             # D major on the title
put("bass", bass(38, FILM - tT, 2.5), tT, -7)
put("bass", sub(26, FILM - tT, 0.05, 1.5), tT, -10)
for i, mm in enumerate([74, 78, 81, 86, 90]):
    put("bell", bell(mm, 2.6), tT + i * 0.07, -13, -0.5 + i * 0.25)


def stereo_reverb(x, tail, mix, seed):
    return np.stack([fx.reverb(x[:, ch], tail=tail, mix=mix, seed=seed + ch, damp=5000)[: len(x)] for ch in range(2)], 1)


music = stereo_reverb(bus["pad"], 3.0, 0.4, 900) + stereo_reverb(bus["bell"], 2.2, 0.35, 910) * 0.9 + bus["bass"] * 0.8 + stereo_reverb(bus["perc"], 1.2, 0.2, 920) * 0.8
music = fx.highpass(music.T, 28, 2).T
fade = np.ones(N)
fade[-int(1.2 * SR):] = np.linspace(1, 0, int(1.2 * SR)) ** 2
music = fx.normalise(music * fade[:, None], 0.9)
wavfile.write(HERE.parent / "assets" / "music_dry.wav", SR, (music * 32767).astype(np.int16))
print("wrote music_dry.wav", round(N / SR, 2), "s")
