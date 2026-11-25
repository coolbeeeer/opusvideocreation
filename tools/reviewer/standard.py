"""The standard: every rule the reviewer applies, with its threshold, in one place.

Rule ids: S = script (stage 1), P = plan (stage 2), F = film (stage 3). "must" rules block approval; "should" rules are
listed in the fix list but do not block. The numbers were calibrated on the three vertical films in projects/
(ocean-glow-short, mitochondria-short, black-hole-short): see tools/reviewer/calibration/README.md for what each film
measures. `python tools/reviewer/review.py rules` prints this table.
"""

T = {
    # ---------------------------------------------------------------- stage 1: script
    "film_max_s": 60.0,           # Shorts / Reels: under 60 s keeps every platform option open
    "film_min_s": 20.0,
    "film_target": (40.0, 58.0),
    "wpm_must": (115.0, 190.0),   # words per minute over the whole film (my films: 146-165)
    "wpm_should": (130.0, 175.0),
    "speech_wps": 3.2,            # words per second of speech, to estimate length before the voice exists
    "hook_max_words": 14,         # first sentence
    "hook_max_s": 4.5,            # ... and it must be over by then
    "sentence_must": 26,          # words
    "sentence_should": 20,
    "sentence_mean_should": 14.0,
    "you_should": 3,              # "you/your" count: talk to the viewer
    "numbers_should": 2,          # concrete numbers or comparisons
    "pause_must": (0.0, 1.5),
    "pause_should": (0.3, 0.9),
    "tail_should": 2.0,           # seconds after the last word (title hold)
    "scene_must": (2.0, 16.0),    # seconds
    "scene_should": (3.0, 13.0),
    "scenes_should": (4, 10),
    "sources_min": 3,             # unique http(s) links in SCRIPT.md, and at least one per 2 lines
    "jargon_letters": 13,         # words this long must be introduced ("called", "this is", ...)
    "heard_min": 0.97,            # share of script words align.py actually heard (not interpolated)

    # ---------------------------------------------------------------- stage 2: plan
    "ev_rate_must": 0.40,         # picture events per second of a scene (my films: about 0.8-1.2)
    "ev_rate_should": 0.65,
    "ev_min_per_scene": 2,
    "gap_must": 3.0,              # longest stretch of narration without a planned picture event
    "gap_should": 2.0,
    "label_share_must": 0.50,     # text events (labels, titles) as a share of all events
    "label_share_should": 0.35,
    "anchored_must": 0.85,        # share of events anchored to a word
    "offset_max": 0.6,            # s before the anchor word starts or after it ends
    "free_clear_s": 0.25,         # an unanchored event must be this far from any spoken word
    "sizes_min": 3,               # distinct shot sizes in the film
    "same_size_run": 3,           # this many scenes in a row at one size with no camera move fails
    "long_scene_s": 6.0,          # scenes longer than this need a size change or a camera move
    "act_rate_must": 1 / 4.5,     # the lead's acts/reacts per second on screen (black hole astronaut: about 1 per 3.6 s)
    "act_rate_should": 1 / 3.0,
    "sfx_cover_must": 0.85,       # picture events other than reactions with a planned sound cue (black hole: 0.89)
    "sfx_top_share_must": 0.40,   # most-used cue name as a share of picture events with a cue
    "sfx_distinct_should": 0.50,
    "first_event_film_s": 1.0,    # the film starts on motion
    "first_event_scene_s": 0.8,
    "title_hold_s": 2.0,
    "holds_max_share": 0.25,      # declared holds (accepted stillness) as a share of the film
    "holds_voice_should_s": 6.0,  # ... and their total while the voice is speaking

    # ---------------------------------------------------------------- stage 3: film
    "lufs": -14.0, "lufs_tol": 1.0, "true_peak_max": -1.0,
    "sync_ms": 20.0,
    "black_s": 0.1,
    "median_motion_must": 0.8,    # mean |luma change| between frames 0.1 s apart, captions excluded (my films 1.4-2.9)
    "median_motion_should": 1.2,
    "still_level": 0.2,           # a frame this still or stiller counts as frozen
    "still_must_s": 1.0,          # a frozen run this long before the voice ends fails
    "still_should_s": 0.6,
    "flat_block_std": 3.0,        # frame_stats.py: a 12x12 block with luma std-dev under 3 is empty background
    "flat_second": 70.0,          # a second with more than 70 % empty blocks is "mostly empty"
    "flat_run_must_s": 2.0,
    "flat_share_must": 0.15,
    "flat_share_should": 0.08,
    "onset_rate_must": 0.50,      # measured picture onsets per second, per scene (my films: 0.6-3.0)
    "onset_rate_should": 0.80,
    "dead_must_s": 2.5,           # no picture onset and little motion while the narration runs
    "dead_should_s": 1.5,
    "dead_motion": 0.6,
    "shown_must": 0.80,           # planned picture events that visibly happen at their time and place (black hole: 0.89)
    "lock_win": (-0.30, 0.50),    # s around the planned time where the change must be
    "shown_ratio": 2.5,           # change in the box at the event / the box's usual change between events
    "shown_blocks": 4,            # ... and at least this many 12 px blocks change by more than 6 levels
    "shown_spatial": 2.0,         # ... and a boxed event changes at least 2x as much as the rest of the frame
    "event_lock_p_must": 0.01,    # events seen at their times vs at times moved 0.7-2.5 s (binomial test)
    "lock_ratio_should": 1.15,    # big picture onsets at planned times / 0.8-2 s away (black hole 1.46, ocean 1.38)
    "lock_p_should": 0.10,        # ... permutation test against randomly shifted plans
    "acts_shown_must": 0.70,      # act/react events with an onset inside their `where` box
    "cue_jump_high_db": 5.0,      # a sound starts: the effects level above 1.5 kHz rises this much at the event ...
    "cue_jump_db": 8.0,           # ... or the whole band rises this much (within -0.1..+0.45 s, vs the 0.65 s before)
    "cue_cover_must": 0.75,       # cued picture events with a sound starting at their time (black hole: 0.91)
    "cue_cover_should": 0.85,
    "cue_lock_p_must": 0.10,      # ... and more often than with the cues shifted 0.7-2.5 s at random (black hole: p 0.003)
    "cue_same_must": 0.60,        # largest group of near-identical cue sounds, share of matched cues
    "cue_same_should": 0.40,
    "cue_same_sim": 0.985,        # spectral similarity above which two cues count as the same sound
    "voice_over_bed_must": 5.0,   # dB, RMS while speaking (my films 6.7-8.0)
    "voice_over_bed_should": 7.0,
    "music_under_voice_must": 9.0,
    "music_present": 0.70,        # share of the film where the music stem is audible
    "captions_follow": 0.70,      # share of words with a caption change at their time
    "seek_px_max": 0.02,          # fresh snapshot vs MP4 frame: share of pixels off by more than 40 (my films: under 0.5 %)
    "seek_mean_max": 8.0,         # ... or mean |difference| per channel (my films 1.3-2.3; up to 5 in fast, blurred, dark frames)
    "sat_share": 7.0,             # % of very saturated bright pixels per second (style rule)
}

