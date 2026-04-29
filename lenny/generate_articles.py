#!/usr/bin/env python3
"""
Lenny's Podcast - Article Generator
Generates high-quality Chinese deep-reading articles from transcripts.

Requires ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable.

Usage:
    python3 generate_articles.py
    python3 generate_articles.py --limit 5
    python3 generate_articles.py --force VIDEO_ID
    python3 generate_articles.py --dry-run
    python3 generate_articles.py --provider openai
"""
import json
import os
import argparse
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VIDEOS_JSON = SCRIPT_DIR / "videos.json"
TRANSCRIPTS_DIR = SCRIPT_DIR / "transcripts"
ARTICLES_DIR = SCRIPT_DIR / "articles"
QUALITY_DIR = SCRIPT_DIR / "quality"

ARTICLE_PROMPT_TEMPLATE = """你是一个公司级内容团队的高级编辑。你的任务是将以下英文访谈 transcript 转化为一篇高质量的中文深度精读文章。

## 视频信息
- 标题：{title}
- 嘉宾：{guest}
- 嘉宾身份：{guest_title}
- 频道：Lenny's Podcast
- 时长：{duration}

## 内容定位
这篇文章面向公司内部传阅，读者包括老板、高层、业务负责人、产品负责人、技术负责人、增长负责人和普通同事。

## 输出要求
请输出一个 JSON 对象（不要用 markdown 代码块包裹），包含以下字段：

{{
  "title": "中文标题（不要直译，要体现核心价值）",
  "tags": ["标签1", "标签2", "标签3", "标签4"],
  "exec-summary": [
    "bullet1：高层最值得关注的内容...",
    "bullet2：...",
    "bullet3：...",
    "bullet4：...",
    "bullet5：..."
  ],
  "guest-background": {{
    "guest": "嘉宾姓名",
    "company": "所在公司",
    "role": "当前角色",
    "background": "代表经历（简述）",
    "topic": "本期讨论的核心问题",
    "importance": "为什么这期内容重要",
    "relevant_teams": "对哪些团队最有参考价值"
  }},
  "core-insights": [
    {{
      "title": "观点标题",
      "core_point": "核心观点阐述",
      "evidence": "嘉宾的论据和依据",
      "case_study": "访谈中提到的具体案例",
      "company_insights": "对公司产品/增长/AI/工程的启发"
    }}
  ],
  "frameworks": [
    {{
      "name": "框架名称",
      "core_question": "这个框架解决什么问题",
      "use_case": "适用场景",
      "steps": "关键步骤（简述）",
      "value": "对公司的参考价值"
    }}
  ],
  "bingx-insights": [
    "启发1：结合交易所/AI Agent/产品体验/工程效率的具体思考...",
    "启发2：...",
    "启发3：..."
  ],
  "action-items": [
    {{
      "action": "具体可执行行动（不要泛泛而谈）",
      "team": "适用团队",
      "scenario": "适用场景",
      "benefit": "预期收益",
      "priority": "P0/P1/P2"
    }}
  ],
  "discussion": [
    "讨论问题1：有启发性的问题，能引导团队思考...",
    "讨论问题2：...",
    "讨论问题3：..."
  ],
  "quotes": [
    {{
      "text": "中文转述的关键表达（不要大段英文）",
      "source": "嘉宾名 - Lenny's Podcast"
    }}
  ],
  "one-liner": "一句话总结本期价值（有判断力，适合列表页展示）",
  "sources": {{
    "video_url": "{video_url}",
    "published_at": "{published_at}",
    "guest": "{guest}",
    "transcript_source": "{transcript_source}",
    "notes": "基于 YouTube 自动字幕整理"
  }}
}}

## 写作要求
1. 高层摘要要有判断力，不要只复述。要指出这期为什么值得关注。
2. 核心观点至少 4-8 个，按主题重新组织，不要按时间线复述。
3. 每个观点都要有：核心观点、论据、案例、公司启发。
4. 方法论要可复用，能写成步骤或检查清单。
5. BingX 启发要结合交易所、AI Agent、合约交易、大前端、工程效率等实际场景。
6. 行动清单 5-10 条，必须具体可执行。
7. 讨论问题 3-5 个，要有启发性。
8. 关键表达用中文转述，不要大段英文。
9. 中文表达自然专业，不堆术语，不鸡汤，不空话。
10. 文章信息密度高，不凑字数。
11. 不要编造 transcript 中没有的内容。
12. 不确定的信息要标注。

## Transcript 内容（前 12000 词）
{transcript}

请直接输出 JSON 对象，不要添加其他文字。"""


