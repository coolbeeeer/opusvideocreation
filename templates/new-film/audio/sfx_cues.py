"""Sound-effect cue sheet. One block per scene; every time comes from a narrated word or a scene start,
using the same formulas as the scene's animation, so sound and picture can never drift apart.
Writes ../assets/sfx_dry.wav (stereo). Then run music.py and mix.py.
"""
from pathlib import Path

import cues
import sound_effects as fx
from cues import FILM, s, w

HERE = Path(__file__).resolve().parent
m = fx.Mix(FILM)


def pop_word(t, n_words=1, stagger=0.14, base=520.0, gain=-14, pan=0.0, tag=False):
    """Sound for kit.show(): a soft whoosh as a banner grows (banners only), then one pop per word.
    Offsets match kit.js: words start 0.06 s (tags) / 0.16 s (banners) after show(), `stagger` apart."""
    first = t + (0.06 if tag else 0.16)
    if not tag:
        m.add(fx.whoosh(0.22, peak=0.6, lo=(700, 2200), hi=(2600, 8000), seed=int(t * 100)), t, gain - 6, pan)
    for k in range(n_words):
        m.add(fx.pop(base * (1.12 ** k), seed=int(t * 1000) + k), first + k * stagger, gain, pan)


# quiet air under every scene, so silence never sounds dead
for name, sc in cues.SCENE.items():
    m.add(fx.room_tone(sc["dur"], seed=len(name) * 7, color=300), sc["start"], -33)

# ===================================================================== intro
tB = w("bacterium")
m.add(fx.whoosh(0.6, peak=0.7, lo=(300, 1000), hi=(1000, 3500), seed=1), tB - 0.45, -14, 0.4)   # slide in
pop_word(tB, 1, tag=True)                                                                     # "Bacterium"
pop_word(w("twenty"), 2, tag=True, base=600)                                                  # "20 minutes"
tS = w("splits") - 0.1
m.add(fx.zip_(0.6, 400, 1300, seed=2), tS, -18)                                               # stretching
m.add(fx.bubble(420, 0.16, seed=3), tS + 0.55, -10)                                           # the pinch-off
pop_word(w("two"), 1, tag=True, base=680)                                                     # "x2"

# ===================================================================== outro
T0, DUR = s("outro"), cues.SCENE["outro"]["dur"]
tOne, tM = w("one", 1, T0), w("millions")
for k in range(24):
    u = (k / 24) ** 0.5
    m.add(fx.bubble(300 + (k * 37) % 600, 0.12, seed=10 + k), max(T0, tOne - 0.2) + u * (tM - tOne + 0.4), -22, ((k * 0.37) % 1.6) - 0.8)
pop_word(tM - 0.05, 1, gain=-11, base=480)                                                    # "Millions" banner
tT = T0 + max(tM - T0 + 0.6, DUR - 2.5)                                                       # same formula as outro.html
m.add(fx.whoosh(0.7, peak=0.9, lo=(150, 600), hi=(600, 2400), seed=40), tT - 0.35, -16)
m.add(fx.chime((587.33, 880.0, 1174.66, 1760.0), 2.0, gap=0.08, seed=41), tT + 0.2, -13)

out = HERE.parent / "assets" / "sfx_dry.wav"
m.write(str(out), peak_db=-1.0)
print("wrote", out)
