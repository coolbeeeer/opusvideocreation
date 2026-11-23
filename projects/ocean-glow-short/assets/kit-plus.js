/* kit-plus.js: additions to kit.js that push the look closer to a Kurzgesagt frame.
   Load after kit.js in the root <head>. Everything is seek-safe: state is a pure function of the timeline,
   randomness comes from K.rng, nothing reads the clock.

   KP.rig(layers)            parallax camera: one camera state drives several depth layers (d<1 far, d>1 near);
                             drop-in for K.camera (works with K.camTo / K.shake); c.pin() keeps HTML labels on world points
   KP.bact(parent, o)        bacterium with a rim light from a world light direction, optional eyes and shield aura
   KP.eyes(parent, o)        cartoon eyes: look (lx, ly), lid, blink, fear; KP.eyeTo / KP.blink tween them
   KP.softDot(...)           out-of-focus "bokeh" dot drawn with a radial gradient (no filter cost)
   KP.vignette(stage, a)     darkened frame edges (HTML overlay)
   KP.grain(stage, tl, dur)  seeded film grain that changes 24x per second, meant to hide banding in dark gradients
                             (costs render time and ~5x file size; see docs/11-style-upgrade.md)
*/
(function () {
  const K = window.KIT;
  const KP = (window.KITPLUS = {});
  let eyeN = 0;

  // ------------------------------------------------------------------ parallax camera
  KP.rig = (layers, o = {}) => {
    // screen centre: from the options, else from the film size in window.VO (vertical films), else 1920x1080
    const cx = o.cx ?? ((window.VO && window.VO.W) || 1920) / 2, cy = o.cy ?? ((window.VO && window.VO.H) || 1080) / 2;
    const c = { px: o.px ?? cx, py: o.py ?? cy, s: o.s ?? 1, rot: 0, sx: 0, sy: 0, pins: [] };
    c.view = (d) => ({ s: 1 + (c.s - 1) * d, px: cx + (c.px - cx) * d, py: cy + (c.py - cy) * d, sx: c.sx * d, sy: c.sy * d });
    c.toScreen = (x, y, d = 1) => {
      const v = c.view(d);
      return [(x - v.px) * v.s + cx + v.sx, (y - v.py) * v.s + cy + v.sy];
    };
    c.apply = () => {
      for (const L of layers) {
        const v = c.view(L.d);
        L.g.setAttribute("transform", `translate(${K.f(cx + v.sx)},${K.f(cy + v.sy)}) scale(${Math.round(v.s * 10000) / 10000}) translate(${K.f(-v.px)},${K.f(-v.py)})`);
      }
      for (const p of c.pins) {
        const [x, y] = c.toScreen(p.x, p.y, p.d);
        p.el.style.left = K.f(x) + "px";
        p.el.style.top = K.f(y) + "px";
      }
    };
    c.pin = (el, x, y, d = 1) => {
      c.pins.push({ el, x, y, d });
      c.apply();
      return el;
    };
    c.apply();
    return c;
  };

  // ------------------------------------------------------------------ eyes
  KP.eyes = (parent, o = {}) => {
    const r = o.r ?? 10, rx = r * 0.8, ry = r, gap = o.gap ?? r * 2.15, pr = r * 0.52;
    const g = K.el("g", { transform: `translate(${K.f(o.x || 0)},${K.f(o.y || 0)}) rotate(${K.f(-(o.rot || 0))})` }, parent);
    const parts = [];
    [-1, 1].forEach((sd) => {
      const id = `${o.prefix || "kp"}-eye${eyeN++}`;
      const eg = K.g(g, { transform: `translate(${K.f((sd * gap) / 2)},0)` });
      const cp = K.el("clipPath", { id }, eg);
      const shape = K.el("ellipse", { rx: K.f(rx), ry: K.f(ry) }, cp);
      const cg = K.g(eg, { "clip-path": `url(#${id})` });
      const white = K.el("ellipse", { rx: K.f(rx), ry: K.f(ry), fill: "#fbf8ff" }, cg);
      const pupil = K.el("circle", { r: K.f(pr), fill: "#1c1233" }, cg);
      const glint = K.el("circle", { r: K.f(pr * 0.34), fill: "#ffffff" }, cg);
      const lid = K.el("rect", { x: K.f(-rx * 1.4 - 2), y: K.f(-ry * 1.4 - 2), width: K.f(rx * 2.8 + 4), height: 0, fill: o.lid || "#7c9640" }, cg);
      parts.push({ shape, white, pupil, glint, lid });
    });
    const api = { g, lx: 0, ly: 0, lid: o.lidStart ?? 0, blink: 0, fear: 0 };
    api.update = () => {
      const k = 1 + api.fear * 0.22, prr = pr * (1 - api.fear * 0.4), lv = Math.min(1, Math.max(api.lid, api.blink));
      const erx = rx * k, ery = ry * k, mx = (erx - prr) * 0.8, my = (ery - prr) * 0.8;
      const px = api.lx * mx, py = api.ly * my;
      for (const p of parts) {
        p.shape.setAttribute("rx", K.f(erx));
        p.shape.setAttribute("ry", K.f(ery));
        p.white.setAttribute("rx", K.f(erx));
        p.white.setAttribute("ry", K.f(ery));
        p.pupil.setAttribute("cx", K.f(px));
        p.pupil.setAttribute("cy", K.f(py));
        p.pupil.setAttribute("r", K.f(prr));
        p.glint.setAttribute("cx", K.f(px - prr * 0.35));
        p.glint.setAttribute("cy", K.f(py - prr * 0.4));
        p.glint.setAttribute("r", K.f(prr * 0.34));
        p.lid.setAttribute("y", K.f(-ery - 2));
        p.lid.setAttribute("height", K.f((2 * ery + 4) * lv));
      }
    };
    api.update();
    return api;
  };
  KP.eyeTo = (tl, e, t, vars, dur = 0.25, ease = "power2.out") => tl.to(e, Object.assign({ duration: dur, ease, onUpdate: e.update }, vars), t);
  KP.blink = (tl, e, t) => {
    tl.to(e, { blink: 1, duration: 0.06, ease: "power1.in", onUpdate: e.update }, t);
    tl.to(e, { blink: 0, duration: 0.1, ease: "power1.out", onUpdate: e.update }, t + 0.06);
  };

  // ------------------------------------------------------------------ bacterium with rim light, eyes, shield aura
  /* o: L, r, pal, seed, flagSide, rot (its world rotation in degrees, used to keep light and eyes world-aligned),
        light [x, y] world direction of the key light (default top-left), eyes (bool), shield (bool), prefix */
  KP.bact = (parent, o = {}) => {
    const L = o.L ?? 150, r = o.r ?? 34, P = Object.assign({ rim: "#bcd66c" }, K.C.bact, o.pal || {});
    const w = Math.max(4, r * 0.17), R = K.rng(o.seed ?? 1), side = o.flagSide ?? 1, rot = o.rot ?? 0;
    const lw = o.light || [-0.62, -0.78];
    const la = Math.atan2(lw[1], lw[0]) - (rot * Math.PI) / 180, lx = Math.cos(la), ly = Math.sin(la), e = r * 0.15;
    const g = K.el("g", {}, parent);
    const flag = o.flag === false ? null : K.el("path", { fill: "none", stroke: P.flag, "stroke-width": K.f(Math.max(3, r * 0.15)), "stroke-linecap": "round" }, g);
    let aura = null, ring = null;
    if (o.shield) {
      aura = K.g(g, { opacity: 0 });
      K.el("path", { d: K.capsule(L + r * 0.5, r * 1.25), fill: "none", stroke: "#b9a2ff", "stroke-width": K.f(r * 1.25), opacity: 0.12 }, aura);
      K.el("path", { d: K.capsule(L + r * 0.5, r * 1.25), fill: "none", stroke: "#cdb8ff", "stroke-width": K.f(r * 0.6), opacity: 0.22 }, aura);
      ring = K.el("path", { d: K.capsule(L + r * 0.5, r * 1.25), fill: "none", stroke: K.C.res.ring, "stroke-width": K.f(r * 0.2), opacity: 0 }, g);
    }
    // rim light: a lit copy of the silhouette, with the dark wall pushed away from the light so a crescent shows
    const rim = K.el("path", { d: K.capsule(L, r), fill: P.rim }, g);
    const wall = K.el("path", { d: K.capsule(L, r), fill: P.wall, transform: `translate(${K.f(-lx * e)},${K.f(-ly * e)})` }, g);
    K.el("path", { d: K.capsule(L - 2 * w, r - w), fill: P.shade }, g);
    K.el("path", { d: K.capsule(L - 2 * w - r * 0.18, (r - w) * 0.8), fill: P.body, transform: `translate(${K.f(lx * r * 0.12)},${K.f(ly * r * 0.12)})` }, g);
    const hx = Math.sign(lx || 1) * L * 0.14, hy = Math.sign(ly || -1) * r * 0.48;
    K.el("path", { d: K.capsule(L * 0.34, r * 0.13), fill: P.hi, opacity: 0.9, transform: `translate(${K.f(hx)},${K.f(hy)})` }, g);
    const dots = K.el("g", { fill: P.dot, opacity: 0.85 }, g);
    for (let i = 0; i < 3; i++) {
      const sx = i % 2 ? 1 : -1;
      K.el("circle", { cx: K.f(sx * (L * 0.2 + R() * L * 0.12)), cy: K.f((R() - 0.5) * r * 0.5), r: K.f(r * (0.08 + R() * 0.05)) }, dots);
    }
    const eyes = o.eyes === false ? null : KP.eyes(g, { r: r * 0.4, gap: r * 0.9, rot, prefix: o.prefix, lid: o.lidColor || "#7f9a42", x: 0, y: -r * 0.02 });
    const api = { g, L, r, phase: R() * 6.28, amp: 1, side, ring, aura, eyes, rim, wall };
    api.update = () => {
      if (!flag) return;
      const x0 = side * (L / 2 - r * 0.15), len = L * 0.6, pts = [];
      for (let i = 0; i <= 14; i++) {
        const u = i / 14;
        pts.push([x0 + side * u * len, Math.sin(api.phase + u * 9) * r * 0.32 * u * api.amp]);
      }
      flag.setAttribute("d", K.smooth(pts, false));
    };
    api.update();
    return api;
  };

  // ------------------------------------------------------------------ soft light and texture
  KP.softDot = (parent, x, y, r, gradId, opacity) =>
    K.el("circle", { cx: K.f(x), cy: K.f(y), r: K.f(r), fill: `url(#${gradId})`, opacity: K.f(opacity) }, parent);

  KP.vignette = (stage, strength = 0.6, color = "6,3,16") => {
    const el = document.createElement("div");
    el.style.cssText = `position:absolute;inset:0;pointer-events:none;background:radial-gradient(ellipse 75% 70% at 50% 48%, rgba(${color},0) 55%, rgba(${color},${strength}) 100%);`;
    stage.appendChild(el);
    return el;
  };

  KP.grain = (stage, tl, dur, o = {}) => {
    const size = 256, cv = document.createElement("canvas");
    cv.width = cv.height = size;
    const ctx = cv.getContext("2d"), img = ctx.createImageData(size, size), R = K.rng(o.seed || 9);
    for (let i = 0; i < size * size; i++) {
      const v = Math.floor(96 + R() * 64);
      img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = v;
      img.data[i * 4 + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
    const el = document.createElement("div");
    el.style.cssText = `position:absolute;inset:0;pointer-events:none;background-image:url(${cv.toDataURL()});background-size:${size}px ${size}px;mix-blend-mode:overlay;opacity:${o.opacity ?? 0.5};`;
    stage.appendChild(el);
    const clock = { t: 0 }, fps = o.fps || 24;
    const place = () => {
      const r2 = K.rng(Math.floor(clock.t * fps) * 7919 + 17);
      el.style.backgroundPosition = `${Math.floor(r2() * size)}px ${Math.floor(r2() * size)}px`;
    };
    place();
    tl.fromTo(clock, { t: 0 }, { t: dur, duration: dur, ease: "none", immediateRender: false, onUpdate: place }, 0);
    return el;
  };
})();
