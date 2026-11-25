"""The film reviewer: checks a film at three stages and writes a fix list. A film is final only when it approves it.

    python tools/reviewer/review.py script <project>        stage 1: the script (film.json, SCRIPT.md)
    python tools/reviewer/review.py plan <project>          stages 1-2: + the event list and shot plan (plan.json)
    python tools/reviewer/review.py film <project>          stages 1-3: + the rendered MP4, the stems, HyperFrames
    python tools/reviewer/review.py verify <project>        is the approval still valid for these exact files?
    python tools/reviewer/review.py draft-plan <project>    write plan.draft.json from an existing film's code
    python tools/reviewer/review.py rules                   print the standard

Options: --plan FILE (default <project>/plan.json), --mp4 FILE (default the newest renders/*.mp4),
--out DIR (default <project>/reviewer), --quick (skip HyperFrames and the seek test; never approves),
--no-sheets.

Writes into the output folder: FIXLIST.md (hand it to the film maker), EVENTS.md (every planned event and what was
measured), review.json (all numbers), sheets/ (frames of every event), history.md (one line per review), and
APPROVED.json only when nothing must be fixed. Exit code 0 = approved (or the requested stages passed),
1 = rejected, 2 = cannot run. The reviewer never changes the film.
"""
import argparse
import datetime
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import film_check  # noqa: E402
import plan_check  # noqa: E402
import script_check  # noqa: E402
from common import VERSION, Issues, Project, fmt_span, reviewer_hash, sha256  # noqa: E402
from standard import KINDS_PICTURE, RULES, rules_table  # noqa: E402

STAGES = ["script", "plan", "film"]
STAGE_NAME = {"script": "1 script", "plan": "2 scenes (plan)", "film": "3 film"}


def esc(s):
    return str(s).replace("|", "/").replace("\n", " ")


def write_report(P, out, issues, ms, stages, verdict, mp4, quick, rnd):
    must = [i for i in issues if i.level == "must"]
    should = [i for i in issues if i.level == "should"]
    order = {s: k for k, s in enumerate(STAGES)}
    keyf = lambda i: (order[i.stage], i.t0 if i.t0 is not None else -1, i.rule)
    must.sort(key=keyf)
    should.sort(key=keyf)
    fps = P.fps
    st_line = " / ".join(
        f"{STAGE_NAME[s]}: " + ("not run" if s not in stages else ("PASSED" if not any(i.stage == s and i.level == "must" for i in issues) else f"REJECTED ({sum(1 for i in must if i.stage == s)} must)"))
        for s in STAGES)
    L = [f"# Film review: {P.name}: {verdict}", ""]
    L.append(f"Reviewed {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} by tools/reviewer {VERSION} (reviewer hash {reviewer_hash()[:12]}), round {rnd}.")
    if mp4:
        L.append(f"Film: `{os.path.relpath(mp4, P.root)}`, plan: `{os.path.relpath(P.plan_path, P.root)}`.")
    L += ["", f"Stages: {st_line}.", ""]
    if quick and "film" in stages:
        L += ["**Quick review:** HyperFrames and the seek test were skipped, so this review cannot approve the film.", ""]
    if verdict == "APPROVED":
        L += ["Nothing must be fixed. `APPROVED.json` records the exact files that were approved; "
              "`python tools/reviewer/review.py verify <project>` checks them before delivery.", ""]
    else:
        L += ["## What to do", "",
              "Fix every **must** item below, then review again: `python tools/reviewer/review.py film <project> --quick` while fixing,",
              "and without `--quick` for the verdict (only a full review can approve). The film is approved only when no must item is left.",
              "Each item says what was measured and what to change; times are film seconds with the frame number. `sheets/` shows the",
              "frames of every event and flagged moment, `EVENTS.md` what was measured for every planned event. Change the film to do what",
              "the plan says; do not weaken the plan to match the film. Rules: `tools/reviewer/STANDARD.md`.", ""]
    for title, rows in (("Must fix", must), ("Should fix", should)):
        L.append(f"## {title} ({len(rows)})")
        L.append("")
        if not rows:
            L += ["None.", ""]
            continue
        L.append("| # | Stage | Rule | Time | Scene | Problem | Fix |")
        L.append("|---|---|---|---|---|---|---|")
        for k, i in enumerate(rows, 1):
            L.append(f"| {k} | {i.stage} | {i.rule} | {fmt_span(i.t0, i.t1, fps)} | {esc(i.scene)} | {esc(i.problem)} | {esc(i.fix)} |")
        L.append("")
    L += measured_section(P, ms)
    L += ["## The rules", "", "Every rule id above is defined in `tools/reviewer/STANDARD.md` (thresholds in `tools/reviewer/standard.py`).", ""]
    (out / "FIXLIST.md").write_text("\n".join(L))


