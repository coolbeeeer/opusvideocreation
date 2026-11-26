# Planned events of ocean-glow-short

Every picture event in plan.json, its film time, and what stage 3 measured. 'Score' is the change in the event's box at its time divided by the box's usual change between events (shown needs 2.5 or more); 'lag' is the strongest change minus the planned time; 'cue at' is when its sound starts.

| Scene | # | Time | Word | Kind | Who | Does / text | Shown | Score | Lag | Cue | Cue at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hook | 1 | 0.00 |  | camera |  | auto: K.camTo(tl, S.cam, 0, { s: 1.06, py: 900 }, tUp, "sine.inOut"); | yes | 3.17 | 0.27 |  |  |
| hook | 2 | 0.52 | three | move |  | auto: drives frame() code | yes | 3.41 | 0.48 | glow_on | 0.97 |
| hook | 4 | 1.18 | animals | move |  | auto: drives frame() code | yes | 3.33 | -0.18 |  |  |
| hook | 5 | 1.87 | open | move |  | auto: drives frame() code | **no** | 0.93 | 0.13 |  |  |
| hook | 6 | 2.30 | ocean | move |  | auto: drives frame() code | **no** | 0.9 | 0.5 |  |  |
| hook | 7 | 3.14 | own | move |  | auto: drives frame() code | **no** | 0.81 | 0.06 |  |  |
| hook | 8 | 4.38 | why | move |  | auto: tl.fromTo(q, { opacity: 0, scale: 0.3, rotation: -20 }, { opacity: 1,  | **no** | 1.52 | 0.49 | boing | 4.38 |
| descent | 1 | 5.05 |  | transition |  | cut to the next scene | yes | 31.13 | 0.02 |  |  |
| descent | 2 | 5.84 | dive | move |  | auto: tl.to([gauge.el, gauge.chip, ...gauge.marks], { opacity: 1, duration:  | yes | 3.04 | 0.16 | cue | 5.76 |
| descent | 3 | 8.15 | by | move |  | auto: drives frame() code | **no** | 1.1 | -0.02 |  |  |
| descent | 5 | 10.21 | below | move |  | auto: drives frame() code | **no** | 2.18 | 0.19 |  |  |
| descent | 7 | 12.14 | forever | move |  | auto: drives frame() code | **no** | 0.58 | -0.27 |  |  |
| chemistry | 1 | 12.87 |  | transition |  | cut to the next scene | yes | 6.71 | 0.06 |  |  |
| chemistry | 2 | 12.87 |  | camera |  | auto: K.camTo(tl, A.cam, 0, { s: 1.05, py: 930 }, tCut - 0.65, "sine.inOut") | yes | 6.71 | 0.06 |  |  |
| chemistry | 3 | 13.45 | so | move |  | auto: tl.to(st, { k: 1.2, duration: 0.3, ease: "power2.out", onUpdate: () => | **no** | 1.01 | 0.08 | cue | 13.48 |
| chemistry | 4 | 14.39 | by | camera |  | auto: K.camTo(tl, A.cam, tCut - 0.65, { px: PX, py: PY, s: 9 }, 0.65, "power | yes | 11.25 | 0.48 | cue |  |
| chemistry | 5 | 14.90 | by | move |  | auto: tl.fromTo(flash, { opacity: 0 }, { opacity: 1, duration: 0.14, ease: " | yes | 42.49 | 0.23 | cue | 15.0 |
| chemistry | 7 | 16.33 | with | move |  | auto: tl.to(fw, { x: 600, y: 815, duration: tMeet - at("with") - 0.05, ease: | yes | 2.95 | 0.4 |  |  |
| chemistry | 9 | 16.80 | enzyme | move |  | auto: tl.to(mo, { v: 0.05, duration: 0.1, ease: "power3.in", onUpdate: () => | yes | 31.44 | 0.13 | pop_word | 16.8 |
| chemistry | 11 | 17.25 | enzyme | move |  | auto: tl.to(s, { opacity: 0, duration: 0.25 }, tMeet + 0.45); | yes | 31.98 | 0.28 | pop_word | 17.31 |
| angler | 1 | 17.47 |  | transition |  | cut to the next scene | yes | 31.98 | 0.06 |  |  |
| angler | 2 | 17.62 |  | camera |  | auto: K.camTo(tl, S.cam, 0.15, { px: 560, py: 900, s: 1.0 }, at("dangles") + | yes | 32.73 | -0.09 |  |  |
| angler | 4 | 19.19 | dangles | camera |  | auto: K.camTo(tl, S.cam, at("dangles") + 0.65, { px: 600, py: 880, s: 1.06 } | yes | 1.66 | 0.0 |  |  |
| angler | 6 | 20.30 | curious | move |  | auto: tl.to(pw, { x: PX, duration: tStop - tIn, ease: "power2.out" }, tIn); | **no** | 1.37 | 0.37 | cue | 20.5 |
| angler | 7 | 20.88 | swims | move |  | auto: drives frame() code | **no** | 1.56 | -0.21 |  |  |
| angler | 8 | 21.26 | closer | move |  | auto: tl.fromTo(heart, { opacity: 0, scale: 0.3, svgOrigin: "0 0", x: PX + 1 | **no** | 1.39 | -0.19 | bubble | 21.28 |
| angler | 9 | 22.19 | bad | move |  | auto: tl.to(aw, { x: AX - 24, y: AY + 12, duration: 0.18, ease: "power2.out" | yes | 17.67 | 0.28 | cue | 22.44 |
| angler | 10 | 22.49 | bad | move |  | auto: tl.to(j, { v: 0, duration: 0.08, ease: "power3.in", onUpdate: upd }, t | yes | 19.45 | -0.02 | cue | 22.74 |
| angler | 11 | 22.84 | bad | move |  | auto: tl.fromTo(burp, { opacity: 0, attr: { cx: LUNGE[0] + 0.9 * AR, cy: LUN | yes | 112.5 | 0.49 | cue | 22.74 |
| hatchet | 1 | 23.29 |  | transition |  | cut to the next scene | yes | 117.58 | 0.04 |  |  |
| hatchet | 2 | 23.29 |  | camera |  | auto: K.camTo(tl, S.cam, 0, { s: 1.38, py: HY + 60 }, at("seen") - 0.35, "si | yes | 117.58 | 0.04 |  |  |
| hatchet | 4 | 24.43 | lights | move |  | auto: tl.to(lights, { k: 1.1, duration: 0.45, ease: "power2.out", onUpdate:  | **no** | 1.73 | -0.23 | glow_on | 24.74 |
| hatchet | 5 | 25.76 | match | move |  | auto: drives frame() code | **no** | 1.84 | 0.37 |  |  |
| hatchet | 6 | 26.20 | glow | move |  | auto: drives frame() code | **no** | 1.82 | -0.07 | descend_ting | 26.2 |
| hatchet | 7 | 27.15 | above | move |  | auto: drives frame() code | **no** | 1.27 | 0.25 |  |  |
| hatchet | 8 | 27.64 | seen | camera |  | auto: K.camTo(tl, S.cam, tS, { px: 540, py: 960, s: 1.0 }, 0.85, "power2.inO | yes | 32.21 | 0.43 | cue | 28.06 |
| hatchet | 9 | 27.99 | seen | move |  | auto: tl.to(sil, { v: 1, duration: 0.3, ease: "power2.inOut", onUpdate: () = | yes | 31.67 | 0.08 | cue | 28.06 |
| hatchet | 10 | 28.34 | below | move |  | auto: tl.to(los, { opacity: 0.9, duration: 0.25 }, tB); | yes | 32.62 | -0.27 | cue | 28.58 |
| hatchet | 11 | 29.57 | vanishes | move |  | auto: tl.to(lights, { k: 1, duration: 0.35, ease: "power2.out", onUpdate: se | yes | 3.91 | 0.23 | cue | 29.77 |
| hatchet | 12 | 29.92 | vanishes | move |  | auto: tl.fromTo(q, { opacity: 0, scale: 0.3, rotation: -20 }, { opacity: 1,  | yes | 3.82 | -0.12 | cue | 29.92 |
| alarm | 1 | 30.55 |  | transition |  | cut to the next scene | yes | 291.97 | 0.05 |  |  |
| alarm | 2 | 30.65 |  | move |  | auto: tl.to(aw, { x: A1[0], y: A1[1], duration: tG - 0.15, ease: "power2.out | yes | 277.59 | -0.05 |  |  |
| alarm | 3 | 31.12 | grab | move |  | auto: tl.to(aw, { x: A1[0] + 22, duration: 0.08, ease: "power3.out" }, tG); | yes | 5.74 | -0.25 | cue | 31.12 |
| alarm | 5 | 32.97 | flash | effect |  | auto: tl.to(jst, { flash: 1.25, duration: 0.15, ease: "power2.out" }, tF); | yes | 30.73 | 0.5 | cue | 32.97 |
| alarm | 7 | 35.00 | likely | camera |  | auto: K.camTo(tl, S.cam, tL - 0.1, { s: 0.94, px: 600, py: 980 }, 1.1, "powe | yes | 13.43 | 0.4 | cue |  |
| alarm | 8 | 35.70 | something | move |  | auto: drives frame() code | yes | 8.51 | -0.3 | thump | 36.09 |
| alarm | 10 | 36.38 | eat | move |  | auto: tl.to(bw, { x: B1[0] + 50, duration: 0.2, ease: "power2.out" }, tE - 0 | yes | 5.09 | 0.49 | cue | 36.31 |
| alarm | 11 | 37.15 | attacker | move |  | auto: tl.set(aw, { opacity: 0 }, tA); | **no** | 2.0 | 0.05 | cue | 37.15 |
| colours | 1 | 37.86 |  | transition |  | cut to the next scene | yes | 9.12 | 0.01 |  |  |
| colours | 2 | 37.86 |  | move |  | auto: tl.to(schoolG, { x: -260, duration: at("because") + 0.3, ease: "none"  | yes | 9.12 | 0.01 |  |  |
| colours | 3 | 39.13 | blue | move |  | auto: tl.to(blueOn, { k: 1.35, duration: 0.15, ease: "power2.out" }, at("blu | yes | 7.91 | 0.07 | chime | 39.19 |
| colours | 4 | 39.67 | because | move |  | auto: tl.to(schoolG, { opacity: 0, duration: 0.35, ease: "power1.in" }, at(" | yes | 24.84 | 0.2 | cue | 39.79 |
| colours | 5 | 39.94 | because | move |  | auto: tl.to(r, { attr: { height: len }, duration: dur, ease: "none" }, tGo); | yes | 24.84 | -0.07 | cue | 40.34 |
| colours | 7 | 42.57 | but | move |  | auto: tl.to(beamG, { opacity: 0, duration: 0.35, ease: "power2.in" }, tBut); | yes | 8.02 | 0.36 | cue | 42.95 |
| colours | 9 | 43.34 | cheats | move |  | auto: drives frame() code | yes | 2.58 | 0.33 | cue | 43.56 |
| colours | 10 | 44.25 | with | move |  | auto: drives frame() code | **no** | 2.39 | 0.22 |  |  |
| colours | 11 | 45.10 | prey | move |  | auto: drives frame() code | **no** | 1.44 | 0.37 | cue | 45.43 |
| colours | 13 | 45.91 | see | move |  | auto: drives frame() code | yes | 5.7 | 0.36 |  |  |
| finale | 1 | 46.55 |  | transition |  | cut to the next scene | yes | 21.0 | 0.05 |  |  |
| finale | 2 | 46.60 |  | camera |  | auto: K.camTo(tl, S.cam, 0.05, { px: 540, py: 1000, s: 1.0 }, at("ocean") +  | yes | 21.0 | 0.0 |  |  |
| finale | 5 | 48.05 | most | move |  | auto: tl.fromTo(br, { opacity: 0.95, strokeDasharray: brLen, strokeDashoffse | yes | 15.45 | 0.02 | zip_ | 47.99 |
| finale | 6 | 48.93 | ocean | camera |  | auto: K.camTo(tl, S.cam, at("ocean") + 0.15, { py: 990, s: 1.03 }, DUR - at( | yes | 9.78 | -0.26 | cue |  |
| finale | 7 | 49.58 | so | move |  | auto: tl.to(br, { opacity: 0, duration: 0.3 }, at("so") - 0.2); | yes | 12.83 | 0.15 | cue | 49.98 |
