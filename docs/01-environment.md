# 01 · Environment

Tested with: Linux x64 (Docker sandbox, read-only system dirs), Node 22, Python 3.11, HyperFrames 0.9.56,
FFmpeg 7.0.2 static, Chrome Headless Shell 152, GSAP 3.15.0 (CDN), Kokoro-ONNX 0.6.1, faster-whisper 1.2.1.

## 1. HyperFrames (the renderer)
HyperFrames turns an HTML page with a paused GSAP timeline into a video by seeking the timeline frame by frame
in headless Chrome and piping frames to FFmpeg. It runs through `npx`; no global install.

```bash
npx hyperframes doctor                 # what is missing
npx hyperframes browser ensure         # downloads Chrome Headless Shell into ~/.cache/hyperframes
npx hyperframes init my-film --non-interactive --resolution=1080p
npx hyperframes check                  # lint + runtime + layout + motion + contrast
npx hyperframes snapshot --at 1,3,5 -o snaps   # PNG stills + contact sheet
npx hyperframes render --fps 60 --quality delivery -o renders/out.mp4
```
Projects pin the CLI version in `package.json` (`hyperframes@0.9.56`); use the pinned version for re-renders.

## 2. FFmpeg when you cannot install system packages
`doctor` reported FFmpeg missing and `dnf`/`apt` failed (read-only filesystem). Fix:
```bash
mkdir -p .tools/bin && cd .tools && curl -sSL -o ff.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xf ff.tar.xz && cp ffmpeg-*-static/ffmpeg ffmpeg-*-static/ffprobe bin/
```
**HyperFrames only trusts system PATH directories**, so a binary in your own folder is not found even if it is on
`PATH`. Point at it explicitly (this was found by reading the CLI source, `findFfBinary`):
```bash
export HYPERFRAMES_FFMPEG_PATH=$PWD/bin/ffmpeg
export HYPERFRAMES_FFPROBE_PATH=$PWD/bin/ffprobe
```
The static build lacks the `drawtext` filter (no fontconfig); avoid it in ffmpeg contact-sheet commands.

## 3. Python
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
```
`numpy` + `scipy` are needed for all audio. `kokoro-onnx` + `soundfile` only for TTS, `faster-whisper` only for
`align.py` (it downloads the `base.en` model from Hugging Face on first use; set `HF_HOME` to choose the cache).
`pip install pycairo` failed here (no system cairo); nothing in this pipeline needs it.

## 4. Kokoro TTS model files (offline voice)
```bash
mkdir -p models/kokoro && cd models/kokoro
curl -sSL -O https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -sSL -O https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
export KOKORO_DIR=$PWD
```
~350 MB total. Voices used: `af_heart` (female, used in the film), `bm_george` (British male), `am_michael`
(American male). At natural speed the male voices read the same script ~10 % slower than `af_heart`.
`create_timed()` returns no timings with the v1.0 model, which is why `align.py` exists.

## 5. Sandbox quirks seen in this build
- **Long-running/background processes were blocked.** `npx hyperframes preview` (Studio on :3002) and
  `run_in_background` jobs did not start. Render in the foreground: a 60 s, 60 fps film took ~160 s on 8 cores.
  The human could not open localhost anyway, so previews are delivered as stills, contact sheets and MP4s.
- **Network:** npm, pip, GitHub releases, Google Fonts and jsDelivr were reachable. YouTube pages were not
  readable; Google Drive links work only when shared "Anyone with the link".
- **Image viewing cache:** the image reader cached by path, so a regenerated contact sheet at the same path
  showed the old image. Write each review sheet to a new filename.
- **Skills:** HyperFrames' optional AI skills (`/hyperframes`, ...) were never installed
  (`HYPERFRAMES_SKIP_SKILLS=1`). Everything here was done from `npx hyperframes docs <topic>`, the bundled
  examples (`init --example product-promo` shows the sub-composition pattern) and the checker.
