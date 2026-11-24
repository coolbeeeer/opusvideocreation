"""Sound-effect cue sheet for "What Happens If You Fall Into a Black Hole?".

Every time comes from a narrated word or a scene start, using the same formulas as the scene animation
(compositions/<scene>.html), so sound and picture stay locked when the voice changes. The friend scene's ticking
clock uses cues.friend_time(), the same slowing-time keys as the picture, so its ticks spread out and drop in
pitch exactly as the clock hand slows. All sounds are synthesised from noise and sine waves (sound_effects.py plus
the recipes below). Writes ../assets/sfx_dry.wav.
"""
from pathlib import Path

import numpy as np
from scipy import signal

import cues
import sound_effects as fx
from cues import FILM, a, s

HERE = Path(__file__).resolve().parent
SR = fx.SR
m = fx.Mix(FILM)
rng = np.random.default_rng(11)
end = lambda scene: cues.SCENE[scene]["end"]


def add(sound, t, gain_db=0.0, pan=0.0):
    if t < 0:                                  # Mix.add cannot place a sound before 0 s; trim its head instead
        sound = sound[int(-t * SR):]
        t = 0.0
    if len(sound):
        m.add(sound, t, gain_db, pan)


def pop_word(t, n_words=1, stagger=0.14, base=520.0, gain=-14, pan=0.0, tag=False):
    """Sound for kit.show(): a soft whoosh as a banner grows (banners only), then one pop per word.
    Offsets match kit.js: words start 0.06 s (tags) / 0.16 s (banners) after show(), `stagger` apart."""
    first = t + (0.06 if tag else 0.16)
    if not tag:
        add(fx.whoosh(0.22, peak=0.6, lo=(700, 2200), hi=(2600, 8000), seed=int(t * 100)), t, gain - 6, pan)
    for k in range(n_words):
        add(fx.pop(base * (1.12 ** k), seed=int(t * 1000) + k), first + k * stagger, gain, pan)


def fade_io(x, fin, fout):
    x = np.array(x, float)
    a_, b_ = int(fin * SR), int(fout * SR)
    if a_:
        x[:a_] *= np.linspace(0, 1, a_)
    if b_:
        x[-b_:] *= np.linspace(1, 0, b_)
    return x


# ---------------------------------------------------------------- recipes for this film
def rumble(dur, cutoff=90.0, seed=0, peak=0.5, wobble=0.0):
    """A black hole's low presence: low-passed noise that swells, with an optional slow wobble."""
    t = fx.time_axis(dur)
    y = fx.lowpass(fx.noise(dur, seed), cutoff, 2) * fx.swell(len(t), peak, 1.2)
    if wobble:
        y *= 0.75 + 0.25 * np.sin(2 * np.pi * wobble * t)
    return fx.edge_fade(fx.normalise(y, 0.9), 80)


def sizzle(dur, seed=0):
    """The hot disk close up: a faint high hiss that flutters."""
    t = fx.time_axis(dur)
    y = fx.bandpass(fx.noise(dur, seed), 3000, 9000) * (0.7 + 0.3 * np.sin(2 * np.pi * 5.3 * t) * np.sin(2 * np.pi * 0.7 * t))
    return fx.edge_fade(fx.normalise(y, 0.6), 120)


def tick(f=2600.0, seed=0):
    """One clock tick: a tiny wooden click with a short ring."""
    t = fx.time_axis(0.07)
    y = np.sin(2 * np.pi * f * t) * fx.decay(len(t), 0.008) + 0.5 * fx.highpass(fx.noise(0.07, seed), 2000) * fx.decay(len(t), 0.004)
    return fx.edge_fade(fx.normalise(y, 0.8), 1)


def beep(f=1000.0, dur=0.12):
    t = fx.time_axis(dur)
    return fx.edge_fade(np.sin(2 * np.pi * f * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 2 * f * t)) * fx.swell(len(t), 0.05, 0.6), 6)


