# 06 · Voice and the timing pipeline

The narration is the clock. Picture and sound are scheduled against **measured word times**, so a new recording
re-times the whole film by re-running four scripts.

```
film script ──vo.py──▶ assets/vo_raw.wav + vo_timing.json ──align.py──▶ vo_words.json ──build.py──▶ timing.js / timing.json + index.html
                                                                                                        │
                                       scenes: K.t("word") ◀──────────────────────────────────────────┤
                                       audio:  w("word")   ◀──────────────────────────────────────────┘
```

## vo.py
- **TTS mode** (stand-in voice): synthesises each sentence separately with Kokoro, so sentence starts are exact,
  and lays them on the film timeline after the cold open with fixed pauses (0.22 s between sentences, 0.34 s
  between lines).
- **Fixed film length:** solve the speaking speed so speech + pauses fit between the open and the end card
  (antibiotics: 1.044x for a 60.0 s film with a 5.3 s open). Cap the speed (1.08x); past that, trim the script.
- **Recording mode** (template: `python vo.py --recording voice.wav`): places the human's recording after the open.
- **Clips mode** (the vertical films' line-based `vo.py`, newest in `projects/mitochondria-short/`:
  `python vo.py --clips DIR`): one recorded or generated clip per `film.json` line, in name order (01.wav ...).
  Silence and room noise are trimmed by loudness (30 ms RMS frames), clips are resampled to 48 kHz and laid out with
  each line's pause, and the exact line starts go to `vo_timing.json` so `align.py` can pin each line's first word.
  Nothing is time-stretched. Tested with noisy 44.1 kHz stereo clips: 125/125 words matched.
- The antibiotics project keeps its script inside `vo.py` (`LINES`); the template reads `film.json`.

## align.py
- Transcribes `vo_raw.wav` with faster-whisper (`base.en`, word timestamps, the script as `initial_prompt`).
- Aligns recognised words to script words with `difflib.SequenceMatcher` on normalised text; unmatched words are
  interpolated between neighbours and listed (antibiotics: 132/132 matched).
- Whisper starts the first word after a pause early, inside the silence. Fix it: the antibiotics `build.py` clamps
  the first word of each sentence to the known sentence start; the template's `align.py` instead moves any word
  that follows a ≥ 0.12 s gap to the first 10 ms frame where speech energy rises (works for human recordings too).
- Mid-sentence accuracy is roughly ±0.1–0.2 s. Lead visual cues a little (0.05–0.15 s before the word):
  slightly early reads as anticipation; late reads as lag.

## build.py
- Places scenes: the first starts at 0 (it contains the cold open); each later scene starts halfway through the
  pause before its first line; the last ends at the film end. Antibiotics hardcodes its 8 scenes in a `cuts`
  dict; the template reads `film.json → scenes`.
- Writes `assets/timing.js` (`window.VO = {words: [[key, start, end]], scenes: {id: {start, end, dur}}, lines, film}`),
  `assets/timing.json` (same, for Python), and `index.html` (scene hosts + whichever of vo/sfx/music.wav exist).
- Rewrites `data-duration` inside each scene file to match its host.

## Swapping in the human's own voice
1. Template: `python vo.py --recording their.wav`. Vertical films: `python vo.py --clips their_clips/` (one file per
   line) or `--recording`. Antibiotics: replace `assets/vo_raw.wav` (48 kHz mono, first
   word at the cold-open time) and update `vo_timing.json` (`film`, `open`, sentence starts if you use the clamp).
2. `python align.py` → check every word matched.
3. `python build.py`, then `audio/sfx_cues.py`, `audio/music.py`, `audio/mix.py`, `python build.py`.
4. Snapshot each scene's key beats again (a slower reader moves everything), then render.
