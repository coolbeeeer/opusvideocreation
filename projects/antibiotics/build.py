"""Builds the film skeleton from the narration timing.

Reads assets/vo_timing.json + assets/vo_words.json and writes:
  assets/timing.js    window.VO = { words: [[key, start, end], ...], scenes: {...}, lines: [...] }
  index.html          root composition: scene hosts placed on the voice timeline + audio stems
It also rewrites data-duration inside each compositions/<id>.html so it matches its host.
Re-run after any voiceover change; every scene re-times itself from window.VO.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
timing = json.loads((HERE / "assets" / "vo_timing.json").read_text())
words = json.loads((HERE / "assets" / "vo_words.json").read_text())
FILM = timing["film"]
L = {l["line"]: l for l in timing["lines"]}

# first word of each sentence: whisper tends to start it early inside the pause, so clamp to the sentence start
sent_starts = sorted(s["start"] for l in timing["lines"] for s in l["sentences"])
key = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
vo_words = []
for i, w in enumerate(words):
    t = w["t"]
    prev_end = words[i - 1]["e"] if i else 0
    starts_here = [s for s in sent_starts if prev_end - 0.05 <= s <= w["e"]]
    if starts_here:
        t = max(t, starts_here[-1])
    vo_words.append([key(w["w"]), round(t, 3), round(w["e"], 3)])

mid = lambda a, b: round((L[a]["end"] + L[b]["start"]) / 2, 3)
cuts = {
    "open": (0.0, L[1]["start"] + 0.10),
    "infection": (L[1]["start"] - 0.15, mid(2, 3)),
    "compare": (mid(2, 3), mid(3, 4)),
    "wall": (mid(3, 4), mid(5, 6)),
    "machines": (mid(5, 6), mid(6, 7)),
    "viruses": (mid(6, 7), mid(7, 8)),
    "resistance": (mid(7, 8), mid(8, 9)),
    "ending": (mid(8, 9), FILM),
}
scenes = {k: {"start": round(a, 3), "end": round(b, 3), "dur": round(b - a, 3)} for k, (a, b) in cuts.items()}

payload = {"words": vo_words, "scenes": scenes, "film": FILM, "vo_end": timing["vo_end"],
           "lines": [{"line": l["line"], "start": l["start"], "end": l["end"]} for l in timing["lines"]]}
(HERE / "assets" / "timing.json").write_text(json.dumps(payload))
(HERE / "assets" / "timing.js").write_text(
    "window.VO = " + json.dumps({"words": vo_words, "scenes": scenes, "film": FILM,
                                 "lines": [{"line": l["line"], "start": l["start"], "end": l["end"]} for l in timing["lines"]]}) + ";\n")

hosts = []
for z, (k, s) in enumerate(scenes.items()):
    hosts.append(
        f'      <div id="host-{k}" class="scene" style="z-index:{z + 1}" data-composition-id="{k}" data-composition-src="compositions/{k}.html" '
        f'data-start="{s["start"]}" data-duration="{s["dur"]}" data-track-index="1" data-width="1920" data-height="1080"></div>')
    comp = HERE / "compositions" / f"{k}.html"
    if comp.exists():
        txt = comp.read_text()
        txt = re.sub(r'(data-composition-id="%s"[^>]*?data-duration=")[0-9.]+(")' % k, r"\g<1>%s\g<2>" % s["dur"], txt, count=1)
        comp.write_text(txt)

audio = []
for i, (name, vol) in enumerate([("vo", 1.0), ("sfx", 1.0), ("music", 1.0)]):
    if (HERE / "assets" / f"{name}.wav").exists():
        audio.append(f'      <audio id="track-{name}" src="assets/{name}.wav" data-start="0" data-duration="{FILM}" data-track-index="{10 + i}" data-volume="{vol}"></audio>')

o = scenes["infection"]["start"]
index = f"""<!doctype html>
<html lang="en" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,800;0,900;1,800&family=Yanone+Kaffeesatz:wght@400;700&display=block" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <script src="assets/timing.js"></script>
    <script src="assets/kit.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #081a2a; }}
      #root {{ position: relative; width: 1920px; height: 1080px; overflow: hidden; font-family: "Nunito", sans-serif; }}
      .scene {{ position: absolute; inset: 0; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{FILM}" data-width="1920" data-height="1080">
{chr(10).join(hosts)}
{chr(10).join(audio)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      // crossfade from the cold open into the skin scene
      tl.fromTo("#host-infection", {{ opacity: 0 }}, {{ opacity: 1, duration: {round(scenes['open']['end'] - o, 3)}, ease: "power1.inOut" }}, {o});
      tl.set({{}}, {{}}, {FILM});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
(HERE / "index.html").write_text(index)
for k, s in scenes.items():
    print(f"{k:11s} {s['start']:6.2f} - {s['end']:6.2f}  ({s['dur']:.2f} s)")
