"""Daily news digest entry point.

Fetches RSS feeds listed in feeds.yml, generates a Markdown digest saved to
digests/YYYY-MM-DD.md, and optionally pushes a notification to a WeChat Work
or DingTalk group robot.

Run locally:
    pip install -r requirements.txt
    python -m src.main
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

from .config import Config
from .digest import generate_markdown, generate_webhook_message
from .feeds import fetch_all
from .notifiers import notify

# Use CST (UTC+8) for the digest date: the cron runs at 22:00 UTC which is
# already the next calendar day in China (06:00 CST), and the user reads the
# digest in that CST morning. Labelling with the CST date matches "today".
CST = timezone(timedelta(hours=8))

REPO_ROOT = Path(__file__).resolve().parent.parent
FEEDS_PATH = REPO_ROOT / "feeds.yml"
DIGESTS_DIR = REPO_ROOT / "digests"


def _today_cst() -> date:
    return datetime.now(CST).date()


def main() -> int:
    config = Config.from_file(FEEDS_PATH)
    if not config.feeds:
        print("[error] no feeds configured in feeds.yml", file=sys.stderr)
        return 1

    print(f"[info] fetching {len(config.feeds)} feeds...", file=sys.stderr)
    items = fetch_all(config.feeds, max_per_feed=config.max_entries_per_feed)
    print(f"[info] total unique items: {len(items)}", file=sys.stderr)

    items = items[: config.max_total_entries]
    if not items:
        print("[error] no items collected from any feed", file=sys.stderr)
        return 1

    today = _today_cst()
    markdown = generate_markdown(items, today)

    DIGESTS_DIR.mkdir(exist_ok=True)
    output_path = DIGESTS_DIR / f"{today.isoformat()}.md"
    output_path.write_text(markdown, encoding="utf-8")
    print(f"[info] digest written to {output_path}", file=sys.stderr)

    webhook_url = os.environ.get("WEBHOOK_URL", "").strip()
    if webhook_url:
        msg = generate_webhook_message(items, today)
        notify(webhook_url, msg, f"每日世界新闻摘要 {today.isoformat()}")
    else:
        print("[info] WEBHOOK_URL not set, skipping notification", file=sys.stderr)

    # GitHub Actions notice (harmless when run locally).
    print(f"::notice::Daily news digest generated: "
          f"{today.isoformat()} ({len(items)} items)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
