"""Original score for "What Happens If You Fall Into a Black Hole?", synthesised in code (no samples, no reference audio).

80 BPM, D minor / D Dorian for the mystery, F Lydian for the wonder of the giant black hole, D major for the end.
The score follows the story and lands on narrated words: a celesta question over a deep pad, a tense ostinato for
the small black hole (ten rising notes for the ten suns, an upward glide for the stretch, a wobbly bass for the
noodle), wide warm chords for the giant one. In the friend's view the music itself slows and drops in pitch until it
stops (a tape-stop driven by the same slowing-time keys as the picture); "for you, time goes on" restarts the same
music box tune at normal speed. Then a descent toward the centre, a broken stutter on "break down", and a warm
resolution under the title. Writes ../assets/music_dry.wav (stereo, not ducked; mix.py does that).
"""
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

import cues
import sound_effects as fx
from cues import FILM, a, s

HERE = Path(__file__).resolve().parent
SR = fx.SR
rng = np.random.default_rng(41)
BEAT = 60 / 80
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)
N = fx.n_samples(FILM)
end = lambda scene: cues.SCENE[scene]["end"]


def new_bus():
    return {k: np.zeros((N, 2)) for k in ["pad", "bell", "bass", "perc"]}


bus = new_bus()


def put(name, x, at, gain_db=0.0, pan=0.0, b=None):
    b = b if b is not None else bus
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
    b[name][i:j] += x[: j - i] * 10 ** (gain_db / 20)


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
    for mm in notes:
        fr = mtof(mm)
        for d in (-det, 0.0, det):
            p0 = rng.random()
            L += signal.sawtooth(2 * np.pi * (fr * 2 ** (d / 12) * t + p0))
            R += signal.sawtooth(2 * np.pi * (fr * 2 ** ((d + 0.03) / 12) * t + p0 * 0.5))
    e = env_ar(n, a_s, r_s) / (3 * len(notes))
    if isinstance(cutoff, tuple):
        cs = np.geomspace(cutoff[0], cutoff[1], 5)
        u = np.linspace(0, 4, n)
        out = np.zeros((n, 2))
        for k in range(5):
            wk = np.clip(1 - np.abs(u - k), 0, 1)
            if wk.any():
                out += np.stack([fx.lowpass(L, cs[k], 2), fx.lowpass(R, cs[k], 2)], 1) * wk[:, None]
        return out * e[:, None]
    return np.stack([fx.lowpass(L, cutoff, 2) * e, fx.lowpass(R, cutoff, 2) * e], 1)


def bell(mm, dur=1.6, bright=1.0):
    """Celesta-like: inharmonic partials with fast high decays (the 'starlight' voice)."""
    fr, t = mtof(mm), fx.time_axis(dur)
    y = sum(amp * np.sin(2 * np.pi * fr * k * t) * np.exp(-t / (dec * (1 if k == 1 else 0.5)))
            for k, amp, dec in [(1, 1.0, 0.8), (2.0, 0.3 * bright, 0.4), (3.01, 0.14 * bright, 0.25), (4.17, 0.06 * bright, 0.15)] if fr * k < 12000)
    return fx.edge_fade(y, 2)


def musicbox(mm, dur=1.2):
    fr, t = mtof(mm), fx.time_axis(dur)
    y = np.sin(2 * np.pi * fr * t) * np.exp(-t / 0.6) + 0.4 * np.sin(2 * np.pi * fr * 4.0 * t) * np.exp(-t / 0.05) + 0.15 * np.sin(2 * np.pi * fr * 6.1 * t) * np.exp(-t / 0.03)
    return fx.edge_fade(y, 2)


def pluck(mm, dur=0.5, decay_s=0.18):
    fr, t = mtof(mm), fx.time_axis(dur)
    y = sum((0.6 ** (k - 1)) / k * np.sin(2 * np.pi * fr * k * t) * np.exp(-t / (decay_s / k ** 0.7)) for k in range(1, 6))
    return fx.edge_fade(y, 1)


