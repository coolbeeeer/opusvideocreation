"""Original score for "The Bacteria That Moved Into Your Cells", synthesised in code (no samples, no reference audio).

The pulse is one footstep: the walk cycle is 1.15 s with two steps, so a beat is 0.575 s (about 104 BPM), and the
walking sections put their beats exactly on the heel strikes from assets/steps.json. F major for the walk and the
deal, D minor (Dorian) for the ancient sea, a busy arpeggio for the power plant, a music box for Mom, and the walking
theme again in the finale, resolving to F major on the title. Writes ../assets/music_dry.wav (stereo, not ducked;
mix.py does that).
"""
import json
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

import cues
import sound_effects as fx
from cues import FILM, s, w

HERE = Path(__file__).resolve().parent
SR = fx.SR
rng = np.random.default_rng(31)
STEPS = json.loads((HERE.parent / "assets" / "steps.json").read_text())
BEAT = STEPS["period"] / 2                       # one footstep
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)
N = fx.n_samples(FILM)
bus = {k: np.zeros((N, 2)) for k in ["pad", "bell", "bass", "perc"]}
a = lambda scene, word, n=1: w(word, n, s(scene))
end = lambda scene: cues.SCENE[scene]["end"]


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
    """Glassy, celesta-like tone: inharmonic partials with fast high decays."""
    fr, t = mtof(m), fx.time_axis(dur)
    y = sum(amp * np.sin(2 * np.pi * fr * k * t) * np.exp(-t / (dec * (1 if k == 1 else 0.5)))
            for k, amp, dec in [(1, 1.0, 0.8), (2.0, 0.3 * bright, 0.4), (3.01, 0.14 * bright, 0.25), (4.17, 0.06 * bright, 0.15)] if fr * k < 12000)
    return fx.edge_fade(y, 2)


def musicbox(m, dur=1.2):
    """A music-box tine: a pure tone with a bright, fast-decaying click of overtones."""
    fr, t = mtof(m), fx.time_axis(dur)
    y = np.sin(2 * np.pi * fr * t) * np.exp(-t / 0.6) + 0.4 * np.sin(2 * np.pi * fr * 4.0 * t) * np.exp(-t / 0.05) + 0.15 * np.sin(2 * np.pi * fr * 6.1 * t) * np.exp(-t / 0.03)
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


def shaker(dur=0.09, seed=0):
    return fx.edge_fade(fx.highpass(fx.noise(dur, seed), 6000, 2) * fx.swell(fx.n_samples(dur), 0.3, 1.5), 2)


def arp(notes, t0, t1, step, gain=-14, octave=12, voice=bell, pattern=(0, 2, 1, 3, 2, 1), pan=0.35, **kw):
    t, j = t0, 0
    while t < t1 - 0.05:
        mm = notes[pattern[j % len(pattern)] % len(notes)] + octave
        put("bell", voice(mm, **kw), t, gain - (2 if j % 2 else 0), pan * (1 if j % 2 else -1))
        t += step
        j += 1


def chords(seq, cutoff=1300, gain=-7, bass_gain=-10, sub_gain=None, a_s=0.5, r_s=0.9):
    """seq: list of (t0, t1, notes, bass root). Each pad overlaps the next a little."""
    for k, (t0, t1, notes, root) in enumerate(seq):
        c = cutoff[k] if isinstance(cutoff, list) else cutoff
        put("pad", pad(notes, t1 - t0 + 0.8, c, a_s=a_s if k else max(a_s, 0.6), r_s=r_s), t0, gain)
        if root is not None:
            put("bass", bass(root, t1 - t0 + 0.3, 0.9), t0, bass_gain)
            if sub_gain is not None:
                put("bass", sub(root - 12 if root > 40 else root, t1 - t0 + 0.6, 0.3, 0.6), t0, sub_gain)


