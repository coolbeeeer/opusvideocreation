"""Sound-effect cue sheet for "The Bacteria That Moved Into Your Cells".

Every time comes from a narrated word or a scene start, using the same formulas as the scene animation
(compositions/<scene>.html), so sound and picture stay locked when the voice changes. Footsteps come from
assets/steps.json, which audio/js_events.cjs computes with the same walk rig and speed keys as the picture.
All sounds are synthesised from noise and sine waves (sound_effects.py plus the small recipes below).
Writes ../assets/sfx_dry.wav.
"""
import json
from pathlib import Path

import numpy as np
from scipy import signal

import cues
import sound_effects as fx
from cues import FILM, s, w

HERE = Path(__file__).resolve().parent
SR = fx.SR
m = fx.Mix(FILM)
rng = np.random.default_rng(7)
STEPS = json.loads((HERE.parent / "assets" / "steps.json").read_text())


def a(scene, word, n=1):
    """Film time of the n-th `word` spoken at or after the start of `scene` (same rule as the scene's at())."""
    return w(word, n, s(scene))


def end(scene):
    return cues.SCENE[scene]["end"]


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
    """Linear fade-in and fade-out, in seconds."""
    x = np.array(x, float)
    n, a_, b_ = len(x), int(fin * SR), int(fout * SR)
    if a_:
        x[:a_] *= np.linspace(0, 1, a_)
    if b_:
        x[-b_:] *= np.linspace(1, 0, b_)
    return x


# ---------------------------------------------------------------- recipes for this film
def footstep(seed=0, grit=1.0):
    """A shoe on a gravel path: a soft heel thump, then a short crunch as the foot rolls flat."""
    r = np.random.default_rng(seed)
    y = np.zeros(fx.n_samples(0.26))
    th = fx.thump(r.uniform(90, 120), 0.14, drop=1.3, tau=0.028, click=0.3, seed=seed)
    y[: len(th)] += th * 0.9
    cr = fx.bandpass(fx.noise(0.13, seed + 1), 1100, 5200) * fx.decay(fx.n_samples(0.13), 0.035)
    for k in range(7):                                   # a few grains of gravel
        c = fx.highpass(fx.noise(0.008, seed + 10 + k), 2500) * fx.decay(fx.n_samples(0.008), 0.002)
        i = int(r.uniform(0.0, 0.09) * SR)
        j = min(len(cr), i + len(c))
        cr[i:j] += c[: j - i] * r.uniform(0.4, 1.0)
    i = int(0.035 * SR)
    y[i: i + len(cr)] += cr * 0.55 * grit
    return fx.edge_fade(fx.normalise(y, 0.9), 2)


def body_step(seed=0):
    """The same step heard from inside the leg: only a deep, muffled thud with a little room."""
    y = fx.lowpass(footstep(seed, grit=0.3), 260, 4)
    return fx.normalise(fx.reverb(fx.normalise(y, 0.9), tail=0.6, mix=0.3, seed=seed), 0.9)


def chirp(f0=3000.0, n=3, seed=0):
    """A small bird: two or three quick up-and-down whistles."""
    r = np.random.default_rng(seed)
    y = np.zeros(fx.n_samples(0.12 * n + 0.1))
    for k in range(n):
        d = 0.055 + r.uniform(0, 0.03)
        t = fx.time_axis(d)
        f = f0 * r.uniform(0.92, 1.08) * (1 + 0.4 * np.sin(np.pi * t / d))
        sgl = np.sin(2 * np.pi * np.cumsum(f) / SR) * fx.swell(len(t), 0.3, 1.0)
        i = int(k * r.uniform(0.08, 0.11) * SR)
        y[i: i + len(sgl)] += sgl
    return fx.edge_fade(fx.normalise(fx.highpass(y, 1500, 2), 0.7), 3)


def breeze(dur, seed=0):
    """Outdoor air: low-passed noise with slow gusts."""
    t = fx.time_axis(dur)
    y = fx.lowpass(fx.noise(dur, seed), 800, 2) * (0.65 + 0.35 * np.sin(2 * np.pi * 0.23 * t) * np.sin(2 * np.pi * 0.07 * t + 1))
    return fx.edge_fade(fx.normalise(y, 0.8), 200)


