#!/usr/bin/env python3
"""Lenny's Podcast Transcript Fetcher using yt-dlp auto captions."""
import json
import argparse
import urllib.request
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VIDEOS_JSON = SCRIPT_DIR / "videos.json"
TRANSCRIPTS_DIR = SCRIPT_DIR / "transcripts"

_YDL = None

def get_ydl():
    global _YDL
    if _YDL is None:
        import yt_dlp
        _YDL = yt_dlp.YoutubeDL({
            'quiet': True,
            'no_warnings': True,
            'cookiesfrombrowser': ('chrome',),
            'format': 'sb0',
            'skip_download': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'subtitlesformat': 'json3',
        })
    return _YDL


def fetch_transcript(video_id):
    """Fetch auto-caption transcript via yt-dlp subtitle URLs."""
    url = "https://www.youtube.com/watch?v=" + video_id
    try:
        ydl = get_ydl()
        info = ydl.extract_info(url, download=False)
    except Exception as e:
        return "", "error_extract: " + str(e)[:150]

    subs = info.get('automatic_captions', {})
    en_subs = subs.get('en', [])
    json3_url = None
    for s in en_subs:
        if s.get('ext') == 'json3':
            json3_url = s['url']
            break

    if not json3_url:
        return "", "no_english_auto_captions"

    try:
        resp = urllib.request.urlopen(json3_url, timeout=30)
        data = json.loads(resp.read())
        events = data.get('events', [])
        texts = []
        for ev in events:
            for seg in ev.get('segs', []):
                t = seg.get('utf8', '').strip()
                if t and t != '\n':
                    texts.append(t)
        full_text = ' '.join(texts)
        return full_text, "youtube_auto_captions"
    except Exception as e:
        return "", "error_download: " + str(e)[:150]


def run(limit=0, force_id="", dry_run=False):
    if not VIDEOS_JSON.exists():
        print("videos.json not found. Run fetch_videos.py first.")
        return

    videos = json.loads(VIDEOS_JSON.read_text(encoding="utf-8"))
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    ok = skip = fail = done = 0

    for v in videos:
        vid = v["video_id"]
        if force_id and vid != force_id:
            continue
        tf = TRANSCRIPTS_DIR / (vid + ".txt")
        if not force_id and tf.exists() and v.get("transcript_status") == "fetched":
            skip += 1
            continue
        if limit and done >= limit:
            break
        done += 1
        title = v["title"][:60]
        if dry_run:
            print("   Would fetch: " + title)
            continue
        if done > 1:
            time.sleep(8)
        print("[%d] %s..." % (done, title))
        text, source = fetch_transcript(vid)
        if text and len(text) > 100:
            tf.write_text(text, encoding="utf-8")
            v["transcript_status"] = "fetched"
            v["transcript_source"] = source
            wc = len(text.split())
            print("    OK (%d words)" % wc)
            ok += 1
        else:
            v["transcript_status"] = "missing"
            v["transcript_source"] = source
            print("    FAIL: " + source)
            fail += 1

    VIDEOS_JSON.write_text(
        json.dumps(videos, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("\nTranscript Summary:")
    print("  Fetched: %d" % ok)
    print("  Skipped (cached): %d" % skip)
    print("  Failed: %d" % fail)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Fetch Lenny Podcast transcripts")
    p.add_argument("--limit", type=int, default=0, help="Max to fetch (0=all)")
    p.add_argument("--force", type=str, default="", help="Force re-fetch video ID")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    run(limit=a.limit, force_id=a.force, dry_run=a.dry_run)
