# Reference: composition contract, sync math, and worked example

## HyperFrames authoring contract (essentials)

- Root element: `<div id="root" data-composition-id="main" data-start="0" data-duration="<total>" data-width="1920" data-height="1080">`
- Each scene is a child `<div id="sceneN" class="clip center" data-start="..." data-duration="..." data-track-index="1">` with `position:absolute; inset:0; overflow:hidden` (the `.clip` rule).
- One `<audio>` per scene, on its own track:

```html
<audio id="vo1" src="assets/vot1.mp3" data-start="0.25" data-duration="1.40"
       data-track-index="5" data-volume="1"></audio>
```

- Timeline: `const tl = gsap.timeline({ paused: true });` … register with `window.__timelines["main"] = tl;`
- GSAP seek-safe properties ONLY: `opacity, x, y, scale, scaleX, scaleY, rotation, width, height, visibility`. Use `tl.fromTo(sel, fromVars, toVars, absoluteTime)`.
- Every exit tween needs a hard-kill `tl.set(sel, { opacity: 0 }, <scene_end>)` at the scene boundary.
- CJK fonts need `@font-face { font-family: "PingFang SC"; src: local("PingFang SC"); }` style declarations or check fails.
- Useful docs offline: `npx hyperframes docs data-attributes | gsap | compositions`.

## Sync formula (per scene i)

```
audio_start[i] = scene_start[i] + 0.25
speech_end[i]  = audio_start[i] + d[i]          # d = trimmed audio duration
scene_end[i]   = speech_end[i] + 0.05 + gap[i]  # gap = 0.3-0.6s to next scene
scene_start[i+1] = scene_end[i]
exit_anim_start[i] = speech_end[i]
total = speech_end[last] + 0.6
```

In-scene element reveals should land when their keyword is spoken, e.g. if "12 套主题 / 1020 个版式 / 8576 个控件" is one 3.7s narration segment starting at audio_start, stagger the three stat cards at roughly audio_start+0, +0.75, +2.2 (estimated by word position; ±0.3s is imperceptible).

## Worked example (the dashi-promo case)

Script and measured (rate +20%, trimmed) durations:

| Scene | Text | d[i] | audio_start | scene window |
|---|---|---|---|---|
| 1 | 还在手搓 PPT 吗？ | 1.40 | 0.25 | 0.00–2.00 |
| 2 | 大师 PPT Skill，每一页自带编辑控制台。 | 3.24 | 2.25 | 2.00–5.80 |
| 3 | 十二套主题，一千零二十个版式，八千五百多个可调控件。 | 3.66 | 6.05 | 5.80–10.00 |
| 4 | 一行命令，马上开始。 | 1.48 | 10.25 | 10.00–12.40 |

Total = 12.4s. Verification windows extracted from the final MP4 with silencedetect: 0.30–1.60, 2.30–5.45, 6.10–9.67, 10.30–11.68 — each inside its scene.

Scene HTML skeleton:

```html
<div id="scene2" class="clip center" data-start="2.0" data-duration="3.8" data-track-index="1">
  <!-- badge, title, subtitle, cards -->
</div>
```

Timeline excerpt showing entry-while-speaking, exit-at-speech-end:

```js
tl.fromTo("#s2Title", { opacity: 0, scale: 0.72 }, { opacity: 1, scale: 1, duration: 0.6, ease: "back.out(1.6)" }, 2.15);
// ... entries ...
tl.to("#s2Title", { opacity: 0, scale: 0.85, duration: 0.33, ease: "power2.in" }, 5.47);  // speech ends 5.49
tl.set("#s2Title", { opacity: 0 }, 5.8);  // hard kill at scene boundary
```

## BGM: half-volume rule (worked numbers)

The requirement "BGM volume = half of narration volume" fails if implemented as a bare `data-volume="0.5"` — masters differ. Measured on this machine: bundled `bgm-source.mp3` mean −10.4 dB; Edge TTS VO mean −23.0 dB. At 0.5 gain the BGM (−16.7 dB mean) would be ~6 dB LOUDER than the narration.

Fix: pre-gain the BGM so its full-scale mean equals the VO mean. Then `data-volume="0.5"` (−6 dB at playback) lands the music at exactly half the narration's amplitude:

```
gain_db = vo_mean_db − bgm_mean_db        # e.g. −23.0 − (−10.4) = −12.6 dB
```