def glow_on(f=880.0, dur=0.7, seed=0):
    """A light switching on: a soft glassy swell that glides up a little, with a long tail."""
    t = fx.time_axis(dur)
    ph = 2 * np.pi * np.cumsum(f * (1 + 0.06 * t / dur)) / SR
    y = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3.01 * ph)) * fx.swell(len(t), 0.18, 1.4)
    return fx.edge_fade(fx.normalise(fx.reverb(y, tail=1.4, mix=0.4, seed=seed), 0.8), 5)


def poof(seed=0, dur=0.3):
    """A soft puff of smoke: low-passed noise that blooms and fades."""
    y = fx.lowpass(fx.noise(dur, seed), 1600, 2) * fx.swell(fx.n_samples(dur), 0.15, 1.6)
    return fx.edge_fade(fx.normalise(y, 0.8), 3)


def tick(seed=0):
    """A checkbox ticking: a pop and a small bright ding."""
    t = fx.time_axis(0.35)
    ding = (np.sin(2 * np.pi * 1760 * t) + 0.3 * np.sin(2 * np.pi * 3520 * t)) * fx.decay(len(t), 0.12)
    y = np.zeros(len(t))
    p = fx.pop(820, seed=seed)
    y[: len(p)] += p
    y += ding * 0.5
    return fx.edge_fade(fx.normalise(y, 0.85), 3)


def whirr(dur, f=88.0, seed=0):
    """A flagellum spinning: a quiet buzzy motor."""
    t = fx.time_axis(dur)
    y = fx.bandpass(signal.sawtooth(2 * np.pi * f * t * (1 + 0.04 * np.sin(2 * np.pi * 2.3 * t))), 200, 1400) * (0.7 + 0.3 * np.sin(2 * np.pi * 9 * t))
    return fx.edge_fade(fx.normalise(y, 0.6), 60)


def wobble(dur=0.9, f0=150.0, seed=0):
    """Something big and soft arriving: a low wobbling glide."""
    t = fx.time_axis(dur)
    f = f0 * (1 - 0.35 * t / dur) * (1 + 0.05 * np.sin(2 * np.pi * 6 * t))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * fx.swell(len(t), 0.35, 1.2)
    return fx.edge_fade(fx.normalise(fx.lowpass(y, 600, 2), 0.8), 20)


def swish(dur=1.1, seed=0):
    """A sperm's tail: fast, soft whips."""
    t = fx.time_axis(dur)
    y = fx.bandpass(fx.noise(dur, seed), 500, 2400) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * t)) ** 4
    return fx.edge_fade(fx.normalise(y, 0.7), 30)


def clock_ticks(dur=0.9, n=12, seed=0):
    """A dial spinning once: ticks that speed up and slow down."""
    y = np.zeros(fx.n_samples(dur + 0.1))
    for k in range(n):
        u = k / (n - 1)
        tt = dur * (0.5 - 0.5 * np.cos(np.pi * u))          # eased, like the dial
        c = fx.clink(2600 + 200 * (k % 2), 0.05, seed + k)
        i = int(tt * SR)
        y[i: i + len(c)] += c[: len(y) - i] * 0.7
    return fx.normalise(y, 0.8)


# ---------------------------------------------------------------- ambience
tDive = STEPS["walkDive"]
tOut = STEPS["finaleOut"]
park_end = tDive + 0.7
add(fade_io(breeze(park_end, seed=1), 0.6, 0.9), 0, -24)                              # the park: air ...
add(fade_io(fx.lowpass(fx.noise(park_end, 2), 150, 2), 0.6, 0.9) * 0.7, 0, -30)      # ... a distant city hum ...
for k, t0 in enumerate([0.45, 1.6, 2.9, 4.1]):                                       # ... and a few birds
    add(chirp(rng.uniform(2600, 3600), int(rng.integers(2, 4)), seed=10 + k), t0, -27, rng.uniform(-0.6, 0.6))
