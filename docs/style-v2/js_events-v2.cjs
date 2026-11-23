// Replays the resistance scene's seeded placement so sound pops land on the visual pops.
// Style v2: placement uses its own PRNG (K.rng(708)) and skips cells that found no free spot,
// exactly as compositions/resistance.html does.
global.window = {};
require("../assets/kit.js");
const K = window.KIT;
const rpos = K.rng(708);
const RES = [[520, 430], [1180, 330], [880, 700], [1480, 700]];
const NORM = [];
for (let i = 0; i < 30; i++) {
  let x, y, ok = false, tries = 0;
  while (!ok && tries++ < 80) {
    x = 160 + rpos() * 1600; y = 150 + rpos() * 780;
    ok = RES.every((r) => Math.hypot(r[0] - x, r[1] - y) > 230) && NORM.every((n) => Math.hypot(n.x - x, n.y - y) > 195);
  }
  if (!ok) continue;
  rpos(); // rotation
  NORM.push({ x: Math.round(x), y: Math.round(y) });
}
require("fs").writeFileSync(__dirname + "/res_norm.json", JSON.stringify(NORM));
console.log(NORM.length, "positions", JSON.stringify(NORM.slice(0, 3)));
