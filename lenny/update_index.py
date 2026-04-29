#!/usr/bin/env python3
"""
Lenny's Podcast - Index Page Generator
Generates the column index page listing all articles.
"""
import json
import re
from pathlib import Path
from html import escape

SCRIPT_DIR = Path(__file__).parent
VIDEOS_JSON = SCRIPT_DIR / "videos.json"
ARTICLES_DIR = SCRIPT_DIR / "articles"
OUTPUT_DIR = Path.home() / "Desktop" / "GitHub" / "tech-digest" / "lenny"
INDEX_JSON = OUTPUT_DIR / "index.json"

def e(text):
    return escape(str(text)) if text else ""


def build_index_json():
    if not VIDEOS_JSON.exists():
        return []

    videos = json.loads(VIDEOS_JSON.read_text(encoding="utf-8"))
    entries = []

    for v in videos:
        vid = v["video_id"]
        article_file = ARTICLES_DIR / ("%s.json" % vid)
        html_file = OUTPUT_DIR / ("%s.html" % vid)

        if not html_file.exists():
            continue

        article = {}
        if article_file.exists():
            article = json.loads(article_file.read_text(encoding="utf-8"))

        entries.append({
            "video_id": vid,
            "title": article.get("title", v.get("title", "")),
            "guest": v.get("guest", ""),
            "guest_title": v.get("guest_title", ""),
            "published_at": v.get("published_at", ""),
            "duration": v.get("duration", ""),
            "one_liner": article.get("one-liner", ""),
            "tags": article.get("tags", []),
            "thumbnail": v.get("thumbnail", ""),
            "video_url": v.get("url", ""),
            "html_file": "%s.html" % vid,
        })

    return entries


def generate_index_html(entries):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    INDEX_JSON.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Saved %d entries to index.json" % len(entries))

    cards_html = []
    for entry in entries:
        tags_html = ""
        for tag in entry.get("tags", [])[:4]:
            tags_html += '<span class="tag">%s</span>' % e(tag)

        cards_html.append("""
    <li class="article-card">
      <a class="article-link" href="%s">
        <img class="article-thumb" src="%s" alt="" loading="lazy"
             onerror="this.parentNode.querySelector('.thumb-placeholder').style.display='flex';this.style.display='none'">
        <div class="thumb-placeholder" style="display:none">LP</div>
        <div class="article-body">
          <div class="article-meta">
            <span class="article-date">%s</span>
            <span class="article-duration">%s</span>
          </div>
          <div class="article-title">%s</div>
          <div class="article-guest">%s%s</div>
          <div class="article-summary">%s</div>
          <div class="article-tags">%s</div>
        </div>
      </a>
    </li>""" % (
            e(entry.get("html_file", "")),
            e(entry.get("thumbnail", "")),
            e(entry.get("published_at", "")),
            e(entry.get("duration", "")),
            e(entry.get("title", "")),
            e(entry.get("guest", "")),
            (" - " + e(entry["guest_title"])) if entry.get("guest_title") else "",
            e(entry.get("one_liner", "")),
            tags_html,
        ))

    html = INDEX_PAGE_TEMPLATE.replace("{{ARTICLE_CARDS}}", "\n".join(cards_html))
    html = html.replace("{{ARTICLE_COUNT}}", str(len(entries)))

    index_file = OUTPUT_DIR / "index.html"
    index_file.write_text(html, encoding="utf-8")
    size_kb = index_file.stat().st_size / 1024
    print("Generated index.html (%.1f KB) with %d articles" % (size_kb, len(entries)))


