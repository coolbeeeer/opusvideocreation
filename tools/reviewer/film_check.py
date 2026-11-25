"""Stage 3: the finished film. Measures the MP4 (and the stems) against the plan and the word times.

Everything here is measured, because an agent cannot watch or listen. The measures extend tools/frame_stats.py
(empty background, motion) and tools/verify_render.py (specs, loudness, sync, black frames) with:
  - picture onsets: places in the frame that were still for 0.4 s and then change (something appears, moves, reacts),
    found on a grid of 24 px blocks with the caption band masked out, so captions can never count as picture;
  - per planned event: is there an onset at its time (and inside its `where` box)?
  - the word lock: are onsets more frequent at the planned word times than elsewhere? (a permutation test against
    the same plan shifted at random, so a film that moves all the time cannot pass by chance);
  - sound: an onset in the effects stem at every cued event, and how many events share one identical sound.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from scipy import ndimage, signal, stats
from scipy.io import wavfile

from common import Issues, fmt_span
from standard import KINDS_PICTURE, T

FFMPEG = os.environ.get("HYPERFRAMES_FFMPEG_PATH") or shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = os.environ.get("HYPERFRAMES_FFPROBE_PATH") or shutil.which("ffprobe") or "ffprobe"
HF = os.environ.get("REVIEWER_HYPERFRAMES", "hyperframes@0.9.56")
AFPS = 15            # analysis frame rate for onsets
MFPS = 10            # motion frame rate (frames 0.1 s apart, as tools/frame_stats.py)
CB = 6               # coarse block in analysis pixels (analysis = film / 4, so 24 film px)
FB = 3               # fine block (12 film px), used inside `where` boxes


def run_cmd(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def frames(mp4, fps, w, h, pix="gray"):
    """Stream decoded frames (uint8) without holding the whole film in memory."""
    ch = 1 if pix == "gray" else 3
    p = subprocess.Popen([FFMPEG, "-v", "error", "-i", str(mp4), "-vf", f"fps={fps},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", pix, "-"],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = w * h * ch
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        a = np.frombuffer(buf, np.uint8)
        yield a.reshape(h, w) if ch == 1 else a.reshape(h, w, 3)
    p.wait()


def runs_of(mask, rate, t0=0.0):
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            out.append((t0 + i / rate, t0 + j / rate))
            i = j
        else:
            i += 1
    return out


def ev_name(r):
    """How the fix list names an event's anchor: 'word' (2nd), or the time for events placed by time."""
    if r.get("word"):
        return f"'{r['word']}'" + (f" ({r['n']}.)" if int(r.get("n") or 1) > 1 else "")
    return f"placed at {r['t']:.2f} s"


def boxes_overlap(a, b):
    """Two (x0, y0, x1, y1) boxes share some area."""
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def overlaps_hold(a, b, holds, need=0.5):
    if b <= a:
        return False
    cov = sum(max(0.0, min(b, h[1]) - max(a, h[0])) for h in holds)
    return cov >= need * (b - a)


