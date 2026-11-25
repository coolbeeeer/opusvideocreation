# Film review: ocean-glow-short: REJECTED

Reviewed 2026-11-25 07:18 by tools/reviewer 1.0 (reviewer hash 236bd2dbfad4), round 1.
Film: `renders/ocean-glow-v3.mp4`, plan: `../../tools/reviewer/calibration/ocean-glow-short.plan.json`.

Stages: 1 script: PASSED / 2 scenes (plan): REJECTED (5 must) / 3 film: REJECTED (10 must).

## What to do

Fix every **must** item below, then review again: `python tools/reviewer/review.py film <project> --quick` while fixing,
and without `--quick` for the verdict (only a full review can approve). The film is approved only when no must item is left.
Each item says what was measured and what to change; times are film seconds with the frame number. `sheets/` shows the
frames of every event and flagged moment, `EVENTS.md` what was measured for every planned event. Change the film to do what
the plan says; do not weaken the plan to match the film. Rules: `tools/reviewer/STANDARD.md`.

## Must fix (15)

| # | Stage | Rule | Time | Scene | Problem | Fix |
|---|---|---|---|---|---|---|
| 1 | plan | P08 |  |  | Only 83 % of events are anchored to words. | Anchor events to the words they show; the picture must follow the voice. |
| 2 | plan | P09 |  |  | The film uses 1 shot sizes (medium). | Vary the framing: wide to show where we are, close for the action, extreme close for detail (at least 3 sizes). |
| 3 | plan | P11 |  |  | 56 % of picture events (reactions aside) have a sound cue; missing: hook #1 '0.0', hook #4 'animals', hook #5 'open', hook #6 'ocean', hook #7 'own', descent #1 '5.05', descent #3 'by', descent #5 'below' .... | Give every action, appearance, effect and cut its own cue, timed with the same word (a gulp for a swallow, a clank for a bite). |
| 4 | plan | P11 |  |  | ' ' is the cue for 25 of 35 picture events. | Design a sound for each action; one stock sound for everything reads as generic. |
| 5 | plan | P08 | 14.39 s (frame 432) | chemistry | chemistry event 4 ('by'): -0.73 s from the start of its word (0.06 s long). | Anchor it to the word it shows: within 0.6 s before the word starts or after it ends. |
| 6 | film | F07 |  |  | 26 of 54 seconds are mostly empty background (48 %). | Fill the frames listed in review.json (flat_seconds). |
| 7 | film | F09 |  |  | Only 45 of 63 planned picture events visibly happen at their time (71 %). | See the events marked 'not seen' below and in sheets/events-*.jpg: make each one visible (bigger, brighter, moving), on its word. |
| 8 | film | F14 |  |  | HyperFrames check (dense): 0 errors, 17 warnings: ⚠ t=4.878s rotation_pivot_drift #host-hook > div:nth-of-type(2) > svg:nth-of-type(1) > g:nth-of-type(3) > g:nth-of-type(1) > g:nth-of-type(1) > g:nth-of-type(1) > g:nth-of-type(1) > g:nth-of-type(2) > g:nth-of-type(1) — Rotating element's bounding-box center drifts 81px across rotation — it is not spinning about its own center (check transformOrigin/svgOrigin). / ⚠ t=4.878s rotation_pivot_drift #host-hook > div:nth-of-type(2) > svg:nth-of-type(1) > g:nth-of-type(3) > g:nth-of-type(1) > g:nth-of-type(1) > g:nth-of-type(2) > g:nth-of-type(1) > g:nth-of-type(2) > g:nth-of-type(1) — Rotating element's bounding-box center drifts 85px across rotation — it is not spinning about its own center (check transformOrigin/svgOrigin). / ⚠ t=4.878s rotation_pivot_drift g.L-act > g:nth-of-type(1) > g:nth-of-type(3) > g:nth-of-type(1) > g:nth-of-type(2) > g:nth-of-type(1) — Rotating element's bounding-box center drifts 99px across rotation — it is not spinning about its own center (check transformOrigin/svgOrigin). / ⚠ t=4.878s rotation_pivot_drift #host-hook > div:nth-of-type(2) > svg:nth-of-type(1) > g:nth-of-type(3) > g:nth-of-type(1) > g:nth-of-type(1) > g:nth-of-type(4) > g:nth-of-type(1) > g:nth-of-type(1) > g:nth-of-type(1) — Rotating element's bounding-box center drifts 92px across rotation — it is not spinning about its own center (check transformOrigin/svgOrigin). | Fix every finding (docs/09-pitfalls.md has the usual ones). |
| 9 | film | F07 | 9.00-14.00 s (frames 270-420) | descent | 5 seconds in a row are mostly empty background (over 70 % flat). | Fill the frame: a bigger subject, a slow push-in, a low-contrast background layer (KC.cytoplasm, KS.stage stars, KO.snow). If the emptiness is the point, declare a hold with the reason. |
| 10 | film | F07 | 15.00-17.00 s (frames 450-510) | chemistry | 2 seconds in a row are mostly empty background (over 70 % flat). | Fill the frame: a bigger subject, a slow push-in, a low-contrast background layer (KC.cytoplasm, KS.stage stars, KO.snow). If the emptiness is the point, declare a hold with the reason. |
| 11 | film | F07 | 19.00-25.00 s (frames 570-750) | angler | 6 seconds in a row are mostly empty background (over 70 % flat). | Fill the frame: a bigger subject, a slow push-in, a low-contrast background layer (KC.cytoplasm, KS.stage stars, KO.snow). If the emptiness is the point, declare a hold with the reason. |
| 12 | film | F07 | 26.00-28.00 s (frames 780-840) | hatchet | 2 seconds in a row are mostly empty background (over 70 % flat). | Fill the frame: a bigger subject, a slow push-in, a low-contrast background layer (KC.cytoplasm, KS.stage stars, KO.snow). If the emptiness is the point, declare a hold with the reason. |
| 13 | film | F07 | 31.00-33.00 s (frames 930-990) | alarm | 2 seconds in a row are mostly empty background (over 70 % flat). | Fill the frame: a bigger subject, a slow push-in, a low-contrast background layer (KC.cytoplasm, KS.stage stars, KO.snow). If the emptiness is the point, declare a hold with the reason. |
| 14 | film | F07 | 37.00-40.00 s (frames 1110-1200) | alarm | 3 seconds in a row are mostly empty background (over 70 % flat). | Fill the frame: a bigger subject, a slow push-in, a low-contrast background layer (KC.cytoplasm, KS.stage stars, KO.snow). If the emptiness is the point, declare a hold with the reason. |
| 15 | film | F07 | 43.00-48.00 s (frames 1290-1440) | colours | 5 seconds in a row are mostly empty background (over 70 % flat). | Fill the frame: a bigger subject, a slow push-in, a low-contrast background layer (KC.cytoplasm, KS.stage stars, KO.snow). If the emptiness is the point, declare a hold with the reason. |

