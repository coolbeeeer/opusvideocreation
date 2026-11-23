"""Build the film skeleton from film.json + the measured word times. Vertical-aware (width/height from film.json).

Writes:
  assets/timing.js     window.VO = { words: [[key, start, end]], scenes, lines, film, caps }
  assets/timing.json   the same data for the Python audio scripts
  captions.srt         burned-in caption chunks, also for uploading as a subtitle track
  index.html           root composition: one host per scene, the captions layer, and the audio stems in assets/
Also rewrites data-duration inside compositions/<id>.html to match its host.

Scene boundaries: the first scene starts at 0, every later scene starts halfway through the pause before its first
line, and the last scene ends at the end of the film. Re-run after every voiceover change and after mixing audio.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "film.json").read_text())
W, H, FPS = int(CFG.get("width", 1920)), int(CFG.get("height", 1080)), int(CFG.get("fps", 30))
vt = json.loads((HERE / "assets" / "vo_timing.json").read_text())
words = json.loads((HERE / "assets" / "vo_words.json").read_text())
FILM = float(vt["film"])
key = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())

lines = {}
for w in words:
    L = lines.setdefault(w["line"], {"line": w["line"], "start": w["t"], "end": w["e"]})
    L["start"], L["end"] = min(L["start"], w["t"]), max(L["end"], w["e"])
lines = [lines[k] for k in sorted(lines)]
LB = {l["line"]: l for l in lines}

scenes, ids = {}, [s["id"] for s in CFG["scenes"]]
for i, sc in enumerate(CFG["scenes"]):
    first = min(sc["lines"])
    start = 0.0 if i == 0 else round((LB[first - 1]["end"] + LB[first]["start"]) / 2, 3)
    scenes[sc["id"]] = {"start": start, "mood": sc.get("mood", "glow")}
for i, k in enumerate(ids):
    end = scenes[ids[i + 1]]["start"] if i + 1 < len(ids) else FILM
    scenes[k]["end"] = round(end, 3)
    scenes[k]["dur"] = round(end - scenes[k]["start"], 3)

# ------------------------------------------------------------------ caption chunks (2-3 words, broken at punctuation and pauses)
display = [tok for l in CFG["lines"] for tok in l["text"].split()]
assert len(display) == len(words), "film.json and vo_words.json disagree; re-run align.py"
WEAK = {"a", "an", "the", "of", "in", "to", "by", "with", "from", "its", "their", "and", "can", "one", "this", "is"}
caps, cur = [], []
for i, (tok, w) in enumerate(zip(display, words)):
    if cur:
        prev_tok, prev_w = cur[-1]
        text = " ".join(t for t, _ in cur) + " " + tok
        hard = prev_tok[-1] in ".?!,;:" or w["t"] - prev_w["e"] > 0.35 or w["line"] != prev_w["line"]
        soft = len(cur) >= 4 or len(text) > 16
        if soft and not hard and key(prev_tok) in WEAK and len(text) <= 19:
            soft = False            # don't end a caption on "the", "of", "with" ...
        if hard or soft:
            caps.append(cur)
            cur = []
    cur.append((tok, w))
caps.append(cur)
chunks = []
for i, c in enumerate(caps):
    t0 = c[0][1]["t"] - 0.04
    nxt = caps[i + 1][0][1]["t"] - 0.04 if i + 1 < len(caps) else FILM
    t1 = min(nxt, c[-1][1]["e"] + 0.45)
    chunks.append({"start": round(t0, 3), "end": round(t1, 3), "words": [[t, round(w["t"], 3)] for t, w in c]})


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


(HERE / "captions.srt").write_text("".join(f"{i + 1}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{' '.join(t for t, _ in c['words'])}\n\n"
                                          for i, c in enumerate(chunks)))

payload = {"words": [[key(w["w"]), w["t"], w["e"]] for w in words], "scenes": scenes, "film": FILM, "open": vt["open"],
           "vo_end": lines[-1]["end"], "lines": lines, "caps": chunks if CFG.get("captions", True) else [], "W": W, "H": H}
(HERE / "assets" / "timing.json").write_text(json.dumps(payload))
(HERE / "assets" / "timing.js").write_text("window.VO = " + json.dumps(payload) + ";\n")

hosts = []
all_comps = list(scenes.items()) + ([("captions", {"start": 0.0, "dur": FILM})] if CFG.get("captions", True) else [])
for z, (k, s) in enumerate(all_comps):
    lane = ' data-track-index="2" data-track-kind="captions"' if k == "captions" else ' data-track-index="1"'
    hosts.append(f'      <div id="host-{k}" class="scene" style="z-index:{z + 1}" data-composition-id="{k}" data-composition-src="compositions/{k}.html" '
                 f'data-start="{s["start"]}" data-duration="{s["dur"]}"{lane} data-width="{W}" data-height="{H}"></div>')
    comp = HERE / "compositions" / f"{k}.html"
    if comp.exists():
        txt = comp.read_text()
        comp.write_text(re.sub(r'(data-composition-id="%s"[^>]*?data-duration=")[0-9.]+(")' % k, r"\g<1>%s\g<2>" % s["dur"], txt, count=1))
    else:
        print(f"WARNING: compositions/{k}.html does not exist yet")

audio = [f'      <audio id="track-{n}" src="assets/{n}.wav" data-start="0" data-duration="{FILM}" data-track-index="{10 + i}" data-volume="1"></audio>'
         for i, n in enumerate(["vo", "sfx", "music"]) if (HERE / "assets" / f"{n}.wav").exists()]

(HERE / "index.html").write_text(f"""<!doctype html>
<html lang="en" data-resolution="{'portrait' if H > W else 'landscape'}">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,800;0,900;1,800&family=Yanone+Kaffeesatz:wght@400;700&display=block" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <script src="assets/timing.js"></script>
    <script src="assets/kit.js"></script>
    <script src="assets/kit-plus.js"></script>
    <script src="assets/kit-ocean.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: #020a1c; }}
      #root {{ position: relative; width: {W}px; height: {H}px; overflow: hidden; font-family: "Nunito", sans-serif; }}
      .scene {{ position: absolute; inset: 0; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{FILM}" data-width="{W}" data-height="{H}" data-fps="{FPS}">
{chr(10).join(hosts)}
{chr(10).join(audio)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      tl.set({{}}, {{}}, {FILM});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
""")
for k, s in scenes.items():
    print(f"{k:10s} {s['start']:6.2f} - {s['end']:6.2f}  ({s['dur']:.2f} s, mood {s['mood']})")
print(f"film {FILM} s at {W}x{H}; {len(chunks)} caption chunks; audio tracks mounted: {len(audio)} of 3")
