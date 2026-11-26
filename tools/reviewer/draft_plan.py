"""Draft a plan.json from a finished project's code: the scene files' word anchors and the cue sheet's sounds.

    python tools/reviewer/review.py draft-plan projects/<film> [--out plan.draft.json]

Use it for films that were built without a plan. It finds every timeline call that starts on a word
(tl.to / fromTo / set / K.show / K.camTo with at("word") or a variable set from at("word")), guesses the kind from
the call, and attaches the cue from audio/sfx_cues.py that uses the same scene and word. It cannot know who acts,
where things are on screen, or the shot sizes: those fields are written as "TODO" and stage 2 rejects the plan
until they are filled in. A draft is a starting point, never a finished plan.
"""
import json
import re
from pathlib import Path

from common import key

AT = r'at\(\s*"([^"]+)"\s*(?:,\s*(\d+))?\s*\)'
OFF = r'(?:\s*([+-])\s*([0-9]*\.?[0-9]+))?'
VAR_DEF = re.compile(r'\b([A-Za-z_]\w*)\s*=\s*' + AT + OFF + r'\s*[,;\n)]')
REACT_PROPS = {"fear", "calm", "happy", "panic", "worry", "wave", "shrug", "nod", "wake", "smile", "heart", "brow", "eye", "open", "mouth", "lid"}
CAM_PROPS = {"cs", "zoom", "cam", "lens", "pull", "push", "s", "px", "py"}
EFFECT_PROPS = {"vig", "glow", "flare", "flash", "sparks", "sparkle", "red", "fade", "rays", "dna", "shelter", "flex", "work"}


def split_args(s, start):
    """Arguments of the call whose '(' is at s[start]; returns (list of argument strings, end index)."""
    depth, i, args, cur = 0, start, [], []
    quote = None
    while i < len(s):
        ch = s[i]
        if quote:
            cur.append(ch)
            if ch == quote and s[i - 1] != "\\":
                quote = None
        elif ch in "\"'`":
            quote = ch
            cur.append(ch)
        elif ch in "([{":
            depth += 1
            if depth > 1:
                cur.append(ch)
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                args.append("".join(cur).strip())
                return args, i
            cur.append(ch)
        elif ch == "," and depth == 1:
            args.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    return args, i


def parse_time(expr, vars_):
    """('word', n, offset) for at("word") +- x or a variable set from it; ('time', t) for a number; None otherwise."""
    expr = expr.strip()
    m = re.fullmatch(AT + OFF, expr)
    if m:
        off = float(m.group(4) or 0) * (-1 if m.group(3) == "-" else 1)
        return ("word", m.group(1), int(m.group(2) or 1), off)
    m = re.fullmatch(r'([A-Za-z_]\w*)' + OFF, expr)
    if m and m.group(1) in vars_:
        w, n, off0 = vars_[m.group(1)]
        off = float(m.group(3) or 0) * (-1 if m.group(2) == "-" else 1)
        return ("word", w, n, off0 + off)
    m = re.fullmatch(r'[0-9]*\.?[0-9]+', expr)
    if m:
        return ("time", float(expr))
    return None


def guess_kind(call, args, labels):
    if call in ("K.show",):
        return "label", labels.get(args[1].strip(), "")
    if call == "K.camTo":
        return "camera", ""
    props = set(re.findall(r'([A-Za-z_]\w*)\s*:', args[1] if len(args) > 1 else ""))
    target = args[0] if args else ""
    if props & REACT_PROPS:
        return "react", ""
    if props & CAM_PROPS and target in ("st", "S.cam", "cam"):
        return "camera", ""
    if props & EFFECT_PROPS:
        return "effect", ""
    if re.search(r"\b(card|big|title|sub|bar)\b", target):
        return "title", ""
    return "move", ""


