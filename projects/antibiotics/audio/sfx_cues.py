"""Sound-effect cue sheet for the 60 s antibiotics film.

Every cue is placed from the same word timings and scene formulas the animation uses,
so sounds stay in sync if the narration is re-recorded. Writes ../assets/sfx_dry.wav (stereo).
"""
import json
from pathlib import Path

import numpy as np

import cues
import sound_effects as fx
from cues import FILM, s, w

HERE = Path(__file__).resolve().parent
rng = np.random.default_rng(7)
m = fx.Mix(FILM)


def pop_word(t, n_words=1, stagger=0.14, base=520.0, gain=-14, pan=0.0, tag=False):
    """A banner/tag reveal: soft whoosh for the banner, then one pop per word."""
    first = t + (0.06 if tag else 0.16)
    if not tag:
        m.add(fx.whoosh(0.22, peak=0.6, lo=(700, 2200), hi=(2600, 8000), seed=int(t * 100)), t, gain - 6, pan)
    for k in range(n_words):
        m.add(fx.pop(base * (1.12 ** k), seed=int(t * 1000) + k), first + k * stagger, gain, pan)


# ===================================================================== OPEN (0 - 5.4)
m.add(fx.room_tone(2.2, seed=1, color=500), 0.0, -34)
m.add(fx.whoosh(0.7, peak=0.6, lo=(150, 600), hi=(600, 2000), seed=2), 0.85, -24, -0.2)      # hand moves
m.add(fx.whoosh(0.95, peak=0.97, lo=(200, 900), hi=(1800, 7000), seed=3), 1.12, -9)          # dive into the capsule
m.add(fx.gulp(seed=4), 1.93, -8)
m.add(fx.snap(seed=5), 2.1, -12)                                                              # capsule pops open
m.add(fx.thump(90, 0.3, drop=1.0, tau=0.05, seed=6), 2.1, -16)
m.add(fx.fizz(1.3, rate=70, seed=7), 2.15, -13)
m.add(fx.flow(1.5, seed=8), 2.05, -26)
pop_word(2.37, 1, tag=True, pan=-0.6)                                                         # "Stomach"
m.add(fx.whoosh(0.6, peak=0.55, lo=(120, 500), hi=(500, 1800), seed=9), 3.05, -12)          # through the gut wall
m.add(fx.squish(0.32, 300, seed=10), 3.3, -12)
m.add(fx.flow(2.2, seed=11), 3.35, -17)
m.add(fx.heartbeat([0.0, 0.85], 1.4, seed=12), 3.9, -9)
pop_word(3.87, 1, tag=True)                                                                   # "Bloodstream"
m.add(fx.whoosh(0.5, peak=0.85, lo=(200, 800), hi=(800, 3000), seed=13), 4.95, -14)

# ===================================================================== INFECTION (lines 1-2)
T0 = s("infection")
m.add(fx.room_tone(12.8, seed=20, color=260), T0, -32)
tCut = max(w("cut") + 0.02, T0 + 0.5)
m.add(fx.slice_(seed=21), tCut - 0.1, -6)
m.add(fx.squish(0.25, 500, seed=22), tCut + 0.02, -15)
for i in range(4):
    m.add(fx.bubble(700 + i * 140, seed=23 + i), tCut + 0.08 + i * 0.05, -24, (i - 1.5) * 0.2)
tIn = w("bacteria", 1, T0) - 0.15
for i in range(7):
    t = tIn + min(i, 5) * 0.1 + (0.1 if i == 6 else 0)
    m.add(fx.whoosh(0.35, peak=0.8, lo=(500, 1500), hi=(1500, 5000), seed=30 + i), t + 0.2, -24, -0.3 + i * 0.1)
    m.add(fx.squish(0.2, 380 + i * 30, seed=40 + i), t + 0.55, -19, -0.3 + i * 0.1)
