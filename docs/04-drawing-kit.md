# 04 · The drawing kit (`lib/kit.js`)

Loaded once in the root `<head>` as `window.KIT` (scenes use `const K = window.KIT`). Copy it into each project
as `assets/kit.js`. Everything is plain SVG built with `createElementNS`, deterministic, and returns either an SVG
group or a small API object with an `update()` method for animated parameters.

## Basics
| Function | Purpose |
|---|---|
| `K.el(tag, attrs, parent)` / `K.g(parent, attrs)` | create SVG elements |
| `K.rng(seed)` | seeded PRNG (mulberry32) → `() => [0,1)`. **Never use `Math.random()`.** |
| `K.f(n)` | round to 2 decimals for compact attribute strings |
| `K.poly(pts)`, `K.star(cx, cy, n, r1, r2, rot)` | polygon points; starbursts |
| `K.smooth(pts, closed)` | Catmull-Rom → cubic Bézier path through points |
| `K.blob(r, wobble, phase, n, seed, sx, sy)` | organic closed shape; animate `phase` for a living wobble |
| `K.capsule(L, r, waist)` | horizontal capsule centred at 0,0; `waist` 0..1 pinches the middle (cell division) |
| `K.C` | the palette (see docs/03) |

## Organisms and molecules
| Function | Returns | Notes |
|---|---|---|
| `K.bacterium(parent, {L, r, pal, seed, flagSide, flag, shield})` | `{g, waist, phase, amp, ring, badge, update()}` | set `phase` and call `update()` each frame to wiggle the flagellum; set `waist` to pinch; `shield:true` adds a resistance ring + badge (hide them with opacity until they "appear") |
| `K.mol(parent, kind, size)` | `g` | `"pen"` penicillin (4-ring fused to 5-ring + side chain), `"tet"` tetracycline (four fused hexagons), `"quin"` quinolone. Orange = antibiotic |
| `K.rbc(parent, r, tilt)` | `g` | red blood cell; `tilt` 0..1 squashes it for a 3/4 view |
| `K.wbc(parent, r, seed)` | `{g, phase, sx, sy, update()}` | white blood cell blob with lobed nucleus |
| `K.virus(parent, r, seed)` | `g` | spiky violet virus |
| `K.humanCell(parent, r, seed)` | `{g, phase, update()}` | soft pink cell with nucleus and organelles |

## Camera
```js
const cam = K.camera(svgGroup, 960, 540, 1.0);           // look at (px,py) with scale s
K.camTo(tl, cam, t, { px: 960, py: 395, s: 4.6 }, 0.75); // tween any of px, py, s, rot
K.shake(tl, cam, t, 26, 8, 0.045);                        // decaying shake on impacts
```
The camera is a transform on one `<g>` that contains the world. Draw backgrounds **far larger than the frame**
(e.g. `x=-2000 width=5920`) so zooms, pulls and shakes never reveal an edge.

## Text
```js
const ban = K.callout(uiDiv, { text: "Penicillin", x: 960, y: 140, color: "crimson", size: 64 });
const tag = K.tag(uiDiv, { text: "Cell wall", x: 640, y: 300, color: "green", size: 48, pointer: true });
const done = K.show(tl, ban, t);   // banner grows from a sliver, then words pop; returns when the last word lands
K.hide(tl, ban, t2);
```
Callouts/tags are HTML in a `.ui` layer above the SVG (crisp text, not affected by the camera). `x,y` is the
centre (callout) or the pointer tip (tag). `sound_effects` `pop_word()` reproduces `show()`'s timing exactly
(words at +0.16 s for banners, +0.06 s for tags, `stagger` apart).

## Narration timing
```js
const T0 = K.scene("wall").start;            // film time the scene starts
const at = (w, n = 1) => K.t(w, n, T0) - T0;  // scene-local time of the n-th "w" spoken at/after T0
tl.set(bact, { autoAlpha: 0 }, at("bursts"));
```
`K.t` throws if the word is not in the narration, which catches script/scene mismatches immediately.

## Patterns that worked
- **Binary fission without shape morphing:** draw two identical bacteria at the same spot (one looks like one
  cell), then tween them apart by about half their length. While their straight parts overlap the union is one
  longer cell; as the rounded ends separate a pinch appears; then they part. Give the left copy its flagellum on
  the left and the right copy on the right. Nest pairs for 1 → 2 → 4.
- **Failed division:** animate `waist` 0 → 0.42 → 0 with `back.out` on the way back.
- **Zoom into an object as a match cut** (opening): the camera tracks the moving capsule, accelerates its zoom
  (exponential, `power3.in`), and rotates so the capsule ends horizontal at the exact scale the next shot starts
  at; the next shot is the capsule filling the frame, which then splits open. Match orientation and scale, or
  the cut jumps.
