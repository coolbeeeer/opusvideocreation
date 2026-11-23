# Why Most Animals in the Open Ocean Glow: 54-second vertical script

Format: YouTube Shorts and Instagram Reels, 1080x1920 (9:16), 30 fps, 54.2 s, burned-in captions.
Style: `style/STYLE.md` plus the deep-sea notes in `docs/12-vertical-shorts.md`. Dark navy-to-teal water; the light
the animals make (cyan and blue) is the focus colour; red is reserved for the dragonfish's searchlight.
Voice: local Kokoro TTS `af_heart` at 0.95x, one TTS call per line, a stand-in for a human recording.
Audio: narration, procedural sound effects (`audio/sfx_cues.py`), an original score synthesised in code (`audio/music.py`).

Times below are the measured film times of the rendered v3 (from `assets/timing.json`).

| # | Scene | Time | Narration | Picture | Sound |
|---|---|---|---|---|---|
| 1 | `hook` | 0.0-5.1 | Three out of four animals in the open ocean can make their own light. Why? | Four lanternfish in the dark; three light up one after another, the fourth stays dark and looks around. Banner "3 out of 4", a big "?", then everything lifts toward the light | A glassy swell per fish that lights up, word pops, a boing for the "?", a rising whoosh |
| 2 | `descent` | 5.1-12.9 | Dive in, and sunlight fades fast. By two hundred metres, it's twilight. Below a thousand, it's night. Forever. | One continuous dive: sky and Sun, splash, a silver school, a whale, sunbeams fading, the first lights of the twilight zone, then the dark with one nervous pair of eyes. A depth gauge reads the depth live. Banners "Twilight zone", "Midnight zone" | Surf, splash and bubbles, a pressure rumble that builds as we sink, a blink |
| 3 | `chemistry` | 12.9-17.5 | So life makes its own, by mixing a chemical fuel with an enzyme. | The lights come on in a wave; the camera dives into one light organ; inside, a fuel molecule and an enzyme with faces meet and the reaction lights up. Tags "Fuel", "Enzyme", "Light!" | A sparkle wave, a whoosh into the light organ, a snap and a chime when the light appears |
| 4 | `angler` | 17.5-23.3 | An anglerfish dangles a glowing lure. Something curious swims closer. Bad idea. | Start close on the lure, pull back to the anglerfish; a small fish falls for the light (a heart), the jaws snap shut on "Bad idea", the camera shakes | The lure's hum, a heartbeat in the score, a chomp and a burp |
| 5 | `hatchet` | 23.3-30.6 | A hatchetfish lights up its belly to match the faint glow from above. Seen from below, its silhouette vanishes. | Side view: the belly lights come on under the faint light from above. Then the view of a hungry fish below: lights off, the hatchetfish is a dark shape with a lock-on ring; lights on, the shape melts into the light. The hunter is left with a "?" | A glow swell, descending tings for the light from above, two lock-on beeps, a "target lost" sweep, a boing |
| 6 | `alarm` | 30.6-37.9 | Grab certain jellyfish, and they flash like a burglar alarm, likely calling in something bigger to eat the attacker. | A small fish bites an Atolla-style jellyfish; its ring of lights spins like a siren with expanding rings; banner "Burglar alarm"; a big fish comes out of the dark and eats the attacker | Bite, a soft "wee-woo" siren and a ping per ring, a deep approaching rumble, a chomp |
| 7 | `colours` | 37.9-46.6 | Most of this light is blue, because blue travels farthest in water. But one dragonfish cheats, with red light its prey can't see. | Blue lights everywhere; five coloured beams race down and the water swallows them one colour at a time, blue last ("Farthest"). A stoplight loosejaw glides in, switches on a red searchlight; the red shrimp, invisible until now, hums along. Tag "Can't see red"; snap | Sparkles, a click and a hum for the lamp, a ting as each beam dies, a sly two-note sting, the shrimp's two-note hum, a chomp |
| 8 | `finale` | 46.6-54.2 | Sunlight never reaches most of the ocean. So its residents brought their own. | Pull back from the dark to a cross-section of the whole ocean, to scale in depth: a thin sunlit strip, the twilight band, and the dark below 1,000 m (bracketed, "No sunlight"). The deep fills with lights from the bottom up; title "why most open-ocean animals GLOW" held 2.9 s | A long airy pull-back, a cascade of tiny tings, a chime chord on the title |

132 words. Measured speech 46.7 s at 0.95x; pauses are set per line in `film.json` (0.5-0.8 s).

## Accuracy notes
- **"Three out of four"**: 76 % of the animals observed from the surface to about 3,900 m in Monterey Bay could make
  light ([Martini & Haddock 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5379559/)). It counts individuals in the
  water column of one well-surveyed region and is widely used for the open ocean. Sea-floor animals measured 30-41 %
  ([Martini et al. 2019](https://www.nature.com/articles/s41598-019-50961-z)), which is why the script says "open ocean".
- **Light and depth**: 200-1,000 m is the twilight zone; below 1,000 m no light from the surface arrives
  ([NOAA Ocean Exploration](https://oceanexplorer.noaa.gov/ocean-fact/light-distributed/)). The finale's cross-section
  uses the average ocean depth of 3,682 m ([NOAA](https://oceanexplorer.noaa.gov/ocean-fact/ocean-depth/)), so most of
  the water column is below 1,000 m.
- **"A chemical fuel with an enzyme"**: a luciferin oxidised with the help of a luciferase
  ([Haddock, Moline & Case 2010](https://pubmed.ncbi.nlm.nih.gov/21141672/)). Oxygen is left out of the picture.
- **Anglerfish**: the lure (esca) glows because of bioluminescent bacteria living in it
  ([NOAA Ocean Exploration](https://oceanexplorer.noaa.gov/expedition-feature/19biolum-background-midnight-zone/),
  [MBARI](https://www.mbari.org/animal/deep-sea-anglerfish/)); the narration only says "glowing lure", which stays true.
  The lure is drawn green-cyan to keep it apart from the blue animals; real lures glow blue-green.
- **Hatchetfish**: belly photophores match the light coming down from above and hide the silhouette from predators
  below (counter-illumination; [Britannica](https://www.britannica.com/science/How-do-deep-sea-fish-use-photophores-to-hide-from-predators-below-them)).
  The view from below is drawn as a side view against the light, the usual way to diagram it.
- **Burglar alarm**: when caught, *Atolla* jellyfish flash a spinning ring of blue light; the leading explanation is that
  it attracts a larger predator that may attack the attacker ([NOAA Ocean Exploration](https://oceanexplorer.noaa.gov/wp-content/uploads/2025/04/medusa-lander-exploration-notes.pdf),
  [MBARI](https://www.mbari.org/animal/deep-sea-crown-jelly/)). The narration says "likely" because it is a hypothesis.
- **Blue**: most marine bioluminescence is blue because blue light travels best through water
  ([NOAA Ocean Exploration](https://oceanexplorer.noaa.gov/ocean-fact/bioluminescence/)). The beam lengths in the
  diagram show the order (red absorbed first, blue last), not real distances.
- **Red light**: the stoplight loosejaw *Malacosteus niger* and two related dragonfish genera also emit far-red light
  from photophores under the eye, invisible to most deep-sea animals; *Malacosteus* sees it with a chlorophyll-derived
  pigment ([Douglas et al. 1998](https://www.nature.com/articles/30871)). "One dragonfish" means one kind; a few related
  ones do it too. Red shrimp look black in blue light and show up in red light, which is the point of the beam.

Content from these sources was rephrased for compliance with licensing restrictions.
