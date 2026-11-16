"""Voiceover + timing map for the antibiotics film.

Voice: local Kokoro TTS (af_heart), offline, not a voice MCP. It stands in for your own recording.
Each sentence is synthesised separately, so every sentence start is known exactly.
Comma and colon pauses inside a sentence are found from the audio energy, and word starts
are estimated from letter counts inside each clause.

Writes:
  assets/vo_raw.wav       48 kHz mono narration, placed on the film timeline
  assets/vo_timing.json   line, sentence, clause and word times in film seconds
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from scipy.signal import resample_poly

HERE = Path(__file__).resolve().parent
# Kokoro model files (kokoro-v1.0.onnx + voices-v1.0.bin). See docs/01-environment.md for the download.
MODEL = Path(os.environ.get("KOKORO_DIR", HERE / "models" / "kokoro"))
VOICE = "af_heart"
SR_OUT = 48_000

FILM = 60.0
OPEN = 5.3          # cold open before the first word (person takes the capsule, zoom inside)
TAIL = 1.7          # end card hold after the last word
GAP_SENT = 0.22     # pause between sentences inside a line
GAP_LINE = 0.34     # pause between lines

# The approved script, split into sentences (text unchanged).
LINES = [
    ["A tiny cut.", "Within minutes, bacteria slip inside.", "One becomes two, two become four.", "Within hours, millions."],
    ["Usually your immune system wins.", "When it can't, doctors call in help: antibiotics."],
    ["They work because bacteria are built differently from your cells."],
    ["Most bacteria wear a stiff wall, like armour.", "Your cells don't.", "Penicillin targets that wall."],
    ["It jams the tools that build it.", "The wall springs leaks, water rushes in, and the bacterium bursts."],
    ["Other antibiotics block its protein factories, or stop it copying its DNA.", "Either way, it can't multiply."],
    ["But antibiotics only work on bacteria.", "Against viruses, like colds or flu, they do nothing."],
    ["And every time they're used, bacteria that resist them survive, multiply and share their defences.", "That's antibiotic resistance."],
    ["So take them only when prescribed, exactly as prescribed."],
]

kok = Kokoro(str(MODEL / "kokoro-v1.0.onnx"), str(MODEL / "voices-v1.0.bin"))


def synth(text: str, speed: float) -> tuple[np.ndarray, int]:
    audio, sr = kok.create(text, voice=VOICE, speed=speed, lang="en-us")
    return audio.astype(np.float32), sr


def gaps_total() -> float:
    return sum(GAP_SENT * (len(l) - 1) for l in LINES) + GAP_LINE * (len(LINES) - 1)


def render_all(speed: float):
    clips = [[synth(s, speed) for s in line] for line in LINES]
    sr = clips[0][0][1]
    speech = sum(len(a) / sr for line in clips for a, _ in line)
    return clips, sr, speech


def pauses_in(audio: np.ndarray, sr: int, k: int) -> list[float]:
    """Return the centres of the k longest internal low-energy runs (seconds from clip start)."""
    if k == 0:
        return []
    hop = int(sr * 0.01)
    frames = len(audio) // hop
    rms = np.array([np.sqrt(np.mean(audio[i * hop:(i + 1) * hop] ** 2)) for i in range(frames)])
    thr = max(rms.max() * 0.06, 1e-4)
    quiet = rms < thr
    runs, i = [], 0
    while i < frames:
        if quiet[i]:
            j = i
            while j < frames and quiet[j]:
                j += 1
            if i > 5 and j < frames - 5 and (j - i) >= 4:  # internal, at least 40 ms
                runs.append((j - i, (i + j) / 2 * 0.01))
            i = j
        else:
            i += 1
    runs.sort(reverse=True)
    return sorted(t for _, t in runs[:k])


def clause_split(text: str) -> list[str]:
    parts = re.split(r"(?<=[,:])\s+", text)
    return [p for p in parts if p]


def word_times(clause: str, t0: float, t1: float) -> list[dict]:
    words = clause.split()
    weights = [len(re.sub(r"[^A-Za-z0-9']", "", w)) + 1.5 for w in words]
    total = sum(weights)
    out, t = [], t0
    for w, wt in zip(words, weights):
        out.append({"w": re.sub(r"[^A-Za-z0-9']", "", w), "t": round(t, 3)})
        t += (t1 - t0) * wt / total
    return out


# ---- solve the speaking speed so the narration fits between the open and the end card
target_speech = FILM - OPEN - TAIL - gaps_total()
speed = 1.0
for _ in range(3):
    clips, sr, speech = render_all(speed)
    if speech <= target_speech + 0.05:
        break
    speed = float(np.clip(speed * speech / target_speech, 1.0, 1.08))
print(f"speed {speed:.3f}, speech {speech:.2f} s, target {target_speech:.2f} s")

# ---- lay the sentences on the film timeline
timeline = np.zeros(int(FILM * sr), dtype=np.float32)
t = OPEN
lines_out = []
for li, line in enumerate(clips):
    line_start = t
    sents = []
    for si, (audio, _) in enumerate(line):
        text = LINES[li][si]
        d = len(audio) / sr
        i0 = int(round(t * sr))
        timeline[i0:i0 + len(audio)] += audio
        clauses = clause_split(text)
        cuts = pauses_in(audio, sr, len(clauses) - 1)
        if len(cuts) != len(clauses) - 1:  # fall back to letter-proportional split
            lens = np.cumsum([len(c) for c in clauses])
            cuts = list(lens[:-1] / lens[-1] * d)
        bounds = [0.0] + cuts + [d]
        cl_out, words = [], []
        for ci, c in enumerate(clauses):
            a, b = t + bounds[ci], t + bounds[ci + 1]
            cl_out.append({"text": c, "start": round(a, 3), "end": round(b, 3)})
            words += word_times(c, a + (0.03 if ci else 0.0), b - 0.06)
        sents.append({"text": text, "start": round(t, 3), "end": round(t + d, 3), "clauses": cl_out, "words": words})
        t += d + (GAP_SENT if si < len(line) - 1 else 0.0)
    lines_out.append({"line": li + 1, "start": round(line_start, 3), "end": round(t, 3), "sentences": sents})
    t += GAP_LINE

vo_end = lines_out[-1]["end"]
out48 = resample_poly(timeline, SR_OUT, sr).astype(np.float32)
(HERE / "assets").mkdir(exist_ok=True)
sf.write(HERE / "assets" / "vo_raw.wav", out48, SR_OUT)
meta = {"voice": VOICE, "speed": round(speed, 3), "film": FILM, "open": OPEN, "vo_end": round(vo_end, 3), "lines": lines_out}
(HERE / "assets" / "vo_timing.json").write_text(json.dumps(meta, indent=1))
for L in lines_out:
    print(f"line {L['line']}: {L['start']:6.2f}-{L['end']:6.2f}  " + " | ".join(f"{s['start']:.2f}" for s in L["sentences"]))
print(f"narration ends {vo_end:.2f} s, end card holds {FILM - vo_end:.2f} s")
