# Planned events of mitochondria-short

Every picture event in plan.json, its film time, and what stage 3 measured. 'Score' is the change in the event's box at its time divided by the box's usual change between events (shown needs 2.5 or more); 'lag' is the strongest change minus the planned time; 'cue at' is when its sound starts.

| Scene | # | Time | Word | Kind | Who | Does / text | Shown | Score | Lag | Cue | Cue at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| walk | 2 | 2.06 | bacteria | move |  | auto: tl.to(st, { insetIn: 1, duration: 0.3, ease: "back.out(2)" }, at("bact | **no** | 2.27 | 0.07 | cue | 2.34 |
| walk | 3 | 3.87 | former | move |  | auto: tl.to(st, { morph: 1, duration: 0.35, ease: "power2.inOut" }, at("form | **no** | 1.21 | 0.2 | cue | 4.07 |
| walk | 4 | 5.32 | dive | move |  | auto: tl.to(st, { insetIn: 0, duration: 0.25, ease: "power2.in" }, tDive - 0 | yes | 3.22 | 0.48 |  |  |
| walk | 5 | 5.67 | dive | camera |  | auto: tl.to(st, { lens: 1, duration: 0.38, ease: "back.out(1.7)" }, tDive -  | yes | 11.86 | 0.46 |  |  |
| walk | 7 | 7.01 | into | move |  | auto: drives frame() code | yes | 6.09 | 0.26 | cue | 7.3 |
| walk | 9 | 7.84 | cell | move |  | auto: drives frame() code | yes | 9.73 | -0.11 | cue | 8.19 |
| walk | 10 | 8.09 | there | react | mitochondria | the mitochondria wake up: eyes open all over the muscle | yes | 8.02 | -0.29 | cue | 8.39 |
| walk | 11 | 9.32 | thousands | move |  | auto: drives frame() code | **no** | 1.12 | 0.21 | cue | 9.4 |
| origin | 1 | 11.14 |  | transition |  | cut to the next scene | yes | 12.38 | 0.12 |  |  |
| origin | 2 | 11.20 |  | effect |  | auto: tl.to(st, { vig: 0, duration: 0.9, ease: "power2.out" }, 0.05); | yes | 12.38 | 0.07 |  |  |
| origin | 4 | 12.93 | bigger | move |  | auto: tl.to(st, { hx: HX1, duration: 1.0, ease: "power2.out" }, tB - 0.55); | **no** | 1.75 | 0.34 | cue | 13.38 |
| origin | 5 | 13.82 | swallowed | move |  | auto: tl.to(st, { pocket: 1, duration: 0.35, ease: "power2.out" }, tSw - 0.2 | **no** | 2.27 | -0.29 | cue |  |
| origin | 6 | 14.32 | swallowed | camera |  | auto: tl.to(st, { pull: 1, duration: 0.55, ease: "power2.inOut" }, tSw + 0.3 | **no** | 2.24 | 0.15 | cue | 14.32 |
| origin | 7 | 14.61 | bacterium | move |  | auto: tl.to(st, { pocket: 0, duration: 0.45, ease: "power2.inOut" }, tBa - 0 | yes | 3.04 | 0.46 | cue | 14.61 |
| origin | 8 | 15.62 | but | move |  | auto: tl.to(st, { enzIn: 1, duration: 0.6, ease: "power2.out" }, tBut - 0.35 | yes | 4.0 | -0.29 | cue | 15.84 |
| origin | 9 | 16.37 | digested | move |  | auto: tl.to(st, { chomp: 1, duration: 0.12, ease: "power3.in" }, tDig - 0.05 | **no** | 2.45 | 0.3 | cue | 16.47 |
| origin | 10 | 16.72 | digested | react | bacterium | the bacterium calms down: not digested after all | yes | 2.62 | -0.19 | cue | 16.68 |
| origin | 11 | 17.48 | moved | move |  | auto: tl.to(st, { suit: 1, duration: 0.35, ease: "back.out(2.2)" }, at("move | **no** | 0.62 | 0.12 | cue | 17.6 |
| deal | 1 | 18.56 |  | transition |  | cut to the next scene | yes | 34.69 | 0.04 |  |  |
| deal | 2 | 18.56 |  | camera |  | auto: K.camTo(tl, S.cam, 0, { s: 1.06, py: 980 }, at("lots") - 0.3, "sine.in | yes | 34.69 | 0.04 |  |  |
| deal | 3 | 19.42 | shelter | effect |  | auto: tl.to(st, { shelter: 1, duration: 0.4, ease: "power2.out" }, at("shelt | **no** | 1.32 | 0.18 | glow_on | 19.53 |
| deal | 6 | 20.83 | host | move |  | auto: drives frame() code | yes | 3.44 | -0.23 |  |  |
| deal | 8 | 21.64 | energy | react | host cell | the host cell beams: energy | yes | 5.2 | -0.11 | cue | 21.65 |
| deal | 9 | 22.18 | lots | camera |  | auto: K.camTo(tl, S.cam, at("lots") - 0.3, { s: 0.94, py: 900 }, DUR - at("l | yes | 11.49 | 0.49 | cue | 22.5 |
| proof | 1 | 23.36 |  | transition |  | cut to the next scene | yes | 117.68 | 0.04 |  |  |
| proof | 2 | 23.36 |  | camera |  | auto: K.camTo(tl, S.cam, 0, { s: 1.04, py: 940 }, DUR, "sine.inOut"); | yes | 117.68 | 0.04 |  |  |
| proof | 6 | 26.14 | dna | effect |  | auto: tl.to(st, { dna: 1, duration: 0.3, ease: "power2.out" }, at("dna") - 0 | yes | 3.09 | 0.06 | sparkle | 26.36 |
| proof | 7 | 26.94 | dna | effect |  | auto: tl.to(st, { dna: 0.25, duration: 0.6 }, at("dna") + 0.7); | **no** | 2.13 | 0.06 | sparkle |  |
| proof | 8 | 27.53 | wall | move |  | auto: tl.to(st, { wall: 1, duration: 0.45, ease: "back.out(1.8)" }, at("wall | yes | 9.71 | 0.14 | zip_ | 27.8 |
| proof | 9 | 28.22 | split | move |  | auto: tl.to(st, { wall: 0.35, duration: 0.5 }, at("split") - 0.1); | yes | 22.56 | 0.45 | cue | 28.42 |
| proof | 10 | 28.69 | two | move |  | auto: drives frame() code | yes | 22.53 | 0.04 |  |  |
| proof | 11 | 29.46 | like | move |  | auto: tl.to(st, { eq: 1, duration: 0.3, ease: "back.out(2.5)" }, at("like")  | **no** | 1.56 | 0.07 | chime | 29.54 |
| proof | 12 | 29.73 | bacteria | react | mitochondria | mitochondria and bacteria smile side by side | **no** | 2.35 | -0.2 |  |  |
| atp | 1 | 30.57 |  | transition |  | cut to the next scene | yes | 10.46 | 0.03 |  |  |
| atp | 2 | 30.57 |  | camera |  | auto: K.camTo(tl, S.cam, 0, { s: 1.04, py: 940 }, tSwap, "sine.inOut"); | yes | 10.46 | 0.03 |  |  |
| atp | 3 | 31.74 | food | effect |  | auto: tl.to(st, { work: 1, duration: 0.4 }, at("food") - 0.1); | **no** | 1.06 | 0.33 | cue | 32.03 |
| atp | 4 | 32.15 | oxygen | move |  | auto: drives frame() code | **no** | 0.81 | 0.45 | cue | 32.31 |
| atp | 6 | 34.86 | fuel | effect |  | auto: tl.to(st, { flex: 1, duration: 0.25, ease: "power2.out" }, at("fuel")  | **no** | 1.79 | 0.14 | pop_word | 35.02 |
| atp | 8 | 35.16 | fuel | effect |  | auto: tl.to(st, { flex: 0.35, duration: 0.35, ease: "power2.inOut" }, at("fu | **no** | 1.79 | -0.16 | pop_word | 35.16 |
| atp | 9 | 35.67 | you | move |  | auto: tl.to(st, { p2: 1, duration: 0.45, ease: "power2.inOut" }, tSwap); | yes | 3.17 | 0.26 | cue | 35.87 |
| atp | 10 | 35.93 | recycle | move |  | auto: drives frame() code | yes | 3.17 | 0.0 | cue | 36.35 |
| atp | 11 | 36.69 | own | move |  | auto: tl.to(st, { tilt: 0, duration: 1.3, ease: "power2.inOut" }, at("own")  | **no** | 1.36 | 0.44 | cue | 36.65 |
| atp | 13 | 37.80 | every | move |  | auto: tl.to(st, { dialA: 1, duration: 0.3 }, at("every") - 0.1); | **no** | 1.01 | -0.27 | pop_word | 37.9 |
| mother | 1 | 39.33 |  | transition |  | cut to the next scene | yes | 47.81 | 0.0 |  |  |
| mother | 2 | 39.33 |  | move |  | auto: tl.to(st, { come: 1, duration: 1.1, ease: "power2.out" }, 0); | yes | 47.81 | 0.0 |  |  |
| mother | 4 | 40.47 | came | move |  | auto: tl.to(st, { gone: 1, duration: 0.45, ease: "power2.in" }, at("came") - | **no** | 0.69 | -0.27 | cue | 40.62 |
| mother | 5 | 40.96 | mother | effect |  | auto: tl.to(st, { glow: 1, duration: 0.4 }, at("mother") - 0.2); | **no** | 1.22 | 0.24 | glow_on | 41.14 |
| mother | 7 | 41.71 | thanks | move |  | auto: tl.to(st, { out: 1, duration: 0.22, ease: "power2.in" }, tS); | yes | 3.34 | 0.22 | cue | 41.91 |
| mother | 8 | 42.01 | thanks | react | you | you wave: thanks, Mom | yes | 5.38 | -0.08 | cue | 41.91 |
| mother | 9 | 42.29 | mom | appear |  | a heart pops up above the hand | yes | 3.64 | 0.11 | bubble | 42.56 |
| finale | 1 | 43.09 |  | transition |  | cut to the next scene | yes | 17.46 | 0.12 |  |  |
| finale | 2 | 44.38 | take | camera |  | auto: tl.to(st, { lens: 0, duration: 0.3, ease: "power2.in" }, tOut - 0.15); | yes | 6.86 | -0.25 |  |  |
| finale | 3 | 45.52 | deal | effect |  | auto: tl.to(st, { sparks: 1, duration: 0.4 }, at("deal") - 0.1); | **no** | 1.48 | 0.01 | sparkle | 45.88 |
| finale | 6 | 47.51 | ago | effect |  | auto: tl.to(st, { sparks: 0, duration: 0.4 }, tT); | **no** | 2.34 | 0.09 | cue | 47.67 |
