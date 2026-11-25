# The standard

What the reviewer requires, why, and how stage 3 measures it. Every threshold lives in `standard.py` (`T`), every
rule in `standard.py` (`RULES`); `python tools/reviewer/review.py rules` prints the table below from the code.
**must** items block approval; **should** items are listed in the fix list and do not.

The numbers come from my three vertical films (`projects/ocean-glow-short`, `mitochondria-short`,
`black-hole-short`) and from damaged copies of them: see `calibration/README.md` for what each film measures, where
my own films fail, and how often the detectors fire at times where nothing was planned.

## Stage 1: the script

A Short that works here has a hook that lands in the first four seconds, one idea per short sentence, about 150
words a minute (my films: 146-165), the viewer addressed as "you", concrete numbers, a turn ("but", "or better"), a
short last line that calls back to the opening, a source for every claim, and no narration about the video itself.
Every sentence start is a sync point for the picture, so long sentences leave the picture without cues.

Before the voice exists, length and the hook's end are estimated at 3.2 words per second; once `assets/timing.json`
exists they are measured. S15 then checks that `align.py` heard the words rather than interpolating them, because
every picture and sound cue hangs on those times.

## Stage 2: the scenes (plan.json)

How I plan a film: something happens in the picture about once a second, on the word it illustrates; every sentence
is shown, not only captioned or labelled; the shot size changes; characters act instead of posing; every action has
its own sound. The plan format is in [PLAN.md](PLAN.md). Measured on my plan for the black hole film: 0.95-1.30
picture events per second per scene, 20 % text events, 87 % of events on words, three shot sizes, the lead acting
once per 4.0 s, 89 % of actions with a cue.

## Stage 3: the film

An agent cannot watch or listen, so everything here is measured from the MP4 and the three stems:

- **Specs, loudness, sync, black frames** (F01-F04) as `tools/verify_render.py`: ffprobe, ebur128 with true peak,
  cross-correlation of the MP4 audio with the stem sum, blackdetect, plus single-frame brightness flashes.
- **Captions** (F05): the rows of 24 px blocks whose change correlates with the word onsets are the caption band
  (my films: y 1128-1248). They are masked out of every picture measure, so captions can never count as picture, and
  must change on at least 70 % of the words.
- **Motion** (F06): mean absolute luma change between frames 0.1 s apart at frame_stats size (270 x 480), caption band
  excluded; the median over the film, and runs of frames under 0.2 before the voice ends.
- **Empty frames** (F07): exactly `tools/frame_stats.py`: each second's frame at s + 0.5, the share of 12 x 12 blocks
  with luma standard deviation under 3; a second over 70 % is mostly empty.
- **Picture onsets** (F08): on a grid of 24 px blocks at 15 fps, a block that changed less than a third as much
  during the previous 0.4 s and now changes by more than 5 levels starts something; 12 or more connected blocks
  make a big onset. Per scene, and the dead stretches between onsets while the narration runs.
- **Events seen** (F09): for each planned picture event, the mean change of the 12 px blocks in its `where` box over
  [t - 0.3, t + 0.5] s must reach 2.5 times the box's usual change (its median over +-4 s, leaving out every
  planned event in an overlapping box), with at least 4 blocks changing by more than 6 levels, and (for a box) at
  least twice the change in the rest of the frame in that same frame, so a camera move or a cut does not make every
  small event look seen. On the black hole plan: 91 % of planned events are seen, 14 % of times away from any event.
- **The word lock** (F10): the same test with every event moved 0.7-2.5 s (5 times each). Planned times must beat
  moved ones with binomial p at most 0.01 (black hole: 91 % against 44 %, p = 3e-13). As a should, the classic
  measure: big onsets 0.8-2 s from the planned times vs within -0.15..+0.35 s, against 400 randomly shifted plans.
- **Acting** (F11): the F09 test on act and react events, in the character's box.
- **Sound** (F12): an event has its sound when the effects stem's level, in 20 ms steps, rises at least 5 dB above
  1.5 kHz (or 8 dB over the whole band) within [t - 0.1, t + 0.45] s over its median in the 0.65 s before. 91 % of
  my cued events pass, 21 % of times away from any cue. The same coverage with every cue moved 0.7-2.5 s must be
  clearly lower (200 shifts, p at most 0.10). Each sound is fingerprinted (32 log-spaced bands from 60 Hz to 16 kHz
  plus an 8-step envelope); sounds with cosine similarity of 0.985 or more are the same sound, and the largest group
  may hold at most 60 % of the cues (my films: 5-7 %; one stock pop: 95 %).
- **Mix** (F13): RMS of the voice stem while words are spoken against the effects plus music, and the music alone.
- **HyperFrames** (F14): `npx hyperframes@0.9.56 check` in the project, default and `--samples=150`.
- **Seek test** (F15): fresh HyperFrames snapshots at one event per scene compared with the MP4's frames; a
  difference means some state depends on the order frames are rendered (docs/09-pitfalls.md).

Holds (`plan.json`) exempt stillness, empty frames, black and saturation inside them; the seconds after the last word
are exempt from the frozen-picture checks.

## The rules

