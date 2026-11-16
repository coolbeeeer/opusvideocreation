# 02 · The HyperFrames contract

A film is a page whose state is a **pure function of time**. The renderer seeks the timeline to each frame
time (possibly out of order, across parallel workers) and screenshots. Anything not driven by the seek
(timers, `Date.now()`, `Math.random()`, CSS animations, network) breaks determinism.

## Root composition (`index.html`, written by `build.py`)
```html
<div id="root" data-composition-id="main" data-start="0" data-duration="60" data-width="1920" data-height="1080">
  <div id="host-wall" class="scene" style="z-index:4" data-composition-id="wall"
       data-composition-src="compositions/wall.html" data-start="21.3" data-duration="12.18"
       data-track-index="1" data-width="1920" data-height="1080"></div>
  ...
  <audio id="track-vo" src="assets/vo.wav" data-start="0" data-duration="60" data-track-index="10" data-volume="1"></audio>
</div>
<script>
  window.__timelines = window.__timelines || {};
  const tl = gsap.timeline({ paused: true });
  tl.set({}, {}, 60);                 // make the root timeline as long as the film
  window.__timelines["main"] = tl;
</script>
```
- Shared scripts (`assets/timing.js`, `assets/kit.js`, GSAP) load in the root `<head>`, so they exist before
  any scene script runs (verified with a two-scene test).
- `data-track-index` is only a Studio display lane. Later hosts get a higher `z-index` so overlaps layer correctly.
- Crossfades between scenes: overlap the hosts' time ranges and tween the host opacity on the root timeline
  (the cold open → skin scene crossfade does this).
- Audio: one `<audio>` per stem. `data-volume="1"` is 0 dB; the renderer sums the tracks, so keep the sum under
  0 dBFS yourself (`mix.py` does). Sync measured 0.0 ms against the WAVs.

## Scene file (`compositions/<id>.html`)
```html
<template id="wall-template">
  <div data-composition-id="wall" data-width="1920" data-height="1080" data-duration="12.18">
    <style>[data-composition-id="wall"] .stage { position:absolute; inset:0; overflow:hidden; }</style>
    <div class="stage"><svg viewBox="0 0 1920 1080">...</svg><div class="ui"></div></div>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <script>
      (function () {
        const R = document.querySelector('[data-composition-id="wall"]');
        const tl = gsap.timeline({ paused: true });
        // ... build art, add tweens at scene-local times ...
        tl.set({}, {}, DUR);
        window.__timelines = window.__timelines || {};
        window.__timelines["wall"] = tl;
      })();
    </script>
  </div>
</template>
```
- The scene timeline runs in **scene-local time** (0 = the host's `data-start`).
- All scenes share one DOM: query inside `R`, scope CSS with `[data-composition-id="..."]`, and **prefix every
  SVG id** (`wal-bg`, `inf-air`): `url(#id)` references are document-global.
- Use the same GSAP URL everywhere (the bundled example does; it is deduplicated).
- `build.py` rewrites `data-duration` here to match the host. Never edit it by hand.

## GSAP rules that matter for seeking
- Timelines are created `{ paused: true }`. Add tweens with absolute positions: `tl.to(el, vars, 1.5)`.
- `fromTo` tweens that start later must use `immediateRender: false`, or their "from" state is applied at
  time 0 and the element is wrong before the tween starts.
- Procedural state: tween a plain object and redraw in `onUpdate` (camera, flagella, wound shape, sparkles).
  For a shot with many coupled parts (the hand moving the capsule while the camera chases it) drive everything
  from one clock: `tl.fromTo(clock, {t:0}, {t:D, ease:"none", onUpdate: () => draw(clock.t)}, 0)` and compute
  every pose from `t` with `gsap.parseEase(...)` curves. This is seek-safe by construction.
- SVG transforms: GSAP **replaces** an element's `transform` attribute. If markup already has
  `transform="translate(...)"` and you tween that element, the original transform is lost (the ending scene's
  bottle vanished this way). Put the static transform on an inner `<g>` and tween the outer one.
- Rotation/scale pivots: pass `svgOrigin: "0 0"` (local origin, in the parent's coordinate space) on the first
  `gsap.set` of every object you will rotate or scale; the default pivot is not your object's centre.
- Two tweens on the same property that overlap in time: the one that *ends later* wins. The checker reports
  this as `gsap_tween_tail`.
- `repeat` must never compute to -1 (infinite). Clamp with `Math.max(0, ...)`.

## Checker findings and what to do
| Finding | Meaning / action |
|---|---|
| `missing_or_empty_sub_composition` | A host points at a scene file that does not exist yet (fine mid-build) |
| `gsap_tween_tail` | Earlier tween ends after a later one on the same property; shorten it or `overwrite:"auto"` |
| `gsap_repeat_floor_unclamped` | A computed repeat can be -1; clamp |
| `line_unread` | Text on screen too briefly: hold ≈ 0.5 s + 0.3 s per word; the closing line needs ≥ 2 s |
| `text_below_floor` | Text under 28 px. Decorative text (the "Rx" label) gets `data-layout-ignore="true"` |
| `rotation_pivot_drift` | Rotation not about the bbox centre. Intentional for hinges (legs, arms); review, don't "fix" |
| `dead_stretch` | Nothing changes for > 3 s (seen only while later scenes were unwritten) |
| `composition_file_too_large` / `nested_structure_needs_subcomposition` | Structure advice; no effect on output |
| `container_overflow` (info) | Elements outside the frame; expected for off-screen entrances |
