/* Draws docs/walk-cycle.svg from lib/kit-human.js: the key poses of one walk cycle, a strobe of two cycles placed at
   their real world positions (the footprints show that a planted foot does not slide), and curves of the near foot's
   world position and height and of the pelvis bob. Pure maths, no browser.
   Run from the repo root: node tools/walk_cycle_svg.cjs */
const fs = require("fs");
const path = require("path");
const KH = require(path.join(__dirname, "..", "lib", "kit-human.js"));

const G = KH.GAIT, D = KH.DIM, STEP = G.stride / G.stance;               // world px per cycle
const f = (n) => (Math.round(n * 10) / 10).toString();
const rot = (v, a) => [v[0] * Math.cos(a) - v[1] * Math.sin(a), v[0] * Math.sin(a) + v[1] * Math.cos(a)];
const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
const out = [];
const W = 1600, H = 1400;
out.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" font-family="Nunito, Helvetica, Arial, sans-serif">`);
out.push(`<rect width="${W}" height="${H}" fill="#f7f3ea"/>`);
const text = (x, y, s, size = 22, anchor = "middle", fill = "#1d2b3a", weight = 700) =>
  out.push(`<text x="${f(x)}" y="${f(y)}" font-size="${size}" font-weight="${weight}" text-anchor="${anchor}" fill="${fill}">${s}</text>`);

/* one figure as bones: (ox, oy) is the ground point under the pelvis, s the scale; body frame is y-up */
function figure(P, ox, oy, s, alpha = 1) {
  const X = (p) => [ox + p[0] * s, oy - p[1] * s];
  const line = (a, b, w, c) => { const A = X(a), B = X(b); out.push(`<line x1="${f(A[0])}" y1="${f(A[1])}" x2="${f(B[0])}" y2="${f(B[1])}" stroke="${c}" stroke-width="${f(w * s)}" stroke-linecap="round" opacity="${alpha}"/>`); };
  const sole = (leg) => [add(leg.ankle, rot([-D.heel, -D.ankleH], leg.foot)), add(leg.ankle, rot([D.toe, -D.ankleH], leg.foot))];
  const limbs = (i, legC, armC) => {
    const L = P.legs[i], A = P.arms[i];
    if (i === 1) { line(A.shoulder, A.elbow, 34, armC); line(A.elbow, A.wrist, 28, armC); }
    line(L.hip, L.knee, 52, legC); line(L.knee, L.ankle, 40, legC);
    const [heel, toe] = sole(L);
    line(heel, toe, 22, legC);
  };
  limbs(1, "#9aa7c7", "#9ccfd2");                                          // far side (lighter)
  limbs(0, "#2b3a67", "#1f7a80");                                          // near leg
  line(P.pelvis, P.shoulder, 96, "#1f7a80");                               // torso
  const hd = X(P.head);
  out.push(`<circle cx="${f(hd[0])}" cy="${f(hd[1])}" r="${f(D.headR * s)}" fill="#c98a62" opacity="${alpha}"/>`);
  const A = P.arms[0];
  line(A.shoulder, A.elbow, 34, "#2f9aa0"); line(A.elbow, A.wrist, 28, "#c98a62");
  for (const j of [P.legs[0].hip, P.legs[0].knee, P.legs[0].ankle, A.elbow])
    { const J = X(j); out.push(`<circle cx="${f(J[0])}" cy="${f(J[1])}" r="${f(Math.max(3, 9 * s))}" fill="#ffb24d" opacity="${alpha}"/>`); }
}

// ---------------------------------------------------------------- A: key poses of one cycle
text(40, 50, "KH.walkPose(phase): one cycle = 1.15 s = two steps. Near leg dark, far leg light, joints orange.", 28, "start");
text(40, 84, `Each foot is planted for ${G.stance * 100} % of the cycle; knees come from two-bone IK; the pelvis bobs ${G.bob} px twice per cycle.`, 22, "start", "#4a5568", 600);
const names = ["heel strike", "loading", "mid-stance", "heel rising", "toe-off", "swing", "mid-swing", "reaching"];
const phases = [0, 0.12, 0.31, 0.45, 0.62, 0.72, 0.82, 0.93];
phases.forEach((ph, k) => {
  const ox = 120 + k * 195, oy = 520, s = 0.56;
  out.push(`<line x1="${ox - 90}" y1="${oy}" x2="${ox + 90}" y2="${oy}" stroke="#b9ad96" stroke-width="3"/>`);
  figure(KH.walkPose(ph), ox, oy, s);
  text(ox, oy + 36, names[k], 21);
  text(ox, oy + 62, `phase ${ph.toFixed(2)}`, 18, "middle", "#6b7280", 600);
});