pop_word(w("inside") - 0.1, 1, tag=True)                                                      # "Bacteria"
m.add(fx.whoosh(0.55, peak=0.6, lo=(200, 700), hi=(700, 2400), seed=50), w("one") - 0.3, -20)
t2, t4 = w("two") - 0.25, w("four") - 0.25
m.add(fx.zip_(0.4, 400, 1300, seed=51), t2, -21)
m.add(fx.bubble(420, 0.16, seed=52), t2 + 0.33, -12)
pop_word(w("two"), 1, tag=True, base=600)
for k in range(2):
    m.add(fx.zip_(0.4, 450 + k * 80, 1500, seed=53 + k), t4 + k * 0.02, -23, -0.3 + k * 0.6)
    m.add(fx.bubble(480 + k * 90, 0.16, seed=55 + k), t4 + 0.33 + k * 0.03, -13, -0.3 + k * 0.6)
pop_word(w("four"), 1, tag=True, base=680)
tMil = w("millions")
m.add(fx.whoosh(0.6, peak=0.7, lo=(200, 700), hi=(700, 2600), seed=60), w("within", 2, T0) - 0.1, -18)
for k in range(30):
    u = np.sqrt(rng.random())
    m.add(fx.bubble(300 + rng.random() * 700, 0.12, seed=61 + k), tMil - 0.35 + u * 0.8, -25 + rng.random() * 4, rng.uniform(-0.8, 0.8))
m.add(fx.scurry(1.6, rate=90, seed=95), tMil - 0.3, -20)
m.add(fx.strain(1.8, wobble=14, seed=96), tMil - 0.2, -27)
pop_word(tMil, 1, tag=True, base=440, gain=-12)                                                # "1,000,000+"
tUs = w("usually")
m.add(fx.squish(0.4, 220, seed=100), tUs + 0.05, -14, -0.4)
pop_word(w("immune"), 3, tag=True, stagger=0.14)                                               # "White blood cell"
for i in range(4):
    t = tUs + 0.55 + i * 0.36
    m.add(fx.gulp(0.32, seed=101 + i), t + 0.3, -17, -0.4)
tCant = w("can't")
m.add(fx.scurry(1.5, rate=70, seed=110), tCant - 0.2, -18, -0.2)
m.add(fx.squish(0.45, 180, seed=111), tCant + 0.25, -17, -0.3)
m.add(fx.pop(380, 0.16, seed=112), w("doctors"), -12, 0.6)                                    # inset bubble
m.add(fx.chime((660.0, 990.0), 1.2, seed=113), w("doctors") + 0.05, -24, 0.6)
tAb = w("antibiotics")
m.add(fx.whoosh(1.0, peak=0.5, lo=(300, 1200), hi=(1500, 6000), seed=114), tAb - 0.4, -14)
m.add(fx.fizz(1.2, rate=50, seed=115), tAb - 0.3, -17)
pop_word(tAb - 0.05, 1, gain=-11, base=480)                                                    # "Antibiotics" banner

# ===================================================================== COMPARE (line 3)
T0 = s("compare")
m.add(fx.room_tone(3.4, seed=120, color=400), T0, -33)
m.add(fx.whoosh(0.45, peak=0.7, lo=(300, 1000), hi=(1000, 3500), seed=121), T0, -20, -0.5)
m.add(fx.whoosh(0.45, peak=0.7, lo=(300, 1000), hi=(1000, 3500), seed=122), T0 + 0.05, -20, 0.5)
pop_word(w("bacteria", 1, T0) - 0.05, 1, tag=True, pan=0.4)
pop_word(w("differently"), 2, tag=True, pan=-0.4)
m.add(fx.clink(3200, 0.3, seed=123), w("differently"), -18, 0.4)
m.add(fx.whoosh(0.45, peak=0.95, lo=(200, 900), hi=(1500, 6000), seed=124), s("wall") - 0.42, -12, 0.3)