```bash
# prep: loop-if-short, trim to TOTAL, pre-gain, 0.8s fade-in / 1.2s fade-out
ffmpeg -y -stream_loop -1 -i assets/bgm-src.mp3 -t $TOTAL \
  -af "volume=${GAIN}dB,afade=t=in:st=0:d=0.8,afade=t=out:st=$(python3 -c "print($TOTAL-1.2)"):d=1.2" \
  -c:a libmp3lame -q:a 2 assets/bgm.mp3

# THEN measure the prepped file and correct if needed (mandatory):
ffmpeg -i assets/bgm.mp3 -af volumedetect -f null - 2>&1 | grep mean_volume
```

Two measured facts (gbro-cover-design case, 2026-08-28):

1. **`data-volume="0.5"` renders as exactly −6.0 dB** — verified with a controlled A/B test (same sine-wave file embedded at volume 1.0 and 0.5 in one composition; output means −33.1 / −39.1 dB). HyperFrames is NOT the problem. Never "fix" the mix by guessing a volume-mapping constant.
2. **The prepped file runs ~1-1.5 dB below the predicted mean** (fades + mp3 re-encode + loop point). Measure `assets/bgm.mp3` after prep and adjust GAIN by the difference (one re-run) until file mean ≈ VO mean.

```html
<!-- embed: own track, spans the whole composition -->
<audio id="bgm" src="assets/bgm.mp3" data-start="0" data-duration="<TOTAL>"
       data-track-index="6" data-volume="0.5"></audio>
```

Verification trap: **music is dynamic**. In the gbro project the BGM at the 3.9-4.45s verification window sat 5.6 dB below its whole-file mean, so a single-window gap-vs-speech reading showed a 10+ dB delta even though the global mix was exactly 6 dB under. The authoritative level check is prepped-file mean ≈ VO mean (done at prep time, no render needed); single-window readings in the final MP4 can legitimately swing ±6 dB. Only treat the mix as broken if a gap window is silent or the delta exceeds ~12 dB. If a `--bgm` file is quieter than the VO, the same formula applies with a positive gain — but never push the BGM max_volume above −3 dB after gain (clipping risk).

## Known pitfalls

1. **Bundled Chrome download crawls** (~20KB/s from Google). Always `export HYPERFRAMES_BROWSER_PATH` to the system Chrome before rendering.
2. **edge-tts `NoAudioReceived`** on flaky networks — the helper script retries 4× and validates file size > 5KB.
3. **MP3 container duration > decoded duration** — after trimming, probe with ffprobe and trust the checker's `clip_media_fit` correction over the container number.
4. **Rate above +30% sounds bad** — cut script text instead.
5. **Untrimmed TTS has ~0.3-0.5s leading silence** which would break the 0.25s offset math — always trim before measuring.
6. **Black bottom bar (probabilistic)** — static-frame dedup (on by default) reuses a capture taken mid GPU-layer rebuild → an ~87px black band spanning seconds; multi-worker capture adds stray single black frames. Always render with `HF_STATIC_DEDUP=false hyperframes render -w 1`, then run scripts/verify_render.py's BAND check before delivery. The bug is timing-dependent — never trust defaults alone.
7. **Per-frame verification scans are O(n²)** — one ffmpeg per frame re-decodes from frame 0: measured 0.42 s/frame early, 1.27 s/frame late → ~12 min for a 28s/838-frame video. The single-pass band scan in scripts/verify_render.py (one decode, analyze raw bytes in Python) does the same job in ~2 s. Never hand-roll the per-frame loop.
8. **`npm run` / `npx hyperframes@<version>` costs ~34 s per call** (registry resolution over the network, plus occasional `ECOMPROMISED lock` failures) vs ~4 s for the global `hyperframes` CLI. Always call the global CLI directly for lint/check/render.
9. **`hyperframes init` fetches over the network (~1.6 min)** — scaffold by copying the skill's cached `assets/project-template/` instead.
10. **中文多音字会误读（写口播文案时必查）**：「一行命令 / 一行代码」的「行」读 **háng**（表数量"一条"），Edge TTS 会误读成 xíng（"可以"义）。首选修法：**同音字替代**——VO 文本里把「行」写成同音的「航」（"一航命令"），听感与 háng 完全一致，屏幕文案仍写「一行命令」不受影响。备选：SSML phoneme 标注。不要改成「一条命令」这类不通顺的换词。同类高危多音字过一遍再生成：「处理」chǔlǐ、「重量」zhòngliàng（非 chóng）、「银行」yínháng、「长度」chángdù、「长大」zhǎngdà。
