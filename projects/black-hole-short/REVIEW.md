# What Happens If You Fall Into a Black Hole? (51.4 s, vertical): self-review

Final file: `renders/black-hole-v3.mp4`. 1080x1920, 30 fps, 1542 frames, 51.400 s, H.264 High (yuv420p,
4.9 Mb/s), AAC LC stereo 48 kHz (197 kb/s), 32.7 MB. Contact sheet from the MP4, one frame every 1.5 s:
`renders/black-hole-v3-contact.jpg`. Cover for Reels: `renders/black-hole-cover.jpg` (the title at 50.4 s).
v1 and v2 were superseded and are not included; `review/render-v1-every1.5s.jpg` shows the frames v1 was judged on.

## How it is built
- `film.json`: 8 lines with a pause after each, 7 scenes, 1080x1920, 30 fps.
- `vo.py` (Kokoro TTS, one call per line; `--clips` and `--recording` take your own voice), `align.py`
  (faster-whisper: 141 of 141 words matched), `build.py` (scenes, captions, `captions.srt`).
- Drawing: `lib/kit.js`, `lib/kit-plus.js`, `lib/kit-ocean.js` (scene layers, glows), `lib/kit-human.js` (the
  astronauts: the same rig as the walker, with new outfit and face options) and a new `lib/kit-space.js` (space stage,
  black hole, stars, nebula, clock, galaxy, ship, telescope, the noodle).
- Audio: `audio/sfx_cues.py`, `audio/music.py` (original score), `audio/mix.py` (-14 LUFS). `audio/cues.py` has a
  Python twin of the walk kit's `phaseTable`, so the friend scene's slowing clock ticks and the music's tape-stop use
  the same slowing-time keys as the picture.

## Pass 1: snapshots of each scene before rendering
Sheets in `review/` (`<scene>-v1.jpg` is the first look, `-v2` the fixed one).
| Scene | Problem | Fix |
|---|---|---|
| kit | Model sheet: the spaceship read as a flying saucer (aliens) | Redrawn as a capsule with a window, solar panels and an engine |
| kit | The weightless pose bent the knees so far it looked like riding a horse | Legs nearly straight, slight sway |
| kit | The first noodle wound in a spiral and read as a rope, starting at the hips | A straight noodle (a body falling straight in stretches along the line to the centre) with the helmet, a face and both arms still up |
| kit | Stretched past the shadow, the feet reappeared below the black hole | The black hole's `mid` layer (things falling in) is clipped at its centre line |
| hook | The giant black hole's glow showed from the first second and spoiled the reveal | It fades in on "It depends" while the camera pulls back |
| hook | The astronaut was small for an opening shot | Scale 0.58 -> 0.8 |
| hook | At the giant's size, the lensed arcs ended in lumps | Flat ends tucked under the disk |
| small | The noodle was too thin to read as a person | 42 px wide, thinning to 20, with the helmet, eye, "o" mouth and arms |
| small | The noodle was gone before "Spaghettification" appeared | It slides in under the banner |
| small | The pull arrows stood far from the body | Moved next to it |
| giant | "Event horizon" overlapped the astronaut | Astronaut moved right of the tag |
| giant | After the crossing, the lower half was a flat black field | Faint light falling inward, clipped to the inside |
| friend | The telescope view sat on the caption line | Smaller and higher; "Your friend" moved inside the safe area |
| inside | The friend's-view inset was almost black (the red tint had nothing bright to tint) | The black hole's glow drawn inside it |
| inside | The bright centre sat on the caption line; the countdown covered the helmet | Centre moved up, astronaut moved down; the clock gives way to the countdown |
| unknown | The bottom equation touched the captions | Moved up |
| finale | The spaceship and crew peeked in at the bottom from the start; the shrunk black holes sat behind the waving hands | Hidden until "Or better"; black holes smaller and higher |

