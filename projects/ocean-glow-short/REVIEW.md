# Why Most Animals in the Open Ocean Glow (54 s, vertical): self-review

Final file: `renders/ocean-glow-v3.mp4`. 1080x1920, 30 fps, 1626 frames, 54.200 s, H.264 High (yuv420p, 5.2 Mb/s),
AAC LC stereo 48 kHz (196 kb/s), 36.5 MB. Contact sheet from the MP4, one frame every 1.5 s:
`renders/ocean-glow-v3-contact.jpg`. Cover for Reels: `renders/ocean-glow-cover.jpg` (the title frame at 53.2 s).
v1 and v2 renders were superseded and are not included; `review/render-v1-*.jpg` show the frames v1 was judged on.

## How it is built
- `film.json` holds the script as eight lines (one per scene) with a pause after each, the 1080x1920 size and 30 fps.
- `vo.py` makes one Kokoro TTS call per line (not per sentence), trims TTS silence and lays the lines out with the
  pauses from `film.json`. `align.py` measures every word with faster-whisper: 132/132 words matched.
- `build.py` places the 8 scenes and a full-length captions layer, writes `assets/timing.js` and `captions.srt`.
- Scenes are drawn with `lib/kit.js`, `lib/kit-plus.js` (parallax camera, eyes, vignette) and `lib/kit-ocean.js`
  (deep-sea cast, glows, depth gauge), copied into `assets/`.
- Audio: `audio/sfx_cues.py` (every cue from a word time), `audio/music.py` (original score), `audio/mix.py`
  (mastered to -14 LUFS).

## Pass 1: snapshots of each scene before rendering
| Scene | Problem | Fix |
|---|---|---|
| kit | Model sheet: the hatchetfish read as a round puffer fish, the dragonfish as a thin stick, the lanternfish as grey | Hatchetfish redrawn with a straight back, deep keel and thin tail; dragonfish body thickened; lanternfish palette made bluer |
| hook | Lights on the fish too faint to read on a phone | Bigger photophores, a lit belly rim and a larger halo per fish |
| descent | Depth-gauge text 26 px, too small for a phone | 34 px marks, 46 px depth chip |
| descent | Midnight zone nearly empty | Distant flashing jellies, a bigger fish with nervous eyes, more marine snow |
| chemistry | The light burst covered the enzyme's face | Burst moved behind the enzyme, with a lit rim on the enzyme |
| angler | Anglerfish small in the vertical frame; background close to black | Radius 240 -> 290 px; background lifted |
| hatchet | In the silhouette the fins stayed silver, so the fish never vanished | Silhouette covers body and fins, with a stroke over the anti-aliased edges |
| hatchet | The "Hatchetfish" tag overlapped the light coming from above | Tag hides before that light appears |
| alarm | The burglar-alarm flash was too weak to see | Bigger ring lights and a blue halo that follows the flash |
| alarm | "Something bigger" tag cut off at the right edge | Moved left |
| colours | The shrimp was visible during the beam diagram | It fades in with the dragonfish |
| finale | Subtitle too long and small | "why most open-ocean animals", 44 px |
| all | Seek bug: the jellyfish never flashed in some renders. A clock tween drew each frame before the other tweens had updated their values on a forward seek, so it read stale values | Every scene now redraws from the timeline's own `onUpdate`, which runs after all tweens (see `docs/09-pitfalls.md`) |
| all | Checker: 9 errors, `template_literal_selector` (a template literal in `querySelector`) | Hardcoded selectors |
| all | Checker: captions host not marked; "1,000 m" label overlapped the depth chip | `data-track-kind="captions"`; gauge labels hide while the chip passes |
| all | Checker safe-zone warnings: "3 out of 4" above the Shorts top edge; captions below the Shorts / Reels / TikTok bottom edge; gauge and music notes outside TikTok's side edges | Captions moved to x 468, y 1185; labels and gauge moved inside |

## Pass 2: frames taken from the rendered v1 MP4
`tools/frame_stats.py` flagged 17 of 54 seconds as more than 70 % empty background.
| Problem | Fix |
|---|---|
| 8-10 s: open blue water between the school and the twilight zone | A whale silhouette cruising through it |
| 30-33 s and 37 s: the jellyfish alone in the dark | Distant flashing jellies and a drifting school |
| 38-39 s and 43-46 s: small subjects in a large dark frame | A school of blue-lit lanternfish crosses first; the camera pushes in on the dragonfish and the shrimp (scale 1.04 -> 1.36) |

v2 (whale, alarm) measured 16 of 54 seconds; v3 (colours) 15 of 54. The remaining flagged seconds are the midnight
zone, the inside of the light organ and the dark openings of the alarm and finale scenes, where the darkness is the
subject. For comparison the repo's 60 s antibiotics film measures 27 of 60.

## Measured on v3
- HyperFrames check: 0 errors, 0 warnings in lint, runtime, layout (YouTube Shorts, Instagram Reels and TikTok safe
  areas, 9 samples), motion, craft and audio; 13/13 text checks pass WCAG AA contrast.
- Audio: -14.0 LUFS integrated, -1.6 dBTP true peak, LRA 2.2 LU. Voice -17.2 LUFS. While speaking, the music sits
  13.5 dB and the effects 9.5 dB under the voice (RMS). The bed is pulled down on 7.3 % of samples (max 1.2 dB) so the
  summed tracks stay under the ceiling.
- Sync: 0.0 ms between the MP4's audio and the three stems. No black frames.
- Saturated-pixel share: under 7 % everywhere except 5.9 s (25.6 %) and 7.7 s (27.9 %), the sunlit surface water.
- Frames: mean empty background 62.9 %, 15 of 54 seconds over 70 %, mean brightness 48 of 255.
- Render: 1 min 14 s on 8 cores.

## Failed or open checks
- The voice is local Kokoro TTS (`af_heart`, 0.95x), a stand-in for your own voiceover. To swap:
  `python vo.py --recording your.wav`, then `align.py`, `build.py`, the three audio scripts, `build.py`, render.
- I cannot listen to audio. Loudness, peaks, ducking depth and sync are measured, not heard. The siren in the alarm
  scene and the score are the parts most worth a listen.
- Word times come from speech recognition (faster-whisper `base.en`), accurate to roughly 0.1-0.2 s.
- Safe areas are HyperFrames' built-in boxes (Shorts: x 48-888, y 288-1248 px; Reels: 6-94 % by 14-65 %; TikTok: two
  bands). The apps change their overlays over time; check one upload on a phone.
- Not uploaded or tested on YouTube or Instagram; their re-encode may band the dark gradients.
- Style rule broken on purpose: the sunlit water at 5.9 s and 7.7 s is above the 7 % saturation limit for dark scenes
  (it is a day scene; the style file measured about 30 % in day scenes).
- 15 seconds are still more than 70 % flat background by the frame_stats measure (listed above).
- Science simplifications in the picture (the narration is accurate; sources in `SCRIPT.md`):
  - The light organ close-up shows fuel and enzyme only; oxygen is left out, and the names luciferin and luciferase are not used.
  - The anglerfish lure is drawn green-cyan; real lures glow blue-green, from bacteria living in them.
  - The hatchetfish "seen from below" is a side view against the light.
  - The beam diagram shows the order in which colours are absorbed, not real distances.
  - The finale's ocean is to scale in depth only (0.25 px per metre, 3,700 m deep).
