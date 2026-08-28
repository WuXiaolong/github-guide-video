#!/usr/bin/env python3
"""Single-pass render verification for github-guide-video.

Replaces the old per-frame bottom-band scan (which launched one ffmpeg per
frame and re-decoded from frame 0 each time — O(n²), ~12 min for a 30s video)
with one decode pass (~2 s total). Also runs the silence and BGM/VO volume
checks and optional key-frame extraction in the same invocation.

Usage:
  python3 scripts/verify_render.py renders/out.mp4 \
      [--gap-start 2.9 --gap-dur 0.5 --speech-start 3.1 --speech-dur 0.5] \
      [--frames 45,200,430] [--outdir /tmp/frames]

Checks:
  1. BAND   — every frame's bottom 10px band brightness (detects the dedup
              black-bar artifact). Verdict: dark frame count must be 0.
  2. SILENCE— no >=0.3s silence below -50 dB anywhere (BGM must be present).
  3. VOLUME — if --gap-start/--speech-start given: mean_volume of a known
              VO gap vs a known speech window; speech should be ~6 dB hotter
              and the gap must not be silent.
  4. FRAMES — optional: extract listed frame numbers as PNGs for visual check.

Exit code 0 = all checks passed; 1 = failure. Verdicts print as NAME:PASS /
NAME:FAIL lines plus detail.
"""
import argparse
import re
import subprocess
import sys


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def band_scan(video, width, height):
    """One decode pass; analyze the bottom 10px band of every frame."""
    band_h = 10
    crop = f"crop={width}:{band_h}:0:{height - band_h}"
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", video, "-vf", crop,
         "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True)
    raw = proc.stdout
    frame_bytes = width * band_h
    n = len(raw) // frame_bytes
    if n == 0:
        return "FAIL", "no frames decoded", 0
    dark = []
    for i in range(n):
        chunk = raw[i * frame_bytes:(i + 1) * frame_bytes]
        if sum(chunk) / frame_bytes < 150:
            dark.append(i)
    if dark:
        return "FAIL", f"dark frames: {len(dark)} -> {dark[:20]}", n
    return "PASS", f"{n} frames clean", n


def silence_scan(video):
    proc = run(["ffmpeg", "-i", video, "-af",
                "silencedetect=noise=-50dB:d=0.3", "-f", "null", "-"])
    silences = re.findall(r"silence_start: ([0-9.]+)", proc.stderr)
    if silences:
        return "FAIL", f"silence at: {silences[:10]}"
    return "PASS", "no silence >=0.3s (BGM present throughout)"


def seg_mean_volume(video, start, dur):
    proc = run(["ffmpeg", "-ss", str(start), "-t", str(dur), "-i", video,
                "-af", "volumedetect", "-f", "null", "-"])
    m = re.search(r"mean_volume: ([-0-9.]+) dB", proc.stderr)
    return float(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--gap-start", type=float)
    ap.add_argument("--gap-dur", type=float, default=0.5)
    ap.add_argument("--speech-start", type=float)
    ap.add_argument("--speech-dur", type=float, default=0.5)
    ap.add_argument("--frames", help="comma-separated frame numbers to extract")
    ap.add_argument("--outdir", default="/tmp/verify_frames")
    args = ap.parse_args()

    failures = 0

    v, detail, _ = band_scan(args.video, args.width, args.height)
    print(f"BAND:{v} {detail}")
    failures += v == "FAIL"

    v, detail = silence_scan(args.video)
    print(f"SILENCE:{v} {detail}")
    failures += v == "FAIL"

    if args.gap_start is not None and args.speech_start is not None:
        gap = seg_mean_volume(args.video, args.gap_start, args.gap_dur)
        speech = seg_mean_volume(args.video, args.speech_start, args.speech_dur)
        if gap is None or speech is None:
            print("VOLUME:FAIL could not read mean_volume")
            failures += 1
        elif gap < -50:
            print(f"VOLUME:FAIL gap at {args.gap_start}s is silent ({gap} dB) — BGM missing")
            failures += 1
        else:
            delta = speech - gap
            ok = 3 <= delta <= 10  # ~6 dB expected; tolerate measurement spread
            print(f"VOLUME:{'PASS' if ok else 'FAIL'} "
                  f"gap {gap} dB vs speech {speech} dB (delta {delta:.1f} dB, expect ~6)")
            failures += not ok

    if args.frames:
        import os
        os.makedirs(args.outdir, exist_ok=True)
        sel = "+".join(f"eq(n\\,{f})" for f in args.frames.split(","))
        run(["ffmpeg", "-y", "-v", "error", "-i", args.video,
             "-vf", f"select='{sel}',scale=960:-1", "-vsync", "vfr",
             f"{args.outdir}/frame_%d.png"])
        print(f"FRAMES:PASS extracted to {args.outdir}/frame_*.png — view them")

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
