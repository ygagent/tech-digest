#!/usr/bin/env python3
"""
Lenny's Podcast - Video Metadata Fetcher
Fetches latest videos from YouTube channel, filters for full interviews only.

Usage:
    python3 fetch_videos.py --limit 30
    python3 fetch_videos.py --limit 30 --dry-run
"""

import json
import argparse
import re
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
VIDEOS_JSON = SCRIPT_DIR / "videos.json"
CHANNEL_URL = "https://www.youtube.com/@LennysPodcast/videos"

MIN_DURATION_SECONDS = 600  # 10 min minimum for a real interview
SHORTS_MAX_DURATION = 120   # Shorts are under 2 min

SKIP_PATTERNS = [
    r'#shorts',
    r'\bshort\b.*\bclip\b',
    r'\btrailer\b',
    r'\bpreview\b',
    r'\bteaser\b',
    r'\bhighlight\b.*\bclip\b',
    r'\bbest\s+moments?\b',
    r'\bcompilation\b',
]

def is_full_interview(entry: dict) -> bool:
    title = (entry.get("title") or "").lower()
    duration = entry.get("duration") or 0

    if duration < MIN_DURATION_SECONDS:
        return False
    if duration <= SHORTS_MAX_DURATION:
        return False

    for pattern in SKIP_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return False

    return True

def extract_guest_info(title: str) -> tuple[str, str]:
    """Try to parse guest name and title from video title."""
    guest = ""
    guest_title = ""

    paren_match = re.search(r'\(([^)]+)\)', title)
    pipe_match = re.search(r'\|\s*(.+)$', title)

    if pipe_match:
        info = pipe_match.group(1).strip()
        if paren_match and paren_match.start() > pipe_match.start():
            guest = info.split('(')[0].strip()
            guest_title = paren_match.group(1).strip()
        elif ',' in info:
            parts = info.split(',', 1)
            guest = parts[0].strip()
            guest_title = parts[1].strip()
        else:
            guest = info
    elif paren_match:
        guest_title = paren_match.group(1).strip()
        guest = title[:paren_match.start()].strip().rstrip('|').rstrip('-').strip()
        if ':' in guest:
            guest = guest.split(':')[-1].strip()

    return guest, guest_title

def format_duration(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    if h > 0:
        return f"{h}h{m}m"
    return f"{m}m"


def fetch_videos(limit: int = 80) -> list[dict]:
    import yt_dlp

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'playlistend': limit,
    }

    print(f"📡 Fetching up to {limit} videos from {CHANNEL_URL}...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(CHANNEL_URL, download=False)
        entries = info.get('entries', [])

    print(f"   Retrieved {len(entries)} entries from channel")
    return entries


def load_existing_videos() -> dict[str, dict]:
    if VIDEOS_JSON.exists():
        data = json.loads(VIDEOS_JSON.read_text(encoding='utf-8'))
        return {v['video_id']: v for v in data}
    return {}


def run(limit: int = 30, dry_run: bool = False):
    raw_entries = fetch_videos(limit=limit + 30)

    existing = load_existing_videos()

    interviews = []
    skipped = []

    for entry in raw_entries:
        if is_full_interview(entry):
            interviews.append(entry)
        else:
            skipped.append(entry)

    print(f"✅ Filtered: {len(interviews)} full interviews, {len(skipped)} skipped")
    if skipped:
        for s in skipped[:5]:
            print(f"   ⏭  Skipped: {s.get('title','')} ({format_duration(s.get('duration',0))})")

    selected = interviews[:limit]
    print(f"📋 Selected {len(selected)} videos for processing")

    videos = []
    new_count = 0
    for entry in selected:
        vid = entry.get('id', '')
        title = entry.get('title', '')
        guest, guest_title = extract_guest_info(title)

        if vid in existing:
            old = existing[vid]
            old['title'] = title
            old['guest'] = old.get('guest') or guest
            old['guest_title'] = old.get('guest_title') or guest_title
            videos.append(old)
        else:
            new_count += 1
            videos.append({
                'video_id': vid,
                'title': title,
                'url': f'https://www.youtube.com/watch?v={vid}',
                'published_at': '',
                'duration': format_duration(entry.get('duration', 0)),
                'duration_seconds': entry.get('duration', 0),
                'guest': guest,
                'guest_title': guest_title,
                'description': '',
                'thumbnail': f'https://i.ytimg.com/vi/{vid}/maxresdefault.jpg',
                'transcript_status': 'pending',
                'article_status': 'pending',
                'source': 'youtube',
                'channel': "Lenny's Podcast",
                'category': 'Lenny 深度精读',
                'view_count': entry.get('view_count', 0),
            })

    print(f"   New videos: {new_count}, Existing: {len(selected) - new_count}")

    if dry_run:
        print("\n🔍 DRY RUN - Would write the following videos:")
        for i, v in enumerate(videos, 1):
            status = "NEW" if v.get('transcript_status') == 'pending' else "EXISTING"
            print(f"   {i}. [{status}] {v['title']}")
        return

    VIDEOS_JSON.write_text(
        json.dumps(videos, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )
    print(f"\n💾 Saved {len(videos)} videos to {VIDEOS_JSON}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Fetch Lenny's Podcast videos")
    parser.add_argument('--limit', type=int, default=30, help='Number of videos to fetch')
    parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
    args = parser.parse_args()
    run(limit=args.limit, dry_run=args.dry_run)
