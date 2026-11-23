"""Shared timing for the audio scripts: the same word times and scene starts the animation uses."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))  # vendored sound_effects.py sits beside this file

T = json.loads((ROOT / "assets" / "timing.json").read_text())
FILM = T["film"]
SCENE = T["scenes"]


def w(word: str, n: int = 1, after: float = 0.0) -> float:
    """Film time of the n-th occurrence of `word` at or after `after` (same rule as KIT.t)."""
    key = "".join(ch for ch in word.lower() if ch.isalnum())
    k = 0
    for wk, t, _e in T["words"]:
        if t >= after and wk == key:
            k += 1
            if k == n:
                return t
    raise KeyError(word)


def s(name: str) -> float:
    return SCENE[name]["start"]