## Should fix (39)

| # | Stage | Rule | Time | Scene | Problem | Fix |
|---|---|---|---|---|---|---|
| 1 | script | S08 |  |  | The script says 'you/your' 0 times. | Put the viewer in the story: what it means for them, in their body, in their day. |
| 2 | plan | P10 |  |  | No character appears in the film. | Give the story a character with a face (a cell, a fish, an astronaut) and let it react. |
| 3 | plan | P11 |  |  | 9 distinct cue names for 35 cued events. | Vary the cues. |
| 4 | plan | P04 | 5.05-12.87 s (frames 152-386) | descent | Scene 'descent' plans 0.64 picture events per second. | Add events toward one per 1.5 s. |
| 5 | plan | P05 | 5.84-8.15 s (frames 175-244) | descent | Scene 'descent': 2.3 s with no picture event while the narration says "and sunlight fades fast. By". | Show what is said in that stretch: add a picture event on its key word. |
| 6 | plan | P05 | 8.15-10.21 s (frames 244-306) | descent | Scene 'descent': 2.1 s with no picture event while the narration says "By two hundred metres, it's twilight.". | Show what is said in that stretch: add a picture event on its key word. |
| 7 | plan | P05 | 32.97-35.00 s (frames 989-1050) | alarm | Scene 'alarm': 2.0 s with no picture event while the narration says "flash like a burglar alarm,". | Show what is said in that stretch: add a picture event on its key word. |
| 8 | plan | P05 | 39.94-42.57 s (frames 1198-1277) | colours | Scene 'colours': 2.6 s with no picture event while the narration says "blue travels farthest in water.". | Show what is said in that stretch: add a picture event on its key word. |
| 9 | film | F09 | 1.87 s (frame 56) | hook | hook event 5 (move, 'open'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 10 | film | F09 | 2.30 s (frame 69) | hook | hook event 6 (move, 'ocean'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 11 | film | F09 | 3.14 s (frame 94) | hook | hook event 7 (move, 'own'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 12 | film | F09 | 4.38 s (frame 131) | hook | hook event 8 (move, 'why'): "auto: tl.fromTo(q, { opacity: 0, scale: 0.3, rotation: -20 }, { opacity: 1, " is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 13 | film | F16 | 5.50 s (frame 165) | descent | 15.5 % very saturated bright pixels. | Keep one saturated accent; tone down the rest (style rule: about 7 % at most). |
| 14 | film | F16 | 6.50 s (frame 195) | descent | 36.9 % very saturated bright pixels. | Keep one saturated accent; tone down the rest (style rule: about 7 % at most). |
| 15 | film | F16 | 7.50 s (frame 225) | descent | 30.4 % very saturated bright pixels. | Keep one saturated accent; tone down the rest (style rule: about 7 % at most). |
| 16 | film | F09 | 8.15 s (frame 244) | descent | descent event 3 (move, 'by'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 17 | film | F16 | 8.50 s (frame 255) | descent | 20.5 % very saturated bright pixels. | Keep one saturated accent; tone down the rest (style rule: about 7 % at most). |
| 18 | film | F09 | 10.21 s (frame 306) | descent | descent event 5 (move, 'below'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 19 | film | F09 | 12.14 s (frame 364) | descent | descent event 7 (move, 'forever'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 20 | film | F09 | 13.45 s (frame 404) | chemistry | chemistry event 3 (move, 'so'): "auto: tl.to(st, { k: 1.2, duration: 0.3, ease: "power2.out", onUpdate: () =>" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 21 | film | F12 | 14.39 s (frame 432) | chemistry | chemistry event 4 ('by') has no sound starting at its time (planned: cue). | Add or retime its cue. |
| 22 | film | F09 | 20.30 s (frame 609) | angler | angler event 6 (move, 'curious'): "auto: tl.to(pw, { x: PX, duration: tStop - tIn, ease: "power2.out" }, tIn);" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 23 | film | F09 | 20.88 s (frame 626) | angler | angler event 7 (move, 'swims'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 24 | film | F09 | 21.26 s (frame 638) | angler | angler event 8 (move, 'closer'): "auto: tl.fromTo(heart, { opacity: 0, scale: 0.3, svgOrigin: "0 0", x: PX + 1" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 25 | film | F09 | 24.43 s (frame 733) | hatchet | hatchet event 4 (move, 'lights'): "auto: tl.to(lights, { k: 1.1, duration: 0.45, ease: "power2.out", onUpdate: " is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 26 | film | F08 | 24.47-26.07 s (frames 734-782) | hatchet | Dead stretch: 1.6 s with no picture onset and little motion (0.55) while the narration says "lights up its belly to match the". | Show what is being said: an action on its key word, or at least a reaction or camera move. |
| 27 | film | F09 | 25.76 s (frame 773) | hatchet | hatchet event 5 (move, 'match'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 28 | film | F09 | 26.20 s (frame 786) | hatchet | hatchet event 6 (move, 'glow'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 29 | film | F09 | 27.15 s (frame 814) | hatchet | hatchet event 7 (move, 'above'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 30 | film | F08 | 28.07-29.67 s (frames 842-890) | hatchet | Dead stretch: 1.6 s with no picture onset and little motion (0.26) while the narration says "below, its silhouette vanishes.". | Show what is being said: an action on its key word, or at least a reaction or camera move. |
| 31 | film | F06 | 28.90-29.60 s (frames 867-888) | hatchet | The picture is frozen for 0.7 s (motion under 0.2) while the narration says "its silhouette". | Keep something alive: a reaction, a camera drift, the background moving. |
| 32 | film | F12 | 35.00 s (frame 1050) | alarm | alarm event 7 ('likely') has no sound starting at its time (planned: cue). | Add or retime its cue. |
| 33 | film | F09 | 37.15 s (frame 1114) | alarm | alarm event 11 (move, 'attacker'): "auto: tl.set(aw, { opacity: 0 }, tA);" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 34 | film | F08 | 40.73-42.67 s (frames 1222-1280) | colours | Dead stretch: 1.9 s with no picture onset and little motion (0.22) while the narration says "farthest in water. But one". | Show what is being said: an action on its key word, or at least a reaction or camera move. |
| 35 | film | F09 | 44.25 s (frame 1328) | colours | colours event 10 (move, 'with'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 36 | film | F09 | 45.10 s (frame 1353) | colours | colours event 11 (move, 'prey'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 37 | film | F06 | 48.90-49.60 s (frames 1467-1488) | finale | The picture is frozen for 0.7 s (motion under 0.2) in a pause. | Keep something alive: a reaction, a camera drift, the background moving. |
| 38 | film | F12 | 48.93 s (frame 1468) | finale | finale event 6 ('ocean') has no sound starting at its time (planned: cue). | Add or retime its cue. |
| 39 | film | F06 | 49.90-50.60 s (frames 1497-1518) | finale | The picture is frozen for 0.7 s (motion under 0.2) while the narration says "residents brought". | Keep something alive: a reaction, a camera drift, the background moving. |

## Measured

| Words | Film | Pace | Hook | Sentences (max / mean words) | Sources | 'you' | Numbers |
|---|---|---|---|---|---|---|---|
| 132 | 54.2 s | 146.1 wpm | 14 words, ends 3.66 s | 17 (19 / 7.8) | 12 | 0 | 5 |

| Scene | Length | Picture events planned | Shown in the film | Planned /s | Measured onsets /s | Median motion | Shot sizes (moves) |
|---|---|---|---|---|---|---|---|
| hook | 5.0 s | 7 (+1 text) | 3 / 7 | 1.39 | 1.19 | 0.84 | medium (not filled in) |
| descent | 7.8 s | 5 (+2 text) | 2 / 5 | 0.64 | 2.3 | 4.84 | medium (not filled in) |
| chemistry | 4.6 s | 8 (+3 text) | 7 / 8 | 1.74 | 1.52 | 1.75 | medium (not filled in) |
| angler | 5.8 s | 9 (+2 text) | 6 / 9 | 1.55 | 1.2 | 1.42 | medium (not filled in) |
| hatchet | 7.3 s | 11 (+1 text) | 7 / 11 | 1.52 | 0.96 | 0.56 | medium (not filled in) |
| alarm | 7.3 s | 8 (+3 text) | 7 / 8 | 1.09 | 1.37 | 4.03 | medium (not filled in) |
| colours | 8.7 s | 10 (+3 text) | 8 / 10 | 1.15 | 1.38 | 1.45 | medium (not filled in) |
| finale | 7.7 s | 5 (+3 text) | 5 / 5 | 0.65 | 1.05 | 0.2 | medium (not filled in) |

Plan: text share 0.22, anchored to words 0.83, sizes used medium, cue coverage 0.56, holds [].

| Check | Measured |
|---|---|
| MP4 | 1080x1920 h264 yuv420p, 30.0 fps, 54.2 s, 36.5 MB |
| Loudness | -14.0 LUFS, true peak -1.6 dBTP, LRA 2.2 LU |
| Sync | 0.0 ms vs the stems |
| Motion | median 1.42; frozen runs (0.5 s+) [(28.9, 29.6), (42.1, 42.6), (48.9, 49.6), (49.9, 50.6), (52.1, 54.2)] |
| Empty frames | mean flat 68.4 %; seconds over 70 %: [0, 9, 10, 11, 12, 13, 15, 16, 19, 20, 21, 22, 23, 24, 26, 27, 31, 32, 37, 38, 39, 43, 44, 45, 46, 47] |
| Picture onsets | 1.38 per second; dead stretches [(np.float64(24.47), np.float64(26.07)), (28.07, np.float64(29.67)), (np.float64(40.73), np.float64(42.67))] |
| Events shown | 0.714 of planned picture events at their time and place; acts shown - |
| Word lock | the same events moved 0.7-2.5 s are seen 0.518 of the time (p = 0.0012); big picture onsets 1.382x as frequent at planned times as elsewhere (p = 0.027) |
| Sound | cued events with a sound starting at their time 0.914 (shifted cues: 0.657, p = 0.005); largest group of identical cues 0.062 |
| Mix | voice over the bed 9.1 dB, music under the voice 15.5 dB, music present 1.0 |
| Captions | band [1128, 1224] px (correlation 0.347), follow 0.826 of words |
| HyperFrames | default: passed (0 errors, 0 warnings); dense: passed (0 errors, 17 warnings) |
| Seek test | 2.033 s: 1.44, 8.3 s: 1.42, 15.033 s: 1.29, 21.033 s: 1.33, 27.3 s: 1.32, 35.133 s: 1.58, 42.733 s: 1.54, 48.2 s: 1.31 (mean difference per frame) |

## The rules

Every rule id above is defined in `tools/reviewer/STANDARD.md` (thresholds in `tools/reviewer/standard.py`).