def measured_section(P, ms):
    L = ["## Measured", ""]
    s = ms.get("script") or {}
    if s:
        L.append("| Words | Film | Pace | Hook | Sentences (max / mean words) | Sources | 'you' | Numbers |")
        L.append("|---|---|---|---|---|---|---|---|")
        L.append(f"| {s.get('words')} | {s.get('film_s')} s{'' if s.get('measured') else ' (est.)'} | {s.get('wpm')} wpm | {s.get('hook_words')} words, ends {s.get('hook_end_s')} s | "
                 f"{s.get('sentences')} ({s.get('sentence_max')} / {s.get('sentence_mean')}) | {s.get('sources', '-')} | {s.get('you')} | {s.get('numbers')} |")
        L.append("")
    p = ms.get("plan") or {}
    f = ms.get("film") or {}
    if p.get("scenes") or f.get("scenes"):
        L.append("| Scene | Length | Picture events planned | Shown in the film | Planned /s | Measured onsets /s | Median motion | Shot sizes (moves) |")
        L.append("|---|---|---|---|---|---|---|---|")
        evs = f.get("events") or []
        for sc in P.scenes:
            ps = (p.get("scenes") or {}).get(sc["id"], {})
            fs = (f.get("scenes") or {}).get(sc["id"], {})
            e = [x for x in evs if x["scene"] == sc["id"]]
            shown = f"{sum(1 for x in e if x['shown'])} / {len(e)}" if e else "-"
            sizes = ", ".join(f"{a}" + (f" ({b})" if b not in ("static", "none", "") else "") for a, b in zip(ps.get("sizes", []), ps.get("moves", []))) or "-"
            L.append(f"| {sc['id']} | {sc['dur']:.1f} s | {ps.get('picture_events', '-')} (+{ps.get('text_events', 0)} text) | {shown} | {ps.get('rate', '-')} | {fs.get('onset_rate', '-')} | {fs.get('median_motion', '-')} | {sizes} |")
        L.append("")
    if p:
        L.append(f"Plan: text share {p.get('text_share', '-')}, anchored to words {p.get('anchored_share', '-')}, sizes used {', '.join(p.get('distinct_sizes', [])) or '-'}, "
                 f"cue coverage {p.get('sfx_cover', '-')}, holds {[(round(a, 2), round(b, 2), w) for a, b, w in p.get('holds', [])]}.")
        L.append("")
    if f:
        lo = f.get("loudness") or {}
        sp = f.get("specs") or {}
        v = sp.get("video") or {}
        L.append("| Check | Measured |")
        L.append("|---|---|")
        L.append(f"| MP4 | {v.get('width')}x{v.get('height')} {v.get('codec_name')} {v.get('pix_fmt')}, {sp.get('fps')} fps, {sp.get('duration')} s, {sp.get('size_mb')} MB |")
        L.append(f"| Loudness | {lo.get('I')} LUFS, true peak {lo.get('true_peak')} dBTP, LRA {lo.get('LRA')} LU |")
        L.append(f"| Sync | {f.get('sync_ms', '-')} ms vs the stems |")
        L.append(f"| Motion | median {f.get('median_motion')}; frozen runs (0.5 s+) {f.get('still_runs')} |")
        L.append(f"| Empty frames | mean flat {f.get('flat_mean')} %; seconds over 70 %: {f.get('flat_seconds')} |")
        L.append(f"| Picture onsets | {f.get('onsets_per_s')} per second; dead stretches {f.get('dead', [])} |")
        L.append(f"| Events shown | {f.get('shown_share', '-')} of planned picture events at their time and place; acts shown {f.get('acts_shown', '-')} |")
        L.append(f"| Word lock | the same events moved 0.7-2.5 s are seen {f.get('shown_shifted', '-')} of the time (p = {f.get('event_lock_p', '-')}); "
                 f"big picture onsets {f.get('lock_ratio', '-')}x as frequent at planned times as elsewhere (p = {f.get('lock_p', '-')}) |")
        L.append(f"| Sound | cued events with a sound starting at their time {f.get('cue_cover', '-')} (shifted cues: {f.get('cue_cover_shifted', '-')}, p = {f.get('cue_lock_p', '-')}); "
                 f"largest group of identical cues {f.get('cue_same_share', '-')} |")
        L.append(f"| Mix | voice over the bed {f.get('voice_over_bed_db', '-')} dB, music under the voice {f.get('music_under_voice_db', '-')} dB, music present {f.get('music_present', '-')} |")
        L.append(f"| Captions | band {f.get('caption_band_px', '-')} px (correlation {f.get('caption_corr', '-')}), follow {f.get('captions_follow', '-')} of words |")
        hf = f.get("hyperframes")
        if isinstance(hf, dict):
            L.append("| HyperFrames | " + "; ".join(f"{k}: {'passed' if r.get('passed') else 'FAILED'} ({r.get('errors', '?')} errors, {r.get('warnings', '?')} warnings)" for k, r in hf.items()) + " |")
        else:
            L.append(f"| HyperFrames | {hf} |")
        sk = f.get("seek")
        if isinstance(sk, dict) and sk.get("ran"):
            L.append("| Seek test | " + ", ".join(f"{x['t']} s: {x['mean']}" for x in sk["frames"]) + " (mean difference per frame) |")
        else:
            L.append(f"| Seek test | {sk if isinstance(sk, str) else (sk or {}).get('error', '-')} |")
        L.append("")
    return L


