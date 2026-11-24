/* kit-ocean.js: deep-sea cast and environment for the Kurzgesagt-style look. Load after kit.js and kit-plus.js.
   Everything is seek-safe: built once, then driven by plain numbers that GSAP tweens and update() redraws.
   All creatures face right, are centred on (0,0) and carry KO.eye() eyes with the KP.eyeTo / KP.blink API.

   KO.scene(R, id, o)       standard stage: screen-space background, parallax layers, camera rig, UI layer
   KO.glowDefs(defs, p)     radial gradients for glows ("cyan", "blue", "green", "red", "warm", "white")
   KO.glow(parent, o)       emitter: soft halo + bright core; tween api.k (0..1) and call api.update()
   KO.snow / KO.sparks      marine snow; distant twinkling lights
   KO.eye(parent, o)        single eye (profile view)
   KO.fish, KO.angler, KO.hatchet, KO.jelly, KO.shrimp, KO.dragon, KO.fuel, KO.enzyme
   KO.rays(parent, o)       sunbeams under the surface
   KO.depthMeter(ui, o)     HTML depth gauge with a moving depth chip
*/
(function () {
  const K = window.KIT, KP = window.KITPLUS;
  const KO = (window.OCEAN = {});
  const f = K.f;

  // extra banner colours for kit.js callouts and tags (face, drop shadow)
  K.C.banner.amber = ["#b86d14", "#7a4609"];
  K.C.banner.ocean = ["#1c63b8", "#103d75"];
  K.C.banner.red = ["#b8282e", "#76161b"];

  KO.C = {
    glow: { cyan: "#7ff6ff", blue: "#4fb6ff", green: "#6bffcf", red: "#ff3b30", warm: "#ffd36b", white: "#ffffff" },
    snow: "#cfe6ff",
    fish: { base: "#e98552", shade: "#c4643a", hi: "#ffb27f", fin: "#f29a63", dark: "#a8502c" },
    dim: { base: "#3c5582", shade: "#2b3f66", hi: "#5f7cb0", fin: "#46628f", dark: "#1f2e4d" },
    big: { base: "#4b3263", shade: "#36234a", hi: "#6a4a86", fin: "#563a72", dark: "#2a1a3a" },
    angler: { base: "#3b2a52", shade: "#2a1d3c", hi: "#55407a", mouth: "#170c1f", teeth: "#f3efe2", rod: "#5b4880" },
    hatchet: { base: "#9fb5d2", shade: "#6b84a8", hi: "#e6f0fa", back: "#4c6286", fin: "#b9cbe3" },
    jelly: { base: "#8a2544", shade: "#5f1430", hi: "#b8456a", core: "#3e0c22", tent: "#9c3355" },
    shrimp: { base: "#d0493c", shade: "#9f2f2b", hi: "#f07d63", leg: "#b63a33" },
    dragon: { base: "#0c0f1d", sheen: "#2b3556", rim: "#3d4a78", teeth: "#e9e6dc" },
    fuel: { base: "#ffcf5a", shade: "#e2a93c", hi: "#fff0b8" },
    enzyme: { base: "#7069dc", shade: "#524cb6", hi: "#9b95f0" },
  };

  // ------------------------------------------------------------------ stage
  /* Builds the scene DOM inside R and returns handles. o: { bg: [top, bottom], pool: {x, y, rx, ry, color, a},
     layers: depth factors (default far .35, mid .7, act 1, near 1.6), blurNear (px, 0 = none) } */
  KO.scene = (R, id, o = {}) => {
    const W = window.VO.W || 1080, H = window.VO.H || 1920;
    const stage = document.createElement("div");
    stage.className = "stage";
    stage.style.cssText = `position:absolute;inset:0;overflow:hidden;background:${(o.bg || ["#06204a", "#020a1c"])[1]}`;
    R.appendChild(stage);
    const svg = K.el("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, style: "position:absolute;inset:0;overflow:visible" });
    stage.appendChild(svg);
    const defs = K.el("defs", {}, svg);
    const p = o.prefix || id.replace(/[^A-Za-z0-9]/g, "");   // SVG ids are document-global: one prefix per stage
    const bg = K.el("linearGradient", { id: `${p}-bg`, x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    (o.bg || ["#06204a", "#020a1c"]).forEach((c, i, a) => K.el("stop", { offset: i / (a.length - 1), "stop-color": c }, bg));
    K.el("rect", { x: 0, y: 0, width: W, height: H, fill: `url(#${p}-bg)` }, svg);
    KO.glowDefs(defs, p);
    const blurN = o.blurNear ?? 0;
    if (blurN) K.el("filter", { id: `${p}-bn`, x: "-30%", y: "-30%", width: "160%", height: "160%" }, defs).appendChild(K.el("feGaussianBlur", { stdDeviation: blurN }));
    const mk = (name, filt) => {
      const outer = K.g(svg, filt ? { filter: `url(#${filt})` } : {});
      const g = K.g(outer, { class: name });
      return { g, drift: K.g(g) };
    };
    const far = mk("L-far"), mid = mk("L-mid"), act = mk("L-act"), near = mk("L-near", blurN ? `${p}-bn` : null);
    const d = o.layers || [0.35, 0.7, 1, 1.6];
    const cam = KP.rig([{ g: far.g, d: d[0] }, { g: mid.g, d: d[1] }, { g: act.g, d: d[2] }, { g: near.g, d: d[3] }], { cx: W / 2, cy: H / 2, px: W / 2, py: H / 2 });
    if (o.pool) {
      const pl = o.pool;
      const rg = K.el("radialGradient", { id: `${p}-pool`, cx: 0.5, cy: 0.5, r: 0.5 }, defs);
      K.el("stop", { offset: 0, "stop-color": pl.color || "#2a6fb0", "stop-opacity": pl.a ?? 0.6 }, rg);
      K.el("stop", { offset: 1, "stop-color": pl.color || "#2a6fb0", "stop-opacity": 0 }, rg);
      K.el("ellipse", { cx: pl.x ?? W / 2, cy: pl.y ?? H / 2, rx: pl.rx ?? 800, ry: pl.ry ?? 900, fill: `url(#${p}-pool)` }, far.drift);
    }
    const ui = document.createElement("div");
    ui.className = "ui";
    ui.style.cssText = "position:absolute;inset:0;";
    stage.appendChild(ui);
    return { W, H, p, stage, svg, defs, far: far.drift, mid: mid.drift, act: act.drift, near: near.drift, ui, cam };
  };

  // ------------------------------------------------------------------ light
  KO.glowDefs = (defs, p) => {
    for (const [name, c] of Object.entries(KO.C.glow)) {
      const rg = K.el("radialGradient", { id: `${p}-gl-${name}`, cx: 0.5, cy: 0.5, r: 0.5 }, defs);
      [[0, 0.95], [0.18, 0.7], [0.45, 0.26], [0.75, 0.07], [1, 0]].forEach(([o, a]) => K.el("stop", { offset: o, "stop-color": c, "stop-opacity": a }, rg));
    }
  };
  /* o: { x, y, r (halo radius), color, p (scene prefix), core (core radius, 0 = none), k (start intensity) } */
  KO.glow = (parent, o) => {
    const outer = K.g(parent, { transform: `translate(${f(o.x || 0)},${f(o.y || 0)})` });
    const inner = K.g(outer);
    const halo = K.el("circle", { r: f(o.r || 60), fill: `url(#${o.p}-gl-${o.color || "cyan"})` }, inner);
    const core = o.core === 0 ? null : K.el("circle", { r: f(o.core || (o.r || 60) * 0.12), fill: "#ffffff" }, inner);
    const api = { g: outer, inner, halo, core, k: o.k ?? 1 };
    api.update = () => {
      const k = Math.max(0, api.k);
      inner.setAttribute("opacity", f(Math.min(1, k)));
      inner.setAttribute("transform", `scale(${f(0.55 + 0.45 * Math.min(k, 1.6))})`);
    };
    api.update();
    return api;
  };
  KO.snow = (parent, o = {}) => {
    const R = K.rng(o.seed || 3), g = K.g(parent);
    for (let i = 0; i < (o.n || 80); i++) {
      const x = (o.x0 ?? -200) + R() * ((o.x1 ?? 1280) - (o.x0 ?? -200)), y = (o.y0 ?? -200) + R() * ((o.y1 ?? 2120) - (o.y0 ?? -200));
      const r = (o.rmin ?? 1.2) + R() * ((o.rmax ?? 3.6) - (o.rmin ?? 1.2));
      if (R() < 0.3) K.el("ellipse", { cx: f(x), cy: f(y), rx: f(r * 1.6), ry: f(r * 0.8), fill: o.color || KO.C.snow, opacity: f((o.a ?? 0.35) * (0.4 + R() * 0.6)), transform: `rotate(${f(R() * 180)} ${f(x)} ${f(y)})` }, g);
      else K.el("circle", { cx: f(x), cy: f(y), r: f(r), fill: o.color || KO.C.snow, opacity: f((o.a ?? 0.35) * (0.4 + R() * 0.6)) }, g);
    }
    return g;
  };
  /* distant lights; returns {g, list:[{glow, x, y, t0}]}, call twinkle(tl, t0, t1) to blink them on */
  KO.sparks = (parent, o) => {
    const R = K.rng(o.seed || 5), g = K.g(parent), list = [];
    const cols = o.colors || ["cyan", "blue", "green"];
    for (let i = 0; i < (o.n || 30); i++) {
      const x = (o.x0 ?? 0) + R() * ((o.x1 ?? 1080) - (o.x0 ?? 0)), y = (o.y0 ?? 0) + R() * ((o.y1 ?? 1920) - (o.y0 ?? 0));
      const gl = KO.glow(g, { x, y, r: (o.rmin ?? 10) + R() * ((o.rmax ?? 34) - (o.rmin ?? 10)), color: cols[Math.floor(R() * cols.length)], p: o.p, k: o.k ?? 0, core: (o.core ?? 0.14) * ((o.rmin ?? 10) + R() * 10) });
      list.push({ glow: gl, x, y, ph: R() * 6.28, sp: 0.6 + R() * 1.6 });
    }
    return { g, list };
  };

  // ------------------------------------------------------------------ eye (profile)
  KO.eye = (parent, o = {}) => {
    const r = o.r ?? 12, pr = r * (o.pupil ?? 0.55);
    const g = K.g(parent, { transform: `translate(${f(o.x || 0)},${f(o.y || 0)})` });
    const id = `${o.p || "ko"}-e${KO._n = (KO._n || 0) + 1}`;
    const cp = K.el("clipPath", { id }, g);
    const shape = K.el("circle", { r: f(r) }, cp);
    if (o.ring) K.el("circle", { r: f(r * 1.18), fill: o.ring }, g);
    const cg = K.g(g, { "clip-path": `url(#${id})` });
    const white = K.el("circle", { r: f(r), fill: o.white || "#fbf8ff" }, cg);
    const pupil = K.el("circle", { r: f(pr), fill: o.iris || "#140d26" }, cg);
    const glint = K.el("circle", { r: f(pr * 0.34), fill: "#ffffff" }, cg);
    const lid = K.el("rect", { x: f(-r * 1.3), y: f(-r - 2), width: f(r * 2.6), height: 0, fill: o.lid || "#33274a" }, cg);
    const api = { g, lx: o.lx ?? 0.3, ly: o.ly ?? 0, lid: o.lidStart ?? 0, blink: 0, fear: 0 };
    api.update = () => {
      const k = 1 + api.fear * 0.18, er = r * k, prr = pr * (1 - api.fear * 0.42), m = (er - prr) * 0.78;
      shape.setAttribute("r", f(er));
      white.setAttribute("r", f(er));
      const px = api.lx * m, py = api.ly * m;
      pupil.setAttribute("cx", f(px)); pupil.setAttribute("cy", f(py)); pupil.setAttribute("r", f(prr));
      glint.setAttribute("cx", f(px - prr * 0.35)); glint.setAttribute("cy", f(py - prr * 0.4)); glint.setAttribute("r", f(prr * 0.34));
      const lv = Math.min(1, Math.max(api.lid, api.blink));
      lid.setAttribute("y", f(-er - 2)); lid.setAttribute("height", f((2 * er + 4) * lv));
    };
    api.update();
    return api;
  };

  // ------------------------------------------------------------------ small fish
  /* o: L, H, pal, p, photo (number of belly photophores), photoColor, teeth, eyeR, seed */
  KO.fish = (parent, o = {}) => {
    const L = o.L ?? 220, Hh = o.H ?? L * 0.46, P = o.pal || KO.C.fish, g = K.g(parent);
    const pt = (a, b) => [a * L, b * Hh];
    const tail = K.g(g);
    K.el("path", { d: `M ${f(-0.4 * L)} 0 L ${f(-0.72 * L)} ${f(-0.42 * Hh)} Q ${f(-0.6 * L)} 0 ${f(-0.72 * L)} ${f(0.42 * Hh)} Z`, fill: P.fin }, tail);
    K.el("path", { d: `M ${f(-0.3 * L)} ${f(-0.38 * Hh)} Q ${f(-0.12 * L)} ${f(-0.86 * Hh)} ${f(0.08 * L)} ${f(-0.46 * Hh)} Z`, fill: P.fin }, g);
    K.el("path", { d: `M ${f(-0.18 * L)} ${f(0.36 * Hh)} Q ${f(-0.1 * L)} ${f(0.7 * Hh)} ${f(0.04 * L)} ${f(0.44 * Hh)} Z`, fill: P.fin }, g);
    const body = [pt(0.5, 0.04), pt(0.36, -0.36), pt(0.08, -0.5), pt(-0.2, -0.38), pt(-0.42, -0.1), pt(-0.46, 0), pt(-0.42, 0.1), pt(-0.2, 0.34), pt(0.08, 0.47), pt(0.36, 0.36)];
    K.el("path", { d: K.smooth(body, true), fill: P.base }, g);
    K.el("path", { d: K.smooth([pt(0.47, 0.12), pt(0.34, 0.36), pt(0.08, 0.47), pt(-0.2, 0.34), pt(-0.42, 0.1), pt(-0.2, 0.18), pt(0.1, 0.22), pt(0.36, 0.16)], true), fill: P.shade }, g);
    K.el("path", { d: K.smooth([pt(0.3, -0.3), pt(0.06, -0.4), pt(-0.22, -0.26), pt(-0.02, -0.3)], true), fill: P.hi, opacity: 0.85 }, g);
    K.el("path", { d: `M ${f(0.22 * L)} ${f(-0.3 * Hh)} Q ${f(0.15 * L)} 0 ${f(0.22 * L)} ${f(0.3 * Hh)}`, fill: "none", stroke: P.dark, "stroke-width": f(Math.max(2.5, L * 0.016)), "stroke-linecap": "round", opacity: 0.7 }, g);
    if (o.teeth) {
      for (let i = 0; i < 5; i++) K.el("path", { d: `M ${f(0.5 * L - i * L * 0.035)} ${f(0.06 * Hh)} l ${f(-L * 0.012)} ${f(Hh * 0.13)} l ${f(-L * 0.012)} ${f(-Hh * 0.13)} Z`, fill: "#f3efe2" }, g);
    }
    K.el("path", { d: `M ${f(0.5 * L)} ${f(0.06 * Hh)} q ${f(-L * 0.06)} ${f(Hh * 0.08)} ${f(-L * 0.12)} ${f(Hh * 0.04)}`, fill: "none", stroke: P.dark, "stroke-width": f(Math.max(2, L * 0.012)), "stroke-linecap": "round" }, g);
    // light from its own photophores: a lit rim along the belly, shown in proportion to api.light()
    const rim = o.photo ? K.el("path", { d: K.smooth([pt(0.46, 0.14), pt(0.34, 0.36), pt(0.08, 0.47), pt(-0.2, 0.34), pt(-0.4, 0.11)], false), fill: "none", stroke: KO.C.glow[o.photoColor || "cyan"], "stroke-width": f(L * 0.022), "stroke-linecap": "round", opacity: 0 }, g) : null;
    const photos = [];
    for (let i = 0; i < (o.photo || 0); i++) {
      const u = i / Math.max(1, o.photo - 1), x = (0.3 - u * 0.62) * L, y = (0.34 - Math.abs(u - 0.45) * 0.22) * Hh;
      photos.push(KO.glow(g, { x, y, r: L * (o.photoR ?? 0.08), color: o.photoColor || "cyan", p: o.p, core: L * 0.014, k: o.photoK ?? 0 }));
    }
    const eye = KO.eye(g, { x: 0.27 * L, y: -0.07 * Hh, r: o.eyeR ?? Hh * 0.16, p: o.p, lid: P.dark, lx: 0.4 });
    const api = { g, L, H: Hh, tail, eye, photos, rim, phase: (o.seed || 1) * 1.7, amp: 1 };
    api.update = () => tail.setAttribute("transform", `rotate(${f(Math.sin(api.phase) * 11 * api.amp)} ${f(-0.42 * L)} 0)`);
    api.light = (k) => {
      photos.forEach((p) => { p.k = k; p.update(); });
      if (rim) rim.setAttribute("opacity", f(Math.min(1, k) * 0.75));
    };
    if (o.photoK) api.light(o.photoK);
    api.update();
    return api;
  };

  // ------------------------------------------------------------------ anglerfish
  /* big round body; the mouth is a crescent across the front whose lower edge drops as api.jaw goes 0 -> 1 */
  KO.angler = (parent, o = {}) => {
    const r = o.r ?? 170, P = KO.C.angler, g = K.g(parent);
    const tail = K.g(g);
    K.el("path", { d: `M ${f(-0.9 * r)} ${f(-0.05 * r)} L ${f(-1.42 * r)} ${f(-0.5 * r)} Q ${f(-1.22 * r)} ${f(-0.05 * r)} ${f(-1.42 * r)} ${f(0.42 * r)} Z`, fill: P.hi }, tail);
    K.el("path", { d: `M ${f(-0.2 * r)} ${f(-0.9 * r)} Q ${f(-0.5 * r)} ${f(-1.25 * r)} ${f(-0.75 * r)} ${f(-0.72 * r)} Z`, fill: P.hi }, g);
    K.el("path", { d: K.blob(r, 0.05, 1.3, 12, 31, 1.08, 0.88), fill: P.base, transform: `translate(${f(-0.04 * r)},${f(-0.08 * r)})` }, g);
    K.el("path", { d: K.blob(r * 0.86, 0.06, 2, 10, 32, 1.04, 0.62), fill: P.shade, opacity: 0.7, transform: `translate(${f(-0.08 * r)},${f(0.26 * r)})` }, g);
    const R = K.rng(o.seed || 9);
    for (let i = 0; i < 10; i++) K.el("circle", { cx: f((R() - 0.65) * r * 1.3), cy: f((R() - 0.85) * r * 0.75), r: f(r * (0.025 + R() * 0.03)), fill: P.hi, opacity: 0.7 }, g);
    const mouth = K.el("path", { fill: P.mouth }, g);
    const tongue = K.el("path", { fill: "#3a1430" }, g);
    const upT = K.g(g, { fill: P.teeth }), loT = K.g(g, { fill: P.teeth });
    const H0 = [-0.3 * r, 0.12 * r], T = [1.0 * r, -0.02 * r], CU = [0.4 * r, 0.32 * r];
    const qb = (p0, c, p1, u) => [(1 - u) * (1 - u) * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0], (1 - u) * (1 - u) * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1]];
    const upPts = [], teethN = 7;
    for (let i = 0; i < teethN; i++) {
      const u = 0.16 + (i * 0.7) / (teethN - 1), [x, y] = qb(H0, CU, T, u), len = r * (0.13 + (i % 2) * 0.08) * Math.sin(u * Math.PI);
      K.el("path", { d: `M ${f(x - r * 0.04)} ${f(y - 1)} L ${f(x + r * 0.01)} ${f(y + len)} L ${f(x + r * 0.045)} ${f(y - 1)} Z` }, upT);
      upPts.push(u);
    }
    const lowEls = [];
    for (let i = 0; i < teethN - 1; i++) lowEls.push(K.el("path", {}, loT));
    const lip = K.el("path", { fill: "none", stroke: P.hi, "stroke-width": f(r * 0.05), "stroke-linecap": "round", opacity: 0.8 }, g);
    const rim = K.el("path", { d: `M ${f(-0.05 * r)} ${f(-0.93 * r)} Q ${f(0.72 * r)} ${f(-0.86 * r)} ${f(1.0 * r)} ${f(-0.3 * r)}`, fill: "none", stroke: "#9ff7e8", "stroke-width": f(r * 0.06), "stroke-linecap": "round", opacity: 0.55 }, g);
    K.el("path", { d: `M ${f(-0.36 * r)} ${f(0.3 * r)} q ${f(-0.25 * r)} ${f(0.22 * r)} ${f(-0.44 * r)} ${f(0.1 * r)} q ${f(0.1 * r)} ${f(-0.26 * r)} ${f(0.44 * r)} ${f(-0.1 * r)} Z`, fill: P.hi }, g);
    const eye = KO.eye(g, { x: 0.5 * r, y: -0.44 * r, r: r * 0.09, p: o.p, lid: P.shade, lx: 0.6, ly: 0.3 });
    const rod = K.el("path", { fill: "none", stroke: P.rod, "stroke-width": f(r * 0.045), "stroke-linecap": "round" }, g);
    const lureG = K.g(g);
    const lure = KO.glow(lureG, { r: r * 1.2, color: "green", p: o.p, core: r * 0.05 });
    K.el("circle", { r: f(r * 0.08), fill: "#d8fff6" }, lureG);
    const api = { g, r, jaw: 0, sway: 0, eye, lure, tail, rim, phase: 0, lx: 0, ly: 0 };
    api.update = () => {
      const CL = [0.4 * r, 0.32 * r + api.jaw * 0.62 * r], TL = [1.04 * r, 0.02 * r + api.jaw * 0.3 * r];
      const lo = (u) => qb(H0, CL, TL, u);
      mouth.setAttribute("d", `M ${f(H0[0])} ${f(H0[1])} Q ${f(CU[0])} ${f(CU[1])} ${f(T[0])} ${f(T[1])} L ${f(TL[0])} ${f(TL[1])} Q ${f(CL[0])} ${f(CL[1])} ${f(H0[0])} ${f(H0[1])} Z`);
      const [tx, ty] = lo(0.45);
      tongue.setAttribute("d", `M ${f(H0[0] + r * 0.1)} ${f(H0[1] + r * 0.02)} Q ${f(tx)} ${f(ty - r * 0.02 - api.jaw * r * 0.18)} ${f(tx + r * 0.35)} ${f(ty - r * 0.03)} Q ${f(tx)} ${f(ty + r * 0.01)} ${f(H0[0] + r * 0.1)} ${f(H0[1] + r * 0.06)} Z`);
      tongue.setAttribute("opacity", f(Math.min(1, api.jaw * 1.5)));
      lowEls.forEach((el, i) => {
        const u = 0.22 + (i * 0.62) / (teethN - 2), [x, y] = lo(u), len = r * (0.12 + ((i + 1) % 2) * 0.08) * Math.sin(u * Math.PI) * (0.4 + 0.6 * Math.min(1, api.jaw * 2 + 0.2));
        el.setAttribute("d", `M ${f(x - r * 0.04)} ${f(y + 1)} L ${f(x + r * 0.01)} ${f(y - len)} L ${f(x + r * 0.045)} ${f(y + 1)} Z`);
      });
      lip.setAttribute("d", `M ${f(H0[0])} ${f(H0[1] + r * 0.03)} Q ${f(CL[0])} ${f(CL[1] + r * 0.06)} ${f(TL[0])} ${f(TL[1] + r * 0.03)}`);
      // the lure dangles just in front of the mouth, on a rod that arcs forward from the forehead
      const sx = Math.sin(api.sway) * r * 0.07, sy = Math.cos(api.sway * 1.3) * r * 0.06;
      api.lx = (o.lureX ?? 1.36) * r + sx; api.ly = (o.lureY ?? -0.62) * r + sy;
      rod.setAttribute("d", `M ${f(0.22 * r)} ${f(-0.9 * r)} Q ${f(1.0 * r)} ${f(-1.7 * r)} ${f(api.lx)} ${f(api.ly)}`);
      lureG.setAttribute("transform", `translate(${f(api.lx)},${f(api.ly)})`);
      tail.setAttribute("transform", `rotate(${f(Math.sin(api.phase) * 6)} ${f(-0.9 * r)} 0)`);
    };
    api.update();
    return api;
  };

  // ------------------------------------------------------------------ hatchetfish
  KO.hatchet = (parent, o = {}) => {
    const L = o.L ?? 260, Hh = L * 0.9, P = KO.C.hatchet, g = K.g(parent);
    const tailD = `M ${f(-0.4 * L)} ${f(-0.12 * Hh)} L ${f(-0.66 * L)} ${f(-0.3 * Hh)} L ${f(-0.6 * L)} ${f(-0.08 * Hh)} L ${f(-0.66 * L)} ${f(0.12 * Hh)} L ${f(-0.4 * L)} ${f(-0.02 * Hh)} Z`;
    const dorsalD = `M ${f(-0.1 * L)} ${f(-0.34 * Hh)} L ${f(-0.22 * L)} ${f(-0.56 * Hh)} L ${f(-0.32 * L)} ${f(-0.28 * Hh)} Z`;
    K.el("path", { d: tailD, fill: P.fin }, g);
    K.el("path", { d: dorsalD, fill: P.fin }, g);
    // hatchet profile: straight back, deep sharp keel under the chest, long thin tail
    const outline = `M ${f(0.47 * L)} ${f(-0.2 * Hh)} C ${f(0.4 * L)} ${f(-0.34 * Hh)} ${f(0.2 * L)} ${f(-0.38 * Hh)} ${f(0.0)} ${f(-0.36 * Hh)} ` +
      `C ${f(-0.22 * L)} ${f(-0.32 * Hh)} ${f(-0.36 * L)} ${f(-0.2 * Hh)} ${f(-0.46 * L)} ${f(-0.12 * Hh)} L ${f(-0.46 * L)} ${f(-0.02 * Hh)} ` +
      `C ${f(-0.34 * L)} ${f(0.02 * Hh)} ${f(-0.16 * L)} ${f(0.16 * Hh)} ${f(0.04 * L)} ${f(0.5 * Hh)} ` +
      `C ${f(0.14 * L)} ${f(0.54 * Hh)} ${f(0.22 * L)} ${f(0.44 * Hh)} ${f(0.3 * L)} ${f(0.3 * Hh)} C ${f(0.4 * L)} ${f(0.14 * Hh)} ${f(0.48 * L)} ${f(0.0)} ${f(0.47 * L)} ${f(-0.2 * Hh)} Z`;
    K.el("path", { d: outline, fill: P.base }, g);
    K.el("path", { d: `M ${f(-0.34 * L)} ${f(0.02 * Hh)} C ${f(-0.16 * L)} ${f(0.16 * Hh)} ${f(-0.02 * L)} ${f(0.4 * Hh)} ${f(0.04 * L)} ${f(0.5 * Hh)} C ${f(0.14 * L)} ${f(0.54 * Hh)} ${f(0.22 * L)} ${f(0.44 * Hh)} ${f(0.3 * L)} ${f(0.3 * Hh)} C ${f(0.38 * L)} ${f(0.18 * Hh)} ${f(0.44 * L)} ${f(0.08 * Hh)} ${f(0.46 * L)} ${f(0.0)} C ${f(0.2 * L)} ${f(0.12 * Hh)} ${f(-0.1 * L)} ${f(0.08 * Hh)} ${f(-0.34 * L)} ${f(0.02 * Hh)} Z`, fill: P.shade }, g);
    K.el("path", { d: `M ${f(0.44 * L)} ${f(-0.24 * Hh)} C ${f(0.3 * L)} ${f(-0.36 * Hh)} ${f(0.1 * L)} ${f(-0.37 * Hh)} ${f(-0.05 * L)} ${f(-0.35 * Hh)} C ${f(-0.24 * L)} ${f(-0.3 * Hh)} ${f(-0.38 * L)} ${f(-0.18 * Hh)} ${f(-0.45 * L)} ${f(-0.11 * Hh)} C ${f(-0.2 * L)} ${f(-0.2 * Hh)} ${f(0.1 * L)} ${f(-0.28 * Hh)} ${f(0.44 * L)} ${f(-0.24 * Hh)} Z`, fill: P.back }, g);
    K.el("path", { d: `M ${f(0.3 * L)} ${f(-0.14 * Hh)} C ${f(0.1 * L)} ${f(-0.2 * Hh)} ${f(-0.15 * L)} ${f(-0.16 * Hh)} ${f(-0.32 * L)} ${f(-0.08 * Hh)} C ${f(-0.1 * L)} ${f(-0.1 * Hh)} ${f(0.12 * L)} ${f(-0.1 * Hh)} ${f(0.3 * L)} ${f(-0.14 * Hh)} Z`, fill: P.hi, opacity: 0.85 }, g);
    K.el("path", { d: `M ${f(0.18 * L)} ${f(-0.3 * Hh)} Q ${f(0.12 * L)} ${f(0.0)} ${f(0.2 * L)} ${f(0.3 * Hh)}`, fill: "none", stroke: P.back, "stroke-width": f(L * 0.014), "stroke-linecap": "round", opacity: 0.6 }, g);
    const photos = [];
    for (let i = 0; i < 11; i++) {
      const u = i / 10, x = (0.3 - u * 0.6) * L, y = (u < 0.45 ? 0.32 + u * 0.3 : 0.455 - (u - 0.45) * 0.72) * Hh;
      photos.push(KO.glow(g, { x, y, r: L * 0.09, color: "cyan", p: o.p, core: L * 0.016, k: 0 }));
    }
    const eye = KO.eye(g, { x: 0.3 * L, y: -0.2 * Hh, r: Hh * 0.12, p: o.p, lid: P.back, lx: 0.2, ly: -0.75, ring: P.hi });
    // silhouette: the same outline in a dark colour on top; api.dark 0..1 sets how much of it shows (the view from below)
    const sil = K.el("path", { d: outline, fill: o.silColor || "#0a1a33", opacity: 0 }, g);
    photos.forEach((ph) => g.appendChild(ph.g));   // the lights stay on top of the silhouette
    const api = { g, L, eye, photos, k: 0, dark: 0, outline, shapes: [outline, tailD, dorsalD] };
    /* a flat silhouette of the whole fish (body and fins) in one colour; the stroke covers anti-aliased body edges */
    api.silhouette = (parent, fill, opacity = 0) => {
      const sg = K.g(parent, { opacity });
      api.shapes.forEach((d) => K.el("path", { d, fill, stroke: fill, "stroke-width": 5, "stroke-linejoin": "round" }, sg));
      return sg;
    };
    api.update = () => {
      sil.setAttribute("opacity", f(api.dark));
      photos.forEach((ph) => { ph.k = api.k; ph.update(); });
    };
    api.update();
    return api;
  };

  // ------------------------------------------------------------------ Atolla-style jellyfish (side view)
  KO.jelly = (parent, o = {}) => {
    const R0 = o.r ?? 170, P = KO.C.jelly, g = K.g(parent), n = 14;
    const halo = o.halo ? KO.glow(g, { x: 0, y: -R0 * 0.2, r: R0 * o.halo, color: "blue", p: o.p, core: 0, k: 0 }) : null;
    const tents = K.g(g, { fill: "none", stroke: P.tent, "stroke-linecap": "round" });
    const tl = [];
    for (let i = 0; i < 12; i++) tl.push(K.el("path", { "stroke-width": f(R0 * (i === 5 ? 0.05 : 0.025)), opacity: 0.85 }, tents));
    const bell = K.el("path", { fill: P.base }, g);
    const shade = K.el("path", { fill: P.shade }, g);
    const core = K.el("ellipse", { fill: P.core }, g);
    const hi = K.el("path", { fill: "none", stroke: P.hi, "stroke-width": f(R0 * 0.06), "stroke-linecap": "round", opacity: 0.8 }, g);
    const ring = [];
    for (let i = 0; i < n; i++) ring.push(KO.glow(g, { r: R0 * (o.glowR ?? 0.32), color: "blue", p: o.p, core: R0 * 0.035, k: 0 }));
    const eyeL = KO.eye(g, { x: -R0 * 0.22, y: -R0 * 0.28, r: R0 * 0.11, p: o.p, lid: P.shade, lx: 0, ly: 0.2 });
    const eyeR = KO.eye(g, { x: R0 * 0.22, y: -R0 * 0.28, r: R0 * 0.11, p: o.p, lid: P.shade, lx: 0, ly: 0.2 });
    const api = { g, r: R0, pulse: 0, phase: 0, flash: 0, spin: 0, eyes: [eyeL, eyeR] };
    api.update = () => {
      const s = 1 - api.pulse * 0.12, w = R0 * (1 + api.pulse * 0.06), h = R0 * 0.78 * s;
      let d = `M ${f(-w)} 0 C ${f(-w)} ${f(-h * 1.3)} ${f(w)} ${f(-h * 1.3)} ${f(w)} 0`;
      const lap = 10;
      for (let i = 0; i < lap; i++) {
        const x0 = w - (i * 2 * w) / lap, x1 = w - ((i + 1) * 2 * w) / lap;
        d += ` Q ${f((x0 + x1) / 2)} ${f(R0 * 0.16)} ${f(x1)} 0`;
      }
      bell.setAttribute("d", d + " Z");
      shade.setAttribute("d", `M ${f(-w * 0.98)} ${f(-h * 0.1)} C ${f(-w * 0.9)} ${f(-h * 0.55)} ${f(w * 0.9)} ${f(-h * 0.55)} ${f(w * 0.98)} ${f(-h * 0.1)} L ${f(w)} 0 L ${f(-w)} 0 Z`);
      core.setAttribute("cx", 0); core.setAttribute("cy", f(-h * 0.42)); core.setAttribute("rx", f(w * 0.42)); core.setAttribute("ry", f(h * 0.3));
      hi.setAttribute("d", `M ${f(-w * 0.62)} ${f(-h * 0.72)} Q ${f(-w * 0.3)} ${f(-h * 1.0)} ${f(w * 0.1)} ${f(-h * 0.98)}`);
      tl.forEach((p, i) => {
        const x0 = -w * 0.85 + (i * 1.7 * w) / 11, len = R0 * (i === 5 ? 3.6 : 1.3 + ((i * 37) % 7) * 0.12), pts = [];
        for (let k = 0; k <= 8; k++) {
          const u = k / 8;
          pts.push([x0 + Math.sin(api.phase + u * 4 + i) * R0 * 0.12 * u, R0 * 0.08 + u * len]);
        }
        p.setAttribute("d", K.smooth(pts, false));
      });
      ring.forEach((gl, i) => {
        const a = (i / n) * Math.PI * 2, x = Math.cos(a) * w * 0.86, y = Math.sin(a) * R0 * 0.16 - R0 * 0.02;
        gl.g.setAttribute("transform", `translate(${f(x)},${f(y)})`);
        const chase = Math.pow(Math.max(0, Math.cos(a - api.spin)), 6);
        gl.k = api.flash * (0.25 + 0.95 * chase);
        gl.update();
      });
      if (halo) { halo.k = api.flash * (0.55 + 0.25 * Math.sin(api.spin * 2)); halo.update(); }
    };
    api.update();
    return api;
  };

  // ------------------------------------------------------------------ shrimp
  KO.shrimp = (parent, o = {}) => {
    const s = o.s ?? 1, P = KO.C.shrimp, outer = K.g(parent), g = K.g(outer, { transform: `scale(${f(s)})` });
    const legs = K.g(g, { stroke: P.leg, "stroke-width": 4, "stroke-linecap": "round", fill: "none" });
    const lg = [];
    for (let i = 0; i < 5; i++) lg.push(K.el("path", {}, legs));
    const ant = K.g(g, { stroke: P.hi, "stroke-width": 3, "stroke-linecap": "round", fill: "none" });
    const a1 = K.el("path", {}, ant), a2 = K.el("path", {}, ant);
    K.el("path", { d: "M -70 -6 L -104 -30 Q -96 -6 -108 14 Z", fill: P.shade }, g);
    const segs = [[-58, -4, 16], [-38, -12, 20], [-14, -16, 24], [12, -16, 26], [38, -12, 26]];
    segs.forEach(([x, y, r], i) => K.el("ellipse", { cx: x, cy: y, rx: r * 0.95, ry: r * 0.8, fill: i % 2 ? P.base : P.hi }, g));
    K.el("path", { d: "M 26 -36 Q 74 -36 84 -12 Q 70 8 30 6 Z", fill: P.base }, g);
    K.el("path", { d: "M 84 -14 L 112 -22 L 86 -6 Z", fill: P.hi }, g);
    const eye = KO.eye(g, { x: 66, y: -30, r: 9, p: o.p, lid: P.shade, lx: 0.5 });
    const api = { g: outer, eye, phase: 0 };
    api.update = () => {
      lg.forEach((p, i) => {
        const x = -30 + i * 16, sw = Math.sin(api.phase * 2 + i * 0.9) * 6;
        p.setAttribute("d", `M ${x} 4 q ${f(sw)} 12 ${f(sw * 0.6 - 4)} 24`);
      });
      const w = Math.sin(api.phase) * 8;
      a1.setAttribute("d", `M 84 -26 Q 130 ${f(-70 + w)} 190 ${f(-40 + w)}`);
      a2.setAttribute("d", `M 84 -22 Q 140 ${f(-50 - w)} 200 ${f(-6 - w)}`);
    };
    api.update();
    return api;
  };

  // ------------------------------------------------------------------ dragonfish (stoplight loosejaw)
  KO.dragon = (parent, o = {}) => {
    const s = o.s ?? 1, P = KO.C.dragon, outer = K.g(parent), g = K.g(outer, { transform: `scale(${f(s)})` });
    const p = o.p;
    const bg = K.el("linearGradient", { id: `${p}-beam`, x1: 0, y1: 0, x2: 1, y2: 0 }, o.defs);
    K.el("stop", { offset: 0, "stop-color": "#ff3b30", "stop-opacity": 0.75 }, bg);
    K.el("stop", { offset: 1, "stop-color": "#ff3b30", "stop-opacity": 0 }, bg);
    const beam = K.el("path", { d: "M 120 30 L 760 -170 L 760 230 Z", fill: `url(#${p}-beam)`, opacity: 0 }, g);
    const tail = K.g(g);
    K.el("path", { d: "M -440 4 L -520 -44 L -500 6 L -520 50 Z", fill: P.sheen }, tail);
    const body = K.el("path", { fill: P.base, stroke: P.rim, "stroke-width": 3 }, g);
    K.el("path", { d: "M -300 30 L -340 72 L -270 36 Z M -360 -18 L -400 -52 L -340 -14 Z", fill: P.sheen }, g);
    const sheen = K.el("path", { fill: "none", stroke: P.sheen, "stroke-width": 6, "stroke-linecap": "round" }, g);
    const jaw = K.g(g);
    K.el("path", { d: "M 40 26 L 196 64 L 190 78 L 30 46 Z", fill: P.base, stroke: P.rim, "stroke-width": 3 }, jaw);
    for (let i = 0; i < 5; i++) K.el("path", { d: `M ${70 + i * 26} ${36 + i * 6} l 6 -18 l 6 18 Z`, fill: P.teeth }, jaw);
    for (let i = 0; i < 4; i++) K.el("path", { d: `M ${80 + i * 28} 18 l 6 16 l 6 -16 Z`, fill: P.teeth }, g);
    const red = KO.glow(g, { x: 104, y: 22, r: 70, color: "red", p, core: 7, k: 0 });
    const blue = KO.glow(g, { x: 66, y: -6, r: 34, color: "blue", p, core: 4, k: 0.8 });
    const eye = KO.eye(g, { x: 112, y: -6, r: 12, p, lid: P.base, lx: 0.6, iris: "#3a0d10" });
    const api = { g: outer, beam: 0, jaw: 0.35, phase: 0, eye, red, blue };
    api.update = () => {
      const w = Math.sin(api.phase) * 14;
      body.setAttribute("d", `M 158 -6 C 150 -52 60 -62 -10 ${f(-50 + w * 0.15)} C -160 ${f(-34 + w * 0.5)} -340 ${f(-14 + w)} -450 ${f(2 + w)} C -340 ${f(22 + w)} -160 ${f(44 + w * 0.5)} -10 ${f(50 + w * 0.15)} C 60 54 132 40 158 -6 Z`);
      sheen.setAttribute("d", `M 70 -40 C -40 -40 -180 ${f(-26 + w * 0.5)} -360 ${f(-8 + w)}`);
      tail.setAttribute("transform", `translate(0,${f(w)}) rotate(${f(Math.sin(api.phase + 0.6) * 8)} -450 4)`);
      jaw.setAttribute("transform", `rotate(${f(api.jaw * 22)} 40 30)`);
      beam.setAttribute("opacity", f(api.beam));
      red.k = 0.3 + api.beam * 0.9; red.update();
    };
    api.update();
    return api;
  };

  // ------------------------------------------------------------------ chemistry characters
  KO.fuel = (parent, o = {}) => {
    const r = o.r ?? 70, P = KO.C.fuel, g = K.g(parent);
    const hex = (rr) => K.poly(Array.from({ length: 6 }, (_, i) => [Math.cos(i * Math.PI / 3 + Math.PI / 6) * rr, Math.sin(i * Math.PI / 3 + Math.PI / 6) * rr]));
    K.el("polygon", { points: hex(r), fill: P.shade, stroke: P.shade, "stroke-width": r * 0.3, "stroke-linejoin": "round" }, g);
    K.el("polygon", { points: hex(r * 0.92), fill: P.base, stroke: P.base, "stroke-width": r * 0.22, "stroke-linejoin": "round", transform: `translate(${f(-r * 0.05)},${f(-r * 0.08)})` }, g);
    K.el("path", { d: `M ${f(-r * 0.55)} ${f(-r * 0.5)} Q ${f(-r * 0.2)} ${f(-r * 0.8)} ${f(r * 0.25)} ${f(-r * 0.7)}`, fill: "none", stroke: P.hi, "stroke-width": r * 0.12, "stroke-linecap": "round" }, g);
    const eyes = KP.eyes(g, { r: r * 0.2, gap: r * 0.56, prefix: o.p, lid: P.shade, x: 0, y: r * 0.02 });
    return { g, eyes };
  };
  KO.enzyme = (parent, o = {}) => {
    const r = o.r ?? 120, P = KO.C.enzyme, g = K.g(parent);
    const mouth = (rr, open) => {
      const a = open * 0.6;
      return `M 0 0 L ${f(Math.cos(a) * rr)} ${f(-Math.sin(a) * rr)} A ${f(rr)} ${f(rr)} 0 1 0 ${f(Math.cos(a) * rr)} ${f(Math.sin(a) * rr)} Z`;
    };
    const b = K.el("path", { fill: P.shade }, g), b2 = K.el("path", { fill: P.base, transform: `translate(${f(-r * 0.04)},${f(-r * 0.06)})` }, g);
    K.el("path", { d: `M ${f(-r * 0.65)} ${f(-r * 0.42)} Q ${f(-r * 0.3)} ${f(-r * 0.86)} ${f(r * 0.15)} ${f(-r * 0.8)}`, fill: "none", stroke: P.hi, "stroke-width": r * 0.09, "stroke-linecap": "round" }, g);
    const eyes = KP.eyes(g, { r: r * 0.14, gap: r * 0.4, prefix: o.p, lid: P.shade, x: -r * 0.25, y: -r * 0.36 });
    const api = { g, eyes, open: 1 };
    api.update = () => { b.setAttribute("d", mouth(r, api.open)); b2.setAttribute("d", mouth(r * 0.9, api.open)); };
    api.update();
    return api;
  };

  // ------------------------------------------------------------------ sunbeams
  KO.rays = (parent, o = {}) => {
    const g = K.g(parent), R = K.rng(o.seed || 7);
    const lg = K.el("linearGradient", { id: `${o.p}-ray`, x1: 0, y1: 0, x2: 0, y2: 1 }, o.defs);
    K.el("stop", { offset: 0, "stop-color": "#e8fdff", "stop-opacity": 0.55 }, lg);
    K.el("stop", { offset: 1, "stop-color": "#e8fdff", "stop-opacity": 0 }, lg);
    for (let i = 0; i < (o.n || 7); i++) {
      const x = (o.x0 ?? -100) + R() * ((o.x1 ?? 1180) - (o.x0 ?? -100)), w = 40 + R() * 90, len = (o.len ?? 1500) * (0.6 + R() * 0.5), sk = (R() - 0.5) * 300;
      K.el("path", { d: `M ${f(x)} ${f(o.y ?? 0)} L ${f(x + w)} ${f(o.y ?? 0)} L ${f(x + w * 2.2 + sk)} ${f((o.y ?? 0) + len)} L ${f(x - w * 0.6 + sk)} ${f((o.y ?? 0) + len)} Z`, fill: `url(#${o.p}-ray)`, opacity: f(0.35 + R() * 0.4) }, g);
    }
    return g;
  };

  // ------------------------------------------------------------------ depth gauge (HTML)
  /* depth (m) -> 0..1 along the gauge: the top 200 m get 40 %, 200-1000 m the next 45 %, then 1000-4000 m */
  KO.depthU = (d) => (d <= 200 ? (d / 200) * 0.4 : d <= 1000 ? 0.4 + ((d - 200) / 800) * 0.45 : 0.85 + Math.min(1, (d - 1000) / 3000) * 0.15);
  KO.depthMeter = (ui, o = {}) => {
    const x = o.x ?? 74, y0 = o.y0 ?? 330, y1 = o.y1 ?? 1400, el = document.createElement("div");
    el.style.cssText = `position:absolute;left:${x}px;top:${y0}px;width:14px;height:${y1 - y0}px;border-radius:7px;background:linear-gradient(#bff6ff,#3a8fd0 40%,#1b3f7a 85%,#0b1a3a);box-shadow:0 0 0 3px rgba(2,10,28,0.5);opacity:0;`;
    ui.appendChild(el);
    const marks = [];
    for (const [d, label] of o.marks || [[0, "0 m"], [200, "200 m"], [1000, "1,000 m"]]) {
      const m = document.createElement("div");
      m.style.cssText = `position:absolute;left:${x + 26}px;top:${f(y0 + KO.depthU(d) * (y1 - y0) - 19)}px;font:900 34px Nunito,sans-serif;color:#dff2ff;text-shadow:0 3px 0 rgba(2,10,28,0.8);opacity:0;white-space:nowrap;`;
      m.textContent = label;
      ui.appendChild(m);
      marks.push(m);
    }
    const chip = document.createElement("div");
    chip.style.cssText = `position:absolute;left:${x - 11}px;top:${y0}px;transform:translate(0,-50%);display:flex;align-items:center;gap:12px;opacity:0;`;
    chip.innerHTML = `<div style="width:36px;height:36px;border-radius:18px;background:#ffffff;box-shadow:0 0 0 8px rgba(255,255,255,0.25)"></div><div class="v" style="font:900 46px Nunito,sans-serif;color:#ffffff;background:#0e6e78;border-radius:16px;padding:4px 18px;box-shadow:0 6px 0 #073f45;"></div>`;
    ui.appendChild(chip);
    const markY = (o.marks || [[0], [200], [1000]]).map(([d]) => y0 + KO.depthU(d) * (y1 - y0));
    const api = { el, chip, marks, d: 0 };
    api.update = () => {
      const cy = y0 + KO.depthU(api.d) * (y1 - y0);
      chip.style.top = f(cy) + "px";
      chip.querySelector(".v").textContent = `${Math.round(api.d).toLocaleString("en-US")} m`;
      // a mark label hides while the depth chip passes over it, so the two never overlap
      marks.forEach((m, i) => { m.style.visibility = Math.abs(cy - markY[i]) < 52 ? "hidden" : "visible"; });
    };
    api.update();
    return api;
  };
})();
