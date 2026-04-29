#!/usr/bin/env python3
"""
Lenny's Podcast Deep Reading Pipeline
Full pipeline: fetch videos -> transcripts -> articles -> HTML -> index

Usage:
    python3 run_pipeline.py --limit 30           # Full run
    python3 run_pipeline.py --limit 30 --dry-run # Preview only
    python3 run_pipeline.py --force VIDEO_ID     # Regenerate one article
    python3 run_pipeline.py --skip-fetch         # Skip video/transcript fetch
    python3 run_pipeline.py --provider openai    # Use OpenAI instead of Anthropic
"""
import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def run_step(name, cmd):
    print("\n" + "=" * 60)
    print("  %s" % name)
    print("=" * 60)
    result = subprocess.run(
        [sys.executable] + cmd,
        cwd=str(SCRIPT_DIR),
    )
    if result.returncode != 0:
        print("  Step failed with code %d" % result.returncode)
        return False
    return True


def main():
    p = argparse.ArgumentParser(description="Lenny Podcast Deep Reading Pipeline")
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--force", type=str, default="")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--skip-fetch", action="store_true")
    p.add_argument("--skip-articles", action="store_true")
    p.add_argument("--provider", type=str, default="anthropic")
    a = p.parse_args()

    steps = []

    if not a.skip_fetch:
        fetch_cmd = ["fetch_videos.py", "--limit", str(a.limit)]
        if a.dry_run:
            fetch_cmd.append("--dry-run")
        steps.append(("Step 1: Fetch Video Metadata", fetch_cmd))

        transcript_cmd = ["fetch_transcripts.py", "--limit", str(a.limit)]
        if a.force:
            transcript_cmd.extend(["--force", a.force])
        if a.dry_run:
            transcript_cmd.append("--dry-run")
        steps.append(("Step 2: Fetch Transcripts", transcript_cmd))

    if not a.skip_articles:
        article_cmd = ["generate_articles.py", "--provider", a.provider]
        if a.limit:
            article_cmd.extend(["--limit", str(a.limit)])
        if a.force:
            article_cmd.extend(["--force", a.force])
        if a.dry_run:
            article_cmd.append("--dry-run")
        steps.append(("Step 3: Generate Articles", article_cmd))

    html_cmd = ["generate_html.py"]
    if a.force:
        html_cmd.extend(["--force", a.force])
    steps.append(("Step 4: Generate HTML", html_cmd))

    steps.append(("Step 5: Update Index", ["update_index.py"]))

    for name, cmd in steps:
        if not run_step(name, cmd):
            if a.dry_run:
                continue
            print("\nPipeline stopped at: %s" % name)
            return

    print("\n" + "=" * 60)
    print("  Pipeline Complete!")
    print("=" * 60)
    print("  Blog: ~/Desktop/GitHub/tech-digest/lenny/index.html")
    print("  URL:  https://agentbiubiubiu.github.io/tech-digest/lenny/")


if __name__ == "__main__":
    main()
