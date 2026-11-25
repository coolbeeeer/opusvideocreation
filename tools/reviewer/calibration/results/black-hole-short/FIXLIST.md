# Film review: black-hole-short: REJECTED

Reviewed 2026-11-25 07:14 by tools/reviewer 1.0 (reviewer hash 236bd2dbfad4), round 1.
Film: `renders/black-hole-v3.mp4`, plan: `../../tools/reviewer/calibration/black-hole-short.plan.json`.

Stages: 1 script: PASSED / 2 scenes (plan): REJECTED (1 must) / 3 film: REJECTED (1 must).

## What to do

Fix every **must** item below, then review again: `python tools/reviewer/review.py film <project> --quick` while fixing,
and without `--quick` for the verdict (only a full review can approve). The film is approved only when no must item is left.
Each item says what was measured and what to change; times are film seconds with the frame number. `sheets/` shows the
frames of every event and flagged moment, `EVENTS.md` what was measured for every planned event. Change the film to do what
the plan says; do not weaken the plan to match the film. Rules: `tools/reviewer/STANDARD.md`.

## Must fix (2)

| # | Stage | Rule | Time | Scene | Problem | Fix |
|---|---|---|---|---|---|---|
| 1 | plan | P10 | 25.64-32.69 s (frames 769-981) | friend | Scene 'friend': 'friend' is on screen for 7.1 s and only poses (looks). | Give 'friend' actions on the words: react with the face, gesture, move with purpose (my films: panic on 'feet', stretch on 'stretched', shrug on 'nothing'). If the character is only a prop here, take it out of the cast. |
| 2 | film | F11 | 1.97-3.76 s (frames 59-113) | hook | In 'hook', 'astronaut' only poses: none of its 2 planned acts shows up in its box. | Animate 'astronaut' on the planned words (black, big). |

## Should fix (25)

| # | Stage | Rule | Time | Scene | Problem | Fix |
|---|---|---|---|---|---|---|
| 1 | script | S09 |  |  | Only 1 concrete numbers or comparisons. | Give scale: 'ten times as heavy as the Sun', 'your own body weight every day'. |
| 2 | script | S06 | 26.13 s (frame 784) |  | Sentence of 21 words: "But a friend watching from far away sees you slow down, turn red and fade, as if frozen at the edge." | Consider splitting it into two. |
| 3 | plan | P10 |  |  | The lead, 'astronaut', acts once per 4.0 s on screen. | Aim for one act or reaction per 3 s. |
| 4 | plan | P05 | 11.75-14.22 s (frames 352-427) | small | Scene 'small': 2.5 s with no picture event while the narration says "noodle before you even reach it.". | Show what is said in that stretch: add a picture event on its key word. |
| 5 | plan | P05 | 18.34-20.77 s (frames 550-623) | giant | Scene 'giant': 2.4 s with no picture event while the narration says "like the one at the center of our galaxy,". | Show what is said in that stretch: add a picture event on its key word. |
| 6 | plan | P15 | 33.68 s (frame 1010) | inside | inside event 4 is planned on 'time', but the scene code never uses at("time"). | Implement the event on its word, or correct the plan. |
| 7 | plan | P10 | 44.37-51.40 s (frames 1331-1542) | finale | Scene 'finale': its lead, 'astronaut', acts 1 times in 7.0 s. | Add a reaction or gesture on a key word. |
| 8 | film | F09 | 1.97 s (frame 59) | hook | hook event 2 (react, 'black'): "eyes go wide, brows jump and the mouth drops open at the black hole below" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 9 | film | F09 | 3.76 s (frame 113) | hook | hook event 6 (react, 'big'): "eyes widen again and the mouth opens: how big?" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 10 | film | F12 | 8.21 s (frame 246) | small | small event 4 ('pulls') has no sound starting at its time (planned: whoosh (small)). | Add or retime its cue. |
| 11 | film | F09 | 16.32 s (frame 490) | small | small event 13 (move, 'spaghettification'): "the noodle is slurped down into the hole" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 12 | film | F12 | 17.25 s (frame 518) | giant | giant event 1 (placed at 17.25 s) has no sound starting at its time (planned: rumble (deep)). | Add or retime its cue. |
| 13 | film | F09 | 20.77 s (frame 623) | giant | giant event 5 (react, 'gentler'): "relaxes: a smile, eyes half closed" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 14 | film | F08 | 25.64-32.69 s (frames 769-981) | friend | Scene 'friend' shows 0.57 picture onsets per second. | Add picture events. |
| 15 | film | F12 | 25.64 s (frame 769) | friend | friend event 1 (placed at 25.64 s) has no sound starting at its time (planned: rumble (far)). | Add or retime its cue. |
| 16 | film | F09 | 27.99 s (frame 840) | friend | friend event 5 (move, 'slow'): "in the view, the astronaut and the clock hand slow down" is not seen in its box at its time. | Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move). |
| 17 | film | F08 | 29.67-31.20 s (frames 890-936) | friend | Dead stretch: 1.5 s with no picture onset and little motion (0.38) while the narration says "and fade, as if frozen". | Show what is being said: an action on its key word, or at least a reaction or camera move. |
| 18 | film | F16 | 30.50 s (frame 915) | friend | 8.2 % very saturated bright pixels. | Keep one saturated accent; tone down the rest (style rule: about 7 % at most). |
| 19 | film | F08 | 31.20-32.73 s (frames 936-982) | friend | Dead stretch: 1.5 s with no picture onset and little motion (0.19) while the narration says "at the edge.". | Show what is being said: an action on its key word, or at least a reaction or camera move. |
| 20 | film | F16 | 31.50 s (frame 945) | friend | 7.6 % very saturated bright pixels. | Keep one saturated accent; tone down the rest (style rule: about 7 % at most). |
| 21 | film | F06 | 32.00-32.70 s (frames 960-981) | friend | The picture is frozen for 0.7 s (motion under 0.2) in a pause. | Keep something alive: a reaction, a camera drift, the background moving. |
| 22 | film | F16 | 32.50 s (frame 975) | friend | 7.6 % very saturated bright pixels. | Keep one saturated accent; tone down the rest (style rule: about 7 % at most). |
| 23 | film | F06 | 44.50-45.10 s (frames 1335-1353) | finale | The picture is frozen for 0.6 s (motion under 0.2) while the narration says "So if". | Keep something alive: a reaction, a camera drift, the background moving. |
| 24 | film | F06 | 46.40-47.20 s (frames 1392-1416) | finale | The picture is frozen for 0.8 s (motion under 0.2) while the narration says "one.". | Keep something alive: a reaction, a camera drift, the background moving. |
| 25 | film | F12 | 47.11 s (frame 1413) | finale | finale event 6 ('or') has no sound starting at its time (planned: whoosh). | Add or retime its cue. |

