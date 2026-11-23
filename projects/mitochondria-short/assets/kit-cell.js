/* kit-cell.js: cell-biology cast for the mitochondria film. Load after kit.js, kit-plus.js (and kit-ocean.js for glows).
   Seek-safe: shapes are built once and driven by numbers; nothing reads the clock.

   KC.C                          palette (orange = mitochondria and their ancestor, the film's one warm accent)
   KC.mito(parent, o)            mitochondrion character: double wall, folded inner membrane, DNA ring, eyes
   KC.guest(parent, o)           the ancestral bacterium (orange, KP.bact with eyes)
   KC.host(parent, o)            the ancient host cell: a wobbling blob that can make a pocket and swallow something
   KC.atp(parent, o)             an ATP token (energy coin with a bolt)
   KC.sugar / KC.o2              food and oxygen molecules
   KC.egg(parent, o), KC.sperm   for "you got them from your mother"
   KC.thighSection / KC.fascicle / KC.fiber   the three tissue levels of the dive (draw around 0,0)
   KC.cytoplasm(parent, o)       out-of-focus cell interior (membrane folds, drifting molecules) for dark backgrounds
   KC.balance(parent, o)         a balance scale
*/
(function () {
  const K = window.KIT, KP = window.KITPLUS;
  const KC = (window.CELL = {});
  const f = K.f;

  KC.C = {
    mito: { wall: "#c95f00", inner: "#ff9a2e", matrix: "#ffb24d", crista: "#e07012", cristaHi: "#ffd08a", dna: "#fff1d6", hi: "#ffd9a0" },
    guest: { wall: "#b85600", shade: "#d9700f", body: "#ff9a2e", hi: "#ffc061", dot: "#a24f00", flag: "#d0741a", rim: "#ffd08a" },
    host: { mem: "#b7a6df", base: "#8f7bc0", shade: "#7462a6", hi: "#cfc2ef", nuc: "#6a589c" },
    atp: { base: "#ffd23f", rim: "#e0a400", bolt: "#ffffff", glow: "warm" },
    tissue: {
      skin1: "#f0c2aa", skin2: "#dca08a", fat: "#f3d58f", fatShade: "#e2bd6c", fascia: "#e9d6c8",
      muscle: "#b8344a", muscleHi: "#d0566a", gap: "#7d1f33", bone: "#f4efe6", boneShade: "#ddd3c3", marrow: "#e9b97a",
      fiber: "#c23c50", fiberHi: "#d9606f", endo: "#6e1a2c", nucleus: "#7b4aa0", inside: "#5a1830", myo: "#b2475d", myoDark: "#8c2f45", myoHi: "#c8627a",
    },
    egg: { zona: "#f3e6c8", cyto: "#f7d9b8", cytoShade: "#ecc69d", nuc: "#e3a890" },
    sperm: { head: "#d8deec", headShade: "#b8c0d4", tail: "#c9d1e2" },
  };

  // ------------------------------------------------------------------ mitochondrion
  /* o: L (length), r (radius), seed, eyes (bool), dna (bool), prefix
     api: gap (0..1, the two walls pull apart), waist (0..1, pinches for division), phase (wobble), update() */
  KC.mito = (parent, o = {}) => {
    const L = o.L ?? 220, r = o.r ?? 62, P = KC.C.mito, R = K.rng(o.seed ?? 3), g = K.g(parent);
    const outer = K.el("path", { fill: P.wall }, g);
    const gapBand = K.el("path", { fill: "#ffe2b8", opacity: 0 }, g);       // the space between the walls, when they part
    const inner = K.el("path", { fill: P.inner }, g);
    const matrix = K.el("path", { fill: P.matrix }, g);
    const cristae = K.g(g);
    const folds = [];
    const nF = Math.max(3, Math.round((L - 2 * r) / (r * 0.55)) + 2);
    for (let i = 0; i < nF; i++) folds.push({ x: -L / 2 + r * 0.7 + (i + 0.5) * ((L - 1.4 * r) / nF), up: i % 2 === 0, len: 0.55 + R() * 0.25, ph: R() * 6 });
    const foldEls = folds.map(() => [K.el("path", { fill: "none", stroke: P.crista, "stroke-linecap": "round", "stroke-width": f(r * 0.2) }, cristae), K.el("path", { fill: "none", stroke: P.cristaHi, "stroke-linecap": "round", "stroke-width": f(r * 0.07) }, cristae)]);
    const hi = K.el("path", { fill: "none", stroke: P.hi, "stroke-width": f(r * 0.1), "stroke-linecap": "round", opacity: 0.85 }, g);
    const dna = o.dna === false ? null : K.el("circle", { r: f(r * 0.2), fill: "none", stroke: P.dna, "stroke-width": f(r * 0.07), opacity: 0.95 }, g);
    const eyes = o.eyes === false ? null : KP.eyes(g, { r: r * 0.24, gap: r * 0.62, prefix: o.prefix, lid: P.crista, x: L * 0.08, y: -r * 0.06 });
    const api = { g, L, r, gap: 0, waist: 0, phase: R() * 6, eyes, dna, wobble: 1 };
    api.update = () => {
      const gp = api.gap * r * 0.32, w = api.waist;
      outer.setAttribute("d", K.capsule(L + gp * 2, r + gp, w));
      gapBand.setAttribute("d", K.capsule(L + gp * 2 - r * 0.16, r + gp - r * 0.08, w));
      gapBand.setAttribute("opacity", f(Math.min(1, api.gap * 1.4)));
      inner.setAttribute("d", K.capsule(L - r * 0.2, r * 0.88, w));
      matrix.setAttribute("d", K.capsule(L - r * 0.42, r * 0.7, w));
      folds.forEach((F, i) => {
        const s = F.up ? -1 : 1, y0 = s * r * 0.86, y1 = s * r * (0.86 - 1.2 * F.len), wv = Math.sin(api.phase + F.ph) * r * 0.06 * api.wobble;
        const pinch = Math.max(0, 1 - Math.abs(F.x) / (L * 0.12)) * w;          // folds near the waist shrink when it pinches
        const yy1 = y0 + (y1 - y0) * (1 - pinch);
        const d = `M ${f(F.x)} ${f(y0)} Q ${f(F.x + wv)} ${f((y0 + yy1) / 2)} ${f(F.x - wv * 0.5)} ${f(yy1)}`;
        foldEls[i][0].setAttribute("d", d);
        foldEls[i][1].setAttribute("d", d);
      });
      hi.setAttribute("d", `M ${f(-L * 0.3)} ${f(-r * 0.62)} Q ${f(0)} ${f(-r * 0.78)} ${f(L * 0.24)} ${f(-r * 0.64)}`);
      if (dna) { dna.setAttribute("cx", f(-L * 0.22)); dna.setAttribute("cy", f(r * 0.28)); }
    };
    api.update();
    return api;
  };

  // ------------------------------------------------------------------ the ancestral bacterium (orange, with eyes)
  KC.guest = (parent, o = {}) => KP.bact(parent, Object.assign({ L: 190, r: 46, pal: KC.C.guest, prefix: o.prefix, lidColor: "#c96a10" }, o));

  // ------------------------------------------------------------------ the host cell (a wobbling blob that can swallow)
  /* o: R (radius), seed, prefix. api.pocket = { a: angle (rad), depth: 0..1, width: 0..1 }, api.phase, update().
     The pocket pushes the membrane in around the angle `a`: depth 1 = 0.55 R deep. */
  KC.host = (parent, o = {}) => {
    const R0 = o.R ?? 300, P = KC.C.host, g = K.g(parent), Rn = K.rng(o.seed ?? 5), n = 56;
    const offs = Array.from({ length: 6 }, () => [Rn() * 6.28, 1 + Math.floor(Rn() * 4)]);
    const mem = K.el("path", { fill: P.mem }, g), base = K.el("path", { fill: P.base }, g), shade = K.el("path", { fill: P.shade, opacity: 0.6 }, g);
    const insides = K.g(g);
    for (let i = 0; i < 9; i++) {
      const a = Rn() * 6.28, d = R0 * (0.15 + Rn() * 0.5);
      K.el("circle", { cx: f(Math.cos(a) * d), cy: f(Math.sin(a) * d), r: f(R0 * (0.03 + Rn() * 0.04)), fill: P.hi, opacity: 0.55 }, insides);
    }
    const hi = K.el("path", { fill: "none", stroke: P.hi, "stroke-width": f(R0 * 0.05), "stroke-linecap": "round", opacity: 0.8 }, g);
    const eyes = KP.eyes(g, { r: R0 * 0.1, gap: R0 * 0.26, prefix: o.prefix, lid: P.shade, x: R0 * 0.08, y: -R0 * 0.28 });
    const api = { g, R: R0, phase: 0, pocket: { a: 0, depth: 0, width: 0.5 }, eyes, insides };
    const shape = (scale, extra = 0) => {
      const pts = [];
      for (let i = 0; i < n; i++) {
        const a = (i / n) * Math.PI * 2;
        let rr = R0 * scale * (1 + 0.035 * offs.reduce((s, [ph, k]) => s + Math.sin(a * k + ph + api.phase * (0.5 + k * 0.2)), 0) / offs.length * 2.2);
        const dA = Math.atan2(Math.sin(a - api.pocket.a), Math.cos(a - api.pocket.a)), w = Math.max(0.05, api.pocket.width);
        if (Math.abs(dA) < w) rr -= R0 * 0.55 * api.pocket.depth * Math.cos((dA / w) * Math.PI / 2) ** 2;
        pts.push([Math.cos(a) * (rr + extra), Math.sin(a) * (rr + extra)]);
      }
      return K.smooth(pts, true);
    };
    api.update = () => {
      mem.setAttribute("d", shape(1, R0 * 0.04));
      base.setAttribute("d", shape(1));
      shade.setAttribute("d", shape(0.82));
      shade.setAttribute("transform", `translate(${f(R0 * 0.06)},${f(R0 * 0.08)})`);
      hi.setAttribute("d", `M ${f(-R0 * 0.62)} ${f(-R0 * 0.42)} Q ${f(-R0 * 0.35)} ${f(-R0 * 0.78)} ${f(R0 * 0.05)} ${f(-R0 * 0.82)}`);
    };
    api.update();
    return api;
  };

  // ------------------------------------------------------------------ molecules
  KC.atp = (parent, o = {}) => {
    const s = o.s ?? 1, P = KC.C.atp, g = K.g(parent), inner = K.g(g, { transform: `scale(${f(s)})` });
    const hex = (rr) => K.poly(Array.from({ length: 6 }, (_, i) => [Math.cos(i * Math.PI / 3) * rr, Math.sin(i * Math.PI / 3) * rr]));
    if (o.glow !== false && window.OCEAN) window.OCEAN.glow(inner, { r: 70, color: P.glow, p: o.prefix, core: 0, k: 0.55 });
    K.el("polygon", { points: hex(30), fill: P.rim, stroke: P.rim, "stroke-width": 8, "stroke-linejoin": "round" }, inner);
    K.el("polygon", { points: hex(25), fill: P.base, stroke: P.base, "stroke-width": 6, "stroke-linejoin": "round", transform: "translate(-1,-2)" }, inner);
    K.el("path", { d: "M 4 -17 L -8 2 L 0 2 L -4 17 L 9 -3 L 1 -3 Z", fill: P.bolt }, inner);
    return { g };
  };
  KC.sugar = (parent, o = {}) => {
    const g = K.g(parent, { transform: `scale(${f(o.s ?? 1)})` });
    const hex = K.poly(Array.from({ length: 6 }, (_, i) => [Math.cos(i * Math.PI / 3 + Math.PI / 6) * 22, Math.sin(i * Math.PI / 3 + Math.PI / 6) * 22]));
    K.el("polygon", { points: hex, fill: "#fbe3ec", stroke: "#e7a9c0", "stroke-width": 7, "stroke-linejoin": "round" }, g);
    K.el("circle", { cx: 26, cy: -14, r: 7, fill: "#e7a9c0" }, g);
    return { g };
  };
  KC.o2 = (parent, o = {}) => {
    const g = K.g(parent, { transform: `scale(${f(o.s ?? 1)})` });
    K.el("circle", { cx: -12, cy: 0, r: 17, fill: "#9fd8ff" }, g);
    K.el("circle", { cx: 12, cy: 0, r: 17, fill: "#7cc4f4" }, g);
    K.el("circle", { cx: -16, cy: -6, r: 5, fill: "#e6f6ff" }, g);
    return { g };
  };

  // ------------------------------------------------------------------ egg and sperm
  KC.egg = (parent, o = {}) => {
    const R0 = o.R ?? 300, P = KC.C.egg, g = K.g(parent), Rn = K.rng(o.seed ?? 9);
    K.el("circle", { r: f(R0 * 1.1), fill: P.zona, opacity: 0.55 }, g);
    K.el("circle", { r: f(R0), fill: P.cyto }, g);
    K.el("circle", { cx: f(R0 * 0.08), cy: f(R0 * 0.1), r: f(R0 * 0.86), fill: P.cytoShade, opacity: 0.5 }, g);
    K.el("circle", { cx: f(-R0 * 0.18), cy: f(-R0 * 0.12), r: f(R0 * 0.24), fill: P.nuc }, g);
    const minis = K.g(g), list = [];
    for (let i = 0; i < (o.n ?? 46); i++) {
      let x, y, ok = false, tries = 0;
      while (!ok && tries++ < 40) {
        const a = Rn() * 6.28, d = R0 * (0.18 + Rn() * 0.72);
        x = Math.cos(a) * d; y = Math.sin(a) * d;
        ok = Math.hypot(x + R0 * 0.18, y + R0 * 0.12) > R0 * 0.32 && list.every((p) => Math.hypot(p.x - x, p.y - y) > R0 * 0.1);
      }
      if (!ok) continue;
      const mg = K.g(minis, { transform: `translate(${f(x)},${f(y)}) rotate(${f(Rn() * 180)})` });
      const m = KC.mito(mg, { L: R0 * 0.16, r: R0 * 0.045, eyes: false, dna: false, seed: 100 + i });
      list.push({ x, y, m, g: mg });
    }
    return { g, R: R0, minis: list };
  };
  KC.sperm = (parent, o = {}) => {
    const s = o.s ?? 1, P = KC.C.sperm, g = K.g(parent), inner = K.g(g, { transform: `scale(${f(s)})` });
    const tail = K.el("path", { fill: "none", stroke: P.tail, "stroke-width": 7, "stroke-linecap": "round" }, inner);
    const mid = K.g(inner), minis = [];
    for (let i = 0; i < 4; i++) {
      const mg = K.g(mid, { transform: `translate(${f(-46 - i * 15)},${f((i % 2 ? 1 : -1) * 4)}) rotate(${i % 2 ? 20 : -20})` });
      minis.push({ g: mg, m: KC.mito(mg, { L: 20, r: 6.5, eyes: false, dna: false, seed: 300 + i }) });
    }
    K.el("ellipse", { cx: 0, cy: 0, rx: 34, ry: 24, fill: P.head }, inner);
    K.el("ellipse", { cx: 6, cy: 5, rx: 26, ry: 16, fill: P.headShade, opacity: 0.6 }, inner);
    const eyes = KP.eyes(inner, { r: 6.5, gap: 15, prefix: o.prefix, lid: P.headShade, x: 6, y: -4 });
    const api = { g, phase: 0, minis, eyes };
    api.update = () => {
      const pts = [];
      for (let i = 0; i <= 16; i++) { const u = i / 16; pts.push([-100 - u * 210, Math.sin(api.phase - u * 9) * 22 * u]); }
      tail.setAttribute("d", K.smooth(pts, false));
    };
    api.update();
    return api;
  };

  // ------------------------------------------------------------------ tissue levels for the dive (each drawn around 0,0)
  /* the thigh in cross-section: skin, fat, muscle bundles, the femur. Returns { g, bundles: [[x, y, r]...] } */
  KC.thighSection = (parent, R0 = 1120, seed = 21) => {
    const T = KC.C.tissue, g = K.g(parent), Rn = K.rng(seed);
    K.el("circle", { r: R0 * 1.4, fill: T.gap }, g);                                  // beyond the cut edge
    K.el("circle", { r: R0, fill: T.skin2 }, g);
    K.el("circle", { r: R0 * 0.975, fill: T.skin1 }, g);
    K.el("circle", { r: R0 * 0.94, fill: T.fat }, g);
    for (let i = 0; i < 70; i++) {                                                   // fat cells as little bubbles
      const a = Rn() * 6.28, d = R0 * (0.86 + Rn() * 0.07);
      K.el("circle", { cx: f(Math.cos(a) * d), cy: f(Math.sin(a) * d), r: f(R0 * (0.018 + Rn() * 0.012)), fill: T.fatShade, opacity: 0.7 }, g);
    }
    K.el("circle", { r: R0 * 0.83, fill: T.fascia }, g);
    K.el("circle", { r: R0 * 0.815, fill: T.gap }, g);
    const bundles = [];
    for (let ring = 0; ring < 4; ring++) {
      const count = [1, 7, 12, 16][ring], dist = [0, 0.33, 0.55, 0.72][ring] * R0, rad = [0.12, 0.14, 0.12, 0.095][ring] * R0;
      for (let k = 0; k < count; k++) {
        if (ring === 0) continue;                                                     // the femur sits in the middle
        const a = (k / count) * Math.PI * 2 + ring * 0.4 + (Rn() - 0.5) * 0.12, d = dist + (Rn() - 0.5) * R0 * 0.03;
        const x = Math.cos(a) * d, y = Math.sin(a) * d, rr = rad * (0.9 + Rn() * 0.2);
        K.el("path", { d: K.blob(rr, 0.08, Rn() * 6, 9, 30 + bundles.length), fill: T.muscle, transform: `translate(${f(x)},${f(y)})` }, g);
        K.el("path", { d: K.blob(rr * 0.82, 0.08, Rn() * 6, 9, 60 + bundles.length), fill: T.muscleHi, opacity: 0.35, transform: `translate(${f(x - rr * 0.08)},${f(y - rr * 0.1)})` }, g);
        bundles.push([x, y, rr]);
      }
    }
    K.el("circle", { r: R0 * 0.15, fill: T.boneShade }, g);
    K.el("circle", { r: R0 * 0.135, fill: T.bone }, g);
    K.el("circle", { r: R0 * 0.075, fill: T.marrow }, g);
    return { g, bundles };
  };
  /* a muscle bundle in cross-section: many fibres (muscle cells) with nuclei at their edges. Returns { g, fibers } */
  KC.fascicle = (parent, R0 = 1120, seed = 31) => {
    const T = KC.C.tissue, g = K.g(parent), Rn = K.rng(seed), fibers = [];
    K.el("circle", { r: R0 * 1.4, fill: T.endo }, g);
    const step = R0 * 0.2;
    for (let row = -7; row <= 7; row++) {
      for (let col = -7; col <= 7; col++) {
        const x = col * step + (row % 2 ? step / 2 : 0) + (Rn() - 0.5) * step * 0.12, y = row * step * 0.87 + (Rn() - 0.5) * step * 0.12;
        if (Math.hypot(x, y) > R0 * 1.25) continue;
        const rr = step * (0.44 + Rn() * 0.05);
        K.el("path", { d: K.blob(rr, 0.06, Rn() * 6, 7, 200 + fibers.length), fill: T.fiber, transform: `translate(${f(x)},${f(y)})` }, g);
        K.el("path", { d: K.blob(rr * 0.78, 0.07, Rn() * 6, 7, 400 + fibers.length), fill: T.fiberHi, opacity: 0.35, transform: `translate(${f(x - rr * 0.08)},${f(y - rr * 0.1)})` }, g);
        for (let d = 0; d < 14; d++) {                                                 // myofibrils seen end-on
          const a = Rn() * 6.28, dd = rr * Math.sqrt(Rn()) * 0.7;
          K.el("circle", { cx: f(x + Math.cos(a) * dd), cy: f(y + Math.sin(a) * dd), r: f(rr * 0.05), fill: T.endo, opacity: 0.35 }, g);
        }
        const na = Rn() * 6.28;
        K.el("ellipse", { cx: f(x + Math.cos(na) * rr * 0.82), cy: f(y + Math.sin(na) * rr * 0.82), rx: f(rr * 0.16), ry: f(rr * 0.1), fill: T.nucleus, transform: `rotate(${f((na * 180) / Math.PI + 90)} ${f(x + Math.cos(na) * rr * 0.82)} ${f(y + Math.sin(na) * rr * 0.82)})` }, g);
        fibers.push([x, y, rr]);
      }
    }
    return { g, fibers };
  };
  /* inside one muscle fibre: striped myofibrils and rows of mitochondria between them. Returns { g, mitos } */
  KC.fiber = (parent, R0 = 1120, o = {}) => {
    const T = KC.C.tissue, g = K.g(parent), Rn = K.rng(o.seed ?? 41), mitos = [];
    K.el("rect", { x: -R0 * 1.5, y: -R0 * 1.5, width: R0 * 3, height: R0 * 3, fill: T.inside }, g);
    const cols = o.cols ?? 5, gapW = R0 * 2.2 / cols;
    for (let c = 0; c < cols; c++) {
      const x = -R0 * 1.1 + (c + 0.5) * gapW, w = gapW * 0.5;
      K.el("rect", { x: f(x - w / 2), y: -R0 * 1.5, width: f(w), height: R0 * 3, rx: f(w / 2), fill: T.myo }, g);
      for (let s = -9; s <= 9; s++) {                                                  // sarcomere stripes
        const y = s * R0 * 0.16;
        K.el("rect", { x: f(x - w / 2), y: f(y - R0 * 0.025), width: f(w), height: f(R0 * 0.05), fill: T.myoDark }, g);
        K.el("rect", { x: f(x - w / 2), y: f(y + R0 * 0.05), width: f(w), height: f(R0 * 0.012), fill: T.myoHi, opacity: 0.7 }, g);
      }
    }
    const mg = K.g(g);
    for (let c = 0; c <= cols; c++) {
      const x = -R0 * 1.1 + c * gapW;
      for (let s = -4; s <= 4; s++) {
        const y = s * R0 * 0.32 + (c % 2 ? R0 * 0.16 : 0) + (Rn() - 0.5) * R0 * 0.04;
        if (Math.hypot(x, y) > R0 * 1.35) continue;
        const rot = 90 + (Rn() - 0.5) * 14;
        const wrap = K.g(mg, { transform: `translate(${f(x)},${f(y)}) rotate(${f(rot)})` });
        const big = Math.hypot(x, y) < R0 * 0.75 && (s + c) % 3 === 0;
        const m = KC.mito(wrap, { L: R0 * 0.26, r: gapW * 0.15, seed: 500 + mitos.length, eyes: big, dna: big, prefix: o.prefix });
        if (big && m.eyes) { m.eyes.lx = -0.2; m.eyes.update(); }
        mitos.push({ x, y, m, wrap, big, rot });
      }
    }
    return { g, mitos };
  };

  // ------------------------------------------------------------------ out-of-focus cell interior for backgrounds
  /* KC.cytoplasm(parent, o): wavy membrane folds (like the endoplasmic reticulum), a few soft organelle shapes and
     many small drifting molecules, all in low-opacity tints of one colour. It covers more than the frame (camera
     moves) including the bottom band under the apps' UI, so a dark scene never reads as an empty field.
     o: tint, seed, folds (7), blobs (6), n (molecules, 90), W, H. api.update(t) drifts it (a pure function of t). */
  KC.cytoplasm = (parent, o = {}) => {
    const W = o.W ?? 1080, H = o.H ?? 1920, Rn = K.rng(o.seed ?? 11), tint = o.tint ?? "#ffffff";
    const g = K.g(parent, { "data-layout-allow-orbit": "" });          // the molecules tumble as they drift
    const X0 = -240, X1 = W + 240, Y0 = -300, Y1 = H + 300, nF = o.folds ?? 7;
    for (let i = 0; i < (o.blobs ?? 6); i++)
      K.el("path", { d: K.blob(90 + Rn() * 110, 0.14, Rn() * 6, 7, 900 + i), fill: tint, opacity: f(0.035 + Rn() * 0.035), transform: `translate(${f(X0 + Rn() * (X1 - X0))},${f(Y0 + Rn() * (Y1 - Y0))})` }, g);
    const folds = Array.from({ length: nF }, (_, i) => ({
      y0: Y0 + ((i + 0.5) / nF) * (Y1 - Y0) + (Rn() - 0.5) * 140, amp: 30 + Rn() * 45, k: 0.004 + Rn() * 0.004, ph: Rn() * 6, sp: 0.15 + Rn() * 0.25,
      band: K.el("path", { fill: "none", stroke: tint, "stroke-width": f(28 + Rn() * 18), "stroke-linecap": "round", opacity: f(0.045 + Rn() * 0.03) }, g),
      line: K.el("path", { fill: "none", stroke: tint, "stroke-width": f(4 + Rn() * 2), "stroke-linecap": "round", opacity: f(0.1 + Rn() * 0.06) }, g),
    }));
    const mols = Array.from({ length: o.n ?? 90 }, (_, i) => ({
      el: K.el("path", { d: K.blob(4 + Rn() * 9, 0.25, Rn() * 6, 5, 700 + i), fill: tint, opacity: f(0.12 + Rn() * 0.2) }, g),
      x: X0 + Rn() * (X1 - X0), y: Y0 + Rn() * (Y1 - Y0), vx: (Rn() - 0.5) * 16, vy: (Rn() - 0.5) * 16 - 5, rot: Rn() * 360, vr: (Rn() - 0.5) * 40,
    }));
    const wrap = (v, a, b) => a + ((((v - a) % (b - a)) + (b - a)) % (b - a));
    const api = { g };
    api.update = (t) => {
      folds.forEach((F) => {
        const pts = [];
        for (let x = X0; x <= X1; x += 80) pts.push([x, F.y0 + Math.sin(x * F.k + F.ph + t * F.sp) * F.amp]);
        const d = K.smooth(pts, false);
        F.band.setAttribute("d", d);
        F.line.setAttribute("d", d);
      });
      mols.forEach((m) => m.el.setAttribute("transform", `translate(${f(wrap(m.x + m.vx * t, X0, X1))},${f(wrap(m.y + m.vy * t, Y0, Y1))}) rotate(${f(m.rot + m.vr * t)})`));
    };
    api.update(0);
    return api;
  };

  // ------------------------------------------------------------------ balance scale
  /* Two dishes ride on stems at the beam ends and stay level as it tilts, so a standing figure on a dish never
     collides with hanger strings. Origin = the middle of the base.
     o: w (beam length), h (post height). api: tilt (degrees, + = right side down), left / right (groups whose origin
     is the dish surface: put the loads there), update() */
  KC.balance = (parent, o = {}) => {
    const g = K.g(parent), Wd = o.w ?? 640, Hh = o.h ?? 420, col = "#d8e2ee", shadeC = "#a9b6c8", dark = "#8796ab";
    K.el("path", { d: `M -44 0 L 44 0 L 20 ${-Hh} L -20 ${-Hh} Z`, fill: shadeC }, g);
    K.el("rect", { x: -130, y: -20, width: 260, height: 40, rx: 20, fill: col }, g);
    const beam = K.g(g);
    K.el("rect", { x: -Wd / 2, y: -13, width: Wd, height: 26, rx: 13, fill: col }, beam);
    const dish = () => {
      const pg = K.g(g);
      K.el("rect", { x: -11, y: -64, width: 22, height: 64, rx: 7, fill: shadeC }, pg);
      K.el("path", { d: "M -165 -84 L 165 -84 Q 140 -50 0 -50 Q -140 -50 -165 -84 Z", fill: shadeC }, pg);
      K.el("rect", { x: -175, y: -96, width: 350, height: 18, rx: 9, fill: col }, pg);
      const load = K.g(pg, { transform: "translate(0,-96)" });
      return { g: pg, load };
    };
    const L = dish(), Rr = dish();
    const pivot = K.el("circle", { r: 28, fill: dark }, g);
    const api = { g, tilt: 0, left: L.load, right: Rr.load };
    api.update = () => {
      const a = (api.tilt * Math.PI) / 180, arm = Wd / 2 - 30, dx = arm * Math.cos(a), dy = arm * Math.sin(a);
      beam.setAttribute("transform", `translate(0,${-Hh}) rotate(${f(api.tilt)})`);
      L.g.setAttribute("transform", `translate(${f(-dx)},${f(-Hh - dy)})`);
      Rr.g.setAttribute("transform", `translate(${f(dx)},${f(-Hh + dy)})`);
      pivot.setAttribute("cy", -Hh);
    };
    api.update();
    return api;
  };
})();
