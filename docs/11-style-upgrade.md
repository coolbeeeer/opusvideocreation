# 11 · Getting closer to a Kurzgesagt frame

The method in this repo works: voice-timed cues, a sound on every event, measured checks and written review passes.
What separates the sample film from a Kurzgesagt frame is mostly the look and the writing. This page lists what was
measured, what was changed, and what is still open. The changes are in `lib/kit-plus.js`, `lib/kit-ocean.js`,
`tools/frame_stats.py`, the demo in `docs/style-v2/` and the vertical film `projects/ocean-glow-short/`.

## What the sample film measures
`tools/frame_stats.py` on frames decoded from `projects/antibiotics/renders/antibiotics-v2.mp4`
(`docs/style-v2/antibiotics-v2-frame-stats.txt`):

| Finding | Measurement | Why it matters |
|---|---|---|
| Large empty areas | 27 of 60 seconds have more than 70 % flat, untextured background; 14 of the 15 seconds from 39 s to 53 s (viruses, resistance), peaking at 91 % | Small subjects in a big empty field read as unfinished, more so on a phone |
| Dark | mean brightness 31-40 of 255 from 41 s to 53 s | Detail sinks on phones; smooth dark gradients band after YouTube's re-encode |
| Camera motion doesn't show | the camera always moves in code, yet 25 of 60 seconds change by less than 1 brightness level per 0.1 s | A slow drift over a flat gradient is invisible; textured layers at different speeds make it visible |
| Muted colour | 53 of 60 seconds have at most 1 % saturated pixels; lit dark scenes in the reference measured 6.7-7 % (`style/STYLE.md`) | The reference style is gradient-rich and saturated |
| No characters | cells and viruses have no faces | Personified cells that look, react and emote carry the humour |
| Voice rhythm | TTS per sentence with fixed 0.22 / 0.34 s gaps | Even, mechanical pacing; Kurzgesagt records whole paragraphs |
| Loudness | -15.8 LUFS | YouTube plays at about -14 LUFS and does not turn quiet uploads up |

## The upgrades
### Look (`lib/kit-plus.js`)
1. **Parallax depth.** `KP.rig(layers)` drives several layers from one camera (far 0.35x ... near foreground 1.75x).
   It is a drop-in for `K.camera()` and works with `K.camTo` and `K.shake`.
2. **Out-of-focus layers.** Blurred far shapes, large dark blurred foreground shapes cropped by the frame, soft dots.
3. **Light.** A soft pool behind the subject, a rim light from one world light direction (computed through each
   object's rotation), `KP.vignette()`.
4. **Faces.** `KP.eyes()` / `KO.eye()`: look direction, lids, blinks, fear. Animate with `KP.eyeTo` and `KP.blink`.
5. **Keep the field full.** What an event leaves behind stays on screen (husks after a pop, molecules drifting on).
6. **Composition.** When the field thins, push the camera in until the subject fills the frame, then ease back out.
7. **Labels pinned to world points:** `cam.pin(el, x, y)` keeps tags on their objects through camera moves.
8. **Grain** (`KP.grain`), optional: seeded, 24 changes per second. It costs render time and about 5x file size.

### Writing
- Write in the Kurzgesagt voice: a hook in the first line, "you", characters with feelings, one joke per beat, a turn
  ("But ..."), and a close that zooms out. See `projects/ocean-glow-short/SCRIPT.md`.
- Give every claim a source in the script's accuracy notes, and say "likely" where science says "probably".
- Review a storyboard (one still per beat) before animating; stills are cheap to change.

### Voice and sound
- One TTS call per line (a short paragraph) and a pause per line in `film.json`, longer before punchlines.
  `projects/ocean-glow-short/vo.py` does this. Best of all is your own recording.
- Master to -14 LUFS integrated with true peak at or below -1 dBTP (`projects/ocean-glow-short/audio/mix.py`).

### Checks
- `tools/frame_stats.py film.mp4` after every render: flag seconds over 70 % flat or nearly motionless, then look
  at those frames. Darkness can be the point (a midnight zone); write that down in REVIEW.md instead of hiding it.

## Demo: the resistance scene, v1 vs v2 (`docs/style-v2/`)
| Measured on the rendered clip | v1 (repo) | v2 |
|---|---|---|
| Mean empty background | 78.6 % | 59.1 % |
| Seconds more than 70 % empty | 5 of 8 | 0 of 8 |
| Mean brightness (0-255) | 35.8 | 48.0 |
| Median motion | 1.60 | 2.60 |

Render cost for 2 s of film at 60 fps (8 cores, about 7 s of it start-up): v1 12.4 s, v2 33.5 s, v2 without its three
blur filters 17.7 s, v2 without grain 29.1 s. Use pre-blurred shapes or `KP.softDot` (a radial gradient, no filter)
where you can.

Two v1 bugs found on the way: the cell-placement loop kept its last failed try, so some cells were stacked on top of
each other; and the fourth bounced molecule faded out on top of another survivor.

## Measured on the vertical film (`projects/ocean-glow-short/`)
15 of 54 seconds over 70 % flat (the darkness of the midnight zone is part of the story), -14.0 LUFS, -1.6 dBTP, 0 ms
sync, and a clean HyperFrames check including the Shorts, Reels and TikTok safe areas. Its REVIEW.md has the details.
Correction: `tools/frame_stats.py` squashed vertical frames into 480x270 at the time; with the aspect kept, the same
render measures 26 of 54 seconds over 70 % flat.

## Measured on the walking-human film (`projects/mitochondria-short/`)
4 of 50 seconds over 70 % flat (v1 had 23, fixed with a low-contrast cell-interior backdrop, `KC.cytoplasm`),
-14.0 LUFS, -1.6 dBTP, 0 ms sync, a clean HyperFrames check, and a 150-sample safe-area scan. Its REVIEW.md and
NOTES.md have the details.

## Still open
- A recurring musical theme per channel and real instrument timbres (for example a MIDI score rendered through a
  freely licensed SoundFont).
- Shape morphs and line drawing with GSAP's MorphSVG and DrawSVG plugins, free since April 2025
  ([gsap.com](https://gsap.com/blog/3-13/)).
- HyperFrames is pinned at 0.9.56; newer versions exist. Upgrade only after a regression render of `templates/new-film`.
  HyperFrames sends anonymous usage telemetry by default; `npx hyperframes telemetry disable` turns it off.
