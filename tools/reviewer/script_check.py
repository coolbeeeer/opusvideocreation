"""Stage 1: the script. Reads film.json and SCRIPT.md (and the measured voice timing once it exists).

What a good Short script has here (the three vertical films in projects/ are the reference): a hook that lands in
the first four seconds, short sentences, one idea per line, about 150 words a minute, the viewer addressed as "you",
concrete numbers, a turn, a short last line that calls back, sources for every claim, and no generic narration.
"""
import math
import re

from common import Issues, key
from standard import CLICHES, GENERIC_FILLER, T

STOP = set("""a an the and or but so of to in on at by for with from into onto over under is are was were be been being it its
this that these those you your yours we our they their them he she his her i me my as if than then there here what which who
whom whose why how when where not no do does did done have has had can could would should will just about very really also
too only even still all any some every each one ones much many more most such own out up down off again ever""".split())
NUM_WORDS = set("""two three four five six seven eight nine ten eleven twelve twenty thirty forty fifty hundred hundreds
thousand thousands million millions billion billions trillion half twice double triple percent dozen""".split())
TURN = re.compile(r"\b(but|yet|however|instead|except|turns out|or better|actually|until)\b", re.I)
INTRO = re.compile(r"\b(call|called|calls|known as|named|this is|that is|means|is a|are a)\b|:", re.I)


def words_of(text):
    return [w for w in re.findall(r"[A-Za-z0-9'’]+", text)]