def walking(t0, t1, grid0, roots, gain=-17):
    """The walking theme: plucked eighths on the step grid (beats = heel strikes), bass on every other step,
    a shaker between steps. roots: list of (from_time, bass note, pluck notes)."""
    t = grid0 + np.ceil((t0 - grid0) / (BEAT / 2)) * (BEAT / 2)
    k = int(round((t - grid0) / (BEAT / 2)))
    while t < t1 - 0.05:
        cur = [r for r in roots if r[0] <= t + 1e-6][-1]
        notes = cur[2]
        put("bell", pluck(notes[k % len(notes)], 0.45, 0.16), t, gain - (2.5 if k % 2 else 0), 0.25 if k % 2 else -0.25)
        if k % 4 == 0:
            put("bass", bass(cur[1], BEAT * 1.6, 0.35), t, -11)
        if k % 2 == 1:
            put("perc", shaker(0.08, seed=k), t, -27)
        t += BEAT / 2
        k += 1


# chord vocabulary (MIDI), F major and D minor
Fmaj9 = [53, 57, 60, 64, 67]; C6 = [48, 55, 60, 64, 69]; Dm9 = [50, 53, 57, 60, 64]; Bbmaj9 = [46, 50, 53, 57, 60]
Gm9 = [43, 50, 53, 57, 58]; C7sus = [48, 53, 55, 58, 62]; Am7 = [45, 52, 55, 60, 64]; F6 = [53, 57, 60, 62, 65]
Dm_add9 = [50, 52, 53, 57, 62]; A7sus = [45, 50, 52, 55, 59]
PENT = [65, 69, 72, 74, 72, 69]                  # F A C D C A: the walking figure

# ===================================================================== walk: a bright stroll, then the dive
W0, tDive, W1 = s("walk"), STEPS["walkDive"], end("walk")
chords([(W0, 2.3, Fmaj9, 41), (2.3, 4.6, C6, 36), (4.6, tDive + 0.4, Dm9, 38)], cutoff=1500, gain=-9, bass_gain=-13)
walking(W0, tDive + 0.1, 0.0, [(0, 41, PENT), (2.3, 36, [64, 67, 72, 74, 72, 67]), (4.6, 38, [62, 65, 69, 72, 69, 65])])
tCell = a("walk", "cell")
chords([(tDive, a("walk", "into", 2), Bbmaj9, 34), (a("walk", "into", 2), a("walk", "there") - 0.1, Gm9, 31)],
       cutoff=[(1600, 700), (900, 500)], gain=-8, bass_gain=-12, sub_gain=-15, a_s=0.2)
put("bell", bell(77, 2.2, 0.8), a("walk", "leg") + 0.1, -15, -0.3)
put("bell", bell(74, 2.2, 0.8), tCell + 0.1, -15, 0.3)
tThere, tTh = a("walk", "there") - 0.05, a("walk", "thousands")
put("pad", pad(Fmaj9 + [72], W1 - tThere + 0.4, (900, 2600), a_s=0.25, r_s=0.6), tThere, -8)   # there they are
put("bass", sub(29, W1 - tThere, 0.3, 0.5), tThere, -12)
for i, mm in enumerate([77, 81, 84, 88]):
    put("bell", bell(mm, 1.8), tThere + i * 0.07, -14, -0.45 + i * 0.3)
arp([72, 76, 77, 79, 81, 84], tTh, tTh + 0.75, BEAT / 4, gain=-16, pattern=(0, 1, 2, 3, 4, 5))  # thousands
riser = fx.highpass(fx.noise(1.0, 5), 2000) * fx.swell(fx.n_samples(1.0), 0.98, 2.6)
put("perc", riser, W1 - 0.95, -20)                                                    # into the past

# ===================================================================== origin: the ancient sea
O0, O1 = s("origin"), end("origin")
tB, tSw, tBut, tDig, tMv = a("origin", "bigger"), a("origin", "swallowed"), a("origin", "but"), a("origin", "digested"), a("origin", "moved")
put("bass", sub(26, tBut - O0 + 0.2, 0.2, 0.5), O0, -11)                              # a low D under everything
chords([(O0, tB - 0.1, Dm_add9, 38), (tB - 0.1, tSw + 0.2, Bbmaj9, 34), (tSw + 0.2, tBut - 0.3, Gm9, 31)],
       cutoff=[700, 900, 800], gain=-8, bass_gain=-12, a_s=0.15)
