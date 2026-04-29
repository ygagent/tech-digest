#!/usr/bin/env python3
"""Extract subtitle URLs for remaining videos so they can be fetched externally."""
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VIDEOS_JSON = SCRIPT_DIR / "videos.json"

videos = json.loads(VIDEOS_JSON.read_text())
missing = [v for v in videos if v.get('transcript_status') != 'fetched']

print("Extracting subtitle URLs for %d videos..." % len(missing), flush=True)

import yt_dlp
ydl_opts = {
    'quiet': True, 'no_warnings': True,
    'cookiesfrombrowser': ('chrome',),
    'format': 'sb0', 'skip_download': True,
}

urls = {}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    for v in missing:
        vid = v['video_id']
        try:
            info = ydl.extract_info('https://www.youtube.com/watch?v=' + vid, download=False)
            subs = info.get('automatic_captions', {})
            en = subs.get('en', [])
            for s in en:
                if s.get('ext') == 'json3':
                    urls[vid] = s['url']
                    print("  %s: URL found" % vid, flush=True)
                    break
        except Exception as e:
            print("  %s: extract error" % vid, flush=True)

out = SCRIPT_DIR / "subtitle_urls.json"
out.write_text(json.dumps(urls, indent=2, ensure_ascii=False))
print("\nSaved %d URLs to subtitle_urls.json" % len(urls), flush=True)
