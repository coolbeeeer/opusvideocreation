"""Review sheets: for every planned picture event, three frames from the MP4 (before, at, after its word) with a label
that says what the plan promised and whether the reviewer saw it. One JPEG per scene, plus one for flagged times.
These are what a person (or an agent that can look at images) checks before trusting a "shown" result.
"""
import subprocess
from pathlib import Path

import numpy as np

from film_check import FFMPEG

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:          # labels need Pillow; without it the sheets are written unlabelled
    Image = None

TW, TH = 180, 320            # tile size (vertical); landscape tiles are 320 x 180


def grab(mp4, times, fps, W, H):
    """Frames at the given film times, one ffmpeg pass. Returns {frame index: RGB array}."""
    tw, th = (TW, TH) if H >= W else (TH, TW)
    idx = sorted({max(0, int(round(t * fps))) for t in times})
    if not idx:
        return {}, tw, th
    out = {}
    for k in range(0, len(idx), 120):                      # keep the select expression a sane length
        part = idx[k:k + 120]
        sel = "+".join(f"eq(n\\,{i})" for i in part)
        raw = subprocess.run([FFMPEG, "-v", "error", "-i", str(mp4), "-vf", f"select='{sel}',scale={tw}:{th}", "-vsync", "0",
                              "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        fr = np.frombuffer(raw, np.uint8).reshape(-1, th, tw, 3)
        for i, f in zip(part, fr):
            out[i] = f
    return out, tw, th


def font(size):
    if Image is None:
        return None
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def save(arr, path):
    path = Path(path)
    if Image is not None:
        Image.fromarray(arr).save(path, quality=85)
    else:
        h, w = arr.shape[:2]
        subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-i", "-", str(path)], input=arr.tobytes())


def event_sheets(mp4, P, events, out_dir, flags=()):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fps = P.fps
    want = []
    for e in events:
        want += [e["t"] - 0.4, e["t"] + 0.15, e["t"] + 0.6]
    want += [t for t, _ in flags]
    frames_, tw, th = grab(mp4, want, fps, P.W, P.H)
    get = lambda t: frames_.get(max(0, int(round(t * fps))), np.zeros((th, tw, 3), np.uint8))
    written = []
    f1, f2 = font(15), font(13)
    lab_h = 58
    for sc in P.scenes:
        evs = [e for e in events if e["scene"] == sc["id"]]
        if not evs:
            continue
        cols = 2                                                  # two events (six frames) per row
        rows = -(-len(evs) // cols)
        cw = 3 * tw + 8
        sheet = np.full((rows * (th + lab_h + 8) + 8, cols * cw + 8, 3), 24, np.uint8)
        for k, e in enumerate(evs):
            r, c = divmod(k, cols)
            x0, y0 = 8 + c * cw, 8 + r * (th + lab_h + 8)
            for j, t in enumerate((e["t"] - 0.4, e["t"] + 0.15, e["t"] + 0.6)):
                sheet[y0 + lab_h:y0 + lab_h + th, x0 + j * tw:x0 + (j + 1) * tw] = get(t)
            col = (60, 160, 80) if e.get("shown") else (190, 50, 50)
            sheet[y0:y0 + 4, x0:x0 + 3 * tw] = col
        if Image is not None:
            im = Image.fromarray(sheet)
            dr = ImageDraw.Draw(im)
            for k, e in enumerate(evs):
                r, c = divmod(k, cols)
                x0, y0 = 8 + c * cw, 8 + r * (th + lab_h + 8)
                seen = ("SEEN" + (f" {e['lag']:+.2f} s" if e.get("lag") is not None else "")) if e.get("shown") else "NOT SEEN"
                cue = f"  cue {'ok' if e.get('cue_t') is not None else 'MISSING'}" if e.get("sfx") else ""
                dr.text((x0, y0 + 6), f"#{e['i']} {e['t']:.2f}s '{e.get('word') or 'time'}' {e['kind']}{' ' + str(e['who']) if e.get('who') else ''}  {seen}{cue}",
                        fill=(255, 255, 255), font=f1)
                dr.text((x0, y0 + 26), str(e.get("does", ""))[:72], fill=(210, 210, 210), font=f2)
                dr.text((x0, y0 + 42), "before          at the word          after", fill=(150, 150, 150), font=f2)
                if e.get("box"):
                    b = e["box"]
                    sx, sy = tw / P.W, th / P.H
                    dr.rectangle([x0 + tw + b[0] * sx, y0 + lab_h + b[1] * sy, x0 + tw + b[2] * sx, y0 + lab_h + b[3] * sy], outline=(255, 210, 0), width=2)
            sheet = np.array(im)
        p = out_dir / f"events-{sc['id']}.jpg"
        save(sheet, p)
        written.append(p)
    if flags:
        flags = list(flags)[:24]
        cols = 6
        rows = -(-len(flags) // cols)
        sheet = np.full((rows * (th + 40 + 8) + 8, cols * (tw + 8) + 8, 3), 24, np.uint8)
        for k, (t, _txt) in enumerate(flags):
            r, c = divmod(k, cols)
            x0, y0 = 8 + c * (tw + 8), 8 + r * (th + 48)
            sheet[y0 + 40:y0 + 40 + th, x0:x0 + tw] = get(t)
        if Image is not None:
            im = Image.fromarray(sheet)
            dr = ImageDraw.Draw(im)
            for k, (t, txt) in enumerate(flags):
                r, c = divmod(k, cols)
                x0, y0 = 8 + c * (tw + 8), 8 + r * (th + 48)
                dr.text((x0, y0 + 4), f"{t:.2f} s", fill=(255, 255, 255), font=f1)
                dr.text((x0, y0 + 22), txt[:26], fill=(230, 120, 120), font=f2)
            sheet = np.array(im)
        p = out_dir / "flags.jpg"
        save(sheet, p)
        written.append(p)
    return written