for i, (tw, mm) in enumerate([(a("origin", "billion"), 74), (tB, 70), (tSw + 0.25, 67)]):
    put("bell", bell(mm, 2.4, 0.7), tw, -15, (-0.3, 0.3, 0.0)[i])
climb = [50, 51, 52, 53, 54, 55]                                                      # tension: plucks climbing up to "digested"
for k, mm in enumerate(climb):
    put("bell", pluck(mm, 0.35, 0.1), tBut - 0.35 + k * (tDig - tBut + 0.3) / len(climb), -13, -0.2 if k % 2 else 0.2)
put("pad", pad([38, 45, 51, 56], tDig - tBut + 0.6, 600, a_s=0.3, r_s=0.15, det=0.18), tBut - 0.3, -10)
chords([(tMv - 0.15, O1 + 0.2, Fmaj9, 41)], cutoff=(900, 2000), gain=-8, bass_gain=-11, a_s=0.2)   # it moved in
for i, mm in enumerate([72, 76, 79]):
    put("bell", bell(mm, 2.0), tMv + i * 0.09, -15, -0.3 + i * 0.3)

# ===================================================================== deal: warm and bouncy
D0, D1, tHost, tLots = s("deal"), end("deal"), a("deal", "host"), a("deal", "lots")
chords([(D0, tHost - 0.1, Fmaj9, 41), (tHost - 0.1, tLots - 0.2, Bbmaj9, 34), (tLots - 0.2, D1, C7sus, 36)], cutoff=1500, gain=-9, bass_gain=-12)
walking(D0 + 0.1, D1 - 0.2, D0 + 0.1, [(0, 41, [65, 72, 69, 72]), (tHost - 0.1, 34, [65, 70, 74, 70]), (tLots - 0.2, 36, [67, 72, 70, 72])], gain=-19)
arp([65, 67, 69, 70, 72, 74, 76, 77], tLots - 0.1, tLots + 0.6, BEAT / 4, gain=-16, pattern=(0, 1, 2, 3, 4, 5, 6, 7))

# ===================================================================== proof: curious
P0, P1 = s("proof"), end("proof")
tDna, tWall, tSplit, tLike = a("proof", "dna"), a("proof", "wall"), a("proof", "split"), a("proof", "like")
chords([(P0, tDna - 0.1, Bbmaj9, 34), (tDna - 0.1, tWall - 0.1, C6, 36), (tWall - 0.1, tSplit - 0.1, Am7, 33), (tSplit - 0.1, tLike - 0.1, Dm9, 38),
        (tLike - 0.1, P1 + 0.1, F6, 41)], cutoff=1300, gain=-9, bass_gain=-12)
sneak = [62, 65, 69, 65, 64, 65, 67, 69]
t, k = P0 + 0.15, 0
while t < tLike - 0.15:
    put("bell", pluck(sneak[k % len(sneak)], 0.32, 0.08), t, -16 - (3 if k % 2 else 0), -0.2 if k % 2 else 0.2)
    t += BEAT / 2
    k += 1
for i, word in enumerate(["dna", "wall", "two"]):                                     # one rising bell per tick
    put("bell", bell([84, 88, 91][i], 1.4), a("proof", word) + 0.12, -15, 0.2)
for i, mm in enumerate([77, 81, 84, 89]):                                             # "="
    put("bell", bell(mm, 1.8), tLike - 0.1 + i * 0.06, -14, -0.4 + i * 0.27)

# ===================================================================== atp: the power plant, busy
A0, A1 = s("atp"), end("atp")
tAtp, tYou, tEvery = a("atp", "atp"), a("atp", "you"), a("atp", "every")
seq = [(A0, a("atp", "oxygen"), Dm9, 38), (a("atp", "oxygen"), tAtp + 0.6, Bbmaj9, 34), (tAtp + 0.6, tYou - 0.35, Fmaj9, 41),
       (tYou - 0.35, a("atp", "weight"), C6, 36), (a("atp", "weight"), tEvery, Dm9, 38), (tEvery, A1, Bbmaj9, 34)]