KINDS_PICTURE = {"act", "react", "move", "appear", "camera", "effect", "transition"}
KINDS_TEXT = {"label", "title"}
KINDS = KINDS_PICTURE | KINDS_TEXT
SIZES = ["extreme-wide", "wide", "medium", "close", "extreme-close"]
SIZE_ALIASES = {"ews": "extreme-wide", "establishing": "extreme-wide", "ws": "wide", "long": "wide", "ms": "medium",
                "mid": "medium", "two-shot": "medium", "cu": "close", "close-up": "close", "closeup": "close",
                "ecu": "extreme-close", "macro": "extreme-close", "extreme-close-up": "extreme-close", "insert": "close"}
POSE_VERBS = {"stand", "stands", "standing", "float", "floats", "floating", "hover", "hovers", "drift", "drifts",
              "idle", "idles", "wait", "waits", "sit", "sits", "is shown", "appears", "looks", "look", "pose", "poses",
              "bob", "bobs", "sway", "sways", "breathes", "blinks"}
GENERIC_FILLER = [
    "in this video", "today we", "today, we", "let's dive", "lets dive", "let's explore", "let us explore",
    "let's take a look", "in conclusion", "to sum up", "stay tuned", "don't forget to", "subscribe", "like and share",
    "delve", "it's important to note", "it is important to note", "the world of", "a journey", "embark",
    "fascinating world", "without further ado", "buckle up", "in today's",
]
CLICHES = ["have you ever wondered", "believe it or not", "the answer may surprise you", "you won't believe",
           "mind-blowing", "mind blowing", "game changer", "game-changer", "at the end of the day"]

