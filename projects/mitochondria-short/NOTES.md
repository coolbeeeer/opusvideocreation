# Notes: how this film was made, answering your seven questions

Each answer gives the rule first, then how it worked in this film and where the code is. File references are to
this repo; search for the function names, because line numbers drift.

---

## 1. How the human and the walk cycle are built

**A procedural, articulated rig. There are no keyframes.** Every pose is computed from one number, the walk phase
(1 = one full cycle = two steps). Easing lives inside the gait curves, not in tweens. Code: `lib/kit-human.js`
(about 300 lines; read it top to bottom). Diagram: [`docs/walk-cycle.svg`](../../docs/walk-cycle.svg), drawn from
the same maths by `node tools/walk_cycle_svg.cjs`.

### The body (`KH.human`)
- Rigid parts between joints: pelvis, torso, neck, head; shoulder, upper arm, forearm, hand; hip, thigh, shin, foot.
  Sizes are in `KH.DIM` (thigh 168 px, shin 158, torso 214, head radius 56, upper arm 118, forearm 108: an adult
  about 690 px tall).
- Every frame each part is redrawn from its two joint positions. Limbs are tapered capsules (`KH.taper`: two
  circles joined by their outer tangents), so knees and elbows bend without seams. The torso is a rounded
  trapezoid from pelvis to shoulders that leans with the pose. The head is drawn once in profile (face, hair,
  eye, nose, mouth, cheek) and moved and tilted as one group.
- Depth in a flat style: the far arm and far leg are drawn first and 22 % darker (`LOOK.far = 0.78`), then the near
  leg, a "seat of the trousers" shape that hides the hip joints, the torso, the head, and the near arm.
- A look is data. `KH.LOOK` holds the colours and `hairStyle` ("short" or "long"); Mom in `compositions/mother.html`
  is the same rig with a different `look`.

### The walk (`KH.walkPose(phase)`)
Pure maths in a body frame (x forward, y up, ground at 0). It also runs in Node; `audio/js_events.cjs` uses it.
- **Feet** (`KH.footAt`): each foot is planted for 62 % of the cycle and slides backwards at exactly the walking
  speed, so in the world it stands still. At heel strike the foot rolls down from 12 degrees toe-up onto the heel
  (first 10 % of the stance), stays flat, then rolls up onto the toe to 32 degrees (last 28 %). In the swing the
  ankle travels forward on an eased arc: smoothstep forward, a 44 px lift shaped by sin^1.2, toes up 10 degrees.
- **Knees**: two-bone inverse kinematics from hip to ankle (`KH.solveLeg`), always bending forward. If the ankle is
  out of reach the bones stretch by up to 2 % (invisible) instead of snapping.
- **Pelvis**: bobs 20 px twice per cycle, highest at mid-stance, when the standing leg is straight.
- **Torso and head**: a 5 degree forward lean with a 1.2 degree wobble twice per cycle; the head counter-tilts.
- **Arms**: swing 24 degrees opposite the legs, 0.06 of a cycle late; elbows bend 14 degrees, up to 26 on the
  forward swing.
- The other leg and arm are the same functions at phase + 0.5.
- Numbers (`KH.GAIT`): one cycle is 1.15 s, the stance stride 280 px, so the body moves 451.6 px per cycle,
  392.7 px/s.

### Why the feet do not slide
`KH.walker` moves the whole figure by `x = x0 + phase * 451.6`, exactly the distance a planted foot slides back in
the body frame. Measured in Node over a cycle: the planted foot moves 1e-13 px per frame in world space, which is
rounding noise. The strobe in `docs/walk-cycle.svg` shows it: the copies of a planted foot print one solid footprint.

### Changing speed: `KH.phaseTable`
A scene describes speed as keys, not poses. `compositions/walk.html` uses
`[[0, 1], [tDive - 0.3, 1], [tDive + 0.6, 0.1], [DUR, 0.08]]`: normal pace, then 10 % while the camera dives into
the leg. `phaseTable` eases the rate between keys (smoothstep) and integrates it in 1/240 s steps into `phase(t)`.
Position and pose both come from that phase, so the feet stay planted at any speed, and any frame can be rendered
on its own (the renderer seeks frames in any order). `phase.strikes(ta, tb)` lists the heel strikes;
`audio/js_events.cjs` uses the same keys to place the footstep sounds, and the score's beat (0.575 s) is one step.