INDEX_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Lenny's Podcast 深度精读</title>
  <meta property="og:title" content="Lenny's Podcast 深度精读">
  <meta property="og:description" content="全球产品、增长、AI 与创业方法论精读">
  <style>
    :root {
      --bg: #f5f6f8; --surface: #ffffff; --surface2: #f0f2f5;
      --border: #e8ecf1; --text: #1a1d21; --text-secondary: #3d4550; --text-muted: #8c95a1;
      --accent: #2d9f6f; --accent-light: #e8f5ef; --accent-hover: #248a5e;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
      --shadow-md: 0 4px 12px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04);
      --radius: 12px;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Helvetica, Arial, sans-serif;
      background: var(--bg); color: var(--text); line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }
    .topbar {
      background: var(--surface); border-bottom: 1px solid var(--border);
      padding: 14px 32px; display: flex; align-items: center; gap: 12px;
      position: sticky; top: 0; z-index: 100; box-shadow: var(--shadow-sm);
    }
    .topbar-brand {
      font-size: 1.1rem; font-weight: 700; color: var(--accent);
      text-decoration: none; display: flex; align-items: center; gap: 8px;
    }
    .topbar-brand svg { width: 28px; height: 28px; }
    .topbar-nav { display: flex; gap: 4px; margin-left: 24px; }
    .topbar-nav a {
      padding: 6px 16px; border-radius: 20px; font-size: 0.85rem; font-weight: 500;
      color: var(--text-secondary); text-decoration: none; transition: all 0.2s;
    }
    .topbar-nav a:hover { background: var(--surface2); color: var(--text); }
    .topbar-nav a.active { background: var(--accent-light); color: var(--accent); font-weight: 600; }
    .container { max-width: 900px; margin: 0 auto; padding: 48px 24px; }
    h1 { font-size: 1.8rem; font-weight: 800; margin-bottom: 8px; }
    .subtitle { color: var(--text-muted); font-size: 0.95rem; margin-bottom: 16px; }
    .intro {
      background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
      padding: 20px 24px; margin-bottom: 32px; font-size: 0.9rem; color: var(--text-secondary);
      line-height: 1.7; box-shadow: var(--shadow-sm);
    }
    .stats {
      display: flex; gap: 16px; margin-bottom: 32px;
    }
    .stat-card {
      background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
      padding: 16px 20px; flex: 1; text-align: center; box-shadow: var(--shadow-sm);
    }
    .stat-num { font-size: 1.5rem; font-weight: 800; color: var(--accent); }
    .stat-label { font-size: 0.78rem; color: var(--text-muted); margin-top: 4px; }
    .article-list { list-style: none; }
    .article-card {
      border: 1px solid var(--border); border-radius: var(--radius);
      background: var(--surface); margin-bottom: 14px;
      overflow: hidden; transition: all 0.2s; box-shadow: var(--shadow-sm);
    }
    .article-card:hover { border-color: var(--accent); transform: translateY(-2px); box-shadow: var(--shadow-md); }
    .article-link { display: flex; align-items: stretch; text-decoration: none; color: inherit; }
    .article-thumb {
      width: 180px; min-height: 120px; flex-shrink: 0;
      object-fit: cover; background: var(--surface2);
    }
    .thumb-placeholder {
      width: 180px; min-height: 120px; flex-shrink: 0;
      background: linear-gradient(135deg, #2d9f6f 0%, #1a7a4f 100%);
      display: flex; align-items: center; justify-content: center;
      color: rgba(255,255,255,0.9); font-size: 1.5rem; font-weight: 800;
    }
    .article-body { flex: 1; padding: 14px 18px; display: flex; flex-direction: column; justify-content: center; }
    .article-meta { display: flex; gap: 8px; margin-bottom: 6px; }
    .article-date, .article-duration {
      font-size: 0.7rem; font-weight: 600; color: var(--accent);
      background: var(--accent-light); padding: 2px 8px; border-radius: 8px;
    }
    .article-title { font-size: 1rem; font-weight: 700; margin-bottom: 4px; line-height: 1.35; }
    .article-card:hover .article-title { color: var(--accent); }
    .article-guest { font-size: 0.82rem; color: var(--text-muted); margin-bottom: 6px; }
    .article-summary { font-size: 0.82rem; color: var(--text-muted); line-height: 1.45; margin-bottom: 8px; }
    .article-tags { display: flex; gap: 4px; flex-wrap: wrap; }
    .tag {
      display: inline-block; font-size: 0.65rem; padding: 2px 7px; border-radius: 8px;
      background: var(--surface2); color: var(--text-muted); font-weight: 500;
    }
    .footer {
      margin-top: 48px; padding: 20px; text-align: center;
      font-size: 0.85rem; color: var(--text-muted);
    }
    .footer a { color: var(--accent); text-decoration: none; font-weight: 500; }
    @media (max-width: 640px) {
      .container { padding: 24px 16px; }
      h1 { font-size: 1.4rem; }
      .article-thumb, .thumb-placeholder { width: 100px; min-height: 90px; }
      .article-title { font-size: 0.92rem; }
      .stats { flex-direction: column; gap: 10px; }
      .topbar-nav { display: none; }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <a href="../index.html" class="topbar-brand">
      <svg viewBox="0 0 28 28" fill="none"><circle cx="14" cy="14" r="14" fill="#2d9f6f"/><path d="M8 14.5l3.5 3.5 8.5-8" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      Tech Digest
    </a>
    <nav class="topbar-nav">
      <a href="../index.html">每日简报</a>
      <a href="index.html" class="active">Lenny 精读</a>
    </nav>
  </header>
  <div class="container">
    <h1>Lenny's Podcast 深度精读</h1>
    <p class="subtitle">全球产品、增长、AI 与创业方法论精读</p>
    <div class="intro">
      这个专栏系统整理 Lenny's Podcast 中关于产品、增长、AI、创业和组织管理的高质量访谈内容。
      我们不会简单搬运视频摘要，而是将全球一线从业者的经验，转化成适合公司内部学习、讨论和落地的中文深度精读文章，
      帮助团队持续吸收外部先进方法论，提升产品判断、增长认知、AI 落地能力和工程组织效率。
    </div>
    <div class="stats">
      <div class="stat-card">
        <div class="stat-num">{{ARTICLE_COUNT}}</div>
        <div class="stat-label">深度精读文章</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">Lenny's Podcast</div>
        <div class="stat-label">内容来源</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">公司级</div>
        <div class="stat-label">内容定位</div>
      </div>
    </div>
    <ul class="article-list">
{{ARTICLE_CARDS}}
    </ul>
    <div class="footer">
      <a href="../index.html">每日科技简报</a> &middot;
      Lenny's Podcast 深度精读 &middot;
      Powered by <a href="https://cursor.com">Cursor AI</a>
    </div>
  </div>
</body>
</html>"""


def run():
    entries = build_index_json()
    if not entries:
        print("No articles found to index.")
        return
    generate_index_html(entries)


if __name__ == "__main__":
    run()
