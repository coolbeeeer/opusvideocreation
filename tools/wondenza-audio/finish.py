"""Wondenza finish — one entry point: rendered film -> finished mp4.

Takes a rendered film (picture + SFX/music bed, NO voice — the clean cut,
like ``falling_asleep_sfx_clean.mp4``) plus the Fish voice clips at their
start times, and produces the finished film with:

  * our Fish voice, mixed to the locked house mix (voice -15 LUFS,
    bed ~8.4 dB under the voice while speaking, ducked 3 dB)
  * the locked end card + 25% eye watermark (film only)
  * master -14 LUFS, true peak <= -1.5 dBFS, stereo

Usage (post-render finish — clips already recorded, e.g. by voice.py):
    python finish.py --video renders/film.mp4 --clips assets/voice \\
        --timing assets/vo_timing.json --out renders/film-final.mp4

Full auto (record the voice too, from the project's film.json):
    python finish.py --video renders/film.mp4 --record-from film.json \\
        --out renders/film-final.mp4

Timing sources (``--timing``), in order of preference:
  * ``vo_timing.json`` / Opus ``timing.json`` — {"lines": [{line, text, start, end}]}
  * ``clips.json`` (from voice.py) — clips carry their own starts
  * ``VOICE_TIMING.md`` — the user-supplied sheet (Clip | Start at | ... | Line)

The end card is anchored on the last spoken word: from ``--word-times``
(a JSON of {clip: [{w, t, e}]} with times relative to the clip, as
``align.py`` produces) when given, else the last clip's end.

Writes a JSON report (``<out>.report.json``) with every measured number.
Does NOT upload anything. No API key is needed when the clips already exist.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
import voice as voice_mod
from endcard import assemble, correct_master, endcard_times
from mix import (MixError, build_bed, build_voice_stem, combine_bed,
                 measure_loudness, mix_film_audio)


def _run(cmd: list[str], what: str) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise MixError(f"{what} failed: {r.stderr[-1500:]}")
    return r


def parse_timing_sheet(path: Path) -> list[dict]:
    """Parse a VOICE_TIMING.md table into lines.

    Rows look like: | 01 | 0:01.20 | 4.7 s | 5.3 s | You're drifting off... |
    (Clip | Start at | Planned speech | Max length | Line). The planned/max
    columns may be absent; the start and the line text are what matter.
    """
    lines = []
    for raw in path.read_text().splitlines():
        if not raw.strip().startswith("|"):
            continue
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.fullmatch(r"\d+", cells[0]):
            continue
        start = cells[1]
        m = re.fullmatch(r"(?:(\d+):)?(\d+(?:\.\d+)?)", start)
        if not m:
            continue
        minutes = float(m.group(1) or 0)
        start_s = minutes * 60 + float(m.group(2))
        text = cells[-1]
        lines.append({"line": int(cells[0]), "text": text, "start": start_s})
    if not lines:
        raise MixError(f"no timing rows found in {path}")
    return lines


def load_timing(path: Path) -> list[dict]:
    """Load clip start times from vo_timing.json, timing.json, clips.json,
    or a VOICE_TIMING.md sheet. Returns [{"line", "text", "start", "end"}]
    (``end`` is None when the source only gives starts)."""
    if path.suffix == ".md":
        return parse_timing_sheet(path)
    d = json.loads(path.read_text())
    if isinstance(d, dict) and "lines" in d:
        out = []
        for l in d["lines"]:
            out.append({"line": int(l["line"]), "text": l["text"],
                        "start": float(l["start"]),
                        "end": float(l.get("end")) if l.get("end") else None})
        return out
    if isinstance(d, list):
        return [{"line": int(c["line"]), "text": c["text"],
                 "start": float(c["start"]),
                 "end": float(c["start"] + c["duration"])}
                for c in d]
    raise MixError(f"unrecognised timing file: {path}")


def find_clip(clips_dir: Path, line_no: int) -> Path:
    """clipNN_final.wav preferred, clipNN.wav fallback."""
    for name in (f"clip{line_no:02d}_final.wav", f"clip{line_no:02d}.wav"):
        p = clips_dir / name
        if p.exists():
            return p
    raise MixError(f"no clip for line {line_no} in {clips_dir} "
                   f"(looked for clip{line_no:02d}_final.wav / clip{line_no:02d}.wav)")


def clip_duration(path: Path) -> float:
    return voice_mod.clip_duration(path)


def extract_bed(video: Path, out_path: Path) -> Path:
    """The film's own audio, untouched — the SFX+music bed."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn",
          "-c:a", "pcm_s16le", str(out_path)], "extract bed")
    return out_path


