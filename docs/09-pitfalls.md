# 09 · Pitfalls (every one of these happened)

## Environment
- **FFmpeg "not found" while it is on PATH.** HyperFrames trusts only system PATH dirs. Set
  `HYPERFRAMES_FFMPEG_PATH` / `HYPERFRAMES_FFPROBE_PATH`.
- **System installs fail** (read-only `/var`, `~/.local`): put tools under the workspace (`.tools/bin`, a venv).
- **Background jobs / dev servers don't run** in the sandbox: render in the foreground (≈ 2.7 s of render per
  second of 60 fps film on 8 cores); time a 2 s segment with `--start/--end` first to estimate.
- **`numpy` missing** in the system Python: everything audio runs in the venv.
- **Static FFmpeg has no `drawtext`**: don't burn timestamps into contact sheets with it.
- **YouTube pages can't be read; Drive links need "Anyone with the link".** Ask the human for transcripts or files.

## Timing
- **Kokoro returns no word timings** (`create_timed` is empty for v1.0): measure with whisper.
- **Whisper starts post-pause words early**: clamp to sentence starts or refine with the energy onset.
- **Draft scripts run long**: 154 words took 68 s; 132 fit 60 s with a 5.3 s cold open at 1.044x.
- **Contact-sheet timestamps can be mis-mapped** (an off-by-5 s mapping measured the wrong scenes): render a
  time-check grid before measuring anything.

## GSAP / SVG
- **GSAP replaces an SVG `transform` attribute** when it tweens the element: the ending's bottle and note vanished.
  Static transforms go on an inner group.
- **Default rotation pivot is not your centre**: set `svgOrigin: "0 0"` up front (enzyme arms swung from the
  wrong point until each got its own hinge origin).
- **An earlier tween ending later wins** (`gsap_tween_tail`): an enzyme's walk overrode its jam position.
- **`repeat` computed to -1 means infinite**: clamp.
- **`fromTo` without `immediateRender:false`** shows its start state from time 0.
- **SVG ids are global** across all scenes: prefix them.
- **Backgrounds smaller than the camera's travel** show the stage colour at the edges (stomach, bloodstream).

## Visual
- **First pass is too faint and too small**: plan a second pass, measure sizes in px against the frame.
- **Match cuts need matching orientation and scale**: the capsule seam was diagonal at the cut until the camera
  rotated during the dive; the dive overshot (74x) the next shot's scale until set to 51x.
- **Empty frames at cuts** (scene starting with everything at scale 0; debris all gone before the cut): keep
  something in frame on both sides of every cut.
- **A full-frame flash washes everything grey** and hides rim light: 45 % → 18 %.
- **Characters**: hair drawn as one shape reads as a cap: add a fringe, tufts, a sideburn and a rim light.
- **Labels on screen < 1 s** can't be read (`line_unread`); the closing line needs ≥ 2 s.

## Audio
- **Buffer overruns in procedural sounds** (a click placed past the end of a short buffer): clip every add.
- **Music buried**: at -27 LUFS it sat 17 dB under the voice; -24.5 LUFS gives ~15 dB.
- **Summed tracks can clip** where a loud effect lands on a loud word (the burst on "bursts"): sidechain-limit
  SFX + music against the voice before writing the stems.
- **Random visual placement vs sound**: replay the scene's seeded PRNG in Node to get exact event positions.

## Tooling for agents
- **The image reader cached files by path**: write each review image to a new filename.
- **Copying big files with an undo-keeping delete tool fails**: use a shell `rm` for large scratch files.

## Repository hygiene
- **Never commit reference material** (frames, audio or video from a reference) and never commit credentials.
  Tokens pasted into chat should be revoked after use.
