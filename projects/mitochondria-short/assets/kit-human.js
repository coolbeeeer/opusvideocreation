/* kit-human.js: a Kurzgesagt-style human with an articulated rig and a procedural walk cycle.
   Load after kit.js. Seek-safe: every pose is a pure function of a walk phase; nothing reads the clock.

   How it works (see projects/mitochondria-short/NOTES.md for the long version)
   - The body is a rig of rigid parts: pelvis -> torso -> neck -> head, shoulder -> upper arm -> forearm -> hand,
     hip -> thigh -> shin -> foot. Each part is a flat shape drawn from its two joint positions every frame.
   - KH.walkPose(phase, gait) returns joint positions for one instant of the cycle. It is pure maths (also runs in
     Node, see audio/js_events.cjs), in a body frame: x forward, y up, ground at y = 0, pelvis above x = 0.
       feet:   each foot is planted for 62 % of the cycle and slides backwards at exactly the walking speed, so in the
               world it stands still; heel-strike and toe-off rotate the foot about the heel or the toe; during the
               swing the ankle travels forward on an eased arc
       knees:  solved by two-bone inverse kinematics from hip and ankle (knee always bends forward)
       pelvis: bobs twice per cycle, highest at mid-stance
       arms:   swing opposite to the legs with a little lag; elbows bend more on the forward swing
   - KH.human(parent, o) draws the figure and returns { g, setPose(pose), pose }. Poses that are not walks
     (standing, waving) come from KH.standPose() and can be edited joint by joint.
   - KH.phaseTable(keys, t1) turns a speed curve (e.g. "slow to 10 % for the dive") into phase(t) by integration,
     so feet stay planted while time slows down.
*/
(function () {
  const W = typeof window !== "undefined" ? window : globalThis;
  const K = W.KIT;
  const KH = (W.HUMAN = {});
  const f = (n) => (Math.round(n * 100) / 100).toString();
  const D2R = Math.PI / 180;

  // ------------------------------------------------------------------ dimensions (px, for a ~690 px tall adult)
  KH.DIM = {
    ankleH: 24, thigh: 168, shin: 158, heel: 20, toe: 66,           // foot: heel 20 px behind, toe 66 px in front of the ankle
    torso: 214, neck: 16, headR: 56, upperArm: 118, foreArm: 108, handR: 17,
    hipW: 33, kneeW: 24, ankleW: 17, upperArmW: 21, foreArmW: 17,
  };
  KH.GAIT = { stride: 280, stance: 0.62, lift: 44, hipMid: 340, bob: 20, armSwing: 24, lean: 5, period: 1.15 };
  KH.speed = (g = KH.GAIT) => g.stride / g.stance / g.period;     // world px per second at walk rate 1

  // ------------------------------------------------------------------ small maths
  const smooth = (u) => u * u * (3 - 2 * u);
  const clamp01 = (u) => Math.max(0, Math.min(1, u));
  const rot = (v, a) => [v[0] * Math.cos(a) - v[1] * Math.sin(a), v[0] * Math.sin(a) + v[1] * Math.cos(a)];
  const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
  const lerp = (a, b, u) => a + (b - a) * u;

  /* Two-bone IK. hip, ankle in y-up coordinates; returns the knee, bent forward (+x). If the ankle is out of reach
     the bones stretch by up to 2 % (invisible), then the ankle is pulled back toward the hip. */
  KH.solveLeg = (hip, ankle, L1, L2) => {
    let dx = ankle[0] - hip[0], dy = ankle[1] - hip[1], d = Math.hypot(dx, dy);
    const reach = (L1 + L2) * 1.02;
    if (d > reach) { dx *= reach / d; dy *= reach / d; d = reach; }
    const k = Math.max(1, d / (L1 + L2)), a = L1 * k, b = L2 * k;    // stretch only when out of reach
    const cosA = Math.max(-1, Math.min(1, (a * a + d * d - b * b) / (2 * a * d)));
    const alpha = Math.acos(cosA);
    const u = [dx / d, dy / d];
    const kn = rot(u, alpha);                       // counter-clockwise from the hip-ankle line: knee forward
    return { knee: [hip[0] + kn[0] * a, hip[1] + kn[1] * a], ankle: [hip[0] + dx, hip[1] + dy] };
  };

  /* One foot. phi in [0,1): 0 = heel strike, stance until gait.stance, then swing.
     Returns ankle position (y-up, relative to the point under the pelvis) and the foot angle (radians, + = toe up). */
  KH.footAt = (phi, g = KH.GAIT, dim = KH.DIM) => {
    const S = g.stride, Dst = g.stance, a = 0.1, b = 0.72;
    const heelVec = [dim.heel, dim.ankleH], toeVec = [-dim.toe, dim.ankleH];   // ankle relative to heel / toe contact
    const stanceAnkle = (u) => {
      const xs = S * (0.5 - u);                        // where the foot's sole point under the ankle is on the ground
      if (u < a) {                                      // heel strike: rolls down onto the heel
        const beta = 12 * D2R * (1 - smooth(u / a));
        return { p: add([xs - dim.heel, 0], rot(heelVec, beta)), beta };
      }
      if (u < b) return { p: [xs, dim.ankleH], beta: 0 };
      const beta = -32 * D2R * smooth((u - b) / (1 - b)); // toe-off: rolls up onto the toe
      return { p: add([xs + dim.toe, 0], rot(toeVec, beta)), beta };
    };
    if (phi < Dst) return stanceAnkle(phi / Dst);
    const w = (phi - Dst) / (1 - Dst), s0 = stanceAnkle(1), s1 = stanceAnkle(0), e = smooth(w);
    return {
      p: [lerp(s0.p[0], s1.p[0], e), lerp(s0.p[1], s1.p[1], w) + g.lift * Math.sin(Math.PI * w) ** 1.2],
      beta: lerp(s0.beta, s1.beta, e) + 10 * D2R * Math.sin(Math.PI * w),
    };
  };

  /* Full-body pose at walk phase p (cycles; any real number). Leg A is the near leg; arm A the near arm. */
  KH.walkPose = (p, g = KH.GAIT, dim = KH.DIM) => {
    const ph = ((p % 1) + 1) % 1;
    const hipY = g.hipMid - g.bob * (1 - Math.cos(4 * Math.PI * (ph - 0.31))) / 2;
    const pelvis = [0, hipY];
    const legs = [0, 0.5].map((off, i) => {
      const ft = KH.footAt((ph + off) % 1, g, dim);
      const hip = [i ? -6 : 0, hipY];
      const ik = KH.solveLeg(hip, ft.p, dim.thigh, dim.shin);
      return { hip, knee: ik.knee, ankle: ik.ankle, foot: ft.beta };
    });
    const lean = g.lean * D2R + 1.2 * D2R * Math.sin(4 * Math.PI * ph);
    const shoulder = add(pelvis, rot([0, dim.torso], -lean));
    const neck = add(shoulder, rot([0, dim.neck], -lean * 0.5));
    const head = add(neck, [0, dim.headR * 0.9]);
    const arms = [0, 0.5].map((off, i) => {
      const s = Math.cos(2 * Math.PI * (ph + off - 0.06));            // +1 = leg forward -> this arm swings back
      const swing = -g.armSwing * D2R * s;                              // + = forward
      const sh = add(shoulder, [i ? -10 : 4, -8]);
      const elbow = add(sh, rot([0, -dim.upperArm], swing));
      const bend = (14 + 12 * Math.max(0, -s)) * D2R;
      const wrist = add(elbow, rot([0, -dim.foreArm], swing + bend));
      return { shoulder: sh, elbow, wrist };
    });
    return { pelvis, shoulder, neck, head, lean, headTilt: -lean * 0.3, legs, arms };
  };

  /* A standing pose to start from (edit joints for other poses, e.g. a wave). */
  KH.standPose = (dim = KH.DIM) => {
    const hipY = dim.ankleH + dim.thigh + dim.shin - 2;
    const leg = (x) => { const hip = [x, hipY], ankle = [x + 4, dim.ankleH]; return { hip, knee: KH.solveLeg(hip, ankle, dim.thigh, dim.shin).knee, ankle, foot: 0 }; };
    const shoulder = [0, hipY + dim.torso], neck = [0, hipY + dim.torso + dim.neck];
    const arm = (x, a1, a2) => { const sh = [x, shoulder[1] - 8], el = add(sh, rot([0, -dim.upperArm], a1 * D2R)); return { shoulder: sh, elbow: el, wrist: add(el, rot([0, -dim.foreArm], (a1 + a2) * D2R)) }; };
    return { pelvis: [0, hipY], shoulder, neck, head: add(neck, [0, dim.headR * 0.9]), lean: 0, headTilt: 0, legs: [leg(4), leg(-8)], arms: [arm(6, -4, 8), arm(-10, 4, 8)] };
  };
  /* Bend an arm of a pose to absolute angles (degrees from hanging down; + = forward). */
  KH.armTo = (pose, i, a1, a2, dim = KH.DIM) => {
    const sh = pose.arms[i].shoulder, el = add(sh, rot([0, -dim.upperArm], a1 * D2R));
    pose.arms[i] = { shoulder: sh, elbow: el, wrist: add(el, rot([0, -dim.foreArm], (a1 + a2) * D2R)) };
    return pose;
  };

  /* Walk phase as a function of time when the walking speed changes: keys = [[t, rate], ...] (rate 1 = normal).
     The rate is eased between keys (smoothstep) and integrated; returns phase(t) in cycles. */
  KH.phaseTable = (keys, t1, g = KH.GAIT, step = 1 / 240) => {
    const rate = (t) => {
      if (t <= keys[0][0]) return keys[0][1];
      for (let i = 0; i < keys.length - 1; i++) {
        const [ta, ra] = keys[i], [tb, rb] = keys[i + 1];
        if (t <= tb) return lerp(ra, rb, smooth(clamp01((t - ta) / (tb - ta))));
      }
      return keys[keys.length - 1][1];
    };
    const n = Math.ceil(t1 / step) + 2, P = [0];
    for (let i = 1; i < n; i++) P.push(P[i - 1] + rate((i - 0.5) * step) * step / g.period);
    const phase = (t) => { const x = Math.max(0, t) / step, i = Math.min(n - 2, Math.floor(x)); return P[i] + (P[i + 1] - P[i]) * (x - i); };
    phase.rate = rate;
    /* times at which the near (0) or far (0.5) foot strikes, between ta and tb: for footstep sounds */
    phase.strikes = (ta, tb) => {
      const out = [];
      for (let i = 1; i < n; i++) {
        const t = i * step;
        if (t < ta || t > tb) continue;
        for (const off of [0, 0.5]) if (Math.floor(P[i - 1] + off) !== Math.floor(P[i] + off)) out.push({ t: +t.toFixed(3), foot: off ? 1 : 0 });
      }
      return out;
    };
    return phase;
  };

  if (!K) return;   // the rest draws SVG and needs kit.js and a document

  // ------------------------------------------------------------------ drawing
  KH.LOOK = {
    skin: "#c98a62", skinShade: "#a96a48", skinHi: "#dba37c",
    hair: "#3a2420", hairHi: "#563630",
    shirt: "#1f7a80", shirtShade: "#165e63", shirtHi: "#2f9aa0",
    pants: "#2b3a67", pantsShade: "#1f2b4f", pantsHi: "#3a4c80",
    shoe: "#f1eee6", shoeShade: "#c9c3b6", sole: "#8f877a",
    eye: "#1c1233", far: 0.78,          // far limbs are drawn this much darker (multiplied)
    hairStyle: "short",                 // "short" or "long"
  };
  const shade = (hex, k) => {
    const n = parseInt(hex.slice(1), 16), r = (n >> 16) & 255, g2 = (n >> 8) & 255, b = n & 255;
    return "#" + [r, g2, b].map((v) => Math.round(v * k).toString(16).padStart(2, "0")).join("");
  };
  /* tapered capsule between two points (two circles joined by their outer tangents) */
  KH.taper = (p0, r0, p1, r1) => {
    const dx = p1[0] - p0[0], dy = p1[1] - p0[1], d = Math.hypot(dx, dy) || 1e-6;
    const ang = Math.atan2(dy, dx), off = Math.asin(Math.max(-1, Math.min(1, (r0 - r1) / d)));
    const a1 = ang + Math.PI / 2 + off, a2 = ang - Math.PI / 2 - off;
    const P = (c, r, a) => [c[0] + r * Math.cos(a), c[1] + r * Math.sin(a)];
    const s0 = P(p0, r0, a1), e0 = P(p1, r1, a1), e1 = P(p1, r1, a2), s1 = P(p0, r0, a2);
    return `M ${f(s0[0])} ${f(s0[1])} L ${f(e0[0])} ${f(e0[1])} A ${f(r1)} ${f(r1)} 0 0 0 ${f(e1[0])} ${f(e1[1])} L ${f(s1[0])} ${f(s1[1])} A ${f(r0)} ${f(r0)} 0 0 0 ${f(s0[0])} ${f(s0[1])} Z`;
  };
  const toSvg = (p) => [p[0], -p[1]];   // rig maths is y-up; SVG is y-down

  /* Draws a person standing on y = 0 of `parent` (local units: px), facing +x. o.look overrides KH.LOOK. */
  KH.human = (parent, o = {}) => {
    const L = Object.assign({}, KH.LOOK, o.look || {}), dim = Object.assign({}, KH.DIM, o.dim || {});
    const g = K.g(parent);
    const mk = (fill, par = g) => K.el("path", { fill }, par);
    const far = (c) => shade(c, L.far);
    // far side first
    const farArm = { up: mk(far(L.shirt)), fore: mk(far(L.skin)), hand: K.el("circle", { r: dim.handR, fill: far(L.skin) }, g) };
    const farLeg = { thigh: mk(far(L.pants)), shin: mk(far(L.pants)), shoe: K.g(g) };
    K.el("path", { fill: far(L.shoe) }, farLeg.shoe); K.el("path", { fill: far(L.sole) }, farLeg.shoe);
    const nearLeg = { thigh: mk(L.pants), shin: mk(L.pants), shoe: K.g(g), hi: mk(L.pantsHi) };
    K.el("path", { fill: L.shoe }, nearLeg.shoe); K.el("path", { fill: L.sole }, nearLeg.shoe);
    const pelvisBlock = mk(L.pants);                     // the seat of the trousers: hides the hip joints
    const torso = { base: mk(L.shirt), shade: mk(L.shirtShade), hi: mk(L.shirtHi), hem: mk(L.shirtShade) };
    const neck = mk(L.skinShade);
    const head = K.g(g);
    const R0 = dim.headR;
    if (L.hairStyle === "long")                          // the hair that falls behind the face, inside the head group
      K.el("path", { fill: L.hair, d: `M ${f(-R0 * 0.2)} ${f(-R0 * 0.95)} C ${f(-R0 * 1.25)} ${f(-R0 * 0.9)} ${f(-R0 * 1.3)} ${f(R0 * 0.6)} ${f(-R0 * 0.95)} ${f(R0 * 1.55)} C ${f(-R0 * 0.6)} ${f(R0 * 1.75)} ${f(-R0 * 0.1)} ${f(R0 * 1.6)} ${f(R0 * 0.05)} ${f(R0 * 1.2)} C ${f(-R0 * 0.3)} ${f(R0 * 0.5)} ${f(-R0 * 0.1)} ${f(-R0 * 0.2)} ${f(R0 * 0.3)} ${f(-R0 * 0.6)} Z` }, head);
    const headParts = {
      face: K.el("ellipse", { rx: f(dim.headR * 0.92), ry: f(dim.headR), fill: L.skin }, head),
      jaw: K.el("path", { fill: L.skinShade, opacity: 0.35 }, head),
      ear: K.el("ellipse", { cx: f(-dim.headR * 0.12), cy: f(dim.headR * 0.08), rx: f(dim.headR * 0.16), ry: f(dim.headR * 0.22), fill: L.skinShade }, head),
      hair: K.el("path", { fill: L.hair }, head),
      hairHi: K.el("path", { fill: "none", stroke: L.hairHi, "stroke-width": f(dim.headR * 0.09), "stroke-linecap": "round" }, head),
      brow: K.el("path", { fill: "none", stroke: L.hair, "stroke-width": f(dim.headR * 0.08), "stroke-linecap": "round" }, head),
      eye: K.el("ellipse", { rx: f(dim.headR * 0.075), ry: f(dim.headR * 0.1), fill: L.eye }, head),
      nose: K.el("path", { fill: L.skinShade }, head),
      mouth: K.el("path", { fill: "none", stroke: L.skinShade, "stroke-width": f(dim.headR * 0.06), "stroke-linecap": "round" }, head),
      cheek: K.el("ellipse", { rx: f(dim.headR * 0.14), ry: f(dim.headR * 0.09), fill: "#e98f8a", opacity: 0.35 }, head),
    };
    const nearArm = { up: mk(L.shirt), fore: mk(L.skin), hand: K.el("circle", { r: dim.handR, fill: L.skin }, g), sleeveHi: mk(L.shirtHi) };
    // static head drawing (in head-local coordinates, centre of the head at 0,0, facing +x)
    const R = dim.headR;
    headParts.jaw.setAttribute("d", `M ${f(-R * 0.6)} ${f(R * 0.55)} Q ${f(0)} ${f(R * 1.08)} ${f(R * 0.72)} ${f(R * 0.5)} L ${f(R * 0.5)} ${f(R * 0.3)} Q ${f(0)} ${f(R * 0.8)} ${f(-R * 0.5)} ${f(R * 0.35)} Z`);
    if (L.hairStyle === "long") {
      headParts.hair.setAttribute("d", `M ${f(-R * 1.0)} ${f(R * 0.2)} C ${f(-R * 1.15)} ${f(-R * 1.0)} ${f(R * 0.2)} ${f(-R * 1.35)} ${f(R * 0.86)} ${f(-R * 0.46)} C ${f(R * 0.6)} ${f(-R * 0.62)} ${f(R * 0.2)} ${f(-R * 0.6)} ${f(-R * 0.05)} ${f(-R * 0.4)} C ${f(-R * 0.25)} ${f(-R * 0.1)} ${f(-R * 0.5)} ${f(R * 0.05)} ${f(-R * 1.0)} ${f(R * 0.2)} Z`);
    } else {
      headParts.hair.setAttribute("d", `M ${f(-R * 0.95)} ${f(R * 0.12)} C ${f(-R * 1.08)} ${f(-R * 0.95)} ${f(R * 0.35)} ${f(-R * 1.32)} ${f(R * 0.9)} ${f(-R * 0.42)} C ${f(R * 0.62)} ${f(-R * 0.58)} ${f(R * 0.28)} ${f(-R * 0.62)} ${f(R * 0.02)} ${f(-R * 0.48)} C ${f(-R * 0.12)} ${f(-R * 0.26)} ${f(-R * 0.4)} ${f(-R * 0.2)} ${f(-R * 0.5)} ${f(R * 0.18)} Z`);
    }
    headParts.hairHi.setAttribute("d", `M ${f(-R * 0.55)} ${f(-R * 0.72)} Q ${f(-R * 0.1)} ${f(-R * 0.98)} ${f(R * 0.38)} ${f(-R * 0.82)}`);
    headParts.brow.setAttribute("d", `M ${f(R * 0.38)} ${f(-R * 0.28)} Q ${f(R * 0.52)} ${f(-R * 0.36)} ${f(R * 0.66)} ${f(-R * 0.3)}`);
    headParts.eye.setAttribute("cx", f(R * 0.55)); headParts.eye.setAttribute("cy", f(-R * 0.1));
    headParts.nose.setAttribute("d", `M ${f(R * 0.84)} ${f(-R * 0.02)} Q ${f(R * 1.06)} ${f(R * 0.14)} ${f(R * 0.86)} ${f(R * 0.24)} Z`);
    headParts.mouth.setAttribute("d", `M ${f(R * 0.52)} ${f(R * 0.48)} Q ${f(R * 0.64)} ${f(R * 0.56)} ${f(R * 0.76)} ${f(R * 0.46)}`);
    headParts.cheek.setAttribute("cx", f(R * 0.42)); headParts.cheek.setAttribute("cy", f(R * 0.26));

    const shoePath = (len0, len1, h) => `M ${f(-len0)} ${f(-h * 0.2)} Q ${f(-len0 - 4)} ${f(-h)} ${f(-len0 * 0.2)} ${f(-h * 1.05)} L ${f(len1 * 0.45)} ${f(-h * 0.85)} Q ${f(len1 + 8)} ${f(-h * 0.7)} ${f(len1)} ${f(0)} L ${f(-len0)} ${f(0)} Z`;
    const solePath = (len0, len1) => `M ${f(-len0)} ${f(-5)} L ${f(len1 + 2)} ${f(-5)} Q ${f(len1 + 4)} ${f(0)} ${f(len1)} ${f(2)} L ${f(-len0)} ${f(2)} Z`;

    const api = { g, dim, look: L, pose: null, wave: 0 };
    api.setPose = (P) => {
      api.pose = P;
      const sv = toSvg;
      const legDraw = (leg, parts, near) => {
        const hip = sv(leg.hip), knee = sv(leg.knee), ank = sv(leg.ankle);
        parts.thigh.setAttribute("d", KH.taper(hip, dim.hipW, knee, dim.kneeW));
        parts.shin.setAttribute("d", KH.taper(knee, dim.kneeW, ank, dim.ankleW));
        if (near && parts.hi) parts.hi.setAttribute("d", KH.taper([hip[0] + 12, hip[1] + 18], 6, [knee[0] + 10, knee[1] - 6], 4));
        // the shoe: sole point under the ankle at (0,0) of the shoe group, rotated by the foot angle
        const deg = -leg.foot / D2R;
        parts.shoe.setAttribute("transform", `translate(${f(ank[0])},${f(ank[1] + dim.ankleH)}) rotate(${f(deg)} 0 ${f(-dim.ankleH)})`);
        parts.shoe.children[0].setAttribute("d", shoePath(dim.heel + 6, dim.toe, 34));
        parts.shoe.children[1].setAttribute("d", solePath(dim.heel + 6, dim.toe));
      };
      legDraw(P.legs[1], farLeg, false);
      legDraw(P.legs[0], nearLeg, true);
      // torso: a rounded trapezoid from pelvis to shoulders, leaning with the pose
      const pel = sv(P.pelvis), sh = sv(P.shoulder), up = [sh[0] - pel[0], sh[1] - pel[1]], len = Math.hypot(up[0], up[1]);
      const ux = up[0] / len, uy = up[1] / len, px = -uy, py = ux;          // px,py: perpendicular, toward the front
      const pt = (along, side) => [pel[0] + ux * along + px * side, pel[1] + uy * along + py * side];
      pelvisBlock.setAttribute("d", K.smooth([pt(-34, 40), pt(-30, -44), pt(10, -54), pt(36, -50), pt(36, 50), pt(10, 54)], true));
      const T2 = [pt(16, 56), pt(len * 0.55, 60), pt(len + 6, 56), pt(len + 18, 20), pt(len + 18, -24), pt(len + 4, -60), pt(len * 0.5, -58), pt(16, -56)];
      torso.base.setAttribute("d", K.smooth(T2, true));
      torso.shade.setAttribute("d", K.smooth([pt(20, -40), pt(len * 0.5, -44), pt(len + 4, -46), pt(len + 4, -60), pt(len * 0.5, -58), pt(18, -56)], true));
      torso.hi.setAttribute("d", K.smooth([pt(len * 0.35, 44), pt(len * 0.75, 50), pt(len * 0.9, 40), pt(len * 0.6, 34)], true));
      torso.hem.setAttribute("d", K.smooth([pt(14, 57), pt(26, 58), pt(26, -57), pt(14, -56)], true));
      const nk = sv(P.neck);
      neck.setAttribute("d", KH.taper([sh[0], sh[1] + 6], 20, nk, 17));
      const hd = sv(P.head);
      head.setAttribute("transform", `translate(${f(hd[0])},${f(hd[1])}) rotate(${f(-P.headTilt / D2R)})`);
      const armDraw = (arm, parts, near) => {
        const s = sv(arm.shoulder), e = sv(arm.elbow), w = sv(arm.wrist);
        const mid = [s[0] + (e[0] - s[0]) * 0.55, s[1] + (e[1] - s[1]) * 0.55];
        parts.up.setAttribute("d", KH.taper(s, dim.upperArmW + 4, mid, dim.upperArmW + 2));          // short sleeve
        parts.fore.setAttribute("d", KH.taper(mid, dim.upperArmW - 2, e, dim.foreArmW + 1) + " " + KH.taper(e, dim.foreArmW + 1, w, dim.foreArmW - 3));
        const dirx = w[0] - e[0], diry = w[1] - e[1], dl = Math.hypot(dirx, diry) || 1;
        parts.hand.setAttribute("cx", f(w[0] + (dirx / dl) * dim.handR * 0.7)); parts.hand.setAttribute("cy", f(w[1] + (diry / dl) * dim.handR * 0.7));
        if (near && parts.sleeveHi) parts.sleeveHi.setAttribute("d", KH.taper([s[0] + 8, s[1] + 4], 5, [mid[0] + 6, mid[1] - 2], 4));
      };
      armDraw(P.arms[1], farArm, false);
      armDraw(P.arms[0], nearArm, true);
    };
    api.setPose(o.pose || KH.standPose(dim));
    return api;
  };

  /* A walker: a human plus its walk. api.at(phase) poses it; api.x(phase) is its world x (feet stay planted). */
  KH.walker = (parent, o = {}) => {
    const g = K.g(parent), body = K.g(g), h = KH.human(body, o), gait = Object.assign({}, KH.GAIT, o.gait || {});
    const step = gait.stride / gait.stance;            // world px travelled per cycle
    const api = { g, h, gait, phase: 0 };
    api.x = (p) => (o.x0 || 0) + step * p;
    api.at = (p) => {
      api.phase = p;
      h.setPose(KH.walkPose(p, gait, h.dim));
      g.setAttribute("transform", `translate(${f(api.x(p))},${f(o.y0 || 0)})`);
      return api;
    };
    /* a point on the near thigh in world units (u = 0 at the hip, 1 at the knee), for cameras and lenses */
    api.thighPoint = (u = 0.45) => {
      const P = h.pose, a = P.legs[0].hip, b = P.legs[0].knee;
      return [api.x(api.phase) + lerp(a[0], b[0], u), (o.y0 || 0) - lerp(a[1], b[1], u)];
    };
    api.at(0);
    return api;
  };
})();
if (typeof module !== "undefined") module.exports = globalThis.HUMAN || (typeof window !== "undefined" ? window.HUMAN : undefined);