def probe(path: Path) -> dict:
    r = _run(["ffprobe", "-v", "error", "-show_entries",
              "format=duration,size",
              "-show_entries",
              "stream=codec_type,codec_name,width,height,r_frame_rate,channels",
              "-of", "json", str(path)], f"ffprobe {path}")
    d = json.loads(r.stdout)
    streams = {s["codec_type"]: s for s in d["streams"]}
    v = streams.get("video", {})
    a = streams.get("audio", {})
    return {"duration": float(d["format"]["duration"]),
            "size": int(d["format"]["size"]),
            "width": v.get("width"), "height": v.get("height"),
            "fps": v.get("r_frame_rate"), "video_codec": v.get("codec_name"),
            "audio_codec": a.get("codec_name"),
            "channels": a.get("channels")}


def _frame(video: Path, t: float, out: Path,
           crop: str | None = None) -> Path:
    """Extract one frame at time t (seconds) as a PNG."""
    vf = f"select='eq(n\\,0)'"
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}",
           "-i", str(video), "-frames:v", "1"]
    if crop:
        cmd += ["-vf", f"crop={crop}"]
    cmd += [str(out)]
    _run(cmd, f"extract frame {t}s from {video}")
    return out


def frame_psnr(a: Path, b: Path, t_a: float, t_b: float,
               crop: str | None = None, tmpdir: Path | None = None) -> float:
    """PSNR (dB) between a frame of video A at t_a and a frame of video B
    at t_b. ``crop`` (e.g. "800:1920:0:0") limits the comparison to a
    region — used to exclude the watermark corner when proving the
    picture is untouched."""
    tmpdir = tmpdir or Path("/tmp")
    fa = _frame(a, t_a, tmpdir / "psnr_a.png", crop)
    fb = _frame(b, t_b, tmpdir / "psnr_b.png", crop)
    r = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(fa), "-i", str(fb),
         "-filter_complex", "psnr", "-frames:v", "1", "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.search(r"PSNR.*?average:([0-9.]+|inf)", r.stderr)
    if not m:
        return float("nan")
    return float("inf") if m.group(1) == "inf" else float(m.group(1))


