"""Turn `review.py draft-plan` output into a calibration plan for stage 3 (how the mitochondria and ocean plans in this
folder were made):

    python tools/reviewer/review.py draft-plan projects/<film> --out /tmp/<film>.draft.json
    python tools/reviewer/calibration/autoplan.py projects/<film> /tmp/<film>.draft.json tools/reviewer/calibration/<film>.plan.json

Timeline events from the scene code (whole-scene background tweens left out), merged when they start within 0.25 s;
descriptions are the code lines and boxes are 'full'; reactions get who/where read off the frames by hand (REACTS).
Shot sizes and casts are not filled in, so stage 2 results for these plans mean nothing, and with whole-frame boxes
the per-event checks are much weaker than with a real plan."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import Project  # noqa: E402
from standard import KINDS_TEXT  # noqa: E402

REACTS = {
    "mitochondria-short": {
        ("walk", "there"): ("mitochondria", "full", "the mitochondria wake up: eyes open all over the muscle"),
        ("origin", "swallowed"): ("bacterium", [240, 780, 520, 1000], "the bacterium's face turns to fear as the big cell swallows it"),
        ("origin", "digested"): ("bacterium", [300, 700, 640, 960], "the bacterium calms down: not digested after all"),
        ("deal", "energy"): ("host cell", [380, 220, 820, 520], "the host cell beams: energy"),
        ("proof", "bacteria"): ("mitochondria", [140, 400, 1080, 800], "mitochondria and bacteria smile side by side"),
        ("mother", "thanks"): ("you", [220, 330, 480, 760], "you wave: thanks, Mom"),
    },
}
APPEAR = {("mitochondria-short", "mother", "mom"): ([460, 240, 640, 420], "a heart pops up above the hand")}
HOLDS = {
    "mitochondria-short": [
        {"from": 11.0, "to": 13.0, "why": "the match cut into the past: the vignette closes and opens (REVIEW.md, accepted flat seconds 11-12)"},
        {"from": 14.0, "to": 15.0, "why": "the big cell closes around the bacterium (REVIEW.md, accepted flat second 14)"},
        {"from": 23.0, "to": 24.0, "why": "the first second of the proof scene (REVIEW.md, accepted flat second 23)"},
    ],
    "ocean-glow-short": [],
}


def main(project, draft, out):
    P = Project(project, draft)
    name = P.name
    plan = {"version": 1, "_note": "Auto-converted from `review.py draft-plan` output for stage-3 calibration (calibration/autoplan.py): timeline "
                                   "events from the scene code, merged when they start within 0.25 s; descriptions are code lines; reactions have "
                                   "who/where read off the frames. Shots and casts are not filled in, so stage 2 results for this plan mean nothing.",
            "characters": sorted({v[0] for v in REACTS.get(name, {}).values()}), "holds": HOLDS.get(name, []), "scenes": []}
    for k, s in enumerate(P.plan["scenes"]):
        evs = []
        for e in s["events"]:
            code = e.get("_code", "")
            if "duration: DUR" in code:
                continue
            t, err, _ = P.resolve(s["id"], e)
            if err:
                continue
            e = dict(e)
            e["_t"] = t
            evs.append(e)
        evs.sort(key=lambda e: e["_t"])
        kept = []
        for e in evs:
            text = e["kind"] in KINDS_TEXT
            if e["kind"] == "title" and any(x["kind"] == "title" for x in kept):
                continue
            if any((x["kind"] in KINDS_TEXT) == text and abs(x["_t"] - e["_t"]) < 0.25 for x in kept):
                continue
            kept.append(e)
        out_ev = []
        if k > 0:
            out_ev.append({"time": 0, "kind": "transition", "does": "cut to the next scene"})
        for e in kept:
            ev = {key: e[key] for key in ("word", "n", "offset", "time") if key in e}
            w = (s["id"], str(e.get("word") or "").lower())
            if e["kind"] in ("react", "act"):
                if w in REACTS.get(name, {}):
                    who, where, does = REACTS[name][w]
                    ev.update({"kind": "react", "who": who, "where": where, "does": does})
                elif (name,) + w in APPEAR:
                    where, does = APPEAR[(name,) + w]
                    ev.update({"kind": "appear", "where": where, "does": does})
                else:
                    ev.update({"kind": "move", "does": "auto: " + e["_code"].split(":", 1)[1].strip()[:70], "where": "full"})
            elif e["kind"] in KINDS_TEXT:
                ev.update({"kind": e["kind"], "text": e.get("text") if e.get("text") not in (None, "TODO") else "auto"})
            else:
                ev.update({"kind": e["kind"], "does": "auto: " + e["_code"].split(":", 1)[1].strip()[:70], "where": "full"})
            if e.get("sfx"):
                ev["sfx"] = e["sfx"]
            out_ev.append(ev)
        cast = sorted({ev["who"] for ev in out_ev if ev.get("who")})
        plan["scenes"].append({"id": s["id"], "transition": "cut" if k else "cold open", "cast": cast,
                               "shots": [{"time": 0, "size": "medium", "move": "not filled in"}], "events": out_ev})
    json.dump(plan, open(out, "w"), indent=1)
    print(name, sum(len(s["events"]) for s in plan["scenes"]), "events")


if __name__ == "__main__":
    main(*sys.argv[1:4])
