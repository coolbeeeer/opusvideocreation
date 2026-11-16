"""Word-level timing for the narration.

Transcribes assets/vo_raw.wav with faster-whisper (local, offline after the model download) and
aligns the recognised words to the approved script, so every script word gets a measured start time.
Writes assets/vo_words.json: [{"i": index, "w": word, "t": start, "e": end, "line": n}].
"""
import difflib
import json
import re
from pathlib import Path

from faster_whisper import WhisperModel

HERE = Path(__file__).resolve().parent
timing = json.loads((HERE / "assets" / "vo_timing.json").read_text())

norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
script = []
for L in timing["lines"]:
    for s in L["sentences"]:
        for w in s["text"].split():
            script.append({"w": re.sub(r"[^A-Za-z0-9']", "", w), "line": L["line"], "sent_start": s["start"], "sent_end": s["end"]})

model = WhisperModel("base.en", device="cpu", compute_type="int8")
segs, _ = model.transcribe(str(HERE / "assets" / "vo_raw.wav"), word_timestamps=True, beam_size=5, language="en",
                           initial_prompt=" ".join(s["text"] for L in timing["lines"] for s in L["sentences"]))
heard = [{"w": w.word.strip(), "t": w.start, "e": w.end} for seg in segs for w in seg.words]

a = [norm(x["w"]) for x in script]
b = [norm(x["w"]) for x in heard]
sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
match = {}
for blk in sm.get_matching_blocks():
    for k in range(blk.size):
        match[blk.a + k] = blk.b + k

out = []
for i, sw in enumerate(script):
    if i in match:
        h = heard[match[i]]
        out.append({"i": i, "w": sw["w"], "t": round(h["t"], 3), "e": round(h["e"], 3), "line": sw["line"], "src": "heard"})
    else:
        out.append({"i": i, "w": sw["w"], "t": None, "e": None, "line": sw["line"], "src": "interp"})
# fill unmatched words by interpolating between neighbours
for i, o in enumerate(out):
    if o["t"] is None:
        prev = next((out[j] for j in range(i - 1, -1, -1) if out[j]["t"] is not None), None)
        nxt = next((out[j] for j in range(i + 1, len(out)) if out[j]["src"] == "heard"), None)
        t0 = prev["e"] if prev else script[i]["sent_start"]
        t1 = nxt["t"] if nxt else script[i]["sent_end"]
        o["t"], o["e"] = round(t0, 3), round(t1, 3)
(HERE / "assets" / "vo_words.json").write_text(json.dumps(out, indent=0))
miss = [o["w"] for o in out if o["src"] != "heard"]
print(f"{len(out)} script words, {len(out) - len(miss)} matched to speech, unmatched: {miss}")
for o in out:
    print(f"{o['t']:6.2f} {o['w']}", end="   " if (o["i"] + 1) % 8 else "\n")
print()
