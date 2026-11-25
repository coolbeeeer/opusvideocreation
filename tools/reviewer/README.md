# Film reviewer

A reviewer for films made with this repo's pipeline. It checks a film the way I check my own before I call it
done, at three stages, and writes a fix list. It keeps rejecting the film until nothing in the list is a **must**;
then it approves the film and records exactly which files it approved. Any AI (or person) making a film follows the
loop below and delivers only an approved film.

```bash
python tools/reviewer/review.py script projects/<film>      # stage 1: the script (film.json, SCRIPT.md)
python tools/reviewer/review.py plan   projects/<film>      # stages 1-2: + the event list and shot plan (plan.json)
python tools/reviewer/review.py film   projects/<film>      # stages 1-3: + the MP4, the stems, HyperFrames
python tools/reviewer/review.py verify projects/<film>      # is the approval still valid for these exact files?
python tools/reviewer/review.py draft-plan projects/<film>  # plan.draft.json from an existing film's scene code
python tools/reviewer/review.py rules                       # the standard as a table
python tools/reviewer/selftest.py                           # damage a copy of a film in 10 ways; each must be rejected
```

Options: `--plan FILE` (default `<film>/plan.json`), `--mp4 FILE` (default the newest `renders/*.mp4`),
`--out DIR` (default `<film>/reviewer/`), `--quick` (skips the HyperFrames check and the seek test: about 15 s
instead of 2 min, and never approves), `--no-sheets`. Exit code 0 = approved (or the stages asked for passed),
1 = rejected, 2 = cannot run. The reviewer only reads the film's files; it writes into its output folder only.

Needs: Python with `numpy`, `scipy` (and `pillow` for labelled sheets), FFmpeg and FFprobe (on PATH or in
`HYPERFRAMES_FFMPEG_PATH` / `HYPERFRAMES_FFPROBE_PATH`), and for full reviews Node with `npx hyperframes@0.9.56`
(docs/01-environment.md).

## The loop (for the AI making the film)

1. **Script.** Write `film.json` and `SCRIPT.md` (narration, shot table, accuracy notes with sources). Run
   `review.py script`. Fix every must item, rerun until stage 1 passes. Only then record the voice.
2. **Voice and timing.** `python vo.py && python align.py && python build.py`. Rerun `review.py script`: with the
   measured voice it checks the real length, pace and hook time, and that the aligner heard the words.
3. **Plan.** Write `plan.json` ([PLAN.md](PLAN.md)): every picture event on its word, with where, who and its
   sound; the shots; the cast. Run `review.py plan` until stage 2 passes. Only then build scenes.
4. **Build and render** the scenes and the sound exactly as planned, using the same word anchors
   (`at("word") + offset` in the scene, `a(scene, word) + offset` in `audio/sfx_cues.py`). Render the MP4.
5. **Film.** Run `review.py film --quick` while fixing (fast), then `review.py film` (full) for the verdict. Every
   must item gives the time, the frame number, what was measured and what to change. `sheets/` shows the frames.
   Fix, re-render, review again. Repeat until the verdict is **APPROVED**. Do not edit the plan to make the film
   pass: change the film so it does what the plan says (or change both, honestly, and pass stage 2 again).
6. **Deliver.** Run `review.py verify` (it must say APPROVED with every file unchanged). Send the MP4 together
   with `reviewer/APPROVED.json`, `reviewer/FIXLIST.md` (the should items left) and `reviewer/history.md` (every
   round). A film without a valid approval is not final.

Each round appends a line to `history.md`. A new review that does not approve deletes the old `APPROVED.json`,
so an approval always belongs to the last review. `APPROVED.json` holds the SHA-256 of `film.json`, `SCRIPT.md`,
`plan.json`, `timing.json`, the three stems and the MP4, plus a hash of the reviewer's own code and thresholds:
`verify` fails if any of them changed, so neither the film nor the rules can be swapped after approval.

## What it writes