RULES = {
    "S01": ("must", "film.json has lines (text + pause) and scenes that cover every line once, in order"),
    "S02": ("must", "SCRIPT.md has accuracy notes and at least max(3, lines/2) unique source links"),
    "S03": ("must", "film length 20-60 s (should: 40-58 s)"),
    "S04": ("must", "pace 115-190 words per minute of film (should: 130-175)"),
    "S05": ("must", "the hook: first sentence at most 14 words and over within 4.5 s; should ask a question, speak to 'you' or state a number"),
    "S06": ("must", "no sentence over 26 words (should: 20; mean 14)"),
    "S07": ("must", "no generic filler ('in this video', 'let's dive in', 'delve' ...); should avoid cliches"),
    "S08": ("should", "talk to the viewer: 'you'/'your' at least 3 times"),
    "S09": ("should", "at least 2 concrete numbers or comparisons"),
    "S10": ("should", "a turn ('but', 'yet', 'or better' ...) so the story has tension"),
    "S11": ("should", "a short last line (16 words or fewer) with a callback to an earlier line, and a 2 s tail for the title"),
    "S12": ("must", "pauses 0-1.5 s, none after the last line (should: 0.3-0.9 s)"),
    "S13": ("must", "scenes 2-16 s (should: 3-13 s, 4-10 scenes)"),
    "S14": ("should", "long technical words are introduced ('called', 'this is', 'known as')"),
    "S15": ("must", "align.py heard at least 97 % of the script words"),
    "P01": ("must", "plan.json exists and lists every film.json scene, in order"),
    "P02": ("must", "every event and shot is anchored to a word spoken in its scene (or a time inside it)"),
    "P03": ("must", "every event has a known kind; picture events say what happens and where on screen (a box or a region; cameras and cuts excepted); acts/reacts name who"),
    "P04": ("must", "picture events per scene at least 1 per 2.5 s and 2 per scene (should: 1 per 1.5 s)"),
    "P05": ("must", "no stretch of narration over 3 s without a picture event (should: 2 s), except declared holds"),
    "P06": ("must", "every sentence has a picture event on one of its words (or placed by time just before it; a cut alone does not count); long sentences (12+ words) two"),
    "P07": ("must", "text events (labels, titles) at most 50 % (should: 35 %); no sentence carried only by text"),
    "P08": ("must", "85 % of events anchored to a word and within 0.6 s of it (before its start or after its end); free events only in pauses"),
    "P09": ("must", "shot plan: 3+ shot sizes; no 3 scenes in a row at one size without a camera move; scenes over 6 s change size or move (should)"),
    "P10": ("must", "characters act: everyone in a scene's cast acts or reacts in it (not only pose verbs); the lead acts at least once per 4.5 s on screen (should: per 3 s)"),
    "P11": ("must", "85 % of picture events other than reactions have a sound cue; no cue name on more than 40 % of the cued events (should: 50 % distinct names)"),
    "P12": ("should", "every scene after the first says how it begins (transition)"),
    "P13": ("must", "a picture event in the first 1.0 s of the film (should: within 0.8 s of every scene start)"),
    "P14": ("should", "the last scene has a title held at least 2 s"),
    "P15": ("should", "the plan matches the code: event words appear as at(\"word\") in the scene file, cue words in sfx_cues.py"),
    "P16": ("must", "declared holds have from/to/why and total at most 25 % of the film (should: 6 s while speaking)"),
    "F01": ("must", "MP4 specs: H.264 yuv420p, AAC 48 kHz, size, fps, duration and frame count match the film"),
    "F02": ("must", "loudness -14 +/- 1 LUFS integrated, true peak at most -1 dBTP"),
    "F03": ("must", "the three stems exist and the MP4 audio is within 20 ms of them"),
    "F04": ("must", "no black stretches or flash frames outside declared holds"),
    "F05": ("must", "captions are burned in and follow the words (when film.json asks for captions)"),
    "F06": ("must", "motion: median at least 0.8 (should 1.2); no frozen run of 1 s or more before the voice ends (should: 0.6 s)"),
    "F07": ("must", "empty frames: no run of 2 s or more over 70 % flat outside holds; at most 15 % of seconds (should 8 %)"),
    "F08": ("must", "every scene shows at least 0.5 picture onsets per second (should 0.8); no dead stretch of 2.5 s (should 1.5 s)"),
    "F09": ("must", "80 % of planned picture events visibly happen at their time and in their box (the change there is 2.5x the box's usual change between events)"),
    "F10": ("must", "the picture is locked to the words: planned events are seen at their times far more often than when moved 0.7-2.5 s (p at most 0.01); should: the film's big changes cluster at the planned times (1.15x, p 0.10)"),
    "F11": ("must", "characters act: 70 % of act/react events visibly happen inside their box, and in every scene each character shows at least one of its acts"),
    "F12": ("must", "75 % of cued picture events have a sound starting at their time (should 85 %), clearly more than at shifted times (p at most 0.10); no single sound on more than 60 % of them (should 40 %)"),
    "F13": ("must", "mix: voice at least 5 dB over the bed while speaking (should 7), music at least 9 dB under the voice, music present"),
    "F14": ("must", "HyperFrames check: 0 errors and 0 warnings, default run and a 150-sample layout scan"),
    "F15": ("must", "seek test: fresh snapshots match the MP4 frames (no order-dependent state)"),
    "F16": ("should", "very saturated bright pixels at most 7 % per second outside declared holds"),
}


def rules_table():
    rows = ["| Rule | Level | Requirement |", "|---|---|---|"]
    for k, (lvl, txt) in RULES.items():
        rows.append(f"| {k} | {lvl} | {txt} |")
    return "\n".join(rows)
