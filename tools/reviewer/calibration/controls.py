"""Negative controls for the per-event checks: how often does the reviewer see an event, or hear a cue, at times
where nothing was planned?

    python tools/reviewer/calibration/controls.py projects/<film> tools/reviewer/calibration/<film>.plan.json

For every planned picture event it runs the stage-3 visibility test at the planned time and at up to 8 random times
within +-4 s that are at least 0.9 s from every planned event in an overlapping box; for every cued event, the sound
test at the planned time and at random times 0.9 s or more from every planned cue. A useful test fires often at the
planned times and rarely at the others.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import plan_check  # noqa: E402
from common import Issues, Project  # noqa: E402
from film_check import Film, boxes_overlap  # noqa: E402
from standard import KINDS_PICTURE  # noqa: E402


def main(project, plan):
    P = Project(project, plan)
    pm = plan_check.run(P, Issues())
    F = Film(P.find_mp4(), P, pm)
    F.probe()
    F.stems()
    F.picture()
    events = [e for e in pm["events"] if e["t"] is not None]
    pic = [e for e in events if e["kind"] in KINDS_PICTURE]
    rng = np.random.default_rng(3)

    def away(e, pool, use_box, k=8):
        near = [o for o in pool if not use_box or boxes_overlap(F.fine_box(o.get("box")), F.fine_box(e.get("box")))]
        out = []
        for _ in range(400):
            t = e["t"] + rng.uniform(-4, 4)
            if 0.6 <= t <= F.dur - 0.6 and all(abs(t - o["t"]) >= 0.9 for o in near):
                out.append(t)
            if len(out) >= k:
                break
        return out

    a = [F.event_check(e)[0] for e in pic]
    b = [F.event_check(dict(e, t=t))[0] for e in pic for t in away(e, events, True)]
    acts = [ok for e, ok in zip(pic, a) if e["kind"] in ("act", "react")]
    print(f"{P.name}")
    print(f"  picture: seen at planned times {np.mean(a):.3f} (n {len(a)}), away from events {np.mean(b) if b else float('nan'):.3f} (n {len(b)})")
    if acts:
        print(f"  acts:    seen at planned times {np.mean(acts):.3f} (n {len(acts)})")
    print("  not seen:", ", ".join(f"{e['scene']}:{e['word'] or 'time'}" for e, ok in zip(pic, a) if not ok) or "-")
    if "sfx" in F.stem:
        F.cue_levels()
        cued = [e for e in pic if e.get("sfx")]
        cues = [e for e in events if e.get("sfx")]
        sa = [F.cue_hit(e["t"]) is not None for e in cued]
        sb = [F.cue_hit(t) is not None for e in cued for t in away(e, cues, False)]
        print(f"  sound:   at cued events {np.mean(sa):.3f} (n {len(sa)}), away from cues {np.mean(sb) if sb else float('nan'):.3f} (n {len(sb)})")
        print("  no sound:", ", ".join(f"{e['scene']}:{e['word'] or 'time'}" for e, ok in zip(cued, sa) if not ok) or "-")


if __name__ == "__main__":
    main(*sys.argv[1:3])
