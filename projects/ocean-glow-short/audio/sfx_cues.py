"""Sound-effect cue sheet for "Why Most Animals in the Open Ocean Glow".

Every time comes from a narrated word or a scene start, using the same formulas as the scene animation
(compositions/<scene>.html), so sound and picture stay locked when the voice changes. All sounds are synthesised
from noise and sine waves (sound_effects.py plus the small recipes below). Writes ../assets/sfx_dry.wav.
"""
from pathlib import Path

import numpy as np

import cues
import sound_effects as fx
from cues import FILM, s, w

HERE = Path(__file__).resolve().parent
SR = fx.SR
m = fx.Mix(FILM)
rng = np.random.default_rng(5)


def a(scene, word, n=1):
    """Film time of the n-th `word` spoken at or after the start of `scene` (same rule as the scene's at())."""
    return w(word, n, s(scene))


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


# ---------------------------------------------------------------- recipes for this film
def glow_on(f=880.0, dur=0.7, seed=0):
    """A light switching on: a soft glassy swell that glides up a little, with a long tail."""
    t = fx.time_axis(dur)
    n = len(t)
    ph = 2 * np.pi * np.cumsum(f * (1 + 0.06 * t / dur)) / SR
    y = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3.01 * ph)) * fx.swell(n, 0.18, 1.4)
    return fx.edge_fade(fx.normalise(fx.reverb(y, tail=1.4, mix=0.4, seed=seed), 0.8), 5)


def beep(f=1200.0, dur=0.09):
    t = fx.time_axis(dur)
    return fx.edge_fade(np.sin(2 * np.pi * f * t) * fx.decay(len(t), 0.05), 2)


def ping(f=900.0, dur=1.2, seed=0):
    """Sonar-like ping with a watery tail."""
    t = fx.time_axis(dur)
    y = np.sin(2 * np.pi * f * t) * fx.decay(len(t), 0.25) + 0.3 * np.sin(2 * np.pi * f * 2.02 * t) * fx.decay(len(t), 0.12)
    return fx.normalise(fx.reverb(y, tail=1.0, mix=0.35, seed=seed), 0.8)[: len(t)]


