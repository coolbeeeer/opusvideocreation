"""Stage 2: the scenes, from plan.json (the event list and shot plan; format in PLAN.md).

Checks the plan the way I plan my own films: something happens in the picture about once a second, on the word it
illustrates; every sentence is shown, not only captioned; the shot size changes; characters act instead of posing;
every picture event has its own sound. Resolved events are handed to stage 3, which checks the film against them.
"""
import re
from collections import Counter

from common import Issues, key
from standard import KINDS, KINDS_PICTURE, KINDS_TEXT, POSE_VERBS, SIZE_ALIASES, SIZES, T

REGIONS = {  # named boxes as fractions of the frame (x0, y0, x1, y1)
    "full": (0, 0, 1, 1), "top": (0, 0, 1, 0.4), "middle": (0, 0.3, 1, 0.7), "center": (0.2, 0.3, 0.8, 0.7),
    "bottom": (0, 0.6, 1, 1), "left": (0, 0, 0.5, 1), "right": (0.5, 0, 1, 1),
    "top-left": (0, 0, 0.5, 0.4), "top-right": (0.5, 0, 1, 0.4), "bottom-left": (0, 0.6, 0.5, 1), "bottom-right": (0.5, 0.6, 1, 1),
}


def norm_size(s):
    s = str(s or "").strip().lower().replace(" ", "-").replace("_", "-")
    s = SIZE_ALIASES.get(s, s)
    return s if s in SIZES else None


def norm_cue(name):
    """A cue's sound name without sizes and qualifiers, so 'pop (low)' and 'small pop' count as the same 'pop'."""
    c = re.sub(r"[^a-z ]", " ", str(name).lower())
    c = re.sub(r"\b(sfx|sound|cue|soft|small|big|short|long|low|high|quiet|loud)\b", " ", c)
    return " ".join(c.split()) or str(name).strip().lower()


def box_of(where, W, H):
    """[x0, y0, x1, y1] in film pixels from a list or a region name; None if missing or invalid."""
    if where is None:
        return None
    if isinstance(where, str):
        r = REGIONS.get(where.strip().lower())
        return None if r is None else [r[0] * W, r[1] * H, r[2] * W, r[3] * H]
    try:
        x0, y0, x1, y1 = [float(v) for v in where]
    except (TypeError, ValueError):
        return None
    x0, x1 = sorted((max(0, x0), min(W, x1)))
    y0, y1 = sorted((max(0, y0), min(H, y1)))
    return [x0, y0, x1, y1] if (x1 - x0) >= 8 and (y1 - y0) >= 8 else None


