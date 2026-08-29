<p align="center">
  <a href="./README_zh.md"><img alt="中文" src="https://img.shields.io/badge/语言-中文-111111"></a>
  <a href="./README.md"><img alt="English" src="https://img.shields.io/badge/Language-English-111111"></a>
</p>

# github-guide-video · GitHub Repo Promo Video Generator

Drop in a GitHub link, wait a few minutes, and get a **sub-30-second promo video with AI voiceover and background music** (1080p MP4). Visuals are synced line-by-line to the narration — perfect for X/Twitter, Bilibili, Reddit, or embedding in your project's README.

## What It Does

In one sentence: **you give it a repo link, it gives you back a narrated promo video.**

- 🎬 Visuals rendered with [HyperFrames](https://hyperframes.heygen.com) — "HTML that becomes video." It designs a hook, selling points, stats, and CTA tailored to your repo
- 🎙️ Voiceover generated with Microsoft Edge TTS — "Yunxi" sunny male voice by default, with 5 more styles to choose from
- 🎵 Background music added automatically, or bring your own
- ✅ Every output passes an automated audio-visual sync check: narration timing, music ratio, frame integrity

## Installation (one time)

Repo URL: **https://github.com/WuXiaolong/github-guide-video**

### Option 1:

Just tell your agent: `Install the skill at https://github.com/WuXiaolong/github-guide-video` — it handles the rest.

### Option 2:

Open the repo and click:

```text
Code → Download ZIP
```

Unzip, rename the folder to `github-guide-video`, and copy it into your agent's skills directory.

Codex skills directory: ~/.codex/skills
WorkBuddy skills directory: ~/.workbuddy/skills
QwenWork skills directory: ~/.qwenworkcn/skills/

**Restart your agent** (or start a new session) afterwards so the skill loads. It will then appear in your skills list.

## How to Use (really simple)

**Simplest usage** — one sentence:

```
Use github-guide-video to make a promo video for https://github.com/xxx/yyy
```

Wait 6-8 minutes. That's it — nothing else for you to do.

**Pick a voice**:

```
--voice gentle female
```

Available voices:

| --voice value | Voice | Character |
|---|---|---|
| `sunny male` (default) | Yunxi | young, energetic — suits tech promos |
| `gentle female` | Xiaoxiao | warm, natural, universal |
| `steady` | Yunjian | deep, authoritative |
| `magnetic` | Yunyang | documentary-style gravitas |
| `lively` | Xiaoyi | bubbly, youthful |
| `english` | en-US male/female | full English narration |

**Use your own background music**:

```
--bgm /path/to/your-music.mp3
```

If omitted, the skill's bundled bgm-source.mp3 is used.

**Change the video style (workflow)**:

```
--workflow motion-graphics
```

The workflow determines the narrative structure and visual language. The default is `product-launch-video` (pain point → selling points → install CTA), which fits most repos. Options:

| Workflow | Style | When to pick it |
|---|---|---|
| `product-launch-video` (default) | Product launch | Positioning + selling points; the most general choice |
| `motion-graphics` | Motion graphics | Shorter, flashier, fast-paced |
| `faceless-explainer` | Explainer | Teaching tone: what it is and how to use it |
| `general-video` | Custom | Anything goes — the fallback |
| `slideshow` | Slideshow | Deck-like, paginated feel |
| `pr-to-video` | PR walkthrough | Explain one PR / code change, not the whole repo (requires a PR link) |

> HyperFrames ships 10 workflows in total. The other 4 (embedded captions, talking-head recut, music-to-video, Remotion porting) need existing footage or music files, so they aren't suitable for the "just drop a repo link" flow and aren't listed here.

## What You Get

A single `.mp4` file (1920×1080, 30fps, under 30 seconds), typically structured as:

| Section | Visual | Narration |
|---|---|---|
| Opening | Pain-point question, e.g. "Still hand-rolling X?" | Hook the viewer |
| Middle | Product name + selling points / stat cards | What this repo is, why it's strong |
| Ending | Install command + repo URL | How to use it, where to find it |

## What Happens Under the Hood (optional reading)

You don't need to know any of this — the tool handles it all — but here's why it's reliable:

1. **Research**: reads the repo's README, distills the 3 most compelling numbers and 1 command (a 30s video can't carry more)
2. **Script first, visuals second**: each narration segment is generated first, and its measured duration drives the visual pacing — guaranteeing "what's spoken is what's shown"
3. **TTS**: per-scene Edge TTS calls with automatic retries on flaky networks
4. **Mixing**: background music is loudness-aligned first, then set to half the narration volume (a naive half-gain would let the music drown the voice — a lesson learned the hard way)
5. **Render + health check**: the browser renders frame-by-frame to MP4, then automated checks verify frame integrity, continuous music presence, and volume ratio — only a clean pass gets delivered

## FAQ

**Q: Do I need to install anything first?**
Usually not. The skill auto-checks Node.js 22+, FFmpeg, the HyperFrames CLI, and Edge TTS, and tells you the one command to run if something's missing.

**Q: Why does rendering take a few minutes?**
The video is "filmed" frame-by-frame by a browser (~900 frames for 30 seconds) — that's the cost of precise sync. It has been through one round of deep optimization (from 20+ minutes down to 6-8).

**Q: I don't like the script.**
Just say so — "change the second line to X" or "use the star count instead" — and it re-renders in minutes.

**Q: Does it work with English repos?**
Yes. English repo content still gets a Chinese voiceover by default; add `--voice english` for a fully English narration.

## File Layout (for developers/contributors)

```
github-guide-video/
├── README.md              # English docs
├── README_zh.md           # Chinese docs
├── SKILL.md               # Core instructions: the full 8-step workflow for the AI agent
├── reference.md           # Advanced reference: authoring contract, sync formulas, pitfalls
├── .skill-metadata.yaml   # Recommended queries (bilingual)
├── assets/
│   ├── bgm-source.mp3     # Default background music
│   └── project-template/  # Cached blank project template (skips network init)
└── scripts/
    ├── make_vo.sh         # TTS generator: auto-retry + silence trim + exact duration output
    └── verify_render.py   # Render health check: black bars / silence / volume ratio / key frames, single pass
```
