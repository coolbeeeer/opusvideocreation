# ocean-glow-short: a vertical Kurzgesagt-style Short / Reel

"Why most animals in the open ocean glow", 54.2 s, 1080x1920, 30 fps, burned-in captions, voice + effects + score.
The same MP4 is made for YouTube Shorts and Instagram Reels (it also clears TikTok's safe areas).

| File | What it is |
|---|---|
| `renders/ocean-glow-v3.mp4` | The film |
| `renders/ocean-glow-cover.jpg` | Cover frame (title) for Reels / Shorts |
| `renders/ocean-glow-v3-contact.jpg` | One frame every 1.5 s, taken from the MP4 |
| `captions.srt` | The captions as a subtitle file (upload it too: it helps search and accessibility) |
| `SCRIPT.md` | Script, shot table, accuracy notes with sources |
| `REVIEW.md` | Both review passes, measurements, failed or open checks |
| `film.json` | Script lines with per-line pauses, size, fps, voice |
| `compositions/` | One HTML file per scene, plus `captions.html` |
| `audio/` | Cue sheet, score, mix |

## Rebuild
```bash
export KOKORO_DIR=/path/to/kokoro HF_HOME=/path/to/hf-cache      # docs/01-environment.md
export HYPERFRAMES_FFMPEG_PATH=... HYPERFRAMES_FFPROBE_PATH=...  # only if FFmpeg is not on a system path
python vo.py && python align.py          # or: python vo.py --recording your_voice.wav
cp ../../lib/kit.js ../../lib/kit-plus.js ../../lib/kit-ocean.js assets/
python build.py
cd audio && python sfx_cues.py && python music.py && python mix.py && cd ..
python build.py                          # mounts the mixed stems
npx hyperframes@0.9.56 check             # expect 0 errors, 0 warnings
npx hyperframes@0.9.56 render --fps 30 --quality delivery -o renders/ocean-glow.mp4
python ../../tools/verify_render.py renders/ocean-glow.mp4 --stems assets --fps 30 --duration 54.2
python ../../tools/frame_stats.py renders/ocean-glow.mp4
```
`./dev.sh 1.0,2.5,4.0 name` copies the kits, rebuilds, and tiles snapshots of those film times into `review/name.jpg`.

## Making another vertical film from this one
Copy the folder, replace `film.json` (lines + scenes) and the scene files, keep `captions.html`, `build.py`, `vo.py`,
`align.py` and `audio/mix.py`. Rewrite `audio/sfx_cues.py` and `audio/music.py` for the new scenes.
`docs/12-vertical-shorts.md` lists the rules for the format.

## Uploading
- Shorts: upload the MP4 as is (under 3 minutes and 9:16 makes it a Short). Add `captions.srt` as a subtitle track.
- Reels: upload the MP4, choose `ocean-glow-cover.jpg` as the cover.
- The burned-in captions are already in the picture; turn off auto-captions if the app adds a second set.
