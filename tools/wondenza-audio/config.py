"""Wondenza audio — locked constants.

Every number here is a user-locked house rule for the Wondenza channel.
Do not change a value to make a film pass a check; if a value looks wrong,
say so and let the user change it. The S03 reviewer cap (90 s) is separate
and lives in the reviewer, not here.

Sources:
  - Voice model / engine / pace: locked 2026-11-22 (Fish Audio).
  - Mix ratio: fever v2B, user-locked by ear 2026-11-22.
  - Master -14 LUFS: user order 2026-11-24 (was ~-16).
  - End-card pattern: ~/workspace/kaleida-brand/ENDCARD-PATTERN.md, user verdict "Perfect".
  - Mix + assembly recipe: verified on the hypnic-jerk re-voice, 2026-11-26
    (~/workspace/hvp-animation-prep/hypnic-jerk/opus-revoice/REVIEW.md).
"""
from pathlib import Path

# --- Fish Audio voice (locked) -------------------------------------------------
# The API key is NEVER stored here. It comes from the environment:
#   FISH_AUDIO_API_KEY=<key from fish.audio>
# Set it in Kiro as an environment variable / secret. No other credential is needed.
FISH_API_URL = "https://api.fish.audio/v1/tts"
FISH_MODEL_ID = "1d866ca2766944489ae05da868809c15"   # "Modern Tech Storyteller"
FISH_ENGINE = "s2.1-pro-free"                     # FREE evaluation engine.
# NEVER "s2.1-pro" (paid engine 402, no credit) — the module refuses it.
FISH_FORMAT = "wav"
FISH_LANGUAGE = "en"
FISH_LATENCY = "balanced"

# Reading pace. 0.85 is the approved middle pace (0.68 too slow, 1.0 too fast
# for dense scripts). A clip that runs over its max length is re-recorded
# at 1.05x, then 1.1x — never faster.
VOICE_PACE = 0.85
VOICE_SPEEDUP_STEPS = (1.05, 1.10)
VOICE_MAX_SPEED = 1.10

# --- Voice stem ---------------------------------------------------------------
VOICE_LUFS = -15.0          # each clip levelled to this (measured with loudnorm)
VOICE_HIGHPASS_HZ = 80      # HP80 on every clip
VOICE_LIMITER = 0.707        # -3 dBFS peak limit on the voice stem
TRIM_THRESHOLD_DB = -42.0    # leading/trailing silence cut below this
TRIM_LEAD_PAD_S = 0.01       # keep this much before the first speech sample
TRIM_TAIL_PAD_S = 0.05       # keep this much after the last speech sample

# --- Mix ----------------------------------------------------------------------
# The bed (SFX + music) sits BED_VOICE_OFFSET_DB under the voice WHILE SPEAKING.
# It gets there as bed +6 dB vs the original balance, ducked BED_DUCK_DB under
# the voice — the module measures the result and corrects the bed gain so the
# offset lands on target whatever the bed's starting level is.
BED_VOICE_OFFSET_DB = 8.4
BED_DUCK_DB = 3.0
DUCK_ATTACK_MS = 40
DUCK_RELEASE_MS = 350

# --- Master -------------------------------------------------------------------
MASTER_LUFS = -14.0
MASTER_PEAK_DBFS = -1.5
MASTER_LIMITER = 0.79        # alimiter limit; level=false (level=true pushes +2 dB and clips)
MASTER_GAIN_BEFORE_LIMITER = True   # gain MUST come before the limiter (see REVIEW.md)

# --- End card (locked pattern) -------------------------------------------------
HOLD_AFTER_LAST_WORD_S = 0.5    # stillness after the last spoken word
XFADE_DURATION_S = 1.5          # slow crossfade film -> card
CARD_DURATION_S = 3.0           # end-card video length
VOICE_LINE_DELAY_AFTER_CARD_S = 0.2   # "Like and subscribe" lands this long
#                                    # after the card is fully visible
SAMPLE_RATE = 48000

# --- Watermark (locked: 25% eye, top-right, film only) --------------------------
WATERMARK_OPACITY = 0.25
WATERMARK_WIDTH = 240            # icon scaled to this width (1080x1920 frame)
WATERMARK_X = 830
WATERMARK_Y = 30
WATERMARK_COLORKEY = "0x190138:0.08:0.05"   # the eye icon's background colour

# --- Assets (bundled in tools/wondenza-audio/assets/) ---------------------------
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ENDCARD_VIDEO = ASSETS_DIR / "wondenza-endcard-final.mp4"   # 3.0 s, 1080x1920
LIKE_SUBSCRIBE = ASSETS_DIR / "like_subscribe.wav"          # locked clip, 1.21 s — NEVER regenerate
ENDCARD_SFX = ASSETS_DIR / "endcard-audio.wav"               # card bed, 3.5 s
EYE_ICON = ASSETS_DIR / "Kaleida-Icon-GPT.png"               # watermark source
