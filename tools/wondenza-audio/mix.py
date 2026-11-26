"""Wondenza mix — voice stem + SFX/music bed to the locked house mix.

Recipe (verified on the hypnic-jerk re-voice, 2026-11-26):
  * Voice: each clip high-passed at 80 Hz and levelled to -15 LUFS, placed
    at its start time, mixed, panned to stereo (dual-mono — the pan adds
    +3 dB, so the per-clip gain is reduced 3 dB to compensate), limited
    at -3 dBFS. The first mono mix was the re-voice's stereo bug: a mono
    voice stem + stereo bed downmixed the bed to mono. Pan the voice.
  * Bed: the film's own SFX+music, used as-is — never muted, never rebuilt.
    It is ducked ~3 dB under the voice (sidechain, 40 ms attack / 350 ms
    release) and its level is MEASURED and corrected so that, while the
    voice is speaking, the bed sits 8.4 dB under the voice. Two passes:
    duck once, measure the ducked bed against the voice in the speaking
    regions, then apply the corrective bed gain and duck again.
  * Film audio: voice + bed, amix normalize=0. Its measured loudness is
    reported so finish.py can set the final master gain.

Requires: ffmpeg + ffprobe on PATH, and ``soundfile`` + ``numpy``
(both already in the repo's requirements.txt).
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

try:
    import numpy as np
    import soundfile as sf
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "wondenza-audio needs soundfile + numpy (already in the repo's "
        "requirements.txt): pip install soundfile numpy"
    ) from exc


class MixError(RuntimeError):
    pass


def _run(cmd: list[str], what: str) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise MixError(f"{what} failed: {r.stderr[-1500:]}")
    return r


def measure_loudness(path: Path) -> dict:
    """ffmpeg loudnorm measurement. Returns {integrated, true_peak, lra}."""
    r = _run(["ffmpeg", "-i", str(path), "-vn", "-af",
              f"loudnorm=I={C.MASTER_LUFS}:TP={C.MASTER_PEAK_DBFS}:LRA=11"
              ":print_format=json", "-f", "null", "-"],
             f"loudnorm {path}")
    m = re.search(r"\{[^}]*\"input_i\"[^}]*\}", r.stderr, re.S)
    if not m:
        raise MixError(f"loudnorm gave no JSON for {path}: {r.stderr[-500:]}")
    d = json.loads(m.group(0))
    return {"integrated": float(d["input_i"]),
            "true_peak": float(d["input_tp"]),
            "lra": float(d["input_lra"])}


def rms_db_in_regions(path: Path, regions: list[tuple[float, float]]) -> float:
    """RMS level (dBFS) of a wav inside the given (start, end) seconds.

    Used to measure the bed against the voice in exactly the parts where
    the voice is speaking.
    """
    data, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    segs = []
    for start, end in regions:
        i0, i1 = int(start * sr), int(end * sr)
        if i1 > i0 and i0 < len(data):
            segs.append(data[i0:min(i1, len(data))])
    if not segs:
        return float("-inf")
    x = np.concatenate(segs)
    rms = float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0
    return 20 * np.log10(rms) if rms > 0 else float("-inf")


def build_voice_stem(clips: list[dict], film_dur: float,
                     out_path: Path) -> dict:
    """Build the voice stem from trimmed clips placed at their start times.

    ``clips``: [{"path", "start", "duration"}]. Each clip is measured with
    loudnorm and gained to VOICE_LUFS (-15); the gain is reduced 3 dB
    because the final stereo pan adds +3 dB. Returns
    {"path", "integrated", "true_peak"} of the stem.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    inputs, filters, labels = [], [], []
    for i, c in enumerate(clips):
        loud = measure_loudness(Path(c["path"]))
        gain = (C.VOICE_LUFS - loud["integrated"]) - 3.0  # -3 dB for the pan
        inputs += ["-i", c["path"]]
        filters.append(
            f"[{i}:a]highpass=f={C.VOICE_HIGHPASS_HZ},"
            f"volume={gain:.2f}dB,"
            f"adelay={int(round(c['start'] * 1000))}:all=1[v{i}]")
        labels.append(f"[v{i}]")
        print(f"  clip {i + 1:02d}: {loud['integrated']:.2f} LUFS "
              f"-> gain {gain:+.2f} dB, at {c['start']:.2f} s")
    n = len(clips)
    filters.append(
        f"{''.join(labels)}amix=inputs={n}:normalize=0,"
        f"aresample={C.SAMPLE_RATE},apad=whole_dur={film_dur:.2f},"
        f"pan=stereo|c0=c0|c1=c0,alimiter=limit={C.VOICE_LIMITER}:level=false[out]")
    _run(["ffmpeg", "-y", "-v", "error"] + inputs +
         ["-filter_complex", ";".join(filters), "-map", "[out]",
          "-c:a", "pcm_s16le", str(out_path)], "voice stem")
    loud = measure_loudness(out_path)
    print(f"voice stem: {loud['integrated']:.2f} LUFS, peak "
          f"{loud['true_peak']:.2f} dBFS")
    return {"path": str(out_path), **loud}