### Poses that are not walks
Start from `KH.standPose()` and bend arms with `KH.armTo(pose, arm, upperArmDegrees, elbowDegrees)` (angles from
hanging down, + = forward). Mom's wave is `KH.armTo(pose, 0, 112, 55 + 24 * sin(...))`, recomputed every frame;
"you" holds a hand on the chest with `(25, 115)`.

### Why not keyframes or motion paths
- Keyframed limbs slide on the ground as soon as the speed or timing changes, and every re-time means re-keying.
  Here a re-time is an edit to the speed keys.
- GSAP's motion path with auto-rotation was tried in this repo's first ant test and failed: on a slope the ant
  floated off the ground and pivoted around its middle (`docs/10-making-of.md`).

### How to study it
1. `node -e "const KH=require('./lib/kit-human.js'); console.log(KH.walkPose(0.31).legs[0])"` from the repo root.
2. Open `docs/walk-cycle.svg`, then change `KH.GAIT` (try `stance: 0.55` or `bob: 40`) and run
   `node tools/walk_cycle_svg.cjs` again.
3. In the film: `assets/world.js` puts a `KH.walker` on the park path; `compositions/walk.html` calls
   `S.walker.at(phase(t))` every frame and keeps the camera on it with `S.followX(phase)`.

---

## 2. How long the pause after each line is

**Rule of thumb: about 0.5 s between lines of one thought; 0.6-0.8 s after a punchline or a question, at a change
of topic, or where the picture needs time for a transition; 0 after the last line (a 2-3 s tail holds the title).**

Why it matters for the picture: `build.py` starts each scene halfway through the pause before its first line, so
the pause is the room the cut or transition gets. A longer pause also lets a joke land.

This film:
| After line | Pause | Reason |
|---|---|---|
| 1 "...Well, former bacteria." | 0.8 s | a punchline, and the camera has to slow the walk before the dive |
| 2 "...thousands of mitochondria." | 0.7 s | the push onto one mitochondrion and the match cut into the past |
| 3 "...It moved in." | 0.8 s | the end of the origin story (a topic change) and the suitcase gag |
| 4 "...Lots of it." | 0.6 s | a short beat, same story continues |
| 5 "...just like bacteria." | 0.6 s | a short beat |
| 6 "...every single day." | 0.7 s | a big number needs a moment |
| 7 "...Thanks, Mom." | 0.8 s | a joke, and the cut back inside the leg |
| 8 | 0 | the tail (2.85 s) holds the title |

How to check a pause: snapshot the cut (`./dev.sh <cut-0.1>,<cut+0.1> cut`) and watch the render around it. If a
transition feels rushed, add 0.1-0.2 s and re-run `vo.py`, `align.py`, `build.py`; everything is keyed to word
times, so nothing else needs editing. If it drags, the checker's craft pass reports a dead stretch. Total speaking
rate here: 125 words in 50.6 s, about 150 words per minute, which suits a Short.

---

## 3. Grain: when to use it and when to skip it

**Use grain on 16:9 long-form masters with large dark gradients, and only after a banding test. Skip it for
Shorts and Reels and for bright, flat-colour scenes.** This film has no grain (50.6 s, 34 MB).

- What grain is for: the platforms re-encode every upload. Smooth dark gradients (a deep-sea background, a night
  sky) then break into visible bands. Fine noise hides the steps.
- Why it is expensive: noise is the hardest thing for an encoder to compress, so the file grows about 5x
  (`docs/11-style-upgrade.md`). The render-time cost is smaller than it looks: in that test grain added 4.4 s to a
  33.5 s render (about 15 %), while the scene's three blur filters added 15.8 s. If renders are slow, remove blur
  filters first (`KP.softDot` gives soft shapes without a filter).
- Why skip it on Shorts and Reels: the apps re-encode vertical uploads at low bitrates, so grain turns into blocky,
  crawling noise; the upload also gets much bigger. Phone screens are small, so the bands that grain would hide are
  less visible anyway.
