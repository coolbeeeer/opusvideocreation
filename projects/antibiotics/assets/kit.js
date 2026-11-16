/* Shared drawing kit for the antibiotics film. Loaded once in the root <head>.
   Everything here is deterministic (seeded PRNG, no Date/Math.random). */
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const K = (window.KIT = {});
  K.NS = NS;

  // ---------------------------------------------------------------- basics
  K.el = (tag, attrs, parent) => {
    const e = document.createElementNS(NS, tag);
    if (attrs) for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  };
  K.g = (parent, attrs) => K.el("g", attrs || {}, parent);
  K.rng = (seed) => {
    let a = seed >>> 0;
    return () => {
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };
  K.f = (n) => (Math.round(n * 100) / 100).toString();
  K.poly = (pts) => pts.map((p) => `${K.f(p[0])},${K.f(p[1])}`).join(" ");
  K.star = (cx, cy, n, r1, r2, rot = 0) => {
    const p = [];
    for (let i = 0; i < n * 2; i++) {
      const r = i % 2 ? r2 : r1, a = rot + (i * Math.PI) / n;
      p.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
    }
    return K.poly(p);
  };
  /* smooth closed blob through n points around (0,0) with radius r and wobble amount w */
  K.blob = (r, w, phase, n = 10, seed = 1, sx = 1, sy = 1) => {
    const R = K.rng(seed), off = [];
    for (let i = 0; i < n; i++) off.push([R() * 6.283, 0.5 + R()]);
    const pts = [];
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2;
      const rr = r * (1 + w * Math.sin(phase * off[i][1] + off[i][0]));
      pts.push([Math.cos(a) * rr * sx, Math.sin(a) * rr * sy]);
    }
    return K.smooth(pts, true);
  };
  /* Catmull-Rom to cubic Bezier through points */
  K.smooth = (pts, closed) => {
    const n = pts.length, P = (i) => pts[closed ? (i + n) % n : Math.max(0, Math.min(n - 1, i))];
    let d = `M ${K.f(pts[0][0])} ${K.f(pts[0][1])}`;
    const last = closed ? n : n - 1;
    for (let i = 0; i < last; i++) {
      const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
      const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += ` C ${K.f(c1[0])} ${K.f(c1[1])} ${K.f(c2[0])} ${K.f(c2[1])} ${K.f(p2[0])} ${K.f(p2[1])}`;
    }
    return d + (closed ? " Z" : "");
  };
  /* horizontal capsule centred at 0,0. L = total length, r = radius, waist 0..1 pinches the middle */
  K.capsule = (L, r, waist = 0) => {
    const a = Math.max(0.01, L / 2 - r), k = 0.5523 * r, p = waist * r * 0.95, f = K.f;
    const top = p > 0.01
      ? `C ${f(-a * 0.5)} ${f(-r)} ${f(-a * 0.3)} ${f(-r + p)} 0 ${f(-r + p)} C ${f(a * 0.3)} ${f(-r + p)} ${f(a * 0.5)} ${f(-r)} ${f(a)} ${f(-r)}`
      : `L ${f(a)} ${f(-r)}`;
    const bot = p > 0.01
      ? `C ${f(a * 0.5)} ${f(r)} ${f(a * 0.3)} ${f(r - p)} 0 ${f(r - p)} C ${f(-a * 0.3)} ${f(r - p)} ${f(-a * 0.5)} ${f(r)} ${f(-a)} ${f(r)}`
      : `L ${f(-a)} ${f(r)}`;
    return `M ${f(-a)} ${f(-r)} ${top} C ${f(a + k)} ${f(-r)} ${f(a + r)} ${f(-k)} ${f(a + r)} 0 C ${f(a + r)} ${f(k)} ${f(a + k)} ${f(r)} ${f(a)} ${f(r)} ${bot} C ${f(-a - k)} ${f(r)} ${f(-a - r)} ${f(k)} ${f(-a - r)} 0 C ${f(-a - r)} ${f(-k)} ${f(-a - k)} ${f(-r)} ${f(-a)} ${f(-r)} Z`;
  };

  // ---------------------------------------------------------------- palette (style/STYLE.md)
  K.C = {
    bact: { wall: "#56702c", shade: "#6f8a34", body: "#8aa446", hi: "#b4c870", dot: "#4e6626", flag: "#6c8436" },
    res: { ring: "#cdb8ff", badge: "#7a5ab8" },
    orange: { base: "#ff9000", hi: "#ffc061", shade: "#c96400", hole: "#a24f00" },
    rbc: { base: "#a8384a", rim: "#bd4a5c", core: "#82283a" },
    wbc: { base: "#e9e1f4", shade: "#cfc3e4", nuc: "#9a86c4", nucShade: "#7c68a8" },
    virus: { base: "#7656a6", shade: "#5c428a", hi: "#977ac6", spike: "#8a6cbc", knob: "#b49ae0" },
    cell: { mem: "#e6a2b2", base: "#cf8396", shade: "#b86c82", nuc: "#9a5476", nucHi: "#b06a8c", org: "#a85c78" },
    tissue: { epi1: "#f0c2aa", epi2: "#dca08a", epi3: "#c9846f", derm: "#b05a76", derm2: "#93466a", derm3: "#7a3a5e", fiber: "#c06a86" },
    water: { base: "#5cc8e0", hi: "#bff0fa" },
    ink: "#ffffff",
    banner: { crimson: ["#9a1e5a", "#5e0f38"], teal: ["#0e6e78", "#073f45"], violet: ["#5b3d9a", "#35225e"], green: ["#3d7a2c", "#234a18"] },
  };

  // ---------------------------------------------------------------- bacterium
  K.bacterium = (parent, o = {}) => {
    const L = o.L ?? 170, r = o.r ?? 36, P = o.pal ?? K.C.bact, w = o.wall ?? Math.max(4, r * 0.17);
    const R = K.rng(o.seed ?? 1), side = o.flagSide ?? 1;
    const g = K.el("g", {}, parent);
    const flag = o.flag === false ? null : K.el("path", { fill: "none", stroke: P.flag, "stroke-width": K.f(Math.max(3, r * 0.15)), "stroke-linecap": "round" }, g);
    const ring = o.shield ? K.el("path", { fill: "none", stroke: K.C.res.ring, "stroke-width": K.f(r * 0.26), opacity: 0.95 }, g) : null;
    const wall = K.el("path", { fill: P.wall }, g);
    const shade = K.el("path", { fill: P.shade }, g);
    const body = K.el("path", { fill: P.body }, g);
    const hi = K.el("path", { fill: P.hi, opacity: 0.9 }, g);
    const dots = K.el("g", { fill: P.dot }, g);
    for (let i = 0; i < 4; i++) {
      K.el("circle", { cx: K.f((R() - 0.5) * (L - 2 * r) * 0.9), cy: K.f((R() * 0.7 - 0.15) * r * 0.6), r: K.f(r * (0.09 + R() * 0.06)) }, dots);
    }
    const loop = K.el("path", { fill: "none", stroke: P.dot, "stroke-width": K.f(r * 0.07), "stroke-linecap": "round", opacity: 0.8,
      d: `M ${K.f(-L * 0.12)} ${K.f(r * 0.1)} c ${K.f(L * 0.05)} ${K.f(-r * 0.35)} ${K.f(L * 0.12)} ${K.f(r * 0.35)} ${K.f(L * 0.2)} 0 s ${K.f(L * 0.1)} ${K.f(r * 0.3)} ${K.f(L * 0.06)} ${K.f(r * 0.25)}` }, g);
    let badge = null;
    if (o.shield) {
      badge = K.el("g", { transform: `translate(${K.f(L * 0.06)},${K.f(-r * 0.02)}) scale(${K.f(r / 24)})` }, g);
      K.el("path", { d: "M0 -17 L13 -12 L13 0 C13 9 6 15 0 18 C-6 15 -13 9 -13 0 L-13 -12 Z", fill: "#ffffff" }, badge);
      K.el("path", { d: "M0 -12.5 L9 -9 L9 0 C9 6 4.5 10.5 0 13 C-4.5 10.5 -9 6 -9 0 L-9 -9 Z", fill: K.C.res.badge }, badge);
      K.el("path", { d: "M -4.5 0 L -1 3.5 L 5 -3.5", fill: "none", stroke: "#ffffff", "stroke-width": 2.6, "stroke-linecap": "round", "stroke-linejoin": "round" }, badge);
    }
    const api = { g, L, r, waist: 0, phase: R() * 6.28, amp: 1, side, ring, badge, dots, loop };
    api.update = () => {
      const wv = api.waist;
      wall.setAttribute("d", K.capsule(L, r, wv));
      if (ring) ring.setAttribute("d", K.capsule(L + r * 0.5, r * 1.25, wv));
      shade.setAttribute("d", K.capsule(L - 2 * w, r - w, wv));
      body.setAttribute("d", `${K.capsule(L - 2 * w - r * 0.18, (r - w) * 0.8, wv * 0.9)}`);
      body.setAttribute("transform", `translate(0,${K.f(-(r - w) * 0.17)})`);
      hi.setAttribute("d", K.capsule(L * 0.34, r * 0.13));
      hi.setAttribute("transform", `translate(${K.f(-L * 0.14)},${K.f(-r * 0.5)})`);
      if (flag) {
        const x0 = side * (L / 2 - r * 0.15), len = L * 0.6, pts = [];
        for (let i = 0; i <= 14; i++) {
          const u = i / 14;
          pts.push([x0 + side * u * len, Math.sin(api.phase + u * 9) * r * 0.32 * u * api.amp]);
        }
        flag.setAttribute("d", K.smooth(pts, false));
      }
    };
    api.update();
    return api;
  };

  // ---------------------------------------------------------------- molecules (orange = antibiotic)
  const ring = (cx, cy, n, s, rot) => {
    const R = s / (2 * Math.sin(Math.PI / n)), p = [];
    for (let i = 0; i < n; i++) {
      const a = rot + (i * 2 * Math.PI) / n;
      p.push([cx + Math.cos(a) * R, cy + Math.sin(a) * R]);
    }
    return p;
  };
  K.mol = (parent, kind = "pen", size = 1) => {
    const P = K.C.orange, g = K.el("g", {}, parent), inner = K.el("g", { transform: `scale(${K.f(size)})` }, g);
    const sw = 10, s = 30, rings = [], knobs = [], bonds = [];
    if (kind === "pen") {
      // penicillin core: 4-membered beta-lactam fused to a 5-membered ring, plus a side chain ring
      rings.push(ring(0, 0, 4, s, Math.PI / 4));
      const ap = s / (2 * Math.tan(Math.PI / 5));
      rings.push(ring(s / 2 + ap, 0, 5, s, Math.PI));
      rings.push(ring(-s * 1.55, -s * 1.15, 6, s * 0.78, 0));
      bonds.push([[-s / 2, -s / 2], [-s * 1.05, -s * 0.85]]);
      knobs.push([-s / 2 - 14, s / 2 + 12], [s / 2 + ap + 24, s * 0.62], [s / 2 + ap * 0.5, -s - 6]);
    } else if (kind === "tet") {
      // tetracycline: four fused six-membered rings
      const dx = s * Math.sqrt(3);
      for (let i = 0; i < 4; i++) rings.push(ring((i - 1.5) * dx, 0, 6, s, Math.PI / 6 + Math.PI / 2));
      knobs.push([-1.5 * dx, s * 1.65], [-0.5 * dx, s * 1.65], [0.5 * dx, -s * 1.65], [1.5 * dx + 18, s * 1.25]);
    } else {
      // quinolone: two fused six-membered rings plus a third ring hanging off
      const dx = s * Math.sqrt(3);
      rings.push(ring(-dx / 2, 0, 6, s, Math.PI / 6 + Math.PI / 2));
      rings.push(ring(dx / 2, 0, 6, s, Math.PI / 6 + Math.PI / 2));
      rings.push(ring(-dx * 1.55, s * 1.25, 6, s * 0.85, Math.PI / 6 + Math.PI / 2));
      bonds.push([[-dx, s / 2], [-dx * 1.2, s * 0.85]]);
      knobs.push([dx + 16, -s * 0.8], [dx * 0.5, -s * 1.7], [dx + 20, s * 0.9]);
    }
    for (const b of bonds) K.el("line", { x1: b[0][0], y1: b[0][1], x2: b[1][0], y2: b[1][1], stroke: P.base, "stroke-width": sw, "stroke-linecap": "round" }, inner);
    for (const k of knobs) K.el("circle", { cx: K.f(k[0]), cy: K.f(k[1]), r: 9, fill: P.hi }, inner);
    for (const p of rings) K.el("polygon", { points: K.poly(p), fill: P.hole, stroke: P.base, "stroke-width": sw, "stroke-linejoin": "round" }, inner);
    for (const p of rings) K.el("polygon", { points: K.poly(p.map((q, i) => q)), fill: "none", stroke: P.hi, "stroke-width": 3, "stroke-linejoin": "round", opacity: 0.55, transform: "translate(-1.5,-2)" }, inner);
    return g;
  };

  // ---------------------------------------------------------------- red blood cell
  K.rbc = (parent, r = 40, tilt = 0) => {
    const P = K.C.rbc, g = K.el("g", {}, parent), sy = 1 - Math.abs(tilt) * 0.55;
    K.el("ellipse", { rx: r, ry: K.f(r * sy), fill: P.base }, g);
    K.el("ellipse", { rx: K.f(r * 0.86), ry: K.f(r * sy * 0.86), fill: P.rim }, g);
    K.el("ellipse", { cx: 0, cy: K.f(r * 0.05), rx: K.f(r * 0.55), ry: K.f(r * sy * 0.5), fill: P.core }, g);
    K.el("path", { d: `M ${K.f(-r * 0.62)} ${K.f(-r * sy * 0.5)} Q ${K.f(-r * 0.2)} ${K.f(-r * sy * 0.9)} ${K.f(r * 0.3)} ${K.f(-r * sy * 0.72)}`, fill: "none", stroke: "#d86a7a", "stroke-width": K.f(r * 0.1), "stroke-linecap": "round", opacity: 0.7 }, g);
    return g;
  };

  // ---------------------------------------------------------------- white blood cell
  K.wbc = (parent, r = 120, seed = 3) => {
    const P = K.C.wbc, g = K.el("g", {}, parent);
    const body = K.el("path", { fill: P.base }, g);
    const shade = K.el("path", { fill: P.shade, opacity: 0.8 }, g);
    const inside = K.el("g", {}, g);
    const nuc = K.el("g", { fill: P.nuc }, g);
    [[-0.32, -0.08, 0.3], [0.05, -0.28, 0.27], [0.34, 0.02, 0.26], [0.02, 0.22, 0.24]].forEach(([x, y, s]) => K.el("circle", { cx: K.f(x * r), cy: K.f(y * r), r: K.f(s * r) }, nuc));
    K.el("path", { d: `M ${K.f(-0.4 * r)} ${K.f(0.05 * r)} Q 0 ${K.f(0.35 * r)} ${K.f(0.42 * r)} ${K.f(0.12 * r)}`, stroke: P.nucShade, "stroke-width": K.f(r * 0.1), fill: "none", "stroke-linecap": "round" }, nuc);
    const film = K.el("path", { fill: P.base, opacity: 0.35 }, g);
    const api = { g, r, phase: 0, sx: 1, sy: 1, inside };
    api.update = () => {
      const d = K.blob(r, 0.09, api.phase, 11, seed, api.sx, api.sy);
      body.setAttribute("d", d);
      film.setAttribute("d", d);
      shade.setAttribute("d", K.blob(r * 0.86, 0.08, api.phase + 1, 11, seed + 1, api.sx, api.sy));
      shade.setAttribute("transform", `translate(${K.f(r * 0.06)},${K.f(r * 0.1)})`);
    };
    api.update();
    return api;
  };

  // ---------------------------------------------------------------- virus
  K.virus = (parent, r = 70, seed = 5) => {
    const P = K.C.virus, g = K.el("g", {}, parent), n = 14;
    const sp = K.el("g", { stroke: P.spike, "stroke-width": K.f(r * 0.12), "stroke-linecap": "round", fill: P.knob }, g);
    for (let i = 0; i < n; i++) {
      const a = (i / n) * Math.PI * 2;
      K.el("line", { x1: K.f(Math.cos(a) * r * 0.9), y1: K.f(Math.sin(a) * r * 0.9), x2: K.f(Math.cos(a) * r * 1.32), y2: K.f(Math.sin(a) * r * 1.32) }, sp);
      K.el("circle", { cx: K.f(Math.cos(a) * r * 1.38), cy: K.f(Math.sin(a) * r * 1.38), r: K.f(r * 0.13), stroke: "none" }, sp);
    }
    K.el("circle", { r, fill: P.base }, g);
    K.el("circle", { cx: K.f(r * 0.08), cy: K.f(r * 0.1), r: K.f(r * 0.8), fill: P.shade }, g);
    K.el("circle", { cx: K.f(-r * 0.06), cy: K.f(-r * 0.06), r: K.f(r * 0.7), fill: P.base }, g);
    K.el("path", { d: `M ${K.f(-r * 0.5)} ${K.f(-r * 0.25)} Q ${K.f(-r * 0.35)} ${K.f(-r * 0.6)} ${K.f(0)} ${K.f(-r * 0.62)}`, fill: "none", stroke: P.hi, "stroke-width": K.f(r * 0.12), "stroke-linecap": "round" }, g);
    const R = K.rng(seed);
    for (let i = 0; i < 4; i++) K.el("path", { d: `M ${K.f((R() - 0.5) * r * 0.8)} ${K.f((R() - 0.4) * r * 0.8)} q ${K.f(r * 0.12)} ${K.f(-r * 0.1)} ${K.f(r * 0.24)} 0 t ${K.f(r * 0.24)} 0`, fill: "none", stroke: P.shade, "stroke-width": K.f(r * 0.07), "stroke-linecap": "round" }, g);
    return g;
  };

  // ---------------------------------------------------------------- human cell
  K.humanCell = (parent, r = 260, seed = 7) => {
    const P = K.C.cell, g = K.el("g", {}, parent), R = K.rng(seed);
    const mem = K.el("path", { fill: P.mem }, g);
    const body = K.el("path", { fill: P.base }, g);
    const shade = K.el("path", { fill: P.shade, opacity: 0.7 }, g);
    const org = K.el("g", {}, g);
    for (let i = 0; i < 5; i++) {
      const a = R() * 6.28, d = r * (0.45 + R() * 0.3);
      K.el("path", { d: K.capsule(r * 0.22, r * 0.06), fill: P.org, transform: `translate(${K.f(Math.cos(a) * d)},${K.f(Math.sin(a) * d)}) rotate(${K.f(R() * 180)})` }, org);
    }
    for (let i = 0; i < 3; i++) K.el("path", { d: `M ${K.f(-r * 0.5 + i * r * 0.08)} ${K.f(r * 0.3 + i * r * 0.06)} q ${K.f(r * 0.1)} ${K.f(-r * 0.08)} ${K.f(r * 0.2)} 0 t ${K.f(r * 0.2)} 0 t ${K.f(r * 0.2)} 0`, stroke: P.org, "stroke-width": K.f(r * 0.03), fill: "none", "stroke-linecap": "round" }, org);
    K.el("circle", { cx: K.f(r * 0.12), cy: K.f(-r * 0.08), r: K.f(r * 0.34), fill: P.nuc }, g);
    K.el("circle", { cx: K.f(r * 0.04), cy: K.f(-r * 0.16), r: K.f(r * 0.22), fill: P.nucHi }, g);
    K.el("circle", { cx: K.f(r * 0.2), cy: K.f(-r * 0.02), r: K.f(r * 0.08), fill: P.nuc }, g);
    const api = { g, r, phase: 0 };
    api.update = () => {
      mem.setAttribute("d", K.blob(r, 0.035, api.phase, 12, seed));
      body.setAttribute("d", K.blob(r * 0.93, 0.035, api.phase, 12, seed));
      shade.setAttribute("d", K.blob(r * 0.8, 0.04, api.phase + 0.5, 12, seed + 3));
      shade.setAttribute("transform", `translate(${K.f(r * 0.08)},${K.f(r * 0.1)})`);
    };
    api.update();
    return api;
  };

  // ---------------------------------------------------------------- camera
  /* svg group camera: looks at (px,py) with scale s; screen centre is (cx,cy) */
  K.camera = (g, px = 960, py = 540, s = 1, cx = 960, cy = 540) => {
    const c = { px, py, s, rot: 0, sx: 0, sy: 0 };
    c.apply = () => g.setAttribute("transform", `translate(${K.f(cx + c.sx)},${K.f(cy + c.sy)}) rotate(${K.f(c.rot)}) scale(${(Math.round(c.s * 10000) / 10000)}) translate(${K.f(-c.px)},${K.f(-c.py)})`);
    c.apply();
    return c;
  };
  K.camTo = (tl, c, t, vars, dur, ease = "power2.inOut") => tl.to(c, Object.assign({ duration: dur, ease, onUpdate: c.apply }, vars), t);
  K.shake = (tl, c, t, amp = 18, n = 7, step = 0.045) => {
    for (let i = 0; i < n; i++) {
      const k = 1 - i / n, sgn = i % 2 ? -1 : 1;
      tl.to(c, { sx: sgn * amp * k, sy: -sgn * amp * 0.6 * k, duration: step, ease: "none", onUpdate: c.apply }, t + i * step);
    }
    tl.to(c, { sx: 0, sy: 0, duration: step, ease: "none", onUpdate: c.apply }, t + n * step);
  };

  // ---------------------------------------------------------------- callouts (HTML)
  /* banner with arrow-cut ends; words pop in one by one */
  K.callout = (layer, o) => {
    const [face, drop] = K.C.banner[o.color || "crimson"];
    const el = document.createElement("div");
    const size = o.size || 60, h = Math.round(size * 1.55), cut = Math.round(h * 0.24);
    el.className = "kit-callout";
    el.style.cssText = `position:absolute;left:${o.x}px;top:${o.y}px;opacity:0;transform-origin:50% 50%;`;
    const clip = `polygon(${cut}px 0, calc(100% - ${cut}px) 0, 100% 50%, calc(100% - ${cut}px) 100%, ${cut}px 100%, 0 50%)`;
    el.innerHTML = `<div style="position:absolute;left:0;right:0;top:${Math.round(h * 0.1)}px;height:${h}px;background:${drop};clip-path:${clip}"></div>` +
      `<div style="position:relative;height:${h}px;background:${face};clip-path:${clip};display:flex;align-items:center;justify-content:center;gap:${Math.round(size * 0.34)}px;padding:0 ${Math.round(size * 1.05)}px;color:#fff;font-family:Nunito, sans-serif;font-weight:900;font-size:${size}px;white-space:nowrap;letter-spacing:0.005em">` +
      o.text.split(" ").map((w) => `<span class="w" style="display:inline-block;opacity:0;transform-origin:50% 70%">${w}</span>`).join("") + `</div>`;
    if (o.sub) {
      el.innerHTML += `<div class="sub" style="position:absolute;left:0;right:0;top:${h + Math.round(size * 0.35)}px;text-align:center;color:#ffffff;opacity:0;font-family:Nunito, sans-serif;font-weight:800;font-style:italic;font-size:${Math.round(size * 0.55)}px">${o.sub}</div>`;
    }
    layer.appendChild(el);
    gsapSetCenter(el);
    return el;
  };
  /* small rounded tag with an optional pointer */
  K.tag = (layer, o) => {
    const [face] = K.C.banner[o.color || "teal"];
    const size = o.size || 40;
    const el = document.createElement("div");
    el.className = "kit-tag";
    el.style.cssText = `position:absolute;left:${o.x}px;top:${o.y}px;opacity:0;transform-origin:50% 100%;`;
    el.innerHTML = `<div style="background:${face};border-radius:${Math.round(size * 0.35)}px;padding:${Math.round(size * 0.22)}px ${Math.round(size * 0.55)}px;display:flex;gap:${Math.round(size * 0.28)}px;color:#fff;font-family:Nunito, sans-serif;font-weight:900;font-size:${size}px;white-space:nowrap">` +
      o.text.split(" ").map((w) => `<span class="w" style="display:inline-block;opacity:0;transform-origin:50% 70%">${w}</span>`).join("") + `</div>` +
      (o.pointer === false ? "" : `<div style="width:0;height:0;margin:0 auto;border-left:${Math.round(size * 0.32)}px solid transparent;border-right:${Math.round(size * 0.32)}px solid transparent;border-top:${Math.round(size * 0.36)}px solid ${face}"></div>`);
    layer.appendChild(el);
    gsapSetCenter(el);
    return el;
  };
  function gsapSetCenter(el) {
    // centre the element on its x,y anchor
    window.gsap.set(el, { xPercent: -50, yPercent: el.className === "kit-tag" ? -100 : -50 });
  }
  K.show = (tl, el, t, stagger = 0.14) => {
    const isTag = el.className === "kit-tag";
    tl.set(el, { opacity: 1 }, t);
    if (isTag) tl.fromTo(el, { scale: 0.5 }, { scale: 1, duration: 0.24, ease: "back.out(2.4)", immediateRender: false }, t);
    else tl.fromTo(el, { scaleX: 0.03 }, { scaleX: 1, duration: 0.2, ease: "power3.out", immediateRender: false }, t);
    tl.fromTo(el.querySelectorAll(".w"), { opacity: 0, scale: 0.4, y: 12 }, { opacity: 1, scale: 1, y: 0, duration: 0.22, ease: "back.out(2.6)", stagger, immediateRender: false }, t + (isTag ? 0.06 : 0.16));
    const sub = el.querySelector(".sub");
    if (sub) tl.fromTo(sub, { opacity: 0, y: 10 }, { opacity: 0.8, y: 0, duration: 0.3, ease: "power2.out", immediateRender: false }, t + 0.5);
    return t + (isTag ? 0.06 : 0.16) + stagger * (el.querySelectorAll(".w").length - 1) + 0.22;
  };
  K.hide = (tl, el, t) => tl.to(el, { opacity: 0, scale: 0.85, duration: 0.18, ease: "power2.in" }, t);

  // ---------------------------------------------------------------- voice timing
  /* film time of the n-th occurrence of `word` at or after `after` seconds */
  K.t = (word, n = 1, after = 0) => {
    const key = word.toLowerCase().replace(/[^a-z0-9]/g, "");
    let k = 0;
    for (const w of window.VO.words) {
      if (w[1] >= after && w[0] === key && ++k === n) return w[1];
    }
    throw new Error("word not in narration: " + word);
  };
  K.scene = (id) => window.VO.scenes[id];
})();