def bass(mm, dur=1.0, decay_s=0.6):
    fr, t = mtof(mm), fx.time_axis(dur)
    y = np.tanh(1.4 * (np.sin(2 * np.pi * fr * t) + 0.25 * np.sin(4 * np.pi * fr * t)))
    return y * np.exp(-t / decay_s) * env_ar(len(t), 0.01, 0.08)


def sub(mm, dur, a_s=1.0, r_s=1.0):
    t = fx.time_axis(dur)
    return np.sin(2 * np.pi * mtof(mm) * t) * env_ar(len(t), a_s, r_s)


def wah_bass(mm, dur, rate=4.0):
    """The noodle's wobbly bass: a saw through a low-pass that opens and closes, pitch swaying."""
    t = fx.time_axis(dur)
    f = mtof(mm) * (1 + 0.04 * np.sin(2 * np.pi * rate * 0.5 * t))
    y = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * rate * t)
    lo, hi = fx.lowpass(y, 300, 2), fx.lowpass(y, 1400, 2)
    return (lo * (1 - lfo) + hi * lfo) * env_ar(len(t), 0.02, 0.1)


def glide(m0, m1, dur):
    """A string-like glissando: detuned saws sliding from note m0 to m1."""
    t = fx.time_axis(dur)
    f = mtof(m0) * (2 ** ((m1 - m0) / 12)) ** ((t / dur) ** 1.3)
    y = sum(signal.sawtooth(2 * np.pi * np.cumsum(f * 2 ** (d / 12)) / SR) for d in (-0.1, 0, 0.1)) / 3
    return fx.lowpass(y, 2200, 2) * env_ar(len(t), 0.2, 0.25)


def arp(notes, t0, t1, step, gain=-14, octave=12, voice=bell, pattern=(0, 2, 1, 3, 2, 1), pan=0.35, b=None, **kw):
    t, j = t0, 0
    while t < t1 - 0.05:
        mm = notes[pattern[j % len(pattern)] % len(notes)] + octave
        put("bell", voice(mm, **kw), t, gain - (2 if j % 2 else 0), pan * (1 if j % 2 else -1), b=b)
        t += step
        j += 1


def chords(seq, cutoff=1300, gain=-7, bass_gain=-10, sub_gain=None, a_s=0.5, r_s=0.9, b=None):
    """seq: list of (t0, t1, notes, bass root). Each pad overlaps the next a little."""
    for k, (t0, t1, notes, root) in enumerate(seq):
        c = cutoff[k] if isinstance(cutoff, list) else cutoff
        put("pad", pad(notes, t1 - t0 + 0.8, c, a_s=a_s if k else max(a_s, 0.6), r_s=r_s), t0, gain, b=b)
        if root is not None:
            put("bass", bass(root, t1 - t0 + 0.3, 0.9), t0, bass_gain, b=b)
            if sub_gain is not None:
                put("bass", sub(root - 12 if root > 40 else root, t1 - t0 + 0.6, 0.3, 0.6), t0, sub_gain, b=b)


# chord vocabulary (MIDI)
Dm9 = [50, 53, 57, 60, 64]; Bbmaj9 = [46, 50, 53, 57, 60]; Gm9 = [43, 50, 53, 57, 58]; A7sus = [45, 50, 52, 55, 59]
Fmaj9 = [53, 57, 60, 64, 67]; Fly = [53, 57, 59, 64, 67]; Cmaj7 = [48, 55, 59, 64]; Am9 = [45, 52, 55, 59, 60]
Dmaj9 = [50, 57, 61, 64, 66]; Gmaj7 = [43, 50, 55, 59, 62]; D69 = [50, 57, 62, 64, 66, 71]; Ccl = [50, 51, 56, 57, 61]
TUNE = [74, 77, 81, 79, 77, 74, 72, 74, 69, 72, 76, 74]                 # the "time" tune (music box), D Dorian

