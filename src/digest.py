"""Markdown digest generation."""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from typing import List

from .feeds import NewsItem

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _strip_html(text: str) -> str:
    """Very light HTML stripping for summaries (no extra deps)."""
    text = _TAG_RE.sub("", text)
    return _WS_RE.sub(" ", text).strip()


def generate_markdown(items: List[NewsItem], today: date) -> str:
    """Render news items as a Markdown digest, grouped by category."""
    lines = [
        f"# 每日世界新闻摘要 — {today.isoformat()}",
        "",
        f"> 共收录 {len(items)} 条新闻，按分类归档，时间倒序。",
        "",
    ]

    by_category: dict[str, List[NewsItem]] = defaultdict(list)
    for it in items:
        by_category[it.category].append(it)

    for category in sorted(by_category.keys()):
        cat_items = by_category[category]
        lines.append(f"## {category} ({len(cat_items)})")
        lines.append("")
        for it in cat_items:
            title = it.title or "(no title)"
            lines.append(f"- **[{title}]({it.url})**")
            lines.append(f"  - 来源：{it.source} · "
                         f"{it.published.strftime('%Y-%m-%d %H:%M UTC')}")
            summary = _strip_html(it.summary)
            if summary:
                if len(summary) > 200:
                    summary = summary[:197] + "..."
                lines.append(f"  - {summary}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def generate_webhook_message(items: List[NewsItem], today: date,
                             max_items: int = 15) -> str:
    """Compact message for webhook push (kept short for message size limits)."""
    lines = [f"## 每日世界新闻摘要 {today.isoformat()}", ""]
    for it in items[:max_items]:
        title = it.title or "(no title)"
        lines.append(f"- [{title}]({it.url})")
    if len(items) > max_items:
        lines.append(f"- ...及另外 {len(items) - max_items} 条")
    lines.append("")
    lines.append(f"> 完整列表见仓库 `digests/{today.isoformat()}.md`")
    return "\n".join(lines)