| Rule | Level | Requirement |
|---|---|---|
| S01 | must | film.json has lines (text + pause) and scenes that cover every line once, in order |
| S02 | must | SCRIPT.md has accuracy notes and at least max(3, lines/2) unique source links |
| S03 | must | film length 20-60 s (should: 40-58 s) |
| S04 | must | pace 115-190 words per minute of film (should: 130-175) |
| S05 | must | the hook: first sentence at most 14 words and over within 4.5 s; should ask a question, speak to 'you' or state a number |
| S06 | must | no sentence over 26 words (should: 20; mean 14) |
| S07 | must | no generic filler ('in this video', 'let's dive in', 'delve' ...); should avoid cliches |
| S08 | should | talk to the viewer: 'you'/'your' at least 3 times |
| S09 | should | at least 2 concrete numbers or comparisons |
| S10 | should | a turn ('but', 'yet', 'or better' ...) so the story has tension |
| S11 | should | a short last line (16 words or fewer) with a callback to an earlier line, and a 2 s tail for the title |
| S12 | must | pauses 0-1.5 s, none after the last line (should: 0.3-0.9 s) |
| S13 | must | scenes 2-16 s (should: 3-13 s, 4-10 scenes) |
| S14 | should | long technical words are introduced ('called', 'this is', 'known as') |
| S15 | must | align.py heard at least 97 % of the script words |
| P01 | must | plan.json exists and lists every film.json scene, in order |
| P02 | must | every event and shot is anchored to a word spoken in its scene (or a time inside it) |
| P03 | must | every event has a known kind; picture events say what happens and where on screen (a box or a region; cameras and cuts excepted); acts/reacts name who |
| P04 | must | picture events per scene at least 1 per 2.5 s and 2 per scene (should: 1 per 1.5 s) |
| P05 | must | no stretch of narration over 3 s without a picture event (should: 2 s), except declared holds |
| P06 | must | every sentence has a picture event on one of its words (or placed by time just before it; a cut alone does not count); long sentences (12+ words) two |
| P07 | must | text events (labels, titles) at most 50 % (should: 35 %); no sentence carried only by text |
| P08 | must | 85 % of events anchored to a word and within 0.6 s of it (before its start or after its end); free events only in pauses |
| P09 | must | shot plan: 3+ shot sizes; no 3 scenes in a row at one size without a camera move; scenes over 6 s change size or move (should) |
| P10 | must | characters act: everyone in a scene's cast acts or reacts in it (not only pose verbs); the lead acts at least once per 4.5 s on screen (should: per 3 s) |
| P11 | must | 85 % of picture events other than reactions have a sound cue; no cue name on more than 40 % of the cued events (should: 50 % distinct names) |
| P12 | should | every scene after the first says how it begins (transition) |
| P13 | must | a picture event in the first 1.0 s of the film (should: within 0.8 s of every scene start) |
| P14 | should | the last scene has a title held at least 2 s |
| P15 | should | the plan matches the code: event words appear as at("word") in the scene file, cue words in sfx_cues.py |
| P16 | must | declared holds have from/to/why and total at most 25 % of the film (should: 6 s while speaking) |
| F01 | must | MP4 specs: H.264 yuv420p, AAC 48 kHz, size, fps, duration and frame count match the film |
| F02 | must | loudness -14 +/- 1 LUFS integrated, true peak at most -1 dBTP |
| F03 | must | the three stems exist and the MP4 audio is within 20 ms of them |
| F04 | must | no black stretches or flash frames outside declared holds |
| F05 | must | captions are burned in and follow the words (when film.json asks for captions) |
| F06 | must | motion: median at least 0.8 (should 1.2); no frozen run of 1 s or more before the voice ends (should: 0.6 s) |
| F07 | must | empty frames: no run of 2 s or more over 70 % flat outside holds; at most 15 % of seconds (should 8 %) |
| F08 | must | every scene shows at least 0.5 picture onsets per second (should 0.8); no dead stretch of 2.5 s (should 1.5 s) |
| F09 | must | 80 % of planned picture events visibly happen at their time and in their box (the change there is 2.5x the box's usual change between events) |
| F10 | must | the picture is locked to the words: planned events are seen at their times far more often than when moved 0.7-2.5 s (p at most 0.01); should: the film's big changes cluster at the planned times (1.15x, p 0.10) |
| F11 | must | characters act: 70 % of act/react events visibly happen inside their box, and in every scene each character shows at least one of its acts |
| F12 | must | 75 % of cued picture events have a sound starting at their time (should 85 %), clearly more than at shifted times (p at most 0.10); no single sound on more than 60 % of them (should 40 %) |
| F13 | must | mix: voice at least 5 dB over the bed while speaking (should 7), music at least 9 dB under the voice, music present |
| F14 | must | HyperFrames check: 0 errors and 0 warnings, default run and a 150-sample layout scan |
| F15 | must | seek test: fresh snapshots match the MP4 frames (no order-dependent state) |
| F16 | should | very saturated bright pixels at most 7 % per second outside declared holds |

## Changing the standard

Change a number in `standard.py`, run `python tools/reviewer/selftest.py` (every damaged copy must still be
rejected) and the calibration reviews in `calibration/README.md`, and record why. Any change to the reviewer's code
or rules changes its hash, so earlier approvals stop verifying and films must be reviewed again.

The reviewer also checks itself: it refuses to approve (reported as a must item with rule id REVIEWER) and
`verify` refuses the stamp when its own hash differs from the hash published in `README.md` (see "The published
reviewer hash"). To publish a changed reviewer, record the new hash there with the reason — and know that every
earlier approval stops verifying.
