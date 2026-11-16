"""Narration for the film, driven by film.json.

Two modes:
  python vo.py                       synthesise every sentence with local Kokoro TTS (offline, not a voice MCP)
  python vo.py --recording my.wav    use YOUR recorded voiceover instead (placed after the cold open)

Writes:
  assets/vo_raw.wav       48 kHz mono narration on the film timeline
  assets/vo_timing.json   film length, cold-open length, and (TTS mode) exact sentence start/end times

film.json "film": "auto" makes the film exactly as long as the narration needs.
A number (e.g. 60) fixes the length: the TTS speed is solved (up to max_speed) so the narration fits.
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
GAP_SENT, GAP_LINE = float(CFG.get("gap_sentence", 0.22)), float(CFG.get("gap_line", 0.34))
LINES = CFG["lines"]
(HERE / "assets").mkdir(exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument("--recording", help="path to your own voiceover (any sample rate, mono or stereo)")
args = ap.parse_args()


def write(timeline: np.ndarray, sr: int, film: float, extra: dict):
    out = resample_poly(timeline, SR_OUT, sr).astype(np.float32) if sr != SR_OUT else timeline.astype(np.float32)
    sf.write(HERE / "assets" / "vo_raw.wav", out, SR_OUT)
    meta = {"film": film, "open": OPEN, **extra}
    (HERE / "assets" / "vo_timing.json").write_text(json.dumps(meta, indent=1))


if args.recording:
    # ------------------------------------------------ your own voice
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
    write(timeline, sr, film, {"source": "recording", "sentences": []})
    print(f"recording placed at {OPEN:.2f} s; film {film} s. Next: python align.py")
    raise SystemExit

# ---------------------------------------------------- TTS (Kokoro)
from kokoro_onnx import Kokoro  # noqa: E402  (only needed in TTS mode)

MODEL = Path(os.environ.get("KOKORO_DIR", HERE / "models" / "kokoro"))
kok = Kokoro(str(MODEL / "kokoro-v1.0.onnx"), str(MODEL / "voices-v1.0.bin"))
VOICE, LANG = CFG.get("voice", "af_heart"), CFG.get("lang", "en-us")
gaps = sum(GAP_SENT * (len(l) - 1) for l in LINES) + GAP_LINE * (len(LINES) - 1)


def render_all(speed: float):
    clips = [[kok.create(s, voice=VOICE, speed=speed, lang=LANG) for s in line] for line in LINES]
    sr = clips[0][0][1]
    return clips, sr, sum(len(a) / sr for line in clips for a, _ in line)


speed = 1.0
clips, sr, speech = render_all(speed)
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
t, sents = OPEN, []
for li, line in enumerate(clips):
    for si, (audio, _) in enumerate(line):
        i0 = int(round(t * sr))
        timeline[i0:i0 + len(audio)] += audio.astype(np.float32)
        d = len(audio) / sr
        sents.append({"line": li + 1, "text": LINES[li][si], "start": round(t, 3), "end": round(t + d, 3)})
        t += d + (GAP_SENT if si < len(line) - 1 else 0.0)
    t += GAP_LINE
timeline = timeline[: int(film * sr)]
write(timeline, sr, film, {"source": "tts", "voice": VOICE, "speed": round(speed, 3), "sentences": sents})
print(f"film {film} s, voice {VOICE} at {speed:.3f}x, narration {OPEN:.2f}-{sents[-1]['end']:.2f} s. Next: python align.py")
