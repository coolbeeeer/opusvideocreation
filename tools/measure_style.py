"""Measure a reference video's palette and saturation at chosen times (style study; never reuse the frames).

usage: python tools/measure_style.py ref.mp4 6:torch 45:window 85:timeline 495:soil
       python tools/measure_style.py ref.mp4 --grid 0,60,10 --sheet check.jpg   # verify timestamps first

For each time: the 6 dominant colours with their share of the frame, and the share of highly saturated pixels
(saturation > 0.75 and brightness > 170) with the most saturated colour. Always verify the timestamps with
--grid before trusting a measurement: a mapping that is off by a few seconds measures the wrong scene.
"""
import argparse
import subprocess

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("points", nargs="*", help="time[:label] in seconds")
ap.add_argument("--grid", help="start,end,step: write a grid of frames at these times to --sheet")
ap.add_argument("--sheet", default="timecheck.jpg")
a = ap.parse_args()
W, H = 320, 180


def frame(t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", a.video, "-frames:v", "1", "-vf", f"scale={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(int)


if a.grid:
    s, e, st = map(float, a.grid.split(","))
    times = list(np.arange(s, e, st))
    expr = "+".join(f"eq(n\\,{i})" for i in range(len(times)))
    inputs = sum((["-ss", f"{t:.2f}", "-i", a.video] for t in times), [])
    filt = "".join(f"[{i}:v]scale=320:180,trim=end_frame=1[v{i}];" for i in range(len(times)))
    cols = 4
    layout = "|".join(f"{(i % cols) * 320}_{(i // cols) * 180}" for i in range(len(times)))
    filt += "".join(f"[v{i}]" for i in range(len(times))) + f"xstack=inputs={len(times)}:layout={layout}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", filt, "-frames:v", "1", a.sheet])
    print(f"wrote {a.sheet}: frames at {', '.join(f'{t:g}s' for t in times)} (row by row, {cols} per row)")

for p in a.points:
    t, _, label = p.partition(":")
    f = frame(float(t))
    q = f // 28
    _, inv, cnt = np.unique(q, axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    top = np.argsort(-cnt)[:6]
    cols = "  ".join("#%02x%02x%02x %d%%" % (*f[inv == k].mean(0).astype(int), round(100 * cnt[k] / len(f))) for k in top)
    mx, mn = f.max(1), f.min(1)
    sat = (mx - mn) / np.maximum(mx, 1)
    hs = (sat > 0.75) & (mx > 170)
    peak = f[np.argmax(sat * (mx > 170))]
    peak_hex = "#%02x%02x%02x" % tuple(peak)
    print(f"{label or t:14s} t={float(t):6.1f}s  {cols}  | saturated {hs.mean() * 100:4.1f}%  peak {peak_hex}")