def write_events(P, out, ms):
    f = ms.get("film") or {}
    evs = f.get("events") or ms.get("plan", {}).get("events") or []
    L = [f"# Planned events of {P.name}", "",
         "Every picture event in plan.json, its film time, and what stage 3 measured. 'Score' is the change in the event's box at its time divided by the "
         "box's usual change between events (shown needs 2.5 or more); 'lag' is the strongest change minus the planned time; 'cue at' is when its sound starts.", "",
         "| Scene | # | Time | Word | Kind | Who | Does / text | Shown | Score | Lag | Cue | Cue at |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in evs:
        if e.get("t") is None:
            continue
        L.append(f"| {e['scene']} | {e['i']} | {e['t']:.2f} | {esc(e.get('word') or '')} | {e['kind']} | {esc(e.get('who') or '')} | {esc(e.get('does') or '')} | "
                 f"{'' if 'shown' not in e else ('yes' if e['shown'] else '**no**')} | {e.get('score', '')} | {'' if e.get('lag') is None else e['lag']} | "
                 f"{esc(e.get('sfx') or '')} | {'' if e.get('cue_t') is None else e['cue_t']} |")
    (out / "EVENTS.md").write_text("\n".join(L) + "\n")


def approval_files(P, mp4):
    files = [P.root / "film.json", P.root / "SCRIPT.md", P.plan_path, P.root / "assets" / "timing.json"]
    files += [P.root / "assets" / f"{n}.wav" for n in ("vo", "sfx", "music")]
    if mp4:
        files.append(Path(mp4))
    return [f for f in files if f.exists()]


def cmd_review(a, stages):
    P = Project(a.project, a.plan)
    if not P.root.exists():
        print(f"no such project folder: {P.root}")
        return 2
    out = Path(a.out).resolve() if a.out else P.root / "reviewer"
    out.mkdir(parents=True, exist_ok=True)
    issues = Issues()
    ms = {}
    ms["script"] = script_check.run(P, issues)
    plan_m = {}
    if "plan" in stages:
        plan_m = plan_check.run(P, issues)
        ms["plan"] = {k: v for k, v in plan_m.items() if k != "events"} | {"events": plan_m.get("events", [])}
    mp4 = None
    if "film" in stages:
        fm, F = film_check.run(P, issues, plan_m, a.mp4, a.quick)
        ms["film"] = fm
        mp4 = fm.get("mp4")
        if F is not None and not a.no_sheets and fm.get("events") is not None:
            try:
                import sheets
                flags = [(i.t0, i.rule + " " + i.problem[:40]) for i in issues if i.level == "must" and i.stage == "film" and i.t0 is not None]
                sheets.event_sheets(mp4, P, fm.get("events", []), out / "sheets", flags)
            except Exception as e:                       # sheets are evidence, not a check: never fail the review on them
                print(f"(sheets not written: {e})")
    must = [i for i in issues if i.level == "must"]
    complete = stages == STAGES and not a.quick
    verdict = "APPROVED" if (complete and not must) else ("REJECTED" if must else ("PASSED (stages " + ", ".join(stages) + ")"))
    hist = out / "history.md"
    rnd = 1 + (sum(1 for ln in hist.read_text().splitlines() if ln.startswith("| ") and ln[2:3].isdigit()) if hist.exists() else 0)
    write_report(P, out, issues, ms, stages, verdict, mp4, a.quick, rnd)
    if ms.get("plan") or ms.get("film"):
        write_events(P, out, ms)
    if ms.get("film", {}).get("mp4"):
        ms["film"]["mp4"] = os.path.relpath(ms["film"]["mp4"], P.root)          # paths in the record are relative to the film folder
    data = {"film": P.name, "verdict": verdict, "stages": stages, "quick": a.quick, "reviewer": VERSION, "reviewer_hash": reviewer_hash(),
            "plan": os.path.relpath(P.plan_path, P.root), "issues": [i.to_dict() for i in issues], "measured": ms,
            "date": datetime.datetime.now().isoformat(timespec="seconds")}
    (out / "review.json").write_text(json.dumps(data, indent=1, default=str))
    if not hist.exists():
        hist.write_text("| Round | Date | Stages | Verdict | Must (script/plan/film) | Should | MP4 sha256 |\n|---|---|---|---|---|---|---|\n")
    cnt = lambda s: sum(1 for i in must if i.stage == s)
    with open(hist, "a") as h:
        h.write(f"| {rnd} | {data['date']} | {','.join(stages)}{' quick' if a.quick else ''} | {verdict} | {cnt('script')}/{cnt('plan')}/{cnt('film')} | "
                f"{sum(1 for i in issues if i.level == 'should')} | {sha256(Path(mp4))[:12] if mp4 else '-'} |\n")
    stamp = out / "APPROVED.json"
    if verdict == "APPROVED":
        stamp.write_text(json.dumps({"film": P.name, "verdict": "APPROVED", "date": data["date"], "reviewer": VERSION, "reviewer_hash": reviewer_hash(),
                                     "files": {os.path.relpath(f, P.root): sha256(f) for f in approval_files(P, mp4)},
                                     "should_fix_left": sum(1 for i in issues if i.level == "should")}, indent=1))
    elif stamp.exists():
        stamp.unlink()                                   # a new review that does not approve withdraws the old approval
    print(f"{P.name}: {verdict}  ({len(must)} must, {sum(1 for i in issues if i.level == 'should')} should)  ->  {out / 'FIXLIST.md'}")
    for i in sorted(must, key=lambda i: (STAGES.index(i.stage), i.t0 or 0))[:12]:
        print(f"  must {i.rule} {fmt_span(i.t0, i.t1, P.fps):28s} {i.problem[:110]}")
    if len(must) > 12:
        print(f"  ... {len(must) - 12} more in FIXLIST.md")
    return 0 if not must else 1


def cmd_verify(a):
    P = Project(a.project, a.plan)
    out = Path(a.out).resolve() if a.out else P.root / "reviewer"
    stamp = out / "APPROVED.json"
    if not stamp.exists():
        print(f"{P.name}: NOT APPROVED (no {stamp})")
        return 1
    d = json.loads(stamp.read_text())
    bad = []
    for rel, h in d["files"].items():
        p = (P.root / rel) if not Path(rel).is_absolute() else Path(rel)
        if not p.exists():
            bad.append(f"{rel} is missing")
        elif sha256(p) != h:
            bad.append(f"{rel} changed after approval")
    if d.get("reviewer_hash") != reviewer_hash():
        bad.append("the reviewer's code or rules changed since this approval (review again with the current reviewer)")
    # an approval only means something from an unmodified reviewer: refuse one given by locally edited code
    import subprocess
    here = Path(__file__).resolve().parent
    g = subprocess.run(["git", "status", "--porcelain", "--", "."], cwd=here, capture_output=True, text=True)
    if g.returncode == 0 and any(ln[3:].endswith(".py") for ln in g.stdout.splitlines()):
        bad.append("tools/reviewer has uncommitted code changes; an approval from a modified reviewer does not count")
    if bad:
        print(f"{P.name}: APPROVAL INVALID: " + "; ".join(bad))
        return 1
    print(f"{P.name}: APPROVED on {d['date']} by reviewer {d['reviewer']} (hash {d['reviewer_hash'][:16]}); {len(d['files'])} files unchanged.")
    return 0


def cmd_draft(a):
    import draft_plan
    P = Project(a.project, a.plan)
    dst = Path(a.out) if a.out else P.root / "plan.draft.json"
    n = draft_plan.draft(P, dst)
    print(f"wrote {dst} ({n} events). Fill every TODO, then save it as plan.json.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["script", "plan", "film", "all", "verify", "draft-plan", "rules"])
    ap.add_argument("project", nargs="?")
    ap.add_argument("--plan")
    ap.add_argument("--mp4")
    ap.add_argument("--out")
    ap.add_argument("--quick", action="store_true", help="skip HyperFrames and the seek test (never approves)")
    ap.add_argument("--no-sheets", action="store_true")
    a = ap.parse_args()
    if a.command == "rules":
        print(rules_table())
        return 0
    if not a.project:
        ap.error("give the project folder, e.g. projects/black-hole-short")
    if a.command == "verify":
        return cmd_verify(a)
    if a.command == "draft-plan":
        return cmd_draft(a)
    stages = {"script": ["script"], "plan": ["script", "plan"], "film": STAGES, "all": STAGES}[a.command]
    return cmd_review(a, stages)


if __name__ == "__main__":
    sys.exit(main())