def finish(video: Path, clips_dir: Path | None, timing: list[dict],
           out_path: Path, work_dir: Path,
           bed_path: Path | None = None, sfx: Path | None = None,
           music: Path | None = None, word_times: Path | None = None,
           film_dur: float | None = None) -> dict:
    """Run the whole finish. Returns the report dict (also written to
    ``<out>.report.json``)."""
    work_dir.mkdir(parents=True, exist_ok=True)
    video_info = probe(video)
    film_dur = film_dur or video_info["duration"]

    # 1. voice clips + starts
    clips = []
    for line in timing:
        p = find_clip(clips_dir, line["line"])
        dur = clip_duration(p)
        clips.append({"line": line["line"], "text": line["text"],
                      "path": str(p), "start": line["start"],
                      "duration": dur,
                      "end": line.get("end") or line["start"] + dur})
    print(f"{len(clips)} clips, film {film_dur:.2f} s")

    # 2. voice stem
    stem = build_voice_stem(
        [{"path": c["path"], "start": c["start"], "duration": c["duration"]}
         for c in clips], film_dur, work_dir / "voice_stem.wav")

    # 3. bed (the film's own SFX+music, untouched)
    if bed_path is None:
        if sfx is not None and music is not None:
            bed_path = combine_bed(sfx, music, work_dir / "bed.wav")
        else:
            bed_path = extract_bed(video, work_dir / "bed_original.wav")
    bed_loud = measure_loudness(bed_path)
    print(f"bed: {bed_loud['integrated']:.2f} LUFS, peak "
          f"{bed_loud['true_peak']:.2f} dBFS (kept as-is)")
    regions = [(c["start"], c["start"] + c["duration"]) for c in clips]
    bed = build_bed(bed_path, Path(stem["path"]), regions,
                    work_dir / "bed_ducked.wav")

    # 4. film audio
    film_audio = mix_film_audio(Path(stem["path"]), Path(bed["path"]),
                                work_dir / "film_audio.wav")

    # 5. end-card anchor: last spoken word, from word times if given,
    #    else the last clip's end.
    last_word_end = clips[-1]["end"]
    if word_times is not None:
        wt = json.loads(word_times.read_text())
        last_clip = str(clips[-1]["line"]).zfill(2)
        words = wt.get(last_clip) or wt.get(str(clips[-1]["line"])) or []
        if words:
            # Match the script's last word, searching backwards. The raw
            # last entry is often a hallucinated repeat or an interpolated
            # filler (whisper/align pads unmatched trailing words at the
            # clip end) — it is NOT the real last word.
            norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
            last_script_word = norm(clips[-1]["text"].split()[-1])
            target = next((w for w in reversed(words)
                           if norm(w["w"]) == last_script_word), words[-1])
            last_word_end = clips[-1]["start"] + float(target["e"])
            print(f"last word ends {last_word_end:.2f} s "
                  f"(word times: '{target['w']}')")
    print(f"end card: last word {last_word_end:.2f} s, "
          f"times {endcard_times(last_word_end)}")

    # 6. assemble with a first master gain from the film audio's level
    gain = C.MASTER_LUFS - film_audio["integrated"]
    result = assemble(video, Path(film_audio["path"]), last_word_end,
                      out_path, gain_db=gain)

    # 7. correct the master if the measured output is off target
    final = correct_master(out_path, out_path)
    if final.get("corrected"):
        out_path = Path(final["path"])

    # 8. verify: probe + loudnorm + picture identity
    info = probe(out_path)
    loud = measure_loudness(out_path)
    times = result["times"]
    card_t = min(times["xfade_end"] + 0.5, info["duration"] - 0.5)
    film_t = min(45.0, times["hold_start"] - 1.0)
    # the card in the output starts at xfade_start; in the card file it starts at 0
    card_src_t = card_t - times["xfade_start"]
    psnr_film = frame_psnr(out_path, video, film_t, film_t,
                           crop="800:1920:0:0", tmpdir=work_dir)
    psnr_card = frame_psnr(out_path, C.ENDCARD_VIDEO, card_t, card_src_t,
                           tmpdir=work_dir)
    print(f"picture check: film frame PSNR {psnr_film:.2f} dB "
          f"(excl. watermark corner, want >40); card frame PSNR "
          f"{psnr_card:.2f} dB (want >30)")
    ok = (loud["integrated"] >= C.MASTER_LUFS - 0.5
          and loud["integrated"] <= C.MASTER_LUFS + 0.5
          and loud["true_peak"] <= C.MASTER_PEAK_DBFS
          and info["channels"] == 2
          and psnr_film > 40 and psnr_card > 30)
    report = {
        "out": str(out_path), "duration": info["duration"],
        "video": f"{info['width']}x{info['height']} {info['fps']}",
        "channels": info["channels"],
        "loudness_lufs": loud["integrated"],
        "true_peak_dbfs": loud["true_peak"],
        "voice_stem_lufs": stem["integrated"],
        "bed_lufs": bed_loud["integrated"],
        "bed_offset_db": bed["offset_db"],
        "bed_gain_db": bed["bed_gain_db"],
        "endcard_times": times,
        "psnr_film_db": psnr_film, "psnr_card_db": psnr_card,
        "spec_ok": ok,
    }
    (Path(str(out_path) + ".report.json")).write_text(
        json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    if not ok:
        print("WARNING: one or more spec checks failed — see the report.")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Finish a rendered film with the Wondenza voice + mix + end card.")
    ap.add_argument("--video", required=True,
                    help="rendered film mp4 (picture + SFX/music bed, NO voice)")
    ap.add_argument("--clips", help="dir of Fish clips (clipNN_final.wav)")
    ap.add_argument("--timing",
                    help="vo_timing.json, timing.json, clips.json, or VOICE_TIMING.md")
    ap.add_argument("--record-from",
                    help="project film.json — record the voice first (needs FISH_AUDIO_API_KEY)")
    ap.add_argument("--bed", help="bed wav (default: the video's own audio)")
    ap.add_argument("--sfx", help="sfx.wav (with --music, instead of --bed)")
    ap.add_argument("--music", help="music.wav (with --sfx, instead of --bed)")
    ap.add_argument("--word-times", help="word-times JSON for the end-card anchor")
    ap.add_argument("--film-dur", type=float, help="film duration (default: video duration)")
    ap.add_argument("--workdir", default="work")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    video = Path(args.video)
    out_path = Path(args.out)
    work_dir = Path(args.workdir)
    clips_dir = Path(args.clips) if args.clips else None
    timing = None
    if args.record_from:
        if clips_dir is None:
            clips_dir = work_dir / "voice"
        res = voice_mod.record_film(Path(args.record_from), clips_dir)
        timing = [{"line": c["line"], "text": c["text"],
                   "start": None, "end": None} for c in res["clips"]]
        # starts come from the vo_timing.json the recording just wrote
        timing = load_timing(Path(res["vo_timing"]))
    if timing is None:
        if not args.timing:
            ap.error("give --timing or --record-from")
        timing = load_timing(Path(args.timing))
    if clips_dir is None:
        ap.error("give --clips (or --record-from to record them)")
    finish(video, clips_dir, timing, out_path, work_dir,
           bed_path=Path(args.bed) if args.bed else None,
           sfx=Path(args.sfx) if args.sfx else None,
           music=Path(args.music) if args.music else None,
           word_times=Path(args.word_times) if args.word_times else None,
           film_dur=args.film_dur)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
