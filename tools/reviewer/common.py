"""Shared pieces of the film reviewer: loading a project, resolving word anchors, issues, hashes.

A project is a film folder made with this repo's pipeline (projects/<film>/):
  film.json            script lines with pauses, scenes, size, fps          (stage 1 needs this)
  SCRIPT.md            narration, shot table, accuracy notes with sources   (stage 1)
  assets/timing.json   measured word times and scene times (build.py)       (stages 2 and 3)
  assets/vo_words.json measured words with their line numbers (align.py)    (optional, sharper line mapping)
  plan.json            the event list and shot plan (see PLAN.md)           (stages 2 and 3)
  assets/vo.wav, sfx.wav, music.wav   the mixed stems (audio/mix.py)        (stage 3)
  renders/*.mp4        the film                                             (stage 3)
The reviewer only reads these. It writes nothing outside its output folder.
"""
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

VERSION = "1.0"
REVIEWER_DIR = Path(__file__).resolve().parent


def key(word: str) -> str:
    """The word key used everywhere in the pipeline (build.py, kit.js K.t): lower case, letters and digits only."""
    return re.sub(r"[^a-z0-9]", "", word.lower())


def fmt_t(t, fps=30):
    """'12.30 s (frame 369)': times in the fix list always carry the frame number too."""
    if t is None:
        return ""
    return f"{t:.2f} s (frame {int(round(t * fps))})"


def fmt_span(t0, t1, fps=30):
    if t0 is None:
        return ""
    if t1 is None or abs(t1 - t0) < 1e-6:
        return fmt_t(t0, fps)
    return f"{t0:.2f}-{t1:.2f} s (frames {int(round(t0 * fps))}-{int(round(t1 * fps))})"


@dataclass
class Issue:
    stage: str              # "script", "plan" or "film"
    level: str              # "must" (blocks approval) or "should" (listed, does not block)
    rule: str               # rule id from STANDARD.md, e.g. "F07"
    problem: str            # what is wrong, measured
    fix: str                # what to do, concrete
    scene: str = ""
    t0: float = None        # film seconds
    t1: float = None

    def to_dict(self):
        return asdict(self)


