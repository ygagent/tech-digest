#!/usr/bin/env python3
"""
Lenny's Podcast - Article HTML Generator
Reads article content JSON and renders to HTML using article_template.html.

Usage:
    python3 generate_html.py                     # Generate all pending articles
    python3 generate_html.py --force VIDEO_ID    # Regenerate specific article
"""
import json
import re
import argparse
from pathlib import Path
from html import escape

SCRIPT_DIR = Path(__file__).parent
TEMPLATE_PATH = SCRIPT_DIR / "article_template.html"
VIDEOS_JSON = SCRIPT_DIR / "videos.json"
ARTICLES_DIR = SCRIPT_DIR / "articles"
OUTPUT_DIR = Path.home() / "Desktop" / "GitHub" / "tech-digest" / "lenny"

SECTIONS = [
    ("exec-summary", "01. 高层摘要"),
    ("guest-background", "02. 本期主题与嘉宾背景"),
    ("core-insights", "03. 核心观点精读"),
    ("frameworks", "04. 方法论提炼"),
    ("company-insights", "05. 对公司的启发"),
    ("action-items", "06. 公司级行动清单"),
    ("discussion", "07. 讨论问题"),
    ("quotes", "08. 关键表达与金句"),
    ("one-liner", "09. 一句话总结"),
    ("sources", "10. 原始资料"),
]

def e(text):
    return escape(str(text)) if text else ""


def slug_from_title(title):
    s = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
    s = re.sub(r'\s+', '-', s.strip())
    return s[:60].rstrip('-')


def build_toc_links(content, indent="    "):
    lines = []
    for sid, label in SECTIONS:
        sec = content.get(sid)
        if sec:
            lines.append('%s<a href="#%s">%s</a>' % (indent, sid, label))
    return "\n".join(lines)


def render_list_items(items):
    parts = []
    for item in items:
        parts.append("  <li>%s</li>\n" % e(item))
    return "<ul>\n%s</ul>\n" % "".join(parts)


def render_exec_summary(data):
    if isinstance(data, list):
        return render_list_items(data)
    return "<p>%s</p>\n" % e(data)


def render_guest_background(data):
    parts = []
    if isinstance(data, dict):
        for key in ["guest", "company", "role", "background", "topic", "importance", "relevant_teams"]:
            val = data.get(key)
            if val:
                label_map = {
                    "guest": "嘉宾", "company": "公司", "role": "角色",
                    "background": "背景", "topic": "本期主题",
                    "importance": "为什么重要", "relevant_teams": "适合团队"
                }
                parts.append("  <p><strong>%s：</strong>%s</p>\n" % (label_map.get(key, key), e(val)))
    elif isinstance(data, str):
        parts.append("<p>%s</p>\n" % e(data))
    return "".join(parts)


def render_core_insights(data):
    parts = []
    if isinstance(data, list):
        for i, insight in enumerate(data, 1):
            if isinstance(insight, dict):
                title = insight.get("title", "观点 %d" % i)
                parts.append('  <h3>观点 %d：%s</h3>\n' % (i, e(title)))
                for field in ["core_point", "evidence", "case_study", "company_insights"]:
                    val = insight.get(field)
                    if val:
                        label_map = {
                            "core_point": "核心观点",
                            "evidence": "关键论据",
                            "case_study": "典型案例",
                            "company_insights": "对公司的启发"
                        }
                        parts.append("  <h4>%s</h4>\n" % label_map.get(field, field))
                        if isinstance(val, list):
                            parts.append(render_list_items(val))
                        else:
                            parts.append("  <p>%s</p>\n" % e(val))
            elif isinstance(insight, str):
                parts.append("  <p>%s</p>\n" % e(insight))
    return "".join(parts)


def render_frameworks(data):
    parts = []
    if isinstance(data, list):
        parts.append('<table class="action-table">\n')
        parts.append("  <tr><th>Framework</th><th>核心问题</th><th>使用场景</th><th>关键步骤</th><th>参考价值</th></tr>\n")
        for fw in data:
            if isinstance(fw, dict):
                parts.append("  <tr>")
                for k in ["name", "core_question", "use_case", "steps", "value"]:
                    val = fw.get(k, "")
                    if isinstance(val, list):
                        val = "; ".join(val)
                    parts.append("<td>%s</td>" % e(val))
                parts.append("</tr>\n")
        parts.append("</table>\n")
    return "".join(parts)


def render_action_items(data):
    parts = []
    if isinstance(data, list):
        parts.append('<table class="action-table">\n')
        parts.append("  <tr><th>行动项</th><th>适用团队</th><th>适用场景</th><th>预期收益</th><th>优先级</th></tr>\n")
        for item in data:
            if isinstance(item, dict):
                prio = item.get("priority", "P2")
                prio_cls = {"P0": "priority-p0", "P1": "priority-p1"}.get(prio, "priority-p2")
                parts.append("  <tr>")
                parts.append("<td>%s</td>" % e(item.get("action", "")))
                parts.append("<td>%s</td>" % e(item.get("team", "")))
                parts.append("<td>%s</td>" % e(item.get("scenario", "")))
                parts.append("<td>%s</td>" % e(item.get("benefit", "")))
                parts.append('<td class="%s">%s</td>' % (prio_cls, e(prio)))
                parts.append("</tr>\n")
        parts.append("</table>\n")
    return "".join(parts)


def render_discussion(data):
    parts = []
    if isinstance(data, list):
        for i, q in enumerate(data, 1):
            parts.append('<div class="discussion-q"><p>%d. %s</p></div>\n' % (i, e(q)))
    return "".join(parts)


