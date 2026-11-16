# Style file: Kurzgesagt-style flat vector

## Sources
1. The 9 reference stills supplied in chat on 2026-11-16.
2. The reference video from the shared Drive link: `style/ref/ref.mp4`, 17 min 30 s, 1280x720, 30 fps.
   It is the Kurzgesagt Human Era / prehistory episode. The last ~1.5 min is a live-action calendar
   advertisement, which I excluded from the study.
   - Overview: one frame every 10 s as contact sheets (`style/ref/sheets/s01-s07.jpg`).
   - Motion: 15 to 30 fps bursts of label and title entrances (`style/ref/motion/`).
   - Colours: measured from decoded frames (dominant colours by pixel share), not eyeballed.

The reference material is for style study only. No frame, shape or sound from it goes into any output.

> **Not in this repo:** the reference video, its contact sheets and motion bursts are copyrighted and were
> deliberately left out. The paths above describe how the study was done. To repeat it on your own reference,
> follow `docs/03-style-system.md` (sampling frames, measuring colours and saturation, timing text entrances).
Nothing here comes from the One Ant test stills.

---

## 1. Colour scheme

Each scene uses one temperature family plus one accent. Fills are flat or soft two-stop vertical gradients.
Shadows are deeper, more saturated versions of the same hue (plum, maroon, navy). Never neutral grey or black.

Measured palettes (share of frame in brackets):

| Scene | Measured colours |
|---|---|
| Underground soil cross-section (skeleton in strata, 8:15) | `#7e2324` (24 %), `#581d2d` (21 %), `#44122a` (21 %), `#8d2e22` (13 %), `#691a29`, `#350a26` |
| Torch in canyon (night, 0:06) | `#480b26`, `#600e28`, `#2a0727`, `#7d1026`, sky `#2b1241`, light pool `#ae2c0f` |
| Campfire circle (night, 6:55) | ground `#100416` (56 %), `#210319`, `#29041f`, red glow `#490725` / `#7d142d` |
| Round window (0:45) | frame `#250e38` (51 %), interior `#f9b44b` / `#fdb74d`, rim `#823a25` |
| Archaeology dioramas (0:55) | top teal `#003c3c` / `#102c2c` fading to maroon-black `#2b1012` / `#18090a` |
| Timeline (1:25) | teal `#0a5e5e` (52 %), `#07514f` (36 %), bar green `#77ae3f` |
| Title card (2:58) | near-black navy `#010c16` (51 %), `#080b28`, indigo `#100a45` / `#14095f` |
| Karahan Tepe, daytime (3:15) | orange `#e56425`, sand `#d7ac4d`, mint sky `#77ecaf` / `#7feda2`, `#fd9934` |
| Ice-sheet map (11:25) | ocean blue `#0663d5`, ice white `#f6f1fd`, lilac `#dcd0fc`, land yellow `#f5e367` |

Rules:
- Night and underground scenes sit on plum, maroon and indigo. Day scenes sit on mint, sand and orange.
- Dark scenes often use a vertical two-zone gradient (teal at the top, maroon-black at the bottom) plus a darker vignette.
- Soil in cross-section is drawn as horizontal wavy strata in 4 to 6 maroon-plum tones, with small lighter pebble dots and buried objects.

## 2. Saturation

Measured share of highly saturated pixels (saturation > 0.75, brightness > 170):

| Scene | Share | Where the saturated colour is |
|---|---|---|
| Underground soil | 0.0 % | none; the bone white carries the focus |
| Archaeology diorama | 2.2 % | small teal label |
| Torch canyon | 6.7 % | the torch flame and its light pool (warm) |
| Round window | 6.8 % | the warm yellow interior |
| Campfire | 7.0 % | the fire (warm) |
| Karahan Tepe (day) | 29.8 % | spread over the whole landscape |
| Ice map (day) | 29.7 % | blue ocean |

Findings:
- In night, dark and underground scenes, the "one saturated warm colour" rule holds and is measurable:
  under 7 % of the frame is saturated, and it is the light source or the focus (flame, fire, lit window).
- In daytime landscapes and maps it does not hold. Saturation is spread across about 30 % of the frame.
- In 2 of the 9 stills the accent is cool (violet flowers, blue lake).
- For our ant clips, which are underground: muted maroon-plum soil, and the red ant as the one saturated warm colour.
  Keep saturated pixels under about 7 % of the frame, apart from brief flashes from emitting effects.

## 3. Glow

- Glow appears only on things that give off light: fire, torch flames, the sun, embers, the glowing title-card text,
  and the bright light at the end of a time tunnel.
- How the glow is built:
  - A near-white core, then a saturated orange-yellow ring, then a wide soft halo fading into the background.
  - A flat, lighter pool on the ground under the source (orange ellipse under the torch, deep red disc around the campfire).
    The pool has a soft edge but reads as a shape, not a blur.
  - Small round embers rising and fading above flames.
