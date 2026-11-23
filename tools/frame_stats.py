"""Per-second frame statistics for a rendered film, decoded from the MP4 itself.

usage: python frame_stats.py film.mp4        (needs ffmpeg on PATH and numpy)

The film is decoded at 10 fps and scaled so its long side is 480 px, keeping the aspect ratio (480x270 for 16:9,
270x480 for a vertical 9:16 film; squashing a vertical film into 480x270 would make every block 27x85 px).
For one frame per second it reports:
  flat%    share of 12x12-pixel blocks (48x48 px at 1080p) whose luma std-dev is under 3:
           empty, untextured background. Seconds above 70 % are flagged "mostly empty".
  detail%  share of blocks with an edge in them (std-dev over 12)
  motion   mean absolute luma change between frames 0.1 s apart (0-255 scale); near 0 = a frozen-looking frame
  sat%     share of pixels with saturation > 0.75 and value > 170 (the repo's accent-colour metric)
  meanLuma average brightness (0-255)

Proposed as an extra review gate next to tools/verify_render.py: flag any run of seconds that is
mostly empty or nearly motionless, then look at those frames.
"""
import subprocess
import sys

import numpy as np

mp4 = sys.argv[1]
probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", mp4],
                       capture_output=True, text=True).stdout.strip().split(",")
src_w, src_h = int(probe[0]), int(probe[1])
W, H, B = (480, round(480 * src_h / src_w / 2) * 2, 12) if src_w >= src_h else (round(480 * src_w / src_h / 2) * 2, 480, 12)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-vf", f"fps=10,scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                     capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(np.float32)
luma = fr @ np.array([0.299, 0.587, 0.114], np.float32)
hb, wb = H // B, W // B
rows = []
for s in range(int(len(fr) / 10)):
    i = s * 10 + 5
    std = luma[i, :hb * B, :wb * B].reshape(hb, B, wb, B).std(axis=(1, 3))
    flat, detail = (std < 3).mean() * 100, (std > 12).mean() * 100
    motion = np.abs(luma[i] - luma[i - 1]).mean()
    px = fr[i].reshape(-1, 3)
    mx, mn = px.max(1), px.min(1)
    sat = (((mx - mn) / np.maximum(mx, 1) > 0.75) & (mx > 170)).mean() * 100
    rows.append((s, flat, detail, motion, sat, luma[i].mean()))
print(" sec  flat%  detail%  motion  sat%  meanLuma")
for r in rows:
    print(f"{r[0]:4d} {r[1]:6.1f} {r[2]:7.1f} {r[3]:7.2f} {r[4]:5.1f} {r[5]:7.1f}" + ("   <- mostly empty" if r[1] > 70 else ""))
a = np.array(rows)
print(f"\nmean flat {a[:, 1].mean():.1f}%  seconds >70% flat: {(a[:, 1] > 70).sum()} of {len(a)}  "
      f"mean luma {a[:, 5].mean():.1f}  median motion {np.median(a[:, 3]):.2f}")