# ===================================================================== WALL (lines 4-5)
T0 = s("wall")
m.add(fx.room_tone(12.2, seed=130, color=350), T0, -32)
tWall = w("wall", 1, T0)
m.add(fx.whoosh(0.8, peak=0.75, lo=(200, 800), hi=(900, 3500), seed=131), tWall - 0.55, -16)
pop_word(tWall + 0.2, 2, tag=True, pan=-0.4)                                                   # "Cell wall"
tJam = [w("jams"), w("tools"), w("build")]
workFrom = tWall - 0.2
for i, tj in enumerate(tJam):
    t, k = workFrom + i * 0.17, 0
    while t < tj - 0.45:
        m.add(fx.clink(1900 + 260 * i + 90 * (k % 3), 0.18, seed=140 + i * 40 + k), t + 0.08, -23, (i - 1) * 0.5)
        t += 0.55
        k += 1
m.add(fx.machine(tJam[0] - workFrom, rate=3.6, seed=200) * 0.5, workFrom, -27)
tA = w("armour") - 0.05
m.add(fx.clink(2600, 0.5, seed=201), tA, -15)
m.add(fx.sparkle(0.6, count=3, base=2600, seed=202), tA + 0.05, -22)
m.add(fx.pop(420, 0.16, seed=203), w("your", 1, T0) - 0.12, -13, 0.6)                          # inset
pop_word(w("don't") - 0.05, 2, tag=True, pan=0.6)                                               # "No wall"
tP = w("penicillin")
pop_word(tP - 0.05, 1, gain=-11, base=500)                                                     # "Penicillin"
m.add(fx.whoosh(1.0, peak=0.4, lo=(400, 1500), hi=(1500, 5000), seed=204), tP, -17, -0.4)
for i, tj in enumerate(tJam):
    m.add(fx.whoosh(0.6, peak=0.85, lo=(500, 1500), hi=(1500, 5000), seed=205 + i), tj - 0.62, -22, (i - 1) * 0.5)
    m.add(fx.clunk(seed=210 + i), tj, -8, (i - 1) * 0.5)
    m.add(fx.power_down(0.45, 600 - i * 60, seed=215 + i), tj + 0.06, -19, (i - 1) * 0.5)
pop_word(w("tools") - 0.05, 2, tag=True)                                                       # "Wall builders"
tL = w("springs") - 0.1
m.add(fx.creak(1.0, 110, seed=220), tL, -12)
for k in range(9):
    m.add(fx.snap(0.08, seed=221 + k), tL + 0.06 + (k % 7) * 0.04 + k * 0.01, -19, rng.uniform(-0.6, 0.6))
m.add(fx.whoosh(0.8, peak=0.6, lo=(200, 700), hi=(700, 2500), seed=231), w("leaks") - 0.3, -18)
for i in range(9):
    m.add(fx.squish(0.16, 520 + i * 40, seed=232 + i), w("leaks") - 0.1 + i * 0.05, -21, rng.uniform(-0.7, 0.7))
tW, tB = w("water") - 0.1, w("bursts")
m.add(fx.rush(tB - tW + 0.1, seed=245), tW, -9)
m.add(fx.creak(tB - tW, 80, seed=246), tW + 0.2, -14)
m.add(fx.strain(tB - tW, wobble=6, seed=247), tW + 0.1, -18)
# the burst
m.add(fx.impact(42, 1.4, seed=250), tB, 0)
m.add(fx.splash(1.0, seed=251), tB + 0.01, -3)
m.add(fx.crunch(0.4, seed=252), tB, -8)
m.add(fx.pop(300, 0.2, seed=253), tB, -6)
m.add(fx.thunder(1.2, seed=254), tB + 0.02, -12)

