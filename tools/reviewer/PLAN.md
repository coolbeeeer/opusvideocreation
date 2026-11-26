# plan.json: the event list and shot plan

Write `projects/<film>/plan.json` after the script and the voice timing exist and **before** building scenes. It
says, for every scene, what happens in the picture, on which word, where on screen, who does it, and which sound
goes with it. Stage 2 of the reviewer checks the plan itself; stage 3 checks the rendered film against it. A plan
that describes a better film than the one rendered gets the film rejected, so write what you will build, then
build what you wrote.

A full example: `tools/reviewer/calibration/black-hole-short.plan.json` (55 picture events, 7 scenes). For an
existing film, `python tools/reviewer/review.py draft-plan projects/<film>` writes `plan.draft.json` from the
scene code with every field it cannot know marked `TODO`.

## Top level

```json
{
 "version": 1,
 "characters": ["astronaut", "friend"],
 "holds": [{"from": 21.0, "to": 23.0, "why": "the push-in to the event horizon: the glow becomes broad smooth bands"}],
 "captions": {"box": [0, 1150, 1080, 1230]},
 "scenes": [ ... one entry per film.json scene, same ids, same order ... ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `characters` | if the film has any | Every character with a face. The **first one is the lead**: it must act at least once per 4.5 s on screen. |
| `holds` | no | Stretches (film seconds) where stillness or empty background is the point: darkness that is the subject, a breath before the punchline. Each needs `from`, `to` and `why`. At most 25 % of the film. Stage 3 does not flag stillness, empty frames, black or saturation inside a hold. |
| `captions.box` | no | `[x0, y0, x1, y1]` of the burned-in captions. Normally left out: stage 3 finds the caption band itself (the rows whose change follows the words) and never counts captions as picture. |
| `scenes` | yes | One per `film.json` scene, same `id`s and order. |

## A scene

```json
{"id": "small", "transition": "cut", "cast": ["astronaut", "astronomer"],
 "shots": [
  {"time": 0, "size": "wide", "move": "slow push in"},
  {"word": "stretched", "offset": -0.2, "size": "wide", "move": "push in"}
 ],
 "events": [
  {"time": 0, "kind": "transition", "does": "cut to the astronaut hanging above a small black hole", "sfx": "rumble"},
  {"word": "ten", "offset": -0.05, "kind": "appear", "does": "ten suns pop in, one after another, in a row", "where": [200, 960, 880, 1080], "sfx": "pops (rising)"},
  {"word": "feet", "offset": 0.4, "kind": "react", "who": "astronaut", "does": "panics: arms fly up, mouth wide open", "where": [380, 340, 720, 900]},
  {"word": "stretched", "offset": -0.2, "kind": "act", "who": "astronaut", "does": "is stretched: the feet race ahead toward the hole", "where": [420, 260, 680, 1120], "sfx": "stretch"},
  {"word": "spaghettification", "offset": -0.1, "kind": "label", "text": "Spaghettification", "sfx": "pop (banner)"}
 ]}
```

| Field | Required | Meaning |
|---|---|---|
| `transition` | every scene after the first (should) | How the scene begins: cut, cut on motion, match cut, push, pull, wipe, dive ... |
| `cast` | no | Characters on screen in this scene; the first is the scene's lead. Default: everyone named in the scene's events. **Every cast member must act or react in the scene.** Leave out a character that is only a prop. |
| `shots` | yes | The framing at the scene start and at every size change or camera move. |
| `events` | yes | Everything that happens in the picture, plus labels and titles. |

### Anchors (events and shots)

An event or shot happens on a **word**: `"word": "stretched"` is the first time "stretched" is spoken at or after
the scene's start; `"n": 2` the second time; `"offset": -0.2` 0.2 s before the word starts. This is exactly the
scenes' `at("stretched") - 0.2`, so the plan and the code use the same anchor and the film re-times itself when the
voice changes. Words are matched as the pipeline matches them: lower case, letters and digits only ("you'd" is
`youd`, "can't" is `cant`).

An event must fall within 0.6 s of its word (before the word starts or after it ends). Use `"time"` (seconds from
the scene start) only for the scene start and for pauses; an event placed by time while words are being spoken is
rejected. At least 85 % of events must be anchored to words.

### Kinds

| Kind | The viewer sees | Needs |
|---|---|---|
| `act` | a character does something: a gesture, an action, a transformation of its body | `who`, `where`, `does` |
| `react` | a character's face or body responds: fear, a grin, a shrug, a nod | `who`, `where`, `does` |
| `move` | something moves with a purpose: slides in, falls, is swallowed | `where`, `does` |
| `appear` | something appears, pops in, opens, is drawn on | `where`, `does` |
| `effect` | light, colour or shape changes: a glow, a flash, the view turns red | `where`, `does` |
| `camera` | the camera pushes in, pulls back, dives, cuts to a new size | `does` |
| `transition` | the cut or wipe into the scene (a cut alone does not show a sentence) | `does` |
| `label` | text on screen that names something | `text` |
| `title` | the title card | `text` |

`act`, `react`, `move`, `appear`, `effect`, `camera` and `transition` are **picture events**; `label` and `title` are
**text events**. Labels name what the picture shows; they never replace it (a sentence carried only by a label is
rejected, and text may be at most 50 % of all events).

`does` describes what changes, starting with the verb the viewer sees ("panics: arms fly up"). Acts that start with
a pose verb (stands, floats, looks, waits, idles, sways, blinks ...) count as posing.

### where

`[x0, y0, x1, y1]` in film pixels (0, 0 is the top left; a vertical film is 1080 x 1920), the box where the change
happens **at that moment**: the face for a reaction, the body for a gesture, the label's area. Or a region name:
`full`, `top`, `middle`, `center`, `bottom`, `left`, `right`, `top-left`, `top-right`, `bottom-left`,
`bottom-right`. Stage 3 looks for the change inside the box, so a tight box is a stronger check; `full` makes the
event compete with everything else moving in the frame and small events are then easily missed.

### sfx

The name of the event's sound cue, as in `audio/sfx_cues.py` ("thump", "zip (long)", "bubble"). At least 85 % of
picture events other than reactions need one, and no cue name may cover more than 40 % of the cued events. Stage 3
checks that a sound starts in the effects stem at the event's time and that the sounds differ from each other.

### Shot sizes

| Size | The main subject |
|---|---|
| `extreme-wide` | is small (under about a tenth of the frame height) or absent; the place dominates |
| `wide` | is whole, with plenty of room around it |
| `medium` | fills about a third to two thirds of the frame height |
| `close` | fills most of the frame: a face, one cell |
| `extreme-close` | a detail fills the frame: an eye, a molecule |

Aliases: ews, ws, ms, cu, ecu, close-up, macro, establishing, two-shot, insert. `move`: static, or what the camera
does (push in, pull back, drift, dive, track). The film needs at least three sizes, and three scenes in a row at one
size without a camera move are rejected.

## What the reviewer does with the plan

Stage 2 (before scenes are built): every scene shows something about once a second, every sentence has a picture
event on one of its words (two for sentences of 12 words or more), no 3 s of narration without one, the lead acts,
every action has a sound, the shot size changes. Stage 3 (after rendering): each planned picture event must
visibly change its box at its time, far more often than at shifted times; each cued event must have a sound starting
then; the characters' acts must show up in their boxes. `EVENTS.md` in the review folder lists every event with what
was measured, and `sheets/events-<scene>.jpg` shows the frames before, at and after each one with its box drawn.
