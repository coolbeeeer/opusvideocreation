"""Sound-effect cue sheet for the 4-second ant fight. Times match index.html."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # vendored sound_effects.py sits beside this file
import sound_effects as fx  # noqa: E402

DUR = 4.0
m = fx.Mix(DUR)

# room tone + slow drips in the nest (rain recipe at a low rate)
m.add(fx.lowpass(fx.noise(DUR, 40), 220) * 0.6, 0.0, -30)
m.add(fx.rain(DUR, rate=3.0, seed=41, hiss=0.0), 0.0, -22, pan=0.3)

# 0.00-0.80 squaring up: leg shuffles, jaw snaps
m.add(fx.scurry(0.8, rate=22, seed=1), 0.0, -17, pan=-0.45)
m.add(fx.scurry(0.8, rate=22, seed=2), 0.0, -17, pan=0.45)
for t, pan, g in [(0.10, -0.4, -12), (0.18, 0.4, -12), (0.30, -0.4, -6), (0.36, 0.4, -6), (0.42, -0.4, -12), (0.50, 0.4, -12)]:
    m.add(fx.snap(seed=int(t * 100)), t, g, pan)

# 0.80-1.30 charge: fast legs, two whooshes converging
m.add(fx.scurry(0.5, rate=60, seed=3), 0.8, -14, pan=-0.3)
m.add(fx.scurry(0.5, rate=60, seed=4), 0.8, -14, pan=0.3)
m.add(fx.whoosh(0.5, peak=0.9, seed=5), 0.8, -8, pan=-0.5)
m.add(fx.whoosh(0.5, peak=0.9, seed=6), 0.8, -8, pan=0.5)

# 1.25-1.30 bolt draws down the shaft, 1.30 clash
m.add(fx.zap(0.4, seed=7), 1.25, -6)
m.add(fx.impact(seed=8), 1.30, 0)
m.add(fx.thunder(1.0, seed=9), 1.30, -8)
m.add(fx.snap(seed=10), 1.30, -6)

# 1.30-2.30 jaws locked: grinding push and pull, pushing legs
m.add(fx.strain(1.0, wobble=8, seed=11), 1.32, -11)
m.add(fx.scurry(1.0, rate=16, seed=12), 1.32, -18, pan=-0.2)
m.add(fx.scurry(1.0, rate=16, seed=13), 1.32, -18, pan=0.2)

# callout 1: banner grows (soft whoosh), words pop
m.add(fx.whoosh(0.25, peak=0.5, lo=(600, 2000), hi=(2500, 8000), seed=14), 1.42, -17)
m.add(fx.pop(500, seed=15), 1.60, -9)
m.add(fx.pop(640, seed=16), 1.75, -9)

# 2.26-2.90 the throw
m.add(fx.snap(seed=17), 2.32, -12, pan=0.1)
m.add(fx.whoosh(0.62, peak=0.55, seed=18), 2.28, -2, pan=0.3)
m.add(fx.scurry(0.6, rate=70, seed=19), 2.3, -18, pan=0.4)

# 2.88 splash into the puddle
m.add(fx.splash(0.9, seed=20), 2.88, -2, pan=0.5)
m.add(fx.thump(70, 0.35, drop=1.5, tau=0.08, seed=21), 2.88, -8, pan=0.5)

# callout 2
m.add(fx.whoosh(0.25, peak=0.5, lo=(600, 2000), hi=(2500, 8000), seed=22), 2.95, -17, pan=0.4)
m.add(fx.pop(500, seed=23), 3.12, -9, pan=0.4)
m.add(fx.pop(640, seed=24), 3.27, -9, pan=0.4)

# 3.00-4.00 dazed sparkles, twitching legs, victory hop lands
m.add(fx.sparkle(1.0, count=6, seed=25), 3.0, -10, pan=0.5)
m.add(fx.scurry(1.0, rate=8, seed=26), 3.0, -22, pan=0.5)
m.add(fx.thump(90, 0.25, drop=1.0, tau=0.05, click=0.4, seed=27), 3.43, -16, pan=-0.2)

out = Path(__file__).resolve().parent / "assets" / "sfx.wav"
out.parent.mkdir(exist_ok=True)
m.write(str(out), peak_db=-1.0)
print("wrote", out)