body = end("walk") - (tDive - 0.2)                                                   # inside the leg: blood rushing, a heartbeat
add(fade_io(fx.flow(body, seed=3), 0.7, 0.3), tDive - 0.2, -21)
add(fade_io(fx.heartbeat([0.2, 1.05, 1.9, 2.75, 3.6, 4.45], body, seed=4), 0.5, 0.4), tDive - 0.2, -18)
add(fade_io(fx.room_tone(end("origin") - s("origin"), seed=5, color=180), 0.4, 0.3), s("origin"), -26)   # the ancient sea
for k in range(5):
    add(fx.bubble(rng.uniform(240, 500), rng.uniform(0.08, 0.14), seed=20 + k), s("origin") + 0.6 + k * 1.35, -31, rng.uniform(-0.6, 0.6))
inside = end("mother") - s("deal")                                                   # inside cells: a soft, bubbly hush
add(fade_io(fx.room_tone(inside, seed=6, color=260), 0.3, 0.3), s("deal"), -28)
add(fade_io(fx.flow(tOut - s("finale") + 0.4, seed=7), 0.05, 0.5), s("finale"), -22)          # back inside the leg ...
add(fade_io(fx.heartbeat([0.05, 0.9], tOut - s("finale") + 0.5, seed=8), 0.02, 0.4), s("finale"), -19)
fin = FILM - (tOut - 0.5)
add(fade_io(breeze(fin, seed=9), 0.8, 1.6), tOut - 0.5, -24)                          # ... and out into the evening
add(fade_io(fx.lowpass(fx.noise(fin, 10), 150, 2), 0.8, 1.6) * 0.7, tOut - 0.5, -30)
for k, t0 in enumerate([tOut + 0.4, tOut + 2.2]):
    add(chirp(rng.uniform(2400, 3200), 2, seed=30 + k), t0, -29, rng.uniform(-0.6, 0.6))

# ---------------------------------------------------------------- footsteps (the near foot slightly left, the far foot right)
for k, st in enumerate(STEPS["walk"] + STEPS["finale"]):
    pan = -0.12 if st["foot"] == 0 else 0.12
    if st["rate"] >= 0.5:
        add(footstep(seed=100 + k), st["t"], -15 + 3 * (st["rate"] - 1), pan)
    else:                                                                            # during the dive: heard from inside
        add(body_step(seed=100 + k), st["t"], -16)

# ===================================================================== walk
pop_word(a("walk", "you") - 0.05, 1, tag=True)                                      # "You"
tIn = a("walk", "bacteria") - 0.08
add(fx.bubble(520, 0.16, seed=40), tIn, -15, 0.3)                                    # the bubble opens
add(fx.squish(0.26, 520, seed=41), tIn + 0.15, -21, 0.3)                             # wriggling bacteria
tMorph = a("walk", "former") - 0.05
add(poof(seed=42), tMorph, -16, 0.3)                                                 # poof ...
add(fx.sparkle(0.8, count=5, base=1700, seed=43), tMorph + 0.12, -19, 0.3)          # ... they are mitochondria now
add(fx.bubble(380, 0.12, seed=44), tDive - 0.45, -20, 0.3)                           # the bubble closes
add(fx.pop(700, 0.1, seed=45), tDive - 0.1, -17)                                     # the lens opens on the thigh
tLeg = a("walk", "leg") + 0.35
add(fx.whoosh(tLeg - tDive + 0.35, peak=0.8, lo=(150, 700), hi=(700, 4000), seed=46), tDive - 0.2, -13)   # dive into the leg
pop_word(a("walk", "leg") + 0.12, 1, tag=True)                                      # "Muscle"
t2, t3 = a("walk", "into", 2) + 0.05, a("walk", "cell") + 0.42
add(fx.whoosh(t3 - t2 + 0.2, peak=0.75, lo=(120, 500), hi=(500, 2600), seed=47), t2 - 0.1, -14)            # ... into a fibre
pop_word(a("walk", "muscle") - 0.12, 2, tag=True)                                   # "Muscle cells"
tWake = a("walk", "there") - 0.05
for k in range(6):                                                                   # eyes open, here and there
    add(fx.pop(1100 + 140 * k, 0.07, seed=50 + k), tWake + 0.05 + k * 0.05, -24, rng.uniform(-0.6, 0.6))
