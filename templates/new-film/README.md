# new-film: starter project

A working, tested 9.8 s example (`renders/example.mp4`) of the whole pipeline, driven by one config file.
Copy this folder, edit `film.json`, write one HTML file per scene, run the steps. Nothing else is hardcoded.

## Steps
```bash
cp -r templates/new-film projects/my-film && cd projects/my-film
# 1. edit film.json: lines (the approved script, split into sentences), scenes (which lines each covers + mood)
export KOKORO_DIR=/path/to/kokoro            # TTS mode only (docs/01-environment.md)
python vo.py                                 # or: python vo.py --recording my_voice.wav
python align.py                              # word times -> assets/vo_words.json
python build.py                              # scene hosts + assets/timing.js
# 2. write compositions/<scene-id>.html for every scene (copy intro.html as a starting point)
npx hyperframes check && npx hyperframes snapshot --at 1,3,5
# 3. audio
cd audio && python sfx_cues.py && python music.py && python mix.py && cd ..
python build.py                              # again, to mount vo/sfx/music tracks
# 4. render
npx hyperframes render --fps 60 --quality delivery -o renders/my-film.mp4
```

## film.json
| key | meaning |
|---|---|
| `film` | `"auto"` = as long as the narration needs, or a number of seconds (TTS speed is solved to fit, up to `max_speed`) |
| `open` | seconds of picture before the first word (a cold open) |
| `tail` | seconds after the last word (end card / title) |
| `lines` | the script: a list of lines, each a list of sentences. Lines are the unit scenes are built from |
| `scenes` | in order: `id` (= `compositions/<id>.html`), `lines` it covers, `mood` for music.py (`warm tense groove playful dark resolve`) |
| `voice`, `lang` | Kokoro voice and language (`af_heart`, `bm_george`, `am_michael`, ...) |

## What each scene file must do
See `compositions/intro.html`, it is commented. The rules: wrap in `<template>`, scope CSS with
`[data-composition-id="<id>"]`, prefix SVG ids with the scene id, use `K.t(word, n, T0) - T0` for every cue,
seeded randomness only, `svgOrigin: "0 0"` on anything you rotate/scale, register `window.__timelines["<id>"]`.

## Sound cues
`audio/sfx_cues.py` must schedule sounds with the **same formulas** as the scene animation (`w("splits") - 0.1`
in both places). `pop_word()` matches the timing of `kit.show()`; call it for every tag/banner.
