// Replays the resistance scene's seeded placement so sound pops land on the visual pops.
global.window = {};
require("../assets/kit.js");
const K = window.KIT;
const rnd = K.rng(707);
for (let i = 0; i < 70; i++) { rnd(); rnd(); rnd(); rnd(); }
const RES = [[520, 430], [1180, 330], [880, 760], [1480, 700]];
const NORM = [];
for (let i = 0; i < 34; i++) {
  let x, y, ok = false, tries = 0;
  while (!ok && tries++ < 60) {
    x = 150 + rnd() * 1620; y = 150 + rnd() * 780;
    ok = RES.every((r) => Math.hypot(r[0] - x, r[1] - y) > 170) && NORM.every((n) => Math.hypot(n.x - x, n.y - y) > 120);
  }
  rnd();
  NORM.push({ x: Math.round(x), y: Math.round(y) });
}
require("fs").writeFileSync(__dirname + "/res_norm.json", JSON.stringify(NORM));
console.log(NORM.length, "positions", JSON.stringify(NORM.slice(0, 3)));
