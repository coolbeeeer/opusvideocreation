# Film review: mitochondria-short: REJECTED

Reviewed 2026-11-25 07:16 by tools/reviewer 1.0 (reviewer hash 236bd2dbfad4), round 1.
Film: `renders/mitochondria-v2.mp4`, plan: `../../tools/reviewer/calibration/mitochondria-short.plan.json`.

Stages: 1 script: PASSED / 2 scenes (plan): REJECTED (6 must) / 3 film: REJECTED (3 must).

## What to do

Fix every **must** item below, then review again: `python tools/reviewer/review.py film <project> --quick` while fixing,
and without `--quick` for the verdict (only a full review can approve). The film is approved only when no must item is left.
Each item says what was measured and what to change; times are film seconds with the frame number. `sheets/` shows the
frames of every event and flagged moment, `EVENTS.md` what was measured for every planned event. Change the film to do what
the plan says; do not weaken the plan to match the film. Rules: `tools/reviewer/STANDARD.md`.

## Must fix (9)

| # | Stage | Rule | Time | Scene | Problem | Fix |
|---|---|---|---|---|---|---|
| 1 | plan | P08 |  |  | Only 85 % of events are anchored to words. | Anchor events to the words they show; the picture must follow the voice. |
| 2 | plan | P09 |  |  | The film uses 1 shot sizes (medium). | Vary the framing: wide to show where we are, close for the action, extreme close for detail (at least 3 sizes). |
| 3 | plan | P10 |  |  | The lead, 'bacterium', acts 1 times in 7.4 s on screen (one per 7.4 s). | The lead must act or react at least once per 4.5 s on screen (my films: about one per 3 s). |
| 4 | plan | P11 |  |  | 67 % of picture events (reactions aside) have a sound cue; missing: walk #4 'dive', walk #5 'dive', origin #1 '11.14', origin #2 '11.2', deal #1 '18.56', deal #2 '18.56', deal #6 'host', proof #1 '23.36' .... | Give every action, appearance, effect and cut its own cue, timed with the same word (a gulp for a swallow, a clank for a bite). |
| 5 | plan | P11 |  |  | ' ' is the cue for 26 of 37 picture events. | Design a sound for each action; one stock sound for everything reads as generic. |
| 6 | plan | P13 | 0.00 s (frame 0) | walk | The first picture event is at 2.06 s. | Start on motion: something moves in the first second. |
| 7 | film | F09 |  |  | Only 32 of 54 planned picture events visibly happen at their time (59 %). | See the events marked 'not seen' below and in sheets/events-*.jpg: make each one visible (bigger, brighter, moving), on its word. |
| 8 | film | F10 |  |  | The picture is not tied to the words: planned events are seen at their times 59 % of the time, and 47 % of the time when moved 0.7-2.5 s (p = 0.045). | Start each event on its word (at("word") in the scene, the same anchor as plan.json) with a clear start, and keep the rest of its box calm between events; do not run animations on their own clock. |
| 9 | film | F11 | 29.73 s (frame 892) | proof | In 'proof', 'mitochondria' only poses: none of its 1 planned acts shows up in its box. | Animate 'mitochondria' on the planned words (bacteria). |

## Should fix (36)