| File | What it is |
|---|---|
| `FIXLIST.md` | The verdict, every **must** item (blocks approval) and **should** item (listed, does not block), with time, frame, scene, the problem as measured and the fix; then a table of measurements. This is the file to hand to the film maker. |
| `EVENTS.md` | Every planned picture event: time, word, kind, who, what it should show; whether it was seen, its score and lag; its sound and when the sound starts. |
| `sheets/events-<scene>.jpg` | For each event, the frames 0.4 s before its time, 0.15 s after and 0.6 s after, its box drawn, SEEN / NOT SEEN, cue ok / MISSING. `flags.jpg`: the frames at every film-stage must item. |
| `review.json` | Everything above as numbers. |
| `history.md` | One line per review round: stages, verdict, must counts per stage, should count, the MP4's hash. |
| `APPROVED.json` | Only when nothing must be fixed in a full three-stage review. |

## The published reviewer hash

The reviewer checks itself: an approval only counts from the reviewer whose code hashes to the value published
here. `common.reviewer_hash()` hashes the reviewer's top-level `.py` files; `common.published_hash()` reads the
line below. When the two differ, `review` reports a must item with rule id REVIEWER and withholds
`APPROVED.json`, and `verify` refuses the stamp. A maker who edits the reviewer's code or thresholds before a
review changes its hash, so the published hash no longer matches. The only way to get an approval from changed
code is to also change this line — a visible, deliberate edit in git history that invalidates every earlier
approval (their stamps record the old hash).

Published reviewer hash: 02a7edf15391b564cec2eb2ee2cb2e87abc9c4db62f17aabe3561706f0cef0a6

Record the reason for every hash change here:

| Date | Hash (first 12) | Reason |
| ---- | --------------- | ------ |
| 2026-11-25 | 0a563bdd6b24 | Finish work: F14 fix (`passed` needs 0 warnings), published-hash self-check in `review.py` and `common.py`, calibration README. Rules and thresholds unchanged. |
| 2026-11-25 | 02a7edf15391 | F14 `ran` fix: a warnings-only check still ran (previously misreported as "did not run" because `ran` followed the new `passed`). Rules and thresholds unchanged. |

## What it checks

The rules, their thresholds and why are in [STANDARD.md](STANDARD.md). In short:

- **Stage 1, the script:** length 20-60 s, about 150 words a minute, a hook of at most 14 words that is over by
  4.5 s, short sentences, no generic narration ("in this video", "let's dive in"), the viewer as "you", numbers, a
  turn, a short last line that calls back, pauses, scene lengths, sources for every claim, the voice heard.
- **Stage 2, the scenes (plan):** picture events at least one per 2.5 s in every scene (my films: about one per
  second), every sentence shown in the picture rather than only captioned or labelled, no 3 s of narration without
  a picture event, events on words, characters that act rather than pose, a sound for every action, three or more
  shot sizes and no run of same-size static scenes, the film opening on motion, a held title.
- **Stage 3, the film:** the MP4's specs, loudness and sync; captions burned in and following the words; motion
  (median and frozen runs); empty frames (tools/frame_stats.py's measure); picture onsets per scene and dead
  stretches; every planned event visibly changing its box at its time, far more often than at shifted times (the
  word lock); characters' acts visible in their boxes; a sound starting at every cued event, tied to the events,
  and not one stock sound; the mix; the HyperFrames check (default and 150 layout samples); the seek test (fresh
  snapshots match the MP4).

## What it cannot judge

It measures change, timing, sound and layout; it does not understand the picture. It cannot tell whether an event
that visibly happens on its word shows the *right* thing (a fish where the plan says a fish), whether a drawing is
beautiful or on style, whether the science is right beyond the presence of sources, or how the voice and music sound.
It trusts the plan's cast: a posing character left out of `cast` is not checked (the sheets show it). Look at
`sheets/` for every scene and listen to the film before calling it done; `calibration/README.md` lists what it
measured on my three films and where it is weak.