def siren(dur=2.2, lo=760.0, hi=1020.0, rate=2.6):
    """A soft 'wee-woo': a sine that swaps between two pitches, with vibrato and a gentle swell."""
    t = fx.time_axis(dur)
    sw = 0.5 + 0.5 * np.tanh(6 * np.sin(2 * np.pi * rate * t / 2))
    f = (lo + (hi - lo) * sw) * (1 + 0.012 * np.sin(2 * np.pi * 7 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sin(ph) + 0.25 * np.sin(2 * ph)) * fx.swell(len(t), 0.12, 0.8)
    return fx.edge_fade(fx.normalise(fx.bandpass(y, 400, 5000), 0.8), 40)


def rumble(dur=2.0, cutoff=120.0, seed=0, peak=0.5):
    """Low pressure rumble that swells in and out."""
    y = fx.lowpass(fx.noise(dur, seed), cutoff, 2) * fx.swell(fx.n_samples(dur), peak, 1.2)
    return fx.edge_fade(fx.normalise(y, 0.9), 80)


def hum(dur=3.0, f=110.0, seed=0):
    """Glow hum for the lure: two close sines beating slowly, low-passed noise underneath."""
    t = fx.time_axis(dur)
    y = np.sin(2 * np.pi * f * t) + 0.7 * np.sin(2 * np.pi * (f * 1.006) * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    y += fx.lowpass(fx.noise(dur, seed), 300, 2) * 0.6
    return fx.edge_fade(fx.normalise(y * fx.swell(len(t), 0.2, 0.6), 0.7), 120)


def chomp(seed=0):
    """Jaws closing on prey: a snap, a body thump and a crunch."""
    y = np.zeros(fx.n_samples(0.6))
    for snd, g in [(fx.snap(0.08, seed), 1.0), (fx.thump(90, 0.4, drop=1.5, tau=0.06, click=0.6, seed=seed + 1), 0.9), (fx.crunch(0.3, seed + 2), 0.5)]:
        y[: len(snd)] += snd * g
    return fx.normalise(y, 0.95)


def descend_ting(f, seed=0):
    return fx.normalise(fx.reverb(fx.sine_sweep(0.35, f, f * 0.8) * fx.decay(fx.n_samples(0.35), 0.12), tail=0.9, mix=0.35, seed=seed), 0.8)


# ---------------------------------------------------------------- ambience under the whole film
add(fx.room_tone(FILM, seed=1, color=180), 0, -27)                                   # underwater hush
add(rumble(FILM, cutoff=70, seed=2, peak=0.5), 0, -30)                                # very low pressure bed
for k in range(int(FILM / 1.7)):                                                     # stray bubbles now and then
    add(fx.bubble(rng.uniform(220, 520), rng.uniform(0.08, 0.14), seed=100 + k), k * 1.7 + rng.uniform(0, 1.2), rng.uniform(-36, -30), rng.uniform(-0.7, 0.7))

# ===================================================================== hook
S0 = s("hook")
add(glow_on(1174.7, seed=1), S0 + 0.15, -20, -0.4)                                   # fish 1 lights up
add(glow_on(1318.5, seed=2), a("hook", "three") + 0.1, -21, 0.4)                     # fish 2
add(glow_on(1480.0, seed=3), a("hook", "four") + 0.02, -21, -0.3)                    # fish 3
pop_word(a("hook", "four") - 0.02, 4, gain=-15)                                     # "3 out of 4"
add(fx.boing(0.4, 420, seed=4), a("hook", "why") - 0.04, -15)                        # the "?"
tUp = s("descent") - 0.38
add(fx.whoosh(0.5, peak=0.85, lo=(300, 1200), hi=(1500, 7000), seed=5), tUp - 0.1, -14)   # lift toward the light

# ===================================================================== descent
S1, tDive = s("descent"), a("descent", "dive")
add(fx.highpass(fx.noise(tDive - S1 + 0.3, 6), 1500) * 0.15, S1, -24)                 # air and surf above the surface
add(fx.splash(1.0, seed=7), tDive - 0.06, -8)
add(fx.whoosh(0.55, peak=0.4, lo=(150, 700), hi=(700, 2500), seed=8), tDive - 0.25, -14)
for k in range(14):                                                                  # the splash bubbles
    add(fx.bubble(rng.uniform(260, 700), rng.uniform(0.08, 0.15), seed=200 + k), tDive + rng.uniform(0, 0.4), rng.uniform(-22, -16), rng.uniform(-0.5, 0.5))
for k in range(0, 46, 3):                                                            # the bubble trail, thinning out
    add(fx.bubble(rng.uniform(240, 480), 0.11, seed=260 + k), tDive + 0.3 + k * 0.14, -20 - k * 0.3, rng.uniform(-0.4, 0.4))
add(rumble(s("chemistry") - tDive, cutoff=90, seed=9, peak=0.85), tDive, -16)        # pressure builds as we sink
add(fx.pop(700, seed=10), tDive + 0.3, -22, -0.8)                                    # depth gauge appears
pop_word(a("descent", "twilight") - 0.05, 2, gain=-14)                              # "Twilight zone"
add(fx.sparkle(1.2, count=5, base=1500, seed=11), a("descent", "twilight"), -24, 0.3)
pop_word(a("descent", "night") - 0.05, 2, gain=-14, base=440)                       # "Midnight zone"
add(fx.snap(0.05, seed=12), s("chemistry") - 0.3, -26, 0.2)                         # the blink in the dark

# ===================================================================== chemistry
S2, tSo = s("chemistry"), a("chemistry", "so")
add(fx.sparkle(1.4, count=9, base=1700, seed=13), tSo - 0.05, -17)                  # lights come on in a wave
add(glow_on(1174.7, dur=1.0, seed=14), tSo - 0.05, -18)
tCut = a("chemistry", "by") - 0.08
add(fx.whoosh(0.7, peak=0.92, lo=(200, 900), hi=(1200, 7000), seed=15), tCut - 0.68, -12)   # dive into the photophore
add(glow_on(1568.0, dur=0.9, seed=16), tCut - 0.05, -16)
add(fx.whoosh(0.4, peak=0.5, seed=17), tCut + 0.05, -22, -0.6)                       # fuel slides in
add(fx.whoosh(0.4, peak=0.5, seed=18), tCut + 0.1, -22, 0.6)                         # enzyme slides in
pop_word(a("chemistry", "fuel") - 0.05, 1, tag=True, pan=-0.4)                      # "Fuel"
pop_word(a("chemistry", "enzyme") - 0.08, 1, tag=True, pan=0.4, base=600)           # "Enzyme"
tMeet = a("chemistry", "enzyme") + 0.06
add(fx.snap(0.08, seed=19), tMeet, -12)                                              # the enzyme closes on the fuel
add(fx.chime((1174.7, 1568.0, 2349.3), 1.6, gap=0.05, seed=20), tMeet + 0.05, -12)  # light!
add(fx.sparkle(0.8, count=8, base=2200, seed=21), tMeet + 0.08, -16)
pop_word(tMeet + 0.2, 1, tag=True, base=700)                                         # "Light!"

# ===================================================================== angler
S3 = s("angler")
add(hum(s("hatchet") - S3, f=98.0, seed=22), S3, -24)                                # the lure's glow hum
pop_word(a("angler", "anglerfish") + 0.1, 1, tag=True, pan=-0.3)                    # "Anglerfish"
pop_word(a("angler", "lure") - 0.05, 1, tag=True, pan=0.3, base=640)                # "Lure"
tIn = a("angler", "curious") - 0.2
add(fx.whoosh(0.5, peak=0.4, lo=(300, 1200), hi=(1200, 4000), seed=23), tIn, -21, 0.7)    # the curious one swims in
add(fx.bubble(620, 0.18, seed=24), a("angler", "closer") - 0.2, -15, 0.4)           # the little heart
tB = a("angler", "bad")
add(fx.thump(55, 0.6, drop=1.2, tau=0.2, click=0.1, seed=25), tB - 0.35, -16)        # the eye narrows
add(fx.whoosh(0.25, peak=0.7, lo=(200, 1000), hi=(1000, 5000), seed=26), tB - 0.12, -15)
add(chomp(27), tB + 0.12, -6)                                                        # CHOMP
add(fx.impact(50, 0.8, seed=28), tB + 0.14, -14)
add(fx.bubble(260, 0.22, seed=29), tB + 0.5, -16, 0.3)                               # the burp

# ===================================================================== hatchet
S4 = s("hatchet")
pop_word(a("hatchet", "hatchetfish") + 0.05, 1, tag=True)                           # "Hatchetfish"
add(glow_on(1318.5, dur=0.9, seed=30), a("hatchet", "lights") - 0.05, -15)          # the belly lights up
for i, f0 in enumerate([1760.0, 1568.0, 1318.5]):                                    # light drifting down from above
    add(descend_ting(f0, seed=31 + i), a("hatchet", "glow") - 0.1 + i * 0.08, -22, (-0.4, 0.0, 0.4)[i])
tS = a("hatchet", "seen") - 0.3
add(fx.whoosh(0.85, peak=0.5, lo=(150, 800), hi=(800, 3000), seed=34), tS, -15)      # camera pulls out
add(fx.whoosh(0.6, peak=0.4, lo=(120, 500), hi=(500, 1500), seed=35), tS + 0.05, -20, -0.5)  # the hungry fish swims up
add(fx.power_down(0.25, 900, seed=36), a("hatchet", "seen") + 0.05, -20)            # lights off: a dark shape
tLk = a("hatchet", "below")
add(beep(1320), tLk + 0.1, -17)                                                       # lock-on
add(beep(1320), tLk + 0.24, -17)
tV = a("hatchet", "vanishes")
add(glow_on(1568.0, dur=1.0, seed=37), tV - 0.05, -14)                               # lights on, the shape melts away
add(fx.sine_sweep(0.45, 900, 380) * fx.decay(fx.n_samples(0.45), 0.2), tV + 0.15, -20)   # target lost
add(fx.boing(0.4, 360, seed=38), tV + 0.3, -15, -0.4)                                 # "?"

# ===================================================================== alarm
S5, tG = s("alarm"), a("alarm", "grab")
add(fx.whoosh(0.45, peak=0.5, lo=(300, 1200), hi=(1200, 4000), seed=40), S5 + 0.1, -20, -0.6)
add(fx.snap(0.08, seed=41), tG, -12, -0.2)                                            # the bite
add(fx.squish(0.28, seed=42), tG + 0.02, -14, -0.2)
pop_word(a("alarm", "jellyfish") - 0.05, 2, tag=True)                               # "Atolla jellyfish"
tF = a("alarm", "flash") - 0.05
tL = a("alarm", "likely")
add(siren(tL - tF + 0.6), tF, -18)                                                   # the burglar alarm
for i in range(6):                                                                   # one ping per light ring
    add(ping(880, seed=43 + i), tF + i * 0.42, -22, 0.15)
pop_word(a("alarm", "burglar") - 0.05, 2, gain=-12)                                 # "Burglar alarm"
add(fx.whoosh(0.6, peak=0.4, seed=50), tL, -20, -0.6)                                 # the attacker backs off
add(rumble(2.0, cutoff=110, seed=51, peak=0.7), a("alarm", "calling") - 0.2, -11)    # something big approaches
add(fx.thump(40, 0.9, drop=0.8, tau=0.35, click=0.05, seed=52), a("alarm", "something") - 0.05, -13, 0.4)
pop_word(a("alarm", "bigger") - 0.05, 2, tag=True, base=440, pan=0.3)               # "Something bigger"
tE, tA = a("alarm", "eat") - 0.2, a("alarm", "attacker") + 0.05
add(fx.whoosh(tA - tE + 0.1, peak=0.85, lo=(150, 700), hi=(700, 3500), seed=53), tE - 0.05, -12)
add(chomp(54), tA, -6)                                                                # CHOMP
add(fx.impact(46, 0.9, seed=55), tA + 0.02, -13)

# ===================================================================== colours
S6 = s("colours")
add(fx.sparkle(1.4, count=7, base=1400, seed=60), S6 + 0.1, -20)                    # blue lights everywhere
add(fx.chime((1174.7, 1480.0), 1.2, gap=0.06, seed=61), a("colours", "blue") - 0.05, -20)
tGo = a("colours", "because") + 0.02
add(fx.snap(0.05, seed=62), tGo - 0.15, -18)                                         # the lamp clicks on
add(glow_on(587.3, dur=0.8, seed=63), tGo - 0.15, -20)
for i, (L, f0) in enumerate([(120, 330), (195, 392), (305, 494), (470, 587), (660, 740)]):
    d = L / 760
    add(fx.sine_sweep(d + 0.05, f0 * 2, f0 * 1.6) * fx.swell(fx.n_samples(d + 0.05), 0.2, 1.0), tGo, -27, -0.6 + i * 0.3)   # beam racing down
    add(descend_ting(f0 * 2, seed=64 + i), tGo + d, -21, -0.6 + i * 0.3)            # ... and swallowed by the water
pop_word(a("colours", "farthest") - 0.02, 1, tag=True, base=600, pan=0.4)           # "Farthest"
tBut = a("colours", "but") - 0.05
add(fx.whoosh(0.4, peak=0.3, seed=70), tBut, -22)                                     # beams fade
add(fx.whoosh(0.85, peak=0.45, lo=(100, 500), hi=(500, 1800), seed=71), tBut + 0.05, -16, -0.6)   # the dragonfish glides in
pop_word(a("colours", "dragonfish") + 0.05, 1, tag=True, pan=-0.5)                  # "Dragonfish"
tC = a("colours", "cheats")
add(fx.pop(392, 0.14, seed=72), tC - 0.05, -16, -0.4)                                 # sly two-note sting
add(fx.pop(330, 0.18, seed=73), tC + 0.12, -16, -0.4)
add(fx.snap(0.04, seed=74), tC + 0.35, -26, -0.4)                                     # blink
tRed = a("colours", "red") - 0.05
add(fx.thump(70, 0.5, drop=0.6, tau=0.25, click=0.3, seed=75), tRed, -16)            # red searchlight on
add(hum(1.8, f=73.4, seed=76), tRed, -21)
for i, f0 in enumerate([1568.0, 1760.0]):                                             # the shrimp hums along, oblivious
    t0 = a("colours", "prey") - 0.1 + i * 0.25
    add(fx.edge_fade(np.sin(2 * np.pi * f0 * fx.time_axis(0.22)) * fx.swell(fx.n_samples(0.22), 0.3, 1.0), 20), t0, -24, 0.5)
pop_word(a("colours", "can't") - 0.05, 3, tag=True, pan=0.3)                        # "Can't see red"
tSnap = s("finale") - 0.4
add(fx.creak(0.3, 140, seed=77), tSnap - 0.3, -18, -0.2)                             # the loose jaw drops open
add(fx.whoosh(0.2, peak=0.8, seed=78), tSnap - 0.08, -15)
add(chomp(79), tSnap + 0.07, -7)                                                      # CHOMP

# ===================================================================== finale
S7 = s("finale")
tO = a("finale", "ocean")
add(fx.whoosh(tO - S7 + 0.3, peak=0.8, lo=(120, 600), hi=(600, 3000), seed=80), S7 + 0.05, -14)   # long pull back
add(fx.highpass(fx.noise(FILM - tO, 81), 1800) * 0.12, tO - 0.2, -27)                 # the surface, far above
pop_word(a("finale", "never") - 0.05, 2, gain=-14)                                  # "No sunlight"
pop_word(a("finale", "reaches") + 0.05, 2, tag=True, base=640)                      # "Sunlit zone"
add(fx.zip_(0.5, 500, 1400, seed=82), a("finale", "most") - 0.05, -21, -0.8)        # bracket
tOn = a("finale", "so") + 0.05
spread = a("finale", "own") - tOn + 0.2
for k in range(26):                                                                  # the lights of the deep come on, bottom to top
    u = k / 25
    add(fx.drop_plink(1200 + 1600 * u, 0.06, seed=90 + k) * 0.8, tOn + u * spread * 0.9 + rng.uniform(0, 0.08), -22 + 3 * u, rng.uniform(-0.8, 0.8))
add(fx.sparkle(1.6, count=10, base=1800, seed=120), tOn + 0.2, -19)
tT = a("finale", "own") + 0.4
add(fx.whoosh(0.7, peak=0.9, lo=(150, 600), hi=(600, 2400), seed=121), tT - 0.4, -16)   # title
add(fx.chime((587.33, 880.0, 1174.66, 1760.0), 2.6, gap=0.08, seed=122), tT + 0.15, -11)
add(fx.sparkle(1.0, count=5, base=2400, seed=123), tT + 0.4, -19)

out = HERE.parent / "assets" / "sfx_dry.wav"
m.write(str(out), peak_db=-1.0)
print("wrote", out)