tTh = a("walk", "thousands")
for k in range(18):                                                                  # the ripple of pulses, centre outwards
    u = k / 17
    add(fx.drop_plink(1300 + 900 * u, 0.06, seed=60 + k) * 0.8, tTh + u * 0.6 + rng.uniform(0, 0.04), -23 + 2 * u, rng.uniform(-0.8, 0.8))
pop_word(a("walk", "mitochondria") - 0.08, 1, gain=-12)                             # "Mitochondria"
tCut = s("origin")
add(fx.whoosh(1.0, peak=0.96, lo=(200, 900), hi=(900, 6500), seed=80), tCut - 0.95, -14)    # into the past
add(fx.highpass(fx.noise(0.9, 81), 2500) * fx.swell(fx.n_samples(0.9), 0.97, 2.4), tCut - 0.85, -20)

# ===================================================================== origin
S1 = s("origin")
add(fx.impact(38, 1.4, seed=82), S1 + 0.02, -17)                                     # arriving two billion years ago
for k in range(8):
    add(fx.bubble(rng.uniform(260, 600), rng.uniform(0.08, 0.14), seed=83 + k), S1 + 0.1 + rng.uniform(0, 0.7), -24, rng.uniform(-0.5, 0.5))
pop_word(a("origin", "billion") - 0.1, 4)                                           # "~2 billion years ago"
add(whirr(1.9, seed=84), S1 + 0.1, -27)                                              # the bacterium swims
tB, tSw, tBa = a("origin", "bigger"), a("origin", "swallowed"), a("origin", "bacterium")
add(fx.whoosh(1.1, peak=0.55, lo=(80, 400), hi=(400, 1500), seed=85), tB - 0.6, -15, 0.5)   # the big cell drifts in
add(wobble(1.0, 150, seed=86), tB - 0.45, -17, 0.4)
add(fx.squish(0.3, 300, seed=87), tSw - 0.2, -16)                                    # a pocket opens
add(fx.gulp(0.42, seed=88), tSw + 0.3, -11)                                          # gulp
add(fx.squish(0.3, 240, seed=89), tBa - 0.05, -18)                                   # the pocket seals
add(fx.bubble(300, 0.2, seed=90), tBa + 0.1, -18)                                    # a bubble of membrane around it
tBut, tDig = a("origin", "but"), a("origin", "digested")
add(fx.scurry(0.6, rate=22, seed=91), tBut - 0.35, -22, 0.3)                         # the enzymes close in
for i in range(3):                                                                   # bite ... clank
    add(fx.snap(0.07, seed=92 + i), tDig + 0.05 + i * 0.03, -14, (0.3, 0.1, -0.1)[i])
    add(fx.clink(1900 + 260 * i, 0.22, seed=95 + i), tDig + 0.07 + i * 0.03, -16, (0.3, 0.1, -0.1)[i])
for i in range(3):                                                                   # ... and they bounce off
    add(fx.boing(0.42, 300 + 50 * i, seed=98 + i), tDig + 0.14 + i * 0.06, -16, (0.4, 0.15, -0.15)[i])
tMv = a("origin", "moved") - 0.1
add(fx.clunk(0.35, seed=101), tMv + 0.12, -15)                                       # the suitcase goes down
add(fx.chime((1046.5, 1318.5, 1568.0), 1.3, gap=0.05, seed=102), tMv + 0.2, -19)    # at home

# ===================================================================== deal
add(glow_on(660, 0.8, seed=110), a("deal", "shelter") - 0.1, -18)                    # the cosy bubble
pop_word(a("deal", "shelter") - 0.05, 1, tag=True)                                  # "Shelter"
pop_word(a("deal", "food") - 0.05, 1, tag=True, base=600)                           # "Food"
for i in range(8):                                                                   # each sugar is taken in
    add(fx.bubble(420 + 30 * i, 0.12, seed=111 + i), a("deal", "food") - 0.3 + i * 0.08 + 0.7, -21, 0.3)
