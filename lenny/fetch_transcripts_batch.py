#!/usr/bin/env python3
"""Batch fetch missing transcripts using yt-dlp CLI with retries and cooldown."""
import json
import subprocess
import time
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VIDEOS_JSON = SCRIPT_DIR / "videos.json"
TRANSCRIPTS_DIR = SCRIPT_DIR / "transcripts"
DELAY_BETWEEN = 15


def clean_srt_to_text(srt_content):
    """Convert SRT/VTT subtitle content to plain text."""
    lines = srt_content.split('\n')
    texts = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r'^\d+$', line):
            continue
        if re.match(r'\d{2}:\d{2}', line):
            continue
        if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
            continue
        line = re.sub(r'<[^>]+>', '', line)
        line = re.sub(r'\[.*?\]', '', line)
        line = line.strip()
        if line and line not in texts[-1:]:
            texts.append(line)
    return ' '.join(texts)


def fetch_one(video_id):
    """Use yt-dlp CLI to download auto subs for one video."""
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    out_pattern = str(TRANSCRIPTS_DIR / "%(id)s")
    url = "https://www.youtube.com/watch?v=" + video_id

    cmd = [
        "yt-dlp",
        "--cookies-from-browser", "chrome",
        "--write-auto-sub",
        "--sub-lang", "en",
        "--sub-format", "vtt",
        "--skip-download",
        "--no-check-formats",
        "--ignore-errors",
        "-o", out_pattern,
        url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    vtt_file = TRANSCRIPTS_DIR / ("%s.en.vtt" % video_id)
    if vtt_file.exists():
        raw = vtt_file.read_text(encoding="utf-8")
        text = clean_srt_to_text(raw)
        txt_file = TRANSCRIPTS_DIR / ("%s.txt" % video_id)
        txt_file.write_text(text, encoding="utf-8")
        vtt_file.unlink()
        return text, "youtube_auto_captions_vtt"

    srt_file = TRANSCRIPTS_DIR / ("%s.en.srt" % video_id)
    if srt_file.exists():
        raw = srt_file.read_text(encoding="utf-8")
        text = clean_srt_to_text(raw)
        txt_file = TRANSCRIPTS_DIR / ("%s.txt" % video_id)
        txt_file.write_text(text, encoding="utf-8")
        srt_file.unlink()
        return text, "youtube_auto_captions_srt"

    stderr = result.stderr[:300] if result.stderr else ""
    return "", "cli_fail: " + stderr


def run():
    videos = json.loads(VIDEOS_JSON.read_text(encoding="utf-8"))
    missing = [v for v in videos if v.get("transcript_status") != "fetched"]
    print("Missing transcripts: %d" % len(missing))

    ok = fail = 0
    for i, v in enumerate(missing):
        vid = v["video_id"]
        title = v["title"][:55]

        if i > 0:
            print("  (cooling down %ds...)" % DELAY_BETWEEN)
            time.sleep(DELAY_BETWEEN)

        print("[%d/%d] %s..." % (i + 1, len(missing), title))
        text, source = fetch_one(vid)

        if text and len(text) > 100:
            v["transcript_status"] = "fetched"
            v["transcript_source"] = source
            wc = len(text.split())
            print("  OK (%d words)" % wc)
            ok += 1
        else:
            v["transcript_status"] = "missing"
            v["transcript_source"] = source
            print("  FAIL: " + source[:80])
            fail += 1

    VIDEOS_JSON.write_text(
        json.dumps(videos, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("\nBatch Summary: ok=%d fail=%d" % (ok, fail))


if __name__ == "__main__":
    run()
