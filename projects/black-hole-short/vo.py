"""Narration for the film, driven by film.json. Lines are placed one after another with the pause set per line.

Three sources:
  python vo.py                        local Kokoro TTS, one call per line (offline stand-in voice)
  python vo.py --clips DIR            one pre-recorded clip per line (e.g. a channel's locked voice). DIR holds one
                                      audio file per line (wav / flac / ogg, any sample rate, mono or stereo); they are
                                      taken in name order, so call them 01.wav, 02.wav, ... Silence at both ends is
                                      trimmed (--no-trim keeps it). Nothing is time-stretched.
  python vo.py --recording FILE       one continuous recording of the whole script, placed after the cold open

Writes assets/vo_raw.wav (48 kHz mono, on the film timeline) and assets/vo_timing.json (film length, open, and,
for TTS and clips, the exact start and end of every line, which align.py uses to pin each line's first word).
film.json "film": "auto" fits the narration; a number fixes the length (TTS speed is solved up to max_speed;
clips and recordings are never sped up, a warning says when they don't fit).
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
src = ap.add_mutually_exclusive_group()
src.add_argument("--recording", help="one continuous voiceover of the whole script")
src.add_argument("--clips", help="folder with one clip per line, in name order (01.wav, 02.wav, ...)")
ap.add_argument("--no-trim", action="store_true", help="keep the silence at the ends of each clip")
args = ap.parse_args()


def write(timeline: np.ndarray, sr: int, film: float, extra: dict):
    out = resample_poly(timeline, SR_OUT, sr).astype(np.float32) if sr != SR_OUT else timeline.astype(np.float32)
    sf.write(HERE / "assets" / "vo_raw.wav", out, SR_OUT)
    (HERE / "assets" / "vo_timing.json").write_text(json.dumps({"film": film, "open": OPEN, **extra}, indent=1))


def trim(a: np.ndarray, sr: int, below_db: float = 30.0, pad: float = 0.04) -> np.ndarray:
    """Cut the silence (or room noise) at both ends, so the pauses are exactly what film.json asks for.
    Speech is found by loudness, not by sample peaks: 30 ms RMS frames every 10 ms; anything quieter than
    `below_db` under the loud end of the clip (its 95th-percentile frame) counts as silence."""
    hop, win = int(0.01 * sr), int(0.03 * sr)
    if len(a) < win * 3:
        return a
    frames = np.lib.stride_tricks.sliding_window_view(a, win)[::hop]
    rms = np.sqrt(np.mean(frames ** 2, axis=1)) + 1e-12
    loud = np.where(rms > np.percentile(rms, 95) * 10 ** (-below_db / 20))[0]
    if not len(loud):
        return a
    i0 = max(0, loud[0] * hop - int(pad * sr))
    i1 = min(len(a), loud[-1] * hop + win + int(pad * sr))
    return a[i0:i1]


def lay_out(clips, sr, film, extra):
    """Place the clips on the film timeline with the per-line pauses; record exact line starts and ends."""
    timeline = np.zeros(int(film * sr) + sr, dtype=np.float32)
    t, out = OPEN, []
    for li, (a, p) in enumerate(zip(clips, PAUSES)):
        i0 = int(round(t * sr))
        n = max(0, min(len(a), len(timeline) - i0))
        timeline[i0:i0 + n] += a[:n]
        d = len(a) / sr
        out.append({"line": li + 1, "text": LINES[li]["text"], "start": round(t, 3), "end": round(t + d, 3)})
        t += d + p
    write(timeline[: int(film * sr)], sr, film, {**extra, "lines": out})
    print(f"film {film} s, narration {OPEN:.2f}-{out[-1]['end']:.2f} s, tail {film - out[-1]['end']:.2f} s")
    for o in out:
        print(f"  line {o['line']}: {o['start']:6.2f}-{o['end']:6.2f}  {o['text'][:60]}")


def film_length(speech: float) -> float:
    need = OPEN + speech + sum(PAUSES[:-1]) + TAIL
    return round(math.ceil(need * 10) / 10, 1) if CFG["film"] == "auto" else float(CFG["film"])


# ---------------------------------------------------- one continuous recording
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

# ---------------------------------------------------- one clip per line
if args.clips:
    folder = Path(args.clips)
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in (".wav", ".flac", ".ogg", ".aif", ".aiff"))
    if len(files) != len(LINES):
        raise SystemExit(f"{folder} has {len(files)} audio files but film.json has {len(LINES)} lines")
    clips = []
    for f in files:
        a, sr_in = sf.read(f, dtype="float32", always_2d=True)
        a = a.mean(axis=1)
        if sr_in != SR_OUT:
            g = math.gcd(sr_in, SR_OUT)
            a = resample_poly(a, SR_OUT // g, sr_in // g).astype(np.float32)
        clips.append(a if args.no_trim else trim(a, SR_OUT))
    peak = max(float(np.max(np.abs(c))) for c in clips) or 1.0
    clips = [c / peak * 0.7 for c in clips]            # one gain for all clips keeps their relative levels
    speech = sum(len(c) for c in clips) / SR_OUT
    film = film_length(speech)
    need = OPEN + speech + sum(PAUSES[:-1]) + TAIL
    if need > film + 0.05:
        print(f"WARNING: the clips need {need:.2f} s but the film is {film} s. Shorten pauses or lengthen the film.")
    print(f"{len(clips)} clips from {folder}: {speech:.2f} s of speech")
    for f, c in zip(files, clips):
        print(f"  {f.name}: {len(c) / SR_OUT:.2f} s")
    lay_out(clips, SR_OUT, film, {"source": "clips", "clips": [f.name for f in files]})
    print("Next: python align.py")
    raise SystemExit

# ---------------------------------------------------- TTS (Kokoro), one call per line
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
print(f"speed {speed}: {speech:.2f} s of speech for {sum(len(l['text'].split()) for l in LINES)} words")
if CFG["film"] != "auto":
    target = float(CFG["film"]) - OPEN - TAIL - gaps
    for _ in range(6):
        if speech <= target + 0.05:
            break
        speed = float(np.clip(speed * speech / target, 1.0, float(CFG.get("max_speed", 1.08))))
        clips, sr, speech = render_all(speed)
    if speech > target + 0.05:
        print(f"WARNING: narration is {speech - target:.2f} s too long even at {speed:.3f}x. Trim the script or lengthen the film.")
lay_out(clips, sr, film_length(speech), {"source": "tts", "voice": VOICE, "speed": round(speed, 3)})
print("Next: python align.py")
