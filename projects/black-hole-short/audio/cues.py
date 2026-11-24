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


def a(scene: str, word: str, n: int = 1) -> float:
    """Film time of the n-th `word` spoken at or after the start of `scene` (same rule as the scenes' at())."""
    return w(word, n, s(scene))


def phase_table(keys, t1, period=1.0, step=1 / 240):
    """Python twin of KH.phaseTable in lib/kit-human.js: a rate curve [[t, rate], ...], eased with smoothstep between
    keys and integrated, returned as phase(t) (seconds of "local" time when period = 1). The friend scene uses it for
    the astronaut's slowing time; the audio uses the same keys so the ticks and the tape-stop match the picture."""
    import numpy as np

    def rate(t):
        if t <= keys[0][0]:
            return keys[0][1]
        for (ta, ra), (tb, rb) in zip(keys, keys[1:]):
            if t <= tb:
                u = min(1.0, max(0.0, (t - ta) / (tb - ta)))
                return ra + (rb - ra) * u * u * (3 - 2 * u)
        return keys[-1][1]

    n = int(np.ceil(t1 / step)) + 2
    P = np.zeros(n)
    for i in range(1, n):
        P[i] = P[i - 1] + rate((i - 0.5) * step) * step / period
    grid = np.arange(n) * step
    phase = lambda t: np.interp(np.maximum(0, t), grid, P)
    phase.rate = rate
    return phase


def friend_time():
    """The friend's view of your clock: the keys used in compositions/friend.html."""
    S0, D = s("friend"), SCENE["friend"]["dur"]
    t_slow, t_froz = a("friend", "slow") - S0 - 0.25, a("friend", "frozen") - S0 - 0.05
    return phase_table([[0, 1], [t_slow, 1], [t_froz + 0.2, 0], [D, 0]], D + 1), S0, t_slow, t_froz