def run(P, issues: Issues):
    st = "plan"
    m = {"events": [], "shots": [], "scenes": {}}
    if P.plan is None:
        issues.must(st, "P01", f"No plan: {P.plan_path.name} is missing.",
                    "Write plan.json (format: tools/reviewer/PLAN.md) before building scenes, or start from "
                    "`python tools/reviewer/review.py draft-plan <project>` and complete it.")
        return m
    if not P.scenes or P.scenes[0]["start"] is None:
        issues.must(st, "P01", "assets/timing.json is missing, so plan words cannot be timed.",
                    "Record the voice first: python vo.py && python align.py && python build.py.")
        return m
    plan_sc = P.plan.get("scenes", [])
    ids_plan = [s.get("id") for s in plan_sc]
    ids_film = [s["id"] for s in P.scenes]
    if ids_plan != ids_film:
        miss = [i for i in ids_film if i not in ids_plan]
        extra = [i for i in ids_plan if i not in ids_film]
        issues.must(st, "P01", f"plan scenes {ids_plan} do not match the film's scenes {ids_film}"
                    + (f" (missing: {miss})" if miss else "") + (f" (unknown: {extra})" if extra else "") + ".",
                    "List every scene of film.json in plan.json, same ids, same order.")
    chars = set(P.plan.get("characters", []) or [])
    holds = resolve_holds(P, issues)
    m["holds"] = holds
    W, H = P.W, P.H
    sent = P.sentences()
    word_t = [w[1] for w in P.words]
    word_e = [w[2] for w in P.words]
    in_hold = lambda t: any(h[0] <= t <= h[1] for h in holds)
    code = load_code(P)
    cast_time = {}                                       # character -> [acts, seconds on screen]

    for sc in P.scenes:
        sid = sc["id"]
        ps = next((s for s in plan_sc if s.get("id") == sid), None)
        if ps is None:
            continue
        rows = []
        for j, ev in enumerate(ps.get("events", []) or [], 1):
            t, err, wi = P.resolve(sid, ev)
            tag = f"{sid} event {j}" + (f" ('{ev.get('word')}')" if ev.get("word") else "")
            kind = str(ev.get("kind", "")).lower()
            r = {"scene": sid, "i": j, "t": t, "word": ev.get("word"), "n": ev.get("n", 1), "offset": float(ev.get("offset", 0) or 0),
                 "kind": kind, "who": ev.get("who"), "does": ev.get("does") or ev.get("shows") or ev.get("text") or "",
                 "sfx": ev.get("sfx"), "box": box_of(ev.get("where"), W, H), "anchored": bool(ev.get("word")), "wi": wi}
            if err:
                issues.must(st, "P02", f"{tag}: {err}.", "Anchor every event to a word spoken in its scene (the words and their times are in assets/timing.json).", scene=sid)
                continue
            todo = [k for k, v in ev.items() if not k.startswith("_") and "TODO" in str(v)]
            if todo:
                issues.must(st, "P03", f"{tag}: unfinished ({', '.join(todo)} still TODO).", "Fill in every TODO of the draft, or delete the event if it is not a real picture event.", scene=sid, t0=t)
            if not (sc["start"] - 0.3 <= t <= sc["end"] + 0.1):
                issues.must(st, "P02", f"{tag} resolves to {t:.2f} s, outside the scene ({sc['start']:.2f}-{sc['end']:.2f} s).",
                            "Use a word of this scene (n counts occurrences from the scene start).", scene=sid, t0=t)
                continue
            if kind not in KINDS:
                issues.must(st, "P03", f"{tag}: kind '{ev.get('kind')}' is not one of {sorted(KINDS)}.", "Pick the kind that says what the viewer sees change.", scene=sid, t0=t)
                continue
            if kind in KINDS_PICTURE and len(str(r["does"]).split()) < 2:
                issues.must(st, "P03", f"{tag}: picture event without a description ('does').", "Say what the viewer sees, e.g. \"the guest divides in two\".", scene=sid, t0=t)
            if kind in KINDS_TEXT and not ev.get("text"):
                issues.must(st, "P03", f"{tag}: label without its 'text'.", "Give the label's words.", scene=sid, t0=t)
            if kind in ("act", "react"):
                if not r["who"]:
                    issues.must(st, "P03", f"{tag}: {kind} event without 'who'.", "Name the character that acts.", scene=sid, t0=t)
                elif chars and r["who"] not in chars:
                    issues.must(st, "P03", f"{tag}: unknown character '{r['who']}'.", f"Add it to plan 'characters' ({sorted(chars)}).", scene=sid, t0=t)
                if r["box"] is None:
                    issues.must(st, "P03", f"{tag}: {kind} event without a valid 'where' box.", "Give the character's box on screen at that moment ([x0, y0, x1, y1] in film pixels), so stage 3 can check it moves there.", scene=sid, t0=t)
            if ev.get("where") is not None and r["box"] is None:
                issues.must(st, "P03", f"{tag}: 'where' {ev.get('where')} is not a box inside the frame or a region name.", f"Use [x0, y0, x1, y1] in pixels or one of {sorted(REGIONS)}.", scene=sid, t0=t)
            elif ev.get("where") is None and kind in KINDS_PICTURE - {"camera", "transition", "act", "react"}:
                issues.must(st, "P03", f"{tag}: {kind} event without 'where'.",
                            "Say where on screen it happens: [x0, y0, x1, y1] in film pixels, or a region name (top, center, bottom-left ...; 'full' for a change "
                            "of the whole frame). Stage 3 looks for the change there; a small event judged on the whole frame is easily missed.", scene=sid, t0=t)
            if r["anchored"]:
                w0, w1 = P.words[wi][1], P.words[wi][2]           # within 0.6 s of the word: before its start or after its end
                if not (w0 - T["offset_max"] - 1e-6 <= t <= w1 + T["offset_max"] + 1e-6):
                    issues.must(st, "P08", f"{tag}: {t - w0:+.2f} s from the start of its word ({w1 - w0:.2f} s long).",
                                f"Anchor it to the word it shows: within {T['offset_max']} s before the word starts or after it ends.", scene=sid, t0=t)
            if not r["anchored"]:
                near = min((abs(t - x) for x in word_t), default=9)
                speaking = any(a - T["free_clear_s"] <= t <= b + 0.05 for a, b in zip(word_t, word_e))
                if speaking and near < 2.0:
                    issues.must(st, "P08", f"{tag}: placed by time ({t:.2f} s) while words are being spoken.", "Anchor it to the word it illustrates; only pauses and scene starts may use 'time'.", scene=sid, t0=t)
            rows.append(r)
        m["events"] += rows
        # ---------------------------------------------------------------- shots
        shots = []
        for j, sh in enumerate(ps.get("shots", []) or [], 1):
            t, err, _ = P.resolve(sid, sh)
            if err:
                issues.must(st, "P02", f"{sid} shot {j}: {err}.", "Anchor every shot to a word of its scene (or 'time': 0 for the scene start).", scene=sid)
                continue
            size = norm_size(sh.get("size"))
            if size is None:
                issues.must(st, "P09", f"{sid} shot {j}: size '{sh.get('size')}' is not one of {SIZES}.", "Name the shot size.", scene=sid, t0=t)
                continue
            shots.append({"scene": sid, "t": t, "size": size, "move": str(sh.get("move", "static") or "static").lower()})
        if not shots:
            issues.must(st, "P09", f"Scene '{sid}' has no shot plan.", "Add 'shots': the size at the start, and every size change or camera move on its word.", scene=sid, t0=sc["start"])
        m["shots"] += shots
        # ---------------------------------------------------------------- density and gaps
        pic = sorted([r for r in rows if r["kind"] in KINDS_PICTURE], key=lambda r: r["t"])
        txt = [r for r in rows if r["kind"] in KINDS_TEXT]
        rate = len(pic) / sc["dur"] if sc["dur"] else 0
        m["scenes"][sid] = {"dur": sc["dur"], "picture_events": len(pic), "text_events": len(txt), "rate": round(rate, 2),
                            "sizes": [s["size"] for s in shots], "moves": [s["move"] for s in shots]}
        if len(pic) < T["ev_min_per_scene"] or rate < T["ev_rate_must"]:
            issues.must(st, "P04", f"Scene '{sid}' ({sc['dur']:.1f} s) plans {len(pic)} picture events ({rate:.2f}/s).",
                        f"Plan at least one picture event per {1 / T['ev_rate_must']:.1f} s (my films: about one per second): an action, a transformation or a camera move on the word it shows.",
                        scene=sid, t0=sc["start"], t1=sc["end"])
        elif rate < T["ev_rate_should"]:
            issues.should(st, "P04", f"Scene '{sid}' plans {rate:.2f} picture events per second.", "Add events toward one per 1.5 s.", scene=sid, t0=sc["start"], t1=sc["end"])
        sw = [w for w in P.words if sc["start"] <= w[1] < sc["end"]]
        if sw:
            pts = [sw[0][1] - 0.3] + [r["t"] for r in pic] + [sw[-1][2]]
            pts = sorted(pts)
            for a, b in zip(pts, pts[1:]):
                if b - a > T["gap_should"]:
                    if in_hold((a + b) / 2):
                        continue
                    lvl = issues.must if b - a > T["gap_must"] else issues.should
                    lvl(st, "P05", f"Scene '{sid}': {b - a:.1f} s with no picture event {P.narration(a, b)}.",
                        "Show what is said in that stretch: add a picture event on its key word.", scene=sid, t0=a, t1=b)
        # first event in the scene
        if pic and pic[0]["t"] - sc["start"] > T["first_event_scene_s"] and sid != P.scenes[0]["id"]:
            issues.should(st, "P13", f"Scene '{sid}' starts {pic[0]['t'] - sc['start']:.1f} s before its first picture event.", "Start on motion: a transition or a camera move at the cut.", scene=sid, t0=sc["start"])
        # characters: everyone on screen (the scene's `cast`, else everyone named in its events) must act in it
        cast = ps.get("cast")
        if not isinstance(cast, list):
            cast = sorted({r["who"] for r in rows if r.get("who")})
        for who in cast:
            if chars and who not in chars:
                issues.must(st, "P03", f"Scene '{sid}': cast member '{who}' is not in plan 'characters' ({sorted(chars)}).", "List every character in 'characters'.", scene=sid, t0=sc["start"])
            acts = [r for r in rows if r.get("who") == who and r["kind"] in ("act", "react")]
            verbs = [first_verb(r["does"]) for r in acts]
            posing = acts and all(v in POSE_VERBS for v in verbs)
            tot = cast_time.setdefault(who, [0, 0.0])
            tot[0] += len(acts)
            tot[1] += sc["dur"]
            if not acts or posing:
                issues.must(st, "P10", f"Scene '{sid}': '{who}' is on screen for {sc['dur']:.1f} s and " + ("never acts or reacts." if not acts else "only poses (" + ", ".join(sorted(set(verbs))) + ")."),
                            f"Give '{who}' actions on the words: react with the face, gesture, move with purpose (my films: panic on 'feet', stretch on 'stretched', shrug on 'nothing'). "
                            "If the character is only a prop here, take it out of the cast.", scene=sid, t0=sc["start"], t1=sc["end"])
            elif who == cast[0] and len(acts) / sc["dur"] < T["act_rate_must"]:
                issues.should(st, "P10", f"Scene '{sid}': its lead, '{who}', acts {len(acts)} times in {sc['dur']:.1f} s.", "Add a reaction or gesture on a key word.", scene=sid, t0=sc["start"], t1=sc["end"])
        if code and code.get(sid) is not None:
            src = code[sid]
            for r in rows:
                if r["anchored"] and r["kind"] in KINDS_PICTURE and not re.search(r'(at|K\.t)\(\s*"%s"' % re.escape(key(str(r["word"]))), src):
                    issues.should(st, "P15", f"{sid} event {r['i']} is planned on '{r['word']}', but the scene code never uses at(\"{key(str(r['word']))}\").",
                                  "Implement the event on its word, or correct the plan.", scene=sid, t0=r["t"])
        if sid != P.scenes[0]["id"] and not ps.get("transition"):
            issues.should(st, "P12", f"Scene '{sid}' does not say how it begins.", "Add 'transition': cut on motion, match cut, push, pull, wipe ...", scene=sid, t0=sc["start"])

    ev = [r for r in m["events"]]
    pic = [r for r in ev if r["kind"] in KINDS_PICTURE]
    if not ev:
        return m
    # ---------------------------------------------------------------- P06 every sentence shown, P07 text share
    for s in sent:
        if s["i0"] >= len(P.words):
            continue
        # events on the sentence's words, or placed by time just before or during it (a camera move at a cut);
        # a cut alone does not show a sentence, so transitions do not count
        a, b = P.words[s["i0"]][1] - T["offset_max"], P.words[min(s["i1"], len(P.words) - 1)][2] + 0.2
        evs = [r for r in ev if (r["wi"] is not None and s["i0"] <= r["wi"] <= s["i1"]) or (r["wi"] is None and a <= r["t"] <= b)]
        p = [r for r in evs if r["kind"] in KINDS_PICTURE and r["kind"] != "transition"]
        need = 2 if len(s["text"].split()) >= 12 else 1
        sid = P.scene_at(P.words[s["i0"]][1])
        a = P.words[s["i0"]][1] - 0.3
        if not p and evs:
            issues.must(st, "P07", f"\"{s['text']}\" is carried only by text on screen ({', '.join(str(r['does']) for r in evs)}).",
                        "Show it in the picture: what does the sentence make happen? Keep the label, add the action.", scene=sid, t0=a + 0.3, t1=b)
        elif len(p) < need:
            issues.must(st, "P06", f"\"{s['text']}\" has {len(p)} picture events (needs {need}).",
                        "Give the sentence's key word a picture event (if you cannot draw the verb, rewrite the line).", scene=sid, t0=a + 0.3, t1=b)
    share = 1 - len(pic) / len(ev)
    m["text_share"] = round(share, 2)
    if share > T["label_share_must"]:
        issues.must(st, "P07", f"{share * 100:.0f} % of planned events are text (labels, titles).", "Labels name what the picture shows; they cannot replace it. Turn labels into actions.")
    elif share > T["label_share_should"]:
        issues.should(st, "P07", f"{share * 100:.0f} % of planned events are text.", "Aim for at most a third.")
    # ---------------------------------------------------------------- P08 anchoring
    anch = sum(1 for r in ev if r["anchored"]) / len(ev)
    m["anchored_share"] = round(anch, 2)
    if anch < T["anchored_must"]:
        issues.must(st, "P08", f"Only {anch * 100:.0f} % of events are anchored to words.", "Anchor events to the words they show; the picture must follow the voice.")
    # ---------------------------------------------------------------- P09 shot sizes
    sizes = [s["size"] for s in m["shots"]]
    m["distinct_sizes"] = sorted(set(sizes), key=SIZES.index)
    if len(set(sizes)) < T["sizes_min"]:
        issues.must(st, "P09", f"The film uses {len(set(sizes))} shot sizes ({', '.join(m['distinct_sizes']) or 'none'}).",
                    "Vary the framing: wide to show where we are, close for the action, extreme close for detail (at least 3 sizes).")
    run_sz, run_ids = None, []
    for sc in P.scenes:
        sh = [s for s in m["shots"] if s["scene"] == sc["id"]]
        if not sh:
            continue
        moving = any(s["move"] not in ("static", "", "none", "hold") for s in sh) or len({s["size"] for s in sh}) > 1
        sz = sh[-1]["size"]
        if not moving and sz == run_sz:
            run_ids.append(sc["id"])
        else:
            run_sz, run_ids = (sz, [sc["id"]]) if not moving else (None, [])
        if len(run_ids) >= T["same_size_run"]:
            issues.must(st, "P09", f"Scenes {run_ids} are all {sz} with no camera move.", "Change the shot size between them or move the camera.", scene=run_ids[-1], t0=sc["start"])
            run_sz, run_ids = None, []
        if sc["dur"] > T["long_scene_s"] and not moving:
            issues.should(st, "P09", f"Scene '{sc['id']}' ({sc['dur']:.1f} s) holds one {sz} shot without moving.", "Push in, pull out or cut to a new size on a key word.", scene=sc["id"], t0=sc["start"])
    # ---------------------------------------------------------------- P10 the film has someone to follow, and the lead acts often
    m["cast"] = {w: {"acts": a, "seconds": round(s, 2)} for w, (a, s) in cast_time.items()}
    if not cast_time:
        issues.should(st, "P10", "No character appears in the film.", "Give the story a character with a face (a cell, a fish, an astronaut) and let it react.")
    else:
        lead = next((c for c in (P.plan.get("characters") or []) if c in cast_time), None) or max(cast_time, key=lambda w: cast_time[w][1])
        a, s = cast_time[lead]
        m["lead"] = lead
        if s and a / s < T["act_rate_must"]:
            issues.must(st, "P10", f"The lead, '{lead}', acts {a} times in {s:.1f} s on screen (one per {s / max(a, 1):.1f} s).",
                        f"The lead must act or react at least once per {1 / T['act_rate_must']:.1f} s on screen (my films: about one per 3 s).")
        elif s and a / s < T["act_rate_should"]:
            issues.should(st, "P10", f"The lead, '{lead}', acts once per {s / max(a, 1):.1f} s on screen.", "Aim for one act or reaction per 3 s.")
    # ---------------------------------------------------------------- P11 sound per event (a face may react in silence; things that happen make a sound)
    cues = [norm_cue(r["sfx"]) for r in pic if r.get("sfx")]
    need_cue = [r for r in pic if r["kind"] != "react"]
    cover = sum(1 for r in need_cue if r.get("sfx")) / len(need_cue) if need_cue else 0
    m["sfx_cover"] = round(cover, 2)
    if cover < T["sfx_cover_must"]:
        miss = [f"{r['scene']} #{r['i']} '{r['word'] or round(r['t'], 2)}'" for r in need_cue if not r.get("sfx")]
        issues.must(st, "P11", f"{cover * 100:.0f} % of picture events (reactions aside) have a sound cue; missing: {', '.join(miss[:8])}" + (" ..." if len(miss) > 8 else "") + ".",
                    "Give every action, appearance, effect and cut its own cue, timed with the same word (a gulp for a swallow, a clank for a bite).")
    if cues:
        top, cnt = Counter(cues).most_common(1)[0]
        m["sfx_top"] = [top, cnt, len(cues)]
        if cnt / len(cues) > T["sfx_top_share_must"]:
            issues.must(st, "P11", f"'{top}' is the cue for {cnt} of {len(cues)} picture events.", "Design a sound for each action; one stock sound for everything reads as generic.")
        if len(set(cues)) / len(cues) < T["sfx_distinct_should"]:
            issues.should(st, "P11", f"{len(set(cues))} distinct cue names for {len(cues)} cued events.", "Vary the cues.")
    # ---------------------------------------------------------------- P13 first event, P14 title
    if pic and min(r["t"] for r in pic) > T["first_event_film_s"]:
        issues.must(st, "P13", f"The first picture event is at {min(r['t'] for r in pic):.2f} s.", "Start on motion: something moves in the first second.", scene=P.scenes[0]["id"], t0=0.0)
    last = P.scenes[-1]
    titles = [r for r in ev if r["scene"] == last["id"] and r["kind"] == "title"]
    if not titles:
        issues.should(st, "P14", "The last scene has no title event.", "End on the title card (kind 'title'), held at least 2 s.", scene=last["id"])
    elif P.film_len - min(r["t"] for r in titles) < T["title_hold_s"]:
        issues.should(st, "P14", f"The title appears {P.film_len - min(r['t'] for r in titles):.1f} s before the end.", "Hold it at least 2 s.", scene=last["id"])
    return m