# ===================================================================== hook: a question in the dark
H0, H1 = s("hook"), end("hook")
tBlack, tDep = a("hook", "black"), a("hook", "depends")
chords([(H0, tDep - 0.1, Dm9, 38)], cutoff=[(500, 1400)], gain=-9, bass_gain=-14, sub_gain=-14, a_s=1.2)
arp([62, 65, 69, 72, 76], H0 + 0.3, tDep - 0.1, BEAT / 2, gain=-17, pattern=(0, 2, 1, 3, 2, 4))
put("bass", sub(26, 1.6, 0.02, 1.2), tBlack - 0.05, -9)                            # the black hole: a low hit
put("pad", pad(Bbmaj9 + [65], H1 - tDep + 1.0, (900, 2600), a_s=0.35, r_s=0.6), tDep + 0.3, -6)   # how big: a swelling chord
put("bass", sub(22, H1 - tDep + 0.6, 0.4, 0.5), tDep + 0.3, -10)
for i, mm in enumerate([74, 77, 81, 86]):
    put("bell", bell(mm, 1.8), tDep + 0.5 + i * 0.09, -15, -0.4 + i * 0.27)

# ===================================================================== small: tension, ten suns, a stretch and a noodle
S1, S2 = s("small"), end("small")
tTen, tSun, tPull = a("small", "ten"), a("small", "sun"), a("small", "pulls")
tSt, tNo, tSp = a("small", "stretched") - 0.2, a("small", "noodle") - 0.05, a("small", "spaghettification")
chords([(S1, tPull - 0.1, Dm9, 38), (tPull - 0.1, tSt, Gm9, 43)], cutoff=900, gain=-10, bass_gain=-13)
t, k = S1 + 0.1, 0
ost = [38, 38, 50, 38, 41, 38, 50, 43]
while t < tSt - 0.05:                                                              # a low, ticking ostinato
    put("bass", bass(ost[k % len(ost)] + (5 if t > tPull - 0.1 else 0), BEAT * 0.6, 0.14), t, -15)
    t += BEAT / 2
    k += 1
for i in range(10):                                                                 # ten suns, ten rising notes
    put("bell", bell([74, 76, 77, 79, 81, 82, 84, 86, 88, 89][i], 1.0, 0.8), tTen - 0.05 + i * 0.1 + 0.05, -17, -0.6 + i * 0.13)
put("pad", glide(50, 68, tNo - tSt + 0.3), tSt, -8)                                 # stretched: an upward glide
t, k = tNo, 0
while t < tSp + 0.45:                                                              # the noodle: a wobbly, slightly silly bass
    put("bass", wah_bass([38, 41, 43, 41, 38, 36][k % 6], BEAT * 0.95, rate=5.3), t, -13)
    put("bell", pluck([62, 65, 69, 65][k % 4], 0.35, 0.09), t + BEAT / 2, -18, 0.3 if k % 2 else -0.3)
    t += BEAT
    k += 1
for i, mm in enumerate([74, 77, 81, 86]):                                         # "Spaghettification": a little fanfare
    put("bell", pluck(mm, 0.6, 0.2), tSp - 0.05 + i * 0.08, -14, -0.3 + i * 0.2)
put("pad", pad(Dm9, S2 - tSp + 0.3, 1200, a_s=0.2, r_s=0.4), tSp, -12)

# ===================================================================== giant: wide and warm (F Lydian)
G0, G1 = s("giant"), end("giant")
tCross, tEv, tFeel = a("giant", "cross"), a("giant", "event"), a("giant", "feel")
seq = [(G0, a("giant", "galaxy"), Fly, 41), (a("giant", "galaxy"), tCross - 0.4, Cmaj7, 36), (tCross - 0.4, tFeel - 0.3, Am9, 33)]
chords(seq, cutoff=[1500, 1800, (1600, 3200)], gain=-8, bass_gain=-12, sub_gain=-15)
arp([65, 69, 71, 72, 76, 79], G0 + 0.2, tFeel - 0.4, BEAT, gain=-17, pattern=(0, 2, 4, 1, 3, 5))
riser = fx.highpass(fx.noise(tEv + 0.4 - (tCross - 0.4), 3), 2500) * fx.swell(fx.n_samples(tEv + 0.4 - (tCross - 0.4)), 0.95, 2.2)
put("perc", riser, tCross - 0.4, -22)
put("pad", pad([77, 81, 84, 88], G1 - tFeel + 0.8, 3000, a_s=0.5, r_s=0.6, det=0.05), tFeel - 0.3, -15)   # nothing happens: just a high shimmer

