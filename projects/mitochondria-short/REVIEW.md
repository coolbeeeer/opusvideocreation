# The Bacteria That Moved Into Your Cells (50.6 s, vertical): self-review

Final file: `renders/mitochondria-v2.mp4`. 1080x1920, 30 fps, 1518 frames, 50.600 s, H.264 High (yuv420p,
5.2 Mb/s), AAC LC stereo 48 kHz (201 kb/s), 34.2 MB. Contact sheet from the MP4, one frame every 1.5 s:
`renders/mitochondria-v2-contact.jpg`. Cover for Reels: `renders/mitochondria-cover.jpg` (the title at 49.6 s).
The v1 render was superseded and is not included; `review/render-v1-every1.5s.jpg` shows the frames it was judged on.

## How it is built
- `film.json`: 8 lines with a pause after each (`NOTES.md`, question 2), 7 scenes, 1080x1920, 30 fps.
- `vo.py` (Kokoro TTS, one call per line; `--clips` and `--recording` take your own voice), `align.py` (faster-whisper:
  125 of 125 words matched), `build.py` (scenes, captions, `captions.srt`).
- Drawing: `lib/kit.js`, `lib/kit-plus.js` (camera, eyes, bacterium, the new zoom chain), `lib/kit-ocean.js` (glows,
  particles, scene layers), and two new kits: `lib/kit-human.js` (the walking person) and `lib/kit-cell.js`
  (mitochondria, the host cell, tissue levels, ATP, the balance, the cytoplasm backdrop). `assets/world.js` builds
  the park, the walker and the four dive levels for the first and last scenes.
- Audio: `audio/js_events.cjs` (footstep times from the walk rig), `audio/sfx_cues.py`, `audio/music.py` (original
  score whose beat is one footstep), `audio/mix.py` (-14 LUFS).

## Pass 1: snapshots of each scene before rendering
Sheets in `review/` (`<scene>-v1.jpg` is the first look, the higher number the fixed one).
| Scene | Problem | Fix |
|---|---|---|
| kits | Human model sheet: the pelvis and torso read as a block; Mom needed long hair | Reshaped the seat and torso; `hairStyle: "long"` |
| kits | Cell sheet: the mitochondria inside the fibre were too long to read as beans | Shortened |
| walk | The second bacterium's tail poked out of the round thought bubble (checker: container overflow) | Tails point inward |
| walk | "Muscle cells" was on screen 0.44 s; pinned tags slid above the top safe edge as the zoom passed | About 0.6 s; pinned tags stop at the safe-area edge, then hide |
| walk | The subline under "Mitochondria" was on screen 0.44 s (checker: unread line) | Removed; the narration says it |
| origin | The camera reached the wide shot before the big cell arrived, so the bacterium sat small and alone | Two pull-backs: stay big on the bacterium, reveal the host on "bigger"; then a push-in for "it wasn't digested" |
| origin | After the swallow the bacterium's tail stuck out through the host's membrane | The tail retracts (new `len` on `KP.bact`) |
| origin | Grey enzymes on lavender were hard to see, and one covered the host's eye | Bigger, acid green, coming from below; a white "clank" where they bite |
| deal | A second copy of the guest (for the division) showed before the split: two tails | Hidden until it splits |
| deal | Landed coins faded to a muddy brown; coins already in flight jumped when the guest split | Coins stay bright and float; each coin's launch point is fixed from where its guest was at launch time |
| deal | "Energy" tag covered the host's eye; the bubble sat on the caption line; food came from the side away from its tag | Tag below the eyes; the bubble lifted 80 px; food enters under "Food" |
| proof | The pair was small in the top third, the bottom half empty, the last checklist row touched the captions; the bacterium's tail pointed at the mitochondrion like a string | Larger pair, checklist moved up, tail points outward |
| proof | "The proof" was readable for about 0.2 s before the name tags arrived in the same band | The banner sits where the checklist will be and hands over to it |
| proof | The DNA rings were too small to see on "own DNA" | They swell and glow on the word |
| atp | Everything sat in the top third; "Cell fuel" was cut off at the right edge | Rebuilt for 9:16: food from upper left, oxygen from upper right, ATP pouring into a muscle fibre that contracts |
| atp | The balance's hanging pans ran their strings through the person | `KC.balance` redrawn with dishes riding on the beam |
| atp | "≈" never appeared in "≈ your body weight": the glyph is not in Nunito and the renderer drew nothing | "~your body weight" |
| mother | The sperm was tiny at the right edge; its mitochondria were invisible | It comes down from above at twice the size, with a "Dad's" tag on its mitochondria |
| mother | A slow crossfade ghosted Mom over the egg; her raised arm read as asking a question | The egg shrinks away and Mom and you pop in; Mom waves from the elbow; you stand opposite |
| finale | The title sat on the walker's head | The last shot pulls back to 0.72x and the title sits above the walker |
| finale | The gradient bar under the title never showed (its opacity was set to 0 and never animated back) | Fixed |
| finale | Lights in the legs too small; the sunset foreground a flat brown | Bigger lights with a halo; the near ground darkens toward the bottom |

