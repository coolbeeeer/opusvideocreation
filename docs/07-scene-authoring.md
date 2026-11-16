# 07 · From script to scenes

## 1. Script
- ~130 words per 60 s at a natural pace. Draft, time it with TTS, cut words rather than speed the voice up.
- One **line** = one idea = usually one scene. Short sentences: every sentence start is a free sync point.
- Write a shot table (`projects/antibiotics/SCRIPT.md` is the example): time, narration, picture, sound effects.
- Add accuracy notes for every claim; prefer current wording ("exactly as prescribed", not "always finish the course").
- Give each idea a **picture verb**: "jams" → a clamp closes on the molecule; "springs leaks" → crosslinks pop
  out and holes open; "share their defences" → a ring travels down a tube. If you cannot draw the verb, rewrite the line.

## 2. Shot design rules that held up
- **Start on motion and end on a beat.** The burst lands on the word "bursts"; the title lands while the last
  words are still being spoken.
- **One subject, one accent colour.** The saturated orange is reserved for the antibiotic in every scene.
- **Go in and come back out.** The wall scene starts wide on the bacterium, zooms 4.6x into the wall for the
  mechanism, then pulls back out for the consequence (holes, swelling, burst). Viewers keep their bearings.
- **Labels name what the voice names, when it names it.** Tags pop on the word; banners for concepts
  ("Penicillin", "Antibiotic resistance"), tags for things ("Cell wall", "Wall builders").
- **Insets for side remarks** ("Your cells don't" shows a soft membrane in a circle while the camera stays on the wall).
- **Keep transitions inside the pauses** between lines; cut on motion (dives, pulls) so the cut is not noticed.

## 3. The antibiotics_v2 breakdown
| Scene (file) | Film time | Beats → technique |
|---|---|---|
| `open` | 0.0–5.4 | person lifts capsule (IK arm, procedural clock) → camera dives into the capsule, rotating to match the next shot → capsule halves split in the stomach, molecules burst out → gut-wall wipe → bloodstream ride (walls scroll, RBCs drift with the flow, heartbeat pulses) → pull-out, crossfade |
| `infection` | 5.15–17.9 | skin cross-section; slash + V-shaped wound on "cut" → bacteria tumble in on "bacteria" → zoom to one, fission ×2 on "two", ×4 on "four" → pull back, swarm pops in by distance on "millions" → white blood cell squeezes out, engulfs 4 → more bacteria swamp it on "can't" → Rx bottle inset on "doctors" → orange molecules flood from the capillary + banner on "antibiotics" |
| `compare` | 17.9–21.3 | human cell vs bacterium slide in, tags on "bacteria" / "differently", glint on the wall, dive toward the bacterium |
| `wall` | 21.3–33.5 | wide → zoom into the mesh (beads + crosslink pegs) with builder enzymes adding pegs (clink each) → glint on "armour" → inset membrane "No wall" → penicillin banner + molecules → each molecule jams an enzyme on "jams", "tools", "build" → mesh stretches, pegs pop out on "springs leaks" → pull out, holes → water drops stream in, cell swells and wobbles → starburst + fragments + spray + shake on "bursts" |
| `machines` | 33.5–40.6 | cutaway cell: ribosome on mRNA growing a bead chain; tetracycline wedges in, tint + stop → DNA loop with copying clamp; quinolone locks it → zoom out, cell pinches and fails to divide, banner "Can't multiply" |
| `viruses` | 40.6–46.7 | three bacteria popped by molecules → four viruses arrive, banner + tags "Colds", "Flu" → molecules bounce off, "No effect" |
| `resistance` | 46.7–54.9 | wave of molecules sweeps a swarm; each pops as the wave passes its x → four survivors reveal shields → they divide → a newcomer receives a plasmid through a pilus and gains a shield → banner, colony grows, slow push |
| `ending` | 54.9–60.0 | Rx bottle + prescription; tags "Only when prescribed", "Exactly as prescribed"; dose ticks → title card (blur-to-sharp glow, gradient bar) held ≥ 2 s |

## 4. Scene file checklist
- [ ] `<template id="<id>-template">` wrapping a div with `data-composition-id="<id>"`
- [ ] CSS scoped with `[data-composition-id="<id>"]`; SVG ids prefixed with the scene id
- [ ] `T0 = K.scene(id).start`, `at = (w, n) => K.t(w, n, T0) - T0`; **no hardcoded speech times**
- [ ] backgrounds oversized for every camera move; camera never fully still
- [ ] `K.rng(seed)` for randomness; `svgOrigin: "0 0"` on rotated/scaled objects
- [ ] later `fromTo` tweens have `immediateRender: false`; nothing visible before it should be
- [ ] objects that will be tweened have no static `transform` attribute in markup (wrap them)
- [ ] the scene's first frame is not empty (things already in frame at the cut)
- [ ] every label gets a sound cue in `sfx_cues.py` with the same formula
- [ ] `timeline` registered as `window.__timelines["<id>"]`, with `tl.set({}, {}, DUR)`
