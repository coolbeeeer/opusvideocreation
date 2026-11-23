"""Mix the three stems for HyperFrames: voice, sound effects, music. Mastered for Shorts / Reels.

- voice: 80 Hz high-pass, levelled, peak-limited
- music: levelled, then ducked ~7 dB under the voice by an envelope follower
- sfx:   levelled and peak-limited
- the renderer sums the three tracks, so sfx + music are pulled down wherever voice + sfx + music would pass the
  ceiling (the voice is never touched)
- finally all three stems get the same gain so the sum lands on -14 LUFS integrated (YouTube's and Instagram's
  playback reference), and the ceiling is re-applied; a 1.8 dB margin below 0 dBFS leaves room for AAC overshoot
Writes ../assets/vo.wav, sfx.wav, music.wav (48 kHz) and prints the loudness of each and of the sum.
"""
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, minimum_filter1d

import cues  # noqa: F401  (sets the sound_effects path)
import sound_effects as fx

A = Path(__file__).resolve().parent.parent / "assets"
SR = fx.SR
FILM = cues.FILM
N = int(FILM * SR)
TARGET_LUFS, CEIL_DB = -14.0, -1.8


def load(name):
    sr, x = wavfile.read(A / name)
    assert sr == SR, (name, sr)
    x = x.astype(np.float64) / (32768.0 if x.dtype == np.int16 else 1.0)
    x = x if x.ndim == 2 else x[:, None]
    out = np.zeros((N, x.shape[1]))
    out[: min(N, len(x))] = x[:N]
    return out


def lufs(x):
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        wavfile.write(f.name, SR, np.clip(x, -1, 1).astype(np.float32))
        r = subprocess.run(["ffmpeg", "-nostats", "-i", f.name, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])


def gain_to(x, target):
    return x * 10 ** ((target - lufs(x)[0]) / 20)


def smooth_env(x, attack, release):
    a_up, a_dn = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    out, cur = np.empty_like(x), 0.0
    for i, v in enumerate(x):
        cur = (a_up * cur + (1 - a_up) * v) if v > cur else (a_dn * cur + (1 - a_dn) * v)
        out[i] = cur
    return out


def ceiling(vo, sx, mu, ceil_db):
    """Scale sfx + music sample by sample so |voice| + |sfx + music| stays under the ceiling (4 ms look-ahead, 80 ms release)."""
    c = 10 ** (ceil_db / 20)
    bed = sx + mu
    need = np.ones(N)
    over = (np.abs(vo) + np.max(np.abs(bed), axis=1)) > c
    need[over] = np.clip((c - np.abs(vo[over])) / np.maximum(np.max(np.abs(bed[over]), axis=1), 1e-9), 0, 1)
    g = minimum_filter1d(need, int(0.004 * SR) * 2 + 1)
    a = np.exp(-1 / (0.08 * SR))
    out, cur = np.empty_like(g), 1.0
    for i, v in enumerate(g):
        cur = v if v < cur else a * cur + (1 - a) * v
        out[i] = cur
    return sx * out[:, None], mu * out[:, None], out


# ---------------------------------------------------------------- levels before the master gain
vo = load("vo_raw.wav")[:, 0]
vo = signal.sosfilt(signal.butter(2, 80, "highpass", fs=SR, output="sos"), vo)
vo = gain_to(vo, -17.0)

env = signal.sosfilt(signal.butter(2, 8, "lowpass", fs=SR, output="sos"), np.abs(vo))
env = np.clip(env / (np.percentile(env[env > 1e-4], 90) + 1e-9), 0, 1)
env = smooth_env(maximum_filter1d(env, int(0.05 * SR)), 0.04, 0.35)
mu = gain_to(load("music_dry.wav"), -24.5) * (10 ** (-7.0 * env / 20))[:, None]
sx = fx.limit(gain_to(load("sfx_dry.wav"), -22.5), -4.0, release=0.05)

# ---------------------------------------------------------------- master gain to the target, then the ceiling (twice to converge)
for it in range(3):
    g = 10 ** ((TARGET_LUFS - lufs(vo[:, None] + sx + mu)[0]) / 20)
    vo, sx, mu = vo * g, sx * g, mu * g
    vo = fx.limit(vo, CEIL_DB - 0.7, release=0.06)
    sx, mu, k = ceiling(vo, sx, mu, CEIL_DB)
reduced = (1 - k) > 0.01
print(f"bed pulled down on {reduced.mean() * 100:.2f}% of samples, max {20 * np.log10(max(k.min(), 1e-6)):.1f} dB")

for name, x in [("vo.wav", vo[:, None]), ("sfx.wav", sx), ("music.wav", mu)]:
    wavfile.write(A / name, SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
total = vo[:, None] + sx + mu
for name, x in [("voice", vo), ("sfx", sx), ("music", mu), ("SUM", total)]:
    i, p = lufs(x)
    print(f"{name:6s} {i:6.1f} LUFS  peak {p:5.1f} dBFS")
speech = env > 0.3
vr = 10 * np.log10(np.mean(vo[speech] ** 2) + 1e-12)
for name, x in [("music", mu), ("sfx", sx), ("bed", sx + mu)]:
    br = 10 * np.log10(np.mean(x[speech] ** 2) + 1e-12)
    print(f"while speaking: {name} is {vr - br:.1f} dB under the voice (RMS)")
