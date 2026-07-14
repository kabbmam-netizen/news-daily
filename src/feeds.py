"""RSS feed fetching and parsing."""
from __future__ import annotations

import concurrent.futures
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

import feedparser

from .config import FeedConfig


@dataclass
class NewsItem:
    title: str
    url: str
    summary: str
    published: datetime
    source: str
    category: str


def _parse_published(entry) -> datetime:
    """Parse entry published time; fall back to now if missing or malformed."""
    for field_name in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, field_name, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass
    return datetime.now(timezone.utc)


def fetch_feed(feed: FeedConfig, max_entries: int) -> List[NewsItem]:
    """Fetch and parse a single RSS feed. Returns [] on any failure."""
    try:
        parsed = feedparser.parse(feed.url)
        if not parsed.entries:
            reason = getattr(parsed, "bozo_exception", "no entries")
            print(f"[warn] feed '{feed.name}' returned no entries: {reason}",
                  file=sys.stderr)
            return []
        items: List[NewsItem] = []
        for entry in parsed.entries[:max_entries]:
            url = getattr(entry, "link", "") or ""
            if not url:
                continue
            items.append(NewsItem(
                title=(getattr(entry, "title", "") or "(no title)").strip(),
                url=url,
                summary=getattr(entry, "summary", "") or "",
                published=_parse_published(entry),
                source=feed.name,
                category=feed.category,
            ))
        return items
    except Exception as e:  # network / parse errors - skip, don't crash
        print(f"[warn] failed to fetch feed '{feed.name}': {e}", file=sys.stderr)
        return []


def fetch_all(feeds: List[FeedConfig], max_per_feed: int = 10,
              workers: int = 8) -> List[NewsItem]:
    """Fetch all feeds concurrently, dedup by URL, sort newest first."""
    items: List[NewsItem] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_feed = {pool.submit(fetch_feed, f, max_per_feed): f for f in feeds}
        for future in concurrent.futures.as_completed(future_to_feed):
            feed = future_to_feed[future]
            try:
                result = future.result()
            except Exception as e:
                print(f"[warn] feed '{feed.name}' raised: {e}", file=sys.stderr)
                result = []
            if result:
                print(f"[info] {feed.name}: {len(result)} entries", file=sys.stderr)
            items.extend(result)

    # Dedup by URL. Note: cross-source dedup is weak (same story has different
    # URLs at BBC vs Guardian); this only catches exact-URL duplicates.
    # Acceptable for the "raw aggregation" tier.
    seen: set[str] = set()
    unique: List[NewsItem] = []
    for it in items:
        if it.url in seen:
            continue
        seen.add(it.url)
        unique.append(it)

    unique.sort(key=lambda x: x.published, reverse=True)
    return unique
