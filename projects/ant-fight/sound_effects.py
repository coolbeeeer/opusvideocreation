"""Procedural sound effects, built only from noise and sine waves (numpy + scipy).

No samples and no third-party audio: every sound here is synthesised, so it is original.

Core recipes (from the tutorial):
    noise   white noise, then filtered
    whoosh  noise x a swell envelope, getting brighter toward the peak
    thump   a sine that drops in pitch x an exponential decay
    rain    many short water drops over a soft hiss bed

Extra recipes built from the same parts: pop, snap, zap, thunder, impact, splash,
sparkle, scurry, strain, bubble, crunch.

Use `Mix` to place sounds on a timeline and write a stereo WAV.
"""
from __future__ import annotations

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48_000


# ---------------------------------------------------------------- basics
def n_samples(dur: float) -> int:
    return max(1, int(round(dur * SR)))


def time_axis(dur: float) -> np.ndarray:
    return np.arange(n_samples(dur)) / SR


def noise(dur: float, seed: int = 0) -> np.ndarray:
    """White noise, unit variance."""
    return np.random.default_rng(seed).standard_normal(n_samples(dur))


def _sos(kind: str, freq, order: int):
    return signal.butter(order, freq, btype=kind, fs=SR, output="sos")


def lowpass(x, f, order=4):
    return signal.sosfilt(_sos("lowpass", f, order), x)


def highpass(x, f, order=4):
    return signal.sosfilt(_sos("highpass", f, order), x)


def bandpass(x, lo, hi, order=2):
    return signal.sosfilt(_sos("bandpass", [lo, hi], order), x)


def normalise(x, peak=1.0):
    m = float(np.max(np.abs(x))) if x.size else 0.0
    return x * (peak / m) if m > 0 else x