def run(P, issues: Issues):
    st = "script"
    m = {}                                            # measurements for the report
    if not P.film:
        issues.must(st, "S01", "film.json is missing: the reviewer cannot read the script.",
                    "Write film.json with `lines` (text + pause) and `scenes` (id + lines), as in projects/black-hole-short/film.json.")
        return m
    lines = P.lines
    if not lines or not all(ln["text"].strip() for ln in lines):
        issues.must(st, "S01", "film.json has no lines, or a line without text.", "Give every line its narration text.")
        return m
    # ---------------------------------------------------------------- S01 structure
    covered = []
    for s in P.film.get("scenes", []):
        covered += list(s.get("lines", []))
    n = len(lines)
    if sorted(covered) != list(range(1, n + 1)) or covered != sorted(covered):
        issues.must(st, "S01", f"film.json scenes do not cover lines 1-{n} exactly once and in order (they list {covered}).",
                    "Assign every line to exactly one scene, in narration order.")
    # ---------------------------------------------------------------- numbers we need
    tokens = P.display_tokens()
    nwords = len(tokens)
    pauses = [ln["pause"] for ln in lines]
    open_s, tail_s = float(P.film.get("open", 0.6)), float(P.film.get("tail", 2.8))
    measured = P.timing is not None and len(P.words) == nwords
    if measured:
        film_len = P.film_len
        speech = sum(e - t for _k, t, e, _l in P.words)
    else:
        speech = nwords / T["speech_wps"]
        film_len = open_s + speech + sum(pauses[:-1]) + tail_s
    wpm = nwords / film_len * 60
    sents = P.sentences()
    slen = [len(s["text"].split()) for s in sents]
    m.update({"words": nwords, "lines": n, "sentences": len(sents), "film_s": round(film_len, 2), "measured": measured,
              "wpm": round(wpm, 1), "sentence_max": max(slen), "sentence_mean": round(sum(slen) / len(slen), 1)})
    # ---------------------------------------------------------------- S02 sources
    sp = P.root / "SCRIPT.md"
    if not sp.exists():
        issues.must(st, "S02", "SCRIPT.md is missing: no shot table, no accuracy notes, no sources.",
                    "Write SCRIPT.md like projects/black-hole-short/SCRIPT.md: narration table, shots, and an accuracy note with a source link for every claim.")
    else:
        txt = sp.read_text()
        urls = sorted(set(re.findall(r"https?://[^\s)\]>]+", txt)))
        need = max(T["sources_min"], math.ceil(n / 2))
        m["sources"] = len(urls)
        if not re.search(r"^#+\s*(accuracy|sources|fact)", txt, re.I | re.M):
            issues.must(st, "S02", "SCRIPT.md has no 'Accuracy notes' (or 'Sources') section.",
                        "Add an '## Accuracy notes' section: one numbered note per claim, each with its source link.")
        if len(urls) < need:
            issues.must(st, "S02", f"SCRIPT.md links {len(urls)} unique sources; a {n}-line script needs at least {need}.",
                        "Add a source link (official agency, journal, encyclopedia) to every factual claim's accuracy note.")
        sec = re.split(r"^#+\s*(?:accuracy|sources)[^\n]*$", txt, flags=re.I | re.M)
        if len(sec) > 1:
            notes = len(re.findall(r"^\s*(?:\d+\.|[-*])\s+\S", sec[1].split("\n#")[0], re.M))
            m["accuracy_notes"] = notes
            if notes < math.ceil(n / 2):
                issues.must(st, "S02", f"Only {notes} accuracy notes for {n} lines.",
                            "Write one accuracy note per line that makes a claim: what it says, what the source says, what is simplified.")
    # ---------------------------------------------------------------- S03 length, S04 pace
    est = "" if measured else " (estimated; the voice is not recorded yet)"
    if not (T["film_min_s"] <= film_len <= T["film_max_s"]):
        issues.must(st, "S03", f"The film is {film_len:.1f} s{est}; a Short must be {T['film_min_s']:.0f}-{T['film_max_s']:.0f} s.",
                    "Cut words (not voice speed) until it fits: remove the weakest sentence first." if film_len > T["film_max_s"] else "Add a beat: the story needs room for its turn and payoff.")
    elif not (T["film_target"][0] <= film_len <= T["film_target"][1]):
        issues.should(st, "S03", f"The film is {film_len:.1f} s{est}; the target is {T['film_target'][0]:.0f}-{T['film_target'][1]:.0f} s.",
                      "Aim for about 50 s: long enough for a hook, a turn and a payoff.")
    lo, hi = T["wpm_must"]
    if not (lo <= wpm <= hi):
        issues.must(st, "S04", f"Pace is {wpm:.0f} words per minute of film{est}; it must be {lo:.0f}-{hi:.0f}.",
                    "Too fast: cut words and give the picture time. Too slow: tighten pauses or cut dead lines." if wpm > hi else "Tighten the script or the pauses; long silences read as dead air.")
    elif not (T["wpm_should"][0] <= wpm <= T["wpm_should"][1]):
        issues.should(st, "S04", f"Pace is {wpm:.0f} words per minute{est}; my films run 146-165.", "Adjust words or pauses toward about 150 words per minute.")
    # ---------------------------------------------------------------- S05 hook
    first = sents[0]
    fw = len(first["text"].split())
    if measured:
        hook_end = P.words[first["i1"]][2]
    else:
        hook_end = open_s + fw / T["speech_wps"]
    m["hook_words"], m["hook_end_s"] = fw, round(hook_end, 2)
    if fw > T["hook_max_words"] or hook_end > T["hook_max_s"]:
        issues.must(st, "S05", f"The hook \"{first['text']}\" is {fw} words and ends at {hook_end:.1f} s{est}.",
                    f"Open with one short sentence ({T['hook_max_words']} words or fewer) that is over by {T['hook_max_s']:.1f} s: a question or a surprising claim about the viewer.",
                    t0=0.0, t1=hook_end)
    l1 = lines[0]["text"].lower()
    if not ("?" in lines[0]["text"] or re.search(r"\byou(r|'re|'d)?\b", first["text"], re.I) or any(w.lower() in NUM_WORDS or w.isdigit() for w in words_of(first["text"]))):
        issues.should(st, "S05", f"The hook \"{first['text']}\" asks no question, does not speak to 'you' and has no number.",
                      "Make the first line a question, a claim about the viewer, or a striking number.", t0=0.0)
    # ---------------------------------------------------------------- S06 sentence length
    for s, k in zip(sents, slen):
        t0 = P.words[s["i0"]][1] if measured else None
        if k > T["sentence_must"]:
            issues.must(st, "S06", f"Sentence of {k} words: \"{s['text']}\"", "Split it: every sentence start is a sync point for the picture.", t0=t0)
        elif k > T["sentence_should"]:
            issues.should(st, "S06", f"Sentence of {k} words: \"{s['text']}\"", "Consider splitting it into two.", t0=t0)
    if m["sentence_mean"] > T["sentence_mean_should"]:
        issues.should(st, "S06", f"Mean sentence length is {m['sentence_mean']} words.", "Shorter sentences: aim for 14 words on average or fewer.")
    # ---------------------------------------------------------------- S07 filler and cliches
    full = " ".join(ln["text"] for ln in lines)
    low = full.lower().replace("’", "'")
    for ph in GENERIC_FILLER:
        if ph in low:
            issues.must(st, "S07", f"Generic narration: \"{ph}\".", "Delete it and say the thing itself. Kurzgesagt never announces what the video will do.")
    for ph in CLICHES:
        if ph in low:
            issues.should(st, "S07", f"Cliche: \"{ph}\".", "Replace it with a concrete question or fact.")
    # ---------------------------------------------------------------- S08 you, S09 numbers, S10 turn
    you = len(re.findall(r"\byou(r|rs|'re|'d|'ll|'ve)?\b", low))
    nums = sum(1 for w in words_of(full) if w.lower() in NUM_WORDS or re.fullmatch(r"\d[\d,.]*", w))
    m["you"], m["numbers"] = you, nums
    if you < T["you_should"]:
        issues.should(st, "S08", f"The script says 'you/your' {you} times.", "Put the viewer in the story: what it means for them, in their body, in their day.")
    if nums < T["numbers_should"]:
        issues.should(st, "S09", f"Only {nums} concrete numbers or comparisons.", "Give scale: 'ten times as heavy as the Sun', 'your own body weight every day'.")
    if not TURN.search(full):
        issues.should(st, "S10", "No turn ('but', 'yet', 'or better' ...): the script is a list of facts.", "Build tension: set up an expectation, then turn it.")
    # ---------------------------------------------------------------- S11 ending
    last = lines[-1]["text"]
    lw = len(last.split())
    content = lambda t: {w for w in (key(x) for x in words_of(t)) if len(w) > 3 and w not in STOP}
    earlier = set()
    for ln in lines[:-1]:
        earlier |= content(ln["text"])
    earlier |= content(P.film.get("title", ""))
    if lw > 16:
        issues.should(st, "S11", f"The last line is {lw} words.", "End short: one sentence that lands the payoff.")
    if not (content(last) & earlier):
        issues.should(st, "S11", f"The last line \"{last}\" shares no key word with the rest of the script or the title.",
                      "Call back to the hook (the walk in the mitochondria film: 'every step you take').")
    if tail_s < T["tail_should"]:
        issues.should(st, "S11", f"Tail after the last word is {tail_s:.1f} s.", "Give the title at least 2 s after the last word (film.json 'tail').")
    # ---------------------------------------------------------------- S12 pauses
    for i, p in enumerate(pauses, 1):
        if i == n:
            if p > 0.05:
                issues.must(st, "S12", f"Line {n} (the last) has a {p} s pause after it.", "Set the last pause to 0; the tail holds the title.")
            continue
        if not (T["pause_must"][0] <= p <= T["pause_must"][1]):
            issues.must(st, "S12", f"Line {i} has a {p} s pause.", "Pauses between lines: 0.3-0.9 s (0.4 s inside one thought, 0.6-0.8 s after a punchline or before a transition).")
        elif not (T["pause_should"][0] <= p <= T["pause_should"][1]):
            issues.should(st, "S12", f"Line {i} has a {p} s pause.", "Use 0.3-0.9 s; see NOTES.md question 2 in projects/mitochondria-short.")
    # ---------------------------------------------------------------- S13 scenes
    sc_specs = P.film.get("scenes", [])
    if measured and P.scenes and P.scenes[0]["start"] is not None:
        durs = [(s["id"], s["dur"], s["start"]) for s in P.scenes]
    else:
        # estimate: words of the scene's lines at the speech rate plus their pauses
        durs, t = [], open_s
        for s in sc_specs:
            d = sum(len(lines[i - 1]["text"].split()) / T["speech_wps"] + lines[i - 1]["pause"] for i in s.get("lines", []) if 0 < i <= n)
            durs.append((s["id"], d, t))
            t += d
    m["scenes"] = len(durs)
    for sid, d, t0 in durs:
        if not (T["scene_must"][0] <= d <= T["scene_must"][1]):
            issues.must(st, "S13", f"Scene '{sid}' is {d:.1f} s{est}.", "Split a long scene at a sentence; merge a very short one into its neighbour.", scene=sid, t0=t0)
        elif not (T["scene_should"][0] <= d <= T["scene_should"][1]):
            issues.should(st, "S13", f"Scene '{sid}' is {d:.1f} s{est}.", "Scenes of 3-13 s keep the pace; consider splitting or merging.", scene=sid, t0=t0)
    if not (T["scenes_should"][0] <= len(durs) <= T["scenes_should"][1]):
        issues.should(st, "S13", f"{len(durs)} scenes.", "A 50 s Short reads best as 5-8 scenes.")
    # ---------------------------------------------------------------- S14 jargon
    for i, s in enumerate(sents):
        for w in words_of(s["text"]):
            if len(re.sub(r"[^A-Za-z]", "", w)) >= T["jargon_letters"]:
                ctx = s["text"] + " " + (sents[i - 1]["text"] if i else "")
                if not INTRO.search(ctx):
                    issues.should(st, "S14", f"'{w}' is not introduced: \"{s['text']}\"", "Introduce long technical words: 'Astronomers really call this spaghettification.'")
    # ---------------------------------------------------------------- S15 alignment quality
    if P.vo_words:
        heard = sum(1 for w in P.vo_words if w.get("src", "heard") == "heard") / max(1, len(P.vo_words))
        m["heard"] = round(heard, 3)
        if heard < T["heard_min"]:
            issues.must(st, "S15", f"align.py heard only {heard * 100:.0f} % of the script words; the rest are guessed.",
                        "Re-run vo.py and align.py; rewrite words the voice cannot say clearly. Picture cues hang on these times.")
    if P.timing and len(P.words) != nwords:
        issues.must(st, "S15", f"film.json has {nwords} words but assets/timing.json has {len(P.words)}.",
                    "The voice is out of date: run vo.py, align.py and build.py again.")
    return m