def quindar(f=2525.0, dur=0.25):
    """The radio tone NASA used to mark the start of a transmission."""
    t = fx.time_axis(dur)
    return fx.edge_fade(np.sin(2 * np.pi * f * t) * 0.8, 8)


def stretch(dur=1.0, seed=0):
    """A body pulled long: a rubbery tone gliding up an octave and a half, with a creak under it."""
    t = fx.time_axis(dur)
    f = 140 * 2 ** (1.5 * (t / dur) ** 1.4) * (1 + 0.03 * np.sin(2 * np.pi * 9 * t))
    y = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * fx.swell(len(t), 0.85, 1.2)
    y = fx.bandpass(y, 200, 2400) + 0.35 * fx.creak(dur, 120, seed)
    return fx.edge_fade(fx.normalise(y, 0.8), 15)


def wobble(dur=3.0, f0=180.0, rate=3.2, seed=0):
    """A noodle wobbling: a soft sine whose pitch swings up and down."""
    t = fx.time_axis(dur)
    f = f0 * (1 + 0.22 * np.sin(2 * np.pi * rate * t))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.55 + 0.45 * np.sin(2 * np.pi * rate * t + 1.2)) * fx.swell(len(t), 0.3, 0.8)
    return fx.edge_fade(fx.normalise(fx.lowpass(y, 900, 2), 0.7), 80)


def slurp(dur=0.6, seed=0):
    """A noodle sucked in: band noise whose band sweeps up, ending in a little pop."""
    n, t = fx.n_samples(dur), fx.time_axis(dur)
    src = fx.noise(dur, seed)
    out = np.zeros(n)
    for k, (lo, hi) in enumerate([(300, 700), (500, 1100), (800, 1700), (1200, 2600), (1800, 3800)]):
        w = np.clip(1 - np.abs(np.linspace(0, 4, n) - k), 0, 1)
        out += fx.bandpass(src, lo, hi) * w
    out *= fx.swell(n, 0.75, 1.4) * (0.6 + 0.4 * np.sin(2 * np.pi * 18 * t))
    p = fx.pop(900, 0.1, seed=seed + 1)
    out[-len(p):] += p * 0.9
    return fx.edge_fade(fx.normalise(out, 0.85), 4)


def puff(dur=0.35, seed=0):
    """A small thruster: a soft burst of hiss."""
    y = fx.bandpass(fx.noise(dur, seed), 900, 5000) * fx.decay(fx.n_samples(dur), 0.09)
    return fx.edge_fade(fx.normalise(y, 0.8), 3)


def freeze(dur=1.2, seed=0):
    """Time stops: a glassy chord that rings, then a soft click."""
    y = fx.chime((1568.0, 2093.0, 2637.0), dur, gap=0.025, seed=seed) * 0.8
    c = fx.clink(3200, 0.12, seed + 1)
    y[: len(c)] += c * 0.6
    return fx.normalise(y, 0.85)


def descend(dur=1.2, f0=600.0, f1=90.0):
    """A long downward glide: the sound of something slowing and reddening."""
    t = fx.time_axis(dur)
    y = fx.sine_sweep(dur, f0, f1) * fx.swell(len(t), 0.15, 1.0)
    return fx.edge_fade(fx.normalise(y, 0.7), 20)


def whistle(notes=(1046.5, 1318.5), dur=0.6):
    """A carefree two-note whistle."""
    out = np.zeros(fx.n_samples(dur * len(notes)))
    for k, f in enumerate(notes):
        t = fx.time_axis(dur)
        ff = f * (1 + 0.012 * np.sin(2 * np.pi * 6 * t)) * (1 + 0.04 * np.exp(-t / 0.05))
        y = np.sin(2 * np.pi * np.cumsum(ff) / SR) * fx.swell(len(t), 0.2, 1.0)
        i = int(k * dur * 0.8 * SR)
        out[i: i + len(y)] += y
    return fx.edge_fade(fx.normalise(fx.highpass(out, 500), 0.6), 10)


