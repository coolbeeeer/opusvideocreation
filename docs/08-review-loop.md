# 08 · The review loop

The agent cannot watch video. It reviews by **looking at stills** and **measuring files**. Every scene went through
this loop at least twice; the film went through it twice more after rendering.

## Loop
1. `npx hyperframes check` → fix errors, read every warning (docs/02 has the table).
2. Snapshot the beats you just built, not evenly spaced frames:
   ```bash
   npx hyperframes snapshot --at 21.6,22.5,23.6,24.8,26.3,27.9,29.0,30.3,31.6,32.5,32.8,33.2 --no-end -o .snaps/wall
   ffmpeg -y -pattern_type glob -i '.snaps/wall/frame-*.png' -vf "scale=640:-1,tile=4x3:padding=4:color=0x202020" -frames:v 1 review/wall-v1.jpg
   ```
   Write each sheet to a **new filename** (image viewers may cache by path).
3. Look at the sheet and critique it against three questions, writing the answers in `REVIEW.md`:
   - **Too faint?** (dark-on-dark legs, a flash washing the frame grey, labels on busy areas)
   - **Too small?** (the first pass is always too small: ants 330 px in a 1400 px chamber, a 50 px capsule,
     thin mandibles that made "jaws locked" invisible)
   - **Wrong?** (an object poking through a wall, a hard edge from a shade shape, a background not covering a camera
     move, hair reading as a cap, a pivot in the wrong place, an empty first or last frame)
4. Fix, re-snapshot the same times, compare.
5. Render, then review **frames decoded from the MP4** (not snapshots):
   ```bash
   python tools/verify_render.py renders/film.mp4 --stems assets --duration 60 --sheet review/render-v1.jpg
   ```
   plus frames on both sides of every scene cut (`select='eq(n\,F1)+eq(n\,F2)...'`).
6. Fix what the render review finds (antibiotics v1 → v2: capsule too small, zoom overshoot, empty frame after
   the burst, empty frame at a scene start), re-render, re-verify.

## What "done" means (measured)
| Check | Target | antibiotics_v2 |
|---|---|---|
| frames | fps × duration | 3600 = 60 × 60.000 |
| loudness | ≈ -16 LUFS integrated | -15.8 |
| peak | ≤ -1 dBFS | -1.3 |
| sync | 0 ms vs stems | 0.0 ms |
| black frames | none | none |
| saturated share | ≲ 7 % in dark scenes | 0–4 %, one exception logged |
| checker | 0 errors; warnings reviewed | 1 structural warning |

## REVIEW.md format
For each pass: what was checked (which times), a table of problem → fix, then the final measurements, then a
**Failed or open checks** list. Copy `projects/antibiotics/REVIEW.md`. The failed/open list goes into the report
to the human verbatim; never drop an item because it is awkward.