- Lit objects near a light get a solid rim-light shape (yellow) on the side facing the light. They do not glow.
- Objects away from the light sink toward the background colour. At the campfire, the outer ring of people is dim and low-contrast.
- Title cards are an exception: the big title text itself glows warm orange, as if it were a light.

## 4. Text and labels

Typography:
- Labels and banners use a heavy rounded geometric sans in white. Nunito 800-900 is a close free match.
- Big title cards ("HUMAN HISTORY", "DARK MATTER ERA") use a narrow, hand-cut display face in cream with an orange glow,
  and a small purple script-like line above ("The Year Zero of").
- Phrases are short: "Timeline", "Year 0", "Present Day", "Modern Archaeology", "Karahan Tepe", "Grains".

Containers:
- Ribbon banners with arrow-cut (hexagonal) ends, in a solid colour per topic: crimson on maps, teal and green on
  diagrams, orange for artefacts. Each banner has a darker drop shape offset downward by a few pixels.
- A smaller, semi-transparent italic sub-line under the banner ("Present-Day Türkiye", "Day 1").
- Small rounded tags ("-3000", "2026"), and round icon pins with a thick coloured ring and a pointer.

Motion, measured frame by frame at 30 fps:
- Banner first: it grows horizontally from a thin vertical sliver to full width in about 0.2 s (6 frames), with an ease-out.
- Then the text: the whole phrase rises up into the banner through a mask in about 0.1 to 0.15 s (3 to 4 frames).
  Kurzgesagt banners bring in the full phrase at once, not word by word.
- The sub-line arrives later. "Day 1" follows "Karahan Tepe" by several seconds, timed to the narration.
- Pins and tags pop in one after another, about 1 s apart, in narration order, each with a slight scale overshoot.
- Title cards: the word fades in from blurred and dim orange to sharp cream with a glow in about 0.6 s.
  The second word follows. Numbers build digit by digit ("-2" to "-20" to "-200" to "-2000").
- Your brief asks for callouts that pop in word by word, as in the tutorial. That differs from Kurzgesagt banners.
  My plan: for callouts (like "jaws locked"), the banner grows from a sliver as above, then each word pops in with a
  small overshoot, staggered about 0.15 s. Place labels and banners follow the Kurzgesagt way (whole phrase rises in).

## 5. Detail level and depth while staying 2D

- Shapes are simple rounded silhouettes with flat fills. Detail goes on the subject. Backgrounds are a few big shapes.
- Each object gets 2 to 3 tones: a base, a darker shade shape on one side, and a small lighter highlight shape.
  Rocks and stones get scattered small lighter speckle dots.
- Outlines are rare. Exceptions: isolated objects on dark ground (bones, skulls) get a dark outline darker than the background,
  sticker-style, so they separate. Landmasses on maps get a pale rim. Character portraits sit in white or coloured rings.
- Depth is layered, not drawn in perspective:
  - Far layers move toward the background colour and lose contrast.
  - Near layers are darker, more saturated and cropped by the frame edge.
  - Overlap does the rest, with no gaps and no strokes.
- Cutaway dioramas: interiors are shown as a cross-section of a solid block (houses, the earth), which suits an ant nest.
- The camera is never fully still. Wide shots drift slowly (Karahan Tepe pans steadily across about 15 s).
  Maps change scene by pushing in and crossfading to a more detailed map.
- Small repeated marks add texture without noise: wave ticks on water, tiny stars, embers, pebble dots, dashed route lines.

---

## Applying it to the ant fight clip (step 4)

- Scene: an ant nest in cross-section. Soil strata use the measured underground palette (`#7e2324`, `#581d2d`, `#44122a`,
  `#8d2e22`, `#691a29`, `#350a26`). Tunnels are darker cut channels (`#2a0a20`). Chambers are rounded pockets,
  slightly lighter on the floor. Pebble dots and small buried objects add texture. A thin dark night surface sits along the top.
- The red ant is the one saturated warm colour. The rival ant is a muted deep violet with lighter violet highlights.
- Only emitting things glow: the clash starburst and the lightning strike (white core, yellow ring, wide halo, short life).
  The ants get a flat yellow rim light on the side facing the flash while it lasts. They do not glow.
- The puddle is a teal-blue pool (close to the timeline teal `#0a5e5e`, lifted) with white dash highlights. It is the only cool accent.
- The "jaws locked" callout is a crimson arrow-cut banner with a darker drop shape. It grows from a sliver, then the words pop in.
- Depth: far chambers dim and close to the soil colour. Foreground roots and pebbles dark and cropped by the frame edge.
  The camera drifts slowly even when nothing else moves.
- Size check before rendering: ants must read at a glance at 1080p (the tutorial's ants started too faint).
