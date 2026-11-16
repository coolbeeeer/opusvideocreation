"""Verify a rendered film from the MP4 itself (an agent cannot watch or listen, so it measures).

usage: python tools/verify_render.py projects/antibiotics/renders/antibiotics-v2.mp4 [--stems projects/antibiotics/assets]
                                     [--fps 60] [--duration 60] [--sheet out.jpg] [--every 2]

Checks: resolution/fps/frame count/duration, audio loudness + peak, audio sync against the stems
(vo.wav + sfx.wav + music.wav), black frames, saturated-pixel share over time, and writes a contact sheet.
Exit code 1 if a hard check fails.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("mp4")
ap.add_argument("--stems", help="folder with vo.wav, sfx.wav, music.wav")
ap.add_argument("--fps", type=float, default=60)
ap.add_argument("--duration", type=float)
ap.add_argument("--sheet", help="write a contact sheet jpg here")
ap.add_argument("--every", type=float, default=2.0, help="seconds between contact-sheet frames")
a = ap.parse_args()
fails = []
run = lambda cmd: subprocess.run(cmd, capture_output=True, text=True)

# ---- container
info = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate,nb_frames,sample_rate,channels",
                       "-show_entries", "format=duration", "-of", "json", a.mp4]).stdout)
v = next(s for s in info["streams"] if s["codec_type"] == "video")
au = [s for s in info["streams"] if s["codec_type"] == "audio"]
dur = float(info["format"]["duration"])
num, den = map(int, v["r_frame_rate"].split("/"))
fps = num / den
print(f"video  {v['width']}x{v['height']} @ {fps:g} fps, {v.get('nb_frames')} frames, {dur:.3f} s")
if abs(fps - a.fps) > 0.01:
    fails.append(f"fps {fps} != {a.fps}")
if a.duration and abs(dur - a.duration) > 0.02:
    fails.append(f"duration {dur:.3f} != {a.duration}")
if v.get("nb_frames") and abs(int(v["nb_frames"]) - round(dur * fps)) > 1:
    fails.append("frame count does not match duration x fps")

# ---- audio loudness + sync
if au:
    r = run(["ffmpeg", "-nostats", "-i", a.mp4, "-map", "0:a", "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
    P = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
    print(f"audio  {au[0].get('sample_rate')} Hz x{au[0].get('channels')}, {I:.1f} LUFS integrated, peak {P:.1f} dBFS")
    if P > -0.5:
        fails.append(f"audio peak {P} dBFS is too hot (clipping risk)")
    if a.stems:
        from scipy import signal
        from scipy.io import wavfile
        mp = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", a.mp4, "-map", "0:a", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
        ref = None
        for n in ["vo.wav", "sfx.wav", "music.wav"]:
            p = Path(a.stems) / n
            if p.exists():
                x = wavfile.read(p)[1].astype(float) / 32768
                x = x.mean(1) if x.ndim == 2 else x
                ref = x if ref is None else ref[: len(x)] + x[: len(ref)]
        if ref is not None:
            k = min(len(mp), len(ref))
            c = signal.correlate(mp[:k], ref[:k], mode="full", method="fft")
            lag = (np.argmax(c) - (k - 1)) / 48.0
            print(f"sync   MP4 audio vs stems: {lag:.1f} ms")
            if abs(lag) > 20:
                fails.append(f"audio is {lag:.0f} ms out of sync with the stems")
else:
    print("audio  none")

# ---- black frames
bd = run(["ffmpeg", "-v", "info", "-i", a.mp4, "-vf", "blackdetect=d=0.05:pix_th=0.04", "-an", "-f", "null", "-"]).stderr
blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bd)
print(f"black  {len(blacks)} black stretch(es)" + (": " + ", ".join(f"{s}-{e}s" for s, e in blacks) if blacks else ""))

# ---- saturation share over time (style rule: one saturated accent, ~<7 % in dark scenes)
W, H = 320, 180
print("satur  share of pixels with saturation>0.75 and brightness>170:")
line = []
for t in np.arange(0.5, dur, max(1.0, dur / 30)):
    fr = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", a.mp4, "-frames:v", "1", "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    if len(fr) < W * H * 3:
        continue
    f = np.frombuffer(fr, np.uint8).reshape(-1, 3).astype(int)
    mx, mn = f.max(1), f.min(1)
    share = (((mx - mn) / np.maximum(mx, 1) > 0.75) & (mx > 170)).mean() * 100
    line.append(f"{t:4.1f}s {share:4.1f}%" + (" <-- over 7%" if share > 7 else ""))
print("       " + "\n       ".join(line))

# ---- contact sheet
if a.sheet:
    cols = 6
    n = int(dur / a.every) + 1
    rows = -(-n // cols)
    run(["ffmpeg", "-v", "error", "-y", "-i", a.mp4, "-vf", f"fps=1/{a.every},scale=480:-1,tile={cols}x{rows}:padding=3:color=0x202020", "-frames:v", "1", a.sheet])
    print(f"sheet  {a.sheet} (one frame every {a.every:g} s)")

print("RESULT", "PASS" if not fails else "FAIL: " + "; ".join(fails))
sys.exit(1 if fails else 0)
