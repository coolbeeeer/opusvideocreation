"""Original score for the antibiotics film, synthesised from scratch (numpy + scipy). No samples, no reference audio.

Key: D minor / D Dorian, 100 BPM. Sections follow the narration:
  cold open (warm) -> inside the body (muffled) -> infection (pulsing, building) -> immune / "antibiotics" (lift to F major)
  -> science groove (Dm7 G7 Bbmaj7 C) -> burst hit -> machines (lighter) -> viruses (pizzicato) -> resistance (dark drone)
  -> resolution (Bbmaj7 F/A Gm7 D major) under the title.
Writes ../assets/music_dry.wav (stereo, undocked).
"""
from pathlib import Path

import numpy as np
from scipy import signal

import cues
import sound_effects as fx
from cues import FILM, s, w

HERE = Path(__file__).resolve().parent
SR = fx.SR
rng = np.random.default_rng(11)
BEAT = 0.6
GRID0 = 0.1
snap = lambda t: GRID0 + round((t - GRID0) / BEAT) * BEAT
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)
N = fx.n_samples(FILM)
bus = {k: np.zeros((N, 2)) for k in ["pad", "pluck", "bass", "drums", "fx"]}


def put(name, x, at, gain_db=0.0, pan=0.0):
    x = np.asarray(x, float)
    if x.ndim == 1:
        th = (pan + 1) * np.pi / 4
        x = np.stack([x * np.cos(th), x * np.sin(th)], 1) * np.sqrt(2)
    i = int(round(at * SR))
    if i >= N:
        return
    j = min(N, i + len(x))
    bus[name][i:j] += x[: j - i] * 10 ** (gain_db / 20)


def env_ar(n, a, r):
    e = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        e[:na] = np.linspace(0, 1, na) ** 1.5
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e


def pad(notes, dur, cutoff=1400.0, a=0.6, r=0.9, det=0.09):
    n = fx.n_samples(dur)
    t = fx.time_axis(dur)
    L = np.zeros(n)
    R = np.zeros(n)
    for m in notes:
        f = mtof(m)
        for d in (-det, 0.0, det):
            p0 = rng.random()
            L += signal.sawtooth(2 * np.pi * (f * 2 ** (d / 12) * t + p0))
            R += signal.sawtooth(2 * np.pi * (f * 2 ** ((d + 0.03) / 12) * t + p0 * 0.5))
    e = env_ar(n, a, r)
    L = fx.lowpass(L, cutoff, 2) * e
    R = fx.lowpass(R, cutoff, 2) * e
    return np.stack([L, R], 1) / (3 * len(notes))


def pluck(m, dur=0.7, bright=1.0, decay_s=0.32):
    f = mtof(m)
    t = fx.time_axis(dur)
    y = np.zeros_like(t)
    for k in range(1, 7):
        if f * k > 9000:
            break
        y += (bright ** (k - 1)) / k * np.sin(2 * np.pi * f * k * t) * np.exp(-t / (decay_s / k ** 0.7))
    y += fx.highpass(fx.noise(dur, int(m * 7)), 2000) * np.exp(-t / 0.004) * 0.15
    return fx.edge_fade(y, 1)


def bass(m, dur=0.5, decay_s=0.25):
    f = mtof(m)
    t = fx.time_axis(dur)
    y = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    y = np.tanh(1.5 * y) * np.exp(-t / decay_s) * env_ar(len(t), 0.005, 0.05)
    return y


def kick(seed=0):
    return fx.thump(52, 0.35, drop=2.2, tau=0.09, click=0.2, seed=seed)


def hat(seed=0, open_=False):
    d = 0.18 if open_ else 0.05
    return fx.highpass(fx.noise(d, seed), 7000) * fx.decay(fx.n_samples(d), 0.05 if open_ else 0.012)


def riser(dur, seed=0):
    n = fx.n_samples(dur)
    src = fx.noise(dur, seed)
    u = np.linspace(0, 1, n)
    y = np.zeros(n)
    hop = 2400
    for i in range(0, n, hop):
        lo = 300 + 4000 * u[i] ** 2
        y[i:i + hop] = fx.bandpass(src[max(0, i - 4000):i + hop], lo, lo * 2.2)[-min(hop, n - i):]
    return y * u ** 2


def chord_bed(t0, t1, notes, cutoff=1400.0, gain=-6.0, a=0.6, r=0.9):
    put("pad", pad(notes, t1 - t0 + r * 0.5, cutoff, a, r), t0, gain)