# ===================================================================== MACHINES (line 6)
T0 = s("machines")
m.add(fx.room_tone(7.1, seed=260, color=300), T0, -32)
tStop1 = w("factories") + 0.35
tStop2 = w("dna") + 0.1
m.add(fx.machine(tStop1 - T0 + 0.5, rate=6.25, slow_from=tStop1 - T0 - 0.5, seed=261), T0, -16, -0.45)
m.add(fx.machine(tStop2 - T0 + 0.5, rate=4.5, slow_from=tStop2 - T0 - 0.6, seed=262), T0, -20, 0.45)
pop_word(w("protein") - 0.1, 2, tag=True, pan=-0.45)
m.add(fx.whoosh(tStop1 - w("block") + 0.2, peak=0.85, lo=(400, 1400), hi=(1400, 5000), seed=263), w("block") - 0.1, -17, -0.6)
m.add(fx.clunk(seed=264), tStop1, -9, -0.45)
m.add(fx.power_down(0.6, 520, seed=265), tStop1 + 0.05, -15, -0.45)
pop_word(w("copying") - 0.1, 2, tag=True, pan=0.45)
m.add(fx.whoosh(tStop2 - w("stop") + 0.2, peak=0.85, lo=(400, 1400), hi=(1400, 5000), seed=266), w("stop") - 0.1, -17, 0.6)
m.add(fx.clunk(seed=267), tStop2, -9, 0.45)
m.add(fx.power_down(0.6, 440, seed=268), tStop2 + 0.05, -15, 0.45)
m.add(fx.whoosh(0.7, peak=0.6, lo=(200, 700), hi=(700, 2400), seed=269), w("either") - 0.2, -19)
tM = w("multiply", 1, T0)
m.add(fx.creak(0.55, 140, seed=270), tM - 0.55, -14)
m.add(fx.boing(0.45, 260, seed=271), tM + 0.05, -12)
m.add(fx.power_down(0.35, 300, seed=272), tM + 0.08, -17)
pop_word(tM - 0.15, 2, gain=-11, base=460)                                                     # "Can't multiply"

# ===================================================================== VIRUSES (line 7)
T0 = s("viruses")
m.add(fx.room_tone(6.1, seed=280, color=450), T0, -33)
for i in range(3):
    m.add(fx.bubble(380 + i * 70, 0.14, seed=281 + i), T0 + 0.1 + i * 0.08, -17, -0.5)
pop_word(T0 + 0.3, 1, tag=True, pan=-0.5)
tBa = w("bacteria", 1, T0)
for i in range(3):
    t = tBa - 0.55 + i * 0.12
    m.add(fx.whoosh(0.5, peak=0.9, lo=(500, 1500), hi=(1500, 5000), seed=284 + i), t, -24, -0.6)
    m.add(fx.pop(320 + i * 40, 0.18, seed=287 + i), t + 0.56, -8, -0.5)
    m.add(fx.crunch(0.25, seed=290 + i), t + 0.56, -17, -0.5)
tV = w("viruses")
m.add(fx.whoosh(0.7, peak=0.6, lo=(300, 1000), hi=(1000, 3500), seed=293), tV - 0.25, -16, 0.5)
pop_word(tV - 0.05, 1, gain=-11, base=500, pan=0.4)
pop_word(w("colds") - 0.05, 1, tag=True, pan=0.2)
pop_word(w("flu") - 0.05, 1, tag=True, base=600, pan=0.6)
tN = w("nothing")
for i in range(3):
    t = tN - 0.65 + i * 0.12
    m.add(fx.whoosh(0.42, peak=0.9, lo=(500, 1500), hi=(1500, 5000), seed=294 + i), t, -24, 0.3)
    m.add(fx.boing(0.42, 300 + i * 50, seed=297 + i), t + 0.42, -10, 0.4)
pop_word(tN - 0.1, 2, tag=True, pan=0.4)                                                       # "No effect"

# ===================================================================== RESISTANCE (line 8)
T0 = s("resistance")
m.add(fx.room_tone(8.3, seed=300, color=220), T0, -30)
m.add(fx.scurry(8.2, rate=14, seed=301), T0, -27)
tU, SWEEP = w("used") - 0.45, 1.5
m.add(fx.whoosh(SWEEP + 0.5, peak=0.5, lo=(200, 900), hi=(900, 4000), seed=302), tU, -13)
for k, p in enumerate(json.loads((HERE / "res_norm.json").read_text())):
    tp = tU + ((p["x"] + 250) / 2600) * (SWEEP + 0.5) + 0.05
    pan = (p["x"] - 960) / 960 * 0.8
    m.add(fx.pop(300 + (k % 5) * 40, 0.16, seed=310 + k), tp + 0.06, -15, pan)
    if k % 3 == 0:
        m.add(fx.crunch(0.2, seed=360 + k), tp + 0.06, -24, pan)