// ---------------------------------------------------------------- B: strobe of the legs at true world positions
const sB = 0.8, oyB = 990, x0B = 330;
text(40, 632, "Strobe: the legs every 1/8 cycle for two cycles, drawn where the walker really is (x = x0 + phase x 451.6 px).", 22, "start");
text(40, 660, "Nothing is stretched: where a foot is planted, its copies land on top of each other and print a solid footprint.", 20, "start", "#4a5568", 600);
out.push(`<line x1="40" y1="${oyB}" x2="${W - 40}" y2="${oyB}" stroke="#b9ad96" stroke-width="3"/>`);
let hipPath = "";
for (let k = 0; k <= 16; k++) {
  const ph = k / 8, P = KH.walkPose(ph), ox = x0B + ph * STEP * sB;
  const X = (p) => [ox + p[0] * sB, oyB - p[1] * sB];
  const seg = (a, b, w, c, op) => { const A = X(a), B = X(b); out.push(`<line x1="${f(A[0])}" y1="${f(A[1])}" x2="${f(B[0])}" y2="${f(B[1])}" stroke="${c}" stroke-width="${f(w)}" stroke-linecap="round" opacity="${op}"/>`); };
  [[1, "#9aa7c7"], [0, "#2b3a67"]].forEach(([i, c]) => {
    const L = P.legs[i];
    seg(L.hip, L.knee, 8, c, 0.35); seg(L.knee, L.ankle, 7, c, 0.35);
    seg(add(L.ankle, rot([-D.heel, -D.ankleH], L.foot)), add(L.ankle, rot([D.toe, -D.ankleH], L.foot)), 9, c, 0.35);
  });
  const hp = X(P.pelvis);
  hipPath += (k ? " L " : "M ") + f(hp[0]) + " " + f(hp[1]);
  out.push(`<circle cx="${f(hp[0])}" cy="${f(hp[1])}" r="5" fill="#1f7a80"/>`);
}
out.push(`<path d="${hipPath}" fill="none" stroke="#1f7a80" stroke-width="2" stroke-dasharray="6 5"/>`);
text(x0B + 2 * STEP * sB + 70, oyB - 262, "pelvis path (dashed)", 18, "start", "#1f7a80", 700);

// ---------------------------------------------------------------- C: curves over two cycles
const gx0 = 110, gx1 = W - 60, gyTop = 1070, gyH = 200;
const T = (ph) => gx0 + (ph / 2) * (gx1 - gx0);
out.push(`<rect x="${gx0}" y="${gyTop}" width="${gx1 - gx0}" height="${gyH}" fill="#ffffff" stroke="#d6cdb8"/>`);
for (let c = 0; c <= 2; c++) { out.push(`<line x1="${f(T(c))}" y1="${gyTop}" x2="${f(T(c))}" y2="${gyTop + gyH}" stroke="#d6cdb8"/>`); text(T(c), gyTop + gyH + 24, `${c} cycle${c === 1 ? "" : "s"}`, 16, "middle", "#6b7280", 600); }
for (let c = 0; c < 2; c++) out.push(`<rect x="${f(T(c))}" y="${gyTop}" width="${f(T(c + G.stance) - T(c))}" height="${gyH}" fill="#2b3a67" opacity="0.06"/>`);
const curve = (fn, lo, hi, col, label, lx, ly) => {
  let d = "";
  for (let i = 0; i <= 400; i++) {
    const ph = (i / 400) * 2, v = fn(ph), y = gyTop + gyH - ((v - lo) / (hi - lo)) * gyH;
    d += (i ? " L " : "M ") + f(T(ph)) + " " + f(y);
  }
  out.push(`<path d="${d}" fill="none" stroke="${col}" stroke-width="3"/>`);
  out.push(`<line x1="${lx}" y1="${ly - 6}" x2="${lx + 34}" y2="${ly - 6}" stroke="${col}" stroke-width="4"/>`);
  text(lx + 44, ly, label, 18, "start", col, 700);
};
curve((ph) => ph * STEP + KH.walkPose(ph).legs[0].ankle[0], -150, 2 * STEP + 200, "#2b3a67", "near ankle, world x: holds while the foot is down", gx0, gyTop + gyH + 62);
curve((ph) => KH.walkPose(ph).legs[0].ankle[1], 0, 140, "#d9700f", "near ankle height: heel and toe rolls, 44 px lift", gx0 + 520, gyTop + gyH + 62);
curve((ph) => KH.walkPose(ph).pelvis[1], 300, 360, "#1f7a80", "pelvis height: 20 px bob, highest at mid-stance", gx0 + 1020, gyTop + gyH + 62);
text(40, gyTop - 14, "Shaded: near foot planted (62 % of each cycle).", 18, "start", "#4a5568", 600);
out.push("</svg>");
const file = path.join(__dirname, "..", "docs", "walk-cycle.svg");
fs.writeFileSync(file, out.join("\n"));
console.log("wrote", file);