## Measured

| Words | Film | Pace | Hook | Sentences (max / mean words) | Sources | 'you' | Numbers |
|---|---|---|---|---|---|---|---|
| 141 | 51.4 s | 164.6 wpm | 9 words, ends 2.52 s | 15 (21 / 9.4) | 4 | 10 | 1 |

| Scene | Length | Picture events planned | Shown in the film | Planned /s | Measured onsets /s | Median motion | Shot sizes (moves) |
|---|---|---|---|---|---|---|---|
| hook | 4.9 s | 5 (+3 text) | 3 / 5 | 1.02 | 1.64 | 5.55 | medium (tracks the fall), wide (pull back) |
| small | 12.4 s | 13 (+1 text) | 12 / 13 | 1.05 | 0.81 | 1.08 | wide (slow push in), wide (push in) |
| giant | 8.4 s | 8 (+3 text) | 7 / 8 | 0.95 | 2.98 | 6.29 | extreme-wide, extreme-wide (slow push in), medium (push in to the edge) |
| friend | 7.1 s | 7 (+1 text) | 6 / 7 | 0.99 | 0.57 | 0.4 | extreme-wide (slow drift) |
| inside | 6.9 s | 9 (+2 text) | 9 / 9 | 1.3 | 1.01 | 2.49 | wide (slow push in) |
| unknown | 4.8 s | 6 (+1 text) | 6 / 6 | 1.26 | 1.05 | 2.49 | wide (dive toward the centre), medium (ease back) |
| finale | 7.0 s | 7 (+3 text) | 7 / 7 | 1.0 | 1.28 | 0.16 | wide, extreme-wide (pull back) |

Plan: text share 0.2, anchored to words 0.87, sizes used extreme-wide, wide, medium, cue coverage 0.89, holds [(21.0, 23.0, 'the push-in to the event horizon: the lensed glow becomes broad smooth bands (REVIEW.md, accepted flat seconds 21-22)'), (48.0, 49.0, 'the breath before the title while the ship drifts (REVIEW.md, accepted flat second 48)')].

| Check | Measured |
|---|---|
| MP4 | 1080x1920 h264 yuv420p, 30.0 fps, 51.4 s, 32.7 MB |
| Loudness | -14.1 LUFS, true peak -1.7 dBTP, LRA 1.9 LU |
| Sync | 0.0 ms vs the stems |
| Motion | median 1.49; frozen runs (0.5 s+) [(32.0, 32.7), (44.5, 45.1), (46.4, 47.2), (49.4, 51.4)] |
| Empty frames | mean flat 60.7 %; seconds over 70 %: [21, 22, 48] |
| Picture onsets | 1.32 per second; dead stretches [(29.67, 31.2), (31.2, 32.73)] |
| Events shown | 0.909 of planned picture events at their time and place; acts shown 0.769 |
| Word lock | the same events moved 0.7-2.5 s are seen 0.441 of the time (p = 3.3e-13); big picture onsets 1.462x as frequent at planned times as elsewhere (p = 0.007) |
| Sound | cued events with a sound starting at their time 0.909 (shifted cues: 0.75, p = 0.005); largest group of identical cues 0.05 |
| Mix | voice over the bed 9.2 dB, music under the voice 15.1 dB, music present 0.98 |
| Captions | band [1152, 1224] px (correlation 0.319), follow 0.851 of words |
| HyperFrames | default: passed (0 errors, 0 warnings); dense: passed (0 errors, 0 warnings) |
| Seek test | 3.233 s: 1.47, 10.1 s: 1.45, 21.833 s: 1.13, 28.133 s: 1.49, 35.1 s: 1.46, 42.5 s: 1.48, 47.267 s: 1.48 (mean difference per frame) |

## The rules

Every rule id above is defined in `tools/reviewer/STANDARD.md` (thresholds in `tools/reviewer/standard.py`).
