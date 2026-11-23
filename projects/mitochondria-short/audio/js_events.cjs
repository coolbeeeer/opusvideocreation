/* Footstep times for the sound effects, computed with the same walk rig and speed keys as the picture.
   Run: node audio/js_events.cjs  ->  writes assets/steps.json { walk: [...], finale: [...] }, film times in seconds.
   The keys below must match compositions/walk.html and compositions/finale.html (search for "phaseTable"). */
const fs = require("fs");
const path = require("path");
const KH = require(path.join(__dirname, "..", "..", "..", "lib", "kit-human.js"));
const T = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "assets", "timing.json"), "utf8"));

const key = (w) => w.toLowerCase().replace(/[^a-z0-9]/g, "");
const wordAt = (word, n, after) => {            // same rule as KIT.t: n-th occurrence at or after `after`
  let k = 0;
  for (const [wk, t] of T.words) if (t >= after && wk === key(word) && ++k === n) return t;
  throw new Error("word not in narration: " + word);
};
const scene = (id) => {
  const S = T.scenes[id];
  return { T0: S.start, DUR: S.dur, at: (w, n = 1) => wordAt(w, n, S.start) - S.start };
};
const out = {};

// walk.html: normal pace, then almost frozen for the dive
{
  const { T0, DUR, at } = scene("walk"), tDive = at("dive");
  const phase = KH.phaseTable([[0, 1], [tDive - 0.3, 1], [tDive + 0.6, 0.1], [DUR, 0.08]], DUR + 1);
  out.walk = phase.strikes(0, DUR).map((s) => ({ t: +(T0 + s.t).toFixed(3), foot: s.foot, rate: +phase.rate(s.t).toFixed(3) }));
  out.walkDive = +(T0 + tDive).toFixed(3);
}
// finale.html: barely moving while inside the leg, back to full pace once the person is in view
{
  const { T0, DUR, at } = scene("finale"), tOut = at("take") + 0.05;
  const phase = KH.phaseTable([[0, 0.08], [tOut - 0.8, 0.12], [tOut + 0.2, 1], [DUR, 1]], DUR + 1);
  out.finale = phase.strikes(0, DUR).map((s) => ({ t: +(T0 + s.t).toFixed(3), foot: s.foot, rate: +phase.rate(s.t).toFixed(3) }));
  out.finaleOut = +(T0 + tOut).toFixed(3);
}
out.period = KH.GAIT.period;
fs.writeFileSync(path.join(__dirname, "..", "assets", "steps.json"), JSON.stringify(out, null, 1));
console.log(`walk: ${out.walk.length} strikes (${out.walk.map((s) => s.t).join(", ")})`);
console.log(`finale: ${out.finale.length} strikes (${out.finale.map((s) => s.t).join(", ")})`);
