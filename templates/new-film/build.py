"""Build the film skeleton from film.json + the measured word times.

Writes:
  assets/timing.js     window.VO = { words: [[key, start, end]], scenes: {id: {start, end, dur}}, lines, film }
  assets/timing.json   the same data for the Python audio scripts
  index.html           root composition: one host per scene, plus the audio stems that exist in assets/
Also rewrites data-duration inside compositions/<id>.html to match its host.

Scene boundaries: the first scene starts at 0 (it contains the cold open), every later scene starts halfway
through the pause before its first line, and the last scene ends at the end of the film.
Re-run after every voiceover change, and once more after the audio is mixed (to mount the tracks).
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "film.json").read_text())
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
    first, last = min(sc["lines"]), max(sc["lines"])
    start = 0.0 if i == 0 else round((LB[first - 1]["end"] + LB[first]["start"]) / 2, 3)
    scenes[sc["id"]] = {"start": start, "mood": sc.get("mood", "groove")}
for i, k in enumerate(ids):
    end = scenes[ids[i + 1]]["start"] if i + 1 < len(ids) else FILM
    scenes[k]["end"] = round(end, 3)
    scenes[k]["dur"] = round(end - scenes[k]["start"], 3)

payload = {"words": [[key(w["w"]), w["t"], w["e"]] for w in words], "scenes": scenes, "film": FILM,
           "open": vt["open"], "vo_end": lines[-1]["end"], "lines": lines}
(HERE / "assets" / "timing.json").write_text(json.dumps(payload))
(HERE / "assets" / "timing.js").write_text("window.VO = " + json.dumps(payload) + ";\n")

hosts = []
for z, (k, s) in enumerate(scenes.items()):
    hosts.append(f'      <div id="host-{k}" class="scene" style="z-index:{z + 1}" data-composition-id="{k}" data-composition-src="compositions/{k}.html" '
                 f'data-start="{s["start"]}" data-duration="{s["dur"]}" data-track-index="1" data-width="1920" data-height="1080"></div>')
    comp = HERE / "compositions" / f"{k}.html"
    if comp.exists():
        txt = comp.read_text()
        comp.write_text(re.sub(r'(data-composition-id="%s"[^>]*?data-duration=")[0-9.]+(")' % k, r"\g<1>%s\g<2>" % s["dur"], txt, count=1))
    else:
        print(f"WARNING: compositions/{k}.html does not exist yet")

audio = [f'      <audio id="track-{n}" src="assets/{n}.wav" data-start="0" data-duration="{FILM}" data-track-index="{10 + i}" data-volume="1"></audio>'
         for i, n in enumerate(["vo", "sfx", "music"]) if (HERE / "assets" / f"{n}.wav").exists()]

(HERE / "index.html").write_text(f"""<!doctype html>
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
      tl.set({{}}, {{}}, {FILM});
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
""")
for k, s in scenes.items():
    print(f"{k:12s} {s['start']:6.2f} - {s['end']:6.2f}  ({s['dur']:.2f} s, mood {s['mood']})")
print(f"audio tracks mounted: {len(audio)} of 3")
