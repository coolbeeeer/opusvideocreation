# 12 · Vertical films for YouTube Shorts and Instagram Reels

`projects/ocean-glow-short/` is the worked example: 54 s, 1080x1920, 30 fps, burned-in captions, -14 LUFS.
Its `build.py`, `vo.py`, `align.py`, `compositions/captions.html` and `audio/mix.py` are vertical-aware and can be
copied into a new project as they are.

## Format
| Setting | Value | Where |
|---|---|---|
| Size | 1080x1920 (9:16) | `film.json` `width` / `height`; `build.py` writes them into `index.html` and `window.VO.W/H` |
| Frame rate | 30 fps | `film.json` `fps`; render with `--fps 30` (half the frames of 60, half the render time) |
| Length | under 60 s keeps every option open (Shorts allow up to 3 min; Reels over 3 min are not shown to new viewers) | `film.json` `film: "auto"` |
| Loudness | -14 LUFS integrated, true peak at or below -1 dBTP | `audio/mix.py` |
| Codec | H.264 High, yuv420p, AAC 48 kHz stereo (what `--quality delivery` writes) | `npx hyperframes render` |

## Safe areas
The apps draw buttons and text over the video. `npx hyperframes check` tests text against these boxes (from its
`SOCIAL_SAFE_AREAS` table) and warns with `outside_safe_zone`:

| Platform | Text must stay inside (1080x1920) |
|---|---|
| YouTube Shorts | x 48-888, y 288-1248 |
| Instagram Reels | x 65-1015, y 269-1248 (6-94 % by 14-65 %) |
| TikTok | x 120-960 for y 240-840, then x 120-780 for y 840-1260 |

So put captions near y 1185 centred on x 468, keep banners below y 290, and keep the subject between y 300 and 1200.
The bottom quarter can hold scenery but nothing anyone needs to read. Mark deliberate exceptions with
`data-layout-allow-safe-zone`.

## Captions
Most people scroll with the sound off, so burn captions in. `build.py` cuts the measured words into chunks of up to
4 words (breaking at punctuation and pauses, never ending a chunk on "the", "of", "with" ...), writes them to
`window.VO.caps` and to `captions.srt`, and mounts `compositions/captions.html` as a full-length layer with
`data-track-kind="captions"`. The word being spoken turns cyan. Upload `captions.srt` as well.

## Narration
- One TTS call per line and a pause per line (`film.json` `lines[].pause`): the voice keeps its phrasing across
  sentences, and a longer pause before a punchline gives it room ("Something curious swims closer. Bad idea.").
- `vo.py` trims the silence Kokoro leaves at both ends of a clip, so the pauses are exactly what `film.json` says.
- `film.json` `speed` sets the base reading speed (0.95 for this film); a fixed film length may raise it up to `max_speed`.
- About 130 words fill 50 s at 0.95x with these pauses.

## Writing for the vertical frame
- One subject at a time, big. A 300 px fish in a 1920 px frame reads; a 100 px one doesn't.
- Use the height: dives, falls, beams and light coming from above are natural in 9:16.
- Start on motion or a question in the first second; there is no title card at the start.
- Darkness is a valid picture in a deep-sea film, but keep something alive in it (distant lights, snow, eyes).

## Kits
- `lib/kit-plus.js`: parallax camera rig (`KP.rig`, centred on the film size), eyes, vignette, grain, rim-lit bacteria.
- `lib/kit-ocean.js`: `KO.scene()` builds a stage (background, four parallax layers, camera, UI layer) in one call;
  `KO.glow` light sources; marine snow; twinkling lights; sunbeams; a depth gauge; and a deep-sea cast with eyes:
  `fish` (lanternfish with photophores), `angler`, `hatchet` (with a full silhouette for counter-illumination),
  `jelly` (Atolla-style, with a spinning ring of lights), `shrimp`, `dragon` (stoplight loosejaw with a red beam),
  `fuel`, `enzyme`. Model sheet: render each once on a test stage before building scenes.

## Checks that caught real problems here
- `template_literal_selector` (error): ``querySelector(`[data-composition-id="${ID}"]`)`` crashes the HTML bundler's
  CSS parser. Use a hardcoded string.
- `outside_safe_zone` (warning): see the table above.
- `content_overlap`: a moving label passing over a fixed one (the depth chip over "1,000 m").
- A stale-value seek bug that no checker catches: see `docs/09-pitfalls.md`, "a clock tween reads stale values".
