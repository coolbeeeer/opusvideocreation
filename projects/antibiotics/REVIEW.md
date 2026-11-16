# How Antibiotics Work (60 s): self-review

Final file: `renders/antibiotics-v2.mp4`. 1920x1080, 60 fps, 3600 frames, 60.000 s, AAC stereo 48 kHz.
Contact sheet (one frame every 2 s, taken from the MP4): `renders/antibiotics-v2-contact.jpg`.
The v1 render is not included (it was superseded); `review/render-v1-*.jpg` show the frames it was judged on.

## How it is built
- Narration timing drives everything. `vo.py` places each sentence on the film timeline, `align.py` measures every
  word's start time, `build.py` places the 8 scenes and writes `assets/timing.js`. Each scene asks for word times
  (for example the burst waits for the word "bursts"), so a new voiceover re-times the whole film.
- Scenes: `compositions/open, infection, compare, wall, machines, viruses, resistance, ending`. Shared drawing code: `assets/kit.js`.
- Audio: `audio/sfx_cues.py` (sound effects from `audio/sound_effects.py`, a copy of `lib/sound_effects.py`), `audio/music.py` (original score),
  `audio/mix.py` (levels, ducking, peak safety). Three tracks are layered in `index.html`: voice, sound effects, music.

## Pass 1: snapshots of each scene before rendering
| Scene | Problem | Fix |
|---|---|---|
| open | Stomach and bloodstream backgrounds did not cover the camera moves, so teal edges showed | Enlarged the backgrounds |
| open | Hair read as a cap; the hand was a blob | Added fringe, tufts and a sideburn plus a moonlight rim; drew fingers and a thumb |
| open | The capsule seam was diagonal at the cut into the stomach shot | The camera now rotates during the dive so the seam is vertical, matching the next shot |
| open | "Stomach" tag still on screen during the gut-wall wipe | Hides 0.25 s earlier |
| infection | The hair strand pointed into the sky at an odd angle | Re-drawn to curve out of the skin |
| infection | The white blood cell was too small to read in the crowd | 130 px wide, and the camera zooms in on it |
| compare | "Your cell" was on screen 0.3 s (checker: `line_unread`) | Appears on "differently" instead |
| wall | Enzyme arms rotated around the wrong point | Each arm hinges at its base |
| wall | A walking tween overrode the jam position (checker: `gsap_tween_tail`) | Walking stops before each jam |
| wall | Penicillin molecules too small in the zoomed view | 0.17 -> 0.22 scale |
| machines | A repeat count could become -1 (checker: `gsap_repeat_floor_unclamped`) | Clamped |
| machines | Message-strand ticks drifted outside the cell | Shortened and slowed |
| resistance | Shield badge too small to read | Larger, with a check mark; thicker ring |
| ending | Bottle and note invisible: GSAP replaced their SVG transforms | Wrapped in their own groups |
| ending | Title on screen under 2 s (checker: `line_unread`) | Title arrives at 57.6 s |

## Pass 2: frames taken from the rendered v1 MP4
| Problem | Fix |
|---|---|
| The capsule in the hand was about 50 px, too small for the first shot of the film | 1.45x larger |
| The dive into the capsule overshot the next shot's scale | Final zoom 74x -> 51x |
| After the burst the frame went empty for about 0.5 s | Debris and spray linger until the cut |
| The viruses scene opened on a nearly empty frame | Its bacteria start already in frame |

## Measured on v2
- Audio: -15.8 LUFS integrated, -1.3 dBFS peak. Voice -19.1 LUFS, music 14.7 dB under the voice while speaking.
- Audio sync: 0.0 ms offset between the MP4 and the three stems.
- No black frames (ffmpeg blackdetect).
- Saturated-pixel share per scene (style rule: under about 7 %): 0.0-4.1 % in every scene except the stomach shot.

## Failed or open checks
- Voice: local Kokoro TTS (`af_heart`, offline, not a voice MCP) at 1.044x speed, because no recording was supplied.
  It stands in for your own voiceover. To swap: replace `assets/vo_raw.wav` with your recording, then run align, build,
  sfx, music, mix and render again; every cue re-times itself.
- I cannot listen to audio. Loudness, peaks, ducking depth and sync are measured, not heard.
- Word times come from speech recognition (faster-whisper `base.en`), accurate to roughly 0.1-0.2 s.
- Style rule broken once: in the stomach shot (2.1-2.7 s) the opening capsule fills the frame, so 28.9 % of pixels are
  saturated orange. It is the antibiotic itself, on screen for about 0.6 s.
- `composition_file_too_large` warning on `wall.html` (321 lines). Structure only, no effect on the render.
- Science simplifications in the picture (the narration is accurate):
  - Penicillin's targets are drawn as "wall builders" under the wall.
  - Tetracycline is shown jamming the whole protein factory; it binds the small ribosome subunit.
  - The quinolone is shown jamming a copying clamp; it actually traps the enzymes that untwist DNA during copying.
  - Sharing defences is shown as a plasmid passed through a tube (conjugation).