- **Wipe to hide a shot change:** a full-screen layer (the gut wall) slides through the frame; switch the shots
  at the instant it covers the whole frame (compute that instant from the tween's ease).
- **Inset bubble:** an HTML circle with a 14 px white ring containing an inline SVG ("doctors call in help",
  "Your cells don't"). Pops in with `back.out`.
- **Two-segment IK arm:** solve the elbow from shoulder and hand target each frame, choose the solution with the
  elbow lower, draw the sleeve as a thick round-capped stroke, rotate the hand to the forearm angle.
- **Crowds that arrive in a wave:** delay each element by its distance from the source (`t0 + d / maxD * spread`).
- **Machines stop when jammed:** schedule their work loop only up to the jam time, then a grey tint overlay at
  ~55 % opacity reads as "frozen" without redrawing.

## Add-on kits
Load them after `kit.js` in the root `<head>`; each file's header lists its API.

| File | Global | What it adds |
|---|---|---|
| `lib/kit-plus.js` | `window.KITPLUS` (`KP`) | `KP.rig(layers)` parallax camera (one state, several depth layers, `cam.pin()` for labels), `KP.eyes` + `KP.eyeTo` + `KP.blink`, `KP.bact` (rim-lit bacterium with eyes and a shield aura), `KP.softDot`, `KP.vignette`, `KP.grain` |
| `lib/kit-ocean.js` | `window.OCEAN` (`KO`) | `KO.scene()` stage builder, `KO.glow` light sources, marine snow, twinkling lights, sunbeams, a depth gauge, and a deep-sea cast: lanternfish, anglerfish, hatchetfish, Atolla-style jellyfish, shrimp, dragonfish, fuel and enzyme characters |
| `lib/kit-human.js` | `window.HUMAN` (`KH`) | An articulated person and a procedural walk cycle (below). The maths half also loads in Node with `require` |
| `lib/kit-cell.js` | `window.CELL` (`KC`) | `KC.mito` (mitochondrion: double wall that can part, folds, DNA ring, eyes), `KC.guest` (the orange ancestral bacterium), `KC.host` (a wobbling cell that opens a pocket to swallow), `KC.thighSection` / `KC.fascicle` / `KC.fiber` (three tissue levels for a dive, each drawn around 0,0 and returning its bundles, fibres or mitochondria), `KC.atp`, `KC.sugar`, `KC.o2`, `KC.egg`, `KC.sperm`, `KC.balance` (dishes ride on the beam), `KC.cytoplasm` (out-of-focus cell interior for dark backgrounds; `update(t)` drifts it) |
| `lib/kit-space.js` | `window.SPACE` (`KS`) | `KS.stage` (a `KO.scene` with nebula, two star layers sized to the camera's reach, and dust), `KS.blackHole` (glow, accretion disk drawn as circles in a group squashed by `tilt` so it foreshortens, its near half again in front of the shadow, lensed arcs, photon ring; layers `back`, `mid` (under the shadow, clipped at the centre line: put things that fall in here) and `front`; `api.disk` dims the disk), `KS.stars`, `KS.nebula`, `KS.wisps`, `KS.dust`, `KS.clock` (`set(seconds)`), `KS.galaxy`, `KS.sun`, `KS.ship`, `KS.telescope`, `KS.noodle` (`set(top, bottom, x, w, phase)`), looks `KS.SUIT`, `KS.FRIEND`, `KS.LAB` and a weightless `KS.floatPose(t, o)` for `KH.human` |

Every creature returns an API object: set its numbers (`phase`, `jaw`, `flash`, `k`, ...) and call `update()`.
Redraw from the timeline's `onUpdate` (see `docs/09-pitfalls.md`) so tweened values are current when you draw.
`KP.bact` and `KC.guest` also take `len` (flagellum length, 1 = full, 0 = retracted).

## The walking person (`lib/kit-human.js`)
Worked example and a long explanation: `projects/mitochondria-short/NOTES.md`, question 1. Diagram:
`docs/walk-cycle.svg` (`node tools/walk_cycle_svg.cjs` redraws it).

| Call | Returns | Notes |
|---|---|---|
| `KH.walkPose(phase, gait?)` | joint positions (y-up body frame) | pure maths; phase in cycles, any real number |
| `KH.standPose()`, `KH.armTo(pose, arm, a1, a2)` | a pose | angles in degrees from hanging down, + = forward; arm 0 is the near arm |
| `KH.human(parent, { look })` | `{ g, setPose(pose), setFace(f), pose }` | the figure, facing +x, feet on y = 0; `look` overrides `KH.LOOK` colours and `hairStyle`, and switches on outfit parts: `suit` (long sleeves, `glove`), `helmet` (glass dome and collar; `visor`, `rim`), `pack` (a backpack colour), `stripe`, `glasses` |
| `h.setFace({ brow, mouth, open, eye })` | | expressions: `brow` + raises the brow (worry), - frowns; `mouth` + smile, - frown (0.8 rests); `open` 0..1 an "o" mouth; `eye` 1 normal, 0.15 closed, 1.4 wide |
| `KH.walker(parent, { x0, y0, look })` | `{ at(phase), x(phase), thighPoint(u) }` | a human plus its walk; `x(phase)` moves it exactly as far as a planted foot slides, so feet never skate |
| `KH.phaseTable(keys, t1)` | `phase(t)`, plus `.rate(t)` and `.strikes(ta, tb)` | speed keys `[[t, rate], ...]` eased and integrated: slow-motion without foot sliding; strikes for footstep sounds |

Use the same speed keys in the scene and in the audio script that places footsteps (`audio/js_events.cjs`).

## Dives through scales (`KP.zoomChain` in `lib/kit-plus.js`)
`KP.zoomChain(parent, levels, { prefix, W, H })` nests worlds: `levels[0] = { draw }`, and each next level
`{ draw, at, r, mag, fade?, ringOpacity? }` sits in a circular lens of radius `r` around `at` (a point or a function,
in the parent level's units) and is `mag` times more detailed. Drive it with `zc.set(Z, F)` (screen px per level-0
unit, and the level-0 point at the screen centre), open lenses with `zc.lens[i]`, and aim with `zc.point(i, p)`.
Key the zoom in log space so each tenfold step takes the same time. Each level gets one transform and levels that
are too small, too big or covered by a deeper lens are hidden, so a 3,370x dive renders as fast as a still.
Worked example: `projects/mitochondria-short/assets/world.js` and `compositions/walk.html`; NOTES.md question 6.
