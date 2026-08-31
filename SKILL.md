---
name: github-guide-video
description: Make a sub-30-second promotional/recommendation video for a GitHub repository using HyperFrames (HTML-rendered video) with Edge TTS voiceover and background music (BGM at half the narration volume), with visuals precisely synced to narration. Use when the user provides a GitHub repo link and asks for a promo/recommendation/intro video, with optional --voice to pick narration style (e.g. sunny male, gentle female), --bgm to pick background music, and --workflow to pick a HyperFrames workflow (default product-launch-video).
---

# GitHub Guide Video

Turn a GitHub repo into a ≤30s narrated promo video. Params:

- `--github <url>` (required): the GitHub repository link
- `--voice <style>` (optional): narration style, see Voice table below. Default: Yunxi 阳光男声 (zh-CN-YunxiNeural)
- `--bgm <path>` (optional): background music file. Default: the skill's bundled `assets/bgm-source.mp3`. BGM volume is always half the narration volume (see Step 5b)
- `--workflow <name>` (optional): HyperFrames workflow (route) that shapes scene structure and visual language. Default: `product-launch-video`. See Workflow table below. Whatever route is chosen, the skill's own hard caps stay: ≤30s total, Edge TTS narration, half-volume BGM, sync verification

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

## Workflow table (--workflow)

HyperFrames ships 10 workflows (routes). Meaningful for a repo link input:

| Value | Fits a repo promo? | Style |
|---|---|---|
| `product-launch-video` (default) | ✅ best | marketing angle: positioning, selling points, install CTA; site capture optional |
| `motion-graphics` | ✅ | short design-led unit, kinetic type, stat hits, no-narration feel (narration kept short) |
| `faceless-explainer` | ✅ | explain the topic with invented visuals, teaching tone |
| `general-video` | ✅ | anything custom — the fallback |
| `slideshow` | ✅ (if user wants a deck) | navigable deck feel instead of a linear video |
| `pr-to-video` | ✅ (needs a PR reference) | explain one PR / code change instead of the whole repo |

