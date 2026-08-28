---
name: github-guide-video
description: Make a sub-30-second promotional/recommendation video for a GitHub repository using HyperFrames (HTML-rendered video) with Edge TTS voiceover, with visuals precisely synced to narration. Use when the user provides a GitHub repo link and asks for a promo/recommendation/intro video, with optional --voice to pick narration style (e.g. sunny male, gentle female).
---

# GitHub Guide Video

Turn a GitHub repo into a ≤30s narrated promo video. Params:

- `--github <url>` (required): the GitHub repository link
- `--voice <style>` (optional): narration style, see Voice table below. Default: Yunxi 阳光男声 (zh-CN-YunxiNeural)

## Prerequisites (verify once per session)

```bash
node --version        # >= 22
ffmpeg -version       # any recent version
which hyperframes     # if missing: npm install -g hyperframes
ls ~/Library/Python/3.12/bin/edge-tts   # if missing: pip3 install --user edge-tts
```

Render MUST use the system Chrome (bundled headless Chrome downloads from a slow Google host):

```bash
export HYPERFRAMES_BROWSER_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

(On other machines, use the local Chrome/Chromium path.)

## Workflow

### Step 1: Collect repo facts

Fetch the README with a hard timeout (GitHub web pages often stall; raw content usually works):

```bash
curl -sL --max-time 60 https://raw.githubusercontent.com/<owner>/<repo>/main/README.md
# try /master/ if main 404s
```

Distill 4-6 selling points: what it is, key numbers/features, install command, repo URL. The video can only carry ~3 numbers and ~1 command — pick the strongest.

### Step 2: Write the narration script

Structure the video as 4-6 scenes. For a 30s video the narration budget is 25-28s of speech (leave breathing room). Scene template that works:

1. Hook (question/pain point) — 2-4s
2. Product name + one-line value — 4-6s
3. 1-2 feature/stat scenes — 8-14s total
4. Install command + repo URL (CTA) — 4-6s

Rules: write the script FIRST, then build visuals around it — never the reverse. Numbers in the script must match numbers shown on screen. For acronyms spell out pauses ("P P T") so TTS reads them letter-by-letter when appropriate.

### Step 3: Generate TTS per scene

One audio file per scene (never one file for the whole video — you need per-scene durations for alignment). Use the helper script:

```bash
bash scripts/make_vo.sh "<voice>" "+20%" "<text>" assets/vo1.mp3
# prints the trimmed duration in seconds on the last line
```

Retry policy is built in (network flakiness causes `NoAudioReceived`). If total speech exceeds the budget, raise the rate by +5% steps (sweet spot +15% to +25%; above +30% sounds rushed — cut script text instead).

### Step 4: Compute the timeline from measured audio

For each scene i with audio duration `d[i]` (from Step 3 output):

- `audio_start[i] = scene_start[i] + 0.25` — voice begins 0.25s after scene appears
- `scene_end[i] = audio_start[i] + d[i] + 0.05` then add a 0.3-0.6s gap before the next scene
- exit animations start exactly at `audio_start[i] + d[i]`
- total duration = last audio end + ~0.6s tail

Record the plan as a table before writing any HTML. A worked example with all math is in [reference.md](reference.md).

### Step 5: Author the composition

```bash
cd <workspace> && hyperframes init <repo-name>-promo --example blank
```

Write `index.html`: scenes as `<div class="clip" data-start data-duration>` with a paused GSAP timeline registered to `window.__timelines`, and one `<audio>` per scene with `data-start`/`data-duration` set to the measured values. Authoring contract and the exact alignment example: [reference.md](reference.md).

### Step 6: Check and fix

```bash
npm run check
```

Fix every error before rendering. The three recurring ones:

- `gsap_exit_missing_hard_kill` → add `tl.set("#id", { opacity: 0 }, <scene_end>)` after each exit tween
- `font_family_without_font_face` → add `@font-face { font-family: "..."; src: local("..."); }` for each CJK/system font used
- `clip_media_fit` (audio slot vs decoded length) → set `data-duration` to the value the checker reports

### Step 7: Render

```bash
export HYPERFRAMES_BROWSER_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HF_STATIC_DEDUP=false hyperframes render -w 1 -o renders/<name>.mp4
```

Mandatory flags, learned the hard way:

- `HF_STATIC_DEDUP=false` — the default-on static-frame dedup can reuse a capture taken mid GPU layer rebuild, producing full-width black bars at the bottom (~87px tall, lasting seconds). Multi-worker capture (`-w 1` off) adds stray single black frames from capture races. Dedup off + single worker rendered 625/625 clean frames at essentially the same speed (~2.3 min for a 21s video). This bug is probabilistic — another project may render clean with defaults, so never rely on defaults; always set these flags and always run the Step 8 bottom-band scan.
- If `npm run render` fails with npm `ECOMPROMISED "Lock compromised"` (pinned npx script), call the global `hyperframes` CLI directly as shown above.

### Step 8: Verify audio-visual sync (mandatory)

Extract speech windows and compare against scene boundaries:

```bash
ffmpeg -i renders/<output>.mp4 -af "silencedetect=noise=-35dB:d=0.3" -f null - 2>&1 | grep silence_
```

Each speech window must fall inside its intended scene (started ~0.25s after scene start, ended ≤0.1s before scene exit begins). Also extract 1 key frame per scene (`ffmpeg -vf "select='eq(n,<frame>)'"`) and view them. Then scan every frame's bottom band for black-bar corruption (dedup artifact — mandatory even when Step 7 flags were used):

```bash
python3 -c "
import subprocess
V='renders/<output>.mp4'
dark=[n for n in range(0,625) if (lambda o: o and sum(o)/len(o)<150)(subprocess.run(['ffmpeg','-i',V,'-vf',f'select=eq(n\\\\,{n}),crop=1920:10:0:1070','-frames:v','1','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True).stdout)]
print('dark frames:',len(dark),dark[:20])"
```

Zero dark frames required. Only then deliver the MP4 to the outputs folder.

## Voice table

| --voice value | Edge TTS voice | Character |
|---|---|---|
| 阳光 / 男声 / sunny / male | zh-CN-YunxiNeural | young, energetic — default, suits tech promos |
| 温柔 / 女声 / gentle / female | zh-CN-XiaoxiaoNeural | warm, natural, universal |
| 沉稳 / steady | zh-CN-YunjianNeural | deep, authoritative |
| 磁性 / 深沉 | zh-CN-YunyangNeural | documentary-style gravitas |
| 少女 / lively | zh-CN-XiaoyiNeural | bubbly, youthful |
| english / en | en-US-GuyNeural (male) / en-US-JennyNeural (female) | English narration |

If the user names a style not in the table, pick the closest and say which voice was used.

## Deliverables

Final MP4 copied to the session outputs folder and presented to the user, plus a one-line summary of total duration and voice used.