Checker (`npx hyperframes@0.9.56 check`). The default run samples the safe areas only 9 times, so I also ran
`--samples=100` and `--samples=150`:
| Finding | Fix |
|---|---|
| "Mitochondrion" outside TikTok's left edge, "Bacterium" outside Shorts' right edge (25.3 s) | Tags moved inward, 44 px |
| Only with more samples: "ATP" outside the Shorts and TikTok right edges (33.6-35.7 s); "weight" outside TikTok's right edge (38.2-39.2 s) | Labels below y 840 kept within x 120-780 (TikTok's lower band is narrower because of its buttons); the balance moved left |
| Only with more samples: `rotation_pivot_drift` on the enzymes and coins, which spin while they fly | `data-layout-allow-orbit` on those groups (the checker's opt-out for intended motion) |
| Only with more samples: `off_pivot_rotation` on the day dial's hand | The checker takes the hub from the most-shared circle centre in the whole scene SVG (here the coins' glows), not from the dial; a hub circle on the dial and the same opt-out, with a comment |

## Pass 2: frames taken from the rendered MP4
| Check | v1 | Fix | v2 |
|---|---|---|---|
| frame_stats: seconds over 70 % flat | 23 of 50, including 20 in a row (23-42 s) with motion as low as 0.06 | `KC.cytoplasm`, an out-of-focus cell interior behind the proof, ATP and mother scenes | 4 of 50 |
| frame_stats itself | Squashed vertical frames into 480x270 (blocks of 27x85 px) | Keeps the aspect ratio now | |
| Cut frames (`review/render-v2-cuts.jpg`) | | | Clean; the walk-to-origin match cut lines up in size and angle |
| Seek order: 7 frames from the MP4 against fresh seeks at the same times | | | Mean difference 1.3-1.75 of 255 (compression), at most 0.31 % of pixels off by more than 40: no order-dependent state |

The four remaining flagged seconds are accepted: 11-12 s (the vignette closing and opening is the match cut into the
past), 14 s (one second while the big cell closes around the bacterium), 23 s (the first second of the proof scene).
Measurements: `review/frame-stats-v1.txt`, `review/frame-stats-v2.txt`, `review/verify-v2.txt`.

## Measured on v2
- HyperFrames check: 0 errors, 0 warnings, 0 info in lint, runtime, layout (Shorts, Reels and TikTok safe areas),
  motion, contrast (18 of 18 text checks pass WCAG AA), craft (404 samples) and audio. The 150-sample layout run is
  also clean.
- Audio: -14.0 LUFS integrated, -1.6 dBTP true peak, LRA 2.2 LU. Voice -17.1 LUFS. While speaking, the music sits
  13.5 dB and the effects 9.3 dB under the voice (RMS), the same balance as the ocean Short. The bed is pulled down on
  4.1 % of samples (at most 1.1 dB) so the summed tracks stay under the ceiling.
- Sync: 0.0 ms between the MP4's audio and the three stems. No black frames.
- Saturated-pixel share: under 7 % everywhere except 10.6 s (8.1 %), the close-up of the orange mitochondrion.
- Frames: mean flat background 59.8 %, 4 of 50 seconds over 70 %, mean brightness 93 of 255, median motion 2.8.
- Render: 61 s on 8 cores.

## Failed or open checks
- The voice is local Kokoro TTS (`af_heart`, 0.95x), a stand-in. To use your channel's voice, record or generate one
  clip per line and run `python vo.py --clips DIR` (steps in `NOTES.md`, question 5).
- I cannot listen to audio. Loudness, peaks, ducking, sync and the footstep timing are measured, not heard. Worth a
  listen: the footsteps (synthesised gravel), the score's walking theme, and the "time travel" riser at 11.1 s.
- Word times come from speech recognition (faster-whisper `base.en`), accurate to roughly 0.1-0.2 s.
- Safe areas are HyperFrames' built-in boxes, and only text is checked against them. The apps change their
  overlays; check one upload on a phone.
- Not uploaded to YouTube or Instagram, so their re-encode is untested.
- 10.6 s is 8.1 % saturated pixels, over the 7 % guide; it is the film's accent colour filling the frame for one beat.
- Four seconds are over 70 % flat background (listed above).
- With the corrected `frame_stats.py`, the ocean Short re-measures 26 of 54 flagged seconds, not the 15 in its
  review. I have not changed that film.
- Science simplifications are listed in `SCRIPT.md`: the dive compresses scale, the host is drawn as a generic blob
  (it was probably an archaeon), "swallowed" is the classic picture of a debated step, and the "deal" simplifies the
  early exchange.
