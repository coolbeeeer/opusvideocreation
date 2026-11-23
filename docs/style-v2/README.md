# Style v2 demo: the antibiotics "resistance" scene

The same 8.24 s scene as `projects/antibiotics/compositions/resistance.html`, with the same narration, word cues and
beats, redrawn with the upgrades from `docs/11-style-upgrade.md`. The shipped antibiotics film is unchanged.

| File | What it is |
|---|---|
| `resistance-v1-vs-v2.jpg` | Three moments of the scene: repo version above, v2 below, with the empty-background share of each frame |
| `resistance-v1-vs-v2.mp4` | The 8 s scene side by side with sound (v2's audio) |
| `resistance-v2.html` | Drop-in replacement for `projects/antibiotics/compositions/resistance.html` |
| `js_events-v2.cjs` | Replacement for `projects/antibiotics/audio/js_events.cjs` (the cells sit in new places) |
| `antibiotics-v2-frame-stats.txt` | `tools/frame_stats.py` run on `antibiotics-v2.mp4`: the measurements behind doc 11 |

## Swap it into the antibiotics film
```bash
cd projects/antibiotics
cp ../../lib/kit-plus.js assets/
cp ../../docs/style-v2/resistance-v2.html compositions/resistance.html
cp ../../docs/style-v2/js_events-v2.cjs audio/js_events.cjs
# build.py writes index.html: add  <script src="assets/kit-plus.js"></script>  after the kit.js line in its template
python build.py
cd audio && node js_events.cjs && python sfx_cues.py && python music.py && python mix.py && cd ..
python build.py
npx hyperframes@0.9.56 render --fps 60 --quality delivery -o renders/antibiotics-v3.mp4
```
Expect the resistance scene to render about 2.7x slower than before, mostly because of its three SVG blur filters.