class Issues(list):
    def must(self, stage, rule, problem, fix, scene="", t0=None, t1=None):
        self.append(Issue(stage, "must", rule, problem, fix, scene, t0, t1))

    def should(self, stage, rule, problem, fix, scene="", t0=None, t1=None):
        self.append(Issue(stage, "should", rule, problem, fix, scene, t0, t1))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def reviewer_hash() -> str:
    """One hash over the reviewer's own code and rules: an approval only counts for the reviewer that gave it."""
    h = hashlib.sha256()
    for p in sorted(REVIEWER_DIR.glob("*.py")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


SENT_SPLIT = re.compile(r"(?<=[.?!])\s+")


class Project:
    """Everything the stages read, loaded once. Missing parts are None; each stage reports what it needs."""

    def __init__(self, root, plan_path=None):
        self.root = Path(root).resolve()
        self.name = self.root.name
        self.film = self._json("film.json")
        self.timing = self._json("assets/timing.json")
        self.vo_words = self._json("assets/vo_words.json")
        self.vo_timing = self._json("assets/vo_timing.json")
        self.plan_path = Path(plan_path).resolve() if plan_path else self.root / "plan.json"
        self.plan = json.loads(self.plan_path.read_text()) if self.plan_path.exists() else None
        f = self.film or {}
        self.W = int(f.get("width", (self.timing or {}).get("W", 1920)))
        self.H = int(f.get("height", (self.timing or {}).get("H", 1080)))
        self.fps = float(f.get("fps", 30))
        self.vertical = self.H > self.W
        self.lines = self._lines()
        self.words = []                      # [(key, t, e, line)] measured, in order
        if self.timing:
            wl = [w.get("line") for w in (self.vo_words or [])]
            for i, (k, t, e) in enumerate(self.timing["words"]):
                self.words.append((k, float(t), float(e), wl[i] if i < len(wl) else None))
        self.scenes = []                     # [{"id", "start", "end", "dur", "lines"}] in film order
        if self.timing:
            spec = {s["id"]: s.get("lines", []) for s in f.get("scenes", [])}
            for sid, sc in self.timing["scenes"].items():
                self.scenes.append({"id": sid, "start": float(sc["start"]), "end": float(sc["end"]), "dur": float(sc["dur"]), "lines": spec.get(sid, [])})
        elif f.get("scenes"):
            self.scenes = [{"id": s["id"], "start": None, "end": None, "dur": None, "lines": s.get("lines", [])} for s in f["scenes"]]
        self.film_len = float(self.timing["film"]) if self.timing else None
        self.vo_end = float(self.timing.get("vo_end", 0)) if self.timing else None

    def _json(self, rel):
        p = self.root / rel
        return json.loads(p.read_text()) if p.exists() else None

    def _lines(self):
        """Normalise both film.json formats to [{"text", "pause"}]: the vertical films' line objects and the
        template's lists of sentences."""
        f = self.film or {}
        out = []
        for ln in f.get("lines", []):
            if isinstance(ln, dict):
                out.append({"text": ln.get("text", ""), "pause": float(ln.get("pause", f.get("gap_line", 0.5)))})
            elif isinstance(ln, list):
                out.append({"text": " ".join(ln), "pause": float(f.get("gap_line", 0.34))})
            else:
                out.append({"text": str(ln), "pause": float(f.get("gap_line", 0.5))})
        return out

    # ---------------------------------------------------------------- words and anchors
    def word_index_lines(self):
        """Line number (1-based) of every word, from vo_words.json, else by counting the tokens of each line."""
        if self.words and all(w[3] is not None for w in self.words):
            return [w[3] for w in self.words]
        out = []
        for i, ln in enumerate(self.lines, 1):
            out += [i] * len(ln["text"].split())
        return out

    def sentences(self):
        """[{"line", "text", "i0", "i1"}]: sentences with the indices of their first and last word (display tokens)."""
        out, i = [], 0
        for li, ln in enumerate(self.lines, 1):
            for s in SENT_SPLIT.split(ln["text"].strip()):
                n = len(s.split())
                if n:
                    out.append({"line": li, "text": s, "i0": i, "i1": i + n - 1})
                    i += n
        return out

    def scene(self, sid):
        return next((s for s in self.scenes if s["id"] == sid), None)

    def scene_at(self, t):
        for s in self.scenes:
            if s["start"] is not None and s["start"] <= t < s["end"]:
                return s["id"]
        return self.scenes[-1]["id"] if self.scenes else ""

    def resolve(self, sid, ev):
        """Film time of a plan event or shot. Anchors follow the scenes' at(): the n-th occurrence of the word at or
        after the scene start, plus the offset. Returns (time, error message or None, word index or None)."""
        sc = self.scene(sid)
        if sc is None or sc["start"] is None:
            return None, f"scene '{sid}' has no measured times (run build.py)", None
        if "time" in ev and ev.get("word") in (None, ""):
            try:
                return sc["start"] + float(ev["time"]), None, None
            except (TypeError, ValueError):
                return None, f"time '{ev.get('time')}' is not a number", None
        w = ev.get("word")
        if not w:
            return None, "no anchor: give it a 'word' (or a 'time' if it falls in a pause)", None
        k, n = key(str(w)), int(ev.get("n", 1) or 1)
        c = 0
        for i, (wk, t, _e, _l) in enumerate(self.words):
            if t >= sc["start"] - 1e-6 and wk == k:
                c += 1
                if c == n:
                    return t + float(ev.get("offset", 0) or 0), None, i
        return None, f"word '{w}' (occurrence {n}) is not spoken in or after scene '{sid}'", None

    def spoken_between(self, t0, t1, limit=14):
        ws = [self.words[i] for i in range(len(self.words)) if t0 <= self.words[i][1] <= t1]
        disp = self.display_tokens()
        idx = [i for i in range(len(self.words)) if t0 <= self.words[i][1] <= t1]
        text = " ".join(disp[i] if i < len(disp) else self.words[i][0] for i in idx[:limit])
        return text + (" ..." if len(idx) > limit else ""), ws

    def narration(self, t0, t1):
        """'while the narration says "..."', or 'in a pause' / 'after the last word' when nothing is said."""
        said, _ = self.spoken_between(t0, t1)
        if said:
            return f'while the narration says "{said}"'
        return "after the last word" if self.words and t0 >= self.words[-1][2] else "in a pause"

    def display_tokens(self):
        return [tok for ln in self.lines for tok in ln["text"].split()]

    def find_mp4(self):
        r = self.root / "renders"
        c = sorted(r.glob("*.mp4"), key=lambda p: p.stat().st_mtime) if r.exists() else []
        return c[-1] if c else None