def buzzer(dur=0.35):
    t = fx.time_axis(dur)
    y = signal.square(2 * np.pi * 140 * t) * 0.5 + signal.square(2 * np.pi * 147 * t) * 0.5
    return fx.edge_fade(fx.normalise(fx.lowpass(y, 2200, 2) * fx.swell(len(t), 0.1, 0.5), 0.6), 8)


def glitch(dur=0.4, seed=0):
    """Digital breakage: a buzz gated into stutters, crushed to a few bits."""
    r = np.random.default_rng(seed)
    t = fx.time_axis(dur)
    y = signal.sawtooth(2 * np.pi * 220 * t) * 0.5 + fx.noise(dur, seed) * 0.5
    gate = np.repeat(r.random(int(dur * 40) + 1) > 0.45, int(SR / 40))[: len(t)]
    y = np.round(y * gate * 4) / 4                                          # bit-crush
    return fx.edge_fade(fx.normalise(fx.bandpass(y, 200, 6000), 0.7), 3)


# ---------------------------------------------------------------- ambience: a quiet bed, louder near black holes
add(fx.room_tone(FILM, seed=1, color=160), 0, -35)
add(fade_io(rumble(end("hook"), 80, 2, 0.8), 0.5, 0.3), 0, -23)                       # the hole below comes closer
add(fade_io(rumble(end("small") - s("small"), 95, 3, 0.5, wobble=0.3), 0.2, 0.4), s("small"), -22)
add(fade_io(sizzle(end("small") - s("small"), 4), 0.4, 0.4), s("small"), -35)
add(fade_io(rumble(end("giant") - s("giant"), 55, 5, 0.6), 0.3, 0.4), s("giant"), -20)  # the giant: deeper
add(fade_io(rumble(end("friend") - s("friend"), 70, 6, 0.5), 0.3, 0.4), s("friend"), -28)
add(fade_io(rumble(end("inside") - s("inside"), 60, 7, 0.7, wobble=0.6), 0.3, 0.2), s("inside"), -21)
add(fade_io(rumble(end("unknown") - s("unknown"), 45, 8, 0.6), 0.2, 0.4), s("unknown"), -21)

# ===================================================================== hook
add(fx.whoosh(2.4, peak=0.5, lo=(150, 700), hi=(700, 3000), seed=10), 0.0, -20)      # falling
pop_word(a("hook", "hole") - 0.05, 1, tag=True, base=600)                          # "?"
add(fx.thump(42, 0.9, drop=0.6, tau=0.35, click=0.1, seed=11), a("hook", "black") - 0.05, -14)   # the black hole looms
tDep = a("hook", "depends")
add(fx.whoosh(1.1, peak=0.6, lo=(120, 500), hi=(500, 2400), seed=12), tDep - 0.1, -15)            # pulling back
add(fx.impact(34, 1.6, seed=13), tDep + 0.45, -13)                                               # the giant appears
pop_word(a("hook", "big") - 0.05, 1, tag=True, base=640, pan=-0.3)                 # "Small"
pop_word(a("hook", "it", 2) - 0.05, 1, tag=True, base=420, pan=0.3)                # "Giant"

# ===================================================================== small
tTen, tSun = a("small", "ten"), a("small", "sun")
for i in range(10):                                                                 # ten suns pop in, rising
    add(fx.pop(520 * 2 ** (i / 12 * 1.4), 0.1, seed=20 + i), tTen - 0.05 + i * 0.1 + 0.05, -17, -0.6 + i * 0.13)