def combine_bed(sfx: Path, music: Path, out_path: Path) -> Path:
    """Combine Opus's separate sfx.wav + music.wav into one bed."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(sfx), "-i", str(music),
          "-filter_complex",
          f"[0:a][1:a]amix=inputs=2:normalize=0,aresample={C.SAMPLE_RATE}[out]",
          "-map", "[out]", "-c:a", "pcm_s16le", str(out_path)],
         "combine bed")
    return out_path


def _duck(bed: Path, voice_stem: Path, out_path: Path,
          bed_gain_db: float = 0.0) -> Path:
    """Duck the bed under the voice (sidechain compressor).

    The reduction is driven by the voice level (threshold 0.05, ratio 2,
    40 ms attack / 350 ms release — the same envelope as the fever mix).
    ``bed_gain_db`` is applied to the bed BEFORE the duck, so the duck
    amount does not change when the level is corrected.
    """
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(bed), "-i", str(voice_stem),
          "-filter_complex",
          f"[0:a]volume={bed_gain_db:.2f}dB,aresample={C.SAMPLE_RATE}[b];"
          f"[1:a]aresample={C.SAMPLE_RATE}[v];"
          f"[b][v]sidechaincompress=threshold=0.05:ratio=2"
          f":attack={C.DUCK_ATTACK_MS}:release={C.DUCK_RELEASE_MS}[out]",
          "-map", "[out]", "-c:a", "pcm_s16le", str(out_path)], "duck bed")
    return out_path


def build_bed(bed: Path, voice_stem: Path,
              regions: list[tuple[float, float]], out_path: Path) -> dict:
    """Duck the bed and set its level so it sits BED_VOICE_OFFSET_DB under
    the voice while speaking. Two passes: duck, measure the ducked bed
    against the voice in the speaking regions, correct the bed gain, duck
    again. Returns {"path", "bed_gain_db", "offset_db"} (the achieved
    offset, measured in the speaking regions).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".pass1.wav")
    _duck(bed, voice_stem, tmp)
    voice_rms = rms_db_in_regions(voice_stem, regions)
    bed_rms = rms_db_in_regions(tmp, regions)
    gain = (voice_rms - C.BED_VOICE_OFFSET_DB) - bed_rms
    print(f"  bed pass 1: voice {voice_rms:.1f} dBFS, ducked bed "
          f"{bed_rms:.1f} dBFS in speech -> bed gain {gain:+.2f} dB")
    _duck(bed, voice_stem, out_path, bed_gain_db=gain)
    bed_rms2 = rms_db_in_regions(out_path, regions)
    offset = voice_rms - bed_rms2
    print(f"  bed pass 2: ducked bed {bed_rms2:.1f} dBFS in speech, "
          f"offset {offset:.1f} dB under voice (target {C.BED_VOICE_OFFSET_DB})")
    tmp.unlink(missing_ok=True)
    return {"path": str(out_path), "bed_gain_db": round(gain, 2),
            "offset_db": round(offset, 2)}


def mix_film_audio(voice_stem: Path, bed: Path, out_path: Path) -> dict:
    """Voice + bed -> film audio. Returns its measured loudness."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(voice_stem),
          "-i", str(bed), "-filter_complex",
          f"[0:a][1:a]amix=inputs=2:normalize=0,"
          f"aresample={C.SAMPLE_RATE}[out]",
          "-map", "[out]", "-c:a", "pcm_s16le", str(out_path)],
         "film audio")
    loud = measure_loudness(out_path)
    print(f"film audio: {loud['integrated']:.2f} LUFS, peak "
          f"{loud['true_peak']:.2f} dBFS")
    return {"path": str(out_path), **loud}


def main() -> int:
    ap = argparse.ArgumentParser(description="Mix the Wondenza voice + bed.")
    ap.add_argument("--clips", required=True,
                    help="clips.json from voice.py (paths + starts)")
    ap.add_argument("--bed", required=True, help="SFX+music bed wav")
    ap.add_argument("--film-dur", type=float, required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    clips = json.loads(Path(args.clips).read_text())
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    regions = [(c["start"], c["start"] + c["duration"]) for c in clips]
    stem = build_voice_stem(
        [{"path": c["path"], "start": c["start"], "duration": c["duration"]}
         for c in clips], args.film_dur, out_dir / "voice_stem.wav")
    bed = build_bed(Path(args.bed), Path(stem["path"]), regions,
                    out_dir / "bed_ducked.wav")
    mix_film_audio(Path(stem["path"]), Path(bed["path"]),
                   out_dir / "film_audio.wav")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
