# Agent playbook: make a 60-second flat-vector explainer

You are an AI agent with a shell, a file editor, and the ability to look at images. You cannot watch video
or hear audio. This playbook is written for exactly that situation. Follow the phases in order and do not
skip the gates: each gate exists because skipping it caused a real failure while building `antibiotics_v2`.

Reference output: `projects/antibiotics/renders/antibiotics-v2.mp4`. Starter project: `templates/new-film/`.

---

## Ground rules (from the user who commissioned this; keep them)

1. **The human never touches a terminal.** You install, configure, render and verify everything.
2. **Nothing is final until the human approves it.** Show each deliverable and wait.
3. **Report every failed check plainly**, including the ones you cannot fix.
4. **Original assets only.** Never reuse a reference video's frames, audio or music. Reference material is
   for style study only and never enters an output or this repo.
5. **Do not adjust things by hand in a GUI.** Everything is code, so it is reproducible.
6. **Do not start with a voice MCP.** The narration is the human's own script (and ideally their own voice).
   A local TTS voice is acceptable as a stand-in, labelled as such.
7. **Expect iteration.** The first render is never the final one; budget review passes.

---

## Phase 0: environment (docs/01-environment.md)
- `npx hyperframes doctor` must show FFmpeg, FFprobe and Chrome as OK. If FFmpeg is not on a system PATH,
  set `HYPERFRAMES_FFMPEG_PATH` / `HYPERFRAMES_FFPROBE_PATH` (HyperFrames ignores user PATH dirs).
- Python venv with `requirements.txt`. Kokoro model files for TTS. faster-whisper downloads its model once.
- **Gate:** a 10-second silent test renders at 1920x1080, 60 fps, exactly 600 frames
  (`projects/one-ant-test/` is the one used here). Inspect frames **decoded from the MP4**, not only snapshots.

## Phase 1: style (docs/03-style-system.md, style/STYLE.md)
- Use `style/STYLE.md` as-is for this look. To build a new look: get the human's reference frames or video,
  sample frames at intervals into contact sheets, **measure** colours and saturation share with numpy, and
  time text entrances frame by frame. Write the result as a style file and get it approved.
- **Gate:** the human approves the style file.

## Phase 2: short style clip (optional for a new topic, mandatory for a new look)
- A 4-second clip exercising the style (the ant fight did this). Then self-review: what is too faint, too
  small, or wrong; write it in `REVIEW.md`; fix; re-render. The first pass is always too faint and too small.

## Phase 3: script (docs/07-scene-authoring.md)
- Draft narration of **~130 words per 60 s** for a natural pace (154 words ran 68 s and had to be cut).
- Write a shot table: time, narration, picture, sound effects. Check every factual claim; add an accuracy note.
- Time the draft with TTS before showing it, and report the measured length.
- **Gate:** the human approves the script. Apply requested changes literally (here: "start with a human taking
  the antibiotic, zoom into it, go inside the body").

## Phase 4: voice and timing (docs/06-voice-timing.md)
```bash
python vo.py            # or: python vo.py --recording their_voice.wav
python align.py         # every script word gets a measured start time
python build.py         # scenes placed on the voice timeline; writes assets/timing.js
```
- **Every visual cue and every sound cue is expressed as a word time** (`K.t("bursts") - T0`). Never hardcode
  seconds that depend on speech. This is what makes the film re-time itself when the voice changes.
- **Gate:** all script words matched (`align.py` prints unmatched words; investigate any).

## Phase 5: scenes (docs/02, 04, 07)
- One HTML file per scene in `compositions/`. Start from `templates/new-film/compositions/intro.html`.
- Draw with `lib/kit.js` (copied to `assets/kit.js`). Keep one saturated warm accent per scene: the subject.
- After **every** scene: `npx hyperframes check`, then `npx hyperframes snapshot --at <times>` at its key beats,
  build a contact sheet, and **look at it**. A passing check says nothing about how it looks.
- **Gate:** every scene reviewed in stills; checker passes (warnings reviewed, see docs/09-pitfalls.md).

## Phase 6: audio (docs/05-audio.md)
```bash
cd audio && python sfx_cues.py && python music.py && python mix.py && cd .. && python build.py
```
- Sound effects: synthesised from noise and sine waves (`lib/sound_effects.py`); one cue per visual event,
  using the **same time formula** as the animation; a pop for every word of every label.
- Music: original, generated in code, sections keyed to the narration.
- Mix targets that worked: voice -19 LUFS, music ducked ~6.5 dB under speech and ~15 dB below the voice,
  total ≈ -16 LUFS, peak ≤ -1.5 dBFS (a sidechain pulls SFX+music down wherever the sum would clip).
- **Gate:** measured loudness and peak in range; you cannot listen, so say so in the report.

## Phase 7: render and verify (docs/08-review-loop.md)
```bash
npx hyperframes render --fps 60 --quality delivery -o renders/film.mp4
```
- Verify on the **MP4**: ffprobe (frames = fps × duration), ebur128 loudness/peak, audio sync by
  cross-correlating the MP4 audio with the stem sum (expect 0 ms), blackdetect, a contact sheet every 1.5–2 s,
  frames around every scene cut, saturated-pixel share per scene.
- Do one more review pass on the rendered frames, fix, re-render (v2). Write `REVIEW.md` with both passes,
  the measurements, and every failed or open check.
- **Gate:** the human approves the film.

---

## Report template (what the human sees)
1. Where the file is, and its measured specs (resolution, fps, frames, duration, audio).
2. What happens, beat by beat with times.
3. Sound: voice source (say plainly if it is a stand-in), effects, music, measured levels and sync.
4. Self-correction: what each review pass found and fixed (point to `REVIEW.md`).
5. **Failed or open checks**, one bullet each, including "I can't listen to audio".
6. The decision you need from them, as a question.
