# Opus Video Creation

A complete, reproducible method for an AI agent to make **flat 2D vector explainer videos** in the
"antibiotics_v2" style: dark, flat-shaded, Kurzgesagt-inspired science explainers with original art,
procedural sound effects, an original score, and motion locked to the narration.

Everything here was produced by an AI agent working only with code and a renderer. It is written so a
**different** agent can read it and make new videos the same way.

> **The quality bar:** [`projects/antibiotics/renders/antibiotics-v2.mp4`](projects/antibiotics/renders/antibiotics-v2.mp4)
> (60 s, 1920×1080, 60 fps, voice + sound effects + music). Contact sheet: `projects/antibiotics/renders/antibiotics-v2-contact.jpg`.

## Start here
1. **`docs/AGENT_PLAYBOOK.md`**: the step-by-step recipe with its approval gates.
2. **`templates/new-film/`**: a tested starter project (9.8 s example render included). Copy it, edit `film.json`,
   write one HTML file per scene.
3. The references below when you need detail.

## Contents
| Path | What it is |
|---|---|
| `docs/AGENT_PLAYBOOK.md` | The recipe: phases, commands, gates, report template |
| `docs/01-environment.md` | Installing HyperFrames, FFmpeg (and the env vars it needs), Python, the TTS models; sandbox quirks |
| `docs/02-hyperframes-contract.md` | How a film is structured (root + scene files), seek-safe GSAP rules, checker findings |
| `docs/03-style-system.md` | The look in eight rules, the palettes, and how to measure a style from a reference |
| `docs/04-drawing-kit.md` | `kit.js` API: organisms, molecules, camera, callouts, narration timing; reusable patterns |
| `docs/05-audio.md` | Sound-effect recipes, cue sheets, the procedural score, mixing targets, verifying audio you can't hear |
| `docs/06-voice-timing.md` | TTS or a human recording → measured word times → scenes and sounds scheduled from them |
| `docs/07-scene-authoring.md` | Script → shots; the antibiotics scene breakdown; a scene checklist |
| `docs/08-review-loop.md` | Stills, contact sheets, the faint/small/wrong critique, MP4 verification, REVIEW.md |
| `docs/09-pitfalls.md` | Every failure hit during the build and its fix |
| `docs/10-making-of.md` | How this video was made: the brief, each step, decisions and lessons |
| `style/STYLE.md` | The measured style guide |
| `lib/kit.js`, `lib/sound_effects.py` | Canonical shared libraries (projects carry copies) |
| `tools/verify_render.py` | Checks an MP4: specs, loudness, peak, audio sync vs stems, black frames, saturation, contact sheet |
| `tools/measure_style.py` | Measures a reference video's palette and saturation; verifies timestamps first |
| `templates/new-film/` | Config-driven starter project (`film.json`), tested end to end |
| `projects/antibiotics/` | The full 60 s film: script, scenes, audio pipeline, review notes, render |
| `projects/ant-fight/` | 4 s style clip with sound (steps 4–5) and its review notes |
| `projects/one-ant-test/` | The 10 s setup test (step 2) |

## The method in one paragraph
Videos are **HTML + SVG + a paused GSAP timeline**, rendered to MP4 by [HyperFrames](https://hyperframes.heygen.com)
(headless Chrome driven by `npx hyperframes`). Each scene is one HTML file with its own seekable timeline; a root
`index.html` mounts the scenes on the film timeline. Art is hand-built SVG from a small kit so everything shares
one look. Audio is **three code-generated stems** (narration, sound effects, music) mixed in Python and layered as
`<audio>` tracks. The decisive trick is the **voice-timing pipeline**: it measures when every narrated word is
spoken, and every animation and every sound effect is scheduled from those word times, so picture and sound stay
locked even when the voiceover changes.

## Quickstart: re-render the antibiotics film
```bash
pip install -r requirements.txt               # numpy + scipy are enough for steps 2-4
cd projects/antibiotics
# 1. (optional) new narration: needs the Kokoro model (docs/01) and faster-whisper
#    python vo.py && python align.py          # the repo ships vo_raw.wav + timing, so you can skip this
python build.py                               # scenes + assets/timing.js from the voice timing
cd audio && node js_events.cjs && python sfx_cues.py && python music.py && python mix.py && cd ..
python build.py                               # mount the mixed stems
npx hyperframes render --fps 60 --quality delivery -o renders/antibiotics.mp4
python ../../tools/verify_render.py renders/antibiotics.mp4 --stems assets --duration 60
```
The repo ships the mixed stems (`assets/vo.wav`, `sfx.wav`, `music.wav`), so `npx hyperframes render` also works
straight after cloning. HyperFrames needs FFmpeg; see `docs/01-environment.md` if `doctor` can't find it.

## Licensing and attribution
- **All code and artwork here are original**, generated procedurally. No copyrighted characters are reproduced.
- The look is **inspired by** the Kurzgesagt explainer style; this project is **not affiliated with Kurzgesagt**.
  No frames, audio or footage from any reference video are included. Reference material was used only to study
  the style and was deliberately left out.
- The method follows the RandomAI tutorial "Claude Opus 5.5 Can Now Make Kurzgesagt-Style Animations (Full Tutorial)".
- Fonts (Nunito, Yanone Kaffeesatz) load from Google Fonts (SIL Open Font License); GSAP from jsDelivr;
  HyperFrames is a third-party renderer. All music and sound effects are synthesised in code.
- The narration in the sample film is a local TTS voice (Kokoro `af_heart`), a stand-in for a human recording.
