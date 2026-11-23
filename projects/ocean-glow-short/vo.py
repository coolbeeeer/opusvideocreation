"""Narration for the film, driven by film.json. One TTS call per script line (a short paragraph), not per sentence,
so the voice keeps its phrasing across sentences; the pause after each line is set per line in film.json.

  python vo.py                       local Kokoro TTS (offline stand-in voice)
  python vo.py --recording my.wav    your own recording instead (placed after the cold open)

Writes assets/vo_raw.wav (48 kHz mono, on the film timeline) and assets/vo_timing.json.
film.json "film": a number fixes the length (the TTS speed is solved up to max_speed); "auto" fits the narration.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "film.json").read_text())
SR_OUT = 48_000
OPEN, TAIL = float(CFG["open"]), float(CFG["tail"])
LINES = CFG["lines"]
PAUSES = [float(l.get("pause", 0.45)) for l in LINES]
(HERE / "assets").mkdir(exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument("--recording", help="path to your own voiceover (any sample rate, mono or stereo)")
args = ap.parse_args()


def write(timeline: np.ndarray, sr: int, film: float, extra: dict):
    out = resample_poly(timeline, SR_OUT, sr).astype(np.float32) if sr != SR_OUT else timeline.astype(np.float32)
    sf.write(HERE / "assets" / "vo_raw.wav", out, SR_OUT)
    (HERE / "assets" / "vo_timing.json").write_text(json.dumps({"film": film, "open": OPEN, **extra}, indent=1))


def trim(a: np.ndarray, sr: int, thr_db: float = -42.0, pad: float = 0.03) -> np.ndarray:
    """Cut the silence TTS leaves at both ends, so the pauses are exactly what film.json asks for."""
    env = np.abs(a)
    idx = np.where(env > env.max() * 10 ** (thr_db / 20))[0]
    if not len(idx):
        return a
    return a[max(0, idx[0] - int(pad * sr)): min(len(a), idx[-1] + int(pad * sr))]


if args.recording:
    rec, sr = sf.read(args.recording, dtype="float32", always_2d=True)
    rec = rec.mean(axis=1)
    rec = rec / (np.max(np.abs(rec)) + 1e-9) * 0.7
    need = OPEN + len(rec) / sr + TAIL
    film = round(math.ceil(need * 10) / 10, 1) if CFG["film"] == "auto" else float(CFG["film"])
    if need > film + 0.05:
        print(f"WARNING: recording needs {need:.2f} s but film is {film} s; it will be cut off")
    timeline = np.zeros(int(film * sr), dtype=np.float32)
    i0 = int(OPEN * sr)
    n = min(len(rec), len(timeline) - i0)
    timeline[i0:i0 + n] = rec[:n]
    write(timeline, sr, film, {"source": "recording", "lines": []})
    print(f"recording placed at {OPEN:.2f} s; film {film} s. Next: python align.py")
    raise SystemExit

from kokoro_onnx import Kokoro  # noqa: E402  (TTS mode only)

MODEL = Path(os.environ.get("KOKORO_DIR", HERE / "models" / "kokoro"))
kok = Kokoro(str(MODEL / "kokoro-v1.0.onnx"), str(MODEL / "voices-v1.0.bin"))
VOICE, LANG = CFG.get("voice", "af_heart"), CFG.get("lang", "en-us")
gaps = sum(PAUSES[:-1])


def render_all(speed: float):
    clips, sr = [], 24_000
    for l in LINES:
        a, sr = kok.create(l["text"], voice=VOICE, speed=speed, lang=LANG)
        clips.append(trim(np.asarray(a, np.float32), sr))
    return clips, sr, sum(len(a) for a in clips) / sr


speed = float(CFG.get("speed", 1.0))   # base reading speed; a fixed film length may raise it up to max_speed
clips, sr, speech = render_all(speed)
print(f"natural speed: {speech:.2f} s of speech for {sum(len(l['text'].split()) for l in LINES)} words")
if CFG["film"] == "auto":
    film = round(math.ceil((OPEN + speech + gaps + TAIL) * 10) / 10, 1)
else:
    film = float(CFG["film"])
    target = film - OPEN - TAIL - gaps
    for _ in range(6):
        if speech <= target + 0.05:
            break
        speed = float(np.clip(speed * speech / target, 1.0, float(CFG.get("max_speed", 1.08))))
        clips, sr, speech = render_all(speed)
    if speech > target + 0.05:
        print(f"WARNING: narration is {speech - target:.2f} s too long even at {speed:.3f}x. Trim the script or lengthen the film.")

timeline = np.zeros(int(film * sr) + sr, dtype=np.float32)
t, out = OPEN, []
for li, (a, p) in enumerate(zip(clips, PAUSES)):
    i0 = int(round(t * sr))
    timeline[i0:i0 + len(a)] += a
    d = len(a) / sr
    out.append({"line": li + 1, "text": LINES[li]["text"], "start": round(t, 3), "end": round(t + d, 3)})
    t += d + p
timeline = timeline[: int(film * sr)]
write(timeline, sr, film, {"source": "tts", "voice": VOICE, "speed": round(speed, 3), "lines": out})
print(f"film {film} s, voice {VOICE} at {speed:.3f}x, narration {OPEN:.2f}-{out[-1]['end']:.2f} s, tail {film - out[-1]['end']:.2f} s")
for o in out:
    print(f"  line {o['line']}: {o['start']:6.2f}-{o['end']:6.2f}  {o['text'][:60]}")