def edge_fade(x, ms=4.0):
    """Short fades at both ends so nothing clicks."""
    k = min(len(x) // 2, int(SR * ms / 1000))
    if k > 0:
        ramp = np.linspace(0, 1, k)
        x = x.copy()
        x[:k] *= ramp
        x[-k:] *= ramp[::-1]
    return x


def swell(n: int, peak: float = 0.7, curve: float = 2.0) -> np.ndarray:
    """0 -> 1 -> 0 envelope that peaks at fraction `peak` of its length."""
    u = np.linspace(0.0, 1.0, n)
    up = np.clip(u / max(peak, 1e-6), 0, 1) ** curve
    down = np.clip((1 - u) / max(1 - peak, 1e-6), 0, 1) ** curve
    return np.minimum(up, down)


def decay(n: int, tau: float) -> np.ndarray:
    """Exponential decay with time constant `tau` seconds."""
    return np.exp(-np.arange(n) / SR / tau)


def sine_sweep(dur: float, f_start: float, f_end: float, curve: str = "exp") -> np.ndarray:
    """Sine whose pitch glides from f_start to f_end."""
    n = n_samples(dur)
    u = np.linspace(0, 1, n)
    if curve == "exp":
        f = f_start * (f_end / f_start) ** u
    else:
        f = f_start + (f_end - f_start) * u
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def reverb(x, tail=0.8, mix=0.2, seed=99, damp=5000):
    """Cheap room: convolve with a decaying, low-passed noise burst."""
    ir = lowpass(noise(tail, seed), damp) * decay(n_samples(tail), tail / 5)
    ir = normalise(ir) * 0.6
    wet = signal.fftconvolve(x, ir)[: len(x) + n_samples(tail)]
    dry = np.pad(x, (0, len(wet) - len(x)))
    return dry * (1 - mix) + normalise(wet, np.max(np.abs(x)) or 1) * mix


# ---------------------------------------------------------------- core recipes
def whoosh(dur=0.6, peak=0.7, lo=(250, 1200), hi=(1500, 6000), seed=1):
    """Noise x a swell. The tone brightens as it swells (low band fades into a high band)."""
    n = n_samples(dur)
    raw = noise(dur, seed)
    low = bandpass(raw, *lo)
    high = bandpass(raw, *hi)
    env = swell(n, peak)
    y = (low * (1 - env) + high * env * 0.8) * env
    return edge_fade(normalise(y, 0.9))


def thump(freq=55.0, dur=0.5, drop=2.5, tau=0.12, click=0.25, seed=2):
    """Sine that falls in pitch, times an exponential decay, plus a soft click on the attack."""
    n = n_samples(dur)
    t = time_axis(dur)
    f = freq * (1 + drop * np.exp(-t / 0.025))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * decay(n, tau)
    hit = lowpass(noise(dur, seed), 2500) * decay(n, 0.006) * click
    y = np.tanh(1.6 * (body + hit))
    return edge_fade(normalise(y, 0.95))


def drop_plink(f0, dur=0.06, seed=0):
    """One water drop: a short upward chirp with a fast decay."""
    n = n_samples(dur)
    y = sine_sweep(dur, f0, f0 * 1.7) * decay(n, dur / 4)
    return edge_fade(y, 1)


def rain(dur=3.0, rate=35.0, seed=3, hiss=0.12):
    """Rain as drops: Poisson-timed plinks over a soft filtered hiss."""
    rng = np.random.default_rng(seed)
    n = n_samples(dur)
    y = lowpass(highpass(noise(dur, seed + 1), 900), 7000) * hiss
    count = rng.poisson(rate * dur)
    for _ in range(count):
        start = int(rng.uniform(0, n - SR * 0.07))
        d = drop_plink(rng.uniform(1400, 4800), rng.uniform(0.03, 0.07))
        y[start : start + len(d)] += d * rng.uniform(0.15, 0.6)
    return edge_fade(normalise(y, 0.8), 30)


# ---------------------------------------------------------------- extra recipes
def pop(freq=520.0, dur=0.12, seed=4):
    """Bubbly UI pop for text and icons popping in."""
    n = n_samples(dur)
    y = sine_sweep(dur, freq, freq * 2.1) * decay(n, 0.03)
    y += bandpass(noise(dur, seed), 1500, 5000) * decay(n, 0.004) * 0.25
    return edge_fade(normalise(y, 0.9), 1)


def snap(dur=0.08, seed=5):
    """Hard little click, like mandibles snapping shut."""
    n = n_samples(dur)
    y = bandpass(noise(dur, seed), 1800, 6500) * decay(n, 0.008)
    y += np.sin(2 * np.pi * 900 * time_axis(dur)) * decay(n, 0.01) * 0.4
    return edge_fade(normalise(y, 0.9), 1)


def zap(dur=0.4, seed=6):
    """Electric crackle: high noise gated into random bursts, plus a 120 Hz buzz."""
    rng = np.random.default_rng(seed)
    n = n_samples(dur)
    crackle = highpass(noise(dur, seed), 2000)
    gate = np.zeros(n)
    i = 0
    while i < n:
        on = int(rng.uniform(0.003, 0.02) * SR)
        gate[i : i + on] = rng.uniform(0.4, 1.0)
        i += on + int(rng.uniform(0.002, 0.03) * SR)
    t = time_axis(dur)
    buzz = signal.sawtooth(2 * np.pi * 120 * t) * 0.25
    y = (crackle * gate + buzz * gate) * swell(n, 0.15, 1.0)
    return edge_fade(normalise(y, 0.9), 2)


def thunder(dur=1.6, seed=7):
    """Sharp crack, then a low rumble that rolls and fades."""
    n = n_samples(dur)
    crack = highpass(noise(dur, seed), 1500) * decay(n, 0.03)
    rumble = lowpass(noise(dur, seed + 1), 180, 2)
    roll = 0.6 + 0.4 * normalise(lowpass(noise(dur, seed + 2), 6, 2))
    rumble = rumble * np.clip(roll, 0.2, 1.5) * swell(n, 0.06, 1.0)
    y = crack * 0.6 + normalise(rumble) * 0.9
    return edge_fade(normalise(np.tanh(1.4 * y), 0.95), 20)


def impact(freq=48.0, dur=0.9, seed=8):
    """Big hit: deep thump plus a noise crack, with a short room tail."""
    n = n_samples(dur)
    body = thump(freq, dur, drop=3.0, tau=0.18, click=0.5, seed=seed)
    crack = bandpass(noise(dur, seed + 1), 800, 7000) * decay(n, 0.02) * 0.7
    y = body + crack
    return normalise(reverb(y, tail=0.6, mix=0.18, seed=seed + 2), 0.95)


def splash(dur=0.9, seed=9):
    """Water splash: a noise burst with a fast attack, then a scatter of drops."""
    rng = np.random.default_rng(seed)
    n = n_samples(dur)
    body = bandpass(noise(dur, seed), 350, 4500) * decay(n, 0.12) * swell(n, 0.02, 1.0)
    y = normalise(body) * 0.9
    for k in range(26):
        start = int(SR * (0.03 + 0.6 * (k / 26) ** 1.6 + rng.uniform(0, 0.03)))
        d = drop_plink(rng.uniform(1200, 4200), rng.uniform(0.03, 0.06))
        end = min(n, start + len(d))
        y[start:end] += d[: end - start] * rng.uniform(0.1, 0.45) * (1 - k / 30)
    return edge_fade(normalise(y, 0.9), 2)


def sparkle(dur=1.0, count=5, base=1900.0, seed=10):
    """Little bell twinkles, for dazed stars and shine."""
    rng = np.random.default_rng(seed)
    n = n_samples(dur)
    y = np.zeros(n)
    for k in range(count):
        start = int(SR * (k / count) * dur * 0.85 + rng.uniform(0, 0.03) * SR)
        f = base * rng.choice([1.0, 1.26, 1.5, 1.68, 2.0])
        d = 0.5
        t = time_axis(d)
        bell = sum(a * np.sin(2 * np.pi * f * m * t) for m, a in [(1, 1.0), (2.76, 0.35), (5.4, 0.12)])
        bell = bell * decay(len(t), 0.12)
        end = min(n, start + len(bell))
        y[start:end] += bell[: end - start] * rng.uniform(0.5, 1.0)
    return edge_fade(normalise(y, 0.8), 3)


def scurry(dur=0.8, rate=26.0, seed=11):
    """Fast leg ticks for small creatures moving."""
    rng = np.random.default_rng(seed)
    n = n_samples(dur)
    y = np.zeros(n)
    t = 0.0
    while t < dur - 0.02:
        tick = bandpass(noise(0.012, int(rng.integers(1_000_000))), 2500, 9000) * decay(n_samples(0.012), 0.002)
        i = int(t * SR)
        y[i : i + len(tick)] += tick * rng.uniform(0.4, 1.0)
        t += rng.uniform(0.6, 1.4) / rate
    return edge_fade(normalise(y, 0.8), 3)


def strain(dur=1.0, wobble=9.0, seed=12):
    """Grinding push-and-pull: low band noise pulsing at `wobble` Hz."""
    n = n_samples(dur)
    t = time_axis(dur)
    base = bandpass(noise(dur, seed), 120, 700)
    am = 0.55 + 0.45 * np.sin(2 * np.pi * wobble * t)
    y = base * am * swell(n, 0.5, 0.6)
    return edge_fade(normalise(y, 0.8), 10)


def bubble(freq=300.0, dur=0.14, seed=13):
    """Soft liquid blip: a quick upward chirp, rounder than `pop`."""
    n = n_samples(dur)
    y = sine_sweep(dur, freq, freq * 2.8) * swell(n, 0.15, 1.5)
    return edge_fade(normalise(y, 0.8), 1)


def crunch(dur=0.35, seed=14):
    """Brittle break: dense clicks over a crackly noise burst."""
    rng = np.random.default_rng(seed)
    n = n_samples(dur)
    y = bandpass(noise(dur, seed), 600, 6000) * decay(n, 0.07)
    for _ in range(40):
        i = int(rng.uniform(0, min(0.25, dur * 0.8)) * SR)
        c = highpass(noise(0.006, int(rng.integers(1_000_000))), 3000) * decay(n_samples(0.006), 0.0015)
        e = min(n, i + len(c))
        y[i:e] += c[: e - i] * rng.uniform(0.5, 1.4)
    return edge_fade(normalise(y, 0.9), 2)


# ---------------------------------------------------------------- mixing
class Mix:
    """Stereo timeline. Place mono or stereo sounds at times with gain and pan."""

    def __init__(self, dur: float):
        self.n = n_samples(dur)
        self.buf = np.zeros((self.n, 2))

    def add(self, sound, at: float, gain_db: float = 0.0, pan: float = 0.0):
        x = np.asarray(sound, dtype=float)
        g = 10 ** (gain_db / 20)
        if x.ndim == 1:
            theta = (pan + 1) * np.pi / 4  # constant-power pan, -1 left .. +1 right
            x = np.stack([x * np.cos(theta), x * np.sin(theta)], axis=1) * np.sqrt(2)
        i = int(round(at * SR))
        if i >= self.n:
            return self
        j = min(self.n, i + len(x))
        self.buf[i:j] += x[: j - i] * g
        return self

    def master(self, peak_db: float = -1.0, drive: float = 1.0) -> np.ndarray:
        y = np.tanh(self.buf * drive) if drive != 1.0 else self.buf.copy()
        m = float(np.max(np.abs(y))) or 1.0
        return y * (10 ** (peak_db / 20) / m)

    def write(self, path: str, peak_db: float = -1.0, drive: float = 1.0):
        y = self.master(peak_db, drive)
        wavfile.write(path, SR, (y * 32767).astype(np.int16))
        return path


# ---------------------------------------------------------------- recipes added for the antibiotics film
def gulp(dur=0.42, seed=30):
    """Swallow: a throat click, then a low resonant 'glug' that drops in pitch."""
    n = n_samples(dur)
    t = time_axis(dur)
    click = bandpass(noise(dur, seed), 900, 3000) * decay(n, 0.006) * 0.5
    f = 260 * np.exp(-t / 0.09) + 95
    glug = np.sin(2 * np.pi * np.cumsum(f) / SR) * swell(n, 0.12, 1.2)
    slosh = bandpass(noise(dur, seed + 1), 200, 900) * swell(n, 0.35, 1.5) * 0.35
    return edge_fade(normalise(click + glug + slosh, 0.9), 3)


def fizz(dur=1.2, rate=60.0, seed=31):
    """Dissolving: a soft hiss bed with lots of tiny high bubbles."""
    rng = np.random.default_rng(seed)
    n = n_samples(dur)
    y = highpass(noise(dur, seed), 3000) * 0.18 * swell(n, 0.15, 1.0)
    for _ in range(int(rate * dur)):
        i = int(rng.uniform(0, n - SR * 0.05))
        b = bubble(rng.uniform(900, 2600), rng.uniform(0.02, 0.05), int(rng.integers(1_000_000)))
        y[i:i + len(b)] += b * rng.uniform(0.15, 0.5) * (1 - i / n) ** 0.7
    return edge_fade(normalise(y, 0.8), 20)


def slice_(dur=0.35, seed=32):
    """Blade cut: a very fast bright whoosh and a short metallic ring."""
    n = n_samples(dur)
    t = time_axis(dur)
    sw = bandpass(noise(dur, seed), 2500, 9000) * swell(n, 0.25, 2.0)
    ring = sum(a * np.sin(2 * np.pi * f * t) for f, a in [(3150, 1.0), (4720, 0.6), (6380, 0.35)]) * decay(n, 0.05)
    lead = np.clip((t - 0.06) * 40, 0, 1)
    return edge_fade(normalise(sw + ring * lead * 0.5, 0.9), 2)


def squish(dur=0.28, f0=420.0, seed=33):
    """Wet squelch: band noise through a resonance that sweeps down."""
    n = n_samples(dur)
    t = time_axis(dur)
    src = noise(dur, seed)
    y = np.zeros(n)
    hop = 480
    for i in range(0, n, hop):
        fc = f0 * (1.8 - 1.2 * i / n)
        seg = bandpass(src[max(0, i - 2000):i + hop], fc * 0.7, fc * 1.4)
        y[i:i + hop] = seg[-min(hop, n - i):]
    y *= swell(n, 0.2, 1.3)
    y += np.sin(2 * np.pi * np.cumsum(f0 * (1 - 0.5 * t / dur)) / SR) * decay(n, 0.06) * 0.4
    return edge_fade(normalise(y, 0.85), 3)


def clink(freq=2400.0, dur=0.22, seed=34):
    """Small hard click with a short inharmonic ring (bricks locking, glints)."""
    n = n_samples(dur)
    t = time_axis(dur)
    ring = sum(a * np.sin(2 * np.pi * freq * m * t) for m, a in [(1.0, 1.0), (2.32, 0.5), (4.25, 0.25)]) * decay(n, 0.035)
    tick = highpass(noise(dur, seed), 4000) * decay(n, 0.002)
    return edge_fade(normalise(ring + tick, 0.8), 1)


def clunk(dur=0.35, seed=35):
    """Mechanical lock: a mid thump plus a dull knock."""
    body = thump(140, dur, drop=1.2, tau=0.05, click=0.6, seed=seed)
    knock = bandpass(noise(dur, seed + 1), 300, 1800) * decay(n_samples(dur), 0.025)
    return edge_fade(normalise(body + knock * 0.8, 0.9), 2)


def power_down(dur=0.5, f0=700.0, seed=36):
    """A machine stopping: a buzzy tone sliding down and fading."""
    n = n_samples(dur)
    t = time_axis(dur)
    f = f0 * np.exp(-t / (dur * 0.35))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sin(ph) + 0.35 * signal.sawtooth(ph)) * np.exp(-t / (dur * 0.45))
    return edge_fade(normalise(lowpass(y, 3000), 0.8), 5)