tE, tL = a("deal", "energy"), a("deal", "lots")
for i in range(12):                                                                  # energy coins fly out
    add(fx.clink(2100 + 90 * i, 0.2, seed=120 + i), tE - 0.15 + i * 0.06, -19, rng.uniform(-0.6, 0.6))
pop_word(tE - 0.05, 1, tag=True, base=640)                                          # "Energy"
add(fx.squish(0.28, 380, seed=135), tL - 0.25, -16)                                  # the guest divides
add(fx.pop(600, 0.12, seed=136), tL + 0.2, -17)
for k in range(22):                                                                  # lots of it
    add(fx.clink(2300 + 70 * (k % 9), 0.2, seed=140 + k), tL - 0.12 + k * 0.035, -21, rng.uniform(-0.8, 0.8))
add(fx.sparkle(1.0, count=6, base=2000, seed=170), tL + 0.1, -21)

# ===================================================================== proof
pop_word(a("proof", "proof") - 0.1, 2)                                              # "The proof"
pop_word(a("proof", "mitochondria") - 0.02, 1, tag=True, pan=-0.3)                  # "Mitochondrion"
pop_word(a("proof", "mitochondria") + 0.28, 1, tag=True, base=600, pan=0.3)         # "Bacterium"
for i, word in enumerate(["dna", "wall", "two"]):                                    # the checklist: slide in, tick
    t0 = a("proof", word) - 0.05
    add(fx.whoosh(0.22, peak=0.5, lo=(600, 2000), hi=(2000, 6000), seed=180 + i), t0, -24, -0.3)
    add(tick(seed=183 + i), t0 + 0.17, -15)
add(fx.sparkle(0.9, count=5, base=1500, seed=190), a("proof", "dna") - 0.1, -19)    # the DNA rings light up
add(fx.zip_(0.3, 500, 1500, seed=191), a("proof", "wall") - 0.15, -20)              # the walls pull apart
add(fx.boing(0.35, 420, seed=192), a("proof", "wall") - 0.05, -22)
tSp = a("proof", "split") - 0.1
add(fx.squish(0.3, 360, seed=193), tSp + 0.2, -16, -0.4)                             # both divide
add(fx.squish(0.3, 420, seed=194), tSp + 0.25, -16, 0.4)
add(fx.pop(560, 0.1, seed=195), tSp + 0.7, -18, -0.4)
add(fx.pop(640, 0.1, seed=196), tSp + 0.75, -18, 0.4)
add(fx.chime((1318.5, 1760.0), 1.0, gap=0.08, seed=197), a("proof", "like") - 0.1, -16)   # "="

# ===================================================================== atp
tFood, tOx, tAtp = a("atp", "food"), a("atp", "oxygen"), a("atp", "atp")
tSwap = a("atp", "you") - 0.35
add(fade_io(fx.machine(tSwap - tFood + 0.2, rate=7, seed=200), 0.3, 0.4), tFood - 0.1, -26)   # the power plant runs
for i in range(7):
    add(fx.bubble(300 + 25 * i, 0.12, seed=201 + i), tFood - 0.35 + i * 0.1 + 0.85, -22, -0.4)   # food goes in
    add(fx.bubble(560 + 30 * i, 0.1, seed=210 + i), tOx - 0.35 + i * 0.1 + 0.85, -23, 0.4)      # oxygen goes in
for i in range(26):                                                                  # ATP pours out and is used
    t0 = tAtp - 0.3 + i * 0.09
    add(fx.clink(2000 + 60 * (i % 7), 0.16, seed=220 + i), t0, -25, rng.uniform(-0.4, 0.4))
    add(fx.pop(900 + 40 * (i % 5), 0.06, seed=250 + i), t0 + 0.8, -26, rng.uniform(-0.6, 0.6))