tR = w("resist")
m.add(fx.sparkle(0.8, count=4, base=1600, seed=400), tR - 0.35, -16)
pop_word(tR, 1, tag=True, pan=-0.4)                                                            # "Resistant"
for i, x in enumerate([520, 1180, 880, 1480]):
    tb = w("survive") - 0.4 + i * 0.1
    m.add(fx.clink(1500, 0.2, seed=401 + i), tb + 0.32, -14, (x - 960) / 960 * 0.8)
    m.add(fx.boing(0.3, 420, seed=405 + i), tb + 0.32, -20, (x - 960) / 960 * 0.8)
tMr = w("multiply", 1, T0) - 0.2
for i, x in enumerate([520, 1180, 880, 1480]):
    m.add(fx.zip_(0.4, 380, 1200, seed=410 + i), tMr + i * 0.05, -23, (x - 960) / 960 * 0.8)
    m.add(fx.bubble(400 + i * 50, 0.16, seed=414 + i), tMr + 0.3 + i * 0.05, -14, (x - 960) / 960 * 0.8)
tS, tD = w("share") - 0.15, w("defences")
m.add(fx.zip_(0.3, 900, 2600, seed=420), tS, -19, -0.6)
for k in range(5):
    m.add(fx.bubble(900 + k * 120, 0.08, seed=421 + k), tS + 0.25 + k * (tD - tS - 0.2) / 5, -23, -0.6)
m.add(fx.sparkle(0.7, count=3, base=2100, seed=430), tD + 0.05, -15, -0.6)
pop_word(tD - 0.1, 2, tag=True, pan=-0.6)                                                      # "Shared defence"
tT = w("that's")
pop_word(tT, 2, gain=-10, base=420)                                                            # "Antibiotic resistance"
for k in range(12):
    m.add(fx.bubble(260 + rng.random() * 300, 0.14, seed=440 + k), tT + 0.2 + rng.random() * 1.0, -21, rng.uniform(-0.8, 0.8))

# ===================================================================== ENDING (line 9 + title)
T0 = s("ending")
m.add(fx.room_tone(5.1, seed=460, color=500), T0, -33)
m.add(fx.thump(120, 0.3, drop=0.8, tau=0.05, click=0.5, seed=461), T0 + 0.32, -13, -0.3)
m.add(fx.whoosh(0.5, peak=0.6, lo=(300, 1200), hi=(1200, 4000), seed=462), T0 + 0.15, -21, 0.3)
pop_word(w("only") - 0.1, 3, tag=True, stagger=0.13, pan=-0.3)
tEx = w("exactly")
for i in range(5):
    m.add(fx.clink(2200 + i * 120, 0.15, seed=463 + i), tEx + i * 0.1 + 0.05, -17, 0.2 + i * 0.05)
pop_word(w("prescribed") + 0.15, 3, tag=True, stagger=0.13, pan=0.3)
tTitle = T0 + cues.SCENE["ending"]["dur"] - 2.42
m.add(fx.whoosh(0.7, peak=0.9, lo=(150, 600), hi=(600, 2400), seed=470), tTitle - 0.35, -16)
m.add(fx.chime((587.33, 880.0, 1174.66, 1760.0), 2.2, gap=0.08, seed=471), tTitle + 0.2, -13)
m.add(fx.sparkle(0.8, count=4, base=2400, seed=472), tTitle + 0.45, -21)

out = HERE.parent / "assets" / "sfx_dry.wav"
m.write(str(out), peak_db=-1.0)
print("wrote", out)
