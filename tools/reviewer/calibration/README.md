# Calibration

What the reviewer measured on my three films, and where it is weak. The point of calibration is not to make
the reviewer pass my films: it is to know what the numbers look like on films I consider done, so a new film's
numbers mean something. All three films are **REJECTED**. That is deliberate: the standard is stricter than my
films, and I refused to weaken it (see "Changing the standard" in [STANDARD.md](../STANDARD.md)).

## How it was run

The films were built from scene code, not from a plan, so the projects have no `plan.json`. The plans used here
were drafted from the scene code (`review.py draft-plan`) and then filled in by hand; they live next to this file
as `<film>.plan.json`. The films themselves were not changed for calibration.

```bash
cd tools/reviewer
python review.py film ../../projects/black-hole-short   --plan calibration/black-hole-short.plan.json   --out calibration/results/black-hole-short
python review.py film ../../projects/mitochondria-short --plan calibration/mitochondria-short.plan.json --out calibration/results/mitochondria-short
python review.py film ../../projects/ocean-glow-short   --plan calibration/ocean-glow-short.plan.json   --out calibration/results/ocean-glow-short
```

Full three-stage reviews (not `--quick`): script, plan, film, including the HyperFrames check (default and 150
layout samples) and the seek test. `results/<film>/` holds the full output of the latest round (`review.json`,
`FIXLIST.md`, `EVENTS.md`, `sheets/`, `history.md`).

Round 1 ran 2026-11-25 in the Kiro sandbox with reviewer `236bd2dbfad4`. The fresh numbers below ran
2026-11-25 on the finish machine with the published reviewer `02a7edf15391` — black-hole round 4, mitochondria
round 3, ocean round 3. The films and plans did not change between rounds; the MP4 hashes are the same. (An
intermediate published hash, `0a563bdd6b24`, covered the first finish pass; it was superseded the same day by the
F14 `ran` fix — a warnings-only check still ran — which changed no measured number: every fresh check on this
machine carries an error, so `ran` was true either way. The numbers below were re-measured under the final hash
and are identical to the intermediate pass.)

## Results

| | black-hole-short | mitochondria-short | ocean-glow-short |
|---|---|---|---|
| Film | `renders/black-hole-v3.mp4` | `renders/mitochondria-v2.mp4` | `renders/ocean-glow-v3.mp4` |
| Duration | 51.4 s | 50.6 s | 54.2 s |
| Verdict (latest round) | REJECTED | REJECTED | REJECTED |
| Must / should (latest) | 4 / 25 | 13 / 37 | 16 / 39 |
| Must / should (round 1) | 2 / 25 | 9 / 36 | 15 / 39 |
| Must by rule (latest) | P10 1, F11 1, F14 2 | P08 1, P09 1, P10 1, P11 2, P13 1, F09 1, F10 1, F11 3, F14 2 | P08 2, P09 1, P11 2, F07 8, F09 1, F14 2 |
| Script: words / pace | 141 words, 164.6 wpm | 125 words, 148.2 wpm | 132 words, 146.1 wpm |
| Script: hook | 9 words, over by 2.52 s | 8 words, over by 2.52 s | 14 words, over by 3.66 s |
| Script: sources | 4 | 11 | 12 |
| Plan: events | 69 | 73 | 81 |
| Plan: text share / anchored / sfx cover | 0.20 / 0.87 / 0.89 | 0.26 / 0.85 / 0.67 | 0.22 / 0.83 / 0.56 |
| Film: median motion | 1.49 | 2.90 | 1.42 |
| Film: events shown (shifted) | 0.909 (0.437) | 0.574 (0.465) | 0.714 (0.518) |
| Film: event word-lock p | 2.3e-13 | 0.07 | 0.0012 |
| Film: lock ratio | 1.49 | 1.14 | 1.43 |
| Film: cue cover (cue lock p) | 0.909 (0.005) | 0.946 (0.045) | 0.914 (0.005) |
| Film: acts shown | 0.769 | 0.60 | — (no acts in plan) |
| Film: loudness / true peak | −14.1 LUFS / −1.7 dBFS | −14.0 LUFS / −1.6 dBFS | −14.0 LUFS / −1.6 dBFS |
| Film: audio sync | 0.0 ms | 0.0 ms | 0.0 ms |
| HyperFrames default | ran, **not passed**: 1 error, 0 warnings | ran, **not passed**: 1 error, 1 warning | ran, **not passed**: 1 error, 0 warnings |
| HyperFrames dense (150 samples) | ran, **not passed**: 2 errors, 3 warnings | ran, **not passed**: 2 errors, 3 warnings | ran, **not passed**: 1 error, 17 warnings |

