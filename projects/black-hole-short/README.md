# black-hole-short: "What Happens If You Fall Into a Black Hole?"

A vertical Kurzgesagt-style Short / Reel, 51.4 s, 1080x1920, 30 fps, burned-in captions, voice + effects + score,
-14 LUFS. An astronaut falls toward a small black hole and is stretched into a noodle; at a giant one they cross the
edge and feel nothing, while a friend far away sees them slow down, turn red and freeze; inside, every path leads to
the centre, where physics as we know it breaks down. Moral: pick a giant one. Or better, be the friend.

| File | What it is |
|---|---|
| `renders/black-hole-v3.mp4` | The film |
| `renders/black-hole-cover.jpg` | Cover frame (title) for Reels / Shorts |
| `renders/black-hole-v3-contact.jpg` | One frame every 1.5 s, taken from the MP4 |
| `captions.srt` | The captions as a subtitle file |
| `SCRIPT.md` | Narration, shot table, accuracy notes with sources |
| `REVIEW.md` | Both review passes, measurements, failed or open checks |
| `film.json` | Script lines with per-line pauses, size, fps, voice |
| `compositions/` | One HTML file per scene, plus `captions.html` |
| `audio/` | Cue sheet, score, mix; `cues.py` also has the friend scene's slowing-time keys |
| `review/` | Snapshot sheets from Pass 1, cut frames and measurements from Pass 2 |

## What is new in this film
- `lib/kit-space.js`: a space stage (`KS.stage`: gradient, nebula, two star layers, dust), a flat-style black hole
  whose disk foreshortens correctly (`KS.blackHole`: the disk is drawn as circles in a squashed group, its near half
  again in front of the shadow), and the noodle.
- `lib/kit-human.js` gained outfit and face options: `suit`, `helmet`, `pack`, `stripe`, `glasses`, and
  `setFace({ brow, mouth, open, eye })`. The astronauts are the same rig as the mitochondria film's walker.
- Spaghettification: the astronaut is scaled about the head (`scale(1/sqrt(k), k)`, so the feet race ahead while the
  head is held back), then crossfaded into `KS.noodle` at the same length; both live in the black hole's `mid` layer,
  which is drawn under the shadow and clipped at the centre line, so whatever crosses the edge disappears.
- Slowing time: the friend scene drives your drift, your clock, the ticks and a tape-stop on the music from one rate
  curve (`KH.phaseTable` in the picture, `cues.phase_table` in the audio), eased from 1 to 0.

## Rebuild
```bash
export KOKORO_DIR=/path/to/kokoro HF_HOME=/path/to/hf-cache      # docs/01-environment.md
export HYPERFRAMES_FFMPEG_PATH=... HYPERFRAMES_FFPROBE_PATH=...  # only if FFmpeg is not on a system path
python vo.py && python align.py          # or: python vo.py --clips your_clips/   (one file per line)
cp ../../lib/kit.js ../../lib/kit-plus.js ../../lib/kit-ocean.js ../../lib/kit-human.js ../../lib/kit-space.js assets/
python build.py
cd audio && python sfx_cues.py && python music.py && python mix.py && cd ..
python build.py                          # mounts the mixed stems
npx hyperframes@0.9.56 check             # expect 0 errors, 0 warnings; also try --samples=150
npx hyperframes@0.9.56 render --fps 30 --quality delivery -o renders/black-hole.mp4
python ../../tools/verify_render.py renders/black-hole.mp4 --stems assets --fps 30 --duration 51.4
python ../../tools/frame_stats.py renders/black-hole.mp4
```
`./dev.sh 1.0,2.5,4.0 name` copies the kits, rebuilds, and tiles snapshots of those film times into `review/name.jpg`.

## Uploading
- Shorts: upload the MP4 as is and add `captions.srt` as a subtitle track.
- Reels: upload the MP4 and choose `black-hole-cover.jpg` as the cover.
- The captions are burned in; turn off the app's auto-captions if it adds a second set.
