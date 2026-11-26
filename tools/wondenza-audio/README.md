# Wondenza audio — Opus's films, our voice

This module makes a film built in this repo come out with the Wondenza
house sound — our locked Fish voice, our mix, our end card and watermark —
instead of the Kokoro stand-in voice. Once it is wired in, there is no
re-voicing step: you build the film, it already sounds like Wondenza.

## Setup (one time, ~2 minutes)

1. **Set the Fish key in Kiro** (environment variable / secret):
   ```
   FISH_AUDIO_API_KEY=<the key from the Fish Audio dashboard, fish.audio>
   ```
   That is the only credential. The module reads it from the environment
   and never stores it, never prints it, never writes it to a file.
   The voice engine is `s2.1-pro-free` (free) — the module refuses the
   paid engine outright, so there is nothing to pay for.

2. **Dependencies** — already in the repo's `requirements.txt`, plus ffmpeg:
   ```
   pip install soundfile numpy scipy   # (numpy/scipy for the voice trim + mix measurement)
   ffmpeg                               # already needed for rendering
   ```

3. **Copy this folder into the repo** at `tools/wondenza-audio/` (it is
   already there if you are reading this in the repo). The `assets/`
   folder carries the end card, the locked "Like and subscribe" clip,
   the card bed and the eye icon — do not regenerate or replace them.

## How it fits your pipeline

Your pipeline is unchanged except the voice step. `vo.py` currently calls
Kokoro; this module replaces that one call:

```
film script ──voice.py──▶ assets/vo_raw.wav + vo_timing.json ──align.py──▶ vo_words.json ──build.py──▶ timing.js / timing.json
                                                                            │
                                              render (clean cut, NO voice) │
                                                                            ▼
                                              finish.py ──▶ film-final.mp4 (voice + mix + end card + watermark)
```

### Step 1 — record the voice (replaces the Kokoro call in `vo.py`)

```bash
python tools/wondenza-audio/voice.py --film-json film.json --out-dir assets
```

Reads `film.json` (`lines`, `open`, `tail`, `film`, `speed`, `max_speed`)
exactly like your `vo.py`. One Fish clip per line, trimmed so speech
starts at the clip's start time, laid on the film timeline. Writes
`assets/vo_raw.wav` (48 kHz mono) and `assets/vo_timing.json` in the
exact format your `vo.py` writes, so `align.py` and `build.py` run
unchanged. If the narration is too long for a fixed film length, the
speed is solved up (capped at 1.1x); a clip that runs over its own max
length is re-recorded at 1.05x, then 1.1x.

Or record a single line for a quick test:

```bash
python tools/wondenza-audio/voice.py --text "You're drifting off." --out-dir /tmp/vo-test
```

### Step 2 — render the film as a clean cut

Render as usual, but **without the voice track** — picture + SFX + music
only, like `falling_asleep_sfx_clean.mp4`. The voice is added by
`finish.py` afterwards. (If the render already contains a voice, the
finish will double it — render clean.)

### Step 3 — finish (voice + mix + end card + watermark)

```bash
python tools/wondenza-audio/finish.py \
    --video renders/film.mp4 \
    --clips assets/voice \
    --timing assets/vo_timing.json \
    --word-times assets/vo_words.json \
    --out renders/film-final.mp4
```

Or all in one (records the voice too):

```bash
python tools/wondenza-audio/finish.py \
    --video renders/film.mp4 \
    --record-from film.json \
    --out renders/film-final.mp4
```

`--timing` also accepts an Opus `timing.json` or a `VOICE_TIMING.md`
sheet. `--bed` takes a bed wav instead of the video's own audio;
`--sfx` + `--music` take the separate stems. The last spoken word is
anchored from `--word-times` when given (tightest), else the last
clip's end.

`finish.py` writes `<out>.report.json` with every measured number and
prints it. It also verifies the picture is untouched (PSNR of a film
frame vs the source, excluding the watermark corner, and of a card
frame vs the end-card file).

## What each file does

| File | Job |
|---|---|
| `config.py` | Every locked constant. Do not change a value to make a film pass — say so and let the user change it. |
| `voice.py` | Fish TTS client (env key only), per-line recording, silence trim, speed solving, `vo_raw.wav` + `vo_timing.json`. |
| `mix.py` | Voice stem (HP80, -15 LUFS, stereo) + bed (ducked ~3 dB, level corrected so it sits 8.4 dB under the voice while speaking) -> film audio. |
| `endcard.py` | Append the end card + 25% eye watermark (film only), master gain before the limiter. |
| `finish.py` | One entry point: video + clips + timing -> finished mp4 + report. |

## The locked spec (do not change without the user)

- **Voice:** Fish Audio, model `1d866ca2766944489ae05da868809c15`, engine
  `s2.1-pro-free` only, pace 0.85. Per-clip level -15 LUFS, HP80, peak
  limited at -3 dBFS. Leading silence trimmed so speech starts at the
  clip's start time.
- **Mix:** bed (SFX + music) ducked 3 dB under the voice and levelled so
  it sits **~8.4 dB under the voice while speaking**. Master **-14 LUFS**,
  true peak **≤ -1.5 dBFS**, stereo.
- **End card:** 0.5 s stillness after the last word, 1.5 s crossfade,
  card 3.0 s, "Like and subscribe" (the locked clip in `assets/`,
  never regenerate) 0.2 s after the card is fully visible. 25% eye
  watermark top-right, film only.
- **Master chain:** gain BEFORE the limiter (`alimiter limit=0.79,
  level=false`). Gain after the limiter clips — that was a real bug
  once (peak -0.62 dBFS). The voice stem is panned to stereo BEFORE
  mixing — a mono voice stem + stereo bed downmixes the bed to mono
  (the other real bug once).

## Pace — the 2026-11-26 lesson

Record at the natural 0.85 pace and let the film follow the voice. Do
NOT force the voice into fixed timing slots by varying the speed from
clip to clip: on the hypnic re-voice the 12 clips were recorded at
different per-clip speeds (three rounds) to squeeze our faster voice
into Opus's fixed Kokoro timing, the pace wandered, and the user judged
the voice "weird". The fix was to re-record all 12 clips fresh at the
natural 0.85 pace (71.13 s total vs the planned 84.0 s) and have Opus
re-time the picture + SFX to our voice. That is the correct direction:
**the picture follows the voice, never the other way round.** For a new
film this is automatic — `film="auto"` + `align.py` re-times the picture
to the measured word times. For a re-voice of an already-timed film, if
the voice sounds uneven after the speed-up retries, send the
natural-pace clips to Opus for a re-time instead of varying speeds
further.

## Proven on

The hypnic-jerk re-voice (2026-11-26): Opus's 92.8 s clean cut +
12 Fish clips -> 93.10 s, 1080x1920 30 fps, stereo, -13.86 LUFS /
peak -1.91 dBFS, picture pixel-identical outside the watermark corner
(PSNR 49.85 dB), mech check PASS WITH WARNINGS. Build record:
`~/workspace/hvp-animation-prep/hypnic-jerk/opus-revoice/REVIEW.md`.
