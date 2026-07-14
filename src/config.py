"""Configuration loading from feeds.yml."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


@dataclass
class FeedConfig:
    name: str
    url: str
    category: str = "General"


@dataclass
class Config:
    feeds: List[FeedConfig] = field(default_factory=list)
    max_entries_per_feed: int = 10
    max_total_entries: int = 50

    @classmethod
    def from_file(cls, path: str | Path) -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        feeds = [FeedConfig(**f) for f in data.get("feeds", [])]
        return cls(
            feeds=feeds,
            max_entries_per_feed=data.get("max_entries_per_feed", 10),
            max_total_entries=data.get("max_total_entries", 50),
        )
