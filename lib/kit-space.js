/* kit-space.js: space cast for the black hole film. Load after kit.js, kit-plus.js, kit-ocean.js (glows) and
   kit-human.js (the astronauts). Seek-safe: shapes are built once and driven by numbers; nothing reads the clock.

   KS.C                         palette (warm accretion-disk colours are the film's accent)
   KS.SUIT, KS.FRIEND, KS.LAB   looks for KH.human: a white spacesuit with orange trim, a mint one, a lab coat
   KS.floatPose(t, o)           a weightless pose for KH.human (arms out, knees bent), a pure function of t
   KS.stars(parent, o)          starfield; update(t) twinkles it
   KS.nebula(parent, o)         soft coloured clouds (radial gradients, no filters)
   KS.blackHole(parent, o)      flat-style black hole: glow, accretion disk (back and front halves, foreshortened),
                                lensed arcs, photon ring, shadow; update(t) swirls the disk. Layers: back, mid
                                (for things that fall in: drawn under the shadow), front
   KS.clock(parent, o)          a clock face; set(seconds) turns the hand
   KS.galaxy(parent, o)         a spiral galaxy seen face-on; update(t) turns it
   KS.sun(parent, o)            a small cartoon sun
   KS.ship(parent, o)           a small round spaceship
   KS.telescope(parent, o)      a hand telescope (a tube with a lens), drawn along +x
   KS.noodle(parent, o)         a spaghettified astronaut: a noodle on an inward spiral; update(u)
*/
(function () {
  const K = window.KIT, KP = window.KITPLUS, KO = window.OCEAN, KH = window.HUMAN;
  const f = K.f;
  const KS = (window.SPACE = {});
  let uid = 0;

  KS.C = {
    space: ["#2a1f66", "#140f3f", "#07051c"],
    star: "#fff6e2", starBlue: "#cfe0ff", starWarm: "#ffd9a6",
    disk: ["#fffbe9", "#ffe9a8", "#ffc766", "#ff9a45", "#f0643c", "#b8394f"],      // inner (hottest) to outer
    ring: "#fff4cf", shadow: "#030208", inside: "#0d0822",
    nebula: ["#7b4fd6", "#c4508e", "#3c6fe0", "#2fb3b8"],
  };
  const mix = (a, b, u) => {
    const pa = parseInt(a.slice(1), 16), pb = parseInt(b.slice(1), 16);
    const c = [16, 8, 0].map((s) => Math.round(((pa >> s) & 255) * (1 - u) + ((pb >> s) & 255) * u));
    return "#" + c.map((v) => v.toString(16).padStart(2, "0")).join("");
  };
  KS.mix = mix;

  // ------------------------------------------------------------------ looks for KH.human
  KS.SUIT = {
    skin: "#e0ac86", skinShade: "#c08a66", hair: "#3a2420", hairHi: "#5a3a30",
    shirt: "#f4f6fb", shirtShade: "#c9d1e4", shirtHi: "#ffffff",
    pants: "#e8ecf5", pantsShade: "#bfc8dc", pantsHi: "#ffffff",
    shoe: "#8d98b0", shoeShade: "#6d7790", sole: "#4a5268",
    suit: true, glove: "#ff8a3d", helmet: true, pack: "#b9c2d8", stripe: "#ff8a3d", far: 0.8,
  };
  KS.FRIEND = Object.assign({}, KS.SUIT, {
    skin: "#8d5b3f", skinShade: "#6f4430", hair: "#1e1414", hairHi: "#3a2a26",
    shirt: "#bdf2e0", shirtShade: "#86cdb8", shirtHi: "#e4fff6", pants: "#aee8d6", pantsShade: "#7fc4b0", pantsHi: "#dcfff3",
    glove: "#3f6fe0", stripe: "#3f6fe0", pack: "#86cdb8",
  });
  KS.LAB = {
    skin: "#f0c7a8", skinShade: "#d4a585", hair: "#9a9aa6", hairHi: "#c4c4ce",
    shirt: "#ffffff", shirtShade: "#d3dbe8", shirtHi: "#ffffff", pants: "#3a3550", pantsShade: "#2c2840", pantsHi: "#4a4566",
    suit: true, glove: "#f0c7a8", glasses: true,
  };

  /* A weightless pose: knees bent, arms held out, everything swaying slowly. o: amp (sway), phase, arms ("out" |
     "up" | "relax"). Edit the result with KH.armTo for gestures. */
  KS.floatPose = (t, o = {}) => {
    const P = KH.standPose(), D = KH.DIM, a = o.amp ?? 1, ph = o.phase ?? 0;
    const arms = o.arms || "out";
    if (arms === "up") {
      KH.armTo(P, 0, 150 + 10 * Math.sin(t * 7 + ph) * a, 20);
      KH.armTo(P, 1, -150 + 10 * Math.sin(t * 7 + ph + 2) * a, -20);
    } else if (arms === "relax") {
      KH.armTo(P, 0, 30 + 8 * Math.sin(t * 0.9 + ph) * a, 50);
      KH.armTo(P, 1, -20 + 8 * Math.sin(t * 0.8 + ph + 1) * a, 40);
    } else {
      KH.armTo(P, 0, 70 + 14 * Math.sin(t * 0.9 + ph) * a, 30 + 10 * Math.sin(t * 1.3 + ph) * a);
      KH.armTo(P, 1, -55 + 12 * Math.sin(t * 0.8 + ph + 1) * a, 25);
    }
    const hipY = P.pelvis[1];
    [[0, 9, 0.95], [1, -7, 0.91]].forEach(([i, swing, reach]) => {
      const s = (swing + 6 * Math.sin(t * 0.7 + ph + i * 1.7) * a) * (Math.PI / 180);
      const hip = P.legs[i].hip, L = (D.thigh + D.shin) * reach;
      const ankle = [hip[0] + Math.sin(s) * L, hipY - Math.cos(s) * L];
      const ik = KH.solveLeg(hip, ankle, D.thigh, D.shin);
      P.legs[i] = { hip, knee: ik.knee, ankle: ik.ankle, foot: -0.35 };
    });
    return P;
  };

  // ------------------------------------------------------------------ a space stage
  /* KS.stage(R, id, o): KO.scene with the space gradient, nebula clouds and two starfields at different depths
     (far stars move less than near ones when the camera moves), sized for big camera moves.
     Returns the KO.scene handles plus S.sky.update(t) to twinkle the stars. o: seed, bg, nebula (false = none). */
  KS.stage = (R, id, o = {}) => {
    const S = KO.scene(R, id, { bg: o.bg || KS.C.space, layers: o.layers || [0.25, 0.55, 1, 1.45], pool: o.pool });
    const sd = o.seed ?? 1, k = o.stars ?? 1;               // o.stars scales the star counts (1 = about 230 stars in view)
    // the area the far and mid layers can show during the films' camera moves (see docs/09-pitfalls.md: a starfield
    // spread over a much bigger area looks empty)
    const box = { x0: -700, x1: 1780, y0: -1100, y1: 3020 };
    if (o.nebula !== false) {
      KS.nebula(S.far, Object.assign({ seed: sd + 1, n: 7, a: o.nebulaA ?? 0.55 }, box));
      KS.wisps(S.far, Object.assign({ seed: sd + 4, n: 16, a: o.nebulaA ?? 0.55 }, box));
    }
    const s1 = KS.stars(S.far, Object.assign({ seed: sd + 2, n: Math.round(900 * k), a: 0.8, bigShare: 0.04 }, box));
    const s2 = KS.stars(S.mid, Object.assign({ seed: sd + 3, n: Math.round(240 * k), a: 1, bigShare: 0.16, rmin: 1.4, rmax: 3.4, halo: 0.12, p: S.p }, box));
    if (o.dust !== false) KS.dust(S.near, { seed: sd + 5, n: 12, p: S.p });
    S.sky = { update: (t) => { s1.update(t); s2.update(t); } };
    return S;
  };

  // ------------------------------------------------------------------ stars and clouds
  /* o: n, area (x0 x1 y0 y1), a (brightness), bigShare (share drawn as 4-point sparkles), rmin/rmax (dot radius),
        halo (share with a soft glow; needs o.p, a KO glow prefix), seed. update(t) twinkles about a quarter of them. */
  KS.stars = (parent, o = {}) => {
    const Rn = K.rng(o.seed ?? 5), g = K.g(parent), tw = [];
    const x0 = o.x0 ?? -300, x1 = o.x1 ?? 1380, y0 = o.y0 ?? -400, y1 = o.y1 ?? 2320;
    const cols = [KS.C.star, KS.C.star, KS.C.starBlue, KS.C.starWarm];
    const rmin = o.rmin ?? 0.8, rmax = o.rmax ?? 2.7;
    for (let i = 0; i < (o.n ?? 260); i++) {
      const x = x0 + Rn() * (x1 - x0), y = y0 + Rn() * (y1 - y0), big = Rn() < (o.bigShare ?? 0.07);
      const c = cols[Math.floor(Rn() * cols.length)], a = (o.a ?? 0.9) * (0.35 + Rn() * 0.65);
      if (o.halo && o.p && Rn() < o.halo && KP) KP.softDot(g, x, y, 14 + Rn() * 22, `${o.p}-gl-${c === KS.C.starWarm ? "warm" : c === KS.C.starBlue ? "blue" : "white"}`, 0.35 * a);
      let el;
      if (big) {
        const s = 6 + Rn() * 7;
        el = K.el("path", { d: `M 0 ${f(-s)} L ${f(s * 0.22)} ${f(-s * 0.22)} L ${f(s)} 0 L ${f(s * 0.22)} ${f(s * 0.22)} L 0 ${f(s)} L ${f(-s * 0.22)} ${f(s * 0.22)} L ${f(-s)} 0 L ${f(-s * 0.22)} ${f(-s * 0.22)} Z`, fill: c, transform: `translate(${f(x)},${f(y)})` }, g);
      } else el = K.el("circle", { cx: f(x), cy: f(y), r: f(rmin + Rn() * (rmax - rmin)), fill: c }, g);
      el.setAttribute("opacity", f(a));
      if (Rn() < 0.25) tw.push({ el, a, ph: Rn() * 6.28, sp: 1 + Rn() * 2.5 });
    }
    const api = { g };
    api.update = (t) => tw.forEach((s) => s.el.setAttribute("opacity", f(s.a * (0.55 + 0.45 * Math.sin(t * s.sp + s.ph)))));
    api.update(0);
    return api;
  };
  /* Nebula wisps: soft-edged translucent blobs clustered along a diagonal band, so the sky has structure at the scale
     of a phone screen (smooth gradients alone read as an empty field). */
  KS.wisps = (parent, o = {}) => {
    const Rn = K.rng(o.seed ?? 13), g = K.g(parent), cols = o.colors || KS.C.nebula;
    const x0 = o.x0 ?? -300, x1 = o.x1 ?? 1380, y0 = o.y0 ?? -400, y1 = o.y1 ?? 2320;
    for (let i = 0; i < (o.n ?? 14); i++) {
      const u = Rn(), x = x0 + u * (x1 - x0) + (Rn() - 0.5) * 500, y = y1 - u * (y1 - y0) + (Rn() - 0.5) * 700;   // a band from lower left to upper right
      const r = 120 + Rn() * 260, c = cols[Math.floor(Rn() * cols.length)];
      K.el("path", { d: K.blob(r, 0.28, Rn() * 6, 9, 300 + i, 1.6, 0.8), fill: c, opacity: f((o.a ?? 0.55) * (0.08 + Rn() * 0.1)), transform: `translate(${f(x)},${f(y)}) rotate(${f(-35 + (Rn() - 0.5) * 30)})` }, g);
      K.el("path", { d: K.blob(r * 0.55, 0.3, Rn() * 6, 8, 500 + i, 1.5, 0.8), fill: c, opacity: f((o.a ?? 0.55) * (0.08 + Rn() * 0.08)), transform: `translate(${f(x + (Rn() - 0.5) * r * 0.6)},${f(y + (Rn() - 0.5) * r * 0.4)}) rotate(${f(-35)})` }, g);
    }
    return { g };
  };
  /* Out-of-focus dust in the near layer: big, faint soft dots that slide past faster than the stars (depth). */
  KS.dust = (parent, o = {}) => {
    const Rn = K.rng(o.seed ?? 17), g = K.g(parent);
    for (let i = 0; i < (o.n ?? 12); i++) KP.softDot(g, -300 + Rn() * 1680, -500 + Rn() * 2900, 30 + Rn() * 70, `${o.p}-gl-${Rn() < 0.5 ? "blue" : "white"}`, 0.06 + Rn() * 0.1);
    return { g };
  };
  KS.nebula = (parent, o = {}) => {
    const Rn = K.rng(o.seed ?? 9), g = K.g(parent), defs = K.el("defs", {}, g), id = `neb${++uid}`;
    const cols = o.colors || KS.C.nebula;
    cols.forEach((c, i) => {
      const rg = K.el("radialGradient", { id: `${id}-${i}`, cx: 0.5, cy: 0.5, r: 0.5 }, defs);
      [[0, 0.55], [0.4, 0.28], [0.75, 0.08], [1, 0]].forEach(([of, a]) => K.el("stop", { offset: of, "stop-color": c, "stop-opacity": a }, rg));
    });
    for (let i = 0; i < (o.n ?? 7); i++) {
      const r = (o.rmin ?? 260) + Rn() * ((o.rmax ?? 560) - (o.rmin ?? 260));
      K.el("ellipse", { cx: f((o.x0 ?? -200) + Rn() * ((o.x1 ?? 1280) - (o.x0 ?? -200))), cy: f((o.y0 ?? -200) + Rn() * ((o.y1 ?? 2120) - (o.y0 ?? -200))), rx: f(r), ry: f(r * (0.55 + Rn() * 0.5)), fill: `url(#${id}-${i % cols.length})`, opacity: f((o.a ?? 0.6) * (0.5 + Rn() * 0.5)), transform: "" }, g);
    }
    return { g };
  };

  // ------------------------------------------------------------------ the black hole
  /* o: R (shadow radius, px), tilt (disk ellipse ratio, 0.18), p (scene prefix for KO glows), seed, glow (0..1),
        disk (0..1 opacity of the disk), bands (number of disk bands, 6), spin (radians per second at the inner edge).
     The disk is drawn as concentric circles inside a group squashed by `tilt`, so it foreshortens correctly; its
     near half is drawn again in front of the shadow. The lensed image of the far side arcs over the top. */
  KS.blackHole = (parent, o = {}) => {
    const R = o.R ?? 160, tilt = o.tilt ?? 0.18, D = KS.C.disk, id = `bh${++uid}`, nB = o.bands ?? 6;
    const g = K.g(parent), defs = K.el("defs", {}, g);
    // `mid` holds things that fall in from above: it is clipped at the centre line, so nothing that has gone into
    // the shadow can show below it
    const cpm = K.el("clipPath", { id: `${id}-mid` }, defs);
    K.el("rect", { x: -R * 40, y: -R * 60, width: R * 80, height: R * 60 }, cpm);
    const back = K.g(g), mid = K.g(g, o.midClip === false ? {} : { "clip-path": `url(#${id}-mid)` }), shadowG = K.g(g), front = K.g(g);
    const glow = KO ? KO.glow(back, { r: R * (o.glowR ?? 3.6), color: "warm", p: o.p, core: 0, k: o.glow ?? 0.55 }) : null;
    // bands: inner radius 1.5 R to about 3.3 R
    const bands = Array.from({ length: nB }, (_, i) => {
      const a = R * (1.5 + i * (1.8 / nB)), w = R * (1.8 / nB) * 1.05, c = D[Math.min(D.length - 1, i)];
      const lg = K.el("linearGradient", { id: `${id}-b${i}`, x1: -a, y1: 0, x2: a, y2: 0, gradientUnits: "userSpaceOnUse" }, defs);
      K.el("stop", { offset: 0, "stop-color": mix(c, "#ffffff", 0.45) }, lg);          // the side coming toward us is brighter
      K.el("stop", { offset: 0.5, "stop-color": c }, lg);
      K.el("stop", { offset: 1, "stop-color": mix(c, "#7a1f45", 0.45) }, lg);
      return { a, w, c, omega: (o.spin ?? 0.9) * Math.pow(1.5 / (a / R), 1.5) };
    });
    const cp = K.el("clipPath", { id: `${id}-near` }, defs);
    K.el("rect", { x: -R * 8, y: 0, width: R * 16, height: R * 8 }, cp);
    const diskLayer = (parentG, near) => {
      const dg = K.g(parentG, { transform: `scale(1,${f(tilt)})` });
      const inner = K.g(dg, near ? { "clip-path": `url(#${id}-near)` } : {});
      return bands.map((b, i) => {
        K.el("circle", { r: f(b.a), fill: "none", stroke: `url(#${id}-b${i})`, "stroke-width": f(b.w) }, inner);
        const streak = K.el("circle", { r: f(b.a + b.w * 0.15), fill: "none", stroke: mix(b.c, "#ffffff", 0.6), "stroke-width": f(b.w * 0.18), "stroke-dasharray": `${f(b.a * 0.5)} ${f(b.a * 0.9)}`, "stroke-linecap": "round", opacity: 0.4 }, inner);
        return streak;
      });
    };
    const diskBack = K.g(back), lens = K.g(back);
    const streaksBack = diskLayer(diskBack, false);
    // lensed arcs: the far side of the disk, bent over the top of the shadow (thick) and under it (thin)
    // flat ends that dip a little below the disk plane, so they tuck behind the near half of the disk
    const arc = (r, w, c, top, op) => {
      const a0 = top ? Math.PI - 0.12 : 0.12, a1 = top ? 2 * Math.PI + 0.12 : Math.PI - 0.12, n = 32, pts = [];
      for (let k = 0; k <= n; k++) { const a = a0 + ((a1 - a0) * k) / n; pts.push([Math.cos(a) * r, Math.sin(a) * r]); }
      const d = "M " + pts.map((q) => `${f(q[0])} ${f(q[1])}`).join(" L ");
      return K.el("path", { d, fill: "none", stroke: c, "stroke-width": f(w), "stroke-linecap": "butt", opacity: op }, lens);
    };
    [[1.42, 0.13, D[3]], [1.3, 0.13, D[2]], [1.19, 0.12, D[1]], [1.1, 0.08, D[0]]].forEach(([r, w, c]) => arc(R * r, R * w, c, true, 0.95));
    const lensStreak = arc(R * 1.26, R * 0.05, "#ffffff", true, 0.45);
    lensStreak.setAttribute("stroke-dasharray", `${f(R * 0.35)} ${f(R * 0.6)}`);
    arc(R * 1.1, R * 0.07, D[2], false, 0.75);
    arc(R * 1.04, R * 0.04, D[0], false, 0.8);
    const ring = K.el("circle", { r: f(R * 1.02), fill: "none", stroke: KS.C.ring, "stroke-width": f(R * 0.035) }, shadowG);
    const shadow = K.el("circle", { r: f(R), fill: KS.C.shadow }, shadowG);
    const diskFront = K.g(front);
    const streaksFront = diskLayer(diskFront, true);
    const api = { g, R, back, mid, front, shadow, ring, glow, diskBack, diskFront, lens, disk: o.disk ?? 1 };
    api.update = (t) => {
      bands.forEach((b, i) => {
        const deg = f(((-b.omega * t * 180) / Math.PI) % 360);
        streaksBack[i].setAttribute("transform", `rotate(${deg})`);
        streaksFront[i].setAttribute("transform", `rotate(${deg})`);
      });
      lensStreak.setAttribute("stroke-dashoffset", f(-t * R * 0.9));
      [diskBack, diskFront].forEach((d) => d.setAttribute("opacity", f(api.disk)));
      lens.setAttribute("opacity", f(Math.min(1, api.disk * 1.2)));
      if (glow) glow.update();
    };
    api.update(0);
    return api;
  };

  // ------------------------------------------------------------------ small props
  KS.clock = (parent, o = {}) => {
    const r = o.r ?? 60, g = K.g(parent), period = o.period ?? 4;
    K.el("circle", { r: f(r * 1.12), fill: o.rim ?? "#2a2350" }, g);
    const face = K.el("circle", { r: f(r), fill: o.face ?? "#fbf7ee" }, g);
    for (let k = 0; k < 12; k++) {
      const a = (k / 12) * Math.PI * 2, r1 = r * (k % 3 ? 0.8 : 0.72);
      K.el("line", { x1: f(Math.sin(a) * r1), y1: f(-Math.cos(a) * r1), x2: f(Math.sin(a) * r * 0.9), y2: f(-Math.cos(a) * r * 0.9), stroke: "#2a2350", "stroke-width": f(r * (k % 3 ? 0.05 : 0.09)), "stroke-linecap": "round" }, g);
    }
    const hand = K.el("line", { x1: 0, y1: f(r * 0.12), x2: 0, y2: f(-r * 0.72), stroke: o.hand ?? "#ff6a3d", "stroke-width": f(r * 0.1), "stroke-linecap": "round" }, g);
    K.el("circle", { r: f(r * 0.1), fill: "#2a2350" }, g);
    const api = { g, face, hand };
    api.set = (sec) => hand.setAttribute("transform", `rotate(${f(((sec / period) * 360) % 360)})`);
    api.set(0);
    return api;
  };
  KS.galaxy = (parent, o = {}) => {
    const r = o.r ?? 150, Rn = K.rng(o.seed ?? 4), g = K.g(parent), spin = K.g(g);
    if (KO) KO.glow(spin, { r: r * 1.1, color: "blue", p: o.p, core: 0, k: 0.45 });
    for (let arm = 0; arm < 2; arm++) for (let k = 0; k < 70; k++) {
      const u = k / 70, th = arm * Math.PI + u * 4.2 + (Rn() - 0.5) * 0.35, rr = r * (0.12 + 0.88 * u) + (Rn() - 0.5) * r * 0.08;
      K.el("circle", { cx: f(Math.cos(th) * rr), cy: f(Math.sin(th) * rr * 0.62), r: f((1.2 + Rn() * 3) * (1.2 - u * 0.6)), fill: Rn() < 0.25 ? "#ffd9a6" : "#d6e4ff", opacity: f(0.5 + Rn() * 0.5) }, spin);
    }
    if (KO) KO.glow(spin, { r: r * 0.42, color: "warm", p: o.p, core: 0, k: 0.9 });
    K.el("ellipse", { rx: f(r * 0.1), ry: f(r * 0.07), fill: "#fff3d6" }, spin);
    const api = { g };
    api.update = (t) => spin.setAttribute("transform", `rotate(${f(t * (o.speed ?? 6))})`);
    return api;
  };
  KS.sun = (parent, o = {}) => {
    const r = o.r ?? 30, g = K.g(parent);
    for (let k = 0; k < 10; k++) {
      const a = (k / 10) * Math.PI * 2;
      K.el("line", { x1: f(Math.cos(a) * r * 1.2), y1: f(Math.sin(a) * r * 1.2), x2: f(Math.cos(a) * r * 1.55), y2: f(Math.sin(a) * r * 1.55), stroke: "#ffc94a", "stroke-width": f(r * 0.16), "stroke-linecap": "round" }, g);
    }
    K.el("circle", { r: f(r), fill: "#ffd23f" }, g);
    K.el("circle", { cx: f(-r * 0.25), cy: f(-r * 0.25), r: f(r * 0.45), fill: "#ffe98a", opacity: 0.8 }, g);
    return { g };
  };
  /* A small crewed spacecraft seen from the side, nose to the right: a rounded hull, a big round window, solar
     panels on a strut, an engine bell with a soft flame at the back. o.s scales it (about 520 px long at 1). */
  KS.ship = (parent, o = {}) => {
    const s = o.s ?? 1, g = K.g(parent), b = K.g(g, { transform: `scale(${f(s)})` });
    const panel = (x, y) => {
      const pg = K.g(b, { transform: `translate(${x},${y})` });
      K.el("rect", { x: -70, y: -34, width: 140, height: 68, rx: 6, fill: "#2c4fa8" }, pg);
      for (let i = -2; i <= 2; i++) K.el("line", { x1: i * 28, y1: -34, x2: i * 28, y2: 34, stroke: "#5f86e8", "stroke-width": 4 }, pg);
      K.el("line", { x1: -70, y1: 0, x2: 70, y2: 0, stroke: "#5f86e8", "stroke-width": 4 }, pg);
    };
    K.el("rect", { x: -40, y: -150, width: 14, height: 300, rx: 7, fill: "#8d98b0" }, b);                            // strut
    panel(-33, -150); panel(-33, 150);
    const flame = K.el("path", { d: "M -250 -26 Q -330 0 -250 26 Z", fill: "#ff9a45", opacity: 0.9 }, b);
    K.el("path", { d: "M -200 -40 L -250 -56 L -250 56 L -200 40 Z", fill: "#6d7790" }, b);                         // engine bell
    K.el("path", { d: "M -210 -78 Q -210 -96 -186 -96 L 150 -96 Q 270 -96 270 0 Q 270 96 150 96 L -186 96 Q -210 96 -210 78 Z", fill: "#eef1f8" }, b);   // hull
    K.el("path", { d: "M -210 40 L 255 40 Q 245 80 150 96 L -186 96 Q -210 96 -210 78 Z", fill: "#c9d1e4" }, b);
    K.el("rect", { x: -150, y: -96, width: 26, height: 192, fill: "#ff8a3d" }, b);                                  // a stripe
    K.el("circle", { cx: 150, cy: -6, r: 58, fill: "#2a2350" }, b);                                                   // window
    const win = K.el("circle", { cx: 150, cy: -6, r: 48, fill: "#bfe6ff", opacity: 0.85 }, b);
    K.el("path", { d: "M 118 -30 Q 140 -50 165 -48", fill: "none", stroke: "#ffffff", "stroke-width": 9, "stroke-linecap": "round", opacity: 0.9 }, b);
    [-60, 0, 60].forEach((x) => K.el("circle", { cx: x, cy: -40, r: 9, fill: "#ffd23f" }, b));                        // lights
    return { g, flame, win };
  };
  KS.telescope = (parent, o = {}) => {
    const L = o.L ?? 120, g = K.g(parent);
    K.el("path", { d: `M 0 -10 L ${f(L)} -18 L ${f(L)} 18 L 0 10 Z`, fill: o.color ?? "#3a3f73" }, g);
    K.el("rect", { x: f(L - 6), y: -22, width: 16, height: 44, rx: 6, fill: "#2a2350" }, g);
    K.el("ellipse", { cx: f(L + 10), cy: 0, rx: 5, ry: 17, fill: "#9fd8ff" }, g);
    K.el("rect", { x: f(L * 0.35), y: -14, width: 10, height: 28, rx: 4, fill: "#ff8a3d" }, g);
    return { g };
  };

  /* The spaghettified astronaut: a long, thin, wobbling noodle in the suit's colours with the helmet at the top.
     A body falling straight in stretches along the line to the centre, so the noodle is straight (radial), not a
     spiral. set(top, bottom, x, w, phase): top and bottom y, the x of the line, the width, the wobble phase.
     Draw it in the black hole's `mid` layer, so the part that has crossed the shadow's edge disappears. */
  KS.noodle = (parent, o = {}) => {
    const g = K.g(parent);
    const mkS = (stroke, cap = "round") => K.el("path", { fill: "none", stroke, "stroke-linecap": cap, "stroke-linejoin": "round" }, g);
    const arms = [mkS(o.color ?? "#f4f6fb"), mkS(o.color ?? "#f4f6fb")];                         // two thin arms, still up in panic
    const gloves = [0, 1].map(() => K.el("circle", { r: 1, fill: o.stripe ?? "#ff8a3d" }, g));
    const body = mkS(o.color ?? "#f4f6fb"), shade = mkS(o.shade ?? "#c9d1e4"), stripe = mkS(o.stripe ?? "#ff8a3d", "butt");
    const helmet = K.g(g);
    K.el("circle", { r: 0.5, fill: o.skin ?? "#e0ac86" }, helmet);
    K.el("ellipse", { cx: 0.22, cy: -0.08, rx: 0.07, ry: 0.11, fill: "#1c1233" }, helmet);             // a wide eye
    K.el("ellipse", { cx: 0.28, cy: 0.24, rx: 0.07, ry: 0.09, fill: "#5a2a2e" }, helmet);             // an "o" mouth
    K.el("circle", { r: 1, fill: "#bfe6ff", "fill-opacity": 0.3, stroke: "#eef4ff", "stroke-width": 0.14 }, helmet);
    K.el("path", { d: "M -0.55 -0.6 Q 0 -1.05 0.6 -0.62", fill: "none", stroke: "#ffffff", "stroke-width": 0.12, "stroke-linecap": "round", opacity: 0.7 }, helmet);
    const api = { g };
    api.set = (top, bottom, x, w, phase = 0, amp = 1) => {
      const len = Math.max(1, bottom - top), n = Math.max(8, Math.round(len / 24)), pts = [];
      const wob = (u) => Math.sin(phase + u * 9) * w * 0.55 * amp * Math.sin(Math.PI * Math.min(1, u * 1.3));
      for (let k = 0; k <= n; k++) { const u = k / n; pts.push([x + wob(u), top + len * u]); }
      const d = K.smooth(pts, false);
      body.setAttribute("d", d); body.setAttribute("stroke-width", f(w));
      shade.setAttribute("d", d); shade.setAttribute("stroke-width", f(w * 0.32)); shade.setAttribute("transform", `translate(${f(-w * 0.22)},0)`);
      stripe.setAttribute("d", d); stripe.setAttribute("stroke-width", f(w * 1.02)); stripe.setAttribute("stroke-dasharray", `${f(w * 0.45)} ${f(Math.max(w * 2, len / 7))}`);
      const hr = Math.max(w * 1.45, 16), hx = x + wob(0);
      helmet.setAttribute("transform", `translate(${f(hx)},${f(top)}) scale(${f(hr)})`);
      // arms: from the shoulders (just under the helmet) up and out, wobbling with the body
      [-1, 1].forEach((sd, i) => {
        const sy = top + hr * 1.1, sx = hx + sd * w * 0.3, L = Math.min(len * 0.22, hr * 2.6);
        const ex = sx + sd * L * 0.45 + Math.sin(phase * 1.3 + i) * w * 0.3, ey = sy - L;
        arms[i].setAttribute("d", `M ${f(sx)} ${f(sy)} Q ${f(sx + sd * L * 0.5)} ${f(sy - L * 0.4)} ${f(ex)} ${f(ey)}`);
        arms[i].setAttribute("stroke-width", f(w * 0.55));
        gloves[i].setAttribute("cx", f(ex)); gloves[i].setAttribute("cy", f(ey)); gloves[i].setAttribute("r", f(w * 0.42));
      });
    };
    api.set(0, 100, 0, 30);
    return api;
  };
})();