def first_verb(text):
    t = str(text).lower().strip()
    for v in sorted(POSE_VERBS, key=len, reverse=True):
        if t.startswith(v):
            return v
    return t.split()[0] if t.split() else ""


def resolve_holds(P, issues):
    """Declared holds: stretches accepted as still or empty, each with a reason (my REVIEW.md 'accepted' list)."""
    out, total, speak = [], 0.0, 0.0
    for h in P.plan.get("holds", []) or []:
        try:
            a, b = float(h["from"]), float(h["to"])
        except (KeyError, TypeError, ValueError):
            issues.must("plan", "P16", f"Hold {h} needs numeric 'from' and 'to' (film seconds).", "Give from, to and why.")
            continue
        if not str(h.get("why", "")).strip() or b <= a:
            issues.must("plan", "P16", f"Hold {a:.2f}-{b:.2f} s has no reason or no length.", "Say why the stillness or emptiness is the point (my rule: darkness that is the subject, a breath before a punchline).", t0=a, t1=b)
            continue
        out.append((a, b, h["why"]))
        total += b - a
        for _k, t, e, _l in P.words:
            speak += max(0.0, min(b, e) - max(a, t))
    if P.film_len and total > T["holds_max_share"] * P.film_len:
        issues.must("plan", "P16", f"Holds total {total:.1f} s ({total / P.film_len * 100:.0f} % of the film).", "Fix the stillness instead of declaring it; holds are for the few beats where it is the point.")
    elif speak > T["holds_voice_should_s"]:
        issues.should("plan", "P16", f"Holds cover {speak:.1f} s of narration.", "Keep accepted stillness out of the narration where you can.")
    return out


def load_code(P):
    comp = P.root / "compositions"
    if not comp.exists():
        return None
    return {s["id"]: (comp / f"{s['id']}.html").read_text() if (comp / f"{s['id']}.html").exists() else None for s in P.scenes}
