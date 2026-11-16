"""Original score generated from scene moods (film.json "mood" per scene). No samples, no reference audio.

Moods: warm, tense, groove, playful, dark, resolve. Each scene gets its mood's chord loop; chords change on a
100 BPM beat grid. The last scene always resolves to its final chord and fades. For bespoke scoring
(hits on specific words, risers into a climax) see projects/antibiotics/audio/music.py, which adds those by hand.
Writes ../assets/music_dry.wav (stereo, not yet ducked; mix.py does that).
"""
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

import cues
import sound_effects as fx
from cues import FILM

HERE = Path(__file__).resolve().parent
SR = fx.SR
rng = np.random.default_rng(11)
BEAT = 0.6
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)
N = fx.n_samples(FILM)
bus = {k: np.zeros((N, 2)) for k in ["pad", "pluck", "bass", "drums"]}
snap = lambda t: round(t / BEAT) * BEAT


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


def pad(notes, dur, cutoff=1400.0, a=0.5, r=0.8, det=0.09):
    n, t = fx.n_samples(dur), fx.time_axis(dur)
    L, R = np.zeros(n), np.zeros(n)
    for m in notes:
        f = mtof(m)
        for d in (-det, 0.0, det):
            p0 = rng.random()
            L += signal.sawtooth(2 * np.pi * (f * 2 ** (d / 12) * t + p0))
            R += signal.sawtooth(2 * np.pi * (f * 2 ** ((d + 0.03) / 12) * t + p0 * 0.5))
    e = env_ar(n, a, r)
    return np.stack([fx.lowpass(L, cutoff, 2) * e, fx.lowpass(R, cutoff, 2) * e], 1) / (3 * len(notes))


def pluck(m, dur=0.7, bright=0.6, decay_s=0.32):
    f, t = mtof(m), fx.time_axis(dur)
    y = sum((bright ** (k - 1)) / k * np.sin(2 * np.pi * f * k * t) * np.exp(-t / (decay_s / k ** 0.7)) for k in range(1, 7) if f * k < 9000)
    return fx.edge_fade(y + fx.highpass(fx.noise(dur, int(m * 7)), 2000) * np.exp(-t / 0.004) * 0.15, 1)


def bass(m, dur=0.5, decay_s=0.25):
    f, t = mtof(m), fx.time_axis(dur)
    y = np.tanh(1.5 * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)))
    return y * np.exp(-t / decay_s) * env_ar(len(t), 0.005, 0.05)


# chord loops per mood: (chord notes, bass root)
MOODS = {
    "warm":    dict(prog=[([50, 57, 64, 65], 38), ([46, 53, 57, 62], 34)], cutoff=1300, arp=0.5 * BEAT, drums=False, bassstep=None),
    "tense":   dict(prog=[([50, 57, 62, 65], 38), ([46, 53, 58, 62], 34)], cutoff=1100, arp=0.25 * BEAT, drums=False, bassstep=0.5 * BEAT),
    "groove":  dict(prog=[([50, 57, 60, 65], 38), ([43, 50, 59, 65], 43), ([46, 53, 57, 62], 46), ([48, 55, 60, 64], 48)], cutoff=1700, arp=0.25 * BEAT, drums=True, bassstep=0.5 * BEAT),
    "playful": dict(prog=[([53, 57, 60, 65], 41), ([46, 53, 58, 62], 46), ([48, 52, 55, 60], 48), ([53, 57, 60, 65], 41)], cutoff=900, arp=0.5 * BEAT, drums=False, bassstep=0.5 * BEAT, short=True),
    "dark":    dict(prog=[([50, 51, 57], 26)], cutoff=800, arp=None, drums=False, bassstep=BEAT),
    "resolve": dict(prog=[([46, 53, 57, 62], 34), ([45, 53, 57, 60], 33), ([43, 50, 53, 58], 31), ([38, 50, 57, 62, 66], 38)], cutoff=2000, arp=0.5 * BEAT, drums=False, bassstep=None),
}

scenes = list(cues.SCENE.items())
for si, (name, sc) in enumerate(scenes):
    M = MOODS.get(sc.get("mood", "groove"), MOODS["groove"])
    t0, t1, last = sc["start"], sc["end"], si == len(scenes) - 1
    prog = M["prog"]
    step = max(2 * BEAT, (t1 - t0) / len(prog)) if (last and sc.get("mood") == "resolve") else 2 * BEAT
    t, k = t0, 0
    while t < t1 - 0.05:
        c1 = t1 if (last and k == len(prog) - 1) else min(t + step, t1)
        notes, root = prog[min(k, len(prog) - 1)] if last else prog[k % len(prog)]
        put("pad", pad(notes, c1 - t + 0.4, M["cutoff"], a=0.25 if k else 0.5, r=0.6), t, -6)
        if M["bassstep"]:
            b = snap(t)
            while b < c1 - 0.05:
                if b >= t - 0.01:
                    put("bass", bass(root, M["bassstep"] * 1.6, 0.08 if M.get("short") else 0.22), b, -9)
                b += M["bassstep"]
        else:
            put("bass", bass(root, c1 - t + 0.3, 0.9), t, -8)
        if M["arp"]:
            a, j = snap(t), 0
            while a < c1 - 0.05:
                if a >= t - 0.01:
                    m = notes[1:][(0, 2, 1, 3, 2, 1)[j % 6] % len(notes[1:])] + 12
                    put("pluck", pluck(m, 0.7, 0.55, 0.09 if M.get("short") else 0.3), a, -16 - (2 if j % 2 else 0), 0.35 * (1 if j % 2 else -1))
                a += M["arp"]
                j += 1
        if M["drums"]:
            d, j = snap(t), 0
            while d < c1 - 0.05:
                if d >= t - 0.01:
                    if j % 4 == 0:
                        put("drums", fx.thump(52, 0.35, drop=2.2, tau=0.09, click=0.2, seed=j), d, -10)
                    put("drums", fx.highpass(fx.noise(0.05, j + 99), 7000) * fx.decay(fx.n_samples(0.05), 0.012), d + BEAT / 2, -19, 0.25)
                d += BEAT / 2
                j += 1
        if sc.get("mood") == "dark":
            put("pad", pad([26, 33, 38], c1 - t + 0.4, 500, a=1.0, r=0.6, det=0.15), t, -3)
        t, k = c1, k + 1


def stereo_reverb(x, tail, mix, seed):
    return np.stack([fx.reverb(x[:, ch], tail=tail, mix=mix, seed=seed + ch, damp=4500)[: len(x)] for ch in range(2)], 1)


music = stereo_reverb(bus["pad"], 2.4, 0.35, 900) + stereo_reverb(bus["pluck"], 1.8, 0.3, 910) * 0.9 + bus["bass"] * 0.8 + bus["drums"] * 0.7
music = fx.highpass(music.T, 30, 2).T
fade = np.ones(N)
fade[-int(0.5 * SR):] = np.linspace(1, 0, int(0.5 * SR)) ** 2
music = fx.normalise(music * fade[:, None], 0.9)
wavfile.write(HERE.parent / "assets" / "music_dry.wav", SR, (music * 32767).astype(np.int16))
print("wrote music_dry.wav", round(N / SR, 2), "s; moods:", ", ".join(f"{k}={v.get('mood')}" for k, v in scenes))