def flow(dur=2.0, seed=37):
    """Inside a vessel: a low rushing bed that swells slowly."""
    n = n_samples(dur)
    base = lowpass(noise(dur, seed), 380, 2)
    mod = 0.7 + 0.3 * np.sin(2 * np.pi * 0.9 * time_axis(dur))
    return edge_fade(normalise(base * mod, 0.8), 60)


def heartbeat(beats, dur, bpm_gap=0.22, seed=38):
    """Lub-dub pairs at the given times (seconds, relative)."""
    n = n_samples(dur)
    y = np.zeros(n)
    for k, t0 in enumerate(beats):
        for j, (f, g) in enumerate([(52, 1.0), (60, 0.7)]):
            s = thump(f, 0.35, drop=0.8, tau=0.07, click=0.15, seed=seed + k * 2 + j) * g
            i = int((t0 + j * bpm_gap) * SR)
            if i < n:
                e = min(n, i + len(s))
                y[i:e] += s[: e - i]
    return normalise(lowpass(y, 400), 0.9)


def creak(dur=1.2, f0=95.0, seed=39):
    """Straining material: a slow, wobbling sawtooth groan with grit."""
    rng = np.random.default_rng(seed)
    n = n_samples(dur)
    t = time_axis(dur)
    wob = np.cumsum(rng.standard_normal(n)) / SR
    wob = wob - np.linspace(wob[0], wob[-1], n)
    f = f0 * (1 + 0.06 * np.sin(2 * np.pi * 3.1 * t) + 3.0 * wob)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = bandpass(signal.sawtooth(ph), 150, 1600) * swell(n, 0.6, 0.8)
    grit = bandpass(noise(dur, seed), 800, 2500) * (np.abs(np.sin(2 * np.pi * 17 * t)) ** 6) * 0.4
    return edge_fade(normalise(y + grit, 0.8), 15)