def arp(t0, t1, notes, step=BEAT / 4, pattern=(0, 2, 1, 3, 2, 1), gain=-14.0, bright=0.6, decay_s=0.3, pan_w=0.35, octave=12):
    t, k = snap(t0), 0
    while t < t1 - 0.05:
        if t >= t0 - 0.01:
            m = notes[pattern[k % len(pattern)] % len(notes)] + octave
            put("pluck", pluck(m, 0.7, bright, decay_s), t, gain + (-2 if k % 2 else 0), pan_w * (1 if k % 2 else -1))
        t += step
        k += 1


def bassline(t0, t1, root, step=BEAT / 2, gain=-8.0, decay_s=0.22, pattern=(0, 0, 12, 0)):
    t, k = snap(t0), 0
    while t < t1 - 0.05:
        if t >= t0 - 0.01:
            put("bass", bass(root + pattern[k % len(pattern)], step * 1.6, decay_s), t, gain)
        t += step
        k += 1


def drums(t0, t1, kick_every=2, hats=True, gain=-10.0):
    t, k = snap(t0), 0
    while t < t1 - 0.05:
        if t >= t0 - 0.01:
            if k % (2 * kick_every) == 0:
                put("drums", kick(k), t, gain)
            if hats:
                put("drums", hat(k + 99), t + BEAT / 2, gain - 9, 0.25)
        t += BEAT / 2
        k += 1


# chord shapes (MIDI)
D2, F2, G2, A2, Bb2, C3, D3 = 38, 41, 43, 45, 46, 48, 50
Dm9 = [50, 57, 64, 65]
Bbmaj7 = [46, 53, 57, 62]
Dm = [50, 57, 62, 65]
Gm = [43, 50, 58, 62]
Eb = [51, 55, 58, 63]
A7 = [45, 49, 52, 55]
F = [41, 48, 57, 60]
Dm7 = [50, 57, 60, 65]
G7 = [43, 50, 59, 65]
C = [48, 55, 60, 64]
Am7 = [45, 52, 55, 60]
Fmaj = [53, 57, 60, 65]
Bb = [46, 53, 58, 62]
Cmaj = [48, 52, 55, 60]
Dmaj = [38, 50, 57, 62, 66]
FA = [45, 53, 57, 60]
Gm7 = [43, 50, 53, 58]

# ---------------------------------------------------------------- 1. cold open (0 - 2.05): warm
chord_bed(0.0, 2.1, Dm9, cutoff=1300, gain=-5, a=0.35, r=0.5)
arp(0.4, 2.0, [62, 65, 69, 76], step=BEAT / 2, pattern=(0, 1, 2, 3, 2, 1), gain=-15, bright=0.5, decay_s=0.5)
put("fx", riser(0.95, 1), 1.1, -14)
# ---------------------------------------------------------------- 2. inside the body (2.05 - 5.3): muffled
chord_bed(2.05, s("infection") + 0.2, Bbmaj7, cutoff=650, gain=-3, a=0.15, r=0.7)
arp(2.3, 5.1, [58, 62, 65, 69], step=BEAT / 2, pattern=(0, 2, 1, 3), gain=-19, bright=0.3, decay_s=0.45)
for t in (3.9, 4.75):
    put("bass", bass(D2, 0.6, 0.3), t, -6)