## Why the latest round has more musts than round 1

Two causes, neither is a rule change (no rule or threshold changed between rounds):

1. **F14 on this machine (all three films, +2/+2/+1 musts).** The HyperFrames check loads each film's page in
   headless Chrome, and on this machine Chrome cannot load the Google Fonts stylesheet (`css2`):
   `request_failed: Failed to load css2: net::ERR_TUNNEL_CONNECTION_FAILED`. The same URL returns 200 from
   `curl` on the same machine, so it is Chrome/proxy-specific, not the film and not the network. Every check on
   this machine therefore carries 1 environmental error. The dense-run overflow findings (black-hole and
   mitochondria: text/canvas overflow in the finale) are downstream of the same failure: with the font missing,
   the fallback font is wider and the big title text overflows. In round 1 (Kiro) the font loaded, both checks
   ran clean except ocean's dense run, which had 17 warnings. **F14 musts measured on this machine are not
   comparable with round 1's; the film measures (motion, events, sound) are unaffected and agree with round 1.**
2. **One borderline act in mitochondria (F11 1 → 3, acts 0.60 vs 0.80).** The acts check is a frame-difference
   measurement with a threshold; one act sits on the threshold and flips between machines (different ffmpeg /
   decoder builds give slightly different pixel values). The shifted-time comparisons are seeded, so this is
   cross-machine measurement noise, not a code change. Treat acts near the threshold as "check by eye", not as a
   certain fail.

Black-hole's `history.md` has a round 2 (2026-11-25T08:52:06, 6 must / 9 should) that was run **without** the
calibration plan — the plan argument was left off by mistake during the finish work, so the film was reviewed with
no plan (P01 must, no events). It was re-run correctly as rounds 3 and 4. The history is append-only and was left
as it is; round 4 is the valid number.

## Where the reviewer is weak (what calibration showed)

- **Acting (F11/P10) is the sharpest rule, and it bites my own films.** Black-hole fails it on the hook
  astronaut (2 planned acts, neither shows in its box); mitochondria fails it on the bacterium in `origin`. The
  plan-level P10 (characters that pose instead of act) fires on all three films. If a film is going to fail, this
  is the most likely reason — and it is the rule I most wanted to keep strict.
- **Plan coverage (P08/P09/P11).** Ocean's plan has the weakest sound cover (0.56) and the most plan musts;
  mitochondria's is 0.67. The reviewer is strict about every action having a sound and every sentence being shown
  in the picture, not just captioned.
- **Empty background (F07).** Ocean has 8 F07 musts — long stretches that are mostly flat background. The film
  reads as good to the eye, which means either the film leans on glow that the flatness measure does not see, or
  the measure is right and the film is emptier than it looks. That is an open question, not a verdict.
- **F14 (HyperFrames) is the noisiest check.** Besides the font-loading environment issue above, the dense run's
  layout findings depend on which 150 samples are drawn. Treat a single dense-run warning as a hint to look at
  the frame, not as a proven fault.
- **What it cannot judge** is in the main README: whether an event that visibly happens on its word shows the
  *right* thing, whether a drawing is beautiful or on style, whether the science is right beyond the presence of
  sources, or how the voice and music sound. Calibration does not change that. Look at `sheets/` and listen before
  calling a film done.

## Self-test

`python tools/reviewer/selftest.py` damages a copy of black-hole-short in 10 known ways (generic opening, labels
instead of picture, posing, slideshow, captions only, picture late, wrong event times, one pop for all sounds, no
effects, random hits) and requires each damaged copy to be rejected on the rules that describe the damage. It
passed 10/10 on the finish machine (2026-11-25, reviewer `02a7edf15391`), with the undamaged copy rejected on
F11/P10 as in round 1. See [FINISH-NOTES.md](FINISH-NOTES.md) for the full validation record.