def rush(dur=1.6, seed=40):
    """Water rushing in: noise that rises in pitch and level."""
    n = n_samples(dur)
    src = noise(dur, seed)
    lo = bandpass(src, 200, 900)
    hi = bandpass(src, 900, 4000)
    u = np.linspace(0, 1, n) ** 1.5
    y = (lo * (1 - u) + hi * u) * (0.2 + 0.8 * u)
    bub = fizz(dur, rate=25, seed=seed + 1) * 0.35
    return edge_fade(normalise(y + bub, 0.85), 20)


def machine(dur=2.0, rate=8.0, slow_from=None, seed=41):
    """Busy little machine: regular ticks and a soft whirr; optional slow-down to a stop."""
    n = n_samples(dur)
    t = time_axis(dur)
    y = np.zeros(n)
    tt, k = 0.0, 0
    while tt < dur - 0.05:
        c = clink(1800 + 300 * (k % 3), 0.06, seed + k) * (0.6 if k % 2 else 1.0)
        i = int(tt * SR)
        y[i:i + len(c)] += c[: n - i] * 0.6
        step = 1.0 / rate
        if slow_from is not None and tt > slow_from:
            step *= 1 + (tt - slow_from) * 4
        tt += step
        k += 1
    whirr = bandpass(noise(dur, seed), 300, 1200) * (0.55 + 0.45 * np.sin(2 * np.pi * rate * t)) * 0.25
    if slow_from is not None:
        whirr *= np.clip(1 - (t - slow_from) * 2, 0, 1)
    return edge_fade(normalise(y + whirr, 0.8), 10)


