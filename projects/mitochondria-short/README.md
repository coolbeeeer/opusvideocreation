# mitochondria-short: "The Bacteria That Moved Into Your Cells"

A vertical Kurzgesagt-style Short / Reel, 50.6 s, 1080x1920, 30 fps, burned-in captions, voice + effects + score,
-14 LUFS. It opens on a wide shot of a person walking through a park and dives, in one continuous zoom, into the
leg, a muscle bundle and a muscle fibre full of mitochondria, then tells how they were once free-living bacteria.

**Start with [`NOTES.md`](NOTES.md)**: it answers your seven questions (the human and the walk, pauses, grain,
empty frames, your own voice clips, the dive, and the two review passes).

| File | What it is |
|---|---|
| `renders/mitochondria-v2.mp4` | The film |
| `renders/mitochondria-cover.jpg` | Cover frame (title) for Reels / Shorts |
| `renders/mitochondria-v2-contact.jpg` | One frame every 1.5 s, taken from the MP4 |
| `captions.srt` | The captions as a subtitle file |
| `NOTES.md` | How it was made: answers to the seven questions |
| `SCRIPT.md` | Narration, shot table, accuracy notes with sources |
| `REVIEW.md` | Both review passes, measurements, failed or open checks |
| `film.json` | Script lines with per-line pauses, size, fps, voice |
| `assets/world.js` | The park, the walker and the four dive levels (used by the first and last scenes) |
| `compositions/` | One HTML file per scene, plus `captions.html` |
| `audio/` | Footstep times (`js_events.cjs`), cue sheet, score, mix |
| `review/` | Snapshot sheets from Pass 1, cut frames and measurements from Pass 2 |

Code to study for the human and the walk: `lib/kit-human.js` (the rig and the walk cycle),
`assets/world.js` (the walker in the park), `compositions/walk.html` (the walk slowing down for the dive), and the
diagram [`docs/walk-cycle.svg`](../../docs/walk-cycle.svg).

## Rebuild
```bash
export KOKORO_DIR=/path/to/kokoro HF_HOME=/path/to/hf-cache      # docs/01-environment.md
export HYPERFRAMES_FFMPEG_PATH=... HYPERFRAMES_FFPROBE_PATH=...  # only if FFmpeg is not on a system path
python vo.py && python align.py          # or: python vo.py --clips your_clips/   (one file per line)
cp ../../lib/kit.js ../../lib/kit-plus.js ../../lib/kit-ocean.js ../../lib/kit-human.js ../../lib/kit-cell.js assets/
python build.py
cd audio && node js_events.cjs && python sfx_cues.py && python music.py && python mix.py && cd ..
python build.py                          # mounts the mixed stems
npx hyperframes@0.9.56 check             # expect 0 errors, 0 warnings
npx hyperframes@0.9.56 render --fps 30 --quality delivery -o renders/mitochondria.mp4
python ../../tools/verify_render.py renders/mitochondria.mp4 --stems assets --fps 30 --duration 50.6
python ../../tools/frame_stats.py renders/mitochondria.mp4
```
`./dev.sh 1.0,2.5,4.0 name` copies the kits, rebuilds, and tiles snapshots of those film times into `review/name.jpg`.
`audio/js_events.cjs` must use the same speed keys as `walk.html` and `finale.html` (search for `phaseTable`).

## Uploading
- Shorts: upload the MP4 as is and add `captions.srt` as a subtitle track.
- Reels: upload the MP4 and choose `mitochondria-cover.jpg` as the cover.
- The captions are burned in; turn off the app's auto-captions if it adds a second set.