add(fx.sparkle(0.8, count=5, base=1800, seed=31), tSun - 0.05, -20)
tOut = a("small", "pulls") - 0.2
add(fx.whoosh(0.3, peak=0.3, lo=(800, 2500), hi=(2500, 7000), seed=32), tOut, -24)                # suns shrink away
add(fx.zip_(0.6, 160, 520, seed=33), a("small", "harder") - 0.1, -14, 0.4)          # the long pull on the feet
add(fx.zip_(0.18, 900, 1300, seed=34), a("small", "head") - 0.12, -18, 0.4)         # the short pull on the head
tSt, tNo, tSp = a("small", "stretched") - 0.2, a("small", "noodle") - 0.05, a("small", "spaghettification")
add(stretch(tNo - tSt + 0.25, seed=35), tSt, -12)                                   # stretched ...
add(fade_io(wobble(tSp + 0.9 - tNo, seed=36), 0.15, 0.3), tNo, -20)                 # ... into a wobbling noodle
add(fx.bubble(420, 0.18, seed=37), a("small", "astronomers") - 0.12, -15, -0.5)     # the astronomer's bubble
add(tick(2200, 38), a("small", "really") + 0.05, -18, -0.5)                          # chalk taps on "really"
add(tick(1900, 39), a("small", "really") + 0.25, -19, -0.5)
pop_word(tSp - 0.1, 1, gain=-12)                                                     # "Spaghettification"
add(slurp(0.6, seed=40), tSp + 0.5, -12)                                             # slurped into the hole
add(fx.thump(50, 0.6, drop=0.8, tau=0.2, click=0.15, seed=41), tSp + 1.0, -14)        # ... gulp

# ===================================================================== giant
pop_word(a("giant", "giant") - 0.05, 1, tag=True, base=440)                       # "Giant"
add(fx.bubble(500, 0.18, seed=50), a("giant", "like") - 0.1, -15, 0.5)              # the galaxy inset
add(fx.sparkle(1.2, count=6, base=1500, seed=51), a("giant", "center") - 0.1, -21, 0.5)
pop_word(a("giant", "galaxy") - 0.05, 2, tag=True, base=560, pan=0.4)              # "Milky Way"
tCross, tEv, tFeel = a("giant", "cross"), a("giant", "event"), a("giant", "feel")
add(fx.whoosh(tEv + 0.4 - (tCross - 0.5), peak=0.7, lo=(100, 500), hi=(500, 2600), seed=52), tCross - 0.5, -15)   # pushing in on the edge
pop_word(tEv - 0.08, 2, tag=True, base=480, pan=-0.3)                               # "Event horizon"
add(fx.zip_(0.5, 600, 1600, seed=53), tEv - 0.15, -22)                              # the dashed line draws on
add(fx.chime((1318.5, 1760.0), 1.6, gap=0.12, seed=54), tFeel - 0.25, -22)          # crossing: a soft shimmer, nothing more
add(whistle((1046.5, 1318.5), 0.42), tFeel - 0.05, -17, 0.3)                         # the astronaut whistles

# ===================================================================== friend
pop_word(a("friend", "friend") - 0.05, 2, tag=True, base=600, pan=-0.2)           # "Your friend"
add(quindar(2525, 0.22), a("friend", "watching") - 0.15, -22, 0.3)                  # radio tone
add(fx.machine(0.5, rate=24, seed=60), a("friend", "watching") - 0.05, -24, 0.3)    # the telescope's focus motor
add(fx.bubble(380, 0.22, seed=61), a("friend", "far") - 0.15, -15)                   # the view opens
local, S0, t_slow, t_froz = cues.friend_time()
t = 0.0                                                                             # the clock in the view: a tick every
k = 1                                                                               # half second of *your* time, as the
while t < cues.SCENE["friend"]["dur"]:                                              # friend sees it: they spread out and
    t += 1 / 240                                                                    # drop in pitch as time slows
    if local(t) >= k * 0.5:
        r = max(0.05, local.rate(t))
        if r > 0.08:
            add(tick(2600 * (0.35 + 0.65 * r), 62 + k), S0 + t, -15 - 6 * (1 - r))
        k += 1
add(descend(1.6, 520, 70), a("friend", "red") - 0.1, -18)                            # turning red
add(fx.whoosh(1.0, peak=0.3, lo=(200, 800), hi=(800, 2000), seed=63), a("friend", "fade") - 0.05, -26)
add(freeze(1.4, seed=64), S0 + t_froz, -13)                                         # frozen