def scene_events(src):
    vars_ = {}
    for m in VAR_DEF.finditer(src):
        off = float(m.group(5) or 0) * (-1 if m.group(4) == "-" else 1)
        vars_[m.group(1)] = (m.group(2), int(m.group(3) or 1), off)
    labels = {}
    for m in re.finditer(r'const\s+([A-Za-z_]\w*)\s*=\s*(?:S\.cam\.pin\()?K\.(?:tag|callout)\([^{]*\{\s*text:\s*"([^"]+)"', src):
        labels[m.group(1)] = m.group(2)
    out = []
    for m in re.finditer(r'\b(tl\.to|tl\.fromTo|tl\.set|K\.show|K\.camTo)\(', src):
        call = m.group(1)
        args, _ = split_args(src, m.end() - 1)
        if call == "K.show" and len(args) >= 3:
            texpr = args[2]
        elif call == "K.camTo" and len(args) >= 3:
            texpr = args[2]
        elif call == "tl.fromTo" and len(args) >= 4:
            texpr = args[3]
        elif call in ("tl.to", "tl.set") and len(args) >= 3:
            texpr = args[2]
        else:
            continue
        tm = parse_time(texpr, vars_)
        if tm is None:
            continue
        kind, text = guess_kind(call, [a for a in args], labels)
        line = src.count("\n", 0, m.start()) + 1
        ev = {"kind": kind, "_code": f"line {line}: {src[m.start():m.start() + 90].splitlines()[0]}"}
        if tm[0] == "word":
            ev.update({"word": tm[1], "n": tm[2], "offset": round(tm[3], 3)})
        else:
            ev["time"] = tm[1]
        if kind == "label":
            ev["text"] = text or "TODO"
        else:
            ev["does"] = "TODO: what the viewer sees"
        if kind not in ("label", "title", "camera"):
            ev["where"] = "TODO: [x0, y0, x1, y1] in film pixels, or a region name"
        if kind in ("act", "react"):
            ev["who"] = "TODO"
        out.append(ev)
    # also every remaining at("word") anchor that drives frame() code (ripples, flows): kind unknown
    used = {(e.get("word"), e.get("n")) for e in out}
    for m in re.finditer(AT + OFF, src):
        w, n = m.group(1), int(m.group(2) or 1)
        if (w, n) not in used:
            used.add((w, n))
            off = float(m.group(4) or 0) * (-1 if m.group(3) == "-" else 1)
            line = src.count("\n", 0, m.start()) + 1
            out.append({"kind": "move", "word": w, "n": n, "offset": round(off, 3), "does": "TODO: what the viewer sees",
                        "where": "TODO: [x0, y0, x1, y1] in film pixels, or a region name", "_code": f"line {line}: drives frame() code"})
    return out


def cue_map(sfx_src):
    """{(scene, word key, n): [cue names]} from audio/sfx_cues.py lines like add(fx.gulp(...), a("origin", "swallowed") + 0.3)."""
    cues = {}
    for ln in sfx_src.splitlines():
        if ln.lstrip().startswith("#"):
            continue
        names = re.findall(r'(?:add\(\s*(?:fx\.)?([A-Za-z_]\w*)\(|^\s*(pop_word)\()', ln)
        name = next((a or b for a, b in names if (a or b) not in ("fade_io", "np", "fx")), None)
        for m in re.finditer(r'a\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*(?:,\s*(\d+))?\s*\)', ln):
            cues.setdefault((m.group(1), key(m.group(2)), int(m.group(3) or 1)), []).append(name or "cue")
    return cues


def draft(P, out_path):
    comp = P.root / "compositions"
    sfx = P.root / "audio" / "sfx_cues.py"
    cues = cue_map(sfx.read_text()) if sfx.exists() else {}
    plan = {"version": 1, "_draft": "Generated by tools/reviewer/draft_plan.py from the scene code. Fill every TODO, delete events that are not picture events, add who/where for acts and the shot sizes.",
            "characters": [], "holds": [], "scenes": []}
    for sc in P.scenes:
        f = comp / f"{sc['id']}.html"
        evs = scene_events(f.read_text()) if f.exists() else []
        for ev in evs:
            if ev.get("word"):
                c = cues.get((sc["id"], key(ev["word"]), ev.get("n", 1)))
                if c:
                    ev["sfx"] = c[0]
        evs.sort(key=lambda e: (P.resolve(sc["id"], e)[0] or 1e9))
        plan["scenes"].append({"id": sc["id"], "transition": "TODO" if sc is not P.scenes[0] else "cold open",
                               "shots": [{"time": 0, "size": "TODO", "move": "TODO"}], "events": evs})
    Path(out_path).write_text(json.dumps(plan, indent=1))
    n = sum(len(s["events"]) for s in plan["scenes"])
    return n