- Banding test, when in doubt: render 3 s of the darkest gradient with and without grain, re-encode both at a low
  bitrate (for example `ffmpeg -i in.mp4 -c:v libx264 -crf 30 out.mp4`) and compare on a phone. Add grain only if
  the version without it bands.
- Cheaper ways to break up a gradient: a vignette (`KP.vignette`), drifting particles (`KO.snow`), soft dots
  (`KP.softDot`), or a low-contrast background layer such as `KC.cytoplasm` in this film. They add structure the
  encoder can keep, at a fraction of the cost.

---

## 4. When frame_stats flags a second as too empty: fix it or accept it?

**Fix it when any of these is true:**
1. the subject is small or missing, so the frame says nothing;
2. it is in the first 3 seconds (the hook decides whether people swipe away);
3. it lasts more than about 2 seconds in a row;
4. the motion column is near zero at the same time (under about 0.5): the frame looks frozen.

**Accept it when** the emptiness is literally the subject (the dark midnight zone in the ocean film), or it is a
beat of a second or less (a transition, a breath before a punchline). Write each accepted second in `REVIEW.md`
with the reason, so the next person does not "fix" it.

**How to fix it:** add depth, not clutter. A low-contrast background layer, a bigger subject or a slow push-in, or
the next beat moved earlier. Never fill a frame with extra labels.

This film:
- v1 measured 23 of 50 seconds over 70 % flat, including 20 seconds in a row (23-42 s: proof, ATP, mother), with
  motion as low as 0.06 in the proof scene. Rules 3 and 4 say fix. I added `KC.cytoplasm`, an out-of-focus cell
  interior (wavy membrane folds, soft organelle shapes, drifting molecules at 3-12 % opacity), behind those scenes.
  v2 measures 4 of 50.
- Accepted: 11-12 s (the match cut into the past: the closing and opening vignette is the transition), 14 s (one
  second while the big cell closes around the bacterium) and 23 s (the first second of the proof scene).
- While doing this I found that `tools/frame_stats.py` squashed vertical films into 480x270, so every block was
  27x85 px of the original. It now keeps the aspect ratio. Re-measured, the ocean Short has 26 flagged seconds
  instead of the 15 its review reported; the rule above applies to it too.

---

## 5. Can vo.py use pre-recorded clips instead of Kokoro?

**Yes: `python vo.py --clips DIR`, one audio file per line of `film.json`.** Tested here with simulated 44.1 kHz
stereo clips with room noise: all 125 words matched, and every line's first word landed 0.06-0.10 s after the line
start.

```bash
# 1. One file per film.json line, named so they sort in order: 01.wav, 02.wav ... 08.wav
#    (wav, flac, ogg or aiff; any sample rate; mono or stereo). Each clip says exactly that line's text.
python vo.py --clips path/to/clips      # trims silence and room noise at both ends, resamples to 48 kHz,
                                        # one gain for all clips, lays them out with film.json's pauses
python align.py                         # word times by speech recognition, pinned to each line's start
python build.py
cd audio && node js_events.cjs && python sfx_cues.py && python music.py && python mix.py && cd ..
python build.py                         # mounts the new stems
npx hyperframes@0.9.56 check && npx hyperframes@0.9.56 render --fps 30 --quality delivery -o renders/new.mp4
```

- Nothing is time-stretched. With `"film": "auto"` the film takes the length the clips need, and every animation,
  sound and caption moves with it, because all of them are keyed to word times. With a fixed length, `vo.py` warns
  when the clips do not fit.