class Film:
    """All measurements of one MP4, computed once."""

    def __init__(self, mp4, P, plan_m):
        self.mp4, self.P = Path(mp4), P
        self.W, self.H = P.W, P.H
        self.aw, self.ah = (self.W // 4) // 6 * 6, (self.H // 4) // 6 * 6
        self.holds = plan_m.get("holds", []) if plan_m else []
        self.events = plan_m.get("events", []) if plan_m else []
        self.m = {}

    # ---------------------------------------------------------------- container, loudness, black, sync
    def probe(self):
        info = json.loads(run_cmd([FFPROBE, "-v", "error", "-show_entries", "stream=codec_type,codec_name,pix_fmt,width,height,r_frame_rate,nb_frames,sample_rate,channels",
                                   "-show_entries", "format=duration,size", "-of", "json", str(self.mp4)]).stdout or "{}")
        v = next((s for s in info.get("streams", []) if s["codec_type"] == "video"), None)
        a = next((s for s in info.get("streams", []) if s["codec_type"] == "audio"), None)
        num, den = map(int, v["r_frame_rate"].split("/")) if v else (0, 1)
        self.fps = num / den if den else 0
        self.dur = float(info.get("format", {}).get("duration", 0))
        self.m["specs"] = {"video": v and {k: v.get(k) for k in ("codec_name", "pix_fmt", "width", "height", "nb_frames")}, "fps": round(self.fps, 3),
                           "duration": round(self.dur, 3), "audio": a and {k: a.get(k) for k in ("codec_name", "sample_rate", "channels")},
                           "size_mb": round(int(info.get("format", {}).get("size", 0)) / 1e6, 1)}
        return v, a

    def loudness(self):
        r = run_cmd([FFMPEG, "-nostats", "-i", str(self.mp4), "-map", "0:a", "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
        I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)
        TP = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", r)
        LRA = re.findall(r"LRA:\s+([\d.]+) LU", r)
        self.m["loudness"] = {"I": float(I[-1]) if I else None, "true_peak": float(TP[-1]) if TP and TP[-1] != "-inf" else None, "LRA": float(LRA[-1]) if LRA else None}

    def blacks(self):
        bd = run_cmd([FFMPEG, "-v", "info", "-i", str(self.mp4), "-vf", "blackdetect=d=0.05:pix_th=0.04", "-an", "-f", "null", "-"]).stderr
        self.m["black"] = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bd)]
        lw, lh = (68, 120) if self.H > self.W else (120, 68)
        lum = np.array([f.mean() for f in frames(self.mp4, self.fps or 30, lw, lh)])
        flash = []
        for i in range(1, len(lum) - 1):
            if abs(lum[i] - lum[i - 1]) > 35 and abs(lum[i] - lum[i + 1]) > 35 and abs(lum[i - 1] - lum[i + 1]) < 10:
                flash.append(i / (self.fps or 30))
        self.m["flash"] = flash

    def stems(self):
        A = self.P.root / "assets"
        out = {}
        for n in ("vo", "sfx", "music"):
            p = A / f"{n}.wav"
            if p.exists():
                sr, x = wavfile.read(p)
                x = x.astype(np.float32) / (32768.0 if x.dtype == np.int16 else 1.0)
                out[n] = (sr, x.mean(1) if x.ndim == 2 else x)
        self.stem = out
        return out

    def sync(self):
        if not self.stem:
            return
        mp = np.frombuffer(subprocess.run([FFMPEG, "-v", "error", "-i", str(self.mp4), "-map", "0:a", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
        ref = None
        for n in ("vo", "sfx", "music"):
            if n in self.stem:
                sr, x = self.stem[n]
                if sr != 48000:
                    continue
                ref = x.copy() if ref is None else ref[: len(x)] + x[: len(ref)]
        if ref is None or not len(mp):
            return
        k = min(len(mp), len(ref), 48000 * 30)
        c = signal.correlate(mp[:k], ref[:k], mode="full", method="fft")
        self.m["sync_ms"] = round((int(np.argmax(c)) - (k - 1)) / 48.0, 1)

    # ---------------------------------------------------------------- picture
    def picture(self):
        aw, ah = self.aw, self.ah
        fine = []
        for g in frames(self.mp4, AFPS, aw, ah):
            fine.append(g.reshape(ah // FB, FB, aw // FB, FB).mean(axis=(1, 3)).astype(np.float32))
        Fi = np.array(fine)                                            # (N, ah/3, aw/3) fine block means
        N = len(Fi)
        Co = Fi.reshape(N, Fi.shape[1] // 2, 2, Fi.shape[2] // 2, 2).mean(axis=(2, 4))     # coarse 24 px blocks
        self.N = N
        dco = np.vstack([np.zeros((1,) + Co.shape[1:], np.float32), np.abs(np.diff(Co, axis=0))])
        self.cap_rows = self.caption_rows(dco)
        self.cap_signal = dco[:, self.cap_rows, :].mean(axis=(1, 2)) if self.cap_rows else None
        dco[:, self.cap_rows, :] = 0
        self.dco = dco
        dfi = np.vstack([np.zeros((1,) + Fi.shape[1:], np.float32), np.abs(np.diff(Fi, axis=0))])
        for r in self.cap_rows:                                        # fine rows of the caption band
            dfi[:, 2 * r:2 * r + 2, :] = 0
        self.dfi = dfi                                                 # (N, rows, cols) change of the fine blocks
        self._series = {}
        del Fi, fine
        self.onsets = self.find_onsets(dco, 5.0, 3)                   # [(t, size, (y0, x0, y1, x1) in coarse blocks)]
        big = sorted({round(t, 4) for t, sz, _ in self.onsets if sz >= 12})
        merged = []
        for t in big:
            if not merged or t - merged[-1] >= 0.2:
                merged.append(t)
        self.big = np.array(merged)
        self.m["onsets_per_s"] = round(len(self.big) / max(self.dur, 1e-6), 2)
        # one pass at 10 fps and tools/frame_stats.py's frame size (long side 480, aspect kept): motion between frames
        # 0.1 s apart with the caption band left out, and frame_stats' per-second measures on frame s * 10 + 5
        fw, fh = (round(480 * self.W / self.H / 2) * 2, 480) if self.H >= self.W else (480, round(480 * self.H / self.W / 2) * 2)
        rowmask = np.ones(fh, bool)
        if self.cap_rows:
            y0, y1 = self.cap_rows[0] * CB * 4, (self.cap_rows[-1] + 1) * CB * 4          # film px
            rowmask[int(y0 * fh / self.H):int(np.ceil(y1 * fh / self.H))] = False
        B, W3 = 12, np.array([0.299, 0.587, 0.114], np.float32)
        hb, wb = fh // B, fw // B
        mo, per, prev = [0.0], [], None
        for k, fr in enumerate(frames(self.mp4, MFPS, fw, fh, "rgb24")):
            luma = fr.astype(np.float32) @ W3
            if prev is not None:
                mo.append(float(np.abs(luma[rowmask] - prev[rowmask]).mean()))
            prev = luma
            if k % MFPS == MFPS // 2:
                sd = luma[:hb * B, :wb * B].reshape(hb, B, wb, B).std(axis=(1, 3))
                px = fr.reshape(-1, 3).astype(np.int32)
                mx, mn = px.max(1), px.min(1)
                sat = (((mx - mn) / np.maximum(mx, 1) > 0.75) & (mx > 170)).mean() * 100
                per.append({"t": k // MFPS + 0.5, "flat": float((sd < T["flat_block_std"]).mean() * 100), "detail": float((sd > 12).mean() * 100), "sat": float(sat)})
        self.motion = np.array(mo)
        self.m["median_motion"] = round(float(np.median(self.motion[1:])), 2) if len(self.motion) > 1 else 0.0
        self.per_second = per

    def caption_rows(self, d):
        """Rows of coarse blocks whose change follows the spoken words: the burned-in captions."""
        plan_box = ((self.P.plan or {}).get("captions") or {}).get("box")
        nrow = d.shape[1]
        if plan_box:
            y0, y1 = plan_box[1] / 4 / CB, plan_box[3] / 4 / CB
            return list(range(max(0, int(y0)), min(nrow, int(np.ceil(y1)))))
        N = d.shape[0]
        w = np.zeros(N)
        for _k, t, _e, _l in self.P.words:
            i = int(round(t * AFPS))
            if 0 <= i < N:
                w[i] = 1
        if not w.any():
            return []
        w = ndimage.gaussian_filter1d(w, 1.0)
        rs = ndimage.gaussian_filter1d(d.mean(axis=2), 1.0, axis=0)
        cor = np.array([np.corrcoef(w, rs[:, r])[0, 1] if rs[:, r].std() > 0 else 0 for r in range(nrow)])
        cor = np.nan_to_num(cor)
        self.cap_corr = cor
        best = int(np.argmax(cor))
        self.m["caption_corr"] = round(float(cor[best]), 3)
        if cor[best] < 0.2:
            return []
        rows = {best}
        for step in (-1, 1):
            r = best + step
            while 0 <= r < nrow and cor[r] >= max(0.06, 0.25 * cor[best]):
                rows.add(r)
                r += step
        lo, hi = min(rows) - 1, max(rows) + 1                      # one more row each side for outline and shadow
        rows = list(range(max(0, lo), min(nrow, hi + 1)))
        self.m["caption_band_px"] = [rows[0] * CB * 4, (rows[-1] + 1) * CB * 4]
        return rows

    @staticmethod
    def find_onsets(d, thr, minsize, quiet=int(0.4 * AFPS)):
        """Blocks that change by more than `thr` after `quiet` frames of changing less than a third of that."""
        pm = np.zeros_like(d)
        for k in range(1, quiet + 1):
            pm[k:] = np.maximum(pm[k:], d[:-k])
        on = (d > thr) & (pm < 0.35 * d)
        out = []
        for i in range(1, len(d)):
            if not on[i].any():
                continue
            lab, n = ndimage.label(on[i])
            if not n:
                continue
            objs = ndimage.find_objects(lab)
            sizes = ndimage.sum(on[i], lab, range(1, n + 1))
            for sz, sl in zip(sizes, objs):
                if sz >= minsize:
                    out.append((i / AFPS, int(sz), (sl[0].start, sl[1].start, sl[0].stop, sl[1].stop)))
        return out

    def fine_box(self, box):
        """The event's box on the fine grid (rows y0:y1, columns x0:x1); the whole frame for no box or a huge one."""
        ny, nx = self.dfi.shape[1:]
        if box is None or (box[2] - box[0]) * (box[3] - box[1]) > 0.6 * self.W * self.H:
            return 0, 0, nx, ny
        x0, y0 = int(box[0] / 4 / FB), int(box[1] / 4 / FB)
        x1, y1 = int(np.ceil(box[2] / 4 / FB)), int(np.ceil(box[3] / 4 / FB))
        return max(0, x0), max(0, y0), min(nx, max(x1, x0 + 1)), min(ny, max(y1, y0 + 1))

    def box_series(self, fb):
        if fb not in self._series:
            x0, y0, x1, y1 = fb
            self._series[fb] = self.dfi[:, y0:y1, x0:x1].mean(axis=(1, 2))
        return self._series[fb]

    def event_check(self, ev):
        """Does the picture visibly change in the event's box at its time? The change in the box during
        [t - 0.3, t + 0.5] s must be at least 2.5x the box's usual change between planned events (the same box over
        +-4 s, leaving out every planned event in an overlapping box), cover at least 4 blocks of 12 px, and (for a
        box) be at least twice the change in the rest of the frame. calibration/README.md has the rates on my films
        and at times away from any event. Returns (shown, lag of the strongest change, score)."""
        t = ev["t"]
        fb = self.fine_box(ev.get("box"))
        s = self.box_series(fb)
        N = len(s)
        i = int(round(t * AFPS))
        a = max(1, int(np.ceil((t + T["lock_win"][0]) * AFPS)))
        b = min(N, int(np.floor((t + T["lock_win"][1]) * AFPS)) + 1)
        if b - a < 3:
            return False, None, 0.0
        lo, hi = max(1, i - 4 * AFPS), min(N, i + 4 * AFPS)
        mask = np.zeros(N, bool)
        mask[lo:hi] = True
        for o in self.events:
            if o.get("t") is None or not boxes_overlap(self.fine_box(o.get("box")), fb):
                continue
            j = int(round(o["t"] * AFPS))
            mask[max(0, j - int(0.3 * AFPS)):j + int(0.6 * AFPS) + 1] = False
        mask[max(0, a - 3):b + 3] = False
        base = float(np.median(s[mask])) if mask.sum() >= 15 else float(np.median(s[lo:hi]))
        x0, y0, x1, y1 = fb
        ny, nx = self.dfi.shape[1:]
        n_in = (x1 - x0) * (y1 - y0)
        win = self.dfi[a:b]
        area = (win[:, y0:y1, x0:x1] > 6).sum(axis=(1, 2))            # blocks visibly changing, per frame
        ok = (s[a:b] >= T["shown_ratio"] * (base + 0.05)) & (area >= T["shown_blocks"])
        if n_in < 0.6 * nx * ny:
            # a boxed event must also stand out from the rest of the frame in the same frame: during a camera move
            # or a cut everything changes, and a small face change in the middle of it does not read
            rest = (win.sum(axis=(1, 2)) - s[a:b] * n_in) / max(1, nx * ny - n_in)
            ok &= s[a:b] >= T["shown_spatial"] * rest + 0.1
        cand = np.where(ok)[0] if ok.any() else np.arange(b - a)
        k = a + int(cand[np.argmax(s[a:b][cand])])
        score = float(s[k]) / (base + 0.05)
        shown = bool(ok.any())
        if not shown and t <= 0.3:                                     # the opening: the film must start on motion
            j = int(0.6 * MFPS)
            if len(self.motion) > j and self.motion[1:j + 1].mean() >= max(0.5, np.median(self.motion[1:])):
                return True, 0.0, round(score, 2)
        if not shown and ev["kind"] == "camera":                       # a camera move changes speed rather than starting a change
            j = int(t * MFPS)
            m0, m1 = self.motion[max(1, j - 8):max(2, j - 2)], self.motion[j:j + 6]
            if len(m0) and len(m1) and (m1.mean() > 1.5 * m0.mean() + 0.3 or m1.mean() < 0.5 * m0.mean() - 0.3):
                return True, 0.0, round(score, 2)
        return shown, (k / AFPS - t), round(score, 2)

    def event_lock(self, rows):
        """The same visibility test with every planned event moved 0.7-2.5 s earlier or later (5 times each). If the
        events are seen at their planned times much more often than at shifted ones, the picture follows the plan's
        words; a film that changes everywhere all the time is 'seen' at shifted times too. Returns (share seen at
        shifted times, one-sided binomial p of the planned share)."""
        rng = np.random.default_rng(5)
        hits = n = 0
        for r in rows:
            for _ in range(5):
                t = r["t"] + rng.uniform(0.7, 2.5) * rng.choice([-1, 1])
                if 0.5 <= t <= self.dur - 0.5:
                    n += 1
                    hits += bool(self.event_check(dict(r, t=t))[0])
        p0 = hits / max(n, 1)
        k = sum(1 for r in rows if r["shown"])
        return p0, float(stats.binom.sf(k - 1, len(rows), min(max(p0, 1e-3), 0.999)))

    def lock(self, times):
        on = self.big
        if len(times) < 8 or len(on) == 0:
            return 0.0, 1.0

        def ratio(a):
            lag = (on[None, :] - a[:, None]).ravel()
            win = np.sum((lag >= -0.15) & (lag <= 0.35)) / 0.5
            base = np.sum((np.abs(lag) >= 0.8) & (np.abs(lag) <= 2.0)) / 2.4
            return win / max(base, 1e-9)

        a = np.array(sorted(times))
        r0 = ratio(a)
        rng = np.random.default_rng(7)
        null = np.array([ratio(a + rng.uniform(-2.5, 2.5, len(a))) for _ in range(400)])
        return round(float(r0), 3), round(float((np.sum(null >= r0) + 1) / (len(null) + 1)), 3)

    # ---------------------------------------------------------------- sound
    def cue_levels(self):
        """Level of the effects stem in 20 ms steps (dB), over the whole band and above 1.5 kHz (pops, clicks and
        hits live high; whooshes and rumbles low), and the spectral flux used to time each sound."""
        sr, x = self.stem["sfx"]
        hop = int(0.02 * sr)
        n = len(x) // hop
        self.E = 10 * np.log10((x[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-10)
        b, a = signal.butter(2, 1500 / (sr / 2), "high")
        xh = signal.lfilter(b, a, x)
        self.Eh = 10 * np.log10((xh[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-10)
        f, tt, Z = signal.stft(x, sr, nperseg=1024, noverlap=1024 - 480)
        lm = np.log1p(100 * np.abs(Z))
        self.flux = np.concatenate([[0], np.clip(np.diff(lm, axis=1), 0, None).sum(0)])
        self.flux_t = tt

    def cue_hit(self, t):
        """Does a sound start at t? The effects level within [t - 0.1, t + 0.45] s rises at least 5 dB above 1.5 kHz
        (or 8 dB over the whole band) over its median in the 0.65 s before. Returns the sound's time (its sharpest
        attack) or None. Measured on my films: 91 % of cued events, 24 % of times away from any cue."""
        i = int(t / 0.02)
        a, b = max(0, i - 40), max(1, i - 7)
        c, d = max(0, i - 5), min(len(self.E), i + 23)
        if d - c < 3:
            return None
        if not (self.Eh[c:d].max() - np.median(self.Eh[a:b]) >= T["cue_jump_high_db"] or self.E[c:d].max() - np.median(self.E[a:b]) >= T["cue_jump_db"]):
            return None
        w = np.where((self.flux_t >= t - 0.1) & (self.flux_t <= t + 0.45))[0]
        return float(self.flux_t[w[np.argmax(self.flux[w])]]) if len(w) else t

    def fingerprint(self, t):
        sr, x = self.stem["sfx"]
        i = int(t * sr)
        seg = x[max(0, i - int(0.01 * sr)): i + int(0.30 * sr)]
        if len(seg) < 2048 or np.abs(seg).max() < 1e-4:
            return None
        edges = np.geomspace(60, 16000, 33)
        f, _tt, Z = signal.stft(seg, sr, nperseg=1024, noverlap=768)
        Pw = np.abs(Z) ** 2
        bands = np.array([Pw[(f >= a) & (f < b)].sum(0) for a, b in zip(edges[:-1], edges[1:])])
        spec = np.log10(bands.mean(1) + 1e-12)
        spec -= spec.mean()
        env = np.log10(bands.sum(0) + 1e-12)
        env = np.interp(np.linspace(0, 1, 8), np.linspace(0, 1, len(env)), env)
        env -= env.mean()
        v = np.concatenate([spec, 0.5 * env])
        return v / (np.linalg.norm(v) + 1e-9)

    # ---------------------------------------------------------------- HyperFrames and the seek test
    def hf_copy(self):
        """HyperFrames writes a cache into the folder it runs in; run it on a copy so the film's folder stays untouched."""
        if getattr(self, "_hf", None) is None:
            self._hf = Path(tempfile.mkdtemp(prefix="reviewer-hf-")) / self.P.root.name
            shutil.copytree(self.P.root, self._hf, symlinks=False,
                            ignore=shutil.ignore_patterns("renders", "review", "reviewer", ".hyperframes", "node_modules", ".snaps", "vo", "*.mp4"))
        return self._hf

    def cleanup(self):
        if getattr(self, "_hf", None) is not None:
            shutil.rmtree(self._hf.parent, ignore_errors=True)
            self._hf = None

    def hyperframes(self):
        env = dict(os.environ, HYPERFRAMES_SKIP_SKILLS="1")
        res = {}
        for name, extra in (("default", []), ("dense", ["--samples=150", "--no-craft", "--no-contrast"])):
            try:
                r = subprocess.run(["npx", "--yes", HF, "check", "--no-cache"] + extra, cwd=self.hf_copy(), capture_output=True, text=True, timeout=1500, env=env)
            except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                res[name] = {"ran": False, "error": str(e)}
                continue
            out = r.stdout + r.stderr
            found = [ln.strip() for ln in out.splitlines() if re.match(r"\s+[✗⚠ℹ] ", ln)]
            errs = sum(int(x) for x in re.findall(r"(\d+) error\(s\)", out))
            warns = sum(int(x) for x in re.findall(r"(\d+) warning\(s\)", out))
            passed = "Check passed" in out
            res[name] = {"ran": passed or "Check failed" in out, "passed": passed, "errors": errs, "warnings": warns, "findings": found[:40]}
            if not res[name]["ran"]:
                res[name]["error"] = out[-600:]
        self.m["hyperframes"] = res
        return res

    def seek_test(self, times):
        if not times:
            return None
        # exactly on a frame (fast motion must compare like with like), one per frame, in order
        times = sorted({round(round(t * self.fps) / self.fps, 4) for t in times})
        env = dict(os.environ, HYPERFRAMES_SKIP_SKILLS="1")
        tmp = Path(tempfile.mkdtemp(prefix="reviewer-seek-"))
        try:
            r = subprocess.run(["npx", "--yes", HF, "snapshot", "--at", ",".join(f"{t:.4f}" for t in times), "--no-end", "-o", str(tmp)],
                               cwd=self.hf_copy(), capture_output=True, text=True, timeout=900, env=env)
            shots = sorted(tmp.glob("frame-*.png"))
            if len(shots) != len(times):
                return {"ran": False, "error": (r.stdout + r.stderr)[-600:]}
            from_png = []
            for p in shots:
                raw = subprocess.run([FFMPEG, "-v", "error", "-i", str(p), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
                from_png.append(np.frombuffer(raw, np.uint8).reshape(self.H, self.W, 3))
            idx = [int(round(t * self.fps)) for t in times]
            sel = "+".join(f"eq(n\\,{i})" for i in idx)
            raw = subprocess.run([FFMPEG, "-v", "error", "-i", str(self.mp4), "-vf", f"select='{sel}'", "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            mp = np.frombuffer(raw, np.uint8).reshape(-1, self.H, self.W, 3)
            out = []
            for t, a, b in zip(times, from_png, mp):
                dd = np.abs(a.astype(np.int16) - b.astype(np.int16))
                out.append({"t": round(t, 3), "mean": round(float(dd.mean()), 2), "px_off": round(float((dd.max(2) > 40).mean()), 4)})
            return {"ran": True, "frames": out}
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError) as e:
            return {"ran": False, "error": str(e)}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def run(P, issues: Issues, plan_m, mp4=None, quick=False):
    st = "film"
    mp4 = Path(mp4) if mp4 else P.find_mp4()
    if mp4 is None or not Path(mp4).exists():
        issues.must(st, "F01", "No rendered MP4 found in renders/.", "Render the film: npx hyperframes render --fps 30 --quality delivery -o renders/<film>.mp4")
        return {}, None
    F = Film(mp4, P, plan_m)
    m = F.m
    m["mp4"] = str(mp4)
    fps_film = P.fps
    # ---------------------------------------------------------------- F01 specs
    v, a = F.probe()
    if v is None:
        issues.must(st, "F01", "The MP4 has no video stream.", "Re-render.")
        return m, F
    exp_dur = P.film_len or F.dur
    probs = []
    if v.get("codec_name") != "h264" or v.get("pix_fmt") != "yuv420p":
        probs.append(f"video is {v.get('codec_name')}/{v.get('pix_fmt')} (needs h264/yuv420p)")
    if (int(v.get("width", 0)), int(v.get("height", 0))) != (P.W, P.H):
        probs.append(f"size {v.get('width')}x{v.get('height')} (film.json says {P.W}x{P.H})")
    if abs(F.fps - fps_film) > 0.01:
        probs.append(f"{F.fps:g} fps (film.json says {fps_film:g})")
    if abs(F.dur - exp_dur) > 1.5 / fps_film + 0.02:
        probs.append(f"duration {F.dur:.3f} s (timing.json says {exp_dur:.3f} s)")
    if v.get("nb_frames") and abs(int(v["nb_frames"]) - round(F.dur * F.fps)) > 1:
        probs.append("frame count does not match duration x fps")
    if a is None:
        probs.append("no audio stream")
    elif a.get("codec_name") != "aac" or int(a.get("sample_rate", 0)) != 48000 or int(a.get("channels", 0)) != 2:
        probs.append(f"audio is {a.get('codec_name')} {a.get('sample_rate')} Hz x{a.get('channels')} (needs AAC 48 kHz stereo)")
    if probs:
        issues.must(st, "F01", "MP4 specs: " + "; ".join(probs) + ".", "Render with `npx hyperframes render --fps 30 --quality delivery` after build.py, so the film length comes from the voice timing.")
    # ---------------------------------------------------------------- F02 loudness
    if a is not None:
        F.loudness()
        L = m["loudness"]
        if L["I"] is None or abs(L["I"] - T["lufs"]) > T["lufs_tol"]:
            issues.must(st, "F02", f"Integrated loudness {L['I']} LUFS (target {T['lufs']} +/- {T['lufs_tol']}).", "Master with audio/mix.py (TARGET_LUFS = -14) and re-render.")
        if L["true_peak"] is not None and L["true_peak"] > T["true_peak_max"]:
            issues.must(st, "F02", f"True peak {L['true_peak']} dBTP (at most {T['true_peak_max']}).", "Lower the ceiling in audio/mix.py; AAC overshoots.")
    # ---------------------------------------------------------------- F03 stems and sync
    stems = F.stems()
    miss = [n for n in ("vo", "sfx", "music") if n not in stems]
    if miss:
        issues.must(st, "F03", f"Missing stems: {', '.join(n + '.wav' for n in miss)} in assets/.", "Keep the three mixed stems (audio/mix.py writes them); the reviewer checks the voice, effects and music separately.")
    F.sync()
    if "sync_ms" in m and abs(m["sync_ms"]) > T["sync_ms"]:
        issues.must(st, "F03", f"The MP4 audio is {m['sync_ms']:+.0f} ms off the stems.", "Rebuild (python build.py) so index.html mounts the current stems, then re-render.")
    # ---------------------------------------------------------------- picture measures
    F.blacks()
    F.picture()
    holds = F.holds
    vo_end = P.vo_end or F.dur
    # F04 black and flash frames
    for b0, b1 in m["black"]:
        if b1 - b0 >= T["black_s"] and not overlaps_hold(b0, b1, holds):
            issues.must(st, "F04", f"Black frames for {b1 - b0:.2f} s.", "Cover the cut: start the next scene on its first frame, or declare a hold if black is intended.", scene=P.scene_at(b0), t0=b0, t1=b1)
    for t in m["flash"]:
        if not overlaps_hold(t - 0.05, t + 0.05, holds):
            issues.must(st, "F04", "A single flash frame (brightness jumps for one frame).", "Find the frame-0 state that differs from the tween's start (fromTo without immediateRender:false, a set() at the wrong time).", scene=P.scene_at(t), t0=t)
    # F05 captions
    if (P.film or {}).get("captions", P.vertical):
        if not F.cap_rows:
            issues.must(st, "F05", f"No burned-in captions found (best caption-row correlation with the words {m.get('caption_corr', 0):.2f}).",
                        "Burn in captions (compositions/captions.html, film.json captions: true) in the safe area near y 1185.")
        else:
            c = F.cap_signal
            med = float(np.median(c))
            mad = float(np.median(np.abs(c - med))) + 1e-6
            hit = 0
            for _k, t, _e, _l in P.words:
                i0, i1 = max(0, int((t - 0.1) * AFPS)), min(len(c), int((t + 0.2) * AFPS) + 1)
                hit += bool(i1 > i0 and c[i0:i1].max() > med + 3 * mad)
            cov = hit / max(1, len(P.words))
            m["captions_follow"] = round(cov, 3)
            if cov < T["captions_follow"]:
                issues.must(st, "F05", f"The captions change on only {cov * 100:.0f} % of the spoken words.", "Captions must follow the voice word by word (build.py chunks + captions.html highlight).")
    # F06 motion and still runs
    mo = F.motion
    if m["median_motion"] < T["median_motion_must"]:
        issues.must(st, "F06", f"Median motion {m['median_motion']} (at least {T['median_motion_must']}; my films 1.4-2.9).", "The film is too still: animate the subject, drift the camera, add life in the background (particles, wobble).")
    elif m["median_motion"] < T["median_motion_should"]:
        issues.should(st, "F06", f"Median motion {m['median_motion']}.", "Add motion toward 1.2 or more.")
    for a0, a1 in runs_of(mo < T["still_level"], MFPS):
        a0 = max(a0, 0.1)
        if a1 - a0 < T["still_should_s"] or a0 >= vo_end or overlaps_hold(a0, a1, holds):
            continue
        lvl = issues.must if a1 - a0 >= T["still_must_s"] else issues.should
        lvl(st, "F06", f"The picture is frozen for {a1 - a0:.1f} s (motion under {T['still_level']}) {P.narration(a0, a1)}.",
            "Keep something alive: a reaction, a camera drift, the background moving.", scene=P.scene_at(a0), t0=a0, t1=a1)
    m["still_runs"] = [(round(a0, 2), round(a1, 2)) for a0, a1 in runs_of(mo < T["still_level"], MFPS) if a1 - a0 >= 0.5]
    # F07 empty frames
    flags = [p for p in F.per_second if p["flat"] > T["flat_second"] and not overlaps_hold(p["t"] - 0.5, p["t"] + 0.5, holds)]
    m["flat_seconds"] = [int(p["t"]) for p in F.per_second if p["flat"] > T["flat_second"]]
    m["flat_mean"] = round(float(np.mean([p["flat"] for p in F.per_second])), 1) if F.per_second else None
    secs = sorted(int(p["t"]) for p in flags)
    run_s, prev = [], None
    for s in secs + [None]:
        if s is not None and prev is not None and s == prev + 1:
            run_s[-1].append(s)
        elif s is not None:
            run_s.append([s])
        prev = s
    for r in run_s:
        if len(r) >= T["flat_run_must_s"]:
            issues.must(st, "F07", f"{len(r)} seconds in a row are mostly empty background (over {T['flat_second']:.0f} % flat).",
                        "Fill the frame: a bigger subject, a slow push-in, a low-contrast background layer (KC.cytoplasm, KS.stage stars, KO.snow). If the emptiness is the point, declare a hold with the reason.",
                        scene=P.scene_at(r[0] + 0.5), t0=float(r[0]), t1=float(r[-1] + 1))
    share = len(flags) / max(1, len(F.per_second))
    if share > T["flat_share_must"]:
        issues.must(st, "F07", f"{len(flags)} of {len(F.per_second)} seconds are mostly empty background ({share * 100:.0f} %).", "Fill the frames listed in review.json (flat_seconds).")
    elif share > T["flat_share_should"]:
        issues.should(st, "F07", f"{len(flags)} of {len(F.per_second)} seconds are mostly empty background.", "Fill or declare them.")
    # F16 saturation
    for p in F.per_second:
        if p["sat"] > T["sat_share"] and not overlaps_hold(p["t"] - 0.5, p["t"] + 0.5, holds):
            issues.should(st, "F16", f"{p['sat']:.1f} % very saturated bright pixels.", "Keep one saturated accent; tone down the rest (style rule: about 7 % at most).", scene=P.scene_at(p["t"]), t0=p["t"])
    # ---------------------------------------------------------------- F08 onsets per scene and dead stretches
    pic = [e for e in F.events if e["kind"] in KINDS_PICTURE and e["t"] is not None]
    scene_rows = {}
    for sc in P.scenes:
        o = F.big[(F.big >= sc["start"]) & (F.big < sc["end"])]
        rate = len(o) / sc["dur"]
        seg = mo[int(sc["start"] * MFPS) + 1:max(int(sc["start"] * MFPS) + 2, int(sc["end"] * MFPS))]
        scene_rows[sc["id"]] = {"dur": round(sc["dur"], 2), "onsets": int(len(o)), "onset_rate": round(rate, 2), "median_motion": round(float(np.median(seg)), 2) if len(seg) else 0}
        if overlaps_hold(sc["start"], sc["end"], holds, 0.6):
            continue
        if rate < T["onset_rate_must"]:
            issues.must(st, "F08", f"Scene '{sc['id']}' shows {len(o)} picture onsets in {sc['dur']:.1f} s ({rate:.2f}/s).",
                        "Make things happen in the picture on the words: appear, move, react, transform (my films: 0.6-3 per second).", scene=sc["id"], t0=sc["start"], t1=sc["end"])
        elif rate < T["onset_rate_should"]:
            issues.should(st, "F08", f"Scene '{sc['id']}' shows {rate:.2f} picture onsets per second.", "Add picture events.", scene=sc["id"], t0=sc["start"], t1=sc["end"])
    m["scenes"] = scene_rows
    # per-event visibility (feeds dead stretches, F09, F11)
    ev_rows = []
    for e in pic:
        shown, lag, score = F.event_check(e)
        ev_rows.append(dict(e, shown=shown, lag=None if lag is None else round(lag, 2), score=score))
    if P.words:
        w0, w1 = P.words[0][1], P.words[-1][2]
        pts = sorted([w0] + [t for t in F.big if w0 <= t <= w1] + [r["t"] + (r["lag"] or 0) for r in ev_rows if r["shown"] and w0 <= r["t"] <= w1] + [w1])
        dead = []
        for g0, g1 in zip(pts, pts[1:]):
            if g1 - g0 < T["dead_should_s"] or overlaps_hold(g0, g1, holds):
                continue
            seg = mo[int(g0 * MFPS) + 1:int(g1 * MFPS)]
            med = float(np.median(seg)) if len(seg) else 0
            said = P.narration(g0, g1)
            if med < T["dead_motion"]:
                lvl = issues.must if g1 - g0 >= T["dead_must_s"] else issues.should
                lvl(st, "F08", f"Dead stretch: {g1 - g0:.1f} s with no picture onset and little motion ({med:.2f}) {said}.",
                    "Show what is being said: an action on its key word, or at least a reaction or camera move.", scene=P.scene_at(g0), t0=g0, t1=g1)
                dead.append((round(g0, 2), round(g1, 2)))
            elif g1 - g0 >= 3.5:
                issues.should(st, "F08", f"{g1 - g0:.1f} s with motion but no new picture event {said}.",
                              "Add a beat on a key word; steady motion alone does not tell the story.", scene=P.scene_at(g0), t0=g0, t1=g1)
        m["dead"] = dead
    # F09 shown, F10 lock
    if not pic:
        issues.must(st, "F09", "No planned picture events to check the film against.", "Fix plan.json first (stage 2).")
    else:
        shown = [r for r in ev_rows if r["shown"]]
        m["shown_share"] = round(len(shown) / len(ev_rows), 3)
        if len(shown) / len(ev_rows) < T["shown_must"]:
            issues.must(st, "F09", f"Only {len(shown)} of {len(ev_rows)} planned picture events visibly happen at their time ({len(shown) / len(ev_rows) * 100:.0f} %).",
                        "See the events marked 'not seen' below and in sheets/events-*.jpg: make each one visible (bigger, brighter, moving), on its word.")
        for r in ev_rows:
            if not r["shown"]:
                where = " in its box" if r.get("box") else ""
                issues.should(st, "F09", f"{r['scene']} event {r['i']} ({r['kind']}, {ev_name(r)}): \"{r['does']}\" is not seen{where} at its time.",
                              "Make it visible at that moment: larger, more contrast, a clear start (a pop, a snap, a fast move).", scene=r["scene"], t0=r["t"])
        p0, ep = F.event_lock(ev_rows)
        m["shown_shifted"], m["event_lock_p"] = round(p0, 3), float(f"{ep:.2g}")
        if ep > T["event_lock_p_must"]:
            issues.must(st, "F10", f"The picture is not tied to the words: planned events are seen at their times {len(shown) / len(ev_rows) * 100:.0f} % of the time, "
                        f"and {p0 * 100:.0f} % of the time when moved 0.7-2.5 s (p = {ep:.2g}).",
                        "Start each event on its word (at(\"word\") in the scene, the same anchor as plan.json) with a clear start, and keep the rest of its box calm "
                        "between events; do not run animations on their own clock.")
        times = [r["t"] for r in ev_rows]
        ratio, p = F.lock(times)
        m["lock_ratio"], m["lock_p"] = ratio, p
        if ratio < T["lock_ratio_should"] or p > T["lock_p_should"]:
            issues.should(st, "F10", f"The film's big changes are only {ratio:.2f}x as frequent at the planned times as elsewhere (p = {p:.2f}).",
                          "Check that the big animations start on their words, and that plan.json lists every big change as an event.")
    # F11 acting
    acts = [r for r in ev_rows if r["kind"] in ("act", "react")]
    if acts:
        sh = [r for r in acts if r["shown"]]
        m["acts_shown"] = round(len(sh) / len(acts), 3)
        if len(sh) / len(acts) < T["acts_shown_must"]:
            issues.must(st, "F11", f"Only {len(sh)} of {len(acts)} character acts/reacts visibly happen inside their box.",
                        "The characters pose: make each act read on a phone (big gestures, eyes and mouth that change, a squash or stretch).")
        bywho = {}
        for r in acts:
            bywho.setdefault((r["scene"], r["who"]), []).append(r)
        for (sid, who), rs in bywho.items():
            if not any(r["shown"] for r in rs):
                issues.must(st, "F11", f"In '{sid}', '{who}' only poses: none of its {len(rs)} planned acts shows up in its box.",
                            f"Animate '{who}' on the planned words ({', '.join(str(r['word']) for r in rs)}).", scene=sid, t0=rs[0]["t"], t1=rs[-1]["t"])
    m["events"] = ev_rows
    # ---------------------------------------------------------------- F12 sound per event, F13 mix
    if "sfx" in stems:
        F.cue_levels()
        cued = [r for r in ev_rows if r.get("sfx")]
        matched = []
        for r in cued:
            ct = F.cue_hit(r["t"])
            r["cue_t"] = None if ct is None else round(ct, 3)
            if ct is not None:
                matched.append(r)
        cov = len(matched) / len(cued) if cued else 0
        m["cue_cover"] = round(cov, 3)
        if cued:
            # the same coverage with every cue moved 0.7-2.5 s at random: a stem full of sounds everywhere also covers
            # the events, so the real times must do clearly better than shifted ones
            rng = np.random.default_rng(11)
            ts = np.array([r["t"] for r in cued])
            null = []
            for _ in range(200):
                sh = np.clip(ts + rng.uniform(0.7, 2.5, len(ts)) * rng.choice([-1, 1], len(ts)), 0.0, F.dur - 0.1)
                null.append(np.mean([F.cue_hit(x) is not None for x in sh]))
            p = (np.sum(np.array(null) >= cov) + 1) / (len(null) + 1)
            m["cue_lock_p"], m["cue_cover_shifted"] = round(float(p), 3), round(float(np.median(null)), 3)
            if cov < T["cue_cover_must"]:
                issues.must(st, "F12", f"Only {len(matched)} of {len(cued)} cued picture events have a sound starting at their time ({cov * 100:.0f} %).",
                            "Give each picture event its sound, timed with the same word formula as the picture (audio/sfx_cues.py: a(scene, word) + offset).")
            elif p > T["cue_lock_p_must"]:
                issues.must(st, "F12", f"Sounds start at {cov * 100:.0f} % of the cued events, but also at {np.median(null) * 100:.0f} % of random times near them (p = {p:.2f}): the effects are not tied to the events.",
                            "Cut the effects that belong to no event, and put each event's sound on its word.")
            elif cov < T["cue_cover_should"]:
                issues.should(st, "F12", f"{cov * 100:.0f} % of cued events have a sound at their time.", "Check the silent ones in EVENTS.md (cue at: empty).")
            for r in cued:
                if r["cue_t"] is None and cov >= T["cue_cover_must"]:
                    issues.should(st, "F12", f"{r['scene']} event {r['i']} ({ev_name(r)}) has no sound starting at its time (planned: {r['sfx']}).", "Add or retime its cue.", scene=r["scene"], t0=r["t"])
        V = [F.fingerprint(r["cue_t"]) for r in matched]
        V = np.array([v for v in V if v is not None])
        if len(V) >= 5:
            S = V @ V.T
            seen, big = np.zeros(len(V), bool), 0
            for i in range(len(V)):
                if seen[i]:
                    continue
                stack, comp = [i], 0
                seen[i] = True
                while stack:
                    j = stack.pop()
                    comp += 1
                    for k in np.where((S[j] >= T["cue_same_sim"]) & ~seen)[0]:
                        seen[k] = True
                        stack.append(k)
                big = max(big, comp)
            share = big / len(V)
            m["cue_same_share"] = round(share, 3)
            if share > T["cue_same_must"]:
                issues.must(st, "F12", f"{big} of {len(V)} event cues are the same sound ({share * 100:.0f} %).", "Give each event its own sound (my films: under 10 % share one sound).")
            elif share > T["cue_same_should"]:
                issues.should(st, "F12", f"{share * 100:.0f} % of event cues are the same sound.", "Vary the cues.")
    if "vo" in stems and P.words:
        sr, vo = stems["vo"]
        speak = np.zeros(len(vo), bool)
        for _k, t, e, _l in P.words:
            speak[int(t * sr):int(e * sr)] = True
        rms = lambda x: float(np.sqrt(np.mean(x ** 2)) + 1e-12)
        if speak.any():
            vr = rms(vo[speak])
            bed = np.zeros_like(vo)
            for n in ("sfx", "music"):
                if n in stems:
                    x = stems[n][1][: len(vo)]
                    bed[: len(x)] += x
            db = lambda r: 20 * np.log10(r)
            m["voice_over_bed_db"] = round(db(vr) - db(rms(bed[speak])), 1)
            if m["voice_over_bed_db"] < T["voice_over_bed_must"]:
                issues.must(st, "F13", f"The voice is only {m['voice_over_bed_db']} dB over effects + music while speaking.", "Duck the music and level the effects (audio/mix.py): at least 7 dB.")
            elif m["voice_over_bed_db"] < T["voice_over_bed_should"]:
                issues.should(st, "F13", f"Voice {m['voice_over_bed_db']} dB over the bed while speaking.", "Aim for 7 dB or more.")
            if "music" in stems:
                mu = stems["music"][1][: len(vo)]
                m["music_under_voice_db"] = round(db(vr) - db(rms(mu[speak[: len(mu)]])), 1)
                if m["music_under_voice_db"] < T["music_under_voice_must"]:
                    issues.must(st, "F13", f"Music is only {m['music_under_voice_db']} dB under the voice.", "Lower or duck the music (my films: about 13 dB under).")
                win = int(0.5 * sr)
                n = len(mu) // win
                lv = 20 * np.log10(np.sqrt((mu[: n * win].reshape(n, win) ** 2).mean(1)) + 1e-9)
                pres = float(np.mean(lv > -50))
                m["music_present"] = round(pres, 2)
                if pres < T["music_present"]:
                    issues.must(st, "F13", f"Music is audible in only {pres * 100:.0f} % of the film.", "Score the whole film (audio/music.py), with sections keyed to the scenes.")
    # ---------------------------------------------------------------- F14 HyperFrames, F15 seek test
    if quick:
        m["hyperframes"] = "skipped (--quick)"
        m["seek"] = "skipped (--quick)"
    else:
        res = F.hyperframes()
        for name, r in res.items():
            if not r.get("ran"):
                issues.must(st, "F14", f"HyperFrames check ({name}) did not run: {r.get('error', '')[:200]}", "Run it in the project folder (docs/01-environment.md), then review again.")
                continue
            if r["errors"] or r["warnings"]:
                issues.must(st, "F14", f"HyperFrames check ({name}): {r['errors']} errors, {r['warnings']} warnings: " + " | ".join(r["findings"][:4]), "Fix every finding (docs/09-pitfalls.md has the usual ones).")
            elif any(f.startswith("ℹ") for f in r["findings"]):
                issues.should(st, "F14", f"HyperFrames check ({name}) info: " + " | ".join(f for f in r["findings"] if f.startswith("ℹ"))[:300], "Review the info findings.")
        sample = []
        for sc in P.scenes:
            c = [r["t"] for r in ev_rows if r["scene"] == sc["id"]]
            t = c[len(c) // 2] + 0.15 if c else (sc["start"] + sc["end"]) / 2
            sample.append(min(max(t, 0.5), F.dur - 0.5))
        seek = F.seek_test(sample[:10])
        F.cleanup()
        m["seek"] = seek
        if not seek or not seek.get("ran"):
            issues.must(st, "F15", f"The seek test did not run: {(seek or {}).get('error', 'no times')[:200]}", "Make `npx hyperframes snapshot` work in the project folder, then review again.")
        else:
            for fr in seek["frames"]:
                if fr["mean"] > T["seek_mean_max"] or fr["px_off"] > T["seek_px_max"]:
                    issues.must(st, "F15", f"A fresh snapshot differs from the MP4 frame (mean {fr['mean']}, {fr['px_off'] * 100:.1f} % of pixels off).",
                                "Some state depends on the order frames are rendered: set every value before the update() that draws it, redraw from tl.eventCallback('onUpdate') (docs/09-pitfalls.md).",
                                scene=P.scene_at(fr["t"]), t0=fr["t"])
    return m, F