# ===================================================================== inside
S5 = s("inside")
tSec = a("inside", "only") - 0.15
add(fx.bubble(560, 0.16, seed=70), S5 + 0.15, -17, -0.5)                             # the friend's view, small
pop_word(S5 + 0.25, 2, tag=True, base=700, pan=-0.5)                                # "Friend's view"
tt = 0.5
while S5 + tt < tSec - 0.2:                                                          # your clock: steady ticks
    add(tick(2600, 80 + int(tt * 10)), S5 + tt, -15, 0.45)
    tt += 0.5
tIn, tPath = a("inside", "inside"), a("inside", "every")
add(fx.rush(1.8, seed=71), tIn - 0.3, -19)                                           # light pouring in toward the centre
for i, (j, pan) in enumerate([(0.05, -0.6), (0.45, 0.6), (0.85, 0.0)]):            # three jets, three directions
    add(puff(0.4, seed=72 + i), tPath + j, -13, pan)
add(fx.sparkle(1.0, count=5, base=1200, seed=75), tPath - 0.05, -23)                # the paths appear
pop_word(a("inside", "center") - 0.08, 1, tag=True, base=520)                     # "Center"
for k in range(3):                                                                  # countdown beeps
    if tSec + k < end("inside"):
        add(beep(1100 if k == 0 else 1000), tSec + k + 0.02, -15)
add(fx.heartbeat([0.0, 0.62, 1.2, 1.74], end("inside") - tSec + 0.3, seed=76), tSec, -15)

# ===================================================================== unknown
S6 = s("unknown")
tQ, tLaws, tBreak = a("unknown", "nobody") - 0.1, a("unknown", "laws") - 0.15, a("unknown", "break") - 0.05
add(fx.whoosh(tQ - S6, peak=0.9, lo=(150, 600), hi=(600, 3500), seed=80), S6, -15)   # diving at the centre
pop_word(a("unknown", "there") - 0.05, 1, tag=True, base=440)                      # "Singularity"
add(fx.boing(0.5, 300, seed=81), tQ + 0.02, -13)                                     # "?"
for i in range(3):
    add(fx.pop(600 + 120 * i, 0.12, seed=82 + i), tLaws + 0.04 + i * 0.07, -16, (-0.4, 0.4, 0.0)[i])   # equations appear
add(glitch(0.4, seed=85), tBreak - 0.35, -16)                                        # they glitch ...
for i in range(3):                                                                  # ... crack ...
    add(fx.crunch(0.3, seed=86 + i), tBreak + i * 0.06, -14, (-0.4, 0.4, 0.0)[i])
    add(fx.snap(0.06, seed=89 + i), tBreak + i * 0.06, -15, (-0.4, 0.4, 0.0)[i])
add(descend(0.9, 900, 200), tBreak + 0.25, -21)                                       # ... and fall away

# ===================================================================== finale
pop_word(a("finale", "you") - 0.1, 1, tag=True, base=640, pan=-0.3)                # "Small"
pop_word(a("finale", "get") + 0.05, 1, tag=True, base=440, pan=0.3)                # "Giant"
add(buzzer(0.32), a("finale", "pick") - 0.05, -17, -0.3)                            # not that one
add(fx.chime((1318.5, 1760.0), 0.9, gap=0.06, seed=90), a("finale", "giant") - 0.08, -16, 0.3)   # that one
tOr = a("finale", "or") - 0.1
add(fx.whoosh(1.0, peak=0.6, lo=(150, 700), hi=(700, 3000), seed=91), tOr, -15)       # everything recedes
add(fade_io(fx.machine(2.2, rate=6, seed=92), 0.5, 1.0) * 0.6, tOr + 0.2, -27)        # the ship's soft engine
tT = a("finale", "friend") + 0.55
add(fx.whoosh(0.7, peak=0.9, lo=(150, 600), hi=(600, 2400), seed=93), tT - 0.4, -16)  # title
add(fx.chime((587.33, 880.0, 1174.66, 1760.0), 2.6, gap=0.08, seed=94), tT + 0.15, -12)
add(fx.sparkle(1.0, count=5, base=2400, seed=95), tT + 0.4, -20)

out = HERE.parent / "assets" / "sfx_dry.wav"
m.write(str(out), peak_db=-1.0)
print("wrote", out)
