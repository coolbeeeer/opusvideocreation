"""Wondenza end card — append the locked end card + watermark to a film.

The locked pattern (user verdict "Perfect", 2026-11-22):
  * ~0.5 s stillness after the last spoken word (the final film frame holds)
  * 1.5 s crossfade — film fades out as the card fades in, card bed fades in
  * end card (3.0 s): eye, one blink, "Wondenza", Like & Subscribe
  * "Like and subscribe" (the LOCKED clip, never regenerated) lands ~0.2 s
    after the card is fully visible, bed ducked beneath it
  * 25% eye watermark, top-right, through the FILM only — it fades out with
    the crossfade and is absent from the card
  * the source fps is kept (a 30 fps film stays 30 fps; the 60 fps card is
    converted to match). Never mix frame rates in one file.

Master chain: the final gain comes BEFORE the limiter
(alimiter limit=0.79, level=false). Gain after the limiter clips — that was
the re-voice's limiter-order bug (peak -0.62 dBFS).

``assemble()`` takes the finished film video + the mixed film audio and
writes the final mp4. ``correct_master()`` re-encodes ONLY the audio
(video stream copied) with a corrective gain, if the measured output is
off the -14 LUFS target.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
from mix import MixError, measure_loudness


def probe_fps(video: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=r_frame_rate",
                        "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        raise MixError(f"cannot probe fps of {video}: {r.stderr[-300:]}")
    num, den = r.stdout.strip().split("/")
    return float(num) / float(den)


def endcard_times(last_word_end: float) -> dict:
    """All end-card times from the last spoken word's end."""
    hold_start = last_word_end
    xfade_start = hold_start + C.HOLD_AFTER_LAST_WORD_S
    xfade_end = xfade_start + C.XFADE_DURATION_S
    total = xfade_start + C.CARD_DURATION_S
    like_at = xfade_end + C.VOICE_LINE_DELAY_AFTER_CARD_S
    return {"last_word_end": round(last_word_end, 3),
            "hold_start": round(hold_start, 3),
            "xfade_start": round(xfade_start, 3),
            "xfade_end": round(xfade_end, 3),
            "like_at": round(like_at, 3),
            "total": round(total, 3)}


def assemble(film_video: Path, film_audio: Path, last_word_end: float,
             out_path: Path, gain_db: float = 0.0) -> dict:
    """Append the end card + watermark. ``gain_db`` is the master gain
    (computed from the film audio's measured loudness to hit -14 LUFS);
    it is applied BEFORE the limiter. Returns the end-card times + the
    output's measured loudness.
    """
    times = endcard_times(last_word_end)
    fps = probe_fps(film_video)
    fps_s = f"{fps:.0f}" if fps == int(fps) else f"{fps:.3f}"
    xs, xe, total = times["xfade_start"], times["xfade_end"], times["total"]
    like_at = times["like_at"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fc = (
        f"[0:v]fps={fps_s},settb=AVTB,trim=0:{xe},setpts=PTS-STARTPTS[film];"
        f"[1:v]fps={fps_s},settb=AVTB[card];"
        f"[4:v]scale={C.WATERMARK_WIDTH}:-1,"
        f"colorkey={C.WATERMARK_COLORKEY},format=yuva420p,"
        f"colorchannelmixer=aa={C.WATERMARK_OPACITY}[wm];"
        f"[film][wm]overlay={C.WATERMARK_X}:{C.WATERMARK_Y}[filmm];"
        f"[filmm][card]xfade=transition=fade:duration={C.XFADE_DURATION_S}"
        f":offset={xs},format=yuv420p[vout];"
        f"[5:a]atrim=0:{xe},asetpts=PTS-STARTPTS,"
        f"afade=t=out:st={xs}:d={C.XFADE_DURATION_S}[filma];"
        f"[1:a]adelay={int(xs * 1000)}:all=1,"
        f"afade=t=in:st={xs}:d={C.XFADE_DURATION_S}[beda];"
        f"[3:a]adelay={int(xs * 1000)}:all=1[sfxa];"
        f"[beda][sfxa]amix=inputs=2:normalize=0[cardmix];"
        f"[2:a]adelay={int(like_at * 1000)}:all=1[voice];"
        f"[filma][cardmix][voice]amix=inputs=3:normalize=0,"
        f"volume={gain_db:.2f}dB,"
        f"alimiter=limit={C.MASTER_LIMITER}:level=false[aout]"
    )
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-i", str(film_video), "-i", str(C.ENDCARD_VIDEO),
           "-i", str(C.LIKE_SUBSCRIBE), "-i", str(C.ENDCARD_SFX),
           "-i", str(C.EYE_ICON), "-i", str(film_audio),
           "-filter_complex", fc,
           "-map", "[vout]", "-map", "[aout]",
           "-c:v", "libx264", "-crf", "16", "-preset", "medium",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-ar", str(C.SAMPLE_RATE), "-t", f"{total:.2f}", str(out_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise MixError(f"end-card assembly failed: {r.stderr[-1500:]}")
    loud = measure_loudness(out_path)
    print(f"assembled {out_path} ({total:.2f} s, {fps_s} fps): "
          f"{loud['integrated']:.2f} LUFS, peak {loud['true_peak']:.2f} dBFS")
    return {"times": times, "fps": fps, **loud, "path": str(out_path)}


def correct_master(src: Path, out_path: Path,
                   target_lufs: float = C.MASTER_LUFS) -> dict:
    """Re-encode ONLY the audio (video stream copied) with a corrective
    gain so the output lands on the master target. Gain before the limiter.
    Returns the corrected output's measured loudness.
    """
    loud = measure_loudness(src)
    corr = target_lufs - loud["integrated"]
    if abs(corr) <= 0.3 and loud["true_peak"] <= C.MASTER_PEAK_DBFS:
        print(f"master already on target ({loud['integrated']:.2f} LUFS, "
              f"peak {loud['true_peak']:.2f}) — no correction")
        return {"path": str(src), "corrected": False, **loud}
    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src),
         "-c:v", "copy",
         "-af", f"volume={corr:.2f}dB,"
                f"alimiter=limit={C.MASTER_LIMITER}:level=false",
         "-c:a", "aac", "-b:a", "192k", "-ar", str(C.SAMPLE_RATE),
         str(out_path)], capture_output=True, text=True)
    if r.returncode != 0:
        raise MixError(f"master correction failed: {r.stderr[-1000:]}")
    loud2 = measure_loudness(out_path)
    print(f"master corrected {corr:+.2f} dB -> {loud2['integrated']:.2f} LUFS, "
          f"peak {loud2['true_peak']:.2f} dBFS")
    return {"path": str(out_path), "corrected": True, "correction_db": round(corr, 2),
            **loud2}


def main() -> int:
    ap = argparse.ArgumentParser(description="Append the Wondenza end card.")
    ap.add_argument("--film-video", required=True)
    ap.add_argument("--film-audio", required=True)
    ap.add_argument("--last-word-end", type=float, required=True)
    ap.add_argument("--gain-db", type=float, default=0.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    assemble(Path(args.film_video), Path(args.film_audio),
             args.last_word_end, Path(args.out), gain_db=args.gain_db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