pop_word(tAtp - 0.05, 1, tag=True, base=640, pan=0.3)                               # "ATP"
pop_word(a("atp", "fuel") - 0.1, 2, tag=True, pan=-0.3)                             # "Cell fuel"
add(fx.thump(80, 0.35, drop=1.2, tau=0.07, click=0.2, seed=280), a("atp", "fuel") - 0.2, -16)   # the fibre contracts
add(fx.strain(0.35, wobble=12, seed=281), a("atp", "fuel") - 0.18, -24)
add(fx.whoosh(0.5, peak=0.5, seed=282), tSwap - 0.05, -18)                           # to the balance
tRec = a("atp", "recycle")
for i in range(26):                                                                  # coins rain onto the dish
    add(fx.clink(1500 + 45 * (i % 11), 0.18, seed=290 + i), tRec - 0.15 + i * 0.05 + 0.32, -19 + (i % 3), 0.4)
tOwn = a("atp", "own") - 0.25
add(fx.creak(1.2, 110, seed=320), tOwn + 0.05, -24)                                  # the beam swings level ...
add(fx.clunk(0.3, seed=321), tOwn + 1.25, -20)                                       # ... and settles
pop_word(a("atp", "weight") - 0.12, 3, gain=-13)                                    # "~your body weight"
pop_word(a("atp", "every") - 0.05, 2, gain=-14, base=600)                           # "every day"
add(clock_ticks(0.9, 12, seed=330), a("atp", "every"), -20)                         # the day dial turns once
add(fx.chime((1568.0,), 0.8, seed=331), a("atp", "every") + 0.9, -21)

# ===================================================================== mother
S5 = s("mother")
add(swish(1.1, seed=340), S5, -22)                                                   # the sperm swims down
pop_word(a("mother", "every") - 0.05, 1, tag=True, base=480)                        # "Dad's"
tC = a("mother", "came") - 0.05
for i, dt in enumerate([0.12, 0.2, 0.27, 0.33]):                                     # Dad's mitochondria vanish
    add(poof(seed=341 + i, dur=0.22), tC + dt, -20 - i, 0.1)
add(glow_on(784, 0.9, seed=346), a("mother", "mother") - 0.2, -17)                   # the egg glows
pop_word(a("mother", "mother") - 0.08, 2, tag=True)                                 # "Mom's egg"
tS = a("mother", "thanks") - 0.35
add(fx.whoosh(0.35, peak=0.6, seed=347), tS - 0.02, -19)                             # Mom and you
add(fx.pop(500, 0.12, seed=348), tS + 0.2, -18)
add(fx.bubble(760, 0.16, seed=349), a("mother", "mom") - 0.08, -15)                 # the heart
add(fx.sparkle(0.7, count=4, base=2100, seed=350), a("mother", "mom"), -22)

# ===================================================================== finale
S6 = s("finale")
add(fx.whoosh(tOut - S6 + 0.4, peak=0.8, lo=(120, 600), hi=(600, 3200), seed=360), S6, -13)   # out of the leg
add(fx.pop(640, 0.1, seed=361), tOut - 0.15, -19)                                    # the lens closes
add(fx.sparkle(1.6, count=9, base=1600, seed=362), a("finale", "deal") - 0.1, -20)  # lights in the legs
add(glow_on(523.3, 1.2, seed=363), a("finale", "deal") - 0.1, -24)
pop_word(a("finale", "billion") - 0.15, 3, tag=True)                                # "~2 billion years"
tT = a("finale", "ago") + 0.25
add(fx.whoosh(0.7, peak=0.9, lo=(150, 600), hi=(600, 2400), seed=364), tT - 0.4, -16)   # title
add(fx.chime((523.25, 783.99, 1046.5, 1568.0), 2.6, gap=0.08, seed=365), tT + 0.15, -11)
add(fx.sparkle(1.0, count=5, base=2400, seed=366), tT + 0.4, -19)

out = HERE.parent / "assets" / "sfx_dry.wav"
m.write(str(out), peak_db=-1.0)
print("wrote", out)
