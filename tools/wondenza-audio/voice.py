"""Wondenza voice — Fish Audio narration for Opus's films.

Drop-in replacement for the Kokoro call in a project's ``vo.py``.
Same outputs, same format, so the rest of the pipeline (align.py, build.py)
does not change:

  * one clip per script line (``clip01.wav`` ...), trimmed so speech starts
    at the clip's start time
  * ``assets/vo_raw.wav`` — the clips laid on the film timeline (48 kHz mono)
  * ``assets/vo_timing.json`` — ``{"film", "open", "source": "fish", "voice",
    "speed", "lines": [{"line", "text", "start", "end"}]}``

The API key is read ONLY from the environment (``FISH_AUDIO_API_KEY``).
It is never hardcoded, never written to a file, and never printed.
Set it in Kiro from the Fish Audio dashboard (fish.audio).

Locked: model ``1d866ca2766944489ae05da868809c15``, engine ``s2.1-pro-free``
(free). The paid engine is refused outright — there is no credit for it.

A clip that runs over its max length is re-recorded faster (1.05x, then
1.1x), per the user's rule. Fish's speed->duration is NOT linear (it
overshoots), so the retry checks the measured duration each time.

Requires: ffmpeg + ffprobe on PATH, and ``soundfile`` + ``numpy``
(both already in the repo's requirements.txt).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

try:
    import numpy as np
    import soundfile as sf
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "wondenza-audio needs soundfile + numpy (already in the repo's "
        "requirements.txt): pip install soundfile numpy"
    ) from exc


class VoiceError(RuntimeError):
    pass


def get_api_key() -> str:
    """The Fish key, from the environment only. Never hardcoded."""
    key = os.environ.get("FISH_AUDIO_API_KEY", "").strip()
    if not key:
        raise VoiceError(
            "FISH_AUDIO_API_KEY is not set. In Kiro, add it as an environment "
            "variable / secret (copy it from the Fish Audio dashboard, "
            "fish.audio). The module never stores a key."
        )
    return key


def _check_engine(engine: str) -> None:
    if engine != "s2.1-pro-free":
        raise VoiceError(
            f"refusing engine {engine!r}: only s2.1-pro-free is allowed "
            "(the paid engine has no credit — do not use it)"
        )


def synthesize(text: str, out_path: Path, speed: float | None = None,
               api_key: str | None = None, engine: str = C.FISH_ENGINE) -> Path:
    """One Fish Audio TTS call. Writes a wav file. Returns the path.

    ``speed`` is the prosody multiplier (0.85 = the locked middle pace).
    Omit it for the API default.
    """
    _check_engine(engine)
    key = api_key or get_api_key()
    text = text.strip()
    if not text:
        raise VoiceError("empty text")
    body: dict = {
        "text": text,
        "reference_id": C.FISH_MODEL_ID,
        "format": C.FISH_FORMAT,
        "latency": C.FISH_LATENCY,
        "language": C.FISH_LANGUAGE,
    }
    if speed is not None:
        body["prosody"] = {"speed": round(float(speed), 3)}
    req = urllib.request.Request(
        C.FISH_API_URL, data=json.dumps(body).encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("model", engine)
    try:
        with urllib.request.build_opener().open(req, timeout=120) as resp:
            total = 0
            with open(out_path, "wb") as fh:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    fh.write(chunk)
                    total += len(chunk)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        if exc.code == 401:
            raise VoiceError(
                "Fish Audio 401: the key was rejected. Check "
                "FISH_AUDIO_API_KEY in Kiro (copy it fresh from fish.audio)."
            ) from exc
        if exc.code == 402:
            raise VoiceError(
                "Fish Audio 402: payment required — the paid engine was "
                "requested somewhere. This module only ever sends "
                "s2.1-pro-free; check nothing else is calling the API."
            ) from exc
        if exc.code == 429:
            raise VoiceError(
                f"Fish Audio 429 (rate limit): wait and retry. {detail}"
            ) from exc
        raise VoiceError(f"Fish Audio HTTP {exc.code}: {detail}") from exc
    if total == 0 or not out_path.exists():
        raise VoiceError(f"Fish Audio returned no audio for {out_path}")
    return out_path


def trim_clip(src: Path, out_path: Path,
              threshold_db: float = C.TRIM_THRESHOLD_DB,
              lead_pad: float = C.TRIM_LEAD_PAD_S,
              tail_pad: float = C.TRIM_TAIL_PAD_S) -> dict:
    """Cut the silence Fish leaves at both ends, precisely.

    First speech sample is found at ``threshold_db`` below the clip peak;
    keep ``lead_pad`` before it and ``tail_pad`` after the last speech sample.
    (The re-voice measured first speech at 0.146-0.215 s in the raw clips.)

    Returns ``{"start", "end", "duration"}`` — the trim points in the RAW
    clip, in seconds — so the caller can record them (like final_trims.json).
    """
    data, sr = sf.read(str(src), dtype="float32", always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    peak = float(np.max(np.abs(data))) if len(data) else 0.0
    if peak <= 0:
        raise VoiceError(f"{src}: silent clip, nothing to trim")
    thr = peak * 10 ** (threshold_db / 20)
    idx = np.where(np.abs(data) > thr)[0]
    if not len(idx):
        raise VoiceError(f"{src}: no speech above {threshold_db} dB")
    start = max(0.0, idx[0] / sr - lead_pad)
    end = min(len(data) / sr, idx[-1] / sr + tail_pad)
    start_i, end_i = int(start * sr), int(end * sr)
    sf.write(str(out_path), data[start_i:end_i], sr)
    return {"start": round(start, 3), "end": round(end, 3),
            "duration": round((end_i - start_i) / sr, 3)}


def clip_duration(path: Path) -> float:
    info = sf.info(str(path))
    return info.frames / info.samplerate


def record_lines(lines: list[dict], out_dir: Path,
                 pace: float = C.VOICE_PACE,
                 api_key: str | None = None) -> list[dict]:
    """Record one Fish clip per script line.

    Each ``line`` is ``{"text": ...}`` and may carry ``"max_length"`` (seconds)
    and ``"pause"`` (seconds after the line). Clips are written as
    ``clip01.wav`` ... in ``out_dir`` (trimmed), plus ``clips.json``.

    If a clip runs over its max length, it is re-recorded at 1.05x, then
    1.1x (the user's rule). Fish's speed->duration is not linear, so the
    measured duration is checked after every retry. NOTE: if MANY clips
    need speed-ups, the pace wanders from clip to clip and the voice
    sounds uneven — that is what happened on the hypnic re-voice
    (2026-11-26, user verdict "the voice sounds weird"). For a NEW film,
    do not force the voice into fixed slots: record at the natural 0.85
    pace, let the film length follow the voice (film="auto"), and re-time
    the picture to the voice (align.py + build.py). The speed-up retry
    exists only for re-voicing an already-timed film, where the slots are
    fixed — and even there, if the voice sounds uneven, send the
    natural-pace clips to Opus for a re-time instead of varying speeds
    further.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for i, line in enumerate(lines, start=1):
        text = line["text"]
        max_len = line.get("max_length")
        name = f"clip{i:02d}"
        raw = out_dir / f"{name}_raw.wav"
        final = out_dir / f"{name}.wav"
        speed = pace
        for attempt, mult in enumerate((1.0, *C.VOICE_SPEEDUP_STEPS)):
            s = pace * mult
            synthesize(text, raw, speed=s, api_key=api_key)
            trims = trim_clip(raw, final)
            dur = trims["duration"]
            if max_len is None or dur <= max_len + 0.02:
                break
            if attempt == len(C.VOICE_SPEEDUP_STEPS):
                print(f"WARNING: {name} is {dur:.2f} s at {s:.3f}x, still over "
                      f"max {max_len:.2f} s — keeping it; trim the line or "
                      "lengthen the film.")
            else:
                print(f"  {name}: {dur:.2f} s over max {max_len:.2f} s, "
                      f"retrying at {pace * C.VOICE_SPEEDUP_STEPS[attempt]:.3f}x")
        results.append({"line": i, "text": text, "path": str(final),
                        "duration": dur, "speed": round(s, 3),
                        "trim": trims,
                        "pause": float(line.get("pause", 0.45)),
                        "max_length": max_len})
        print(f"  {name}: {dur:.2f} s at {s:.3f}x  {text[:60]}")
    (out_dir / "clips.json").write_text(json.dumps(results, indent=1))
    return results


def build_timeline(clips: list[dict], open_s: float, film: float,
                   out_dir: Path) -> tuple[Path, Path]:
    """Lay trimmed clips on the film timeline (after the cold open).

    Writes ``vo_raw.wav`` (48 kHz mono) and ``vo_timing.json`` in the exact
    format ``vo.py`` produces, so ``align.py`` and ``build.py`` work unchanged.
    Returns ``(vo_raw_path, vo_timing_path)``.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    inputs, filters, labels = [], [], []
    t = open_s
    timing_lines = []
    for i, c in enumerate(clips):
        inputs += ["-i", c["path"]]
        delay_ms = int(round(t * 1000))
        filters.append(f"[{i}:a]aresample={C.SAMPLE_RATE},"
                       f"aformat=channel_layouts=mono,"
                       f"adelay={delay_ms}:all=1[c{i}]")
        labels.append(f"[c{i}]")
        timing_lines.append({"line": c["line"], "text": c["text"],
                             "start": round(t, 3),
                             "end": round(t + c["duration"], 3)})
        t += c["duration"] + c.get("pause", 0.45)
    filters.append(f"{''.join(labels)}amix=inputs={len(clips)}:normalize=0,"
                   f"aresample={C.SAMPLE_RATE},"
                   f"apad=whole_dur={film:.2f}[out]")
    vo_raw = out_dir / "vo_raw.wav"
    cmd = (["ffmpeg", "-y", "-v", "error"] + inputs +
           ["-filter_complex", ";".join(filters), "-map", "[out]",
            "-c:a", "pcm_s16le", str(vo_raw)])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise VoiceError(f"ffmpeg timeline failed: {r.stderr[-1000:]}")
    vo_timing = out_dir / "vo_timing.json"
    vo_timing.write_text(json.dumps(
        {"film": film, "open": open_s, "source": "fish",
         "voice": C.FISH_MODEL_ID, "speed": clips[0]["speed"] if clips else None,
         "lines": timing_lines}, indent=1))
    return vo_raw, vo_timing


def record_film(film_json: Path, out_dir: Path,
                pace: float = C.VOICE_PACE,
                api_key: str | None = None) -> dict:
    """Full ``vo.py`` flow for a project: read film.json, record the lines,
    solve the speed so the narration fits a fixed film length (or fit the
    film to the narration when ``film`` is ``"auto"``), write vo_raw.wav +
    vo_timing.json. Returns ``{"film", "vo_raw", "vo_timing", "clips"}``.

    film.json shape (same as the template): ``{"open", "tail", "film",
    "lines": [{"text", "pause"}], "speed", "max_speed"}``. A line may carry
    ``"max_length"`` to cap its clip.
    """
    cfg = json.loads(film_json.read_text())
    open_s = float(cfg["open"])
    tail = float(cfg["tail"])
    lines = [{"text": l["text"], "pause": float(l.get("pause", 0.45)),
              "max_length": l.get("max_length")} for l in cfg["lines"]]
    gaps = sum(l["pause"] for l in lines[:-1])
    max_speed = float(cfg.get("max_speed", C.VOICE_MAX_SPEED))

    clips = record_lines(lines, out_dir, pace=pace, api_key=api_key)
    speech = sum(c["duration"] for c in clips)

    if cfg["film"] == "auto":
        film = round(math.ceil((open_s + speech + gaps + tail) * 10) / 10, 1)
    else:
        film = float(cfg["film"])
        target = film - open_s - tail - gaps
        speed = pace
        warned = False
        for _ in range(6):
            if speech <= target + 0.05:
                break
            speed = min(speed * speech / target, pace * max_speed)
            if not warned:
                # Lesson 2026-11-26: forcing the voice into a fixed film
                # length by varying the speed makes the pace wander and the
                # voice sound weird (the re-voiced hypnic film's voice was
                # judged "weird" for exactly this reason). Prefer
                # film="auto" and let the picture re-time to the voice
                # (align.py + build.py do that), or trim the script.
                print("WARNING: narration too long for a fixed "
                      f"{film} s film — raising speed to {speed:.3f}x. "
                      "Varying the speed makes the pace wander and the voice "
                      "sound uneven. Prefer film='auto' (film follows the "
                      "voice) or trim the script.")
                warned = True
            clips = record_lines(lines, out_dir, pace=speed, api_key=api_key)
            speech = sum(c["duration"] for c in clips)
        if speech > target + 0.05:
            print(f"WARNING: narration is {speech - target:.2f} s too long "
                  f"even at {speed:.3f}x. Trim the script or lengthen the film.")
    vo_raw, vo_timing = build_timeline(clips, open_s, film, out_dir)
    narr_end = open_s + sum(c["duration"] for c in clips) + gaps
    print(f"film {film} s, Fish voice at {clips[0]['speed']:.3f}x, "
          f"narration {open_s:.2f}-{narr_end:.2f} s, tail {film - narr_end:.2f} s")
    return {"film": film, "vo_raw": str(vo_raw),
            "vo_timing": str(vo_timing), "clips": clips}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Record Fish Audio narration (Wondenza voice) for a film.")
    ap.add_argument("--film-json", help="project film.json (lines/open/tail/film)")
    ap.add_argument("--text", help="record a single line of text")
    ap.add_argument("--out-dir", required=True, help="where clips + vo files go")
    ap.add_argument("--pace", type=float, default=C.VOICE_PACE)
    args = ap.parse_args()
    if args.film_json:
        record_film(Path(args.film_json), Path(args.out_dir), pace=args.pace)
    elif args.text:
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        raw = out / "clip_raw.wav"
        final = out / "clip.wav"
        synthesize(args.text, raw, speed=args.pace)
        trims = trim_clip(raw, final)
        print(f"wrote {final} ({trims['duration']:.2f} s, trims {trims})")
    else:
        ap.error("give --film-json or --text")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