- The trim finds speech by loudness (30 ms RMS frames; anything 30 dB under the clip's loud part is silence), so a
  noise floor does not keep 1-2 s of room tone. `--no-trim` keeps the clips as they are.
- If the text in a clip differs from `film.json` (an ad-lib), edit `film.json` to match, or `align.py` reports the
  unmatched words.
- One continuous recording instead of clips: `python vo.py --recording take.wav`.
- The template in `templates/new-film/` still has the older sentence-based `vo.py` without `--clips`; start new
  Shorts from this folder (or `ocean-glow-short`) to get it.

---

## 6. How the dive from the wide shot into the cell works

**One continuous zoom through nested levels (`KP.zoomChain` in `lib/kit-plus.js`), driven by a single log-zoom
value.** No cuts, no giant layer.

1. **Four levels, each drawn once in its own units** (`assets/world.js`): the park with the walker (level 0); the
   thigh in cross-section with skin, fat, muscle bundles and the bone (level 1, `KC.thighSection`); one bundle full
   of muscle fibres (level 2, `KC.fascicle`); the inside of one fibre with rows of mitochondria between the
   myofibrils (level 3, `KC.fiber`). Each level is 28, 10.2 and 11.8 times more detailed than the one above it:
   3,370x in total.
2. **Each level sits in a circular lens inside the level above.** Level 1's lens is anchored to a moving point on
   the thigh (`walker.thighPoint(0.42)`), so it rides the leg. It opens with a white ring and an overshoot. Levels 2
   and 3 have no ring: their lens is the outline of a real bundle and a real fibre, and they fade in as their
   on-screen scale grows (`fade: [0.035, 0.11]`), so detail seems to emerge from the tissue.
3. **One number drives the camera.** The scene keys the zoom in log space (`ZK` in `walk.html`, eased per segment)
   on words: it starts on "dive", reaches the thigh on "leg", the bundle on "into", the fibre on "cell". Log space
   makes each level take the same screen time per tenfold zoom. `S.focus(logZ)` eases the camera point from the
   walker to each lens centre just before that lens is reached, so every pan is short.
4. **The walk slows to 10 % during the dive** (`KH.phaseTable`), so the leg barely moves while the camera is in it.
5. **Rendering stays cheap.** `zc.set(Z, F)` gives each level one transform, hides a level when its scale is
   useless (below 0.003 or above 80), and hides every level above a lens that covers the whole screen. No transform
   ever carries the full 3,370x, so there are no precision problems and the browser never draws a giant layer.
6. **The exit is a match cut.** The camera locks on one big-eyed mitochondrion and pushes in while a radial vignette
   closes. The origin scene opens with the orange ancestral bacterium at the same size and angle under the same
   vignette, which then opens on the ancient sea.
7. **The finale runs the chain backwards**: it starts inside the fibre and eases out to the person, while their
   walk accelerates back to full pace.

Rejected: one SVG scaled 3,370x (float precision and render cost) and hard cuts between levels (the viewer loses
the sense that this is inside the walking person).

---

## 7. What Pass 1 (stills) and Pass 2 (rendered frames) check

**Pass 1 is about the picture's design, on stills, before anything is rendered. Pass 2 is about the delivered
file, on frames decoded from the MP4.** Anything that needs time, sound or the encoder belongs to Pass 2.

**Pass 1: snapshots at story beats** (`./dev.sh 12.3,14.0,... name` -> `review/name.jpg`, plus full-size frames)
- Composition in the 9:16 frame: is the subject big enough on a phone, and where is the empty space?
- Readability: label size, contrast, nothing covering a face or the caption line.
- Each tag or banner on screen at the moment its word is said, and long enough to read.
- Characters: poses, eyes, continuity across a cut (same size and angle for a match cut).
- Science in the picture: does it show what the line says?
- `npx hyperframes check`: lint, safe areas for Shorts, Reels and TikTok, contrast, overlaps, unread lines. It
  samples only 9 times for the safe areas, so I also ran it with `--samples=150` (it found five more problems).

**Pass 2: the rendered MP4** (`tools/verify_render.py`, `tools/frame_stats.py`, frames pulled with ffmpeg)
- File: size, frame rate, frame count, duration, codecs.
- Sound: integrated loudness and true peak (-14 LUFS, at most -1 dBTP), voice against the bed, and sync between the
  MP4's audio and the stems.
- Black frames, and frames on both sides of every cut.
- Empty or frozen stretches (frame_stats), saturation, and the contact sheet as a whole for pacing.
- Seek-order bugs: frames from the MP4 compared with fresh seeks at the same times. A mismatch means some state
  depends on the order frames were rendered in.

In this film Pass 1 changed every scene after the walk (`REVIEW.md` lists each fix). Pass 2 caught the empty
background in three scenes and the frame_stats aspect bug; the cut frames and the seek comparison were clean.