def call_anthropic(prompt, max_tokens=8000):
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def call_openai(prompt, max_tokens=8000):
    import openai
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def generate_article(video, transcript_text, provider="anthropic"):
    prompt = ARTICLE_PROMPT_TEMPLATE.format(
        title=video.get("title", ""),
        guest=video.get("guest", "Unknown"),
        guest_title=video.get("guest_title", ""),
        duration=video.get("duration", ""),
        video_url=video.get("url", ""),
        published_at=video.get("published_at", ""),
        transcript_source=video.get("transcript_source", "youtube_auto_captions"),
        transcript=transcript_text[:48000],
    )

    if provider == "openai":
        raw = call_openai(prompt)
    else:
        raw = call_anthropic(prompt)

    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split('\n')
        raw = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])

    return json.loads(raw)


def quality_check(article, video):
    """Basic quality scoring."""
    score = {"completeness": 0, "professional": 0, "accuracy": 0, "copyright": 0}
    issues = []

    required_sections = [
        "exec-summary", "guest-background", "core-insights",
        "frameworks", "bingx-insights", "action-items",
        "discussion", "quotes", "one-liner", "sources"
    ]
    present = sum(1 for s in required_sections if article.get(s))
    score["completeness"] = int(present / len(required_sections) * 100)

    insights = article.get("core-insights", [])
    if len(insights) >= 4:
        score["professional"] += 40
    elif len(insights) >= 2:
        score["professional"] += 20
    actions = article.get("action-items", [])
    if len(actions) >= 5:
        score["professional"] += 30
    elif len(actions) >= 3:
        score["professional"] += 15
    frameworks = article.get("frameworks", [])
    if len(frameworks) >= 2:
        score["professional"] += 30
    elif len(frameworks) >= 1:
        score["professional"] += 15

    score["accuracy"] = 80
    if article.get("sources", {}).get("video_url"):
        score["accuracy"] += 10
    if article.get("sources", {}).get("transcript_source"):
        score["accuracy"] += 10

    score["copyright"] = 90
    one_liner = article.get("one-liner", "")
    if len(one_liner) > 5:
        score["copyright"] += 10

    total = int((
        score["completeness"] * 0.3 +
        score["professional"] * 0.3 +
        score["accuracy"] * 0.2 +
        score["copyright"] * 0.2
    ))

    return {
        "video_id": video.get("video_id", ""),
        "quality_score": total,
        "completeness_score": score["completeness"],
        "professional_score": score["professional"],
        "accuracy_score": score["accuracy"],
        "copyright_score": score["copyright"],
        "issues": issues,
    }


def run(limit=0, force_id="", dry_run=False, provider="anthropic"):
    if not VIDEOS_JSON.exists():
        print("videos.json not found.")
        return

    videos = json.loads(VIDEOS_JSON.read_text(encoding="utf-8"))
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)

    ok = skip = fail = done = 0

    for v in videos:
        vid = v["video_id"]
        if force_id and vid != force_id:
            continue

        transcript_file = TRANSCRIPTS_DIR / ("%s.txt" % vid)
        article_file = ARTICLES_DIR / ("%s.json" % vid)

        if v.get("transcript_status") != "fetched" or not transcript_file.exists():
            if not force_id:
                continue
            print("  No transcript for %s" % vid)
            fail += 1
            continue

        if not force_id and article_file.exists() and v.get("article_status") == "generated":
            skip += 1
            continue

        if limit and done >= limit:
            break
        done += 1

        title = v["title"][:55]
        if dry_run:
            print("   Would generate: %s" % title)
            continue

        print("[%d] Generating: %s..." % (done, title))
        transcript = transcript_file.read_text(encoding="utf-8")

        try:
            article = generate_article(v, transcript, provider=provider)

            article_file.write_text(
                json.dumps(article, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            qr = quality_check(article, v)
            quality_file = QUALITY_DIR / ("%s.json" % vid)
            quality_file.write_text(
                json.dumps(qr, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            v["article_status"] = "generated"
            v["article_quality_score"] = qr["quality_score"]
            print("  OK (quality: %d)" % qr["quality_score"])
            ok += 1

            if done < limit or limit == 0:
                time.sleep(3)

        except Exception as ex:
            v["article_status"] = "failed"
            print("  FAIL: %s" % str(ex)[:150])
            fail += 1

    VIDEOS_JSON.write_text(
        json.dumps(videos, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("\nArticle Generation: ok=%d skip=%d fail=%d" % (ok, skip, fail))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate Lenny deep-reading articles")
    p.add_argument("--limit", type=int, default=0, help="Max articles (0=all)")
    p.add_argument("--force", type=str, default="", help="Force regen video ID")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--provider", type=str, default="anthropic",
                   choices=["anthropic", "openai"], help="LLM provider")
    a = p.parse_args()
    run(limit=a.limit, force_id=a.force, dry_run=a.dry_run, provider=a.provider)
