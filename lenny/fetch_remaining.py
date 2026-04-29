#!/usr/bin/env python3
"""Fetch remaining transcripts one by one with long delays to avoid 429."""
import json
import sys
import time
import urllib.request
from pathlib import Path

def log(msg):
    print(msg, flush=True)

SCRIPT_DIR = Path(__file__).parent
VIDEOS_JSON = SCRIPT_DIR / "videos.json"
TRANSCRIPTS_DIR = SCRIPT_DIR / "transcripts"
DELAY = 45

def fetch_one(video_id):
    import yt_dlp
    url = "https://www.youtube.com/watch?v=" + video_id
    ydl_opts = {
        'quiet': True, 'no_warnings': True,
        'cookiesfrombrowser': ('chrome',),
        'format': 'sb0', 'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        subs = info.get('automatic_captions', {})
        en = subs.get('en', [])
        json3_url = None
        for s in en:
            if s.get('ext') == 'json3':
                json3_url = s['url']
                break
        if not json3_url:
            return "", "no_en_captions"

        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(ydl.cookiejar))
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'),
            ('Accept-Language', 'en-US,en;q=0.9'),
            ('Referer', 'https://www.youtube.com/watch?v=' + video_id),
        ]
        resp = opener.open(json3_url, timeout=30)
        data = json.loads(resp.read())
        events = data.get('events', [])
        texts = []
        for ev in events:
            for seg in ev.get('segs', []):
                t = seg.get('utf8', '').strip()
                if t and t != '\n':
                    texts.append(t)
        return ' '.join(texts), "youtube_auto_captions"


videos = json.loads(VIDEOS_JSON.read_text())
TRANSCRIPTS_DIR.mkdir(exist_ok=True)
missing = [v for v in videos if v.get('transcript_status') != 'fetched']
log("Remaining: %d" % len(missing))

ok = fail = 0
for i, v in enumerate(missing):
    vid = v['video_id']
    title = v['title'][:55]
    if i > 0:
        log("  (waiting %ds...)" % DELAY)
        time.sleep(DELAY)
    log("[%d/%d] %s" % (i+1, len(missing), title))
    try:
        text, src = fetch_one(vid)
        if text and len(text) > 100:
            (TRANSCRIPTS_DIR / (vid + ".txt")).write_text(text)
            v['transcript_status'] = 'fetched'
            v['transcript_source'] = src
            log("  OK (%d words)" % len(text.split()))
            ok += 1
        else:
            log("  FAIL: %s" % src)
            fail += 1
    except Exception as e:
        err = str(e)[:100]
        log("  ERROR: %s" % err)
        if '429' in err:
            log("  Rate limited. Increasing delay to 90s...")
            DELAY = 90
        fail += 1
    VIDEOS_JSON.write_text(json.dumps(videos, indent=2, ensure_ascii=False))

log("\nDone: ok=%d fail=%d" % (ok, fail))