| # | Stage | Rule | Time | Scene | Problem | Fix |
|---|---|---|---|---|---|---|
| 1 | plan | P11 |  |  | 7 distinct cue names for 37 cued events. | Vary the cues. |
| 2 | plan | P10 | 0.00-11.14 s (frames 0-334) | walk | Scene 'walk': its lead, 'mitochondria', acts 1 times in 11.1 s. | Add a reaction or gesture on a key word. |
| 3 | plan | P10 | 11.14-18.56 s (frames 334-557) | origin | Scene 'origin': its lead, 'bacterium', acts 1 times in 7.4 s. | Add a reaction or gesture on a key word. |
| 4 | plan | P10 | 18.56-23.36 s (frames 557-701) | deal | Scene 'deal': its lead, 'host cell', acts 1 times in 4.8 s. | Add a reaction or gesture on a key word. |
| 5 | plan | P10 | 23.36-30.57 s (frames 701-917) | proof | Scene 'proof': its lead, 'mitochondria', acts 1 times in 7.2 s. | Add a reaction or gesture on a key word. |
| 6 | plan | P05 | 23.48-26.14 s (frames 704-784) | proof | Scene 'proof': 2.7 s with no picture event while the narration says "The proof: mitochondria still carry their own". | Show what is said in that stretch: add a picture event on its key word. |
| 7 | plan | P05 | 32.15-34.86 s (frames 964-1046) | atp | Scene 'atp': 2.7 s with no picture event while the narration says "and oxygen into ATP, your cells'". | Show what is said in that stretch: add a picture event on its key word. |
| 8 | plan | P04 | 43.09-50.60 s (frames 1293-1518) | finale | Scene 'finale' plans 0.53 picture events per second. | Add events toward one per 1.5 s. |
| 9 | film | F10 |  |  | The film's big changes are only 1.15x as frequent at the planned times as elsewhere (p = 0.14). | Check that the big animations start on their words, and that plan.json lists every big change as an event. |
| 10 | film | F09 | 2.06 s (frame 62) | walk | walk event 2 (move, 'bacteria'): "auto: tl.to(st, { insetIn: 1, duration: 0.3, ease: "back.out(2)" }, at("bact" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 11 | film | F09 | 3.87 s (frame 116) | walk | walk event 3 (move, 'former'): "auto: tl.to(st, { morph: 1, duration: 0.35, ease: "power2.inOut" }, at("form" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 12 | film | F16 | 8.50 s (frame 255) | walk | 7.7 % very saturated bright pixels. | Keep one saturated accent; tone down the rest (style rule: about 7 % at most). |
| 13 | film | F09 | 9.32 s (frame 280) | walk | walk event 11 (move, 'thousands'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 14 | film | F16 | 9.50 s (frame 285) | walk | 9.5 % very saturated bright pixels. | Keep one saturated accent; tone down the rest (style rule: about 7 % at most). |
| 15 | film | F16 | 10.50 s (frame 315) | walk | 9.2 % very saturated bright pixels. | Keep one saturated accent; tone down the rest (style rule: about 7 % at most). |
| 16 | film | F09 | 12.93 s (frame 388) | origin | origin event 4 (move, 'bigger'): "auto: tl.to(st, { hx: HX1, duration: 1.0, ease: "power2.out" }, tB - 0.55);" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 17 | film | F09 | 13.82 s (frame 415) | origin | origin event 5 (move, 'swallowed'): "auto: tl.to(st, { pocket: 1, duration: 0.35, ease: "power2.out" }, tSw - 0.2" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 18 | film | F12 | 13.82 s (frame 415) | origin | origin event 5 ('swallowed') has no sound starting at its time (planned: cue). | Add or retime its cue. |
| 19 | film | F09 | 14.32 s (frame 430) | origin | origin event 6 (camera, 'swallowed'): "auto: tl.to(st, { pull: 1, duration: 0.55, ease: "power2.inOut" }, tSw + 0.3" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 20 | film | F09 | 16.37 s (frame 491) | origin | origin event 9 (move, 'digested'): "auto: tl.to(st, { chomp: 1, duration: 0.12, ease: "power3.in" }, tDig - 0.05" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 21 | film | F09 | 17.48 s (frame 524) | origin | origin event 11 (move, 'moved'): "auto: tl.to(st, { suit: 1, duration: 0.35, ease: "back.out(2.2)" }, at("move" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 22 | film | F09 | 19.42 s (frame 583) | deal | deal event 3 (effect, 'shelter'): "auto: tl.to(st, { shelter: 1, duration: 0.4, ease: "power2.out" }, at("shelt" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 23 | film | F09 | 26.94 s (frame 808) | proof | proof event 7 (effect, 'dna'): "auto: tl.to(st, { dna: 0.25, duration: 0.6 }, at("dna") + 0.7);" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 24 | film | F12 | 26.94 s (frame 808) | proof | proof event 7 ('dna') has no sound starting at its time (planned: sparkle). | Add or retime its cue. |
| 25 | film | F09 | 29.46 s (frame 884) | proof | proof event 11 (move, 'like'): "auto: tl.to(st, { eq: 1, duration: 0.3, ease: "back.out(2.5)" }, at("like") " is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 26 | film | F09 | 29.73 s (frame 892) | proof | proof event 12 (react, 'bacteria'): "mitochondria and bacteria smile side by side" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 27 | film | F09 | 31.74 s (frame 952) | atp | atp event 3 (effect, 'food'): "auto: tl.to(st, { work: 1, duration: 0.4 }, at("food") - 0.1);" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 28 | film | F09 | 32.15 s (frame 964) | atp | atp event 4 (move, 'oxygen'): "auto: drives frame() code" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 29 | film | F09 | 34.86 s (frame 1046) | atp | atp event 6 (effect, 'fuel'): "auto: tl.to(st, { flex: 1, duration: 0.25, ease: "power2.out" }, at("fuel") " is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 30 | film | F09 | 35.16 s (frame 1055) | atp | atp event 8 (effect, 'fuel'): "auto: tl.to(st, { flex: 0.35, duration: 0.35, ease: "power2.inOut" }, at("fu" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 31 | film | F09 | 36.69 s (frame 1101) | atp | atp event 11 (move, 'own'): "auto: tl.to(st, { tilt: 0, duration: 1.3, ease: "power2.inOut" }, at("own") " is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 32 | film | F09 | 37.80 s (frame 1134) | atp | atp event 13 (move, 'every'): "auto: tl.to(st, { dialA: 1, duration: 0.3 }, at("every") - 0.1);" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 33 | film | F09 | 40.47 s (frame 1214) | mother | mother event 4 (move, 'came'): "auto: tl.to(st, { gone: 1, duration: 0.45, ease: "power2.in" }, at("came") -" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 34 | film | F09 | 40.96 s (frame 1229) | mother | mother event 5 (effect, 'mother'): "auto: tl.to(st, { glow: 1, duration: 0.4 }, at("mother") - 0.2);" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 35 | film | F09 | 45.52 s (frame 1366) | finale | finale event 3 (effect, 'deal'): "auto: tl.to(st, { sparks: 1, duration: 0.4 }, at("deal") - 0.1);" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 36 | film | F09 | 47.51 s (frame 1425) | finale | finale event 6 (effect, 'ago'): "auto: tl.to(st, { sparks: 0, duration: 0.4 }, tT);" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |

## Measured

| Words | Film | Pace | Hook | Sentences (max / mean words) | Sources | 'you' | Numbers |
|---|---|---|---|---|---|---|---|
| 125 | 50.6 s | 148.2 wpm | 8 words, ends 2.52 s | 15 (19 / 8.3) | 11 | 8 | 7 |

| Scene | Length | Picture events planned | Shown in the film | Planned /s | Measured onsets /s | Median motion | Shot sizes (moves) |
|---|---|---|---|---|---|---|---|
| walk | 11.1 s | 8 (+4 text) | 5 / 8 | 0.72 | 2.42 | 5.44 | medium (not filled in) |
| origin | 7.4 s | 10 (+1 text) | 5 / 10 | 1.35 | 1.75 | 1.67 | medium (not filled in) |
| deal | 4.8 s | 6 (+3 text) | 5 / 6 | 1.25 | 1.88 | 1.87 | medium (not filled in) |
| proof | 7.2 s | 9 (+3 text) | 6 / 9 | 1.25 | 1.52 | 0.39 | medium (not filled in) |
| atp | 8.8 s | 10 (+4 text) | 4 / 10 | 1.14 | 1.48 | 2.31 | medium (not filled in) |
| mother | 3.8 s | 7 (+2 text) | 5 / 7 | 1.86 | 1.86 | 0.71 | medium (not filled in) |
| finale | 7.5 s | 4 (+2 text) | 2 / 4 | 0.53 | 1.73 | 4.26 | medium (not filled in) |

Plan: text share 0.26, anchored to words 0.85, sizes used medium, cue coverage 0.67, holds [(11.0, 13.0, 'the match cut into the past: the vignette closes and opens (REVIEW.md, accepted flat seconds 11-12)'), (14.0, 15.0, 'the big cell closes around the bacterium (REVIEW.md, accepted flat second 14)'), (23.0, 24.0, 'the first second of the proof scene (REVIEW.md, accepted flat second 23)')].

| Check | Measured |
|---|---|
| MP4 | 1080x1920 h264 yuv420p, 30.0 fps, 50.6 s, 34.2 MB |
| Loudness | -14.0 LUFS, true peak -1.6 dBTP, LRA 2.2 LU |
| Sync | 0.0 ms vs the stems |
| Motion | median 2.9; frozen runs (0.5 s+) [] |
| Empty frames | mean flat 59.7 %; seconds over 70 %: [11, 12, 14, 23] |
| Picture onsets | 1.84 per second; dead stretches [] |
| Events shown | 0.593 of planned picture events at their time and place; acts shown 0.8 |
| Word lock | the same events moved 0.7-2.5 s are seen 0.468 of the time (p = 0.045); big picture onsets 1.145x as frequent at planned times as elsewhere (p = 0.14) |
| Sound | cued events with a sound starting at their time 0.946 (shifted cues: 0.838, p = 0.045); largest group of identical cues 0.057 |
| Mix | voice over the bed 9.0 dB, music under the voice 15.6 dB, music present 1.0 |
| Captions | band [1128, 1248] px (correlation 0.273), follow 0.76 of words |
| HyperFrames | default: passed (0 errors, 0 warnings); dense: passed (0 errors, 0 warnings) |
| Seek test | 7.167 s: 1.62, 14.767 s: 1.34, 20.967 s: 1.28, 27.667 s: 1.71, 35.3 s: 1.4, 41.1 s: 1.48, 45.667 s: 1.44 (mean difference per frame) |

## The rules

Every rule id above is defined in `tools/reviewer/STANDARD.md` (thresholds in `tools/reviewer/standard.py`).