Checker (`npx hyperframes@0.9.56 check`, default and `--samples=150`):
| Finding | Fix |
|---|---|
| "?" above the top safe edge of all three apps | Moved beside the helmet |
| "Center" outside TikTok's right edge (lower band), "Friend's view" outside its left edge | Moved and shrunk |
| Only with 150 samples: "0:12" above the Shorts top edge | Lower |
| Only with 150 samples: the halves of the broken equations fell out of the safe areas | Smaller moves, faster fade |
| Only with 150 samples: "BLACK HOLE?" past the Shorts right edge (184 px Yanone is 800 px wide) | 168 px, centred at x 505: the Shorts safe area is off-centre (x 48-888) |
| `container_overflow` on the three circular insets (their art is cut by the circle on purpose) | `data-layout-allow-overflow` on each inset |

## Pass 2: frames taken from the rendered MP4
| Check | Before | Fix | After |
|---|---|---|---|
| frame_stats: seconds over 70 % flat | v1: 34 of 51 | The stars were spread over an area 12 times the frame, so only about 30 were in view, and smooth nebula gradients count as flat. Stars now fill the area the camera can reach (about 230 in view), the mid layer has bigger stars with halos, and soft-edged nebula wisps and near-layer dust were added (`KS.stage`) | v2: 3 of 51 |
| Seek order: 10 frames from the MP4 against fresh seeks | v2: at 23.9 s 44 % of pixels differed | The giant scene set the disk's brightness after redrawing the black hole, so each frame showed the previous frame's value and a fresh seek showed the starting value. Values are now set before `update()` | v3: all 10 match (mean difference 1.1-1.5 of 255, compression) |
| Cut frames (`review/render-v3-cuts.jpg`) | | | Clean |

Accepted flat seconds: 21-22 s (the push-in to the edge, where the lensed glow becomes broad bands; motion 4.8-7.1)
and 48 s (one second before the title). Saturated pixels: 7.6 % at 31.3 s, the red-tinted telescope view ("turn
red"), over the 7 % guide on purpose. Measurements: `review/verify-v3.txt`, `review/frame-stats-v3.txt`.

## Measured on v3
- HyperFrames check: 0 errors, 0 warnings, 0 info in lint, runtime, layout (Shorts, Reels and TikTok safe areas),
  motion, contrast (10 of 10 text checks pass WCAG AA), craft and audio. The 150-sample layout run is also clean.
- Audio: -14.1 LUFS integrated (the stems sum to -14.0; the AAC encode moves it 0.1), -1.7 dBTP true peak, LRA
  1.9 LU. Voice -17.1 LUFS. While speaking, the music sits 13.3 dB and the effects 9.4 dB under the voice (RMS). The
  effects stem is levelled 1 dB lower than in the other films because this one has more of them under speech.
- Sync: 0.0 ms between the MP4's audio and the three stems. No black frames.
- Frames: mean flat background 60.7 %, 3 of 51 seconds over 70 %, mean brightness 47 of 255, median motion 1.4.
- Render: 65 s on 8 cores.

## Failed or open checks
- The voice is local Kokoro TTS (`af_heart`, 0.95x), a stand-in. `python vo.py --clips DIR` takes one recorded clip
  per line (steps in `projects/mitochondria-short/NOTES.md`, question 5).
- I cannot listen to audio; everything above is measured. Most worth a listen: the music slowing down and dropping in
  pitch in the friend scene (a tape-stop), the ticks spreading out with it, the stretch and slurp in the small scene,
  and the stutter on "break down".
- Word times come from speech recognition (faster-whisper `base.en`), accurate to roughly 0.1-0.2 s.
- Safe areas are HyperFrames' built-in boxes, and only text is checked against them. Check one upload on a phone.
- Not uploaded to YouTube or Instagram, so their re-encode is untested.
- Science simplifications are listed in `SCRIPT.md`: not to scale, non-rotating black holes, the black disk drawn as
  the horizon, and a stylised inside.