# ===================================================================== friend: the tune slows down, drops in pitch and stops
F0, F1 = s("friend"), end("friend")
fb = new_bus()                                                                     # drawn on its own bus, then time-warped
chords([(F0 - 0.1, F1 + 0.5, [50, 57, 62, 66], 38)], cutoff=1100, gain=-10, bass_gain=-15, b=fb)
for i in range(20):
    put("bell", musicbox(TUNE[i % len(TUNE)], 1.1), F0 + 0.15 + i * BEAT / 2, -14, 0.25 if i % 2 else -0.25, b=fb)
local, S0f, t_slow, t_froz = cues.friend_time()
i0, i1 = int(F0 * SR), int(F1 * SR)
tt = np.arange(i1 - i0) / SR
src = F0 + local(tt)                                                              # where the music would be on the friend's clock
rate = np.array([local.rate(x) for x in tt[::240]])
rate = np.interp(tt, tt[::240], rate)
for name in fb:
    for ch in range(2):
        warped = np.interp(src, np.arange(N) / SR, fb[name][:, ch])
        warped *= np.clip(rate * 3, 0, 1)                                          # fades as it freezes (no stuck DC)
        bus[name][i0:i1, ch] += warped
put("pad", pad([81, 86, 88], F1 - (S0f + t_froz) + 0.6, 2600, a_s=0.6, r_s=0.6, det=0.03), S0f + t_froz, -17)   # frozen: a thin high hold

# ===================================================================== inside: for you, time goes on; then the fall to the centre
I0, I1 = s("inside"), end("inside")
tIn, tCen, tSec = a("inside", "inside"), a("inside", "center"), a("inside", "only") - 0.15
put("pad", pad([50, 57, 62, 66], tIn - I0 + 0.6, 1100, a_s=0.3, r_s=0.5), I0, -10)
for i in range(int((tIn - 0.1 - I0) / (BEAT / 2))):                               # the same tune at normal speed
    put("bell", musicbox(TUNE[i % len(TUNE)], 1.1), I0 + 0.1 + i * BEAT / 2, -14, 0.25 if i % 2 else -0.25)
seq = [(tIn - 0.15, tIn + 0.9, Dm9, 38), (tIn + 0.9, tCen - 0.2, Bbmaj9, 36), (tCen - 0.2, tSec, Gm9, 34), (tSec, I1, A7sus, 33)]
chords(seq, cutoff=[1200, 1000, 900, (900, 2400)], gain=-8, bass_gain=-11, sub_gain=-14)
t, k = tIn - 0.15, 0
while t < I1 - 0.05:                                                              # a pulse that quickens toward the end
    put("bass", bass(26 + 12 * (k % 2 == 1), 0.35, 0.12), t, -14)
    t += BEAT / 2 * (0.6 if t > tSec else 1.0)
    k += 1
rise = fx.highpass(fx.noise(I1 - tSec + 0.1, 4), 1800) * fx.swell(fx.n_samples(I1 - tSec + 0.1), 0.98, 2.4)
put("perc", rise, tSec, -18)

