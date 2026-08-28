#!/usr/bin/env bash
# make_vo.sh <edge-tts-voice> <rate> <text> <output.mp3>
# Generates one narration segment, retries on network failure, trims leading/
# trailing silence, prints the trimmed duration (seconds) on the last line.
# Usage: bash scripts/make_vo.sh "zh-CN-YunxiNeural" "+20%" "一行命令，马上开始。" assets/vo1.mp3
set -euo pipefail

VOICE="${1:?usage: make_vo.sh <voice> <rate> <text> <output.mp3>}"
RATE="${2:?missing rate, e.g. +20%}"
TEXT="${3:?missing text}"
OUT="${4:?missing output path}"

EDGE_TTS="$HOME/Library/Python/3.12/bin/edge-tts"
if [ ! -x "$EDGE_TTS" ]; then
  # fall back to whatever is on PATH
  EDGE_TTS="edge-tts"
fi
command -v "$EDGE_TTS" >/dev/null 2>&1 || {
  echo "edge-tts not found. Install: pip3 install --user edge-tts" >&2
  exit 1
}

TMP="${OUT%.mp3}_raw.mp3"
mkdir -p "$(dirname "$OUT")"

# Generate with retry: network flakiness causes NoAudioReceived / empty files.
ok=0
for attempt in 1 2 3 4; do
  if "$EDGE_TTS" --voice "$VOICE" --rate="$RATE" --text "$TEXT" --write-media "$TMP" 2>/dev/null; then
    size=$(stat -f%z "$TMP" 2>/dev/null || stat -c%s "$TMP" 2>/dev/null || echo 0)
    if [ "${size:-0}" -gt 5000 ]; then ok=1; break; fi
  fi
  echo "retry $attempt for $OUT" >&2
  sleep 2
done
if [ "$ok" -ne 1 ]; then
  echo "TTS failed after 4 attempts: $TEXT" >&2
  exit 2
fi

# Trim leading/trailing silence (keep 0.05s pads) so measured duration is speech.
ffmpeg -y -v error -i "$TMP" \
  -af "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse" \
  -c:a libmp3lame -q:a 2 "$OUT"
rm -f "$TMP"

ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
