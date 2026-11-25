# Finish notes — 2026-11-25

The reviewer as Opus left it in Kiro (branch `film-reviewer`, commit `b390474`) was working but unfinished.
This is what the finish changed, what was validated, and what is still open. Reviewer version 1.0.
Published reviewer hash after the finish: `02a7edf15391b564cec2eb2ee2cb2e87abc9c4db62f17aabe3561706f0cef0a6`
(recorded in `README.md`, "The published reviewer hash").

## What changed

1. **F14 fix (`film_check.py`).** HyperFrames prints "Check passed" even when it lists warnings, and the
   reviewer recorded `passed: true` while raising an F14 must for the same check — the record lied. `passed`
   now means what F14 requires: "Check passed" in the output **and** 0 errors **and** 0 warnings. The F14 must
   is now raised on `not passed` instead of on `errors or warnings` (the same condition, stated once). This is
   the fix Opus flagged himself ("`passed` counts even with warnings but my F14 rule requires zero warnings to
   be a true checkmark"). No threshold changed: F14 still requires 0 errors and 0 warnings.
   **Follow-up fix, same file:** `ran` first followed the new `passed`, so a warnings-only check ("Check
   passed" with warnings) was misreported as "did not run" and its findings hidden. `ran` is now independent:
   the check ran if HyperFrames reached a verdict either way ("Check passed" or "Check failed" in the output);
   only a missing verdict means it did not run. Caught during the finish's own review of the first fix, before
   commit. Verified by a direct unit test of the real `hyperframes()` method with canned outputs (clean,
   warnings-only, errors, no verdict — all four give the right `ran`/`passed`/counts); it changed no measured
   number in the calibration reruns, because every fresh check on this machine carries an error and `ran` was
   true either way. The published hash changed once for this fix (`0a563bdd6b24` → `02a7edf15391`); both hashes
   are recorded in `README.md` with their reasons.
2. **Published reviewer hash (`common.py`, `review.py`, `README.md`, `STANDARD.md`).** The loophole Opus noted:
   a maker who edits the reviewer's code or thresholds before a review gets a `reviewer_hash` that just reflects
   the modified code. The expected hash is now published in `README.md` (`common.published_hash()` reads it;
   the hash covers only the top-level `*.py` files, so the README line is not part of the hash). `review.py`
   refuses to approve when its own hash differs from the published one (reported as a must item with rule id
   `REVIEWER`, which withholds `APPROVED.json`), and `verify` refuses such a stamp. The only way to get an
   approval from changed code is to also change the published hash line — a visible, deliberate edit in git
   history that invalidates every earlier approval (their stamps record the old hash). See "The published
   reviewer hash" in `README.md`.
3. **`calibration/README.md`** (new). The measured-numbers table from the calibration runs, the round-1
   comparison, where the reviewer is weak, and the environment caveats. Referenced by `README.md` and
   `STANDARD.md`; it did not exist before.
4. **This file.** The validation record for the finish.

## What did NOT change

- **No rule or threshold changed.** F11/P10 (acting) stay as Opus wrote them, even though his own black-hole
  film fails on them (2 musts in round 1). No rule added, none removed, no number in `standard.py` touched.
  The only `standard.py` value touched anywhere in validation was in a throwaway copy under `/tmp` for the
  negative test (see below), never in the repo.
- No film changed. No pull request created. No other branch touched. The finish lives on `film-reviewer` only.

## Validation (all run on the finish machine, 2026-11-25)

- **`review.py --help`**: works. A script-stage run on black-hole-short passes (0 must, 2 should).
- **Self-test** (`python tools/reviewer/selftest.py`): **10/10 pass**, exit 0 (~12 min), run twice — once under
  the intermediate hash and once under the final hash `02a7edf15391`. Every damaged copy
  (generic opening, labels instead of picture, posing, slideshow, captions only, picture late, wrong event
  times, one pop for all sounds, no effects, random hits) was rejected on the rules that describe the damage.
  The undamaged copy was rejected on F11/P10, as in round 1.
- **Calibration reruns** (full three-stage reviews, `--plan calibration/<film>.plan.json`, results overwritten in
  `calibration/results/<film>/`): black-hole 4 must / 25 should (round 4), mitochondria 13 must / 37 should
  (round 3), ocean 16 must / 39 should (round 3), all under the final hash `02a7edf15391`. All REJECTED, as in
  round 1. The numbers were measured twice under the finish (intermediate hash, then final hash) and are
  identical between the two passes. Deltas vs round 1 are explained in `calibration/README.md`: F14
  musts from headless Chrome being unable to load Google Fonts on this machine (environmental, not the films),
  and one borderline act in mitochondria flipping between machines. Film measures otherwise agree with round 1.
- **TODO placeholder check (P03):** verified by running `draft-plan` on black-hole-short and reviewing the raw
  draft — 125 P03 must items, verdict REJECTED. The draft's TODOs are caught and block approval. Opus had
  already fixed this before the commit; the finish verified it works.
- **`norm_cue`:** verified by direct test — `pop (low)` → `pop`, `whoosh (small)` → `whoosh`, `small pop` →
  `pop`. Qualifiers in the list are stripped; a qualifier outside the list (e.g. `rising`) is kept, which can
  only cause a false must, never a false pass. Opus's fix was already in the pulled code; left as is.
- **Approval path (partial).** Opus demonstrated the full path in Kiro (stamp 2026-11-25 07:22:42, reviewer
  1.0). It could **not** be reproduced end to end on this machine, and the reason is the tool working, not a
  defect: with the font issue worked around (local fonts in a `/tmp` copy — HyperFrames then runs clean, no F14
  musts), black-hole still honestly fails on F11/P10: the astronaut never acts on its hook words (the face is a
  fixed drawing; the tumble is continuous, so `event_check` finds no onset at the word times), and the plan
  rules then fail too (P10 lead frequency, P07 sentence coverage). Approving would need either re-rendering the
  film or gaming the plan, both out of scope for the finish. No `APPROVED.json` was produced on this machine,
  and none is claimed.
- **Negative test (tampered reviewer, `/tmp` copy only, re-run under the final hash).** A copy with
  `acts_shown_must` weakened 0.70 → 0.0 (hash `a283ffa09a39` vs published `02a7edf15391`):
  - `review.py script` with the tampered copy: REJECTED with exactly 1 must, the REVIEWER must ("The reviewer
    is not the published reviewer"). The tampered reviewer cannot approve anything.
  - `verify` with the tampered copy, on a stamp fabricated with the tampered hash and correct file hashes:
    `APPROVAL INVALID: the reviewer is not the published reviewer (its hash is a283ffa09a39, published
    02a7edf15391); approvals from modified code do not count`, exit 1. The published-hash check is the only
    failing check in that run.
  - The real reviewer on the same stamp: `APPROVAL INVALID: the reviewer's code or rules changed since this
    approval ...; tools/reviewer has uncommitted code changes`, exit 1 (the uncommitted-changes item is the
    finish work itself, before commit).

## Environment notes (finish machine)

- Python 3.12.3, numpy 1.26.4, scipy 1.11.4, Pillow, ffmpeg/ffprobe, Node 24, `npx hyperframes@0.9.56`.
- **F14 / Google Fonts:** headless Chrome (as launched by HyperFrames) cannot load `fonts.googleapis.com/css2`
  through this machine's egress proxy (`net::ERR_TUNNEL_CONNECTION_FAILED`), while `curl` on the same machine
  returns 200 for the same URL. Every HyperFrames check on this machine therefore carries 1 environmental error,
  and dense-run overflow findings can be downstream of the missing font (fallback font is wider). F14 results
  measured here are not comparable with Kiro's. The film measures are unaffected. A `/tmp` copy with the fonts
  downloaded locally and the `<link>` replaced by local `@font-face` rules runs HyperFrames clean, which
  confirms the cause.
- A full three-stage review takes ~8 minutes per film on this machine (the self-test ~12 minutes).

## Still open (not part of this finish)

- No real film passes approval; the standard has never approved a film end to end outside Kiro.
- No live auto-loop (reviewer → FIXLIST → maker fixes → re-run is still manual).
- The two-AI same-topic test (my film vs Opus's film on one topic, both reviewed) was never run.
- The F14 environment issue above: if calibration is re-run here, expect the same environmental F14 musts.
- `calibration/results/black-hole-short/history.md` round 2 (2026-11-25T08:52:06) was run during the finish
  without the `--plan` argument, so it reviewed the film with no plan (P01, 6 must / 9 should). It was re-run
  correctly as round 3. The history is append-only and was left as is.
