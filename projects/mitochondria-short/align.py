"""Measure when every script word is spoken.

Transcribes assets/vo_raw.wav with faster-whisper (local; downloads the model once), aligns the recognised words
to the script in film.json, then moves each word that follows a pause to the real speech onset (whisper tends to
start those words early, inside the silence).

Writes assets/vo_words.json: [{"i", "w", "t", "e", "line", "src"}], times in film seconds.
"""
import difflib
import json
import re
from pathlib import Path

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "film.json").read_text())
audio, SR = sf.read(HERE / "assets" / "vo_raw.wav", dtype="float32")
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())

script = []
for li, line in enumerate(CFG["lines"], 1):
    for w in line["text"].split():
        script.append({"w": re.sub(r"[^A-Za-z0-9']", "", w), "line": li})

model = WhisperModel(CFG.get("whisper_model", "base.en"), device="cpu", compute_type="int8")
prompt = " ".join(l["text"] for l in CFG["lines"])
segs, _ = model.transcribe(str(HERE / "assets" / "vo_raw.wav"), word_timestamps=True, beam_size=5, language="en", initial_prompt=prompt)
heard = [{"w": w.word.strip(), "t": w.start, "e": w.end} for seg in segs for w in seg.words]

sm = difflib.SequenceMatcher(a=[norm(x["w"]) for x in script], b=[norm(x["w"]) for x in heard], autojunk=False)
match = {blk.a + k: blk.b + k for blk in sm.get_matching_blocks() for k in range(blk.size)}

out = []
for i, sw in enumerate(script):
    h = heard[match[i]] if i in match else None
    out.append({"i": i, "w": sw["w"], "t": h and round(h["t"], 3), "e": h and round(h["e"], 3), "line": sw["line"], "src": "heard" if h else "interp"})
for i, o in enumerate(out):  # fill unmatched words between their neighbours
    if o["t"] is None:
        prev = next((out[j] for j in range(i - 1, -1, -1) if out[j]["t"] is not None), None)
        nxt = next((out[j] for j in range(i + 1, len(out)) if out[j]["src"] == "heard"), None)
        o["t"] = round(prev["e"] if prev else CFG["open"], 3)
        o["e"] = round(nxt["t"] if nxt else o["t"] + 0.3, 3)

# words that follow a pause: move the start to the first 10 ms frame where speech energy rises
hop = int(SR * 0.01)
rms = np.array([np.sqrt(np.mean(audio[k * hop:(k + 1) * hop] ** 2)) for k in range(len(audio) // hop)])
for i, o in enumerate(out):
    gap = o["t"] - (out[i - 1]["e"] if i else 0.0)
    if i == 0 or gap > 0.12:
        a, b = int(o["t"] * 100), int(min(o["e"], o["t"] + 0.8) * 100)
        if b > a:
            local = rms[a:b]
            thr = max(rms[max(0, a - 20):b + 20].max() * 0.12, 1e-4)
            k = int(np.argmax(local > thr)) if np.any(local > thr) else 0
            o["t"] = round((a + k) / 100, 3)

# the first word of each line starts where vo.py placed the line (exact in TTS mode)
vt = json.loads((HERE / "assets" / "vo_timing.json").read_text())
starts = {l["line"]: l["start"] for l in vt.get("lines", [])}
seen = set()
for o in out:
    if o["line"] in starts and o["line"] not in seen:
        o["t"] = max(o["t"], starts[o["line"]])
        seen.add(o["line"])

(HERE / "assets" / "vo_words.json").write_text(json.dumps(out, indent=0))
miss = [o["w"] for o in out if o["src"] != "heard"]
print(f"{len(out)} script words, {len(out) - len(miss)} matched; unmatched: {miss or 'none'}")
print("  ".join(f"{o['t']:.2f} {o['w']}" for o in out))
