# 03 · The style system

The full measured guide is `style/STYLE.md`. This page is the working summary plus how to derive a style
from a reference yourself.

## The look in eight rules
1. **One temperature family per scene**, flat fills or soft two-stop gradients. Night/body/underground scenes sit
   on plum, maroon, indigo or deep teal; day scenes on mint, sand, orange.
2. **Shadows are deeper, more saturated versions of the same hue**, never grey or black.
3. **One saturated warm accent marks the focus** (in dark scenes, saturated pixels stay under ~7 % of the frame).
   In the antibiotics film the accent is the antibiotic itself: orange `#ff9000`. Bacteria are a muted lime,
   cells muted pink, viruses muted violet.
4. **Glow only on things that emit light** (fire, sun, flashes, the title text). Lit objects get a flat rim of
   colour on the side facing the light; they do not glow.
5. **2–3 tones per object**: base, a darker shade shape, a small lighter highlight shape. No outlines, except
   isolated objects on dark ground (sticker outline) and map landmasses.
6. **Depth by layering**: far layers fade toward the background colour; near layers are darker and cropped by the
   frame edge; overlap does the rest. Small repeated marks (specks, pebbles, wave ticks) add texture.
7. **The camera is never fully still.** Slow drift or push in every shot.
8. **Text**: heavy rounded sans (Nunito 900) in white on arrow-cut ribbon banners (with a darker drop shape) or
   small rounded tags. Short phrases. Banners grow sideways from a sliver in ~0.2 s, then words pop in one by one
   (~0.14 s stagger, back-out overshoot). Title cards: narrow display face (Yanone Kaffeesatz 700), cream
   `#fff1d6` with an orange glow, a small purple line above, a thin orange→purple→teal bar below.

## Palettes used in antibiotics_v2 (all in `lib/kit.js` → `K.C`)
| Element | Colours |
|---|---|
| Body interior background | radial `#123a4c` → `#071926`; resistance scene `#2a1a40` → `#0b0a1c` |
| Antibiotic (the accent) | base `#ff9000`, highlight `#ffc061`, shade `#c96400`, ring hole `#a24f00` |
| Bacterium | wall `#56702c`, shade `#6f8a34`, body `#8aa446`, highlight `#b4c870`, dots `#4e6626` |
| Red blood cell | `#a8384a`, rim `#bd4a5c`, core `#82283a` |
| White blood cell | `#e9e1f4`, shade `#cfc3e4`, nucleus `#9a86c4` |
| Virus | `#7656a6`, shade `#5c428a`, spikes `#8a6cbc`, knobs `#b49ae0` |
| Skin cross-section | epidermis `#f0c2aa` `#dca08a` `#c9846f`; dermis `#b45c78` → `#874062` |
| Banners | crimson `#9a1e5a`/`#5e0f38`, teal `#0e6e78`/`#073f45`, violet `#5b3d9a`/`#35225e`, green `#3d7a2c`/`#234a18` |
| Room (cold open) | wall `#1f4d5c` → `#143847`, table `#5c3a52`, shirt `#ece2cf`, skin `#c47a58`, hair `#3a1e4a` |

## Deriving a style from a reference (what was done; repeat it for a new look)
The human supplied 9 stills and a 17-minute reference video. The video was sampled, never reused.
```bash
# overview: one frame every 10 s as 4x4 contact sheets
ffmpeg -i ref.mp4 -vf "fps=1/10,scale=480:-1,tile=4x4" sheets/s%02d.jpg
# motion: a full-rate burst around a label entrance, cropped to the label
ffmpeg -ss 181.3 -t 1.6 -i ref.mp4 -vf "fps=20,crop=560:180:360:20,scale=320:-1,tile=6x6" -frames:v 1 motion/banner.jpg
```
- **Measure, don't eyeball** colours: decode a frame to raw RGB, quantise, report the dominant colours by pixel
  share, and the share of highly saturated pixels (saturation > 0.75 and brightness > 170). `tools/measure_style.py`
  does both. Eyeballed hex values from stills were wrong often enough to matter.
- **Verify timestamps** before sampling: the first contact-sheet mapping was off by 5 s and sampled the wrong scenes.
  Render a small grid of frames at the timestamps you intend to sample and look at it first.
- **Report where the rules break.** "One saturated warm colour" held in night scenes (≤ 7 %) but not in day
  scenes (~30 %), and the reference's banners bring whole phrases in at once while the brief wanted word-by-word;
  both were stated in the style file instead of being glossed over.

## Measured on the final film
Saturated-pixel share, sampled from the MP4: 0.0–4.1 % in every scene except the stomach shot (28.9 % for ~0.6 s,
when the opening capsule fills the frame). That exception is listed in `projects/antibiotics/REVIEW.md`.
