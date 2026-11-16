# Ant fight clip: self-review

> In this repo: `renders/ant-fight-sfx.mp4` is the final clip **with sound** (step 5). The silent
> render and `render-check.jpg` named below were working files and are not included.

Clip: 4.0 s, 1920x1080, 60 fps, silent. Style: `style/STYLE.md`.

## Pass 1 (snapshots at 0.3, 1.1, 1.32, 1.85, 2.55, 2.95, 3.7, 3.88 s)

What works:
- The beat order reads: squaring up, charge with speed lines, clash with starburst and bolt, "Jaws locked", throw, splash, dazed, "Out cold".
- The red ant is the one saturated warm colour. The soil uses the measured strata palette.
- Both callout banners grow from a sliver and the words pop in one by one.

Too faint:
1. The violet ant's legs and antennae (`#4a3470`, `#33224f`) almost vanish against the chamber cavity (`#24081c`). Its body reads, but its silhouette does not.
2. The red ant's far-side legs (`#8e1f1c`) are also too dark on the cavity.
3. The clash flash (45 % cream overlay) washes the whole frame grey at 1.32 s. It also hides the rim light on the ants, so the rim light is invisible.
4. The far chambers and tunnels are dim and disconnected. The tunnels are almost the same colour as the dark roots, so tunnels, roots and the shaft read as one tangle.

Too small:
5. The ants are about 330 px long in a chamber about 1400 px wide and 480 px tall. The top half of the chamber is empty.
6. The mandibles are thin 6 px strokes. "Jaws locked" is the callout, but the locked jaws themselves cannot be seen.
7. The puddle is a thin strip about 15 px deep. It reads as a line, not water.
8. The dazed sparkles (22 px) and the splash drops (6 to 14 px) are too small to register at speed.

Wrong:
9. After landing, the violet ant lies on top of the water rather than in it, and its head and mandibles poke through the right chamber wall into the soil.
10. A shade shape on the left back wall leaves a hard vertical edge at about x = 510 px. It looks like a rendering error.
11. The red ant keeps its jaws wide open through the ending, which reads as a gaping mouth.

## Fixes for pass 2
- Enlarge the ants from scale 1.7 to 2.1 (about 430 px long) and re-lay out the positions and the clash point.
- Enlarge the chamber: widen it to the right so the puddle bowl sits fully inside, and deepen the bowl.
- Lighten the violet palette (body `#7656b0`, legs `#8a6cc4`, far legs `#5e4596`) and the red far legs (`#a8302a`).
- Replace the stroke mandibles with large filled pincers that visibly interlock at the clash.
- Cut the flash overlay to 18 % so the starburst, bolt and rim light carry the hit.
- Enlarge the tunnels, connect them to the far chambers, and give tunnels and chambers a lighter floor lip so they separate from the roots. Thin the roots and give them a highlight stroke so they read as roots.
- Make the puddle larger and deeper, with a semi-transparent front water layer, so the thrown ant sinks into it.
- Land the thrown ant fully inside the chamber.
- Remove the back-wall shade shape.
- Sparkles from 22 px to 40 px. Splash drops from 10 to 18 px, with more height.
- Close the red ant's jaws after the throw.

## Pass 2 (snapshots at 0.3, 1.1, 1.33, 1.85, 2.55, 2.95, 3.75 s)

Fixed: ant size (now about 430 px), violet ant and far-leg contrast, filled mandibles, flash strength (rim light now visible),
connected tunnels with a lighter lip, roots with highlight strokes, bigger sparkles and drops, back-wall artefact removed.

Still wrong:
12. Closed mandibles still read as open crescents, so the "locked" moment looks like two open mouths touching.
13. The puddle is narrower than the ant. After landing, the abdomen lies on the dry floor and only the head is in the water.
14. The thrown ant's antennae point down through the bottom of the puddle into the soil.
15. Check warning `line_unread`: the closing callout "Out cold" was on screen for only 0.57 s.

## Pass 3 (snapshots at 1.85, 2.95, 3.3, 3.9 s)

Fixes: closed jaws now rotate past each other so they cross; puddle bowl widened from about 420 px to 560 px and deepened;
landing point moved so the whole ant sits in the water; antennae fold back during the fall; "Out cold" moved earlier,
from 3.2 s to 2.95 s.

Final render: `renders/ant-fight.mp4`, 1920x1080, 60 fps, 240 frames, 4.000 s, silent.
Verified on frames decoded from the MP4 (`renders/render-check.jpg`), not just on snapshots.

## Failed or open checks (not fixed)
- `line_unread` (warning): "Out" is on screen 0.83 s and "cold" 0.70 s. The checker wants a closing line held at least 2 s.
  This cannot be met inside a 4.0 s clip without cutting other beats. Options: extend the clip to about 5 s, or accept it.
- `rotation_pivot_drift` (7 warnings): the legs pivot at the hip and the thrown ant pivots at its feet. Both are intentional.
- `composition_file_too_large` and `nested_structure_needs_subcomposition` (2 warnings): the clip is one 430-line file.
  This is a structure suggestion only and does not affect the render.
- Style check: during the flash, saturated pixels go well above the 7 % target for about 0.25 s. That is allowed for emitting effects (STYLE.md section 2).

## Pass 4: sound (step 5)
- `sfx_cues.py` layers procedural sound effects (`sound_effects.py`) as `assets/sfx.wav`, mounted as an `<audio>` track in `index.html`.
- Measured: -18 LUFS, -1.6 dBFS peak, 0 ms offset between the rendered MP4 audio and the WAV.