put("fx", riser(0.5, 2), 4.85, -16)
# ---------------------------------------------------------------- 3. infection (line 1): pulsing, building
L1 = s("infection")
t_two, t_mil, t_us = w("one"), w("within", 2, L1), w("usually")
chord_bed(L1, t_mil, Dm, cutoff=1100, gain=-7)
bassline(L1 + 0.3, t_us, D2, gain=-10)
arp(L1 + 0.3, t_two, [62, 65, 69, 72], pattern=(0, 2, 1, 3), gain=-20, bright=0.45)
arp(t_two, t_mil, [62, 65, 69, 72], pattern=(0, 2, 1, 3, 2, 1, 0, 3), gain=-17, bright=0.55)
arp(t_two, t_mil, [69, 72, 74, 77], step=BEAT, pattern=(0, 1, 2, 1), gain=-19, bright=0.4, decay_s=0.5)
chord_bed(t_mil, t_us + 0.3, Bb, cutoff=1900, gain=-5, a=0.3)
arp(t_mil, t_us, [58, 62, 65, 70], pattern=(0, 1, 2, 3), gain=-15, bright=0.6)
put("fx", riser(t_us - t_mil, 3), t_mil, -13)
drums(t_mil, t_us, kick_every=1, hats=True, gain=-12)
# ---------------------------------------------------------------- 4. immune system -> antibiotics (line 2)
t_when, t_doc, t_ab = w("when"), w("doctors"), w("antibiotics")
L3 = s("compare")
chord_bed(t_us, t_when, Gm, cutoff=1300, gain=-7)
bassline(t_us, t_when, G2, step=BEAT, gain=-10, pattern=(0, 0, 7, 0))
arp(t_us, t_when, [62, 67, 70, 74], step=BEAT / 2, pattern=(0, 1, 2, 3), gain=-18)
chord_bed(t_when, t_doc, Eb, cutoff=1000, gain=-7)
bassline(t_when, t_ab, 39, step=BEAT, gain=-11, pattern=(0, 0))
chord_bed(t_doc, t_ab, A7, cutoff=1500, gain=-7, a=0.2)
arp(t_doc, t_ab, [57, 61, 64, 67], step=BEAT / 4, pattern=(0, 1, 2, 3), gain=-17, bright=0.6)
put("fx", riser(t_ab - t_doc, 4), t_doc, -15)
chord_bed(t_ab, L3 + 0.3, F, cutoff=2600, gain=-4, a=0.08)
put("bass", bass(F2, 1.4, 0.6), t_ab, -6)
arp(t_ab, L3, [65, 69, 72, 77], step=BEAT / 4, pattern=(0, 1, 2, 3, 2, 1), gain=-13, bright=0.75)
put("pluck", pluck(81, 1.2, 0.7, 0.6), t_ab, -10)
# ---------------------------------------------------------------- 5. science groove (lines 3-5)
t_leak, t_water, t_burst = w("springs"), w("water"), w("bursts")
prog = [Dm7, G7, Bbmaj7, C]
roots = [D2, G2, Bb2, C3]
t, k = snap(L3), 0
while t < t_leak - 0.3:
    t1 = min(t + 2 * BEAT, t_leak - 0.3)
    chord_bed(t, t1, prog[k % 4], cutoff=1700, gain=-8, a=0.1, r=0.4)
    bassline(t, t1, roots[k % 4], gain=-10, pattern=(0, 0, 12, 0))
    arp(t, t1, [x + 12 for x in prog[k % 4][1:]], pattern=(0, 1, 2, 1, 0, 2), gain=-18, bright=0.55)
    t, k = t1, k + 1
drums(L3 + 2 * BEAT, t_leak - 0.3, kick_every=2, hats=True, gain=-13)
put("pluck", pluck(86, 1.0, 0.6, 0.5), w("armour"), -14, 0.3)
put("pluck", pluck(81, 1.0, 0.6, 0.5), w("armour") + 0.15, -16, -0.3)
# leaks -> water -> burst: tension builds, then a hit
chord_bed(t_leak - 0.3, t_water, [46, 53, 57, 62], cutoff=1200, gain=-7, a=0.2, r=0.3)
chord_bed(t_water, t_burst, [45, 52, 56, 62], cutoff=1500, gain=-6, a=0.3, r=0.1)
put("fx", riser(t_burst - t_water + 0.1, 5), t_water - 0.1, -10)
tt = t_water
while tt < t_burst - 0.05:  # accelerating hits
    put("drums", hat(int(tt * 100), True), tt, -16)
    tt += max(0.06, 0.3 * (t_burst - tt) / (t_burst - t_water))
put("pad", pad([38, 45, 50, 53, 57, 62], 1.6, cutoff=3000, a=0.01, r=1.2), t_burst, -2)
put("bass", bass(26, 1.6, 0.7), t_burst, -2)
# ---------------------------------------------------------------- 6. machines (line 6): lighter
L6 = s("machines")
L7 = s("viruses")
prog2, roots2 = [Dm7, Am7, Bbmaj7, Am7], [D2, A2, Bb2, A2]
t, k = snap(L6 + 0.4), 0
while t < L7:
    t1 = min(t + 2 * BEAT, L7)
    chord_bed(t, t1, prog2[k % 4], cutoff=1200, gain=-10, a=0.15, r=0.4)
    bassline(t, t1, roots2[k % 4], step=BEAT, gain=-12, pattern=(0, 12))
    arp(t, t1, [x + 12 for x in prog2[k % 4][1:]], step=BEAT / 4, pattern=(0, 2, 1, 2), gain=-21, bright=0.4, decay_s=0.2)
    t, k = t1, k + 1
