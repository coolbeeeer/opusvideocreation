/* world.js: the park, the walker and the four dive levels, shared by compositions/walk.html and finale.html.
   Loaded in the root <head> after the kits. Everything is built per scene (each scene gets its own copy in its own
   DOM, with its own id prefix) and driven by plain numbers, so any frame can be rendered on its own.

   WORLD.build(R, id, o) -> S
     o.palette   "day" or "sunset"
     S.walker    a KH.walker on the path (S.walker.at(phase) poses it and moves it to its world x)
     S.zc        the zoom chain: level 0 = park, 1 = thigh in cross-section, 2 = a muscle bundle, 3 = inside a muscle fibre
     S.camera(Z, F)  places every level; F in park units. S.followX(phase) is the camera x that keeps the walker framed
     S.focus(logZ, wide)  the camera point for a zoom value: eases from `wide` to each lens centre as the zoom passes it
     S.ui, S.stage, S.defs, S.p (id prefix), S.L3 (the fibre interior: its mitochondria)
*/
(function () {
  const K = window.KIT, KP = window.KITPLUS, KH = window.HUMAN, KC = window.CELL, KO = window.OCEAN;
  const f = K.f;
  const WORLD = (window.WORLD = {});
  const PAL = {
    day: {
      sky: ["#62c4df", "#9fe0ea", "#d6f5ec"], sun: "#fff3c4", glow: "warm",
      far: "#a3d6df", farWin: "#c2e6ea", hill: "#86cfa4", hill2: "#6dbf92", tree: ["#5bb487", "#4aa077", "#76c995"], trunk: "#7d5d4d",
      grass: "#93d27c", grassEdge: "#7cc066", path: "#eed6a2", pathEdge: "#dcbd81", pathDot: "#e3c58c", fg: "#4f9f5f", fg2: "#3f8a50", lamp: "#4f6b78", cloud: "#ffffff",
    },
    sunset: {
      sky: ["#4a5a9a", "#e28b8f", "#ffcf92"], sun: "#ffe7b0", glow: "warm",
      far: "#9a7fa8", farWin: "#ffd59a", hill: "#9b7a8f", hill2: "#86677d", tree: ["#7d6a86", "#6d5b78", "#8f7a96"], trunk: "#5a4458",
      grass: "#b48a78", grassEdge: "#9f7666", path: "#f0bf8f", pathEdge: "#d9a271", pathDot: "#e6b07f", fg: "#4f3850", fg2: "#412e43", lamp: "#4d3e55", cloud: "#ffd0b0",
      groundShade: "#2e1a34",   // the near ground darkens toward the bottom of the frame (dusk)
    },
  };
  WORLD.PAL = PAL;
  const GROUND = 1100;            // the path's surface in park units (= screen px at zoom 1)

  WORLD.build = (R, id, o = {}) => {
    const P = PAL[o.palette || "day"], W = 1080, H = 1920, p = id;
    const stage = document.createElement("div");
    stage.className = "stage";
    stage.style.cssText = `position:absolute;inset:0;overflow:hidden;background:${P.sky[1]}`;
    R.appendChild(stage);
    const svg = K.el("svg", { viewBox: `0 0 ${W} ${H}`, width: W, height: H, style: "position:absolute;inset:0;overflow:visible" });
    stage.appendChild(svg);
    const defs = K.el("defs", {}, svg);
    if (KO) KO.glowDefs(defs, p);
    const sg = K.el("linearGradient", { id: `${p}-sky`, x1: 0, y1: -400, x2: 0, y2: GROUND, gradientUnits: "userSpaceOnUse" }, defs);
    P.sky.forEach((c, i) => K.el("stop", { offset: i / (P.sky.length - 1), "stop-color": c }, sg));
    const S = { W, H, p, stage, svg, defs, P, layers: [] };

    // ---------------------------------------------------------------- level 0: the park, in parallax sub-layers
    const park = (g) => {
      const layer = (d) => { const lg = K.g(g); S.layers.push({ g: lg, d }); return lg; };
      const rnd = K.rng(o.seed || 7);
      // sky and sun move with the camera (d = 0) but still zoom with the world
      const sky = layer(0);
      K.el("rect", { x: -4000, y: -3000, width: 9000, height: 3000 + GROUND, fill: `url(#${p}-sky)` }, sky);
      K.el("rect", { x: -4000, y: GROUND - 40, width: 9000, height: 3000, fill: P.sky[2] }, sky);
      if (KO) KO.glow(sky, { x: o.palette === "sunset" ? 760 : 800, y: o.palette === "sunset" ? 860 : 330, r: o.palette === "sunset" ? 520 : 360, color: "warm", p, core: 0, k: 1 });
      K.el("circle", { cx: o.palette === "sunset" ? 760 : 800, cy: o.palette === "sunset" ? 860 : 330, r: o.palette === "sunset" ? 120 : 78, fill: P.sun }, sky);
      // clouds and birds drift slowly
      const clouds = layer(0.05);
      for (let i = 0; i < 7; i++) {
        const x = -600 + i * 520 + rnd() * 200, y = 420 + rnd() * 300, s = 0.7 + rnd() * 0.6;
        const cg = K.g(clouds, { transform: `translate(${f(x)},${f(y)}) scale(${f(s)})`, opacity: 0.85 });
        [[0, 0, 60], [60, -18, 48], [110, 4, 40], [-55, 8, 40]].forEach(([cx, cy, r]) => K.el("circle", { cx, cy, r, fill: P.cloud }, cg));
        K.el("rect", { x: -95, y: 4, width: 245, height: 44, rx: 22, fill: P.cloud }, cg);
      }
      S.birds = K.g(layer(0.12));
      for (let i = 0; i < 4; i++) K.el("path", { d: "M -16 0 Q -8 -10 0 0 Q 8 -10 16 0", fill: "none", stroke: "#3f5b6a", "stroke-width": 4, "stroke-linecap": "round", transform: `translate(${200 + i * 70},${560 + (i % 2) * 40})` }, S.birds);
      // far city
      const city = layer(0.15);
      for (let i = 0; i < 26; i++) {
        const x = -1400 + i * 170 + rnd() * 40, w = 110 + rnd() * 70, h = 150 + rnd() * 260;
        K.el("rect", { x: f(x), y: f(GROUND - 230 - h), width: f(w), height: f(h + 240), fill: P.far, rx: 6 }, city);
        for (let wy = 0; wy < h - 30; wy += 46) for (let wx = 16; wx < w - 22; wx += 34) if (rnd() > 0.45) K.el("rect", { x: f(x + wx), y: f(GROUND - 210 - h + wy), width: 14, height: 20, rx: 3, fill: P.farWin, opacity: 0.7 }, city);
      }
      // rolling hills with trees
      const hills = layer(0.4);
      let hp = `M -3000 ${GROUND - 120}`;
      for (let x = -3000; x <= 7000; x += 400) hp += ` Q ${x + 200} ${GROUND - 220 - rnd() * 80} ${x + 400} ${GROUND - 120}`;
      K.el("path", { d: `${hp} L 7000 ${GROUND + 400} L -3000 ${GROUND + 400} Z`, fill: P.hill }, hills);
      for (let i = 0; i < 30; i++) {
        const x = -1500 + i * 260 + rnd() * 120, s = 0.7 + rnd() * 0.5, c = P.tree[i % 3];
        const tg = K.g(hills, { transform: `translate(${f(x)},${GROUND - 150}) scale(${f(s)})` });
        K.el("rect", { x: -9, y: -70, width: 18, height: 80, fill: P.trunk, rx: 6 }, tg);
        K.el("circle", { cx: 0, cy: -120, r: 70, fill: c }, tg);
        K.el("circle", { cx: -38, cy: -90, r: 46, fill: c }, tg);
        K.el("circle", { cx: 40, cy: -96, r: 50, fill: c }, tg);
        K.el("path", { d: "M -50 -150 Q -20 -190 20 -178", fill: "none", stroke: "#ffffff", "stroke-width": 9, "stroke-linecap": "round", opacity: 0.25 }, tg);
      }
      // lamp posts and benches, nearer
      const props = layer(0.8);
      K.el("rect", { x: -4000, y: GROUND - 70, width: 12000, height: 120, fill: P.hill2 }, props);
      for (let i = 0; i < 12; i++) {
        const x = -800 + i * 620;
        const lg = K.g(props, { transform: `translate(${x},${GROUND - 30})` });
        K.el("rect", { x: -7, y: -400, width: 14, height: 400, fill: P.lamp, rx: 7 }, lg);
        K.el("path", { d: "M 0 -400 Q 0 -440 44 -440", fill: "none", stroke: P.lamp, "stroke-width": 12, "stroke-linecap": "round" }, lg);
        K.el("rect", { x: 30, y: -448, width: 34, height: 22, rx: 8, fill: P.lamp }, lg);
        if (i % 2) {
          const bg = K.g(props, { transform: `translate(${x + 260},${GROUND - 34})` });
          K.el("rect", { x: -80, y: -46, width: 160, height: 14, rx: 6, fill: P.trunk }, bg);
          K.el("rect", { x: -80, y: -80, width: 160, height: 12, rx: 6, fill: P.trunk }, bg);
          K.el("rect", { x: -64, y: -34, width: 10, height: 36, fill: P.lamp }, bg);
          K.el("rect", { x: 54, y: -34, width: 10, height: 36, fill: P.lamp }, bg);
        }
      }
      // the path the walker is on (d = 1)
      const ground = layer(1);
      K.el("rect", { x: -4000, y: GROUND - 34, width: 12000, height: 40, fill: P.grass }, ground);
      K.el("rect", { x: -4000, y: GROUND - 4, width: 12000, height: 150, fill: P.path }, ground);
      K.el("rect", { x: -4000, y: GROUND - 4, width: 12000, height: 10, fill: P.pathEdge }, ground);
      for (let i = 0; i < 160; i++) K.el("circle", { cx: f(-3000 + rnd() * 10000), cy: f(GROUND + 20 + rnd() * 110), r: f(2 + rnd() * 4), fill: P.pathDot }, ground);
      K.el("rect", { x: -4000, y: GROUND + 146, width: 12000, height: 1400, fill: P.grass }, ground);
      K.el("rect", { x: -4000, y: GROUND + 146, width: 12000, height: 10, fill: P.grassEdge }, ground);
      if (P.groundShade) {
        const gs = K.el("linearGradient", { id: `${p}-gshade`, x1: 0, y1: GROUND + 156, x2: 0, y2: GROUND + 1100, gradientUnits: "userSpaceOnUse" }, defs);
        K.el("stop", { offset: 0, "stop-color": P.groundShade, "stop-opacity": 0 }, gs);
        K.el("stop", { offset: 1, "stop-color": P.groundShade, "stop-opacity": 0.8 }, gs);
        K.el("rect", { x: -4000, y: GROUND + 156, width: 12000, height: 1400, fill: `url(#${p}-gshade)` }, ground);
      }
      S.walkerG = K.g(ground);
      S.walker = KH.walker(S.walkerG, { x0: o.x0 ?? 470, y0: GROUND + 40, look: o.look });
      S.shadow = K.el("ellipse", { cx: 0, cy: GROUND + 42, rx: 120, ry: 14, fill: "#000000", opacity: 0.12 }, ground);
      S.walkerG.parentNode.insertBefore(S.shadow, S.walkerG);
      // foreground grass and flowers, cropped by the bottom of the frame
      const fg = layer(1.35);
      for (let i = 0; i < 60; i++) {
        const x = -1500 + i * 130 + rnd() * 60, y = GROUND + 420 + rnd() * 500, h = 50 + rnd() * 70;
        K.el("path", { d: `M ${f(x - 22)} ${f(y)} Q ${f(x - 14)} ${f(y - h)} ${f(x - 4)} ${f(y - h * 0.4)} Q ${f(x)} ${f(y - h * 1.2)} ${f(x + 6)} ${f(y - h * 0.45)} Q ${f(x + 16)} ${f(y - h)} ${f(x + 24)} ${f(y)} Z`, fill: i % 3 ? P.fg : P.fg2 }, fg);
        if (i % 4 === 0) { K.el("circle", { cx: f(x + 30), cy: f(y - h * 0.9), r: 11, fill: i % 8 ? "#ffd36b" : "#ff9ab5" }, fg); K.el("circle", { cx: f(x + 30), cy: f(y - h * 0.9), r: 4.5, fill: "#ffffff" }, fg); }
      }
    };

    // ---------------------------------------------------------------- the dive levels
    const levels = [
      { draw: park },
      { at: () => S.walker.thighPoint(0.42), r: 40, mag: 28, draw: (g) => { S.L1 = KC.thighSection(g, 1120, 21); } },
      { at: [0, 0], r: 110, mag: 10.2, fade: [0.035, 0.11], ringOpacity: 0, draw: (g) => { S.L2 = KC.fascicle(g, 1120, 31); } },
      { at: [0, 0], r: 95, mag: 11.8, fade: [0.04, 0.12], ringOpacity: 0, draw: (g) => { S.L3 = KC.fiber(g, 1120, { prefix: p, seed: 41 }); } },
    ];
    const worldG = K.g(svg);
    S.zc = KP.zoomChain(worldG, levels, { prefix: p, W, H });
    // aim each lens at a real bundle and a real fibre near the middle (so the pans stay short)
    const nearest = (list, x, y) => list.reduce((b, q) => (Math.hypot(q[0] - x, q[1] - y) < Math.hypot(b[0] - x, b[1] - y) ? q : b));
    const b2 = nearest(S.L1.bundles, 330, -260), f3 = nearest(S.L2.fibers, 90, -60);
    levels[2].at = [b2[0], b2[1]];
    levels[2]._R = b2[2] * 0.96 * levels[2].mag;      // the lens is the bundle's own outline
    levels[3].at = [f3[0], f3[1]];
    levels[3]._R = f3[2] * 0.97 * levels[3].mag;      // ... and the fibre's
    S.lensL2 = b2; S.lensL3 = f3;

    const ui = document.createElement("div");
    ui.className = "ui";
    ui.style.cssText = "position:absolute;inset:0;";
    stage.appendChild(ui);
    S.ui = ui;

    const F0x = (o.x0 ?? 470) + 70;
    S.followX = (phase) => S.walker.x(phase) + 70;
    S.camera = (Z, F) => {
      // parallax inside the park: each sub-layer slides by (1 - d) of the camera's travel
      const dx = F[0] - F0x;
      S.layers.forEach((L) => L.g.setAttribute("transform", `translate(${f(dx * (1 - L.d))},0)`));
      S.zc.set(Z, F);
    };
    /* The camera point for a zoom: from `wide` (park units) to the thigh lens, then to each next lens.
       Each pan starts before its lens is reached and ends before that lens fills the screen. */
    S.focus = (logZ, wide) => {
      const M = S.zc.M, sm = (x) => x * x * (3 - 2 * x);
      const seg = (a, b) => Math.max(0, Math.min(1, (logZ - a) / (b - a)));
      const P1 = S.zc.point(1, [0, 0]), P2 = S.zc.point(2, [0, 0]), P3 = S.zc.point(3, [0, 0]);
      const L1 = Math.log(M[1]), L2 = Math.log(M[2]), L3 = Math.log(M[3]);
      const u1 = sm(seg(0, L1 - 0.4)), u2 = sm(seg(L1 - 0.9, L2 - 1.2)), u3 = sm(seg(L2 - 0.9, L3 - 1.2));
      let F = [wide[0] + (P1[0] - wide[0]) * u1, wide[1] + (P1[1] - wide[1]) * u1];
      F = [F[0] + (P2[0] - P1[0]) * u2, F[1] + (P2[1] - P1[1]) * u2];
      F = [F[0] + (P3[0] - P2[0]) * u3, F[1] + (P3[1] - P2[1]) * u3];
      return F;
    };
    S.GROUND = GROUND;
    return S;
  };
})();
