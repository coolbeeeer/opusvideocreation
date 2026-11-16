"""Mix the three stems for HyperFrames: voice, sound effects, music.

- voice: high-passed, levelled to -19 LUFS, peak-limited
- music: ducked about 6 dB under the voice (envelope follower), levelled
- sfx:   levelled; sfx + music are pulled down wherever voice + sfx + music would pass -1.5 dBFS,
         so the three tracks summed by the renderer can never clip
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
    i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
    p = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
    return i, p


def gain_to(x, target):
    i, _ = lufs(x)
    return x * 10 ** ((target - i) / 20)


def smooth_env(x, attack, release):
    a_up, a_dn = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    out = np.empty_like(x)
    cur = 0.0
    for i, v in enumerate(x):
        cur = (a_up * cur + (1 - a_up) * v) if v > cur else (a_dn * cur + (1 - a_dn) * v)
        out[i] = cur
    return out


# ---------------------------------------------------------------- voice
vo = load("vo_raw.wav")[:, 0]
vo = signal.sosfilt(signal.butter(2, 80, "highpass", fs=SR, output="sos"), vo)
vo = gain_to(vo, -19.0)
vo = fx.limit(vo, -3.0, release=0.06)

# ---------------------------------------------------------------- music, ducked under the voice
mu = load("music_dry.wav")
env = signal.sosfilt(signal.butter(2, 8, "lowpass", fs=SR, output="sos"), np.abs(vo))
env = np.clip(env / (np.percentile(env[env > 1e-4], 90) + 1e-9), 0, 1)
env = smooth_env(maximum_filter1d(env, int(0.05 * SR)), 0.04, 0.35)
duck_db = -6.5 * env
mu = gain_to(mu, -24.5) * (10 ** (duck_db / 20))[:, None]

# ---------------------------------------------------------------- sound effects
sx = gain_to(load("sfx_dry.wav"), -22.5)
sx = fx.limit(sx, -3.0, release=0.05)

# ---------------------------------------------------------------- keep the sum under the ceiling
c = 10 ** (-1.5 / 20)
bed = sx + mu
need = np.ones(N)
over = (np.abs(vo) + np.max(np.abs(bed), axis=1)) > c
need[over] = np.clip((c - np.abs(vo[over])) / np.maximum(np.max(np.abs(bed[over]), axis=1), 1e-9), 0, 1)
g = minimum_filter1d(need, int(0.004 * SR) * 2 + 1)
a = np.exp(-1 / (0.08 * SR))
out = np.empty_like(g)
cur = 1.0
for i, v in enumerate(g):
    cur = v if v < cur else a * cur + (1 - a) * v
    out[i] = cur
sx *= out[:, None]
mu *= out[:, None]
reduced = (1 - out) > 0.01
print(f"bed pulled down on {reduced.mean() * 100:.2f}% of samples, max {20 * np.log10(max(out.min(), 1e-6)):.1f} dB")

for name, x in [("vo.wav", vo[:, None]), ("sfx.wav", sx), ("music.wav", mu)]:
    wavfile.write(A / name, SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
total = vo[:, None] + sx + mu
for name, x in [("voice", vo), ("sfx", sx), ("music", mu), ("SUM", total)]:
    i, p = lufs(x)
    print(f"{name:6s} {i:6.1f} LUFS  peak {p:5.1f} dBFS")
# speech-only windows: how far the bed sits under the voice
speech = env > 0.3
vr = 10 * np.log10(np.mean(vo[speech] ** 2) + 1e-12)
br = 10 * np.log10(np.mean((sx[speech] + mu[speech]) ** 2) + 1e-12)
print(f"while speaking: bed is {vr - br:.1f} dB under the voice (RMS)")
