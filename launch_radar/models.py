"""Data shapes. Posts come in from any source (X API, a browser extension,
a scraped JSON dump) and are normalised into :class:`Post`."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def _parse_dt(v: Any) -> datetime | None:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v, tz=timezone.utc)
    s = str(v).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        # X API v1 style: "Wed Oct 07 03:14:00 +0000 2026"
        dt = datetime.strptime(s, "%a %b %d %H:%M:%S %z %Y")
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


@dataclass
class Author:
    handle: str
    created_at: datetime | None = None
    followers: int = 0
    following: int = 0
    tweets: int = 0
    bio: str = ""
    url: str = ""
    pinned_post_id: str | None = None

    def age_days(self, now: datetime | None = None) -> float | None:
        if not self.created_at:
            return None
        now = now or datetime.now(timezone.utc)
        return (now - self.created_at).total_seconds() / 86400


@dataclass
class Post:
    id: str
    text: str
    url: str
    author: Author
    created_at: datetime | None = None
    likes: int = 0
    reposts: int = 0
    replies: int = 0
    views: int = 0
    is_reply: bool = False
    is_repost: bool = False
    lang: str = "en"
    # optional second measurement for growth scoring: {"minutes": 30, "likes": 12, "reposts": 3}
    later: dict[str, int] | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Post":
        a = d.get("author") or {}
        if isinstance(a, str):
            a = {"handle": a}
        author = Author(
            handle=str(a.get("handle") or a.get("username") or "").lstrip("@"),
            created_at=_parse_dt(a.get("created_at")),
            followers=int(a.get("followers") or a.get("followers_count") or 0),
            following=int(a.get("following") or a.get("following_count") or 0),
            tweets=int(a.get("tweets") or a.get("tweet_count") or 0),
            bio=str(a.get("bio") or a.get("description") or ""),
            url=str(a.get("url") or ""),
            pinned_post_id=a.get("pinned_post_id") or a.get("pinned_tweet_id"),
        )
        pid = str(d.get("id") or "")
        url = d.get("url") or (f"https://x.com/{author.handle}/status/{pid}" if author.handle and pid else "")
        return cls(
            id=pid,
            text=str(d.get("text") or ""),
            url=url,
            author=author,
            created_at=_parse_dt(d.get("created_at")),
            likes=int(d.get("likes") or d.get("like_count") or 0),
            reposts=int(d.get("reposts") or d.get("retweet_count") or 0),
            replies=int(d.get("replies") or d.get("reply_count") or 0),
            views=int(d.get("views") or d.get("impression_count") or 0),
            is_reply=bool(d.get("is_reply", False)),
            is_repost=bool(d.get("is_repost", False)),
            lang=str(d.get("lang") or "en"),
            later=d.get("later"),
        )


@dataclass
class Candidate:
    """A scored post: everything the feed / alert layer needs."""
    post: Post
    score: int
    matched: dict[str, list[str]]
    reasons: list[str]
    tickers: list[str] = field(default_factory=list)
    contracts: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    launchpad: str | None = None
    chain: str | None = None
    category: str | None = None

    @property
    def status(self) -> str:
        if self.score >= 70:
            return "alert"
        if self.score >= 40:
            return "feed"
        return "noise"

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "status": self.status,
            "post_url": self.post.url,
            "author": "@" + self.post.author.handle,
            "text": self.post.text,
            "matched": self.matched,
            "reasons": self.reasons,
            "tickers": self.tickers,
            "contracts": self.contracts,
            "links": self.links,
            "launchpad": self.launchpad,
            "chain": self.chain,
            "category": self.category,
        }


__all__ = ["Author", "Post", "Candidate"]
