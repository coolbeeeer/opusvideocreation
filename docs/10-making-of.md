# 10 · Making of antibiotics_v2 (context from the build session)

This is how the video came to exist, condensed from the working session between the human and the AI agent.
It explains the *why* behind the method. Paraphrased; credentials and private links are omitted.

## The brief
The human wanted the method from the tutorial **"Claude Opus 5.5 Can Now Make Kurzgesagt-Style Animations
(Full Tutorial)"** by RandomAI (https://www.youtube.com/watch?v=wSZx2auhKlc) followed exactly, in order, from a
clean start (none of their earlier builds):

1. **Setup**: Node, HyperFrames (`doctor`, `init`, `preview`, `render`); the agent does all terminal work.
   Fallback if HyperFrames would not install: a Cairo → ffmpeg pipeline (not needed in the end).
2. **10-second test** ("One Ant": a red ant on a mound), silent, 1080p, 60 fps. Only continue once it looks right.
3. **Style study** from real reference frames: colour scheme, which colour is the one saturated warm colour, glow
   only on light sources, word-by-word text, detail level and 2D depth. Save it as a style file.
4. **Styling and refinement**: a ~4 s ant fight (square up, charge, clash with starburst and lightning, camera
   shake, a "jaws locked" callout, a throw into a puddle, dazed sparkles), then **self-correct**: note what is too
   faint/small/wrong in a REVIEW.md, fix, re-render.
5. **Audio**: half the work. Procedural effects in a `sound_effects.py` (noise, whoosh = noise × swell,
   thump = sine × decay, rain = drops), layered onto the video. Use the human's own script and voiceover, not a
   voice MCP. Original music only.
6. **Full build** of a 60 s sample: draft script → human approves → build the animation around it.

Rules: don't touch terminals or code by hand, don't adjust things in Studio, don't start with a voice MCP,
don't expect a polished first try or exact Kurzgesagt parity, **report every failed check plainly**, nothing is
final until approved.

## What happened, step by step
**1. Setup.** `doctor` reported FFmpeg, FFprobe and Chrome missing. System package installs failed (read-only
filesystem). A static FFmpeg went into the workspace, but HyperFrames still could not see it: reading the CLI
source showed it only trusts system PATH dirs and honours `HYPERFRAMES_FFMPEG_PATH`. Chrome came from
`npx hyperframes browser ensure`. `preview` (Studio on :3002) could not run because long-running servers were
blocked, and the human could not open localhost anyway, so review moved to stills and MP4s.

**2. The 10 s test.** The first draft used GSAP's motion path with auto-rotation; on the slope the ant floated off
the mound and pivoted around its middle. Rewritten to sample the path and slope directly with the feet at the
pivot. 600 frames, 60 fps, verified on frames decoded from the MP4. Approved implicitly by moving on.

**3. Style study.** The human pasted 9 reference stills; they were not on disk, so colours were estimated by eye and
the style file said so. They then shared a reference video via Drive; the first download hit a sign-in wall, the
human fixed the sharing, and the 17.5-minute video was sampled into contact sheets and frame-accurate motion
bursts. Colours were **measured** with numpy. The first sample set landed on the wrong scenes (timestamps off by
5 s); a time-check grid caught it. Findings reported honestly: the one-saturated-warm-colour rule holds in dark
scenes (< 7 %) but not day scenes (~30 %); the reference brings banner text in as whole phrases, not word by
word. Approved.

**4. Ant fight.** Pass 1 was too faint (dark violet legs on a dark chamber, a flash washing the frame grey), too
small (330 px ants in a 1400 px chamber, invisible mandibles, a 15 px puddle) and wrong (the thrown ant poking
into the soil, a hard edge from a shade shape). Passes 2 and 3 fixed them; `REVIEW.md` records all 15 notes and
the checker warnings left open. The human: *good, can be improved further; now make a 60 s video on how
antibiotics work, with proper sound effects and audio.*

**5. Audio system.** `sound_effects.py` was written from the tutorial's four recipes plus a dozen more, tested
on the ant clip (0 ms sync, -18 LUFS). The human had not supplied a voiceover, so a local offline TTS (Kokoro)
was installed as a **guide voice**, clearly labelled as a stand-in. The antibiotic script was drafted with a shot
table and accuracy notes; at a natural pace 154 words ran 68 s, so it was cut to 132 words. Three guide voices
were timed (only `af_heart` fit 60 s) and the human was asked to approve the script and choose the voice.

**6. The film.** The human approved the script with one change: *start with a person taking the antibiotic, zoom
into it, go inside the body, then follow the script.* No recording arrived, so the build used `af_heart`.
- `vo.py` solved the speed (1.044x) so 5.3 s of cold open + narration + title fit exactly 60.0 s.
- Kokoro gave no word timings, so `align.py` measured them with faster-whisper: 132/132 words matched.
- `build.py` placed 8 scenes on the voice timeline. A two-scene test confirmed the sub-composition pattern and
  that shared scripts load first. `kit.js` was written for the organisms, molecules, camera and callouts.
- Each scene was snapshot-reviewed and fixed (15 problems in pass 1, see `projects/antibiotics/REVIEW.md`).
- Audio: a cue sheet keyed to word times (with the resistance scene's seeded positions replayed in Node), an
  original score with sections keyed to the narration, and a mix with ducking and a peak-safety sidechain. The music
  was raised 2.5 dB after measuring it 17 dB under the voice.
- v1 rendered in 159 s. Reviewing the MP4's own frames found a too-small capsule, a zoom overshoot and two empty
  frames; v2 fixed them. Final: 3600 frames, -15.8 LUFS, -1.3 dBFS peak, 0 ms sync, no black frames.
- The report listed the open items: the voice is a stand-in; audio checked by measurement only; the stomach shot
  breaks the saturation rule for ~0.6 s; some biology is simplified in the picture (the narration is accurate).

**7. Packaging.** The human asked for everything a new AI would need, plus this context, in this repository.

## Why it came out well
1. **Measured style** instead of impressions, and a style file approved before any art was drawn.
2. **The voice is the clock**: every animation and every sound is scheduled from measured word times.
3. **Sound on every event**, including a pop per word of every label: the tutorial's "after sound effects,
   80 percent of the heavy lifting is done" matched experience.
4. **Explicit critique passes** (too faint / too small / wrong), written down, on stills and then on the MP4.
5. **Verification by measurement** for everything that cannot be seen or heard: frames, loudness, peaks, sync,
   saturation share.
6. **Gates with the human** at style, script and film, and plain reporting of what did not pass.

## Still open at handover
- The narration is the TTS stand-in, not the human's own voice (swap procedure: docs/06).
- Step 6's original target, a 60 s sample of the human's project *Abyssal* (Cold Open S01–S20), was waiting on
  that script.