Not valid for a bare repo link (require other inputs — if requested, tell the user what's missing): `embedded-captions` and `talking-head-recut` (need existing footage), `music-to-video` (needs a music track as the driver), `remotion-to-hyperframes` (needs Remotion source).

If the user names a workflow not in the table, pick the closest and say which was used. The route only changes scene structure, script tone, and visual language — the pipeline (Steps 1, 3-8) is identical.

## Workflow

### Step 1: Collect repo facts

Fetch the README with a hard timeout (GitHub web pages often stall; raw content usually works). Try raw.githubusercontent first, then fall back to the jsdelivr CDN mirror (much faster on slow GitHub connections):

```bash
curl -sL --max-time 30 https://raw.githubusercontent.com/<owner>/<repo>/main/README.md
# fallbacks, in order:
curl -sL --max-time 30 https://cdn.jsdelivr.net/gh/<owner>/<repo>@main/README.md
curl -sL --max-time 30 https://raw.githubusercontent.com/<owner>/<repo>/master/README.md
# last: jsdelivr @master
```

Distill 4-6 selling points: what it is, key numbers/features, install command, repo URL. The video can only carry ~3 numbers and ~1 command — pick the strongest.

### Step 2: Write the narration script

Structure the video as 4-6 scenes. For a 30s video the narration budget is 25-28s of speech (leave breathing room). Default scene template (product-launch-video):

1. Hook (question/pain point) — 2-4s
2. Product name + one-line value — 4-6s
3. 1-2 feature/stat scenes — 8-14s total
4. Install command + repo URL (CTA) — 4-6s

Adapt the template to the chosen --workflow: `motion-graphics` compresses to 3-4 scenes with punchier, shorter narration; `faceless-explainer` replaces the hook with a definition ("X 是…") and spends more time per concept; `pr-to-video` becomes problem → change walkthrough → before/after. Keep the ≤30s cap and the sync rules regardless.

Rules: write the script FIRST, then build visuals around it — never the reverse. Numbers in the script must match numbers shown on screen. For acronyms spell out pauses ("P P T") so TTS reads them letter-by-letter when appropriate.

### Step 3: Generate TTS per scene

One audio file per scene (never one file for the whole video — you need per-scene durations for alignment). Use the helper script, and generate ALL scenes in one bash invocation (network round trips dominate; don't issue one Bash call per segment):

```bash
bash {skill_dir}/scripts/make_vo.sh "<voice>" "+20%" "<scene1 text>" assets/vo1.mp3
bash {skill_dir}/scripts/make_vo.sh "<voice>" "+20%" "<scene2 text>" assets/vo2.mp3
# ... each prints the trimmed duration in seconds on the last line
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

Scaffold from the skill's cached blank template (instant) instead of `hyperframes init` (~1.6 min of network fetch):

```bash
cp -R {skill_dir}/assets/project-template <workspace>/<repo-name>-promo
cd <repo-name>-promo && mkdir -p assets renders
# fallback if the template is missing: hyperframes init <repo-name>-promo --example blank
```

Write `index.html`: scenes as `<div class="clip" data-start data-duration>` with a paused GSAP timeline registered to `window.__timelines`, and one `<audio>` per scene with `data-start`/`data-duration` set to the measured values. Authoring contract and the exact alignment example: [reference.md](reference.md).

### Step 5b: Background music (always on)

BGM is a core part of the deliverable, not an option. Source: `--bgm` if given, else the skill's bundled `assets/bgm-source.mp3` (copy it into the project's `assets/`).

**Do NOT just embed with `data-volume="0.5"`.** Typical BGM masters are hotter than Edge TTS speech (measured: bgm −16.7 dB mean at 0.5 gain vs VO −23 dB mean), so a bare half-gain makes music LOUDER than narration. Pre-gain the BGM first so that, at half gain, it sits exactly 6 dB (half amplitude) below the narration:

```bash
# 1. measure levels (mean_volume) of VO files and the BGM source
ffmpeg -i assets/vo1.mp3 -af volumedetect -f null - 2>&1 | grep mean_volume
ffmpeg -i assets/bgm-src.mp3 -af volumedetect -f null - 2>&1 | grep mean_volume

# 2. gain = vo_mean_db - bgm_mean_db  (e.g. -23.0 - (-10.4) = -12.6 dB)
#    loop if short, trim to TOTAL, fade in/out, write prepped bgm
ffmpeg -y -stream_loop -1 -i assets/bgm-src.mp3 -t $TOTAL \
  -af "volume=${GAIN}dB,afade=t=in:st=0:d=0.8,afade=t=out:st=$(python3 -c "print($TOTAL-1.2)"):d=1.2" \
  -c:a libmp3lame -q:a 2 assets/bgm.mp3

# 3. MANDATORY: measure the PREPPED file, not the prediction — fades + mp3
#    re-encode + loop-point cost ~1-1.5 dB. If it deviates from vo_mean by
#    more than 0.5 dB, adjust GAIN by the difference and re-run step 2 once.
ffmpeg -i assets/bgm.mp3 -af volumedetect -f null - 2>&1 | grep mean_volume
```

`data-volume="0.5"` itself is exactly −6 dB in the render (verified empirically with a sine-wave A/B test: volume 1.0 → identical level, volume 0.5 → exactly −6.0 dB). The only things that break the half-volume target are (a) the ~1-1.5 dB prep loss above, and (b) trusting a single-window measurement in Step 8 (see below). No second-round render calibration is needed if step 3 confirms the prepped file mean ≈ VO mean.

4. Embed alongside the VO elements (own track, full duration):

```html
<audio id="bgm" src="assets/bgm.mp3" data-start="0" data-duration="<TOTAL>"
       data-track-index="6" data-volume="0.5"></audio>
```

With the pre-gain, `data-volume="0.5"` lands the BGM at literally half the VO's amplitude. Fix any `clip_media_fit` warning on the bgm element the same way as VO slots.

### Step 6: Check and fix

Always call the GLOBAL `hyperframes` CLI directly — never `npm run check` / `npm run render` / `npx hyperframes@…`. The pinned-npm-script path resolves the npm registry over the network on EVERY call (~34 s overhead each, plus `ECOMPROMISED lock` errors); the global CLI starts in ~4 s.

Iterate with fast lint (~10 s); run the full check (~60 s, launches Chrome for runtime validation) only ONCE, right before rendering:

```bash
hyperframes lint    # iterate here until 0 errors
hyperframes check   # once, final gate before render
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

### Step 8: Verify the render (mandatory — use the script, never a per-frame loop)

With BGM mixed in, `silencedetect` can no longer isolate speech windows, so verify against the known timeline table from Step 4. Run all checks with the bundled script (single decode pass, ~10 s total):

```bash
python3 {skill_dir}/scripts/verify_render.py renders/<output>.mp4 \
  --gap-start <a known VO gap start> --speech-start <a known speech start> \
  --frames <one frame per scene, comma-separated> --outdir /tmp/vframes
```

It checks, and prints PASS/FAIL per item: (1) BAND — every frame's bottom 10px band for the dedup black-bar artifact (mandatory even with Step 7 flags; 0 dark frames required — but note the absolute threshold misfires on intentionally dark designs: if BAND fails on a dark scene, re-check with the relative method — bottom band vs a reference row 40-50px higher in the SAME frame, a drop >8 luma points is a real bar, equal levels is just dark design); (2) SILENCE — no ≥0.3s silence at −50 dB anywhere (BGM present throughout); (3) VOLUME — a known VO gap vs a known speech window should differ by ~6 dB and the gap must not be silent. IMPORTANT: music is dynamic — any single 0.5s window can sit ±6 dB off the BGM's whole-file mean, so a measured delta anywhere in ~4-12 dB is consistent with a CORRECT mix. The authoritative level check is the Step 5b one (prepped bgm.mp3 file mean ≈ VO file mean); do NOT re-calibrate the render gain from a single window reading; (4) FRAMES — extracts the listed frames as PNGs; VIEW them (one per scene) before delivery. Exit code 0 = all passed.

Do NOT hand-roll a per-frame scan with one ffmpeg per frame — that re-decodes the video from frame 0 every time (O(n²)): measured ~12 min for a 28s video vs ~2 s for the script's single pass.

Only when everything passes, deliver the MP4 to the outputs folder.

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

## Timing budget (measured on this machine)

Normal total for a ≤30s video is now ~6-8 min end to end. Know what each phase should cost so you can spot a stall:

| Phase | Normal | Was / pitfall |
|---|---|---|
| README fetch | ≤30 s | stalls minutes on GitHub — use the jsdelivr fallback |
| Scaffold | instant | `hyperframes init` was ~1.6 min — use the cached template |
| TTS (4-6 segments) | 30-90 s | network flaky; retries built into make_vo.sh |
| lint iterations | ~10 s each | full `check` is 60 s — lint while iterating, check once |
| Render (via global CLI) | 2-2.5 min | `npm run render`/npx adds ~34 s of registry resolution per call |
| verify_render.py | ~10 s | a hand-rolled per-frame scan is O(n²) — ~12 min for 28s video |

While the render runs in the background, prepare the Step 4 timeline table's gap/speech timestamps for the verification command instead of sleeping.

## Deliverables

Final MP4 copied to the session outputs folder and presented to the user, plus a one-line summary of total duration, voice used, and BGM source (default or --bgm path).