# ===================================================================== unknown: a dissonant hush, a stutter, nothing
U0, U1 = s("unknown"), end("unknown")
tQ, tLaws, tBreak = a("unknown", "nobody") - 0.1, a("unknown", "laws") - 0.15, a("unknown", "break") - 0.05
put("pad", pad(Ccl, U1 - U0 + 0.6, (500, 1500), a_s=0.4, r_s=0.6, det=0.18), U0, -11)
put("bass", sub(26, U1 - U0, 0.3, 0.8), U0, -11)
sw = pad([62, 65, 69], tQ - U0 + 0.1, 2000, a_s=tQ - U0, r_s=0.05)              # a swell that ends on "Nobody knows"
put("pad", sw, U0, -12)
for i, mm in enumerate([81, 84, 86]):
    put("bell", bell(mm, 1.4, 0.6), tLaws + i * 0.12, -16, (-0.4, 0.4, 0.0)[i])
# "break down": the music stutters (a short slice repeated, crushed), then drops away
sl = int(0.11 * SR)
for name in ["pad", "bell"]:
    i0 = int(tBreak * SR)
    piece = bus[name][i0 - sl:i0].copy()
    for r in range(5):
        j = i0 + r * sl
        bus[name][j:j + sl] = np.round(piece * 6 * (1 - r * 0.15)) / 6
    bus[name][i0 + 5 * sl:int(U1 * SR)] *= 0.25
put("pad", glide(57, 38, 0.9), tBreak + 0.5, -14)

# ===================================================================== finale: pick a giant one; better, be the friend; resolve
E0 = s("finale")
tPick, tOr, tT = a("finale", "pick"), a("finale", "or") - 0.1, a("finale", "friend") + 0.55
chords([(E0, tPick - 0.1, Gmaj7, 43), (tPick - 0.1, tOr, Dmaj9, 38), (tOr, tT - 0.05, A7sus, 45)], cutoff=1500, gain=-9, bass_gain=-12)
t, k = E0 + 0.1, 0
while t < tT - 0.1:                                                               # light, happy plucks
    put("bell", pluck([62, 66, 69, 71, 69, 66][k % 6], 0.45, 0.14), t, -17 - (2 if k % 2 else 0), 0.25 if k % 2 else -0.25)
    t += BEAT / 2
    k += 1
for i, mm in enumerate([74, 78, 81]):
    put("bell", bell(mm, 1.2), a("finale", "giant") - 0.05 + i * 0.08, -15, -0.3 + i * 0.3)
for i in range(8):                                                                 # the time tune, resolved, as you become the friend
    put("bell", musicbox([74, 78, 81, 79, 78, 74, 76, 81][i], 1.2), tOr + 0.4 + i * BEAT / 2, -15, 0.25 if i % 2 else -0.25)
put("pad", pad(D69, FILM - tT + 0.2, (2400, 1200), a_s=0.05, r_s=1.6), tT, -5)    # D major on the title
put("bass", bass(38, FILM - tT, 2.5), tT, -8)
put("bass", sub(26, FILM - tT, 0.05, 1.5), tT, -11)
for i, mm in enumerate([74, 78, 81, 86, 90]):
    put("bell", bell(mm, 2.6), tT + i * 0.07, -13, -0.5 + i * 0.25)


def stereo_reverb(x, tail, mix, seed):
    return np.stack([fx.reverb(x[:, ch], tail=tail, mix=mix, seed=seed + ch, damp=5000)[: len(x)] for ch in range(2)], 1)


music = stereo_reverb(bus["pad"], 3.2, 0.42, 900) + stereo_reverb(bus["bell"], 2.4, 0.38, 910) * 0.9 + bus["bass"] * 0.8 + stereo_reverb(bus["perc"], 1.2, 0.2, 920) * 0.8
music = fx.highpass(music.T, 28, 2).T
fade = np.ones(N)
fade[-int(1.2 * SR):] = np.linspace(1, 0, int(1.2 * SR)) ** 2
music = fx.normalise(music * fade[:, None], 0.9)
wavfile.write(HERE.parent / "assets" / "music_dry.wav", SR, (music * 32767).astype(np.int16))
print("wrote music_dry.wav", round(N / SR, 2), "s")