def boing(dur=0.45, f0=320.0, seed=42):
    """Springy bounce: a sine with fast vibrato that falls in pitch."""
    n = n_samples(dur)
    t = time_axis(dur)
    f = f0 * (1.5 - 0.6 * t / dur) * (1 + 0.12 * np.sin(2 * np.pi * 22 * t) * np.exp(-t / 0.2))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * decay(n, 0.13)
    return edge_fade(normalise(y, 0.8), 2)


def chime(notes=(880.0, 1318.5, 1760.0), dur=2.0, gap=0.09, seed=43):
    """Soft bell chord, played as a quick upward roll."""
    n = n_samples(dur)
    y = np.zeros(n)
    for k, f in enumerate(notes):
        t = time_axis(dur - k * gap)
        b = sum(a * np.sin(2 * np.pi * f * m * t) for m, a in [(1, 1.0), (2.0, 0.25), (3.01, 0.12), (5.4, 0.05)]) * decay(len(t), 0.6)
        i = int(k * gap * SR)
        y[i:i + len(b)] += b
    return edge_fade(normalise(y, 0.8), 20)


def zip_(dur=0.3, f0=700.0, f1=2600.0, seed=44):
    """Quick rising zip, for something stretching out."""
    n = n_samples(dur)
    t = time_axis(dur)
    f = f0 * (f1 / f0) ** (t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = signal.square(ph * 0.5) * 0.3 + np.sin(ph)
    return edge_fade(normalise(bandpass(y, 500, 6000) * swell(n, 0.7, 1.0), 0.7), 3)


def room_tone(dur=4.0, seed=45, color=300.0):
    """Very quiet air for a scene, so silence never feels dead."""
    return edge_fade(normalise(lowpass(noise(dur, seed), color, 2)) * 0.5, 200)


def limit(x, ceiling_db=-3.0, release=0.08, lookahead=0.004):
    """Look-ahead peak limiter (mono or stereo): instant attack, smooth release."""
    from scipy.ndimage import minimum_filter1d
    x = np.asarray(x, dtype=float)
    peak = np.abs(x) if x.ndim == 1 else np.max(np.abs(x), axis=1)
    c = 10 ** (ceiling_db / 20)
    need = np.minimum(1.0, c / np.maximum(peak, 1e-9))
    la = max(1, int(lookahead * SR))
    g = minimum_filter1d(need, size=2 * la + 1)
    a = np.exp(-1.0 / (release * SR))
    out = np.empty_like(g)
    cur = 1.0
    for i, v in enumerate(g):
        cur = v if v < cur else a * cur + (1 - a) * v
        out[i] = cur
    return x * (out if x.ndim == 1 else out[:, None])