drums(L6 + 0.4, L7, kick_every=4, hats=True, gain=-16)
# ---------------------------------------------------------------- 7. viruses (line 7): pizzicato
L8 = s("resistance")
prog3, roots3 = [Fmaj, Bb, Cmaj, Fmaj], [F2, Bb2, C3, F2]
t, k = snap(L7 + 0.1), 0
while t < L8:
    t1 = min(t + 2 * BEAT, L8)
    chord_bed(t, t1, prog3[k % 4], cutoff=900, gain=-13, a=0.1, r=0.3)
    arp(t, t1, [x + 12 for x in prog3[k % 4]], step=BEAT / 2, pattern=(0, 2, 1, 3), gain=-14, bright=0.4, decay_s=0.09)
    bassline(t, t1, roots3[k % 4], step=BEAT / 2, gain=-12, decay_s=0.08, pattern=(0, 7, 12, 7))
    t, k = t1, k + 1
# ---------------------------------------------------------------- 8. resistance (line 8): dark
L9 = s("ending")
t_thats = w("that's")
put("pad", pad([26, 33, 38], L9 - L8 + 0.4, cutoff=500, a=1.5, r=0.6, det=0.15), L8, -2)
put("pad", pad([50, 51, 57], t_thats - L8, cutoff=900, a=2.5, r=0.3), L8 + 0.3, -9)
t = snap(L8)
while t < L9 - 0.2:
    put("bass", bass(D2, 0.5, 0.18), t, -10)
    t += BEAT
put("fx", riser(t_thats - L8 - 1.0, 6), L8 + 1.0, -18)
put("bass", bass(22, 2.5, 1.2), t_thats, -3)
put("pad", pad([46, 49, 53, 58], L9 - t_thats + 0.4, cutoff=1100, a=0.05, r=0.5), t_thats, -7)
# ---------------------------------------------------------------- 9. resolution + title
t_pres = w("prescribed")
t_ex = w("exactly")
t_title = L9 + cues.SCENE["ending"]["dur"] - 2.42
chord_bed(L9, t_pres, Bbmaj7, cutoff=1500, gain=-7, a=0.4)
chord_bed(t_pres, t_ex, FA, cutoff=1600, gain=-7)
chord_bed(t_ex, t_title, Gm7, cutoff=1700, gain=-7)
put("pad", pad(Dmaj, FILM - t_title, cutoff=2400, a=0.25, r=1.4), t_title, -4)
arp(L9, t_title, [62, 65, 69, 74], step=BEAT / 2, pattern=(0, 1, 2, 3), gain=-17, bright=0.5, decay_s=0.5)
for i, m in enumerate([74, 78, 81, 86]):
    put("pluck", pluck(m, 1.8, 0.5, 0.9), t_title + 0.2 + i * 0.12, -12, (-0.3, 0.3)[i % 2])
put("bass", bass(D2, 2.4, 1.0), t_title, -5)

# ---------------------------------------------------------------- mixdown
def stereo_reverb(x, tail, mix, seed):
    out = np.zeros((len(x), 2))
    for ch in range(2):
        out[:, ch] = fx.reverb(x[:, ch], tail=tail, mix=mix, seed=seed + ch, damp=4500)[: len(x)]
    return out


music = (stereo_reverb(bus["pad"], 2.4, 0.35, 900) * 1.0 + stereo_reverb(bus["pluck"], 1.8, 0.3, 910) * 0.9
         + bus["bass"] * 0.8 + bus["drums"] * 0.7 + stereo_reverb(bus["fx"], 1.5, 0.3, 920) * 0.7)
music = fx.highpass(music.T, 30, 2).T
fade = np.ones(N)
fade[-int(0.5 * SR):] = np.linspace(1, 0, int(0.5 * SR)) ** 2
music *= fade[:, None]
music = fx.normalise(music, 0.9)
from scipy.io import wavfile  # noqa: E402

wavfile.write(HERE.parent / "assets" / "music_dry.wav", SR, (music * 32767).astype(np.int16))
print("wrote music_dry.wav", music.shape[0] / SR, "s")