def render_quotes(data):
    parts = []
    if isinstance(data, list):
        for q in data:
            if isinstance(q, dict):
                parts.append('<div class="quote-block">\n')
                parts.append("  <blockquote>%s</blockquote>\n" % e(q.get("text", "")))
                if q.get("source"):
                    parts.append('  <div class="quote-source">— %s</div>\n' % e(q["source"]))
                parts.append("</div>\n")
            elif isinstance(q, str):
                parts.append('<div class="quote-block"><blockquote>%s</blockquote></div>\n' % e(q))
    return "".join(parts)


def render_one_liner(data):
    return '<div class="callout"><strong>一句话总结：</strong>%s</div>\n' % e(data)


def render_sources(data):
    parts = []
    if isinstance(data, dict):
        for k, v in data.items():
            label_map = {
                "video_url": "YouTube 视频",
                "published_at": "发布时间",
                "guest": "嘉宾",
                "transcript_source": "Transcript 来源",
                "notes": "备注"
            }
            parts.append("  <p><strong>%s：</strong>%s</p>\n" % (
                label_map.get(k, k),
                '<a href="%s">%s</a>' % (e(v), e(v)) if "http" in str(v) else e(v)
            ))
    return "".join(parts)


def build_main_content(content, video):
    parts = []
    title = content.get("title", video.get("title", ""))
    parts.append("  <h1>%s</h1>\n" % e(title))
    parts.append('  <div class="meta">%s &middot; %s &middot; Lenny\'s Podcast 深度精读</div>\n' % (
        e(video.get("published_at", "")), e(video.get("duration", ""))
    ))

    tags = content.get("tags", ["Lenny's Podcast", "Product", "Growth", "AI"])
    parts.append('  <div class="tags">\n')
    for tag in tags:
        parts.append('    <span class="tag">%s</span>\n' % e(tag))
    parts.append("  </div>\n")

    guest = video.get("guest", "")
    guest_title = video.get("guest_title", "")
    if guest:
        parts.append('  <div class="guest-meta">\n')
        parts.append('    <img class="guest-avatar" src="%s" alt="%s" onerror="this.style.display=\'none\'">\n' % (
            e(video.get("thumbnail", "")), e(guest)
        ))
        parts.append('    <div class="guest-info">\n')
        parts.append('      <div class="guest-name">%s</div>\n' % e(guest))
        if guest_title:
            parts.append('      <div class="guest-title-text">%s</div>\n' % e(guest_title))
        parts.append("    </div>\n")
        vid_url = video.get("url", "")
        if vid_url:
            parts.append('    <a class="video-link" href="%s" target="_blank">&#9654; 观看原视频</a>\n' % e(vid_url))
        parts.append("  </div>\n\n")

    section_renderers = {
        "exec-summary": render_exec_summary,
        "guest-background": render_guest_background,
        "core-insights": render_core_insights,
        "frameworks": render_frameworks,
        "company-insights": render_exec_summary,
        "action-items": render_action_items,
        "discussion": render_discussion,
        "quotes": render_quotes,
        "one-liner": render_one_liner,
        "sources": render_sources,
    }

    for sid, label in SECTIONS:
        data = content.get(sid)
        if not data:
            continue
        parts.append('  <h2 id="%s">%s</h2>\n\n' % (sid, label))
        renderer = section_renderers.get(sid)
        if renderer:
            parts.append(renderer(data))
        parts.append("\n")

    return "".join(parts)


def generate_article(article_path, video, output_dir=None):
    content = json.loads(Path(article_path).read_text(encoding="utf-8"))
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    title = content.get("title", video.get("title", ""))
    summary = content.get("one-liner", "")

    toc = build_toc_links(content)
    toc_mobile = build_toc_links(content, indent="      ")
    main = build_main_content(content, video)

    html = template
    html = html.replace("{{META_TITLE}}", "Lenny 精读 - " + e(title))
    html = html.replace("{{OG_TITLE}}", e(title))
    html = html.replace("{{OG_DESCRIPTION}}", e(summary))
    html = html.replace("{{OG_IMAGE}}", e(video.get("thumbnail", "")))
    html = html.replace("{{TOC_LINKS}}", toc)
    html = html.replace("{{TOC_LINKS_MOBILE}}", toc_mobile)
    html = html.replace("{{MAIN_CONTENT}}", main)

    out = Path(output_dir) if output_dir else OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    slug = slug_from_title(title)
    vid = video.get("video_id", slug)
    out_file = out / ("%s.html" % vid)
    out_file.write_text(html, encoding="utf-8")
    size_kb = out_file.stat().st_size / 1024
    print("  Generated %s (%.1f KB)" % (out_file.name, size_kb))
    return out_file


def run(force_id="", output_dir=None):
    if not VIDEOS_JSON.exists():
        print("videos.json not found.")
        return

    videos = json.loads(VIDEOS_JSON.read_text(encoding="utf-8"))
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    ok = skip = fail = 0

    for v in videos:
        vid = v["video_id"]
        if force_id and vid != force_id:
            continue

        article_file = ARTICLES_DIR / ("%s.json" % vid)
        if not article_file.exists():
            if not force_id:
                skip += 1
            continue

        try:
            generate_article(str(article_file), v, output_dir)
            ok += 1
        except Exception as ex:
            print("  FAIL %s: %s" % (vid, str(ex)[:100]))
            fail += 1

    print("\nHTML Generation: ok=%d skip=%d fail=%d" % (ok, skip, fail))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate Lenny article HTML")
    p.add_argument("--force", type=str, default="", help="Force regenerate specific video ID")
    p.add_argument("--output", type=str, default="", help="Output directory")
    a = p.parse_args()
    run(force_id=a.force, output_dir=a.output or None)
