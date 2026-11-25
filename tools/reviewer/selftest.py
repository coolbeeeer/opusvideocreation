"""Self-test: does the reviewer reject films that are bad in known ways?

    python tools/reviewer/selftest.py [--project projects/black-hole-short]
                                      [--plan tools/reviewer/calibration/black-hole-short.plan.json] [--keep]

Copies the project into a temporary folder (the film in projects/ is never touched), reviews the copy as it is, then
builds one damaged copy per row below and reviews each (quick mode, no HyperFrames). A damaged copy passes the test
when the review rejects it with new must items under the rules that describe the damage. Prints a table and exits 1 if any row fails.

  script: generic opening    "In this video, let's dive into ..." before the hook                       S05, S07
  plan: labels instead       every picture event becomes a label                                         P07
  plan: posing               every act is "stands" or "floats"                                           P10
  film: slideshow            one frame held every 2 s                                                    F06, F08, F09
  film: captions only        one still frame, only the caption band moves                                F06, F09
  film: picture late         the picture 0.7 s behind the voice                                          F09, F10
  plan: wrong times          every event moved 0.8-2 s from its word                                     F09, F10
  sound: one pop             the effects replaced by the same pop on every cued event                    F12
  sound: no effects          the effects stem silent                                                     F12
  sound: random hits         varied sounds at random times instead of on the events                      F12
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy.io import wavfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from film_check import FFMPEG  # noqa: E402

REPO = HERE.parent.parent


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(" ".join(map(str, cmd))[:300] + "\n" + r.stderr[-800:])
    return r


def copy_project(src, dst):
    """Small files are copied, big ones (stems, renders, scene code) linked: the damaged copies replace links with files."""
    dst.mkdir(parents=True)
    for name in ("film.json", "SCRIPT.md"):
        if (src / name).exists():
            shutil.copy2(src / name, dst / name)
    (dst / "assets").mkdir()
    for p in (src / "assets").iterdir():
        if p.suffix == ".json":
            shutil.copy2(p, dst / "assets" / p.name)
        elif p.name in ("vo.wav", "sfx.wav", "music.wav"):
            (dst / "assets" / p.name).symlink_to(p)
    for d in ("compositions", "audio"):
        if (src / d).exists():
            (dst / d).symlink_to(src / d)
    (dst / "renders").mkdir()
    mp4 = sorted((src / "renders").glob("*.mp4"), key=lambda p: p.stat().st_mtime)[-1]
    (dst / "renders" / "film.mp4").symlink_to(mp4)
    return dst / "renders" / "film.mp4"


def must_counts(d):
    c = {}
    for i in d.get("issues", []):
        if i["level"] == "must":
            c[i["rule"]] = c.get(i["rule"], 0) + 1
    return c


def review(proj, plan, out):
    r = subprocess.run([sys.executable, str(HERE / "review.py"), "film", str(proj), "--plan", str(plan), "--out", str(out), "--quick", "--no-sheets"],
                       capture_output=True, text=True)
    if not (out / "review.json").exists():
        print(r.stdout[-1500:], r.stderr[-1500:])
        return "CRASHED", [], {}
    d = json.loads((out / "review.json").read_text())
    return d["verdict"], sorted({i["rule"] for i in d["issues"] if i["level"] == "must"}), d


def read_wav(p):
    sr, x = wavfile.read(p)
    return sr, x.astype(np.float32) / (32768.0 if x.dtype == np.int16 else 1.0)


def write_wav(p, sr, x):
    p.unlink(missing_ok=True)
    wavfile.write(p, sr, np.clip(x, -1, 1).astype(np.float32))


def remux(proj, mp4_in, sr=48000):
    """Rebuild the MP4's audio from the (changed) stems, so the film and its stems still agree."""
    A = proj / "assets"
    xs = [read_wav(A / f"{n}.wav")[1] for n in ("vo", "sfx", "music")]
    xs = [x if x.ndim == 2 else np.repeat(x[:, None], 2, axis=1) for x in xs]
    n = max(len(x) for x in xs)
    mix = np.zeros((n, 2), np.float32)
    for x in xs:
        mix[: len(x)] += x[:, :2]
    tmp = proj / "renders" / "mix.wav"
    wavfile.write(tmp, sr, np.clip(mix, -1, 1).astype(np.float32))
    out = proj / "renders" / "film.tmp.mp4"
    sh([FFMPEG, "-v", "error", "-y", "-i", str(mp4_in), "-i", str(tmp), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-ac", "2", str(out)])
    final = proj / "renders" / "film.mp4"
    final.unlink()
    out.rename(final)
    tmp.unlink()


def encode(proj, args):
    out = proj / "renders" / "film.tmp.mp4"
    sh([FFMPEG, "-v", "error", "-y"] + args + ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", str(out)])
    final = proj / "renders" / "film.mp4"
    final.unlink()
    out.rename(final)


def pop(sr, f=900.0, dur=0.09, seed=0):
    t = np.arange(int(dur * sr)) / sr
    return (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.018) + 0.3 * np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t / 0.004)) * 0.5


def cued_times(base_review):
    return [e["t"] for e in base_review["measured"]["film"]["events"] if e.get("sfx")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=str(REPO / "projects" / "black-hole-short"))
    ap.add_argument("--plan", default=str(HERE / "calibration" / "black-hole-short.plan.json"))
    ap.add_argument("--keep", action="store_true", help="keep the temporary folder")
    ap.add_argument("--work", help="work in this folder (created; kept) instead of a temporary one")
    a = ap.parse_args()
    src, plan0 = Path(a.project).resolve(), Path(a.plan).resolve()
    work = Path(a.work).resolve() if a.work else Path(tempfile.mkdtemp(prefix="reviewer-selftest-"))
    if a.work:
        shutil.rmtree(work, ignore_errors=True)
        work.mkdir(parents=True)
        a.keep = True
    rows = []
    verdict, base_must, base_meas = "not run", [], ""
    try:
        base = work / "base"
        copy_project(src, base / src.name)
        verdict, base_must, base_d = review(base / src.name, plan0, base / "review")
        print(f"undamaged copy: {verdict}, must rules {base_must}")
        bf = base_d["measured"]["film"]
        base_meas = (f"motion {bf.get('median_motion')}, events seen {bf.get('shown_share')} (moved: {bf.get('shown_shifted')}), "
                     f"sound at events {bf.get('cue_cover')} (moved: {bf.get('cue_cover_shifted')}), same sound {bf.get('cue_same_share')}")
        film = base_d["measured"]["film"]
        dur = film["specs"]["duration"]
        band = film.get("caption_band_px") or [int(0.6 * 1920), int(0.66 * 1920)]
        plan = json.loads(plan0.read_text())
        W, H = (film["specs"]["video"]["width"], film["specs"]["video"]["height"])

        def case(name, expect, make, plan_obj=None):
            d = work / name.replace(" ", "-").replace(":", "")
            proj = d / src.name
            mp4 = copy_project(src, proj)
            pp = d / "plan.json"
            pp.write_text(json.dumps(plan_obj if plan_obj is not None else plan))
            make(proj, mp4.resolve())
            v, must, dd = review(proj, pp, d / "review")
            new = [r for r in must if r not in base_must]
            cb, cv = must_counts(base_d), must_counts(dd)
            ok = v == "REJECTED" and all(cv.get(r, 0) > cb.get(r, 0) for r in expect)   # each expected rule finds something new
            counts = ", ".join(f"{r} {cb.get(r, 0)}->{cv.get(r, 0)}" for r in expect)
            fm = (dd.get("measured") or {}).get("film") or {}
            meas = (f"motion {fm.get('median_motion')}, events seen {fm.get('shown_share')} (moved: {fm.get('shown_shifted')})" if name.startswith(("film", "plan: wrong"))
                    else f"sound at events {fm.get('cue_cover')} (moved: {fm.get('cue_cover_shifted')}), same sound {fm.get('cue_same_share')}" if name.startswith("sound") else "")
            rows.append((name, counts, new, "pass" if ok else "FAIL", meas))
            print(f"{name:24s} {v:9s} must items {counts:30s} other new must rules: {', '.join(r for r in new if r not in expect) or '-'}  -> {'pass' if ok else 'FAIL'}")

        nothing = lambda proj, mp4: None

        # ------------------------------------------------------------------ script
        def generic(proj, mp4):
            f = json.loads((proj / "film.json").read_text())
            f["lines"][0]["text"] = ("In this video, we are going to take a closer look at what really happens to you when you fall into a black hole. "
                                     + f["lines"][0]["text"])
            (proj / "film.json").write_text(json.dumps(f, indent=1))
        case("script: generic opening", ["S05", "S07"], generic)

        # ------------------------------------------------------------------ plan
        labels = json.loads(json.dumps(plan))
        for s in labels["scenes"]:
            for e in s["events"]:
                if e["kind"] not in ("label", "title", "transition", "camera"):
                    e.update({"kind": "label", "text": e.get("does", "label")[:20]})
        case("plan: labels instead", ["P07"], nothing, labels)

        posing = json.loads(json.dumps(plan))
        for s in posing["scenes"]:
            for e in s["events"]:
                if e["kind"] in ("act", "react"):
                    e["does"] = "stands and looks at the camera" if e["kind"] == "act" else "floats in place"
        case("plan: posing", ["P10"], nothing, posing)

        # ------------------------------------------------------------------ picture
        case("film: slideshow", ["F06", "F08", "F09"], lambda proj, mp4: encode(proj, ["-i", str(mp4), "-vf", "fps=0.5,fps=30", "-c:a", "copy", "-t", f"{dur:.3f}"]))

        def captions_only(proj, mp4):
            still = proj / "renders" / "still.png"
            sh([FFMPEG, "-v", "error", "-y", "-ss", f"{dur * 0.4:.2f}", "-i", str(mp4), "-frames:v", "1", str(still)])
            y0, y1 = max(0, band[0]), min(H, band[1])              # exactly the band the reviewer found: nothing else moves
            encode(proj, ["-loop", "1", "-framerate", "30", "-i", str(still), "-i", str(mp4), "-filter_complex",
                          f"[1:v]crop={W}:{y1 - y0}:0:{y0}[c];[0:v][c]overlay=0:{y0}:shortest=1[v]", "-map", "[v]", "-map", "1:a", "-c:a", "copy", "-t", f"{dur:.3f}"])
        case("film: captions only", ["F06", "F09"], captions_only)

        case("film: picture late", ["F09", "F10"], lambda proj, mp4: encode(proj, ["-i", str(mp4), "-vf", "tpad=start_duration=0.7:start_mode=clone",
                                                                                     "-c:a", "copy", "-t", f"{dur:.3f}"]))

        rng = np.random.default_rng(4)
        moved = json.loads(json.dumps(plan))
        sys.path.insert(0, str(HERE))
        from common import Project
        P = Project(src, plan0)
        for s in moved["scenes"]:
            sc = P.scene(s["id"])
            for e in s["events"]:
                t, err, _ = P.resolve(s["id"], e)
                if err:
                    continue
                for _ in range(20):
                    nt = t + rng.uniform(0.8, 2.0) * rng.choice([-1, 1])
                    if sc["start"] + 0.05 <= nt <= sc["end"] - 0.05:
                        break
                else:
                    nt = sc["start"] + (sc["end"] - sc["start"]) * rng.uniform(0.1, 0.9)
                for k in ("word", "n", "offset"):
                    e.pop(k, None)
                e["time"] = round(nt - sc["start"], 3)
        case("plan: wrong times", ["F09", "F10"], nothing, moved)

        # ------------------------------------------------------------------ sound
        cues = cued_times(base_d)

        def one_pop(proj, mp4):
            sr, x = read_wav(proj / "assets" / "sfx.wav")
            y = np.zeros_like(x)
            p = pop(sr)
            for t in cues:
                i = int(t * sr)
                seg = y[i:i + len(p)]
                seg += (p[: len(seg)] if y.ndim == 1 else p[: len(seg), None])
            write_wav(proj / "assets" / "sfx.wav", sr, y)
            remux(proj, mp4)
        case("sound: one pop", ["F12"], one_pop)

        def silent(proj, mp4):
            sr, x = read_wav(proj / "assets" / "sfx.wav")
            write_wav(proj / "assets" / "sfx.wav", sr, np.zeros_like(x))
            remux(proj, mp4)
        case("sound: no effects", ["F12"], silent)

        def random_hits(proj, mp4):
            sr, x = read_wav(proj / "assets" / "sfx.wav")
            y = np.zeros_like(x)
            r = np.random.default_rng(9)
            for k, t in enumerate(np.sort(r.uniform(0.3, dur - 0.5, len(cues)))):
                p = pop(sr, f=r.uniform(300, 3000), dur=r.uniform(0.06, 0.3), seed=k)
                i = int(t * sr)
                seg = y[i:i + len(p)]
                seg += (p[: len(seg)] if y.ndim == 1 else p[: len(seg), None])
            write_wav(proj / "assets" / "sfx.wav", sr, y)
            remux(proj, mp4)
        case("sound: random hits", ["F12"], random_hits)
    finally:
        if a.keep:
            print(f"kept {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)
    print()
    print(f"Undamaged copy: {verdict}, must rules {', '.join(base_must) or 'none'}; {base_meas}.")
    print()
    print("| Damage | Must items: undamaged -> damaged | All must rules that are new | Measured | Result |")
    print("|---|---|---|---|---|")
    for name, counts, new, res, meas in rows:
        print(f"| {name} | {counts} | {', '.join(new) or '-'} | {meas} | {res} |")
    return 0 if all(r[3] == "pass" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