chords(seq, cutoff=1600, gain=-9, bass_gain=-12)
for t0, t1, notes, root in seq:                                                       # sixteenths + eighth bass
    arp(sorted(notes)[1:], t0, t1, BEAT / 4, gain=-19, octave=12, pattern=(0, 1, 2, 3, 2, 1, 3, 2))
    t = t0
    while t < t1 - 0.05:
        put("bass", bass(root + 12, BEAT * 0.6, 0.12), t, -15)
        t += BEAT / 2
for i, mm in enumerate([77, 81, 84]):
    put("bell", bell(mm, 1.6), tEvery + 0.9 + i * 0.07, -15, -0.3 + i * 0.3)        # a full day

# ===================================================================== mother: a music box
M0, M1 = s("mother"), end("mother")
tThanks, tMom = a("mother", "thanks"), a("mother", "mom")
chords([(M0, a("mother", "came"), Fmaj9, 41), (a("mother", "came"), a("mother", "mother") - 0.1, Am7, 33), (a("mother", "mother") - 0.1, tThanks - 0.35, Bbmaj9, 34),
        (tThanks - 0.35, M1 + 0.1, F6, 41)], cutoff=1100, gain=-10, bass_gain=-14)
tune = [77, 76, 72, 69, 72, 74, 72, 69, 70, 74, 77, 81]
for i, mm in enumerate(tune):
    tt = M0 + 0.1 + i * BEAT / 2
    if tt > tThanks - 0.4:
        break
    put("bell", musicbox(mm, 1.2), tt, -14, 0.25 if i % 2 else -0.25)
for i, mm in enumerate([81, 84, 89]):
    put("bell", musicbox(mm, 1.6), tMom - 0.05 + i * 0.08, -13, -0.3 + i * 0.3)       # thanks, Mom

# ===================================================================== finale: the walk again, resolving on the title
F0, tOut, tT = s("finale"), STEPS["finaleOut"], a("finale", "ago") + 0.25
grid = STEPS["finale"][0]["t"]
chords([(F0, tOut, Bbmaj9, 34), (tOut, a("finale", "deal"), Dm9, 38), (a("finale", "deal"), tT - 0.05, C7sus, 36)],
       cutoff=[(500, 1700), 1600, (1400, 2200)], gain=-8, bass_gain=-12, a_s=0.3)
walking(grid, FILM - 0.4, grid, [(0, 38, [62, 65, 69, 72, 69, 65]), (a("finale", "deal"), 36, [64, 67, 70, 72, 70, 67]), (tT - 0.05, 41, PENT)], gain=-17)
put("pad", pad(Fmaj9 + [72], FILM - tT + 0.2, (2400, 1300), a_s=0.05, r_s=1.6), tT, -5)          # F major on the title
put("bass", bass(41, FILM - tT, 2.5), tT, -8)
put("bass", sub(29, FILM - tT, 0.05, 1.5), tT, -11)
for i, mm in enumerate([72, 77, 81, 84, 89]):
    put("bell", bell(mm, 2.6), tT + i * 0.07, -13, -0.5 + i * 0.25)


def stereo_reverb(x, tail, mix, seed):
    return np.stack([fx.reverb(x[:, ch], tail=tail, mix=mix, seed=seed + ch, damp=5000)[: len(x)] for ch in range(2)], 1)


music = stereo_reverb(bus["pad"], 3.0, 0.4, 900) + stereo_reverb(bus["bell"], 2.0, 0.3, 910) * 0.9 + bus["bass"] * 0.8 + stereo_reverb(bus["perc"], 1.0, 0.2, 920) * 0.8
music = fx.highpass(music.T, 28, 2).T
fade = np.ones(N)
fade[-int(1.2 * SR):] = np.linspace(1, 0, int(1.2 * SR)) ** 2
music = fx.normalise(music * fade[:, None], 0.9)
wavfile.write(HERE.parent / "assets" / "music_dry.wav", SR, (music * 32767).astype(np.int16))
print("wrote music_dry.wav", round(N / SR, 2), "s")
