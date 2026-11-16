# 05 · Audio: sound effects, music, mix

The film has three stems, all generated in code and layered as `<audio>` tracks: `vo.wav`, `sfx.wav`,
`music.wav`. Plan the work as half visuals, half audio; once sound effects are in, most of the heavy lifting
is done.

## Sound-effect library (`lib/sound_effects.py`)
Every sound is synthesised from noise and sine waves (numpy + scipy), so it is original. 48 kHz.
The four core recipes from the tutorial, then everything else is built from the same parts:

| Recipe | How it is made | Used for |
|---|---|---|
| `noise` | white noise, then filtered | building block |
| `whoosh` | noise × a swell envelope, low band crossfading into a high band | camera moves, banners growing, flights |
| `thump` | sine falling in pitch × exponential decay (+ click) | hits, landings, heartbeats |
| `rain` | Poisson-timed water drop "plinks" over a hiss | drips, rain |
| `pop`, `bubble` | short upward sine chirps | text words, cells splitting, popping |
| `snap`, `clink`, `clunk`, `crunch` | band noise and inharmonic partials with fast decays | jaws, wall bricks, locks, breakage |
| `zap`, `thunder`, `impact`, `splash` | gated crackle; crack + rolling rumble; thump + crack + room; burst + drop scatter | lightning, the burst |
| `gulp`, `fizz`, `squish`, `slice_` | resonant glug; hiss + tiny bubbles; swept resonance; bright whoosh + ring | swallowing, dissolving, wet contact, the cut |
| `flow`, `heartbeat`, `creak`, `rush`, `strain` | low rushing bed; lub-dub thump pairs; wobbling sawtooth groan; rising noise | blood, tension, water rushing in |
| `machine`, `power_down`, `boing`, `chime`, `sparkle`, `zip_`, `scurry` | ticks + whirr (optional slowdown); falling buzz; vibrato spring; bell chords | machines, jams, bounces, titles, stretching, legs |
| `room_tone` | very quiet low-passed noise | under every scene so silence never sounds dead |
| `reverb`, `limit` | noise-impulse convolution; look-ahead peak limiter | space; peak control |

`Mix(dur)` is a stereo timeline: `m.add(sound, at, gain_db, pan)` then `m.write(path, peak_db=-1)`.

## Cue sheet (`audio/sfx_cues.py`)
- **Schedule each sound with the same formula as the animation.** If the scene does
  `tl.set(bact, {autoAlpha:0}, at("bursts"))`, the cue is `m.add(fx.impact(), w("bursts"))`. `audio/cues.py`
  exposes `w(word, n, after)` and `s(scene)` with exactly `K.t`'s semantics, reading `assets/timing.json`.
- **Every label gets sound:** `pop_word(t, n_words, tag=...)` = a soft whoosh for banners plus one pop per word at
  `kit.show()`'s offsets.
- **Seeded random placement in JS:** if a scene places 34 bacteria with `K.rng(707)` and pops them as a wave
  passes their x position, replay the same PRNG in Node (`audio/js_events.cjs` requires `kit.js` with a fake
  `window`) to export their positions, and time each pop from them. Never guess.
- Layer: one event often has 2–4 sounds (the burst: impact + splash + crunch + pop + thunder).
- Typical gains: hero events 0 to -6 dB, text pops -11 to -15 dB, ambience -24 to -34 dB.

## Music (`audio/music.py`)
Original, synthesised: detuned-saw pads through a low-pass, additive "pluck" arps, a saturated sine bass,
thump kicks, noise hats, noise risers. 100 BPM, D minor / Dorian. Five buses (pad, pluck, bass, drums, fx), each
with its own noise-convolution reverb.
- **Sections are keyed to word times**, not bar numbers: the infection builds from "one becomes two" to
  "millions"; "antibiotics" lifts to F major; a Dm7–G7–Bbmaj7–C groove runs through the science; risers and
  accelerating hits lead into "bursts", which lands a full-chord hit; resistance is a low drone with a minor-second
  cluster; the end resolves Bbmaj7 → F/A → Gm7 → D major under the title.
- Notes snap to a beat grid; chord changes land on cue times. The template's `music.py` does a simpler version
  from a `mood` per scene.

## Mix (`audio/mix.py`)
1. **Voice:** 80 Hz high-pass, gain to **-19 LUFS** (ffmpeg `ebur128` measures), peak-limit at -3 dBFS.
2. **Music ducking:** envelope follower on the voice (|x| → 8 Hz low-pass → normalised → 40 ms attack, 350 ms
   release) → music gain -6.5 dB × envelope. Music levelled to -24.5 LUFS before ducking.
3. **SFX:** levelled to -22.5 LUFS, peak-limited at -3 dBFS.
4. **Peak safety for the summed tracks:** the renderer sums the three tracks, so compute, per sample, the scale
   `k` that keeps |voice| + k·|sfx + music| ≤ -1.5 dBFS, min-filter it (4 ms look-ahead) with a 80 ms release, and
   apply it to SFX and music only. The voice is never touched. (Engaged on ~2.5 % of samples, max -4.7 dB.)

Result on antibiotics_v2: total **-15.8 LUFS**, peak **-1.3 dBFS**, music ~15 dB under the voice while speaking.
Moving the music from -27 to -24.5 LUFS was a deliberate correction: at -27 it sat 17 dB under and was buried.

## Verifying audio you cannot hear
```bash
ffmpeg -nostats -i film.mp4 -map 0:a -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|Peak:"
```
- **Sync:** cross-correlate the MP4's audio with the sum of the three WAVs; the lag must be 0 ms
  (`tools/verify_render.py`).
- **Balance:** RMS of music and SFX during speech vs the voice (printed by `mix.py`).
- **Shape:** `ffmpeg -i sfx.wav -filter_complex showwavespic=s=1920x300 wave.png` and look at it: the loudest
  event should be the loudest spike.
- Say in the report that audio was checked by measurement only.
